#!/usr/bin/env python3
"""Sample Ollama model-runner RSS and cgroup memory on Linux runners."""
from __future__ import annotations
import argparse, json, time
from datetime import datetime, timezone
from pathlib import Path


def runner_rss_kib() -> tuple[int, list[dict]]:
    total = 0
    processes = []
    proc = Path('/proc')
    for entry in proc.iterdir():
        if not entry.name.isdigit():
            continue
        try:
            cmd = (entry / 'cmdline').read_bytes().replace(b'\\0', b' ').decode(errors='ignore')
            if 'ollama' not in cmd.lower() or 'runner' not in cmd.lower():
                continue
            status = (entry / 'status').read_text(errors='ignore')
            rss = next((int(line.split()[1]) for line in status.splitlines() if line.startswith('VmRSS:')), 0)
            total += rss
            processes.append({'pid': int(entry.name), 'rss_kib': rss, 'cmd': cmd[:240]})
        except (OSError, ValueError, StopIteration):
            continue
    return total, processes


def cgroup_memory_bytes() -> int | None:
    for candidate in (Path('/sys/fs/cgroup/memory.current'), Path('/sys/fs/cgroup/memory/memory.usage_in_bytes')):
        try:
            return int(candidate.read_text().strip())
        except (OSError, ValueError):
            pass
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    parser.add_argument('--stop-file', required=True)
    parser.add_argument('--interval', type=float, default=2.0)
    args = parser.parse_args()
    output = Path(args.output); output.parent.mkdir(parents=True, exist_ok=True)
    stop = Path(args.stop_file)
    peak_rss = 0; peak_cgroup = 0; sample_count = 0
    with output.open('w', encoding='utf-8') as stream:
        stream.write('timestamp_utc,runner_rss_kib,cgroup_memory_bytes,runner_pids\n')
        while not stop.exists():
            rss, processes = runner_rss_kib()
            cgroup = cgroup_memory_bytes()
            peak_rss = max(peak_rss, rss)
            if cgroup is not None: peak_cgroup = max(peak_cgroup, cgroup)
            stream.write(f"{datetime.now(timezone.utc).isoformat()},{rss},{cgroup if cgroup is not None else ''},{'|'.join(str(x['pid']) for x in processes)}\n")
            stream.flush(); sample_count += 1
            time.sleep(max(0.5, args.interval))
    summary = {'peak_model_runner_rss_kib': peak_rss, 'peak_model_runner_rss_mib': round(peak_rss/1024, 2),
               'peak_cgroup_memory_bytes': peak_cgroup or None,
               'peak_cgroup_memory_mib': round(peak_cgroup/1024/1024, 2) if peak_cgroup else None,
               'sample_count': sample_count,
               'measurement_note': 'Runner RSS aggregates processes whose cmdline includes both ollama and runner; cgroup is the whole job/container limit, not model-only.'}
    output.with_name('peak_memory.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
