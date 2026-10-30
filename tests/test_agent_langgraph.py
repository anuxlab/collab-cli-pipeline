"""Unit tests for LangGraph orchestration nodes and bounded repair routing."""
import importlib.util
import sys
import types

# The test environment can validate graph node logic without installing the optional
# runtime package; GitHub workflows install LangGraph before executing the agent.
if importlib.util.find_spec("langgraph") is None:
    langgraph_pkg = types.ModuleType("langgraph")
    langgraph_pkg.__path__ = []
    graph_mod = types.ModuleType("langgraph.graph")
    graph_mod.START = "__start__"
    graph_mod.END = "__end__"

    class StubStateGraph:
        def __init__(self, state_type): self.state_type = state_type
        def add_node(self, *args, **kwargs): pass
        def add_edge(self, *args, **kwargs): pass
        def add_conditional_edges(self, *args, **kwargs): pass
        def compile(self): return self

    graph_mod.StateGraph = StubStateGraph
    sys.modules["langgraph"] = langgraph_pkg
    sys.modules["langgraph.graph"] = graph_mod

from scripts import agent_langgraph as agent


def test_route_continues_until_repair_budget_exhausted():
    assert agent.route_after_diagnosis({"status": "repairing", "attempt_index": 1, "max_repairs": 2}) == "continue"
    assert agent.route_after_diagnosis({"status": "repairing", "attempt_index": 2, "max_repairs": 2}) == "continue"
    assert agent.route_after_diagnosis({"status": "failed", "attempt_index": 3, "max_repairs": 2}) == "finish"
    assert agent.route_after_diagnosis({"status": "passed", "attempt_index": 1, "max_repairs": 2}) == "finish"


def test_diagnose_success_marks_state_passed():
    execution = {
        "returncode": 0,
        "stdout": '{"dataset":"demo","model":"test","accuracy":0.9,"precision":0.8,"recall":0.85,"f1":0.82,"test_samples":10}\n',
        "stderr": "", "duration_seconds": 0.1, "timed_out": False, "sandbox": "docker-network-disabled",
    }
    state = {
        "execution": execution, "attempt_index": 1, "max_repairs": 2,
        "attempts": [{"attempt": 0, "status": "pending"}], "graph_trace": [],
        "messages": [], "response": "print('metrics')", "code": "print('metrics')",
    }
    result = agent.node_diagnose_repair(state)
    assert result["status"] == "passed"
    assert result["validation_ok"] is True
    assert result["final_metrics"]["accuracy"] == 0.9
    assert result["graph_trace"][-1]["node"] == "diagnose_repair"


def test_diagnose_failure_builds_actionable_repair_feedback():
    execution = {
        "returncode": 1, "stdout": "", "stderr": "SyntaxError: invalid syntax",
        "duration_seconds": 0.1, "timed_out": False, "sandbox": "docker-network-disabled",
    }
    state = {
        "execution": execution, "attempt_index": 1, "max_repairs": 2,
        "attempts": [{"attempt": 0, "status": "pending"}], "graph_trace": [],
        "messages": [{"role": "user", "content": "task"}],
        "response": "```python\nbad syntax\n```", "code": "bad syntax\n",
    }
    result = agent.node_diagnose_repair(state)
    assert result["status"] == "repairing"
    assert result["validation_ok"] is False
    assert "SyntaxError" in result["messages"][-1]["content"]
    assert "complete Python script" in result["messages"][-1]["content"]


def test_generate_execute_records_model_failure(monkeypatch, tmp_path):
    def fail_model(*args, **kwargs):
        raise RuntimeError("Ollama unavailable")
    monkeypatch.setattr(agent, "call_model", fail_model)
    state = {
        "model": "local-model", "run_dir": str(tmp_path), "workdir": str(tmp_path),
        "messages": [], "attempt_index": 0, "max_repairs": 1,
        "execution_timeout": 10, "api_timeout": 10, "ollama_url": "http://127.0.0.1:11434",
        "attempts": [], "graph_trace": [],
    }
    result = agent.node_generate_execute(state)
    assert result["attempt_index"] == 1
    assert result["execution"]["returncode"] == 1
    assert "Ollama unavailable" in result["execution"]["stderr"]
    assert result["attempts"][0]["model_call_status"] == "failure"


