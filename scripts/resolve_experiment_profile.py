#!/usr/bin/env python3
"""Resolve reproducible notebook benchmark presets plus explicit field overrides."""
from __future__ import annotations
import argparse

PRESETS = {
    "small":  {"task_set": "simple", "task_ids": "01_python_fundamentals,02_data_quality_eda", "repairs": 0, "timeout": 300, "num_ctx": 1024, "num_predict": 384, "num_batch": 8, "temperature": 0.1, "top_p": 0.8},
    "medium": {"task_set": "all", "task_ids": "01_python_fundamentals,02_data_quality_eda,03_classification,04_regression_diagnostics", "repairs": 1, "timeout": 450, "num_ctx": 1536, "num_predict": 640, "num_batch": 16, "temperature": 0.1, "top_p": 0.85},
    "max":    {"task_set": "all", "task_ids": "", "repairs": 2, "timeout": 600, "num_ctx": 2048, "num_predict": 900, "num_batch": 16, "temperature": 0.1, "top_p": 0.9},
}

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--profile",choices=["small","medium","max","custom"],required=True)
    p.add_argument("--task-set",choices=["simple","complex","all"],default="simple")
    p.add_argument("--repairs",default=""); p.add_argument("--task-ids",default=""); p.add_argument("--timeout",default="")
    p.add_argument("--num-ctx",default=""); p.add_argument("--num-predict",default="")
    p.add_argument("--num-batch",default=""); p.add_argument("--temperature",default=""); p.add_argument("--top-p",default="")
    p.add_argument("--github-output",default=""); p.add_argument("--json-output",default="")
    a=p.parse_args()
    if a.profile == "custom":
        cfg={"task_set":a.task_set,"task_ids":"","repairs":int(a.repairs or 1),"timeout":300,"num_ctx":2048,"num_predict":900,"num_batch":16,"temperature":0.1,"top_p":0.9}
    else:
        cfg=PRESETS[a.profile].copy()
    if a.task_ids.strip(): cfg["task_ids"]=a.task_ids.strip()
    for arg,key,cast in [(a.repairs,"repairs",int),(a.timeout,"timeout",int),(a.num_ctx,"num_ctx",int),(a.num_predict,"num_predict",int),(a.num_batch,"num_batch",int),(a.temperature,"temperature",float),(a.top_p,"top_p",float)]:
        if str(arg).strip(): cfg[key]=cast(arg)
    if not 0 <= cfg["repairs"] <= 5: p.error("repairs must be between 0 and 5")
    if not 60 <= cfg["timeout"] <= 900: p.error("timeout must be between 60 and 900 seconds")
    if not 512 <= cfg["num_ctx"] <= 8192: p.error("num_ctx must be between 512 and 8192")
    if not 128 <= cfg["num_predict"] <= 4096: p.error("num_predict must be between 128 and 4096")
    if not 1 <= cfg["num_batch"] <= 128: p.error("num_batch must be between 1 and 128")
    if not 0 <= cfg["temperature"] <= 2: p.error("temperature must be between 0 and 2")
    if not 0 < cfg["top_p"] <= 1: p.error("top_p must be in (0,1]")
    if a.profile == "custom": cfg["task_ids"]=""
    if a.github_output:
        with open(a.github_output,"a",encoding="utf-8") as f:
            for k,v in cfg.items(): f.write(f"{k}={v}\n")
    if a.json_output:
        from pathlib import Path
        import json
        target=Path(a.json_output); target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(json.dumps({"profile":a.profile, **cfg}, indent=2), encoding="utf-8")
    print(cfg)
    return 0
if __name__ == "__main__": raise SystemExit(main())
