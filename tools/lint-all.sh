#!/usr/bin/env bash
set -euo pipefail

# Lint all services in the repo — Node.js (ESLint/tsc) and Python (flake8).

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)

echo "[lint-all] Linting all services in: $ROOT_DIR"

EXIT_CODE=0

# --- Node.js services ---
CONTENTS=$(ls -1 "$ROOT_DIR"/*/package.json 2>/dev/null || true)
for pkg in $CONTENTS; do
  service_dir=$(dirname "$pkg")
  echo "[lint-all] Linting Node service: $service_dir"
  pushd "$service_dir" >/dev/null
  if npm run | grep -q 'lint'; then
    echo "[lint-all] Running: npm run lint";
    npm ci --silent || true
    npm run lint || EXIT_CODE=$?
  else
    if command -v npx >/dev/null 2>&1; then
      echo "[lint-all] Running: npx eslint .";
      npx eslint . || EXIT_CODE=$?
    else
      echo "[lint-all] No lint script or ESLint available in $service_dir; skipping.";
    fi
  fi
  popd >/dev/null
done

# --- Python services ---
PY_SERVICES=(
  "$ROOT_DIR/services/orchestrator-agent"
  "$ROOT_DIR/services/integration-service"
)
for py_dir in "${PY_SERVICES[@]}"; do
  if [ -d "$py_dir" ]; then
    echo "[lint-all] Linting Python service: $py_dir"
    if command -v flake8 >/dev/null 2>&1; then
      flake8 "$py_dir" --count --select=E9,F63,F7,F82 --show-source --statistics || true
      flake8 "$py_dir" --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics || true
    fi
    if command -v black >/dev/null 2>&1; then
      black --check "$py_dir" || EXIT_CODE=$?
    fi
    if command -v isort >/dev/null 2>&1; then
      isort --check-only "$py_dir" || EXIT_CODE=$?
    fi
  fi
done

exit $EXIT_CODE
