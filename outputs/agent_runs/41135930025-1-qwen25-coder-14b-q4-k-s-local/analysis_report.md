# AI Agent Run Analysis

- **Result:** skipped
- **Model:** qwen2.5-coder:14b-instruct-q4_K_S
- **Workflow:** Local AI Agent Experiment — Qwen2.5-Coder 14B Q4_K_S (Ollama)
- **Run:** 41135930025 (attempt 1)
- **Commit:** e31e1a02043f06caee0b7d0257a4226765894586
- **Failure classification:** `UNKNOWN_FAILURE`

## Executive diagnosis

No known failure signature matched; inspect the stage summary and attached diagnostic logs.

## Workflow stage status

| Stage | Status |
|---|---|
| ollama_setup | success |
| model_pull | success |
| model_check | success |
| agent_step | skipped |

## Resource snapshot

- CPU cores visible: 4
- GPU available: False
- GPU details: No NVIDIA GPU detected; standard hosted runner uses CPU inference.
- MemTotal: 16367524 KiB
- MemAvailable: 14926864 KiB
- SwapTotal: 3145724 KiB
- SwapFree: 3145724 KiB
- Workspace disk free at start: 91587944448 bytes

## Agent metrics

- Attempts recorded: 0
- Repair attempts allowed: not recorded
- Metrics: `null`
- Final execution duration: not recorded seconds

## Key log excerpts

### `docker-cleanup.log` (3 lines, 145 bytes)
```text
Untagged: collab-agent-sandbox:latest
Deleted: sha256:ae4f3e66ce90e8d74345a6362fb0b001f41d95f3cdf62e9221182b42191e7684
Total reclaimed space: 0B

```

### `model_check.log` (21 lines, 522 bytes)
```text
  Model
    architecture        qwen2          
    parameters          14.8B          
    context length      32768          
    embedding length    5120           
    quantization        Q4_K_S         
    template source     go_template    

  Capabilities
    completion    
    tools         
    insert        

  System
    You are Qwen, created by Alibaba Cloud. You are a helpful assistant.    

  License
    Apache License               
    Version 2.0, January 2004    
    ...                          


```

### `model_pull.log` (801 lines, 111456 bytes)
```text
     [K
verifying sha256 digest ⠇ [K[?25h[?2026l[?2026h[?25l[A[A[A[A[A[1Gpulling manifest [K
pulling 0119ca9464dd: 100% ▕█████████████████ ▏ 8.6 GB/8.6 GB  214 MB/s      0s[K
pulling 66b9ea09bd5b: 100% ▕██████████████████▏   68 B                         [K
pulling 1e65450c3067: 100% ▕██████████████████▏ 1.6 KB                         [K
pulling 451734958dfb: 100% ▕██████████████████▏  488 B                         [K
verifying sha256 digest ⠏ [K[?25h[?2026l[?2026h[?25l[A[A[A[A[A[1Gpulling manifest [K
pulling 0119ca9464dd: 100% ▕█████████████████ ▏ 8.6 GB/8.6 GB  214 MB/s      0s[K
pulling 66b9ea09bd5b: 100% ▕██████████████████▏   68 B                         [K
pulling 1e65450c3067: 100% ▕██████████████████▏ 1.6 KB                         [K
pulling 451734958dfb: 100% ▕██████████████████▏  488 B                         [K
verifying sha256 digest ⠋ [K[?25h[?2026l[?2026h[?25l[A[A[A[A[A[1Gpulling manifest [K
pulling 0119ca9464dd: 100% ▕█████████████████ ▏ 8.6 GB/8.6 GB  214 MB/s      0s[K
pulling 66b9ea09bd5b: 100% ▕██████████████████▏   68 B                         [K
pulling 1e65450c3067: 100% ▕██████████████████▏ 1.6 KB                         [K
pulling 451734958dfb: 100% ▕██████████████████▏  488 B                         [K
verifying sha256 digest ⠙ [K[?25h[?2026l[?2026h[?25l[A[A[A[A[A[1Gpulling manifest [K
pulling 0119ca9464dd: 100% ▕█████████████████ ▏ 8.6 GB/8.6 GB  214 MB/s      0s[K
pulling 66b9ea09bd5b: 100% ▕██████████████████▏   68 B                         [K
pulling 1e65450c3067: 100% ▕██████████████████▏ 1.6 KB                         [K
pulling 451734958dfb: 100% ▕██████████████████▏  488 B                         [K
verifying sha256 digest [K
writing manifest [K
success [K[?25h[?2026l

```

### `ollama-install-stderr.log` (0 lines, 0 bytes)
```text
(empty)
```

### `ollama-install.log` (69 lines, 5094 bytes)
```text
########################################                      73.6%
######################################################                    75.6%
#######################################################                   77.5%
#########################################################                 79.3%
##########################################################                81.4%
############################################################              83.5%
#############################################################             85.2%
##############################################################            87.2%
###############################################################           88.1%
################################################################          90.1%
##################################################################        92.1%
###################################################################       93.7%
####################################################################      95.6%
######################################################################    97.6%
#######################################################################   99.6%
######################################################################## 100.0%
>>> Creating ollama user...
>>> Adding ollama user to render group...
>>> Adding ollama user to video group...
>>> Adding current user to ollama group...
>>> Creating ollama systemd service...
>>> Enabling and starting ollama service...
Created symlink /etc/systemd/system/default.target.wants/ollama.service → /etc/systemd/system/ollama.service.
>>> The Ollama API is now available at 127.0.0.1:11434.
>>> Install complete. Run "ollama" from the command line.
WARNING: No NVIDIA/AMD GPU detected. Ollama will run in CPU-only mode.

```

### `ollama-stop.log` (1 lines, 55 bytes)
```text
[?2026h[?25l[1G[K[?25h[?2026l[?25l[2K[1G[?25h
```

