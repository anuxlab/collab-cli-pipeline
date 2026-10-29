#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${COLLAB_CLI_COMMAND:-}" ]]; then
  echo "COLLAB_CLI_COMMAND is empty; skipping Collab CLI integration."
  exit 0
fi

# This deliberately accepts only a configured command string. Confirm the real
# Collab CLI invocation before setting the repository variable. The CLI must be
# installed in the runner or installed in a prior step.
echo "Running configured Collab CLI command..."
bash -lc "$COLLAB_CLI_COMMAND" 2>&1 | tee outputs/collab_cli.log
