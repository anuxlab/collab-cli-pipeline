#!/usr/bin/env python3
"""Generate, execute, diagnose and repair code using a local Ollama model.

Inference is sent only to the Ollama HTTP endpoint on the runner (default localhost).
Generated code is executed separately in a reduced environment or Docker sandbox.
"""
from __future__ import annotations
import argparse
import difflib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from datetime import datetime, timezone

import requests
import nbformat

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TASK = """Write a self-contained Python script for a reproducible binary classification experiment.
Use sklearn.datasets.load_breast_cancer, train_test_split(test_size=0.25, random_state=42, stratify=y),
StandardScaler and LogisticRegression(max_iter=2000) in a Pipeline. Print exactly one final JSON object
on stdout containing dataset, model, accuracy, precision, recall, f1, and test_samples. Metrics must be
numeric and accuracy must be between 0.85 and 1.0. Use only installed packages (numpy and sklearn).
Do not read files except your own working directory, do not use the network, and do not access environment
variables. Include basic validation and exit nonzero if the metrics are invalid. Return only executable Python code."""
DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"


def extract_code(text: str) -> str:
    match = re.search(r"```(?:python|py)?\s*(.*?)```", text, flags=re.I | re.S)
    code = match.group(1).strip() if match else text.strip()
    if code.startswith("```"):
        code = re.sub(r"^```[^\n]*\n|\n```$", "", code).strip()
    if not code:
        raise ValueError("Model returned empty code")
    return code + "\n"


def call_model(model: str, messages: list[dict], timeout: int, base_url: str | None = None) -> str:
    """Call a model served by the local Ollama daemon; no hosted inference API or token."""
    base_url = (base_url or os.environ.get("OLLAMA_BASE_URL") or DEFAULT_OLLAMA_URL).rstrip("/")
    try:
        response = requests.post(
            f"{base_url}/api/chat",
            json={
                "model": model,
                "messages": messages,
                "stream": False,
                # Small context and batch reduce RAM pressure on CPU-only hosted runners.
                "options": {
                    "temperature": 0.1,
                    "num_ctx": int(os.environ.get("OLLAMA_NUM_CTX", "2048")),
                    "num_predict": int(os.environ.get("OLLAMA_NUM_PREDICT", "1400")),
                    "num_batch": int(os.environ.get("OLLAMA_NUM_BATCH", "128")),
                },
            },
            timeout=timeout,
        )
    except requests.RequestException as exc:
        raise RuntimeError(
            f"Local Ollama request failed at {base_url}. Ensure Ollama is running and model '{model}' is pulled. "
            f"Details: {type(exc).__name__}: {str(exc)[:800]}"
        ) from exc
    if not response.ok:
        raise RuntimeError(f"Local Ollama HTTP {response.status_code}: {response.text[:1200]}")
    data = response.json()
    try:
        return data["message"]["content"]
    except (KeyError, TypeError) as exc:
        raise RuntimeError(f"Unexpected local Ollama response: {json.dumps(data)[:1200]}") from exc


