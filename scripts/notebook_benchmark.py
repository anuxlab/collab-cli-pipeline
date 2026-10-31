#!/usr/bin/env python3
"""Progressive notebook-generation benchmark for local Ollama models.

Each task produces a Python source artifact, a semantic multi-cell notebook,
execution evidence, and a rubric-based score. Tasks are intentionally diverse;
model-authored self-assessments are not accepted as the sole grading signal.
"""
from __future__ import annotations
import argparse, json, re, time, ast, subprocess, os
from pathlib import Path
from typing import Any

try:
    from scripts.agent_experiment import MODEL_CALL_STATS, call_model, execute_code, extract_code
    from scripts.notebook_builder import create_generated_notebook
except ModuleNotFoundError:
    from agent_experiment import MODEL_CALL_STATS, call_model, execute_code, extract_code
    from notebook_builder import create_generated_notebook

TASKS: list[dict[str, Any]] = [
 {"id":"01_python_fundamentals","level":"1-simple","title":"Python fundamentals and numerical reasoning","rubric":["mean","median","variance","assert"],"prompt":"Create a clean, reproducible Python notebook script that analyses this fixed list [4, 7, 7, 10, 12, 14, 18]. Compute count, mean, median, population variance, min and max using Python standard library only. Validate results with assertions and explain why mean and median differ. Print one final line beginning BENCHMARK_RESULT= followed by JSON with task_id, count, mean, median, variance, min, max. Do not hardcode computed answers; calculate them."},
 {"id":"02_data_quality_eda","level":"2-basic-analytics","title":"Data quality and exploratory analysis","rubric":["isna","duplicated","groupby","describe","matplotlib"],"prompt":"Build a self-contained pandas/matplotlib analysis using a DataFrame you construct in code (at least 12 rows) about monthly retail transactions with columns date, region, product, units, unit_price, customer_id. Intentionally include at least one missing value and one duplicate. Audit missingness and duplicates, clean them with justified choices, engineer revenue, report groupby revenue by region and monthly trend, and create at least two informative plots. Include assertions and concise evidence-based interpretation. Save plots in the current directory. Print BENCHMARK_RESULT=<JSON> with task_id, rows_before, rows_after, missing_before, duplicates_before, total_revenue, regions. No network or external data."},
 {"id":"03_classification","level":"3-machine-learning","title":"Leakage-aware classification experiment","rubric":["train_test_split","Pipeline","StandardScaler","LogisticRegression","classification_report","confusion_matrix"],"prompt":"Create a rigorous binary classification notebook with sklearn.datasets.load_breast_cancer. Use stratified train/test split with random_state=42 and a Pipeline(StandardScaler, LogisticRegression). Avoid preprocessing leakage. Compare against DummyClassifier baseline; report accuracy, precision, recall, F1, ROC-AUC and confusion matrix. Include class balance, explain metric choice, inspect at least three misclassified cases if any, and create ROC/confusion-matrix plots. Assertions must verify dimensions, finite metrics, and model beats baseline accuracy. Print BENCHMARK_RESULT=<JSON> with task_id, accuracy, f1, roc_auc, baseline_accuracy, test_samples."},
 {"id":"04_regression_diagnostics","level":"4-advanced-ml","title":"Regression with residual diagnostics","rubric":["load_diabetes","train_test_split","RandomForestRegressor","mean_squared_error","residual","cross_val_score"],"prompt":"Create an end-to-end regression notebook using sklearn.datasets.load_diabetes. Split train/test reproducibly. Fit a DummyRegressor baseline and at least two meaningful regressors (e.g. Ridge and RandomForestRegressor); compare MAE, RMSE and R2, include cross-validation on training data only, residual plots and an error-analysis table for largest absolute residuals. Discuss overfitting and feature importance where valid. Assert all metrics finite and report the best model selected using a stated criterion. Print BENCHMARK_RESULT=<JSON> with task_id, best_model, mae, rmse, r2, baseline_rmse."},
 {"id":"05_time_series","level":"5-specialized","title":"Time-series forecasting without temporal leakage","rubric":["date_range","shift","rolling","train","test","naive","forecast"],"prompt":"Build a reproducible synthetic daily time-series forecasting notebook (at least 180 observations) with trend, weekly seasonality and noise. Use chronological train/test split (never random shuffle), create lag and rolling features without future leakage, compare a naive/seasonal-naive baseline with a model such as LinearRegression, and report MAE/RMSE. Plot series, forecast vs actual and residuals. Explain leakage prevention and limitations. Assert train dates precede test dates and metrics are finite. Print BENCHMARK_RESULT=<JSON> with task_id, train_samples, test_samples, baseline_mae, model_mae, model_rmse."},
 {"id":"06_nlp_text_classification","level":"6-nlp","title":"Small-data NLP with error analysis","rubric":["TfidfVectorizer","Pipeline","LogisticRegression","precision","recall","misclassified"],"prompt":"Create a self-contained NLP sentiment classification notebook using a thoughtfully designed synthetic but varied corpus of at least 40 short positive/negative texts (no downloads). Use stratified split, a Pipeline with TfidfVectorizer and LogisticRegression, compare with a simple majority baseline, report precision/recall/F1 and confusion matrix, inspect misclassified texts, and discuss synthetic-data limitations and lexical shortcuts. Include assertions and a plot. Print BENCHMARK_RESULT=<JSON> with task_id, samples, accuracy, f1, baseline_accuracy, misclassified_count."},
 {"id":"07_combinatorial_optimization","level":"7-optimization","title":"Knapsack optimization and algorithmic verification","rubric":["capacity","enumerate","itertools","greedy","optimal","assert"],"prompt":"Create an educational 0/1 knapsack optimization notebook with at least 12 items, integer weights/values and a capacity. Implement and compare (1) a greedy value/weight heuristic and (2) an exact method using dynamic programming or exhaustive enumeration. Verify feasibility, explain why greedy can be suboptimal, show selected items and a plot of value/weight, and include a brute-force cross-check for a small instance. No commercial solver. Assert the exact solution is feasible and not worse than greedy. Print BENCHMARK_RESULT=<JSON> with task_id, capacity, greedy_value, optimal_value, optimal_weight, item_count."},
]

