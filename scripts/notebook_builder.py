"""Semantic, execution-order-preserving Jupyter notebook generation.

The builder never reorders Python statements. It uses AST structure, identifiers,
called APIs and source comments to divide a generated script into notebook-sized
sections that resemble a practical data-science / ML workflow.
"""
from __future__ import annotations

import ast
import hashlib
import re
from pathlib import Path
from typing import Any

import nbformat


SECTION_GUIDES = {
    "Environment and imports": "Import dependencies and prepare the notebook runtime.",
    "Experiment configuration": "Define reproducible parameters, paths, seeds and settings.",
    "Data acquisition": "Load, download or construct the source data used by the experiment.",
    "Data inspection and exploratory analysis": "Inspect data shape, types, missingness and descriptive patterns.",
    "Data validation and quality checks": "Check schema, ranges, duplicates, missing values and input assumptions.",
    "Feature engineering and preprocessing": "Clean, transform and prepare features for downstream analysis.",
    "Train-test split and cross-validation": "Create evaluation partitions without leaking information across splits.",
    "Baseline and reference methods": "Establish a simple reference result before fitting the main model.",
    "Model definition and initialization": "Define estimators, architectures, loss functions or reusable model components.",
    "Model training": "Fit or train the selected model using the prepared training data.",
    "Prediction and inference": "Generate predictions or apply the fitted model to evaluation data.",
    "Evaluation and metrics": "Measure model or experiment performance using appropriate metrics.",
    "Diagnostics and error analysis": "Inspect residuals, failure cases, feature importance or model behaviour.",
    "Visualization": "Create plots and visual summaries to communicate the findings.",
    "Results and interpretation": "Summarize findings and interpret the experiment outputs.",
    "Export and persistence": "Save models, tables, figures and machine-readable results.",
    "Experiment execution": "Run the remaining experiment logic in its original order.",
    "Reusable definitions": "Define functions and classes that are used by later notebook sections.",
}

# Ordered from specific to general. These are semantic hints, not mandatory
# requirements: arbitrary coding tasks still receive useful section headings.
RULES: list[tuple[str, tuple[str, ...]]] = [
    ("Data acquisition", ("read_csv", "read_excel", "read_parquet", "read_json", "read_sql", "load_dataset", "fetch_openml", "download", "requests.get", "urlopen", "read_file", "load_data", "from_csv", "from_json", "make_classification", "make_regression", "load_iris", "load_breast_cancer", "load_wine", "load_diabetes")),
    ("Data inspection and exploratory analysis", ("describe", "value_counts", "nunique", "head", "tail", "sample", "info", "shape", "corr", "cov", "hist", "pairplot", "countplot", "boxplot", "scatterplot", "heatmap", "profile")),
    ("Data validation and quality checks", ("isna", "isnull", "notnull", "duplicated", "assert", "validate", "schema", "check_", "drop_duplicates", "missing", "outlier")),
    ("Feature engineering and preprocessing", ("get_dummies", "onehot", "one_hot", "labelencoder", "standardscaler", "minmaxscaler", "robustscaler", "imputer", "simpleimputer", "columntransformer", "pipeline", "transform", "fit_transform", "scaler", "preprocess", "tokeniz", "vectoriz", "encode", "normalize")),
    ("Train-test split and cross-validation", ("train_test_split", "cross_val", "kfold", "stratifiedkfold", "timeseriessplit", "split_data", "validation_split")),
    ("Baseline and reference methods", ("dummyclassifier", "dummyregressor", "baseline", "majorityclass", "naive", "benchmark_model")),
    ("Model definition and initialization", ("logisticregression(", "randomforest", "decisiontree", "gradientboost", "xgb", "lgbm", "svc(", "svr(", "knn(", "kneighbors", "mlpclassifier", "mlpregressor", "sequential(", "nn.module", "keras", "pytorch", "tensorflow", "catboost", "estimator", "classifier(", "regressor(")),
    ("Model training", (".fit(", "train(", "trainer.fit", "model.fit", "optimizer.step", "backward(", "train_model", "fit_model", "epochs", "training_loop")),
    ("Evaluation and metrics", ("accuracy_score", "precision_score", "recall_score", "f1_score", "classification_report", "confusion_matrix", "mean_squared_error", "root_mean_squared_error", "r2_score", "roc_auc_score", "roc_curve", "silhouette_score", "evaluate(", "metric", "log_loss", "mean_absolute_error", "mse =", "rmse =", "auc =")),
    ("Prediction and inference", (".predict(", "predict_proba(", "decision_function(", "model.generate(", "pipeline.predict", "inference(", "y_pred", "predictions =", "predict(", "generate(", "forward(")),
    ("Diagnostics and error analysis", ("feature_importances_", "coef_", "residual", "error_analysis", "misclassified", "classification_errors", "shap", "permutation_importance", "learning_curve", "validation_curve")),
    ("Visualization", ("plt.show(", "plt.figure(", "plt.subplots(", "sns.", "plotly", "px.", "go.figure", "savefig(", "display(", "altair", "histplot(", "scatter(", "barplot(")),
    ("Export and persistence", ("to_csv(", "to_excel(", "to_parquet(", "to_json(", "joblib.dump", "pickle.dump", "save_model(", "model.save(", "write_text(", "json.dump(", "savefig(")),
]


