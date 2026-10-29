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
