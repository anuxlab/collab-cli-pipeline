# Collab CLI Experiment Pipeline (scaled prototype)

A manually triggered GitHub Actions pipeline for repeatable ML experiments, notebook execution, output validation, artifact retention, and committing results back to this repository.

## Manual runs only

This workflow intentionally uses **only** `workflow_dispatch`. It does not run on pushes, pull requests, schedules, or releases. Existing files are retained unless a same-path file needed an update for the expanded pipeline.

1. Open **Actions → Collab CLI Experiment Pipeline**.
2. Click **Run workflow**.
3. Select `smoke` for a fast one-dataset check or `extended` for the full benchmark.
4. Choose whether to execute the report notebook and run unit tests. The original Iris notebook always runs; the report notebook can be skipped.
5. Inspect the run logs and download the artifacts. On success, generated outputs are committed to the selected branch.

The repository must allow GitHub Actions to write contents. The workflow uses `contents: write` and the built-in `GITHUB_TOKEN`.

## What is being tested

The original `notebooks/ml_pipeline.ipynb` and its output checks are retained and executed on each manual run. The optional `scripts/run_collab_cli.sh` hook is also retained; it runs only when the repository variable `COLLAB_CLI_COMMAND` is configured.

The benchmark uses local scikit-learn datasets (no external data download) and four models:
- Standard-scaled Logistic Regression
- Random Forest
- RBF Support Vector Classifier
- Histogram Gradient Boosting

Datasets:
- Iris (3-class)
- Wine (3-class)
- Breast Cancer Wisconsin (binary)

The `smoke` suite runs Iris with 3-fold cross-validation. The `extended` suite runs all three datasets with 5-fold cross-validation. All splits and model random states are seeded for repeatability.

Metrics include holdout accuracy, balanced accuracy, weighted precision/recall/F1, ROC AUC, cross-validation accuracy mean/std, and fit/prediction duration. The pipeline also saves confusion matrices and classification reports.

## Output artifacts

- `outputs/benchmark_summary.json` — compact run summary and best model per dataset
- `outputs/benchmark_details.json` — per-model confusion matrices and classification reports
- `outputs/benchmark_metrics.csv` — one row per dataset/model combination
- `outputs/f1_comparison.png` — weighted F1 comparison chart
- `outputs/cv_accuracy_comparison.png` — cross-validation comparison chart
- `outputs/run_metadata.json` — runner, commit, run and suite metadata
- `notebooks/experiment_report_executed.ipynb` — executed benchmark report notebook with captured outputs
- `notebooks/ml_pipeline_executed.ipynb` — original Iris notebook with captured outputs
- `outputs/ml_summary.json` and `outputs/feature_importance.csv` — retained outputs from the original Iris pipeline
- `outputs/collab_cli.log` — optional CLI stdout/stderr log