def _node_source(node: ast.AST, lines: list[str]) -> str:
    start = max(0, getattr(node, "lineno", 1) - 1)
    end = getattr(node, "end_lineno", getattr(node, "lineno", 1))
    return "".join(lines[start:end])


def _semantic_section(node: ast.AST, source: str) -> str:
    """Infer a meaningful section from names, calls, comments and AST shape."""
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        return "Environment and imports"
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        # Keep the actual definitions together; a function named train/evaluate
        # is a reusable definition, not an immediate training/evaluation action.
        return "Reusable definitions"
    if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
        return "Experiment configuration"
    if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
        targets = ast.unparse(node.targets[0] if isinstance(node, ast.Assign) else node.target).lower()
        if any(x in targets for x in ("seed", "random_state", "config", "param", "path", "device", "batch_size", "learning_rate", "test_size", "n_estimators")):
            return "Experiment configuration"
    if isinstance(node, ast.If) and isinstance(node.test, ast.Compare):
        if isinstance(node.test.left, ast.Name) and node.test.left.id == "__name__":
            return "Experiment execution"

    text = (source + " " + ast.dump(node, include_attributes=False)).lower()
    # Respect explicit notebook-style section comments and common generated labels.
    comment_match = re.search(r"(?im)^\s*#\s*(?:section\s*:\s*|%%\s*)?([a-z][a-z0-9 /&_-]{3,70})\s*$", source)
    if comment_match:
        label = comment_match.group(1).strip(" #-")
        normalized = label.lower()
        aliases = {
            "load data": "Data acquisition", "data loading": "Data acquisition",
            "exploratory data analysis": "Data inspection and exploratory analysis",
            "eda": "Data inspection and exploratory analysis", "preprocessing": "Feature engineering and preprocessing",
            "feature engineering": "Feature engineering and preprocessing", "training": "Model training",
            "model training": "Model training", "evaluation": "Evaluation and metrics",
            "model evaluation": "Evaluation and metrics", "visualization": "Visualization",
            "results": "Results and interpretation", "save results": "Export and persistence",
        }
        if normalized in aliases:
            return aliases[normalized]

    for section, hints in RULES:
        if any(hint in text for hint in hints):
            return section

    # Common generic operations can still be recognized structurally.
    if isinstance(node, (ast.For, ast.AsyncFor, ast.While)):
        return "Experiment execution"
    if isinstance(node, (ast.Try, ast.With, ast.AsyncWith)):
        return "Experiment execution"
    if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
        return "Experiment configuration"
    return "Experiment execution"


