#!/usr/bin/env bash
# Pre-flight checks before upgrading the Infra Pilot Helm release: working tree
# cleanliness, recent backup, free disk space, Helm availability (and optional
# 'helm diff'), Kubernetes API reachability and an explicit confirmation.
# Nothing is changed unless --execute is passed.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()    { echo -e "${BLUE}${1}${NC}"; }
warn()    { echo -e "${YELLOW}${1}${NC}"; }
success() { echo -e "${GREEN}${1}${NC}"; }
error()   { echo -e "${RED}${1}${NC}" >&2; }

FAILED=0
pass() { success "  [ok]   $1"; }
fail() { error   "  [fail] $1"; FAILED=$((FAILED + 1)); }
skip() { warn    "  [skip] $1"; }

usage() {
  cat <<EOF
Pre-flight checks for an Infra Pilot Helm upgrade.

Usage: $(basename "$0") [OPTIONS]

Target:
  --release NAME        Helm release name (default: infra-pilot)
  --namespace NS        Kubernetes namespace (default: current context namespace)
  --chart DIR           Chart directory (default: helm/infra-pilot)
  --values FILE         Extra values file (repeatable)

Thresholds:
  --max-backup-age-hours N   Fail if the newest backup is older (default: 24)
  --min-free-gb N            Minimum free disk space in GB (default: 5)
  --backup-dir DIR           Directory containing last_success.prom (repeatable,
                             default: \$ROOT_DIR/backups)

Behaviour:
  --allow-dirty         Do not fail when the git working tree is dirty
  --helm-diff           Run 'helm diff upgrade' when the plugin is installed
  --execute             Run the 'helm upgrade' command after a successful preflight
  --yes                 Skip the confirmation prompt (for automation)
  --check-only          Never prompt; only run the checks
  --skip-git            Skip the git working tree check
  --skip-backup         Skip the backup freshness check
  --skip-disk           Skip the disk space check
  --skip-helm           Skip the Helm availability check
  --skip-kubectl        Skip the Kubernetes API check
  --self-test           Run internal self tests (no cluster required) and exit
  --help                Show this help message

Exit status is 0 when every check passes, 1 otherwise. See docs/OPERATIONS.md
for the upgrade runbook.
EOF
  exit "${1:-0}"
}

RELEASE="${HELM_RELEASE:-infra-pilot}"
NAMESPACE="${KUBE_NAMESPACE:-}"
CHART="$ROOT_DIR/helm/infra-pilot"
VALUES_FILES=()
MAX_BACKUP_AGE_HOURS=24
MIN_FREE_GB=5
BACKUP_DIRS=("${BACKUP_DIR:-$ROOT_DIR/backups}")
ALLOW_DIRTY=false
HELM_DIFF=false
EXECUTE=false
ASSUME_YES=false
CHECK_ONLY=false
SKIP_GIT=false
SKIP_BACKUP=false
SKIP_DISK=false
SKIP_HELM=false
SKIP_KUBECTL=false
SELF_TEST=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --release) RELEASE="$2"; shift 2 ;;
    --namespace) NAMESPACE="$2"; shift 2 ;;
    --chart) CHART="$2"; shift 2 ;;
    --values) VALUES_FILES+=("$2"); shift 2 ;;
    --max-backup-age-hours) MAX_BACKUP_AGE_HOURS="$2"; shift 2 ;;
    --min-free-gb) MIN_FREE_GB="$2"; shift 2 ;;
    --backup-dir) BACKUP_DIRS+=("$2"); shift 2 ;;
    --allow-dirty) ALLOW_DIRTY=true; shift ;;
    --helm-diff) HELM_DIFF=true; shift ;;
    --execute) EXECUTE=true; shift ;;
    --yes) ASSUME_YES=true; shift ;;
    --check-only) CHECK_ONLY=true; shift ;;
    --skip-git) SKIP_GIT=true; shift ;;
    --skip-backup) SKIP_BACKUP=true; shift ;;
    --skip-disk) SKIP_DISK=true; shift ;;
    --skip-helm) SKIP_HELM=true; shift ;;
    --skip-kubectl) SKIP_KUBECTL=true; shift ;;
    --self-test) SELF_TEST=true; shift ;;
    --help) usage ;;
    *) error "Unknown option: $1"; usage 2 ;;
  esac
done