def test_web_research_node_injects_references_and_records_trace(monkeypatch, tmp_path):
    fake_report = {
        "provider": "ddgs", "query": "python docs", "status": "success",
        "results": [{"title": "Python docs", "url": "https://docs.python.org", "snippet": "Official docs"}],
        "error": None,
    }
    monkeypatch.setattr(agent, "search_web", lambda *a, **k: fake_report)
    state = {
        "web_search_enabled": True, "web_query": "python docs", "run_dir": str(tmp_path),
        "messages": [{"role": "user", "content": "write code"}], "graph_trace": [],
    }
    result = agent.node_web_research(state)
    assert result["web_research"]["status"] == "success"
    assert "UNTRUSTED DATA" in result["messages"][-1]["content"]
    assert result["graph_trace"][-1]["node"] == "web_research"
    assert (tmp_path / "web_research.json").exists()


def test_web_research_disabled_is_non_blocking(tmp_path):
    state = {
        "web_search_enabled": False, "web_query": "", "run_dir": str(tmp_path),
        "messages": [{"role": "user", "content": "write code"}], "graph_trace": [],
    }
    result = agent.node_web_research(state)
    assert result["web_research"]["status"] == "skipped"
    assert len(result["messages"]) == 1


def test_extract_web_search_request_is_bounded_and_removed():
    query, remainder = agent.extract_web_search_request(
        "Need current API details. <WEB_SEARCH>  sklearn Pipeline latest docs  </WEB_SEARCH>"
    )
    assert query == "sklearn Pipeline latest docs"
    assert "WEB_SEARCH" not in remainder
    assert "Need current API details." in remainder


def test_model_can_autonomously_request_web_search(monkeypatch, tmp_path):
    responses = iter([
        "I need the current API. <WEB_SEARCH>scikit-learn Pipeline documentation</WEB_SEARCH>",
        "```python\nprint('{\"dataset\":\"demo\",\"model\":\"test\",\"accuracy\":0.9,\"precision\":0.9,\"recall\":0.9,\"f1\":0.9,\"test_samples\":10}')\n```",
    ])
    monkeypatch.setattr(agent, "call_model", lambda *a, **k: next(responses))
    monkeypatch.setattr(agent, "search_web", lambda *a, **k: {
        "provider": "ddgs", "query": "scikit-learn Pipeline documentation", "status": "success",
        "results": [{"title": "Official docs", "url": "https://scikit-learn.org/", "snippet": "Pipeline API"}],
        "error": None,
    })
    monkeypatch.setattr(agent, "execute_code", lambda *a, **k: {
        "returncode": 0, "stdout": "{}", "stderr": "", "duration_seconds": 0.01,
        "timed_out": False, "sandbox": "test",
    })
    state = {
        "model": "test-model", "run_dir": str(tmp_path), "workdir": str(tmp_path),
        "messages": [{"role": "user", "content": "Build a model"}], "attempt_index": 0,
        "max_repairs": 5, "execution_timeout": 10, "api_timeout": 10,
        "ollama_url": "http://127.0.0.1:11434", "attempts": [], "graph_trace": [],
        "web_search_enabled": True, "web_search_count": 0,
    }
    result = agent.node_generate_execute(state)
    assert result["web_search_count"] == 1
    assert result["attempts"][0]["web_searches"][0]["status"] == "success"
    assert any(item["node"] == "agent_web_search_tool" for item in result["graph_trace"])


def test_five_repairs_allow_six_total_generation_attempts():
    assert agent.route_after_diagnosis({"status": "repairing", "attempt_index": 5, "max_repairs": 5}) == "continue"
    assert agent.route_after_diagnosis({"status": "failed", "attempt_index": 6, "max_repairs": 5}) == "finish"


def test_dspy_plan_formatter_adds_structured_checklist():
    from scripts.dspy_planner import format_task_plan
    rendered = format_task_plan({
        "status": "success",
        "implementation_plan": "1. Load data\n2. Train model",
        "acceptance_criteria": "Print accuracy JSON",
        "edge_cases": "Empty input; missing values",
    })
    assert "Implementation plan" in rendered
    assert "Acceptance criteria" in rendered
    assert "Empty input" in rendered
    assert "verify every acceptance criterion" in rendered


def test_dspy_planner_fails_open_when_package_missing(monkeypatch):
    import builtins
    from scripts import dspy_planner
    original_import = builtins.__import__

    def blocked_import(name, *args, **kwargs):
        if name == "dspy":
            raise ImportError("intentionally unavailable")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked_import)
    result = dspy_planner.build_task_plan("task", "model", "http://localhost:11434")
    assert result["status"] == "unavailable"
    assert "not installed" in result["error"]