Artifacts are also uploaded to the Actions run for 30 days.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
pytest -q
BENCHMARK_SUITE=smoke python scripts/run_benchmark.py
python scripts/validate_outputs.py
```

To run the extended benchmark locally:

```bash
BENCHMARK_SUITE=extended python scripts/run_benchmark.py
python scripts/validate_outputs.py
```

To execute the report notebook locally (the workflow also always executes the original Iris notebook):

```bash
MPLBACKEND=Agg jupyter nbconvert --to notebook --execute notebooks/experiment_report.ipynb --output experiment_report_executed.ipynb --output-dir notebooks
```

## Safety and boundaries

This prototype runs fixed, reviewed benchmark code; it does not yet ask an LLM to write or execute arbitrary code. Do not expose repository write tokens to an AI-generated-code process. The next stage can add a separately gated Qwen agent job with bounded retries, timeouts, patch review, and generated notebook validation. Actual Collab CLI commands should be integrated only after confirming the CLI package and invocation syntax.

## Known limitations

- These are small built-in demonstration datasets, not evidence of production generalization.
- Cross-validation uses the full dataset independently of the holdout split for model comparison; report the held-out metrics separately from CV metrics.
- Timing values vary by runner load and software versions.
- Model comparison is an engineering smoke test, not a statistically powered model-selection study.

## AI coding-agent experiments (manual-only, local inference)

The original **Collab CLI Experiment Pipeline** and conventional ML benchmark remain in place. Three manually triggered workflows test quantized coding models through **Ollama running on GitHub-hosted runners**. They do not call Hugging Face Inference Providers, OpenAI, or another hosted inference endpoint, and do not require `HF_TOKEN`.

| Workflow in Actions | Model served locally by Ollama | Runner | Workflow file |
|---|---|---|---|
| Local AI Agent Experiment — Qwen2.5-Coder 14B Q4_K_M (Ollama) | `qwen2.5-coder:14b-instruct-q4_K_M` (~9 GB) | GitHub-hosted `ubuntu-latest`, CPU-only | `.github/workflows/agent-qwen-coder-32b.yml` |
| Local AI Agent Experiment — Qwen2.5-Coder 7B Q4_K_M (Ollama) | `qwen2.5-coder:7b-instruct-q4_K_M` (~5.4 GB) | GitHub-hosted `ubuntu-latest`, CPU-only | `.github/workflows/agent-qwen-coder-7b.yml` |
| Local AI Agent Experiment — DeepSeek-Coder-V2-Lite 16B Q4_0 (Ollama) | `deepseek-coder-v2:16b-lite-instruct-q4_0` (~8.9 GB) | GitHub-hosted `ubuntu-latest`, CPU-only | `.github/workflows/agent-deepseek-coder.yml` |

All three use only `workflow_dispatch`: **no push, pull-request, or scheduled trigger**. Each run has a unique path based on run ID, attempt, and model slug, preserving history instead of overwriting previous experiment outputs. The existing workflow file paths were retained while updating the displayed names and model IDs, so the previous Actions run history remains associated with those workflow paths.

### Local inference and hosted-runner memory tuning

- All three AI workflows now use GitHub-hosted `ubuntu-latest` and are triggered manually only. They no longer require self-hosted runner labels, so the old 32B and 16B workflows will not sit queued waiting for a private machine.
- Standard GitHub-hosted `ubuntu-latest` runners do not expose a GPU. Ollama therefore runs these experiments on CPU; VRAM cannot be borrowed as system RAM. GitHub currently documents standard public-repository Linux runners as 4 vCPU/16 GB RAM and private-repository standard Linux runners as 2 vCPU/8 GB RAM. The 14B/16B models are best-effort on the public 16 GB runner and are not reliable on the private 8 GB runner. Quantized weights are only part of peak memory use. A bounded 2 GiB swapfile is attempted when storage permits, but it cannot guarantee a model will fit and can make inference very slow. See the current [GitHub-hosted runner specifications](https://docs.github.com/en/actions/reference/runners/github-hosted-runners).
- The selected model set is Qwen2.5-Coder 7B Q4_K_M (baseline), Qwen2.5-Coder 14B Q4_K_M, and DeepSeek-Coder-V2-Lite 16B Q4_0. Both larger models are quantized and exceed 7B; the original 32B model is not practical for a standard hosted runner with limited RAM.
- Ollama is configured for one parallel request, one loaded model, a 1024-token context, a 512-token generation cap, a reduced 32-token batch size, Flash Attention, and an 8-bit KV cache. These settings trade context/output capacity for lower peak memory use. Ollama keeps only one model loaded and allows a one-minute idle keep-alive to avoid reloading the large model between generation and repair calls.
- After model download and sandbox image build, the workflow attempts to add a temporary 2 GiB disk-backed swapfile only when at least 3 GiB of disk remains. Swap uses SSD, not GPU VRAM; it may avoid some out-of-memory failures but can make inference much slower. If storage is tight, the workflow skips swap and records that decision. Runner RAM, disk, GPU, and swap diagnostics are saved with the run.
- Model weights are downloaded to the ephemeral runner during each run. Prompts and inference stay on the local Ollama daemon; no hosted inference API or `HF_TOKEN` is used.
- The workflow records available RAM, disk, CPU count, and whether an NVIDIA GPU is visible, so run reports can be interpreted against the actual runner resources.


### Agent loop and safety

Each workflow generates Python code, executes it in a Docker container with networking disabled and resource limits, diagnoses errors and invalid metrics, and permits at most two repairs. It saves generated scripts, a generated notebook, per-attempt stdout/stderr, `audit.json`, `summary.json`, and `repair.patch`. Model inference stays outside the generated-code container; the container receives no inference credentials. The model job has read-only repository permissions; a separate persistence job writes the run record and refreshes the comparison report. Do not place private data or secrets in prompts or the execution workspace.

### Comparing model runs

Compare each run's `summary.json`, `audit.json`, `repair.patch`, and stdout/stderr files. The comparison report is stored in `outputs/agent_runs/comparison.csv` and `outputs/agent_runs/comparison.md`. Compare models on the same task, timeout, and repair budget. A model run may fail because of model download, runner memory, Ollama startup, execution, or code quality; inspect retained logs to distinguish these cases.

### Local tests

```bash
pip install -r requirements.txt
pytest -q
```

The unit tests validate code extraction, metric validation, credential isolation, and local Ollama request handling using a mocked response. They do not download model weights or run live inference. Model experiments must be manually started in GitHub Actions.


## Analysis-first AI-agent artifacts

Every manually triggered local Ollama model workflow now builds a compact, analysis-first artifact even when setup, model download, inference, generated-code execution, or validation fails. Start with these files rather than reading raw logs line-by-line:

- `analysis_report.md` — executive diagnosis, stage statuses, resource snapshot, metrics, and short log excerpts.
- `analysis.json` — structured run identity, model settings, runner resources, attempt results, log inventory, failure classification, and next action.
- `artifact_manifest.json` — all artifact files and byte sizes.
- `summary.json` and `audit.json` — agent outcome and per-attempt details when the agent starts.
- `runner_resources.json`, `swap_status.txt`, `model_pull.log`, `ollama-serve.log`, and final system snapshots — supporting evidence.

The model jobs use low-memory local Ollama settings (512-token context, 384-token generation cap, batch 16, one model/request at a time). Standard GitHub-hosted runners do not expose GPU VRAM; the workflows do not pretend that disk swap is VRAM. Larger quantized models may still be slow or OOM on hosted CPU runners. Setup/pull failures are captured and summarized, and artifacts are uploaded on failure. All model workflows remain manual-only.


## LangGraph local-model agent experiments

The AI-agent workflows now invoke `scripts/agent_langgraph.py`. LangGraph explicitly
orchestrates the bounded loop:

1. **Generate** a Python candidate through the local Ollama HTTP endpoint.
2. **Execute** it inside the Docker sandbox (network disabled, resource and process limits).
3. **Diagnose** the execution result and validate the final JSON metrics.
4. **Repair** by sending the model the failed candidate's stdout, stderr, exit code,
   timeout state, and validation reason.
5. Repeat for at most two repairs, then save the final candidate and evidence.

This is a local Ollama setup; LangGraph is the orchestration layer, not a hosted inference
provider. No `HF_TOKEN` is needed. The graph trace is saved as `graph_trace.json`, with
attempt details in `audit.json`, final metrics in `summary.json`, and a human-readable
diagnostic in `analysis_report.md`.

### Reliability fixes included

- Docker execution uses a unique CID file per attempt and removes it in a `finally` block,
  preventing a stale container ID file from blocking later repair attempts.
- Each model workflow installs LangGraph and runs agent unit tests before downloading the
  multi-gigabyte model.
- The persistence job uses narrowly scoped `git add -f` for the run directory and comparison
  reports, so repository ignore rules cannot silently discard experiment evidence.
- Inference uses a 2,048-token context, 1,200-token output limit and batch size 16 to give
  generated Python enough room while keeping the runtime batch small.
- All experiment workflows remain manual-only (`workflow_dispatch`).

The standard GitHub-hosted Ubuntu runner is CPU-only in this configuration. Quantization
reduces weight memory but does not create GPU VRAM; larger model runs may still be slow or
fail if their weights plus runtime overhead exceed available RAM.


## Fixes from the latest hosted-runner failures

The most recent 14B and DeepSeek runs generated code, but Docker returned exit code 125
because the local `collab-agent-sandbox:latest` image had not been built. The preceding
test step failed to import the repository's `scripts` package when invoked through the
`pytest` console entry point. Since the agent step used `always()`, it continued despite
the failed test and skipped Docker build.

The workflows now:
- Run tests as `PYTHONPATH="$GITHUB_WORKSPACE" python -m pytest ...`.
- Install dependencies, run tests, and build the sandbox image **before downloading model weights**.
- Only execute the model agent when prior setup steps succeed and the model is available.
- Classify missing sandbox images as infrastructure failures, not model code failures.
- Reuse the installer-managed Ollama service if it is already healthy, instead of starting a second daemon on port 11434.
- Capture `journalctl -u ollama` in `ollama-systemd.log`.
- Persist results with a fetch/reset/rebuild/retry loop so simultaneous workflow commits do not lose run artifacts or fail on non-fast-forward pushes.
