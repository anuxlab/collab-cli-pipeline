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


def test_local_ollama_chat_request(monkeypatch):
    from scripts import agent_experiment

    class FakeResponse:
        ok = True
        def json(self):
            return {"message": {"content": "print('local')"}}

    captured = {}
    def fake_post(url, json, timeout):
        captured.update(url=url, body=json, timeout=timeout)
        return FakeResponse()

    monkeypatch.setattr(agent_experiment.requests, "post", fake_post)
    result = agent_experiment.call_model(
        "qwen2.5-coder:3b", [{"role": "user", "content": "write code"}], 42,
        "http://127.0.0.1:11434/",
    )
    assert result == "print('local')"
    assert captured["url"] == "http://127.0.0.1:11434/api/chat"
    assert captured["body"]["model"] == "qwen2.5-coder:3b"
    assert captured["body"]["stream"] is False
    assert captured["body"]["options"]["num_ctx"] == 2048
    assert captured["body"]["options"]["num_predict"] == 1200
    assert captured["body"]["options"]["num_batch"] == 16


def test_pretty_printed_multiline_json_is_accepted():
    payload = {
        "dataset": "breast_cancer", "model": "LogisticRegression",
        "accuracy": 0.986013986013986, "precision": 0.9888888888888889,
        "recall": 0.9888888888888889, "f1": 0.9888888888888889,
        "test_samples": 143,
    }
    execution = {
        "returncode": 0, "stdout": "training complete\n" + json.dumps(payload, indent=2) + "\n",
        "stderr": "", "duration_seconds": 0.1, "timed_out": False,
    }
    ok, reason, metrics = validate_execution(execution)
    assert ok is True
    assert reason == "passed"
    assert metrics["test_samples"] == 143


def test_json_object_after_logs_and_nested_braces_is_accepted():
    payload = {
        "dataset": "demo", "model": "test", "accuracy": 0.9,
        "precision": 0.8, "recall": 0.85, "f1": 0.82,
        "test_samples": 10, "metadata": {"note": "brace } inside string"},
    }
    execution = {
        "returncode": 0, "stdout": "INFO: training finished\nRESULTS:\n" + json.dumps(payload, indent=2),
        "stderr": "", "duration_seconds": 0.1, "timed_out": False,
    }
    ok, reason, metrics = validate_execution(execution)
    assert ok is True
    assert reason == "passed"
    assert metrics["accuracy"] == 0.9


def test_docker_infrastructure_errors_are_classified_without_code_repair():
    from scripts.agent_experiment import _is_docker_infrastructure_error
    assert _is_docker_infrastructure_error("docker: failed to create the container ID file: no such file")
    assert _is_docker_infrastructure_error("Cannot connect to the Docker daemon")
    assert not _is_docker_infrastructure_error("Traceback: ValueError: invalid input")


def test_docker_cidfile_uses_absolute_existing_parent(tmp_path, monkeypatch):
    from scripts import agent_experiment
    import os
    monkeypatch.setenv("AGENT_USE_DOCKER", "1")
    monkeypatch.setenv("AGENT_SANDBOX_IMAGE", "test-image")
    captured = {}
    class Result:
        returncode = 0
        stdout = "ok"
        stderr = ""
    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["cwd"] = kwargs["cwd"]
        cid = Path(command[command.index("--cidfile") + 1])
        captured["cidfile"] = cid
        assert cid.is_absolute()
        assert cid.parent.is_dir()
        cid.write_text("container-id")
        return Result()
    monkeypatch.setattr(agent_experiment.subprocess, "run", fake_run)
    monkeypatch.setattr(agent_experiment.os, "getuid", lambda: 1000)
    monkeypatch.setattr(agent_experiment.os, "getgid", lambda: 1000)
    result = agent_experiment.execute_code("print('ok')", tmp_path, 10)
    assert result["returncode"] == 0
    assert captured["cwd"] == tmp_path.resolve()
    assert not captured["cidfile"].exists()