def _stable_cell_id(kind: str, source: str, index: int) -> str:
    digest = hashlib.sha1(f"{kind}:{index}:{source}".encode("utf-8")).hexdigest()[:8]
    return f"{kind}-{digest}"


def build_notebook_cells(source: str) -> list[Any]:
    """Split valid Python into semantic, ordered notebook sections."""
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return [
            nbformat.v4.new_markdown_cell(
                f"## Generated code — syntax validation failed\n\n"
                f"The original candidate is preserved below. Syntax error at line {exc.lineno}: {exc.msg}. "
                "Repair the Python source before executing this notebook."
            ),
            nbformat.v4.new_code_cell(source.rstrip() + "\n"),
        ]

    lines = source.splitlines(keepends=True)
    nodes = list(tree.body)
    if not nodes:
        return [nbformat.v4.new_markdown_cell("## Generated code\n\nNo executable Python was generated.")]

    # Build contiguous groups only. Never reorder nodes: dependencies and side
    # effects remain in precisely the same order as in the original script.
    groups: list[tuple[str, int, int]] = []
    previous_end = 0
    current_section: str | None = None
    group_start = group_end = None
    for node in nodes:
        start = max(0, getattr(node, "lineno", 1) - 1)
        end = getattr(node, "end_lineno", getattr(node, "lineno", 1))
        section = _semantic_section(node, _node_source(node, lines))
        if current_section is None:
            current_section, group_start, group_end = section, previous_end, end
        elif section == current_section and (start - int(group_end or 0)) <= 2:
            group_end = end
        else:
            groups.append((current_section, int(group_start), int(group_end)))
            current_section, group_start, group_end = section, previous_end, end
        previous_end = end
    groups.append((str(current_section), int(group_start), int(group_end)))

    cells: list[Any] = []
    for idx, (section, start, end) in enumerate(groups):
        code = "".join(lines[start:end]).strip("\n")
        if not code.strip():
            continue
        markdown = nbformat.v4.new_markdown_cell(
            f"## {section}\n\n{SECTION_GUIDES.get(section, 'Run this section in sequence; it preserves the generated program logic.')}"
        )
        markdown.metadata["tags"] = ["collab-cli-section"]
        markdown.id = _stable_cell_id("md", section, idx)
        code_cell = nbformat.v4.new_code_cell(code + "\n")
        code_cell.metadata["tags"] = ["collab-cli-generated", "collab-cli-execution-order"]
        code_cell.metadata["collab_cli"] = {"section": section, "source_order": idx}
        code_cell.id = _stable_cell_id("code", code, idx)
        cells.extend((markdown, code_cell))
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
        "collab_cli_agent": {
            "model": model, "status": status, "orchestrator": orchestrator,
            "notebook_layout": "semantic_multi_cell_v2",
            "execution_order_preserved": True,
            "generation_method": "python_ast_semantic_segmentation",
        },
    }
    intro = (
        "# Generated ML / Data Science Experiment\n\n"
        f"**Model:** `{model}`  \n**Orchestrator:** `{orchestrator}`  \n**Agent status:** `{status}`\n\n"
        "## How to use this notebook\n\n"
        "1. Select a Python 3 kernel and install any dependencies not already available.\n"
        "2. Run cells from top to bottom; cells preserve the original script's execution order.\n"
        "3. Inspect data checks and evaluation outputs before interpreting the results.\n"
        "4. Re-run the notebook from a clean kernel to verify reproducibility.\n\n"
        "> Generated from the agent's Python source. Code is grouped semantically without moving statements or changing their order."
    )
    intro_cell = nbformat.v4.new_markdown_cell(intro)
    intro_cell.id = "experiment-readme"
    intro_cell.metadata["tags"] = ["collab-cli-intro"]
    nb.cells = [intro_cell, *build_notebook_cells(source)]

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
