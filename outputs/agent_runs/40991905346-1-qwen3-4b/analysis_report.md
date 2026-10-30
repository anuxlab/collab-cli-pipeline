# AI Agent Run Analysis

- **Result:** blocked_before_inference
- **Model:** qwen3:4b
- **Workflow:** Local AI Agent Experiment — Free Hosted Runner (Resource-Aware SLM)
- **Run:** 40991905346 (attempt 1)
- **Commit:** b668d75d39214285cb01b39ab1af583716ccb8e2
- **Failure classification:** `SANDBOX_IMAGE_MISSING`

## Executive diagnosis

The sandbox image was not built or was unavailable. Check the test and Docker-build steps; do not spend model repair attempts on this infrastructure error.

## Workflow stage status

| Stage | Status |
|---|---|
| ollama_setup | not_run |
| model_pull | not_run |
| model_check | failure |
| agent_step | skipped |

## Resource snapshot

- CPU cores visible: 4
- GPU available: False
- GPU details: No NVIDIA GPU detected; standard hosted runner uses CPU inference.
- MemTotal: 16367520 KiB
- MemAvailable: 14965232 KiB
- SwapTotal: 3145724 KiB
- SwapFree: 3145724 KiB
- Workspace disk free at start: 91681546240 bytes

## Agent metrics

- Attempts recorded: 0
- Repair attempts allowed: not recorded
- Metrics: `null`
- Final execution duration: not recorded seconds

## Key log excerpts

### `docker-cleanup.log` (2 lines, 97 bytes)
```text
Error response from daemon: No such image: collab-agent-sandbox:latest
Total reclaimed space: 0B

```

### `model_check.log` (1 lines, 40 bytes)
```text
Ollama daemon or executable unavailable

```

### `ollama-stop.log` (1 lines, 99 bytes)
```text
/home/runner/work/_temp/852b54e2-c8d1-488b-a956-2d109e016c16.sh: line 3: ollama: command not found

```

### `ollama-systemd.log` (1 lines, 17 bytes)
```text
-- No entries --

```

### `docker-images.txt` (7 lines, 632 bytes)
```text
REPOSITORY                                   TAG       IMAGE ID       CREATED       SIZE
ghcr.io/github/gh-aw-firewall/agent          latest    3186a9688b66   5 days ago    1.01GB
ghcr.io/github/gh-aw-firewall/api-proxy      latest    71caee360497   5 days ago    374MB
ghcr.io/github/gh-aw-mcpg                    latest    adada59dc2eb   7 days ago    183MB
ghcr.io/github/github-mcp-server             latest    4d955ee421ef   8 days ago    50.1MB
ghcr.io/github/gh-aw-firewall/squid          latest    ceba3de0cc73   9 days ago    57.5MB
ghcr.io/dependabot/dependabot-updater-core   latest    dae9747fa760   10 days ago   830MB

```

### `final-disk.txt` (2 lines, 89 bytes)
```text
Filesystem      Size  Used Avail Use% Mounted on
/dev/root       145G   60G   86G  42% /

```

### `final-free-memory.txt` (3 lines, 207 bytes)
```text
               total        used        free      shared  buff/cache   available
Mem:     16760340480  1007947776 14435229696    48037888  1684156416 15752392704
Swap:     3221221376           0  3221221376

```

### `model_check_status.txt` (1 lines, 15 bytes)
```text
status=failure

```

### `model_pull_status.txt` (1 lines, 15 bytes)
```text
status=not_run

```

### `model_resource_gate.txt` (5 lines, 97 bytes)
```text
total_ram_gib=15
available_ram_gib=14
free_disk_gib=86
required_available_ram_gib=5
status=ready

```

### `ollama-ps.txt` (1 lines, 100 bytes)
```text
/home/runner/work/_temp/a9750ae7-f4f7-40f2-924c-903c4dbc5e66.sh: line 10: ollama: command not found

```

### `ollama_setup_status.txt` (1 lines, 15 bytes)
```text
status=not_run

```

## Files in this artifact

See `analysis.json` for structured diagnostics, `summary.json` and `audit.json` for agent-level results, `graph_trace.json` for LangGraph node transitions, `generated_notebook.ipynb` and `generated_attempt_*.py` for generated artifacts, and `ollama-serve.log` / `model_pull.log` for detailed runtime evidence.
