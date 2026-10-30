import json
from pathlib import Path

import nbformat

from scripts.notebook_benchmark import TASKS, score_task
from scripts.notebook_builder import create_generated_notebook


def test_benchmark_spans_increasingly_complex_distinct_domains():
    assert len(TASKS) >= 7
    assert TASKS[0]["level"] == "1-simple"
    assert TASKS[-1]["level"] == "7-optimization"
    titles = {task["title"] for task in TASKS}
    assert len(titles) == len(TASKS)
    assert any("time-series" in task["title"].lower() for task in TASKS)
    assert any("nlp" in task["level"].lower() for task in TASKS)
    assert any("optimization" in task["level"].lower() for task in TASKS)


def test_benchmark_score_checks_execution_result_rubric_and_notebook_integrity(tmp_path):
    task = TASKS[0]
    source = '''import json
from statistics import mean, median, pvariance
values = [4, 7, 7, 10, 12, 14, 18]
assert len(values) == 7
result = {"task_id": "01_python_fundamentals", "count": len(values), "mean": mean(values), "median": median(values), "variance": pvariance(values), "min": min(values), "max": max(values)}
print("BENCHMARK_RESULT=" + json.dumps(result))
'''
    output = tmp_path / "notebook.ipynb"
    execution = {"returncode": 0, "timed_out": False,
                 "stdout": 'BENCHMARK_RESULT=' + json.dumps({"task_id": task["id"]})}
    create_generated_notebook(source, output, model="test", status="passed", orchestrator="test", execution=execution)
    score = score_task(task, source, execution, output)
    assert score["execution_ok"] is True
    assert score["task_result_ok"] is True
    assert score["source_reconstruction_ok"] is True
    assert score["rubric_hits"] == task["rubric"]
    assert score["score"] >= 75


def test_benchmark_does_not_accept_wrong_task_id(tmp_path):
    task = TASKS[0]
    source = "import statistics\nprint('hello')\n"
    output = tmp_path / "notebook.ipynb"
    create_generated_notebook(source, output, model="test", status="passed", orchestrator="test")
    score = score_task(task, source, {"returncode": 0, "stdout": 'BENCHMARK_RESULT={"task_id":"wrong"}'}, output)
    assert score["task_result_ok"] is False


def test_model_similarity_flags_near_identical_code():
    from scripts.compare_notebook_benchmarks import similarity
    first = "import pandas as pd\ndf = pd.read_csv('data.csv')\nprint(df.describe())\n"
    second = "import pandas as pd\ndf=pd.read_csv('data.csv')\nprint(df.describe())\n"
    different = "from itertools import combinations\nprint(list(combinations(range(8), 2)))\n"
    assert similarity(first, second) > 0.85
    assert similarity(first, different) < similarity(first, second)