def execute_code(code: str, workdir: Path, timeout: int) -> dict:
    script = workdir / "generated_solution.py"
    script.write_text(code, encoding="utf-8")
    # Do not pass HF_TOKEN, GITHUB_TOKEN, or any other parent process environment variables.
    safe_env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": str(workdir),
        "TMPDIR": str(workdir),
        "PYTHONNOUSERSITE": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "MPLBACKEND": "Agg",
    }
    started = time.monotonic()
    use_docker = os.environ.get("AGENT_USE_DOCKER", "0") == "1"
    cidfile = workdir / "agent-container.cid"
    if use_docker:
        image = os.environ.get("AGENT_SANDBOX_IMAGE", "collab-agent-sandbox:latest")
        command = [
            "docker", "run", "--rm", "--cidfile", str(cidfile),
            "--network", "none", "--memory", "2g", "--cpus", "2",
            "--pids-limit", "128", "--read-only", "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges", "--tmpfs", "/tmp:rw,nosuid,nodev,size=256m",
            "--user", f"{os.getuid()}:{os.getgid()}",
            "-v", f"{workdir}:/workspace:rw", "-w", "/workspace",
            image, "python", "/workspace/generated_solution.py",
        ]
    else:
        # Local test/development fallback. The GitHub workflows enable Docker isolation.
        command = [sys.executable, "-I", str(script)]
    try:
        result = subprocess.run(
            command, cwd=workdir, env=safe_env, text=True, capture_output=True,
            timeout=timeout, check=False,
        )
        return {
            "returncode": result.returncode,
            "stdout": result.stdout[-12000:], "stderr": result.stderr[-12000:],
            "duration_seconds": round(time.monotonic() - started, 3), "timed_out": False,
            "sandbox": "docker-network-disabled" if use_docker else "local-subprocess-not-hardened",
        }
    except subprocess.TimeoutExpired as exc:
        if use_docker and cidfile.exists():
            container_id = cidfile.read_text(encoding="utf-8").strip()
            if container_id:
                subprocess.run(["docker", "kill", container_id], capture_output=True, timeout=10, check=False)
        return {
            "returncode": 124,
            "stdout": (exc.stdout or b"").decode(errors="replace")[-12000:] if isinstance(exc.stdout, bytes) else (exc.stdout or "")[-12000:],
            "stderr": (exc.stderr or b"").decode(errors="replace")[-12000:] if isinstance(exc.stderr, bytes) else (exc.stderr or "")[-12000:],
            "duration_seconds": round(time.monotonic() - started, 3), "timed_out": True,
            "sandbox": "docker-network-disabled" if use_docker else "local-subprocess-not-hardened",
        }


