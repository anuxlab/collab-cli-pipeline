#!/usr/bin/env python3
"""Create a concise, self-contained diagnostic report for one local Ollama run."""
from __future__ import annotations
import argparse, json, os, platform, re, shutil, subprocess, time
from datetime import datetime, timezone
from pathlib import Path


def read_json(p: Path):
    try: return json.loads(p.read_text(encoding='utf-8'))
    except Exception: return None

def classify(text: str) -> tuple[str, str]:
    s=(text or '').lower()
    checks=[
      (('no space left on device','disk quota exceeded'), 'DISK_FULL', 'Model download or runtime storage exceeded available disk space.'),
      (('out of memory','oom-kill','cannot allocate memory','killed process','signal: killed','requires more system memory','not enough memory','insufficient memory','runner process has terminated'), 'MEMORY_PRESSURE', 'Model loading or inference likely exceeded available RAM; inspect memory snapshots and Ollama logs.'),
      (('manifest not found','pull model manifest','model not found','file does not exist','model tag not found'), 'MODEL_TAG_OR_PULL_FAILURE', 'The configured Ollama model tag may be unavailable or the model pull failed.'),
      (('connection refused','failed to connect','connection error'), 'OLLAMA_UNAVAILABLE', 'The local Ollama daemon was not reachable.'),
      (('timed out','timeout'), 'TIMEOUT', 'A model download, inference request, or generated-code execution exceeded its timeout.'),
      (('docker build','error during connect','cannot connect to the docker daemon'), 'DOCKER_SETUP_FAILURE', 'The isolated execution container could not be built or started.'),
      (('json_missing','stdout_missing','metric_out_of_range','process_failed_or_timed_out'), 'GENERATED_CODE_OR_VALIDATION_FAILURE', 'Inference may have completed, but generated code failed execution or output validation.'),
    ]
    for needles, code, desc in checks:
      if any(n in s for n in needles): return code, desc
    return ('UNKNOWN_FAILURE','No known failure signature matched; inspect the stage summary and attached diagnostic logs.')

