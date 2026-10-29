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
