import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from run_benchmark import datasets_for_suite, models_for_suite

def test_smoke_suite_has_iris_only():
    data = datasets_for_suite("smoke")
    assert [name for name, _ in data] == ["iris"]

def test_extended_suite_has_three_datasets():
    data = datasets_for_suite("extended")
    assert {name for name, _ in data} == {"iris", "wine", "breast_cancer"}

def test_four_models_are_available():
    models = models_for_suite("extended")
    assert len(models) == 4
    assert "LogisticRegression" in models
    assert "RandomForest" in models
    assert "SVC_RBF" in models
    assert "HistGradientBoosting" in models