def run(cmd):
    try:
      p=subprocess.run(cmd, capture_output=True, text=True, timeout=10)
      return {'returncode':p.returncode,'stdout':p.stdout[-5000:],'stderr':p.stderr[-3000:]}
    except Exception as e: return {'error':f'{type(e).__name__}: {e}'}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--run-dir',required=True); args=ap.parse_args()
    d=Path(args.run_dir); d.mkdir(parents=True,exist_ok=True)
    now=datetime.now(timezone.utc).isoformat()
    summary=read_json(d/'summary.json') or {}
    audit=read_json(d/'audit.json') or []
    stages=read_json(d/'stage_status.json') or {}
    # Collect stage outcomes even when a workflow step fails before the agent starts.
    for filename, key in [('ollama_setup_status.txt','ollama_setup'),('model_pull_status.txt','model_pull'),('model_check_status.txt','model_check'),('workflow_status.json','agent_step')]:
      fp=d/filename
      if fp.exists():
        if fp.suffix=='.json':
          obj=read_json(fp) or {}; stages[key]=obj.get('agent_step_outcome', obj.get('status','unknown'))
        else:
          parsed={}
          for line in fp.read_text(encoding='utf-8',errors='replace').splitlines():
            if '=' in line:
              k,v=line.split('=',1); parsed[k.strip()]=v.strip()
          stages[key]=parsed.get('status', parsed.get('exit_code','unknown'))
    resources=read_json(d/'runner_resources.json') or {}
    # Capture the state at finalization; this is deliberately best-effort.
    try:
      free=run(['bash','-lc','free -b; echo ---; df -B1 "$GITHUB_WORKSPACE" 2>/dev/null || df -B1 .; echo ---; cat /proc/meminfo | head -25'])
      (d/'final_system_snapshot.txt').write_text(free.get('stdout','')+'\n'+free.get('stderr',''),encoding='utf-8')
    except Exception: pass
    ollama_list=run(['ollama','list']) if shutil.which('ollama') else {'error':'ollama binary unavailable'}
    (d/'ollama_model_list.json').write_text(json.dumps(ollama_list,indent=2),encoding='utf-8')
    log_files=[]
    for p in sorted(d.glob('*.log'))+sorted(d.glob('*.txt')):
      if p.name in {'analysis_report.md','final_system_snapshot.txt'}: continue
      try:
        raw=p.read_text(encoding='utf-8',errors='replace')
        log_files.append({'file':p.name,'bytes':p.stat().st_size,'lines':len(raw.splitlines()),'tail':raw[-1800:]})
      except Exception: pass
    diagnostic_text='\n'.join([json.dumps(summary),json.dumps(stages),json.dumps(audit),json.dumps(log_files)])
    code, explanation=classify(diagnostic_text)
    agent_status=summary.get('status') or stages.get('agent_step') or 'not_completed'
    if agent_status == 'skipped' and stages.get('model_check') == 'failure':
      agent_status = 'blocked_before_inference'
    if agent_status=='passed': code,explanation='SUCCESS','Agent generated and validated a working solution.'
    elif stages.get('model_pull')=='failure' and code=='UNKNOWN_FAILURE': code,explanation='MODEL_PULL_FAILED','Ollama could not download the configured model; see model_pull.log and Ollama daemon log.'
    report={
      'schema_version':'1.0','generated_at_utc':now,
      'identity':{'repository':os.environ.get('GITHUB_REPOSITORY'),'workflow':os.environ.get('GITHUB_WORKFLOW'),'run_id':os.environ.get('GITHUB_RUN_ID'),'run_attempt':os.environ.get('GITHUB_RUN_ATTEMPT'),'commit_sha':os.environ.get('GITHUB_SHA'),'ref':os.environ.get('GITHUB_REF'),'runner_os':os.environ.get('RUNNER_OS'),'runner_arch':os.environ.get('RUNNER_ARCH')},
      'model':{'requested':os.environ.get('MODEL_ID'),'backend':'local Ollama','quantization':os.environ.get('MODEL_QUANTIZATION','not recorded'),'context_tokens':os.environ.get('OLLAMA_NUM_CTX'),'generation_tokens':os.environ.get('OLLAMA_NUM_PREDICT'),'batch_size':os.environ.get('OLLAMA_NUM_BATCH')},
      'status':agent_status,'failure_classification':{'code':code,'explanation':explanation},
      'stage_status':stages,'runner_resources':resources,
      'agent_summary':summary,'attempts':audit,
      'ollama_model_list':ollama_list,
      'log_inventory':[{'file':x['file'],'bytes':x['bytes'],'lines':x['lines']} for x in log_files],
      'recommended_next_action': explanation if code!='SUCCESS' else 'Compare this run against other models using metrics, attempts, and runtime.'
    }
    (d/'analysis.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    def val(x): return 'not recorded' if x is None or x=='' else str(x)
    lines=[f"# AI Agent Run Analysis",'',f"- **Result:** {val(agent_status)}",f"- **Model:** {val(os.environ.get('MODEL_ID'))}",f"- **Workflow:** {val(os.environ.get('GITHUB_WORKFLOW'))}",f"- **Run:** {val(os.environ.get('GITHUB_RUN_ID'))} (attempt {val(os.environ.get('GITHUB_RUN_ATTEMPT'))})",f"- **Commit:** {val(os.environ.get('GITHUB_SHA'))}",f"- **Failure classification:** `{code}`",'', '## Executive diagnosis','',explanation,'','## Workflow stage status','', '| Stage | Status |','|---|---|']
    for k,v in stages.items(): lines.append(f'| {k} | {v} |')
    lines += ['', '## Resource snapshot','',f"- CPU cores visible: {val(resources.get('cpu_count'))}",f"- GPU available: {val((resources.get('gpu') or {}).get('available'))}",f"- GPU details: {val((resources.get('gpu') or {}).get('details'))}"]
    mem=resources.get('memory_kib') or {}
    for k in ('MemTotal','MemAvailable','SwapTotal','SwapFree'):
      if k in mem: lines.append(f'- {k}: {mem[k]} KiB')
    disk=resources.get('workspace_disk_bytes') or {}
    if disk: lines.append(f"- Workspace disk free at start: {disk.get('free')} bytes")
    lines += ['', '## Agent metrics','',f"- Attempts recorded: {val(summary.get('attempts_used',len(audit) if isinstance(audit,list) else 0))}",f"- Repair attempts allowed: {val(summary.get('max_repairs'))}",f"- Metrics: `{json.dumps(summary.get('metrics'),ensure_ascii=False)}`",f"- Final execution duration: {val((summary.get('final_execution') or {}).get('duration_seconds'))} seconds",'', '## Key log excerpts','']
    if log_files:
      for x in log_files:
        lines += [f"### `{x['file']}` ({x['lines']} lines, {x['bytes']} bytes)",'```text',x['tail'] or '(empty)','```','']
    else: lines += ['No supplemental text logs were found.','']
    lines += ['## Files in this artifact','', 'See `analysis.json` for structured diagnostics, `summary.json` and `audit.json` for agent-level results, `generated_notebook.ipynb` and `generated_attempt_*.py` for generated artifacts, and `ollama-serve.log` / `model_pull.log` for detailed runtime evidence.','']
    (d/'analysis_report.md').write_text('\n'.join(lines),encoding='utf-8')
    # Manifest written last so the artifact can be inventoried without external tools.
    manifest=[]
    for p in sorted(d.rglob('*')):
      if p.is_file() and p.name!='artifact_manifest.json':
        manifest.append({'path':str(p.relative_to(d)),'bytes':p.stat().st_size})
    (d/'artifact_manifest.json').write_text(json.dumps({'generated_at_utc':now,'file_count':len(manifest),'files':manifest},indent=2),encoding='utf-8')
    print(f"Wrote {d/'analysis_report.md'}, analysis.json, and artifact_manifest.json; diagnosis={code}")
if __name__=='__main__': main()
