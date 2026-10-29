import json
from pathlib import Path

from scripts.agent_experiment import extract_code, execute_code, validate_execution


def test_extract_python_fence():
    assert extract_code("```python\nprint('ok')\n```") == "print('ok')\n"


def test_valid_metrics_pass():
    execution = {
        "returncode": 0,
        "stdout": '{"dataset":"demo","model":"test","accuracy":0.9,"precision":0.8,"recall":0.85,"f1":0.82,"test_samples":10}\n',
        "stderr": "", "duration_seconds": 0.1, "timed_out": False,
    }
    ok, reason, metrics = validate_execution(execution)
    assert ok is True
    assert reason == "passed"
    assert metrics["test_samples"] == 10


def test_invalid_metric_fails():
    execution = {
        "returncode": 0,
        "stdout": json.dumps({"dataset":"demo","model":"test","accuracy":1.4,"precision":0.8,"recall":0.85,"f1":0.82,"test_samples":10}),
        "stderr": "", "duration_seconds": 0.1, "timed_out": False,
    }
    ok, reason, _ = validate_execution(execution)
    assert ok is False
    assert reason == "metric_out_of_range"


def test_execution_does_not_inherit_token(tmp_path, monkeypatch):
    monkeypatch.setenv("HF_TOKEN", "test-secret-not-to-pass")
    result = execute_code("import os; print('token=' + str('HF_TOKEN' in os.environ))", tmp_path, 10)
    assert result["returncode"] == 0
    assert "token=False" in result["stdout"]


def test_comparison_report_collects_saved_summaries(tmp_path, monkeypatch):
    from scripts import compare_agent_runs

    runs = tmp_path / "agent_runs"
    one = runs / "run-a"
    one.mkdir(parents=True)
    (one / "summary.json").write_text(json.dumps({
        "model": "test/model", "status": "passed", "attempts_used": 2, "max_repairs": 2,
        "metrics": {"accuracy": 0.9, "precision": 0.9, "recall": 0.9, "f1": 0.9, "test_samples": 40},
        "final_execution": {"duration_seconds": 1.2}, "started_at_utc": "start", "finished_at_utc": "end",
    }))
    monkeypatch.setattr(compare_agent_runs, "RUNS", runs)
    rows = compare_agent_runs.collect_rows()
    assert len(rows) == 1
    assert rows[0]["model"] == "test/model"
    assert rows[0]["accuracy"] == 0.9