### `ollama-systemd.log` (2000 lines, 285098 bytes)
```text
   5.23 t/s, tg_3s =   5.07 t/s
Oct 30 23:06:49 runnervm48cm3 ollama[2696]: slot print_timing: id  0 | task 12783 | n_gen =    581, tg =   5.22 t/s, tg_3s =   5.04 t/s
Oct 30 23:06:52 runnervm48cm3 ollama[2696]: slot print_timing: id  0 | task 12783 | n_gen =    597, tg =   5.22 t/s, tg_3s =   5.04 t/s
Oct 30 23:06:56 runnervm48cm3 ollama[2696]: slot print_timing: id  0 | task 12783 | n_gen =    613, tg =   5.21 t/s, tg_3s =   5.05 t/s
Oct 30 23:06:59 runnervm48cm3 ollama[2696]: slot print_timing: id  0 | task 12783 | n_gen =    629, tg =   5.21 t/s, tg_3s =   5.05 t/s
Oct 30 23:07:02 runnervm48cm3 ollama[2696]: slot print_timing: id  0 | task 12783 | n_gen =    645, tg =   5.21 t/s, tg_3s =   5.05 t/s
Oct 30 23:07:05 runnervm48cm3 ollama[2696]: slot print_timing: id  0 | task 12783 | n_gen =    661, tg =   5.20 t/s, tg_3s =   5.05 t/s
Oct 30 23:07:08 runnervm48cm3 ollama[2696]: slot print_timing: id  0 | task 12783 | n_gen =    677, tg =   5.20 t/s, tg_3s =   5.04 t/s
Oct 30 23:07:11 runnervm48cm3 ollama[2696]: slot print_timing: id  0 | task 12783 | n_gen =    692, tg =   5.19 t/s, tg_3s =   4.97 t/s
Oct 30 23:07:14 runnervm48cm3 ollama[2696]: slot print_timing: id  0 | task 12783 | n_gen =    708, tg =   5.19 t/s, tg_3s =   5.01 t/s
Oct 30 23:07:18 runnervm48cm3 ollama[2696]: slot print_timing: id  0 | task 12783 | n_gen =    724, tg =   5.18 t/s, tg_3s =   5.03 t/s
Oct 30 23:07:21 runnervm48cm3 ollama[2696]: slot print_timing: id  0 | task 12783 | n_gen =    739, tg =   5.18 t/s, tg_3s =   4.96 t/s
Oct 30 23:07:24 runnervm48cm3 ollama[2696]: slot print_timing: id  0 | task 12783 | n_gen =    755, tg =   5.18 t/s, tg_3s =   5.03 t/s
Oct 30 23:07:27 runnervm48cm3 ollama[2696]: slot print_timing: id  0 | task 12783 | n_gen =    771, tg =   5.17 t/s, tg_3s =   5.03 t/s

```

### `docker-images.txt` (8 lines, 746 bytes)
```text
REPOSITORY                                   TAG       IMAGE ID       CREATED          SIZE
collab-agent-sandbox                         latest    ae4f3e66ce90   59 minutes ago   579MB
ghcr.io/github/gh-aw-firewall/agent          latest    3186a9688b66   6 days ago       1.01GB
ghcr.io/github/gh-aw-firewall/api-proxy      latest    71caee360497   6 days ago       374MB
ghcr.io/github/gh-aw-mcpg                    latest    adada59dc2eb   8 days ago       183MB
ghcr.io/github/github-mcp-server             latest    4d955ee421ef   9 days ago       50.1MB
ghcr.io/github/gh-aw-firewall/squid          latest    ceba3de0cc73   10 days ago      57.5MB
ghcr.io/dependabot/dependabot-updater-core   latest    dae9747fa760   11 days ago      830MB

```

### `final-disk.txt` (2 lines, 89 bytes)
```text
Filesystem      Size  Used Avail Use% Mounted on
/dev/root       145G   72G   73G  50% /

```

### `final-free-memory.txt` (3 lines, 207 bytes)
```text
               total        used        free      shared  buff/cache   available
Mem:     16760344576 12436353024   176836608    56209408  4566630400  4323991552
Swap:     3221221376   125644800  3095576576

```

### `model_check_status.txt` (1 lines, 15 bytes)
```text
status=success

```

### `model_pull_status.txt` (2 lines, 27 bytes)
```text
exit_code=0
status=success

```

### `model_resource_gate.txt` (4 lines, 81 bytes)
```text
available_ram_gib=14
free_disk_gib=81
required_available_ram_gib=12
status=ready

```

### `ollama-list-after-pull.txt` (2 lines, 177 bytes)
```text
NAME                                 ID              SIZE      MODIFIED               
qwen2.5-coder:14b-instruct-q4_K_S    9214d9fd3ff9    8.6 GB    Less than a second ago    

```

### `ollama-ps.txt` (2 lines, 241 bytes)
```text
NAME                                 ID              SIZE      PROCESSOR    CONTEXT    RUNNER      UNTIL              
qwen2.5-coder:14b-instruct-q4_K_S    9214d9fd3ff9    9.0 GB    100% CPU     2048       llamacpp    2 minutes from now    

```

### `ollama_setup_status.txt` (1 lines, 15 bytes)
```text
status=success

```

### `swap-policy.txt` (1 lines, 87 bytes)
```text
No temporary swapfile is created; swap-backed inference can thrash hosted-runner disk.

```

## Files in this artifact

See `analysis.json` for structured diagnostics, `summary.json` and `audit.json` for agent-level results, `graph_trace.json` for LangGraph node transitions, `generated_notebook.ipynb` and `generated_attempt_*.py` for generated artifacts, and `ollama-serve.log` / `model_pull.log` for detailed runtime evidence.
