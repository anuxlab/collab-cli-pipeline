#!/usr/bin/env python3
"""Compare progressive notebook benchmark outputs across models."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path
from difflib import SequenceMatcher


def code_for(run: Path, task_id: str) -> str:
    attempts=sorted((run/task_id).glob("attempt_*.py"),key=lambda p:int(re.search(r"attempt_(\d+)",p.name).group(1)))
    return attempts[-1].read_text(encoding="utf-8") if attempts else ""

def similarity(a: str,b: str) -> float:
    # Token-level similarity ignores superficial whitespace and identifier ordering.
    ta=re.findall(r"[A-Za-z_][A-Za-z0-9_]*|\d+(?:\.\d+)?|==|<=|>=|!=|\S",a)
    tb=re.findall(r"[A-Za-z_][A-Za-z0-9_]*|\d+(?:\.\d+)?|==|<=|>=|!=|\S",b)
    return round(SequenceMatcher(None,ta,tb,autojunk=False).ratio(),4) if ta and tb else 0.0

def main():
    p=argparse.ArgumentParser(); p.add_argument("--runs",nargs="+",required=True,help="name=/path/to/benchmark/run_dir"); p.add_argument("--output",required=True); a=p.parse_args()
    runs={}
    for item in a.runs:
        name,path=item.split("=",1); root=Path(path); summary=json.loads((root/"benchmark_summary.json").read_text()); runs[name]=(root,summary)
    task_ids=sorted({t["task"]["id"] for _,summary in runs.values() for t in summary.get("tasks",[])})
    report={"models":{},"task_similarity":{},"warnings":[]}
    for name,(root,summary) in runs.items():
        report["models"][name]={"mean_score":summary.get("mean_score"),"passed":summary.get("passed"),"task_count":summary.get("task_count")}
    for task_id in task_ids:
        pairwise={}; names=list(runs)
        for i,left in enumerate(names):
            for right in names[i+1:]:
                sim=similarity(code_for(runs[left][0],task_id),code_for(runs[right][0],task_id))
                pairwise[f"{left} vs {right}"]=sim
                if sim>=0.92: report["warnings"].append(f"{task_id}: {left} and {right} outputs are highly similar ({sim}); inspect whether both are following the same template.")
        report["task_similarity"][task_id]=pairwise
    Path(a.output).parent.mkdir(parents=True,exist_ok=True); Path(a.output).write_text(json.dumps(report,indent=2),encoding="utf-8"); print(json.dumps(report,indent=2))
if __name__=="__main__": main()
