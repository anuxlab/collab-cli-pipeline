import subprocess, sys
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "scripts" / "resolve_experiment_profile.py"

def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *args], text=True, capture_output=True)

def test_small_profile():
    r=run("--profile","small")
    assert r.returncode == 0
    assert "'repairs': 0" in r.stdout and "'num_predict': 384" in r.stdout

def test_medium_profile():
    r=run("--profile","medium")
    assert r.returncode == 0
    assert "'num_ctx': 1536" in r.stdout and "'repairs': 1" in r.stdout

def test_max_profile():
    r=run("--profile","max")
    assert r.returncode == 0
    assert "'task_ids': ''" in r.stdout and "'repairs': 2" in r.stdout

def test_override_applies_to_profile():
    r=run("--profile","small","--num-predict","512","--repairs","1")
    assert r.returncode == 0
    assert "'num_predict': 512" in r.stdout and "'repairs': 1" in r.stdout

def test_rejects_unreasonable_context():
    r=run("--profile","small","--num-ctx","99999")
    assert r.returncode != 0


def test_task_ids_override_profile():
    r=run("--profile","small","--task-ids","03_classification")
    assert r.returncode == 0
    assert "'task_ids': '03_classification'" in r.stdout

def test_repair_override_profile():
    r=run("--profile","small","--repairs","2")
    assert r.returncode == 0
    assert "'repairs': 2" in r.stdout
