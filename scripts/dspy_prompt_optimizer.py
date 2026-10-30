#!/usr/bin/env python3
"""Low-cost DSPy few-shot prompt optimization for notebook planning.

Uses the same local Ollama model. It optimizes a compact planning module using
rubric-grounded task examples, then emits per-task design guidance. This is an
experimental optimizer: scores must be compared on held-out tasks before treating
an optimized prompt as an improvement.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any


def optimize_notebook_prompts(training_tasks: list[dict[str, Any]], target_tasks: list[dict[str, Any]], model: str, ollama_url: str,
                              output_path: str | Path, timeout: int = 180) -> dict[str, Any]:
    try:
        import dspy
    except ImportError as exc:
        return {"status":"unavailable","error":f"DSPy is not installed: {exc}","guidance":{}}

    base=ollama_url.rstrip("/")
    if not base.endswith("/v1"): base += "/v1"
    try:
        lm=dspy.LM(model=f"openai/{model}",api_base=base,api_key="ollama-local",timeout=timeout,
                    temperature=0.15,max_tokens=500)
        class NotebookPlanning(dspy.Signature):
            """Design a task-specific analytical notebook; avoid generic notebook templates."""
            task_prompt: str=dspy.InputField(desc="Exact notebook task")
            rubric: str=dspy.InputField(desc="Observable task-specific quality criteria")
            design_strategy: str=dspy.OutputField(desc="A concise, task-specific notebook architecture and analytical choices")
            validation_plan: str=dspy.OutputField(desc="Concrete assertions, checks and execution evidence")
            differentiation: str=dspy.OutputField(desc="What makes this analysis specific to this task rather than a generic template")

        class NotebookPlanner(dspy.Module):
            def __init__(self):
                super().__init__(); self.plan=dspy.Predict(NotebookPlanning)
            def forward(self,task_prompt,rubric):
                return self.plan(task_prompt=task_prompt,rubric=rubric)

        def metric(example,prediction,trace=None):
            text=" ".join(str(getattr(prediction,k,"")) for k in ("design_strategy","validation_plan","differentiation")).lower()
            terms=[x.strip().lower() for x in str(example.rubric).split(",") if x.strip()]
            coverage=sum(term in text for term in terms)/max(1,len(terms))
            structure=sum(bool(str(getattr(prediction,k," ")).strip()) for k in ("design_strategy","validation_plan","differentiation"))/3
            specificity=1.0 if len(str(getattr(prediction,"differentiation","")))>=45 else 0.0
            return 0.55*coverage+0.30*structure+0.15*specificity

        # Rubric-grounded labels seed the bootstrap optimizer; the metric independently
        # checks that proposed plans address task criteria and contain all three fields.
        train=[]
        for task in training_tasks:
            rubric=", ".join(task.get("rubric",[]))
            train.append(dspy.Example(task_prompt=task["prompt"],rubric=rubric,
                design_strategy=f"Build a workflow specific to {task['title']}; organize around {rubric}.",
                validation_plan=f"Assert and report evidence for {rubric}; validate data assumptions and numerical outputs.",
                differentiation=f"Use the task's distinctive methods and diagnostics: {rubric}, not a generic classification workflow.").with_inputs("task_prompt","rubric"))
        planner=NotebookPlanner()
        optimizer=dspy.BootstrapFewShot(metric=metric,max_bootstrapped_demos=2,max_labeled_demos=min(4,len(train)),
                                        max_rounds=1,metric_threshold=0.55)
        with dspy.context(lm=lm):
            compiled=optimizer.compile(planner,trainset=train)
            guidance={}
            for task in target_tasks:
                prediction=compiled(task_prompt=task["prompt"],rubric=", ".join(task.get("rubric",[])))
                guidance[task["id"]]={"design_strategy":str(prediction.design_strategy),
                    "validation_plan":str(prediction.validation_plan),"differentiation":str(prediction.differentiation)}
        output={"status":"success","optimizer":"DSPy BootstrapFewShot","model":model,
                "training_tasks":[t["id"] for t in training_tasks],"target_tasks":[t["id"] for t in target_tasks],"guidance":guidance,
                "caveat":"This is a rubric-guided prompt optimization trial, not proof of improved quality. Evaluate on held-out tasks and compare baseline vs optimized runs."}
        Path(output_path).parent.mkdir(parents=True,exist_ok=True)
        Path(output_path).write_text(json.dumps(output,indent=2),encoding="utf-8")
        return output
    except Exception as exc:
        return {"status":"failed_open","optimizer":"DSPy BootstrapFewShot","model":model,
                "error":f"{type(exc).__name__}: {str(exc)[:1500]}","guidance":{}}
