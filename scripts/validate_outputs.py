"""Fail fast when the benchmark's required artifacts are absent or malformed."""
import json
from pathlib import Path

import nbformat
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"

def validate():
    required = [
        OUT / "benchmark_summary.json",
        OUT / "benchmark_details.json",
        OUT / "benchmark_metrics.csv",
        OUT / "f1_comparison.png",
        OUT / "cv_accuracy_comparison.png",
    ]
    missing = [str(p.relative_to(ROOT)) for p in required if not p.is_file() or p.stat().st_size == 0]
    if missing:
        raise SystemExit(f"Missing/empty required outputs: {missing}")
    summary = json.loads((OUT / "benchmark_summary.json").read_text())
    metrics = pd.read_csv(OUT / "benchmark_metrics.csv")
    if summary.get("status") != "success":
        raise SystemExit("Summary status is not success")
    if metrics.empty or metrics[["accuracy", "f1_weighted", "cv_accuracy_mean"]].isna().any().any():
        raise SystemExit("Metrics are empty or contain NaN in required columns")
    for column in ["accuracy", "f1_weighted", "cv_accuracy_mean"]:
        if not metrics[column].between(0, 1).all():
            raise SystemExit(f"Metric out of [0,1] bounds: {column}")
    for executed in [
        ROOT / "notebooks" / "ml_pipeline_executed.ipynb",
        ROOT / "notebooks" / "experiment_report_executed.ipynb",
    ]:
        if executed.exists():
            nb = nbformat.read(executed, as_version=4)
            errors = [
                (i, output.get("ename"), output.get("evalue"))
                for i, cell in enumerate(nb.cells)
                for output in cell.get("outputs", [])
                if output.output_type == "error"
            ]
            if errors:
                raise SystemExit(f"Notebook {executed.name} contains execution errors: {errors}")
    # Validate the original Iris pipeline outputs too, when present.
    legacy_summary = OUT / "ml_summary.json"
    legacy_features = OUT / "feature_importance.csv"
    if legacy_summary.exists():
        legacy = json.loads(legacy_summary.read_text())
        if not isinstance(legacy.get("test_accuracy"), (int, float)) or not 0 <= legacy["test_accuracy"] <= 1:
            raise SystemExit("Legacy ML summary has invalid accuracy")
    if legacy_features.exists() and pd.read_csv(legacy_features).empty:
        raise SystemExit("Legacy feature-importance output is empty")
    print(json.dumps({
        "validation": "passed",
        "experiment_count": int(len(metrics)),
        "datasets": sorted(metrics.dataset.unique().tolist()),
        "models": sorted(metrics.model.unique().tolist()),
        "summary": summary,
    }, indent=2))

if __name__ == "__main__":
    validate()