resolve_namespace() {
  if [[ -n "$NAMESPACE" ]]; then
    return 0
  fi
  NAMESPACE="$(kubectl config view --minify -o jsonpath='{..namespace}' 2>/dev/null || true)"
  NAMESPACE="${NAMESPACE:-default}"
}

check_git() {
  info "Git working tree"
  if ! git -C "$ROOT_DIR" rev-parse --git-dir &> /dev/null; then
    skip "not a git repository"
    return 0
  fi
  local dirty
  dirty="$(git -C "$ROOT_DIR" status --porcelain)"
  if [[ -z "$dirty" ]]; then
    pass "working tree is clean"
  elif [[ "$ALLOW_DIRTY" == true ]]; then
    warn "  [warn] working tree is dirty (--allow-dirty):"
    echo "$dirty" | sed 's/^/           /'
  else
    fail "working tree is dirty; commit or stash first (or --allow-dirty):"
    echo "$dirty" | sed 's/^/           /'
  fi
  local branch
  branch="$(git -C "$ROOT_DIR" rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"
  info "  branch: $branch"
}

backup_age_seconds() {
  local dir="$1"
  local marker="$dir/last_success.prom"
  [[ -f "$marker" ]] || return 1
  local ts now
  ts="$(awk '/backup_last_success_timestamp/{v=$2} END{print v}' "$marker")"
  [[ -n "$ts" ]] || return 1
  now="$(date +%s)"
  echo $((now - ts))
}

check_backup() {
  info "Backup freshness (max $MAX_BACKUP_AGE_HOURS h)"
  local metric="${BACKUP_METRIC_FILE:-}"
  if [[ -n "$metric" && -f "$metric" ]]; then
    BACKUP_DIRS+=("$(dirname "$metric")")
  fi
  local max_seconds=$((MAX_BACKUP_AGE_HOURS * 3600))
  local found=false newest_age="" newest_dir=""
  local dir age
  for dir in "${BACKUP_DIRS[@]}"; do
    if age="$(backup_age_seconds "$dir")"; then
      found=true
      if [[ -z "$newest_age" || "$age" -lt "$newest_age" ]]; then
        newest_age="$age"
        newest_dir="$dir"
      fi
    fi
  done
  if [[ "$found" != true ]]; then
    fail "no last_success.prom found in: ${BACKUP_DIRS[*]}"
    return 0
  fi
  local hours=$((newest_age / 3600))
  if [[ "$newest_age" -le "$max_seconds" ]]; then
    pass "newest backup is ${hours}h old ($newest_dir)"
  else
    fail "newest backup is ${hours}h old (> ${MAX_BACKUP_AGE_HOURS}h) ($newest_dir)"
  fi
}

disk_free_gb() {
  local path="$1"
  df -Pk "$path" | awk 'NR==2{printf "%d", $4/1024/1024}'
}

check_disk() {
  info "Free disk space (min ${MIN_FREE_GB} GB)"
  local target="$ROOT_DIR"
  if [[ -d "${BACKUP_DIRS[0]}" ]]; then
    target="${BACKUP_DIRS[0]}"
  fi
  local free
  free="$(disk_free_gb "$target")"
  if [[ -z "$free" ]]; then
    fail "could not determine free space for $target"
  elif [[ "$free" -ge "$MIN_FREE_GB" ]]; then
    pass "${free} GB free on $target"
  else
    fail "only ${free} GB free on $target (< ${MIN_FREE_GB} GB)"
  fi
}

helm_upgrade_command() {
  local cmd="helm upgrade $RELEASE \"$CHART\" --namespace \"$NAMESPACE\" --install --atomic --timeout 10m"
  local vf
  for vf in "${VALUES_FILES[@]}"; do
    cmd="$cmd --values \"$vf\""
  done
  echo "$cmd"
}

check_helm() {
  info "Helm / chart"
  if ! command -v helm &> /dev/null; then
    fail "helm not found in PATH (install Helm 3, or --skip-helm)"
    return 0
  fi
  pass "helm $(helm version --short 2>/dev/null || echo '?')"
  if [[ -d "$CHART" ]]; then
    if helm lint "$CHART" > /dev/null 2>&1; then
      pass "helm lint $CHART"
    else
      fail "helm lint $CHART failed (run 'helm lint $CHART' for details)"
    fi
  else
    fail "chart directory not found: $CHART"
  fi
  if [[ "$HELM_DIFF" == true ]]; then
    if helm plugin list 2>/dev/null | grep -q '^diff'; then
      info "  running helm diff upgrade ..."
      # shellcheck disable=SC2086
      helm diff upgrade "$RELEASE" "$CHART" --namespace "$NAMESPACE" >/dev/null \
        && pass "helm diff upgrade" || warn "  [warn] helm diff reported differences"
    else
      skip "helm-diff plugin not installed"
    fi
  fi
}