def validate_execution(execution: dict) -> tuple[bool, str, dict | None]:
    if execution["returncode"] != 0:
        return False, "process_failed_or_timed_out", None
    lines = [line.strip() for line in execution["stdout"].splitlines() if line.strip()]
    parsed = None
    for line in reversed(lines):
        try:
            candidate = json.loads(line)
            if isinstance(candidate, dict):
                parsed = candidate
                break
        except json.JSONDecodeError:
            continue
    if parsed is None:
        return False, "stdout_missing_final_json_object", None
    required = {"dataset", "model", "accuracy", "precision", "recall", "f1", "test_samples"}
    if not required.issubset(parsed):
        return False, "json_missing_required_fields", parsed
    try:
        metrics = [float(parsed[k]) for k in ("accuracy", "precision", "recall", "f1")]
        if not all(0.0 <= x <= 1.0 for x in metrics):
            return False, "metric_out_of_range", parsed
        if not isinstance(parsed["test_samples"], int) or parsed["test_samples"] <= 0:
            return False, "invalid_test_samples", parsed
    except (TypeError, ValueError):
        return False, "metrics_not_numeric", parsed
    return True, "passed", parsed


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
    messages = [
        {"role": "system", "content": "You are a careful Python coding agent. Return executable Python code only. Follow the task exactly."},
        {"role": "user", "content": DEFAULT_TASK},
    ]
    audit = []
    initial_code = ""
    final_execution = {}
    final_metrics = None
    status = "failed"
    for attempt in range(args.max_repairs + 1):
        started_at = datetime.now(timezone.utc).isoformat()
        try:
            response = call_model(args.model, messages, args.api_timeout, args.ollama_url)
            code = extract_code(response)
            if attempt == 0:
                initial_code = code
            (run_dir / f"generated_attempt_{attempt}.py").write_text(code, encoding="utf-8")
            execution = execute_code(code, workdir, args.execution_timeout)
            ok, reason, metrics = validate_execution(execution)
            (run_dir / f"stdout_attempt_{attempt}.txt").write_text(execution["stdout"], encoding="utf-8")
            (run_dir / f"stderr_attempt_{attempt}.txt").write_text(execution["stderr"], encoding="utf-8")
            audit.append({
                "attempt": attempt, "started_at_utc": started_at, "status": "passed" if ok else "failed",
                "validation": reason, "execution": execution, "metrics": metrics,
            })
            final_execution, final_metrics = execution, metrics
            if ok:
                status = "passed"
                (run_dir / "generated_solution.py").write_text(code, encoding="utf-8")
                break
            if attempt < args.max_repairs:
                diagnostic = f"Execution return code: {execution['returncode']}\nTimed out: {execution['timed_out']}\nValidation: {reason}\nSTDOUT:\n{execution['stdout']}\nSTDERR:\n{execution['stderr']}"
                messages.extend([
                    {"role": "assistant", "content": response},
                    {"role": "user", "content": "Repair the Python code using this diagnostic. Return the complete corrected executable Python script only.\n\n" + diagnostic},
                ])
        except Exception as exc:
            audit.append({"attempt": attempt, "started_at_utc": started_at, "status": "error", "error": f"{type(exc).__name__}: {str(exc)[:2000]}"})
            if attempt < args.max_repairs:
                messages.extend([
                    {"role": "assistant", "content": "The previous attempt failed before successful execution."},
                    {"role": "user", "content": f"Try again. Previous error: {type(exc).__name__}: {str(exc)[:1500]}. Return complete executable Python code only. Task: {DEFAULT_TASK}"},
                ])
    if initial_code:
        (run_dir / "initial_solution.py").write_text(initial_code, encoding="utf-8")
    # Keep a notebook artifact for every model run, including failed attempts.
    notebook_code = (run_dir / "generated_solution.py").read_text(encoding="utf-8") if (run_dir / "generated_solution.py").exists() else (initial_code or "# No code was generated successfully.\n")
    nb = nbformat.v4.new_notebook()
    nb.metadata = {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "collab_cli_agent": {"model": args.model, "status": status}}
    cell = nbformat.v4.new_code_cell(notebook_code)
    if final_execution:
        cell.execution_count = 1
        cell.outputs = []
        if final_execution.get("stdout"):
            cell.outputs.append(nbformat.v4.new_output("stream", name="stdout", text=final_execution["stdout"]))
        if final_execution.get("stderr"):
            cell.outputs.append(nbformat.v4.new_output("stream", name="stderr", text=final_execution["stderr"]))
        if final_execution.get("returncode", 1) != 0:
            cell.outputs.append(nbformat.v4.new_output("error", ename="ExecutionError", evalue=f"Process returned {final_execution.get('returncode')}", traceback=[]))
    nb.cells = [nbformat.v4.new_markdown_cell(f"# AI-generated ML experiment\n\nModel: `{args.model}`\n\nStatus: **{status}**"), cell]
    nbformat.write(nb, run_dir / "generated_notebook.ipynb")
    if (run_dir / "generated_solution.py").exists():
        final_code = (run_dir / "generated_solution.py").read_text(encoding="utf-8")
        diff = difflib.unified_diff(initial_code.splitlines(True), final_code.splitlines(True), fromfile="initial_solution.py", tofile="generated_solution.py")
        (run_dir / "repair.patch").write_text("".join(diff), encoding="utf-8")
    summary = {
        "experiment": "ai_notebook_code_repair", "model": args.model, "inference_backend": "local_ollama", "ollama_url": args.ollama_url, "status": status,
        "max_repairs": args.max_repairs, "attempts_used": len(audit),
        "started_at_utc": audit[0]["started_at_utc"] if audit else datetime.now(timezone.utc).isoformat(),
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "metrics": final_metrics, "final_execution": final_execution,
        "safety_note": "GitHub workflow runs use a Docker container with network disabled, resource limits, read-only root filesystem, and no credentials. Local fallback execution is not a hardened sandbox.",
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (run_dir / "audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(json.dumps({"status": status, "model": args.model, "attempts_used": len(audit), "run_dir": str(run_dir)}, indent=2))
    return 0 if status == "passed" else 1

if __name__ == "__main__":
    raise SystemExit(main())