SYSTEM = "You are an expert computational notebook author. Produce executable Python only. Make analytical decisions specific to the task, not a generic template. Prefer clear multi-stage analysis, meaningful diagnostics, thoughtful visualizations, explicit assumptions, and evidence-backed interpretation. Never fabricate results: compute them. Preserve reproducibility. Do not reveal private chain-of-thought; provide concise rationale in notebook markdown/comments. End stdout with BENCHMARK_RESULT=<valid JSON>."

def _extract_result(stdout: str) -> dict | None:
    matches = re.findall(r"BENCHMARK_RESULT\s*=\s*(\{.*?\})", stdout or "", flags=re.S)
    for raw in reversed(matches):
        try:
            value = json.loads(raw)
            if isinstance(value, dict): return value
        except json.JSONDecodeError: continue
    return None

def score_task(task: dict, source: str, execution: dict, notebook_path: Path) -> dict:
    lower = source.lower()
    rubric = task["rubric"]
    rubric_hits = [term for term in rubric if term.lower() in lower]
    result = _extract_result(execution.get("stdout", ""))
    code_cells = 0; markdown_cells = 0; headings: list[str] = []
    try:
        import nbformat
        nb = nbformat.read(notebook_path, as_version=4)
        code_cells = sum(c.cell_type == "code" for c in nb.cells)
        markdown_cells = sum(c.cell_type == "markdown" for c in nb.cells)
        headings = [c.source.splitlines()[0].lstrip("# ") for c in nb.cells if c.cell_type == "markdown" and c.source.startswith("## ")]
    except Exception: pass
    task_id_ok = bool(result and result.get("task_id") == task["id"])
    # Verify that AST segmentation did not omit or reorder executable statements.
    reconstructed = "\n".join(c.source for c in nb.cells if c.cell_type == "code") if 'nb' in locals() else ""
    normalize = lambda value: "\n".join(line.rstrip() for line in value.strip().splitlines() if line.strip())
    reconstruction_ok = bool(reconstructed) and normalize(reconstructed) == normalize(source)
    try:
        ast.parse(source)
        syntax_valid = True
    except SyntaxError:
        syntax_valid = False
    infrastructure_error = bool(execution.get("infrastructure_error"))
    executed = execution.get("returncode") == 0 and not execution.get("timed_out") and not infrastructure_error
    # Infrastructure failures are tracked separately and do not count as model failures.
    # Score uses independent signals: syntax, execution, structured output, task-specific constructs,
    # notebook decomposition, and diversity of analytical sections.
    components = {
      "syntax_validity": 10 if syntax_valid else 0,
      "execution": 25 if executed else 0,
      "structured_result": 20 if task_id_ok else 0,
      "rubric_coverage": round(20 * len(rubric_hits) / max(1, len(rubric)), 2),
      "notebook_structure": 10 if code_cells >= 3 and markdown_cells >= 3 else min(10, code_cells + markdown_cells),
      "source_reconstruction": 5 if reconstruction_ok else 0,
      "section_diversity": min(10, len(set(headings)) * 2),
    }
    return {"task_id":task["id"],"level":task["level"],"title":task["title"],"score":round(sum(components.values()),2),"components":components,"rubric_hits":rubric_hits,"rubric_missing":[x for x in rubric if x not in rubric_hits],"execution_ok":executed,"syntax_valid":syntax_valid,"infrastructure_error":infrastructure_error,"failure_category":("infrastructure" if infrastructure_error else "execution" if not executed else "quality" if not task_id_ok or not rubric_hits else "none"),"task_result_ok":task_id_ok,"source_reconstruction_ok":reconstruction_ok,"result":result,"code_cells":code_cells,"markdown_cells":markdown_cells,"section_headings":headings,"returncode":execution.get("returncode"),"timed_out":execution.get("timed_out",False),"stderr":execution.get("stderr","")[-3000:]}