check_kubectl() {
  info "Kubernetes API"
  if ! command -v kubectl &> /dev/null; then
    fail "kubectl not found in PATH (or --skip-kubectl)"
    return 0
  fi
  if kubectl version --request-timeout=5s > /dev/null 2>&1; then
    pass "kubectl can reach the API server"
  else
    fail "kubectl cannot reach the API server"
  fi
}

confirmation_ok() {
  local expected="$1"
  local answer="$2"
  [[ "$answer" == "$expected" || "$answer" == "yes" || "$answer" == "y" || "$answer" == "Y" ]]
}

self_test() {
  local failures=0
  local tmp
  tmp="$(mktemp -d)"
  trap 'rm -rf "${tmp:-}"' EXIT

  # backup age parsing
  mkdir -p "$tmp/backups"
  printf 'backup_last_success_timestamp %s\n' "$(date +%s)" > "$tmp/backups/last_success.prom"
  local age
  if age="$(backup_age_seconds "$tmp/backups")" && [[ "$age" -ge 0 && "$age" -lt 60 ]]; then
    info "self-test: backup age parsing OK"
  else
    error "self-test: backup age parsing FAILED (got '${age:-}')"
    failures=$((failures + 1))
  fi
  if backup_age_seconds "$tmp/empty" 2>/dev/null; then
    error "self-test: missing marker should fail"
    failures=$((failures + 1))
  else
    info "self-test: missing marker detection OK"
  fi

  # disk free returns a number
  local gb
  gb="$(disk_free_gb "$tmp")"
  if [[ "$gb" =~ ^[0-9]+$ ]]; then
    info "self-test: disk free parsing OK (${gb} GB)"
  else
    error "self-test: disk free parsing FAILED"
    failures=$((failures + 1))
  fi

  # confirmation gating
  if confirmation_ok "upgrade" "upgrade" && confirmation_ok "upgrade" "yes" \
     && ! confirmation_ok "upgrade" "nope"; then
    info "self-test: confirmation gating OK"
  else
    error "self-test: confirmation gating FAILED"
    failures=$((failures + 1))
  fi

  if [[ "$failures" == "0" ]]; then
    success "self-test: all checks passed"
    return 0
  fi
  error "self-test: $failures check(s) failed"
  return 1
}

if [[ "$SELF_TEST" == true ]]; then
  self_test
  exit $?
fi

info "Infra Pilot upgrade pre-flight (release=$RELEASE chart=$CHART)"

[[ "$SKIP_GIT" == true ]]     || check_git
[[ "$SKIP_BACKUP" == true ]]  || check_backup
[[ "$SKIP_DISK" == true ]]    || check_disk
[[ "$SKIP_HELM" == true ]]    || check_helm
[[ "$SKIP_KUBECTL" == true ]] || check_kubectl

if [[ "$SKIP_KUBECTL" == false ]]; then
  resolve_namespace 2>/dev/null || true
fi
NAMESPACE="${NAMESPACE:-default}"

if [[ "$FAILED" -gt 0 ]]; then
  error "Pre-flight failed: $FAILED check(s) did not pass."
  exit 1
fi

success "Pre-flight passed."
info "Upgrade command:"
info "  $(helm_upgrade_command)"

if [[ "$CHECK_ONLY" == true ]]; then
  exit 0
fi

if [[ "$ASSUME_YES" != true ]]; then
  read -r -p "Type 'upgrade' to run the upgrade now (anything else aborts): " answer
  if ! confirmation_ok "upgrade" "$answer"; then
    info "Aborted; no changes made."
    exit 0
  fi
fi

if [[ "$EXECUTE" != true ]]; then
  info "Dry pre-flight only: pass --execute to actually run the upgrade."
  exit 0
fi

if ! command -v helm &> /dev/null; then
  error "helm not found in PATH; cannot execute."
  exit 1
fi

# shellcheck disable=SC2086
eval "$(helm_upgrade_command)"
success "Upgrade finished: $RELEASE"
