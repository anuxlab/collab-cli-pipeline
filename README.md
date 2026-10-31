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

## Generated notebook structure

AI-generated notebooks use semantic, execution-order-preserving cell segmentation (`semantic_multi_cell_v2`) rather than wrapping the complete script in one code cell. The builder uses Python AST structure, identifiers, common data-science APIs, and explicit section comments to identify practical workflow stages such as imports, configuration, data acquisition, exploratory inspection, data validation, preprocessing, train/test splitting, baseline methods, model definition, training, prediction, evaluation, diagnostics, visualization, interpretation, and export. Only adjacent statements are grouped; statements are never reordered, so variable dependencies and side effects remain in their original sequence.

Each section receives a meaningful Markdown heading and explanation, stable cell IDs, and metadata identifying its semantic role and source order. The notebook begins with model/orchestrator provenance and run instructions. Invalid Python is preserved in a clearly marked diagnostic cell instead of being silently discarded. Captured process output and failure information are attached to the notebook, while the original `.py` source remains available for reproducibility. The semantic classifier is heuristic: for unfamiliar domains, it falls back to an ordered “Experiment execution” section rather than inventing a domain-specific interpretation. Run the notebook from a clean Python 3 kernel, top to bottom.

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

Each workflow generates Python code, executes it in a Docker container with networking disabled and resource limits, diagnoses errors and invalid metrics, and permits up to five repairs after the initial generation (six total code-generation attempts). It saves generated scripts, a generated notebook, per-attempt stdout/stderr, `audit.json`, `summary.json`, and `repair.patch`. Model inference stays outside the generated-code container; the container receives no inference credentials. The model job has read-only repository permissions; a separate persistence job writes the run record and refreshes the comparison report. Do not place private data or secrets in prompts or the execution workspace.

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
5. Repeat for up to five repairs after the initial generation, then save the final candidate and evidence.

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

## High-end quantized reasoning-model workflow

A separate manual workflow, `.github/workflows/agent-high-end-reasoning.yml`, adds a selectable model benchmark for:

- `qwen3:30b-a3b-q4_K_M` — mixture-of-experts reasoning model (30B total parameters; fewer active per token).
- `deepseek-r1:32b-qwen-distill-q4_K_M` — reasoning-focused model.
- `qwen2.5-coder:32b` — larger coding-specialist model.

These are Ollama model identifiers; the workflow records the exact identifier and model metadata in each run artifact. Quantization labels can differ between Ollama tags, so inspect `ollama show` and the captured model metadata rather than assuming every tag uses the same quantization format.

**Runner requirements:** choose a self-hosted Linux x64 runner for these models. The workflow performs an early resource gate and requires at least 28 GiB total RAM and 35 GiB free workspace disk (32 GiB RAM / 50 GiB disk recommended). A GPU is strongly recommended for practical inference speed; CPU-only execution may be very slow. `ubuntu-latest` is offered only as an explicit selection and will normally stop at the resource gate instead of spending time downloading a model that cannot fit.

The high-end workflow uses a 4,096-token context, a 2,048-token generation budget, batch size 8, and longer configurable inference timeouts. It remains `workflow_dispatch` only; it does not run on pushes or schedules. Start with one model at a time to avoid exhausting runner memory.

## Validator robustness update

The agent now accepts compact JSON, pretty-printed multi-line JSON, and a JSON result surrounded by ordinary log lines. Extraction handles nested objects, escaped quotes, and braces inside JSON strings. It validates the required result keys and metric ranges without requiring the JSON object to occupy one physical stdout line. Regression tests cover the DeepSeek output shape observed in the October 30 run.


## Free GitHub-hosted runner inference profile

The `agent-high-end-reasoning.yml` workflow has been repurposed as the resource-aware SLM workflow for standard `ubuntu-latest` GitHub-hosted runners. It offers one selected model per workflow execution (3B, 4B, or 7B), uses a 4,096-token context with a bounded generation budget, and skips inference before downloading weights when the available RAM or disk check fails. It does not require a self-hosted runner.

