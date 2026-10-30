"""Build readable, multi-cell Jupyter notebooks from generated Python scripts."""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

import nbformat


def _section(node: ast.AST) -> str:
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        return "Imports"
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return "Functions and classes"
    if isinstance(node, ast.If) and isinstance(node.test, ast.Compare):
        # Keep the standard script entry point in its own final cell.
        if isinstance(node.test.left, ast.Name) and node.test.left.id == "__name__":
            return "Run experiment"
    if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
        return "Configuration and constants"
    return "Experiment steps"


def build_notebook_cells(source: str) -> list[Any]:
    """Split valid Python into ordered, logically grouped cells without changing code."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return [
            nbformat.v4.new_markdown_cell("## Generated code\n\nThe candidate contains a syntax error; the original text is preserved below."),
            nbformat.v4.new_code_cell(source.rstrip() + "\n"),
        ]

    lines = source.splitlines(keepends=True)
    nodes = list(tree.body)
    if not nodes:
        return [nbformat.v4.new_markdown_cell("## Generated code\n\nNo executable Python was generated.")]

    groups: list[tuple[str, int, int]] = []
    previous_end = 0
    current_section = None
    group_start = None
    group_end = None
    for node in nodes:
        start = max(0, getattr(node, "lineno", 1) - 1)
        end = getattr(node, "end_lineno", getattr(node, "lineno", 1))
        section = _section(node)
        # Preserve comments/blank lines immediately preceding each AST node.
        if current_section is None:
            group_start = previous_end
            current_section = section
            group_end = end
        elif section == current_section:
            group_end = end
        else:
            groups.append((current_section, int(group_start), int(group_end)))
            current_section = section
            group_start = previous_end
            group_end = end
        previous_end = end
    groups.append((str(current_section), int(group_start), int(group_end)))

    cells: list[Any] = []
    descriptions = {
        "Imports": "Load the libraries required by the experiment.",
        "Configuration and constants": "Set experiment parameters and reusable configuration.",
        "Functions and classes": "Define reusable functions and classes before running the experiment.",
        "Experiment steps": "Execute the experiment steps in order.",
        "Run experiment": "Run the script entry point and produce the final results.",
    }
    for section, start, end in groups:
        code = "".join(lines[start:end]).strip("\n")
        if not code.strip():
            continue
        cells.append(nbformat.v4.new_markdown_cell(f"## {section}\n\n{descriptions.get(section, '')}".rstrip()))
        cells.append(nbformat.v4.new_code_cell(code + "\n"))
    return cells


def create_generated_notebook(
    source: str,
    output_path: str | Path,
    *,
    model: str,
    status: str,
    orchestrator: str,
    execution: dict | None = None,
) -> None:
    nb = nbformat.v4.new_notebook()
    nb.metadata = {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3"},
        "collab_cli_agent": {"model": model, "status": status, "orchestrator": orchestrator,
                             "notebook_layout": "logical_multi_cell"},
    }
    nb.cells = [
        nbformat.v4.new_markdown_cell(
            f"# AI-generated experiment\n\nModel: `{model}`\n\nOrchestrator: **{orchestrator}**\n\nStatus: **{status}**\n\n"
            "Run the code cells from top to bottom. Imports, configuration, reusable definitions and execution are separated into individual sections."
        ),
        *build_notebook_cells(source),
    ]
    if execution:
        code_cells = [cell for cell in nb.cells if cell.cell_type == "code"]
        if code_cells:
            cell = code_cells[-1]
            cell.execution_count = 1
            if execution.get("stdout"):
                cell.outputs.append(nbformat.v4.new_output("stream", name="stdout", text=execution["stdout"]))
            if execution.get("stderr"):
                cell.outputs.append(nbformat.v4.new_output("stream", name="stderr", text=execution["stderr"]))
            if execution.get("returncode", 1) != 0:
                cell.outputs.append(nbformat.v4.new_output(
                    "error", ename="ExecutionError",
                    evalue=f"Process returned {execution.get('returncode')}", traceback=[]
                ))
    nbformat.validate(nb)
    nbformat.write(nb, output_path)
