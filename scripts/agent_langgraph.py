#!/usr/bin/env python3
"""LangGraph-orchestrated local-Ollama generate/execute/diagnose/repair agent.

The graph coordinates bounded attempts. Model inference stays on the local Ollama
daemon; generated code executes only in the Docker sandbox configured by the workflow.
"""
from __future__ import annotations

import argparse
import difflib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TypedDict

import nbformat
from langgraph.graph import END, START, StateGraph

try:
    # Package import is used by pytest; script-directory import supports direct workflow execution.
    from scripts.agent_experiment import (
        DEFAULT_OLLAMA_URL, DEFAULT_TASK, call_model, execute_code, extract_code, validate_execution
    )
except ModuleNotFoundError:
    from agent_experiment import (
        DEFAULT_OLLAMA_URL, DEFAULT_TASK, call_model, execute_code, extract_code, validate_execution
    )


class AgentState(TypedDict, total=False):
    model: str
    run_dir: str
    workdir: str
    messages: list[dict[str, str]]
    attempt_index: int
    max_repairs: int
    execution_timeout: int
    api_timeout: int
    ollama_url: str
    response: str
    code: str
    execution: dict[str, Any]
    validation_ok: bool
    validation_reason: str
    metrics: dict[str, Any] | None
    status: str
    error: str
    attempts: list[dict[str, Any]]
    graph_trace: list[dict[str, Any]]
    initial_code: str
    final_execution: dict[str, Any]
    final_metrics: dict[str, Any] | None
    final_error: str


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def node_generate_execute(state: AgentState) -> dict[str, Any]:
    """Generate one candidate and execute it in the configured sandbox."""
    attempt = int(state.get("attempt_index", 0))
    started = utc_now()
    tick = time.monotonic()
    record: dict[str, Any] = {
        "attempt": attempt,
        "started_at_utc": started,
        "orchestrator": "langgraph",
    }
    response = ""
    code = ""
    execution: dict[str, Any] = {}
    try:
        response = call_model(
            state["model"], state["messages"], int(state["api_timeout"]), state["ollama_url"]
        )
        code = extract_code(response)
        run_dir = Path(state["run_dir"])
        (run_dir / f"generated_attempt_{attempt}.py").write_text(code, encoding="utf-8")
        execution = execute_code(code, Path(state["workdir"]), int(state["execution_timeout"]))
        record.update({
            "model_call_status": "success",
            "model_call_seconds": round(time.monotonic() - tick, 3),
            "execution": execution,
            "candidate_file": f"generated_attempt_{attempt}.py",
        })
        if attempt == 0:
            (run_dir / "initial_solution.py").write_text(code, encoding="utf-8")
    except Exception as exc:
        record.update({
            "model_call_status": "failure",
            "error": f"{type(exc).__name__}: {str(exc)[:3000]}",
            "model_call_seconds": round(time.monotonic() - tick, 3),
        })
        execution = {
            "returncode": 1,
            "stdout": "",
            "stderr": record["error"],
            "duration_seconds": 0.0,
            "timed_out": False,
            "sandbox": "not_started",
        }
        record["execution"] = execution
    record["finished_at_utc"] = utc_now()
    trace = list(state.get("graph_trace", []))
    trace.append({
        "node": "generate_execute",
        "attempt": attempt,
        "timestamp_utc": utc_now(),
        "model_call_status": record.get("model_call_status"),
        "execution_returncode": execution.get("returncode"),
    })
    return {
        "response": response,
        "code": code,
        "execution": execution,
        "attempt_index": attempt + 1,
        "attempts": list(state.get("attempts", [])) + [record],
        "graph_trace": trace,
        "initial_code": state.get("initial_code", code if attempt == 0 else ""),
    }


