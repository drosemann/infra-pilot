# workflow optimization audit (2026-04-25)

## scope
this audit focuses on executable project workflows for:
• `scripts/setup.sh`
• `scripts/test.sh`
• `tools/run-all-tests.sh`
• `tools/lint-all.sh`

## executed work-steps

• baseline test workflow
   • ran `./scripts/test.sh`.
   • observed immediate failure in `orchestrator-agent` because `pytest` returned exit code `5` when no tests were collected.
• cross-service test workflow
   • ran `./tools/run-all-tests.sh` (permission denied due to missing executable bit).
   • re-ran with `bash ./tools/run-all-tests.sh`.
   • observed dependency install failures caused by restricted upstream package access (http 403/proxy errors).
• lint workflow
   • ran `bash ./tools/lint-all.sh`.
   • verified script executes linting but currently fails on existing typescript/react lint errors in `management-panel`.
• setup workflow
   • ran `bash ./scripts/setup.sh`.
   • observed service setup continues on partial failures, but hides useful install error details and includes a stale path check variable.

## implemented optimizations

### 1) test pipeline robustness
• `scripts/test.sh`
   • added strict shell mode (`set -euo pipefail`).
   • added explicit pass/skip/fail counters.
   • treated `pytest` exit code `5` (no tests collected) as skip, not failure.
   • added safe checks for missing test scripts and missing test directories.
   • removed broad stderr suppression to keep actionable diagnostics visible.

### 2) setup workflow reliability
• `scripts/setup.sh`
   • added strict shell mode.
   • removed invalid `services_path` gate and replaced it with direct tool checks.
   • replaced fragile `cd` usage with `pushd/popd` for deterministic directory restoration.
   • improved node installation logic by using `npm ci` when lockfiles are present.
   • preserved non-blocking behavior for optional service setup failures while retaining full error output.

### 3) cross-service test orchestration
• `tools/run-all-tests.sh`
   • added pass/skip/fail summary counters.
   • added lockfile-aware node dependency install strategy (`npm ci` vs `npm install`).
   • added python test-directory checks to avoid unnecessary environment bootstrap when no tests exist.
   • handled `pytest` no-test condition as skipped.
   • added per-test-venv isolation (`.venv`) and clearer final status output.

### 4) lint orchestration flexibility
• `tools/lint-all.sh`
   • added skip/fail summary.
   • uses service lint scripts when available; otherwise falls back to `npx eslint`.
   • supports both javascript and typescript react extension sets (`.js,.ts,.tsx`).
   • keeps services with missing npm/tooling from blocking unrelated lint runs.

## high-value edge cases to keep monitoring

• no-test services
   • many services may intentionally ship without tests during early stages. mark as skipped, not failed.
• offline / restricted network ci runners
   • package managers can fail with proxy/403 responses. consider:
     • artifact caching
     • internal registries
     • retry + backoff with explicit timeout
• script execution permissions
   • some helper scripts may not have executable mode set. prefer documented invocation via `bash <script>` or normalize permissions in repo.
• monorepo dependency drift
   • mixed ecosystems (maven, pip, npm) can fail independently. keep workflows tolerant and report per-service outcomes.
• hidden diagnostics
   • suppressing stderr (`2>/dev/null`) can hide root cause. keep user-friendly summaries, but preserve raw failure output.

## implemented follow-up optimizations (2026-04-25)

• added a unified workflow entrypoint:
  • `scripts/verify.sh` with selectable stages (`health,setup,test,lint,integration`)
  • root `makefile` targets: `verify`, `verify-offline`, `verify-json`
• added offline-safe execution mode:
  • `scripts/setup.sh --offline`
  • `scripts/test.sh --offline`
  • `tools/lint-all.sh --offline`
  • `tools/run-all-tests.sh --offline`
• added machine-readable summary mode:
  • `scripts/test.sh --json`
  • `tools/lint-all.sh --json`
  • `tools/run-all-tests.sh --json`
  • `scripts/verify.sh --json`
• added workflow health probes:
  • `scripts/healthcheck.sh` validates key manifests/config files before heavier stages.