def run_benchmark(model: str, output_dir: Path, ollama_url: str, timeout: int, max_repairs: int, selected: list[dict], prompt_prefix: str | dict = "", seed: int = 42) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    reports=[]
    for task in selected:
        task_dir=output_dir/task["id"]; task_dir.mkdir(parents=True,exist_ok=True)
        task_guidance = prompt_prefix.get(task["id"], "") if isinstance(prompt_prefix, dict) else prompt_prefix
        guidance_text = "\n\nDSPy-OPTIMIZED TASK-SPECIFIC PLANNING GUIDANCE:\n" + json.dumps(task_guidance, indent=2) if task_guidance else ""
        seed_text = f"\n\nBenchmark replicate seed: {seed}. Use this seed for every randomized operation and record it in the final result."
        messages=[{"role":"system","content":SYSTEM + guidance_text + seed_text},{"role":"user","content":task["prompt"] + f"\nUse random_state/random seed {seed} wherever applicable."}]
        attempts=[]; final_source=""; final_exec={}; score={}
        for attempt in range(max_repairs+1):
            started=time.monotonic()
            model_started=time.monotonic()
            try:
                raw=call_model(model,messages,timeout,ollama_url)
                model_call_seconds=round(time.monotonic()-model_started, 3)
                model_performance=dict(MODEL_CALL_STATS)
                source=extract_code(raw)
            except Exception as exc:
                attempts.append({"attempt":attempt,"stage":"generation","model_call_seconds":round(time.monotonic()-model_started, 3),
                                 "error":f"{type(exc).__name__}: {exc}"})
                break
            script=task_dir/f"attempt_{attempt}.py"; script.write_text(source,encoding="utf-8")
            execution=execute_code(source,task_dir,timeout=min(timeout,180))
            nb_path=task_dir/f"notebook_attempt_{attempt}.ipynb"
            create_generated_notebook(source,nb_path,model=model,status="passed" if execution.get("returncode")==0 else "failed",orchestrator="NotebookBenchmark",execution=execution,task_id=task["id"],task_title=task["title"])
            score=score_task(task,source,execution,nb_path)
            attempts.append({"attempt":attempt,"duration_seconds":round(time.monotonic()-started,2),
                             "model_call_seconds":model_call_seconds,"model_performance":model_performance,
                             "execution":execution,"score":score,"failure_category":score.get("failure_category"),
                             "script":script.name,"notebook":nb_path.name})
            final_source,final_exec=source,execution
            if execution.get("returncode")==0 and score["task_result_ok"] and score["score"]>=75: break
            if execution.get("infrastructure_error"):
                attempts[-1]["repair_skipped_reason"] = "sandbox_infrastructure_failure; model repair would not fix the runner"
                break
            if attempt<max_repairs:
                messages.append({"role":"assistant","content":raw})
                messages.append({"role":"user","content":("Repair this notebook script. Keep correct parts; address these independently measured failures.\n"
                    f"Execution return code: {execution.get('returncode')}\nSTDOUT:\n{execution.get('stdout','')[-5000:]}\nSTDERR:\n{execution.get('stderr','')[-5000:]}\n"
                    f"Rubric missing: {score.get('rubric_missing')}\nStructured result valid: {score.get('task_result_ok')}\n"
                    "Return the complete corrected Python script only.")})
        final_nb=task_dir/"notebook.ipynb"
        if final_source:
            create_generated_notebook(final_source,final_nb,model=model,status="passed" if final_exec.get("returncode")==0 else "failed",orchestrator="NotebookBenchmark",execution=final_exec,task_id=task["id"],task_title=task["title"])
        report={"task":task,"attempts":attempts,"final_score":score,"final_status":"passed" if score.get("score",0)>=75 and score.get("execution_ok") and score.get("task_result_ok") else "infrastructure_blocked" if score.get("infrastructure_error") else "failed","failure_category":score.get("failure_category"),"final_notebook":str(final_nb) if final_source else None}
        (task_dir/"task_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
        reports.append(report)
        if report["final_status"] == "infrastructure_blocked":
            # Do not spend inference time repairing or regenerating after a runner
            # failure. Mark remaining tasks as blocked and stop this phase.
            remaining = selected[len(reports):]
            for pending in remaining:
                reports.append({"task":pending,"attempts":[],"final_score":{"score":0,"infrastructure_error":True,"failure_category":"infrastructure"},"final_status":"infrastructure_blocked","failure_category":"infrastructure","final_notebook":None,"blocked_reason":"previous_task_sandbox_infrastructure_failure"})
            break
    summary={"model":model,"seed":seed,"task_count":len(selected),"completed_task_count":sum(bool(r.get("attempts")) for r in reports),"passed":sum(r["final_status"]=="passed" for r in reports),"failed":sum(r["final_status"]=="failed" for r in reports),"infrastructure_blocked":sum(r["final_status"]=="infrastructure_blocked" for r in reports),"mean_score":round(sum(r.get("final_score",{}).get("score",0) for r in reports)/max(1,len(reports)),2),"tasks":reports}
    (output_dir/"benchmark_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    return summary

def docker_preflight() -> dict:
    """Fail fast before model inference if the Docker sandbox is unavailable."""
    if __import__("os").environ.get("AGENT_USE_DOCKER", "0") != "1":
        return {"status": "not_required"}
    try:
        info = subprocess.run(["docker", "info"], text=True, capture_output=True, timeout=20)
        if info.returncode != 0:
            return {"status": "failed", "reason": (info.stderr or info.stdout)[-2000:]}
        image = __import__("os").environ.get("AGENT_SANDBOX_IMAGE", "collab-agent-sandbox:latest")
        check = subprocess.run(["docker", "image", "inspect", image], text=True, capture_output=True, timeout=20)
        if check.returncode != 0:
            return {"status": "failed", "reason": f"Sandbox image missing: {image}. Build Dockerfile.agent-sandbox before benchmark."}
        return {"status": "ready", "image": image}
    except Exception as exc:
        return {"status": "failed", "reason": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model",required=True); p.add_argument("--output-dir",required=True)
    p.add_argument("--ollama-url",default="http://127.0.0.1:11434")
    p.add_argument("--timeout",type=int,default=300); p.add_argument("--max-repairs",type=int,default=2)
    p.add_argument("--task-set",choices=["all","simple","complex"],default="all")
    p.add_argument("--task-ids",default=""); p.add_argument("--prompt-guidance",default="")
    p.add_argument("--dspy-optimize",action="store_true")
    p.add_argument("--phase",choices=["all","baseline","optimize","optimized"],default="all",
                   help="Run benchmark in explicit reproducible phases")
    p.add_argument("--baseline-dir",default="",help="Existing baseline directory for optimize/optimized phases")
    p.add_argument("--guidance-file",default="",help="DSPy guidance JSON for optimized-only phase")
    p.add_argument("--seed",type=int,default=42,help="Reproducibility seed shared by baseline and optimized runs")
    p.add_argument("--holdout-rotation",type=int,default=0,help="Rotate the deterministic DSPy train/holdout split between repeated runs")
    a=p.parse_args(); selected=TASKS
    if a.task_set=="simple": selected=TASKS[:2]
    elif a.task_set=="complex": selected=TASKS[2:]
    if a.task_ids: selected=[t for t in selected if t["id"] in set(a.task_ids.split(","))]
    output=Path(a.output_dir).resolve(); output.mkdir(parents=True,exist_ok=True)
    preflight=docker_preflight()
    (output/"sandbox_preflight.json").write_text(json.dumps(preflight,indent=2),encoding="utf-8")
    if preflight["status"]=="failed":
        print(json.dumps({"status":"infrastructure_blocked","sandbox_preflight":preflight},indent=2)); return 2

    baseline_dir=Path(a.baseline_dir).resolve() if a.baseline_dir else output/"baseline"
    if a.phase in ("all","baseline"):
        baseline=run_benchmark(a.model,baseline_dir,a.ollama_url,a.timeout,a.max_repairs,selected,seed=a.seed)
    else:
        summary_path=baseline_dir/"benchmark_summary.json"
        if not summary_path.exists():
            print(json.dumps({"status":"missing_baseline","expected":str(summary_path)},indent=2)); return 2
        baseline=json.loads(summary_path.read_text(encoding="utf-8"))

    if a.phase=="baseline" or (a.phase=="all" and not a.dspy_optimize):
        print(json.dumps({"phase":"baseline","summary":{k:v for k,v in baseline.items() if k!="tasks"}},indent=2))
        return 0 if baseline["passed"]==baseline["task_count"] else 1

    guidance={}
    optimization_metadata={}
    if a.phase in ("all","optimize") and a.dspy_optimize:
        try:
            from scripts.dspy_prompt_optimizer import optimize_notebook_prompts
        except ModuleNotFoundError:
            from dspy_prompt_optimizer import optimize_notebook_prompts
        # Build optimizer examples from actual baseline evidence; do not invent
        # idealized labels from task titles alone.
        successful_ids={r.get("task",{}).get("id") for r in baseline.get("tasks",[]) if r.get("final_score",{}).get("execution_ok") and r.get("final_score",{}).get("task_result_ok")}
        successful=[t for t in selected if t["id"] in successful_ids]
        # Reserve a deterministic, rotating holdout. Only successful baseline
        # tasks may become demonstrations; holdout tasks are never used as labels.
        rotation = a.holdout_rotation % max(1, len(successful))
        successful = successful[rotation:] + successful[:rotation]
        train_count = max(2, int(len(selected) * 0.6)) if len(selected) >= 4 else 2
        training = successful[:min(train_count, max(0, len(successful)-1))]
        training_ids = {t["id"] for t in training}
        targets=[t for t in selected if t["id"] not in training_ids]
        optimized=optimize_notebook_prompts(training,targets,a.model,a.ollama_url,output/"dspy_optimization.json",timeout=min(a.timeout,180),baseline_reports=baseline.get("tasks",[]))
        guidance=optimized.get("guidance",{}) if optimized.get("status")=="success" else {}
        optimization_metadata=optimized
        if a.phase=="optimize":
            print(json.dumps({"phase":"optimize","optimizer_status":optimized.get("status"),"training_tasks":optimized.get("training_tasks"),"evaluation_tasks":optimized.get("target_tasks")},indent=2))
            return 0 if optimized.get("status")=="success" else 1
        if optimized.get("status") != "success":
            comparison={"model":a.model,"seed":a.seed,"optimizer_status":optimized.get("status"),
                        "baseline_mean_score":baseline.get("mean_score"),"baseline_passed":baseline.get("passed"),
                        "optimized_run_skipped":True,"reason":optimized.get("error", "DSPy did not produce validated guidance")}
            (output/"baseline_vs_dspy.json").write_text(json.dumps(comparison,indent=2),encoding="utf-8")
            print(json.dumps(comparison,indent=2))
            return 1
    elif a.phase=="optimized":
        if not a.guidance_file:
            print("--guidance-file is required for --phase optimized",file=__import__("sys").stderr); return 2
        payload=json.loads(Path(a.guidance_file).read_text(encoding="utf-8")); guidance=payload.get("guidance",payload)
        optimization_metadata=payload
    elif a.phase=="optimize" and not a.dspy_optimize:
        print("--phase optimize requires --dspy-optimize",file=__import__("sys").stderr); return 2

    if a.phase in ("all","optimized"):
        improved=run_benchmark(a.model,output/"optimized",a.ollama_url,a.timeout,a.max_repairs,selected,guidance,seed=a.seed)
        baseline_by={r.get("task",{}).get("id"):r for r in baseline.get("tasks",[])}
        optimized_by={r.get("task",{}).get("id"):r for r in improved.get("tasks",[])}
        deltas={}
        for task in selected:
            tid=task["id"]
            if tid in baseline_by and tid in optimized_by:
                deltas[tid]=round(optimized_by[tid].get("final_score",{}).get("score",0)-baseline_by[tid].get("final_score",{}).get("score",0),2)
        training_ids=optimization_metadata.get("training_tasks",[])
        holdout_ids=optimization_metadata.get("target_tasks",[])
        holdout_deltas=[deltas[tid] for tid in holdout_ids if tid in deltas]
        holdout_delta=round(sum(holdout_deltas)/len(holdout_deltas),2) if holdout_deltas else None
        comparison={"model":a.model,"baseline_mean_score":baseline.get("mean_score"),"optimized_mean_score":improved.get("mean_score"),"score_delta":round(improved.get("mean_score",0)-baseline.get("mean_score",0),2),"per_task_score_delta":deltas,"holdout_mean_score_delta":holdout_delta,"holdout_evaluated_task_count":len(holdout_deltas),"baseline_passed":baseline.get("passed"),"optimized_passed":improved.get("passed"),"baseline_infrastructure_blocked":baseline.get("infrastructure_blocked",0),"optimized_infrastructure_blocked":improved.get("infrastructure_blocked",0),"optimizer_status":optimization_metadata.get("status", "guidance_file_or_disabled"),"seed":a.seed,"holdout_rotation":a.holdout_rotation,"training_task_ids":training_ids,"holdout_task_ids":holdout_ids,"interpretation":"Compare only runs with no infrastructure_blocked tasks. The heldout_mean_score_delta is the primary prompt-optimization signal. A single seed is exploratory; rotate held-out tasks and repeat seeds before claiming improvement."}
        (output/"baseline_vs_dspy.json").write_text(json.dumps(comparison,indent=2),encoding="utf-8")
        print(json.dumps(comparison,indent=2))
        return 0 if improved["passed"]==improved["task_count"] else 1
    return 0
if __name__=="__main__": raise SystemExit(main())
