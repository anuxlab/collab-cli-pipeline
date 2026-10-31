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
                              output_path: str | Path, timeout: int = 180,
                              baseline_reports: list[dict[str, Any]] | None = None) -> dict[str, Any]:
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
            fields = [str(getattr(prediction,k,"" )).strip() for k in
                      ("design_strategy","validation_plan","differentiation")]
            text = " ".join(fields).lower()
            terms=[x.strip().lower() for x in str(example.rubric).split(",") if x.strip()]
            coverage=sum(term in text for term in terms)/max(1,len(terms))
            structure=sum(len(value) >= 45 for value in fields)/3
            action_verbs = ("compare", "assert", "plot", "split", "inspect", "compute", "verify",
                            "fit", "report", "diagnose", "measure", "validate", "analyze", "estimate")
            actionability = min(1.0, sum(text.count(verb) for verb in action_verbs) / 5.0)
            differentiation = fields[2].lower()
            distinct_terms = sum(term in differentiation for term in terms)
            generic = any(phrase in differentiation for phrase in
                          ("standard ml pipeline", "generic workflow", "use appropriate methods", "follow best practices"))
            specificity = min(1.0, distinct_terms / 2.0) * (0.0 if generic else 1.0)
            uniqueness = 1.0 if len(set(value[:100] for value in fields)) == 3 else 0.0
            return 0.40*coverage + 0.20*structure + 0.15*actionability + 0.20*specificity + 0.05*uniqueness

        # Bootstrap only from actual successful baseline artifacts. This avoids
        # teaching DSPy synthetic "ideal" plans that merely echo the rubric.
        reports_by_id = {
            r.get("task", {}).get("id"): r for r in (baseline_reports or [])
        }
        train=[]
        for task in training_tasks:
            report = reports_by_id.get(task["id"], {})
            score = report.get("final_score", {})
            if not (score.get("execution_ok") and score.get("task_result_ok")):
                continue
            hits = score.get("rubric_hits", [])
            headings = score.get("section_headings", [])
            result = score.get("result") or {}
            # These labels summarize observed successful work, not fabricated
            # reference solutions. The prompt optimizer learns useful patterns
            # from executable notebooks and their measured evidence.
            train.append(dspy.Example(
                task_prompt=task["prompt"],
                rubric=", ".join(task.get("rubric", [])),
                design_strategy=("Successful baseline structure: " + "; ".join(headings[:8]) +
                                 ". Observed result keys: " + ", ".join(sorted(result.keys()))),
                validation_plan=("Successful baseline checks covered: " + ", ".join(hits) +
                                 ". Preserve execution, structured output and independent assertions."),
                differentiation=("Observed task-specific implementation for " + task["title"] +
                                 "; use its measured methods and diagnostics rather than a generic ML template."),
            ).with_inputs("task_prompt", "rubric"))
        if len(train) < 2:
            return {"status":"insufficient_baseline_evidence","optimizer":"DSPy BootstrapFewShot",
                    "model":model,"successful_training_examples":len(train),"guidance":{},
                    "error":"At least two successfully executed baseline notebooks are required for evidence-grounded prompt optimization."}
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
