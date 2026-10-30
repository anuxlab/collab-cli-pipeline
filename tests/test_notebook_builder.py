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
    assert notebook.metadata.collab_cli_agent.notebook_layout == "semantic_multi_cell_v2"
    assert len([cell for cell in notebook.cells if cell.cell_type == "code"]) >= 2
    assert notebook.cells[-1].outputs[0].text == '{"value": 42}\n'


def test_invalid_python_is_preserved_in_single_diagnostic_cell():
    cells = build_notebook_cells("def broken(:\n    pass\n")
    assert cells[0].cell_type == "markdown"
    assert cells[1].cell_type == "code"
    assert "def broken(:" in cells[1].source


def test_ml_workflow_gets_meaningful_semantic_sections_in_source_order():
    source = '''import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

RANDOM_STATE = 42

# Load data
df = pd.read_csv("data.csv")

# Explore data
print(df.head())
print(df.describe())

# Validate data
assert not df.empty

# Preprocess features
X = df.drop(columns=["target"])
y = df["target"]
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Split data
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, random_state=RANDOM_STATE)

# Train model
model = LogisticRegression()
model.fit(X_train, y_train)

# Predict and evaluate
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(accuracy)
'''
    cells = build_notebook_cells(source)
    headings = [c.source.splitlines()[0].removeprefix("## ") for c in cells if c.cell_type == "markdown"]
    expected = [
        "Environment and imports", "Experiment configuration", "Data acquisition",
        "Data inspection and exploratory analysis", "Data validation and quality checks",
        "Feature engineering and preprocessing", "Train-test split and cross-validation",
        "Model definition and initialization", "Model training", "Prediction and inference",
        "Evaluation and metrics",
    ]
    positions = [headings.index(h) for h in expected]
    assert positions == sorted(positions)
    # Every generated code cell must retain its relative order in the source.
    joined = "\n".join(c.source for c in cells if c.cell_type == "code")
    assert joined.index('pd.read_csv("data.csv")') < joined.index("train_test_split(")
    assert joined.index("model.fit(") < joined.index("model.predict(")


def test_cells_have_stable_ids_and_semantic_metadata():
    source = "import math\nvalue = math.sqrt(9)\nprint(value)\n"
    first = build_notebook_cells(source)
    second = build_notebook_cells(source)
    assert [c.id for c in first] == [c.id for c in second]
    code_cells = [c for c in first if c.cell_type == "code"]
    assert code_cells
    assert code_cells[0].metadata.collab_cli.section == "Environment and imports"


def test_time_series_notebook_gets_temporal_specific_sections():
    source = '''import numpy as np
from sklearn.linear_model import LinearRegression
series = np.arange(200, dtype=float)
lag_features = series[:-1]
rolling_mean = np.convolve(series, np.ones(7) / 7, mode="valid")
forecast = LinearRegression()
forecast_error = 2.4
rmse = 1.2
'''
    cells = build_notebook_cells(source)
    headings = [c.source.splitlines()[0] for c in cells if c.cell_type == "markdown"]
    assert any("Temporal feature engineering" in h for h in headings)
    assert any("Forecasting and temporal baselines" in h for h in headings)


def test_nlp_notebook_gets_text_specific_sections():
    source = '''from sklearn.feature_extraction.text import TfidfVectorizer
vectorizer = TfidfVectorizer(ngram_range=(1, 2))
X_text = vectorizer.fit_transform(texts)
sentiment_predictions = classifier.predict(X_text)
'''
    headings = [c.source.splitlines()[0] for c in build_notebook_cells(source) if c.cell_type == "markdown"]
    assert any("Text preprocessing and vectorization" in h for h in headings)
    assert any("Text classification and error analysis" in h for h in headings)


def test_optimization_notebook_gets_problem_and_solution_sections():
    source = '''capacity = 20
knapsack_value = 0
optimal_value = 42
is_feasible = True
assert is_feasible
'''
    headings = [c.source.splitlines()[0] for c in build_notebook_cells(source) if c.cell_type == "markdown"]
    assert any("Optimization problem formulation" in h for h in headings)
    assert any("Solution verification" in h for h in headings)
