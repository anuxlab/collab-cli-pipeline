#!/usr/bin/env python3
"""Optional DSPy task planner backed by the repository's local Ollama model.

This is a structured planning aid, not a second model server. It uses Ollama's
OpenAI-compatible endpoint and fails open so the core LangGraph agent can run
without DSPy or a working planner call.
"""
from __future__ import annotations

from typing import Any


def build_task_plan(task: str, model: str, ollama_url: str, timeout: int = 120) -> dict[str, Any]:
    """Ask DSPy for concise requirements, an implementation plan and edge cases."""
    try:
        import dspy
    except ImportError as exc:
        return {"enabled": True, "status": "unavailable", "error": f"DSPy is not installed: {exc}"}

    class TaskPlanning(dspy.Signature):
        """Create an actionable implementation plan. Do not reveal private chain-of-thought."""
        task: str = dspy.InputField(desc="The exact programming task and its constraints")
        implementation_plan: str = dspy.OutputField(desc="Numbered, concise implementation steps")
        acceptance_criteria: str = dspy.OutputField(desc="Observable checks that define a correct solution")
        edge_cases: str = dspy.OutputField(desc="Important input, runtime, and boundary cases")

    try:
        base = ollama_url.rstrip("/")
        if not base.endswith("/v1"):
            base += "/v1"
        lm = dspy.LM(
            model=f"openai/{model}",
            api_base=base,
            api_key="ollama-local",
            timeout=timeout,
            temperature=0.1,
            max_tokens=700,
        )
        with dspy.context(lm=lm):
            prediction = dspy.Predict(TaskPlanning)(task=task)
        plan = {
            "enabled": True,
            "status": "success",
            "implementation_plan": str(prediction.implementation_plan).strip(),
            "acceptance_criteria": str(prediction.acceptance_criteria).strip(),
            "edge_cases": str(prediction.edge_cases).strip(),
            "backend": "local_ollama_openai_compatible",
            "model": model,
        }
        return plan
    except Exception as exc:  # planner failure must not prevent normal generation
        return {
            "enabled": True,
            "status": "failed_open",
            "error": f"{type(exc).__name__}: {str(exc)[:1200]}",
            "backend": "local_ollama_openai_compatible",
            "model": model,
        }


def format_task_plan(plan: dict[str, Any]) -> str:
    if plan.get("status") != "success":
        return "DSPy planning was requested but did not produce a plan. Continue with your own concise task analysis."
    return (
        "DSPy STRUCTURED TASK PLAN (planning aid; verify against the original task):\n"
        f"Implementation plan:\n{plan.get('implementation_plan', '')}\n\n"
        f"Acceptance criteria:\n{plan.get('acceptance_criteria', '')}\n\n"
        f"Edge cases:\n{plan.get('edge_cases', '')}\n\n"
        "Treat this as a checklist, not as a replacement for the user's requirements. "
        "Implement the complete solution and verify every acceptance criterion."
    )
