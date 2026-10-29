#!/usr/bin/env python3
"""Build a cross-run comparison table from saved agent experiment summaries."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "outputs" / "agent_runs"
FIELDS = [
    "run_folder", "model", "status", "attempts_used", "max_repairs",
    "accuracy", "precision", "recall", "f1", "test_samples",
    "execution_seconds", "started_at_utc", "finished_at_utc",
]


def collect_rows():
    rows = []
    if not RUNS.exists():
        return rows
    for summary_path in sorted(RUNS.glob("*/summary.json")):
        try:
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        metrics = summary.get("metrics") or {}
        execution = summary.get("final_execution") or {}
        rows.append({
            "run_folder": summary_path.parent.name,
            "model": summary.get("model", ""),
            "status": summary.get("status", "unknown"),
            "attempts_used": summary.get("attempts_used", ""),
            "max_repairs": summary.get("max_repairs", ""),
            "accuracy": metrics.get("accuracy", ""),
            "precision": metrics.get("precision", ""),
            "recall": metrics.get("recall", ""),
            "f1": metrics.get("f1", ""),
            "test_samples": metrics.get("test_samples", ""),
            "execution_seconds": execution.get("duration_seconds", ""),
            "started_at_utc": summary.get("started_at_utc", ""),
            "finished_at_utc": summary.get("finished_at_utc", ""),
        })
    return rows


def main():
    RUNS.mkdir(parents=True, exist_ok=True)
    rows = collect_rows()
    with (RUNS / "comparison.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    report = ["# AI agent experiment comparison", "", f"Runs with summaries: **{len(rows)}**", ""]
    if rows:
        report.append("| Model | Status | Attempts | Accuracy | F1 | Duration (s) | Run folder |")
        report.append("|---|---:|---:|---:|---:|---:|---|")
        for r in rows:
            def fmt(v):
                return f"{v:.4f}" if isinstance(v, (int, float)) else (str(v) if v != "" else "—")
            report.append(f"| {r['model']} | {r['status']} | {r['attempts_used']} | {fmt(r['accuracy'])} | {fmt(r['f1'])} | {fmt(r['execution_seconds'])} | `{r['run_folder']}` |")
    else:
        report.append("No `summary.json` files have been persisted yet. Run one of the AI Agent Experiment workflows manually.")
    (RUNS / "comparison.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"Wrote comparison report for {len(rows)} summarized run(s).")


if __name__ == "__main__":
    main()
