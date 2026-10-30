# AI Agent Run Analysis

- **Result:** blocked_before_inference
- **Model:** qwen2.5-coder:7b-instruct-q4_K_M
- **Workflow:** Local AI Agent Experiment — Free Hosted Runner (Resource-Aware SLM)
- **Run:** 41129236472 (attempt 1)
- **Commit:** 2c69afa191e1b62bf0b24f308fa417e4721d5b7a
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
- MemTotal: 16367524 KiB
- MemAvailable: 15018904 KiB
- SwapTotal: 3145724 KiB
- SwapFree: 3145724 KiB
- Workspace disk free at start: 91680833536 bytes

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
/home/runner/work/_temp/70fa0f3d-b077-4fb4-a8e7-e85f5b29dc2c.sh: line 3: ollama: command not found

```

### `ollama-systemd.log` (1 lines, 17 bytes)
```text
-- No entries --

```

### `docker-images.txt` (7 lines, 632 bytes)
```text
REPOSITORY                                   TAG       IMAGE ID       CREATED       SIZE
ghcr.io/github/gh-aw-firewall/agent          latest    3186a9688b66   6 days ago    1.01GB
ghcr.io/github/gh-aw-firewall/api-proxy      latest    71caee360497   6 days ago    374MB
ghcr.io/github/gh-aw-mcpg                    latest    adada59dc2eb   8 days ago    183MB
ghcr.io/github/github-mcp-server             latest    4d955ee421ef   9 days ago    50.1MB
ghcr.io/github/gh-aw-firewall/squid          latest    ceba3de0cc73   10 days ago   57.5MB
ghcr.io/dependabot/dependabot-updater-core   latest    dae9747fa760   11 days ago   830MB

```

### `final-disk.txt` (2 lines, 89 bytes)
```text
Filesystem      Size  Used Avail Use% Mounted on
/dev/root       145G   60G   86G  42% /

```

### `final-free-memory.txt` (3 lines, 207 bytes)
```text
               total        used        free      shared  buff/cache   available
Mem:     16760344576  1063862272 14382702592    47898624  1679822848 15696482304
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
required_available_ram_gib=7
status=ready

```

### `ollama-ps.txt` (1 lines, 100 bytes)
```text
/home/runner/work/_temp/f0e1c8c4-85f5-4086-84ca-839d0b58aa22.sh: line 10: ollama: command not found

```

### `ollama_setup_status.txt` (1 lines, 15 bytes)
```text
status=not_run

```

## Files in this artifact

See `analysis.json` for structured diagnostics, `summary.json` and `audit.json` for agent-level results, `graph_trace.json` for LangGraph node transitions, `generated_notebook.ipynb` and `generated_attempt_*.py` for generated artifacts, and `ollama-serve.log` / `model_pull.log` for detailed runtime evidence.