### Runtime and storage controls

- Ollama model layers are restored/saved through `actions/cache` using a model-specific key. Cache availability is best-effort: GitHub cache quotas, eviction, and large model layers mean a cache hit is not guaranteed. If the cache is unavailable, Ollama downloads the model normally.
- Only the selected model is pulled for that workflow execution. The model is stopped after inference, while its cached layers are retained for future runs.
- Temporary Docker containers, the sandbox image, monitor files, and installer files are cleaned up. Experiment outputs and diagnostics are uploaded before the job finishes.
- The workflow records runner resources, periodic Ollama RSS samples, peak Ollama RSS, and per-call prompt/output token counts, generation duration, and output tokens/second in the attempt audit JSON.
- The agent job uploads artifacts with `if: always()`. A separate persistence job attempts to commit the run data even when inference or validation fails.
- No large swapfile is created. Swap-backed inference can cause severe disk thrashing and is not a substitute for RAM.

### Two-model collaboration

A two-SLM setup is feasible on a free runner if the models are used **sequentially**, not kept resident together. A practical pattern is: (1) a 3B/4B model drafts code, (2) unload it, (3) a 7B model reviews the code and produces a concise critique, and (4) the first model (or the reviewer) applies the critique before sandbox execution. In a GitHub Actions design, each model can also run in its own sequential job with an artifact hand-off; each job downloads only its own model. This costs two model downloads on a cold cache and increases wall-clock time, but avoids simultaneous model RAM pressure. A parallel two-model setup is not recommended on standard free hosted runners.

## Optional keyless web research for coding agents

