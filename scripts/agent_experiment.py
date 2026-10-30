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

try:
    from scripts.notebook_builder import create_generated_notebook
except ModuleNotFoundError:
    from notebook_builder import create_generated_notebook

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TASK = """Write a self-contained Python script for a reproducible binary classification experiment.
Use sklearn.datasets.load_breast_cancer, train_test_split(test_size=0.25, random_state=42, stratify=y),
StandardScaler and LogisticRegression(max_iter=2000) in a Pipeline. Print exactly one final JSON object
on stdout containing dataset, model, accuracy, precision, recall, f1, and test_samples. Metrics must be
numeric and accuracy must be between 0.85 and 1.0. Use only installed packages (numpy and sklearn).
Do not read files except your own working directory, do not use the network, and do not access environment
variables. Include basic validation and exit nonzero if the metrics are invalid. Return only executable Python code."""
DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"
MODEL_CALL_STATS: dict = {}


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
    MODEL_CALL_STATS.clear()
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
                    "num_predict": int(os.environ.get("OLLAMA_NUM_PREDICT", "1200")),
                    "num_batch": int(os.environ.get("OLLAMA_NUM_BATCH", "16")),
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
    # Ollama reports nanosecond durations and token counts; retain them for the audit.
    prompt_tokens = int(data.get("prompt_eval_count") or 0)
    output_tokens = int(data.get("eval_count") or 0)
    eval_ns = int(data.get("eval_duration") or 0)
    prompt_ns = int(data.get("prompt_eval_duration") or 0)
    total_ns = int(data.get("total_duration") or 0)
    MODEL_CALL_STATS.clear()
    MODEL_CALL_STATS.update({
        "prompt_tokens": prompt_tokens,
        "output_tokens": output_tokens,
        "prompt_eval_seconds": round(prompt_ns / 1e9, 3),
        "generation_seconds": round(eval_ns / 1e9, 3),
        "total_seconds": round(total_ns / 1e9, 3),
        "tokens_per_second": round(output_tokens / (eval_ns / 1e9), 3) if eval_ns > 0 else None,
    })
    try:
        return data["message"]["content"]
    except (KeyError, TypeError) as exc:
        raise RuntimeError(f"Unexpected local Ollama response: {json.dumps(data)[:1200]}") from exc


def execute_code(code: str, workdir: Path, timeout: int) -> dict:
    """Execute a candidate with per-attempt Docker identity and guaranteed cleanup."""
    import uuid

    script = workdir / "generated_solution.py"
    script.write_text(code, encoding="utf-8")
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
    # Never reuse a cidfile across attempts: stale files make docker run fail before execution.
    cidfile = workdir / f"agent-container-{uuid.uuid4().hex}.cid"
    container_id = ""
    image = os.environ.get("AGENT_SANDBOX_IMAGE", "collab-agent-sandbox:latest")
    if use_docker:
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
        command = [sys.executable, "-I", str(script)]
    try:
        result = subprocess.run(
            command, cwd=workdir, env=safe_env, text=True, capture_output=True,
            timeout=timeout, check=False,
        )
        if cidfile.exists():
            container_id = cidfile.read_text(encoding="utf-8", errors="replace").strip()
        return {
            "returncode": result.returncode,
            "stdout": result.stdout[-12000:], "stderr": result.stderr[-12000:],
            "duration_seconds": round(time.monotonic() - started, 3), "timed_out": False,
            "sandbox": "docker-network-disabled" if use_docker else "local-subprocess-not-hardened",
            "container_id": container_id or None,
        }
    except subprocess.TimeoutExpired as exc:
        if cidfile.exists():
            container_id = cidfile.read_text(encoding="utf-8", errors="replace").strip()
        if use_docker and container_id:
            subprocess.run(["docker", "kill", container_id], capture_output=True, timeout=10, check=False)
        return {
            "returncode": 124,
            "stdout": (exc.stdout or b"").decode(errors="replace")[-12000:] if isinstance(exc.stdout, bytes) else (exc.stdout or "")[-12000:],
            "stderr": (exc.stderr or b"").decode(errors="replace")[-12000:] if isinstance(exc.stderr, bytes) else (exc.stderr or "")[-12000:],
            "duration_seconds": round(time.monotonic() - started, 3), "timed_out": True,
            "sandbox": "docker-network-disabled" if use_docker else "local-subprocess-not-hardened",
            "container_id": container_id or None,
        }
    finally:
        # docker --rm removes the container; this removes its cidfile after success,
        # process failure, or timeout so the next repair attempt can always start.
        if cidfile.exists():
            try:
                cidfile.unlink()
            except OSError:
                pass

def _json_objects_from_text(text: str) -> list[dict]:
    """Extract JSON objects regardless of pretty-printing or surrounding log text.

    A brace scanner is used instead of line-based parsing so multi-line objects,
    nested values, escaped quotes, and braces inside JSON strings are handled.
    """
    candidates: list[dict] = []
    decoder = json.JSONDecoder()
    stripped = text.strip()
    if stripped:
        try:
            whole = json.loads(stripped)
            if isinstance(whole, dict):
                candidates.append(whole)
        except json.JSONDecodeError:
            pass

    start = None
    depth = 0
    in_string = False
    escaped = False
    for index, char in enumerate(text):
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            if depth == 0:
                start = index
            depth += 1
        elif char == "}" and depth:
            depth -= 1
            if depth == 0 and start is not None:
                try:
                    value, end = decoder.raw_decode(text[start:index + 1])
                    if end == len(text[start:index + 1]) and isinstance(value, dict):
                        candidates.append(value)
                except json.JSONDecodeError:
                    pass
                start = None
    return candidates


def validate_execution(execution: dict) -> tuple[bool, str, dict | None]:
    if execution.get("returncode") != 0 or execution.get("timed_out", False):
        return False, "process_failed_or_timed_out", None
    candidates = _json_objects_from_text(execution.get("stdout", ""))
    required = {"dataset", "model", "accuracy", "precision", "recall", "f1", "test_samples"}
    parsed = next((item for item in reversed(candidates) if required.issubset(item)), None)
    if parsed is None:
        if candidates:
            return False, "json_missing_required_fields", candidates[-1]
        return False, "stdout_missing_final_json_object", None
    if not isinstance(parsed.get("dataset"), str) or not parsed["dataset"].strip():
        return False, "invalid_dataset_name", parsed
    if not isinstance(parsed.get("model"), str) or not parsed["model"].strip():
        return False, "invalid_model_name", parsed
    try:
        metrics = [float(parsed[k]) for k in ("accuracy", "precision", "recall", "f1")]
        if not all(0.0 <= x <= 1.0 for x in metrics):
            return False, "metric_out_of_range", parsed
        samples = parsed["test_samples"]
        if isinstance(samples, bool) or int(samples) != samples or int(samples) <= 0:
            return False, "invalid_test_samples", parsed
        parsed["test_samples"] = int(samples)
        for key in ("accuracy", "precision", "recall", "f1"):
            parsed[key] = float(parsed[key])
    except (TypeError, ValueError, OverflowError):
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
    create_generated_notebook(
        notebook_code, run_dir / "generated_notebook.ipynb",
        model=args.model, status=status, orchestrator="Direct agent",
        execution=final_execution,
    )
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
