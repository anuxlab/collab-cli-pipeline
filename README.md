# Collab CLI + Notebook CI prototype

This repository scaffold tests a repeatable notebook execution flow on a GitHub Actions runner. It begins with a deterministic scikit-learn ML pipeline so the execution, output collection, validation, artifact upload, and git commit path can be verified before wiring in an actual Collab CLI command or model agent.

## What the workflow does

1. Runs on manual dispatch or relevant pushes to `main`/`master`.
2. Installs Python dependencies on an Ubuntu runner.
3. Optionally invokes a configured Collab CLI command.
4. Executes `notebooks/ml_pipeline.ipynb` with `nbconvert`.
5. Writes `outputs/ml_summary.json` and `outputs/feature_importance.csv`.
6. Validates the summary and executed notebook for execution errors.
7. Uploads outputs as a GitHub Actions artifact and commits generated outputs back to the repository.

## Setup

1. Copy these files into your repository (or use this scaffold as a starter repo).
2. Ensure the workflow's branch list matches your default branch.
3. In **Settings → Actions → General → Workflow permissions**, allow read/write repository permissions. The workflow also declares `contents: write`.
4. Run **Actions → Collab CLI Notebook Pipeline → Run workflow**.
5. Check the workflow logs, artifact, and committed `outputs/` files.

## Collab CLI integration

The exact CLI package and command have not yet been specified, so the integration step is intentionally optional. After confirming the CLI installation and invocation, set a repository variable named `COLLAB_CLI_COMMAND` to the command (not a secret). If authentication is needed, pass credentials through GitHub Actions secrets and the CLI's documented environment variables; never hard-code tokens in the notebook, command, or committed output. If the CLI is not preinstalled on `ubuntu-latest`, add its official installation step before the optional command.

The current integration hook captures stdout/stderr to `outputs/collab_cli.log`. If the CLI produces notebooks or other files, add their paths to validation and artifact collection, and only commit files that are safe to keep in the repository.

## Why this starts without Qwen

Running a local Qwen model on a standard GitHub-hosted CPU runner can be slow and memory-constrained, and downloading weights on every run wastes time. First validate the notebook and persistence loop. Then add an agent as a separate optional job, ideally using a small quantized model with a cache or a hosted inference endpoint. Keep generated code execution sandboxed and time-limited, and do not give an agent repository write credentials inside its execution process.

## Output files

- `outputs/ml_summary.json` — run timestamp, dataset, accuracy, and split sizes.
- `outputs/feature_importance.csv` — permutation feature importance.
- `outputs/collab_cli.log` — only created when the optional CLI command runs.
- `notebooks/ml_pipeline_executed.ipynb` — notebook with cell outputs saved.


## Workflow trigger policy

This workflow is **manual-run only**. It uses `workflow_dispatch` and does not run automatically on pushes or pull requests. In GitHub, open **Actions → Collab CLI Notebook Pipeline → Run workflow** to start a run. Generated outputs are still committed back to the repository by the workflow when the run succeeds and repository write permissions are enabled.
