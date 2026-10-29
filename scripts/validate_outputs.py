from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
summary_path = ROOT / "outputs" / "ml_summary.json"
executed_notebook = ROOT / "notebooks" / "ml_pipeline_executed.ipynb"

if not summary_path.exists():
    raise SystemExit(f"Missing expected output: {summary_path}")
if not executed_notebook.exists():
    raise SystemExit(f"Missing executed notebook: {executed_notebook}")

summary = json.loads(summary_path.read_text(encoding="utf-8"))
required = {"status", "dataset", "test_accuracy", "n_train", "n_test", "run_utc"}
missing = required - summary.keys()
if missing:
    raise SystemExit(f"Summary missing keys: {sorted(missing)}")
if summary["status"] != "success":
    raise SystemExit(f"ML run did not succeed: {summary['status']}")
if not 0 <= float(summary["test_accuracy"]) <= 1:
    raise SystemExit("test_accuracy must be between 0 and 1")

notebook = json.loads(executed_notebook.read_text(encoding="utf-8"))
errors = [
    (cell_index, output.get("ename"), output.get("evalue"))
    for cell_index, cell in enumerate(notebook.get("cells", []))
    for output in cell.get("outputs", [])
    if output.get("output_type") == "error"
]
if errors:
    raise SystemExit(f"Notebook contains execution errors: {errors}")
print(json.dumps({"validation": "passed", "summary": summary}, indent=2))
