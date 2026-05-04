#!/usr/bin/env bash
set -euo pipefail

# Recommended local execution order before/around this script:
#   1) lint (bash tools/lint-all.sh)
#   2) unit tests
#   3) integration tests
#   4) smoke/e2e tests
# This script primarily orchestrates service-level tests plus repo integration tests.

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
OFFLINE=false
JSON_OUTPUT=false

while [ $# -gt 0 ]; do
  case "$1" in
    --offline)
      OFFLINE=true
      shift
      ;;
    --json)
      JSON_OUTPUT=true
      shift
      ;;
    *)
      echo "Unknown option: $1" >&2
      echo "Usage: $0 [--offline] [--json]" >&2
      exit 1
      ;;
  esac
done

echo "Running tests across all services in $ROOT_DIR..."
if [ "$OFFLINE" = true ]; then
  echo "Offline mode enabled: dependency installation steps will be skipped."
fi

FAILED=0
SKIPPED=0
PASSED=0

HAS_TESTS=false

for svc in "$ROOT_DIR"/services/*; do
  [ -d "$svc" ] || continue
  name=$(basename "$svc")
  echo "==> Service: $name"

  if [ -f "$svc/package.json" ]; then
    echo "--> Node: $name"
    if (cd "$svc" && node -e "const p=require('./package.json'); process.exit(p.scripts && p.scripts.test ? 0 : 1)"); then
      if [ "$OFFLINE" = false ]; then
        if [ -f "$svc/package-lock.json" ]; then
          (cd "$svc" && npm ci --silent && npm test) && PASSED=$((PASSED + 1)) || FAILED=$((FAILED + 1))
        else
          (cd "$svc" && npm install --silent && npm test) && PASSED=$((PASSED + 1)) || FAILED=$((FAILED + 1))
        fi
      else
        if [ -d "$svc/node_modules" ]; then
          (cd "$svc" && npm test) && PASSED=$((PASSED + 1)) || FAILED=$((FAILED + 1))
        else
          echo "---- Skipping Node tests for $name (offline and no node_modules)"
          SKIPPED=$((SKIPPED + 1))
        fi
      fi
    else
      echo "---- Skipping Node tests for $name (no test script found)"
      SKIPPED=$((SKIPPED + 1))
    fi
  fi

  if [ -f "$svc/requirements.txt" ]; then
    echo "--> Python: $name"
    python3 -V >/dev/null 2>&1 || { echo "Python3 not found"; FAILED=$((FAILED + 1)); continue; }
    HAS_TESTS=true

    if [ ! -d "$svc/tests" ]; then
      echo "---- Skipping Python tests for $name (no tests directory found)"
      SKIPPED=$((SKIPPED + 1))
      continue
    fi

    set +e
    (
      cd "$svc"
      python3 -m venv .venv
      # shellcheck disable=SC1091
      source .venv/bin/activate
      if [ "$OFFLINE" = false ]; then
        pip install -r requirements.txt
      fi
      set +e
      pytest -q
      rc=$?
      set -e
      command -v deactivate >/dev/null 2>&1 && deactivate || true

      if [ "$rc" -eq 0 ]; then
        exit 0
      elif [ "$rc" -eq 5 ]; then
        echo "---- No tests collected for $name"
        exit 5
      else
        exit "$rc"
      fi
    )
    rc=$?
    set -e

    if [ "$rc" -eq 0 ]; then
      PASSED=$((PASSED + 1))
    elif [ "$rc" -eq 5 ]; then
      SKIPPED=$((SKIPPED + 1))
    else
      FAILED=$((FAILED + 1))
    fi
  fi

  # Mark if this service contains any test artifact (node script or python requirements)
  if [ -f "$svc/package.json" ]; then
    HAS_TESTS=true
  fi
  if [ -f "$svc/requirements.txt" ]; then
    HAS_TESTS=true
  fi
done

# If no tests are present across all services, exit gracefully to avoid false failures.
if [ "$HAS_TESTS" = false ]; then
  echo "No test scripts or Python requirements found across services. Exiting gracefully."
  exit 0
fi

if [ -d "$ROOT_DIR/tests/integration" ]; then
  echo "==> Integration tests: integration"
  integ_dir="$ROOT_DIR/tests/integration"

  set +e
  (
    if [ -f "$integ_dir/requirements.txt" ]; then
      python3 -m venv "$integ_dir/.venv"
      # shellcheck disable=SC1091
      source "$integ_dir/.venv/bin/activate"
      if [ "$OFFLINE" = false ]; then
        pip install -r "$integ_dir/requirements.txt"
      fi
    fi

    set +e
    pytest -q "$integ_dir"
    rc=$?
    set -e
    command -v deactivate >/dev/null 2>&1 && deactivate || true
    exit "$rc"
  )
  rc=$?
  set -e

  if [ "$rc" -eq 0 ]; then
    PASSED=$((PASSED + 1))
  elif [ "$rc" -eq 5 ]; then
    SKIPPED=$((SKIPPED + 1))
  else
    FAILED=$((FAILED + 1))
  fi
fi

if [ "$JSON_OUTPUT" = true ]; then
  printf '{"script":"run-all-tests","passed":%s,"skipped":%s,"failed":%s,"offline":%s}\n' \
    "$PASSED" "$SKIPPED" "$FAILED" "$OFFLINE"
else
  echo "Summary: passed=$PASSED skipped=$SKIPPED failed=$FAILED"
fi

if [ "$FAILED" -gt 0 ]; then
  exit 1
fi

echo "All service tests completed successfully."
