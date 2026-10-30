import nbformat

from scripts.notebook_builder import build_notebook_cells, create_generated_notebook


def test_generated_script_is_split_into_logical_cells(tmp_path):
    source = '''import math\nimport json\n\nTHRESHOLD = 0.5\n\ndef score(value):\n    return value * 2\n\nresult = score(THRESHOLD)\nprint(json.dumps({"result": result}))\n'''
    cells = build_notebook_cells(source)
    code_cells = [cell for cell in cells if cell.cell_type == "code"]
    markdown_cells = [cell for cell in cells if cell.cell_type == "markdown"]
    assert len(code_cells) >= 3
    assert len(markdown_cells) >= 3
    assert "import math" in code_cells[0].source
    assert "THRESHOLD" in code_cells[1].source
    assert "def score" in code_cells[2].source
    assert "print" in code_cells[-1].source


def test_notebook_metadata_and_outputs_are_valid(tmp_path):
    source = "import json\n\nvalue = 42\nprint(json.dumps({'value': value}))\n"
    path = tmp_path / "generated_notebook.ipynb"
    create_generated_notebook(
        source, path, model="test-model", status="passed", orchestrator="LangGraph",
        execution={"stdout": '{"value": 42}\n', "stderr": "", "returncode": 0},
    )
    notebook = nbformat.read(path, as_version=4)
    nbformat.validate(notebook)
    assert notebook.metadata.collab_cli_agent.notebook_layout == "logical_multi_cell"
    assert len([cell for cell in notebook.cells if cell.cell_type == "code"]) >= 2
    assert notebook.cells[-1].outputs[0].text == '{"value": 42}\n'


def test_invalid_python_is_preserved_in_single_diagnostic_cell():
    cells = build_notebook_cells("def broken(:\n    pass\n")
    assert cells[0].cell_type == "markdown"
    assert cells[1].cell_type == "code"
    assert "def broken(:" in cells[1].source