def node_diagnose_repair(state: AgentState) -> dict[str, Any]:
    """Validate execution and prepare specific feedback for the next graph iteration."""
    execution = state.get("execution", {})
    try:
        ok, reason, metrics = validate_execution(execution)
    except Exception as exc:
        ok, reason, metrics = False, "validator_exception", None
        validation_error = f"{type(exc).__name__}: {exc}"
    else:
        validation_error = ""

    attempts = list(state.get("attempts", []))
    if attempts:
        attempts[-1]["validation"] = reason
        attempts[-1]["status"] = "passed" if ok else "failed"
        attempts[-1]["metrics"] = metrics
        if validation_error:
            attempts[-1]["validation_error"] = validation_error

    trace = list(state.get("graph_trace", []))
    trace.append({
        "node": "diagnose_repair",
        "attempt": max(0, int(state.get("attempt_index", 1)) - 1),
        "timestamp_utc": utc_now(),
        "validation": reason,
        "passed": ok,
    })

    if ok:
        return {
            "validation_ok": True,
            "validation_reason": reason,
            "metrics": metrics,
            "status": "passed",
            "attempts": attempts,
            "graph_trace": trace,
            "final_execution": execution,
            "final_metrics": metrics,
        }

    messages = list(state.get("messages", []))
    response = state.get("response", "")
    code = state.get("code", "")
    diagnostic = (
        f"Attempt {state.get('attempt_index', 1)} failed validation.\n"
        f"Failure class: {reason}\n"
        f"Return code: {execution.get('returncode')}\n"
        f"Timed out: {execution.get('timed_out')}\n"
        f"Sandbox: {execution.get('sandbox')}\n"
        f"STDOUT (tail):\n{execution.get('stdout', '')[-6000:]}\n"
        f"STDERR (tail):\n{execution.get('stderr', '')[-6000:]}\n"
        "Repair the complete Python script. Address the specific error, keep the task requirements, "
        "and print exactly one final JSON object with the required metrics. Return executable Python only."
    )
    if response:
        messages.append({"role": "assistant", "content": response})
    elif code:
        messages.append({"role": "assistant", "content": code})
    messages.append({"role": "user", "content": diagnostic})

    exhausted = int(state.get("attempt_index", 1)) > int(state.get("max_repairs", 2))
    status = "failed" if exhausted else "repairing"
    return {
        "validation_ok": False,
        "validation_reason": reason,
        "metrics": metrics,
        "status": status,
        "messages": messages,
        "attempts": attempts,
        "graph_trace": trace,
        "final_execution": execution,
        "final_metrics": metrics,
        "final_error": reason if exhausted else "",
    }


def route_after_diagnosis(state: AgentState) -> str:
    if state.get("status") == "passed":
        return "finish"
    if int(state.get("attempt_index", 0)) > int(state.get("max_repairs", 2)):
        return "finish"
    return "continue"


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("generate_execute", node_generate_execute)
    graph.add_node("diagnose_repair", node_diagnose_repair)
    graph.add_edge(START, "generate_execute")
    graph.add_edge("generate_execute", "diagnose_repair")
    graph.add_conditional_edges(
        "diagnose_repair",
        route_after_diagnosis,
        {"continue": "generate_execute", "finish": END},
    )
    return graph.compile()