The LangGraph agent includes an optional research node powered by the open-source
[`ddgs`](https://github.com/deedy5/ddgs) Python metasearch package (MIT license).
It queries public search backends without a paid API key or a separately hosted
search service. This is best-effort community metasearch, not an SLA-backed search
API; public backends can rate-limit or temporarily block automated requests.

To enable research in a manually dispatched model workflow:

1. Set **Enable free keyless web research** to `true`.
2. Supply a focused **Search query** (for example, `scikit-learn Pipeline API documentation`).
3. Run the selected model workflow as usual.

The `web_research` LangGraph node runs before generation. It saves `web_research.json`
and `web_research.md`, records its status in `graph_trace.json` and `summary.json`,
and adds bounded snippets plus source URLs to the model context. Search failures
are non-fatal: the agent continues without web context and records the diagnostic.

Search results are explicitly treated as untrusted reference material, not instructions.
Generated code still executes in the Docker sandbox with networking disabled. Web
search happens in the trusted orchestration process, outside that sandbox. Search
is disabled by default to avoid unnecessary network calls on tasks that do not need
current documentation. Install dependency: `ddgs>=9.14,<10`.

## Optional DSPy structured planning

The manual agent workflows include an `enable_dspy_planning` switch (off by default). When enabled, the workflow installs `requirements-dspy.txt` and asks DSPy to produce a concise implementation plan, observable acceptance criteria, and edge cases using the **same local Ollama model** through Ollama's OpenAI-compatible `/v1` endpoint. The plan is added as a checklist before the normal LangGraph generate/execute/diagnose/repair loop.

- No hosted API key or paid model is used; the local Ollama endpoint is the only LM backend.
- DSPy adds one extra model call and may increase run time, so it is opt-in on free hosted runners.
- If DSPy is unavailable or the planning call fails, the agent records the failure and continues with its normal prompt.
- The complete planner result is recorded in `summary.json` under `dspy_planning`.
- Enable it for controlled comparisons; compare otherwise-identical runs with planning on and off.



## Progressive notebook-generation benchmark and prompt optimization

The repository now includes a dedicated benchmark for detecting notebook-generation weaknesses across **seven increasingly difficult and deliberately different tasks**:

1. Python numerical fundamentals (simple)
2. Data quality, EDA, grouping and visualization
3. Leakage-aware binary classification with a baseline and error analysis
4. Regression model comparison, cross-validation and residual diagnostics
5. Time-series forecasting with chronological splits and leakage checks
6. Small-data NLP sentiment classification with misclassification analysis
7. 0/1 knapsack optimization with exact-vs-greedy comparison and verification

Run locally after starting Ollama and pulling the selected model:

```bash
AGENT_USE_DOCKER=1 AGENT_SANDBOX_IMAGE=collab-agent-sandbox:latest \
python scripts/notebook_benchmark.py \
  --model qwen2.5-coder:7b-instruct-q4_K_M \
  --output-dir outputs/notebook-benchmarks/qwen-7b \
  --task-set all --max-repairs 2
```

The benchmark creates one notebook per task, preserves generated source order, executes the source in the isolated sandbox, and records every attempt. It scores Python syntax, successful execution, task-specific structured output, rubric coverage, notebook cell structure, source reconstruction, and semantic-section diversity as separate components. Task ID/title are embedded in notebook metadata and task context refines section names for classification, regression, time series, NLP and optimization.

**Infrastructure errors are not model errors.** Docker daemon/image/CID-file/mount failures are classified as `infrastructure`, not sent back to the model for repair. The benchmark stops inference immediately and marks remaining tasks as `infrastructure_blocked`. It performs a Docker daemon and sandbox-image preflight before spending any model calls. This prevents a broken runner from consuming the repair budget.

### DSPy automatic prompt optimization

To compare a baseline against a DSPy-optimized task-planning prompt:

```bash
pip install -r requirements-dspy.txt
AGENT_USE_DOCKER=1 AGENT_SANDBOX_IMAGE=collab-agent-sandbox:latest \
python scripts/notebook_benchmark.py \
  --model qwen2.5-coder:7b-instruct-q4_K_M \
  --output-dir outputs/notebook-benchmarks/qwen-7b-dspy \
  --task-set all --max-repairs 2 --dspy-optimize
```

This runs the baseline suite, selects only successfully executed baseline notebooks as DSPy demonstrations, and uses `BootstrapFewShot` to optimize a task-specific notebook-planning module. A deterministic rotating holdout is excluded from the demonstrations. The optimizer's labels are derived from actual notebook headings, rubric checks and structured execution results—not synthetic task-title/rubric templates. It then reruns the same task set with generated guidance. It writes `dspy_optimization.json` and `baseline_vs_dspy.json`; comparisons include per-task deltas, seed, training/holdout IDs and infrastructure-blocked counts. If fewer than two successful baseline examples exist, optimization is marked `insufficient_baseline_evidence` and the second generation pass is skipped. DSPy uses the same local Ollama endpoint and no hosted API key.

**Evaluation caution:** the score is a transparent engineering rubric, not a scientific measure of creativity. Use the same `--seed` for baseline and optimized runs; change `--seed` and `--holdout-rotation` between repeated experiments. Compare only runs with zero infrastructure-blocked tasks. Manually inspect correctness and interpretation before concluding that DSPy improved reasoning.

The benchmark supports explicit phases so expensive work can be isolated:

```bash
# Phase 1: baseline only (no duplicate run)
python scripts/notebook_benchmark.py --model qwen2.5-coder:7b --output-dir outputs/exp --phase baseline --seed 42

# Phase 2: DSPy optimization from the saved baseline
python scripts/notebook_benchmark.py --model qwen2.5-coder:7b --output-dir outputs/exp --phase optimize --baseline-dir outputs/exp/baseline --dspy-optimize --holdout-rotation 1

# Phase 3: optimized evaluation, using saved guidance
python scripts/notebook_benchmark.py --model qwen2.5-coder:7b --output-dir outputs/exp --phase optimized --baseline-dir outputs/exp/baseline --guidance-file outputs/exp/dspy_optimization.json --seed 42
```

`--phase all --dspy-optimize` runs the three phases in one workflow. `--phase all` without `--dspy-optimize` runs only the baseline, avoiding an accidental duplicate benchmark.

### Detecting template collapse across models

Run the benchmark separately for each model, then compare outputs. For a normal benchmark, point to its root directory; for a DSPy experiment, compare the `baseline/` directories with one another or the `optimized/` directories with one another:

```bash
python scripts/compare_notebook_benchmarks.py \
  --runs qwen7=outputs/notebook-benchmarks/qwen-7b \
         deepseek=outputs/notebook-benchmarks/deepseek \
         qwen14=outputs/notebook-benchmarks/qwen-14b \
  --output outputs/notebook-benchmarks/cross-model-comparison.json
```

The comparison reports per-model scores and token-level code similarity for the same task. Similarity above 0.92 is flagged for manual review as a possible sign of template collapse; similarity alone does not establish plagiarism or lack of reasoning. The task rubric and generated outputs should be reviewed together.

### GitHub Actions controls

The four manual agent workflows now expose:
- `enable_notebook_benchmark` — run the progressive suite (off by default).
- `notebook_task_set` — `simple`, `complex`, or `all`.
- `enable_dspy_prompt_optimization` — run baseline-vs-DSPy optimization (requires the benchmark to be enabled).

The benchmark uses the same already-pulled local model and Docker sandbox. Notebook benchmark jobs use Ubuntu 24.04 and a 180-minute job timeout. Inputs `notebook_seed` and `notebook_holdout_rotation` support reproducible repeats and rotated holdouts. Memory monitoring now samples Ollama runner RSS (rather than the small Ollama daemon RSS) and whole-job cgroup memory; both metrics are clearly distinguished in `peak_memory.json`. The full suite plus optimization remains optional because it can take many model calls on CPU-only free runners. Benchmark artifacts are stored under the workflow run directory.


## October 31, 2026: Qwen 7B benchmark runtime optimization

See [`RUN_41168974567_41169474521_DIAGNOSIS.md`](RUN_41168974567_41169474521_DIAGNOSIS.md) for the evidence-based diagnosis and comparison with successful run `40991943449`. The Qwen 7B workflow now defaults to the two-task smoke suite, one repair, a 900-token generation cap, and serialized runs per Git ref. Select `all` explicitly for the full seven-task suite. Notebook reports now capture Ollama model-call timing and token counts.

The included `evidence/recent_runs/` directory contains the two cancelled run logs/artifacts and the earlier successful focused-run artifact for reproducibility.


## Qwen 7B notebook experiment profiles

The manual-only `agent-qwen-coder-7b.yml` workflow now preserves the existing benchmark and adds a selectable `notebook_profile`:

| Profile | Tasks | Repairs | Context | Max output tokens | Batch | Request timeout |
|---|---:|---:|---:|---:|---:|---:|
| `small` | 2 introductory tasks | 0 | 1,024 | 384 | 8 | 300s |
| `medium` | 4 tasks (fundamentals through regression) | 1 | 1,536 | 640 | 16 | 450s |
| `max` | All 7 tasks | 2 | 2,048 | 900 | 16 | 600s |
| `custom` | Existing task-set and repair inputs | configurable | configurable | configurable | configurable | configurable |

The `notebook_task_ids`, `notebook_repairs_override`, `notebook_num_ctx`, `notebook_num_predict`, `notebook_num_batch`, `notebook_temperature`, `notebook_top_p`, and `notebook_timeout_override` inputs override the selected preset when non-empty. The existing `notebook_task_set` and `notebook_max_repairs` controls remain available in `custom` mode. The profile resolver validates ranges and writes the resolved configuration to the workflow output.

All existing workflows and model variants remain in place; this is an additive change to the Qwen 7B workflow. The agent's standalone run settings are not changed by the notebook profile. The workflow remains `workflow_dispatch` only.