def write_outputs(state: AgentState, args: argparse.Namespace) -> None:
    run_dir = Path(args.run_dir).resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    attempts = list(state.get("attempts", []))
    execution = state.get("final_execution", {})
    status = state.get("status", "failed")
    initial_code = state.get("initial_code", "")
    final_code = state.get("code", "")

    if status == "passed" and final_code:
        (run_dir / "generated_solution.py").write_text(final_code, encoding="utf-8")
    elif final_code and not (run_dir / "last_candidate.py").exists():
        (run_dir / "last_candidate.py").write_text(final_code, encoding="utf-8")

    if initial_code:
        (run_dir / "initial_solution.py").write_text(initial_code, encoding="utf-8")

    for record in attempts:
        idx = record.get("attempt", 0)
        ex = record.get("execution", {})
        (run_dir / f"stdout_attempt_{idx}.txt").write_text(ex.get("stdout", ""), encoding="utf-8")
        (run_dir / f"stderr_attempt_{idx}.txt").write_text(ex.get("stderr", record.get("error", "")), encoding="utf-8")

    nb_code = final_code or initial_code or "# No code was generated successfully.\n"
    nb = nbformat.v4.new_notebook()
    nb.metadata = {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "collab_cli_agent": {
            "model": args.model,
            "status": status,
            "orchestrator": "LangGraph",
        },
    }
    cell = nbformat.v4.new_code_cell(nb_code)
    if execution:
        cell.execution_count = 1
        cell.outputs = []
        if execution.get("stdout"):
            cell.outputs.append(nbformat.v4.new_output("stream", name="stdout", text=execution["stdout"]))
        if execution.get("stderr"):
            cell.outputs.append(nbformat.v4.new_output("stream", name="stderr", text=execution["stderr"]))
        if execution.get("returncode", 1) != 0:
            cell.outputs.append(nbformat.v4.new_output(
                "error", ename="ExecutionError",
                evalue=f"Process returned {execution.get('returncode')}", traceback=[]
            ))
    nb.cells = [
        nbformat.v4.new_markdown_cell(
            f"# AI-generated ML experiment\n\nModel: `{args.model}`\n\n"
            f"Orchestrator: **LangGraph**\n\nStatus: **{status}**"
        ),
        cell,
    ]
    nbformat.write(nb, run_dir / "generated_notebook.ipynb")

    if initial_code and final_code:
        diff = difflib.unified_diff(
            initial_code.splitlines(True), final_code.splitlines(True),
            fromfile="initial_solution.py", tofile="final_solution.py"
        )
        (run_dir / "repair.patch").write_text("".join(diff), encoding="utf-8")
    elif not (run_dir / "repair.patch").exists():
        (run_dir / "repair.patch").write_text("# No successful repair patch was produced.\n", encoding="utf-8")

    summary = {
        "experiment": "ai_notebook_code_repair",
        "model": args.model,
        "inference_backend": "local_ollama",
        "orchestrator": "langgraph",
        "ollama_url": args.ollama_url,
        "status": status,
        "max_repairs": args.max_repairs,
        "attempts_used": len(attempts),
        "started_at_utc": attempts[0].get("started_at_utc") if attempts else utc_now(),
        "finished_at_utc": utc_now(),
        "metrics": state.get("final_metrics"),
        "final_execution": execution,
        "final_validation": state.get("validation_reason"),
        "final_error": state.get("final_error", ""),
        "safety_note": (
            "Workflow runs use a Docker container with networking disabled, resource limits, "
            "read-only root filesystem, and no credentials. Local fallback execution is not hardened."
        ),
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (run_dir / "audit.json").write_text(json.dumps(attempts, indent=2), encoding="utf-8")
    (run_dir / "graph_trace.json").write_text(json.dumps(state.get("graph_trace", []), indent=2), encoding="utf-8")
    print(json.dumps({
        "status": status, "model": args.model, "orchestrator": "langgraph",
        "attempts_used": len(attempts), "run_dir": str(run_dir),
    }, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--max-repairs", type=int, default=2)
    parser.add_argument("--execution-timeout", type=int, default=60)
    parser.add_argument("--api-timeout", "--model-timeout", dest="api_timeout", type=int, default=300)
    parser.add_argument("--ollama-url", default=os.environ.get("OLLAMA_BASE_URL", DEFAULT_OLLAMA_URL))
    args = parser.parse_args()
    if not 0 <= args.max_repairs <= 2:
        print("--max-repairs must be between 0 and 2", file=sys.stderr)
        return 2

    run_dir = Path(args.run_dir).resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    workdir = run_dir / "execution_workspace"
    workdir.mkdir(exist_ok=True)
    (workdir / "README.txt").write_text("Temporary workspace for generated code.\n", encoding="utf-8")

    initial_state: AgentState = {
        "model": args.model,
        "run_dir": str(run_dir),
        "workdir": str(workdir),
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a careful Python coding agent. Return executable Python code only. "
                    "Follow the task exactly, avoid network/filesystem access outside the working directory, "
                    "and keep the solution concise."
                ),
            },
            {"role": "user", "content": DEFAULT_TASK},
        ],
        "attempt_index": 0,
        "max_repairs": args.max_repairs,
        "execution_timeout": args.execution_timeout,
        "api_timeout": args.api_timeout,
        "ollama_url": args.ollama_url,
        "attempts": [],
        "graph_trace": [],
        "status": "running",
        "initial_code": "",
        "final_execution": {},
        "final_metrics": None,
    }

    try:
        graph = build_graph()
        final_state = graph.invoke(initial_state, config={"recursion_limit": 20})
    except Exception as exc:
        final_state = dict(initial_state)
        final_state["status"] = "failed"
        final_state["final_error"] = f"LangGraph orchestration error: {type(exc).__name__}: {exc}"
        final_state["graph_trace"] = list(initial_state.get("graph_trace", [])) + [{
            "node": "graph_runtime", "timestamp_utc": utc_now(),
            "error": final_state["final_error"],
        }]
    write_outputs(final_state, args)
    return 0 if final_state.get("status") == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
