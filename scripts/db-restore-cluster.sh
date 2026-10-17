#!/usr/bin/env bash
# Restore the Infra Pilot PostgreSQL database inside a Kubernetes cluster
# (Helm release) from a pg_dump custom-format backup. Counterpart of
# scripts/db-restore.sh for the Compose stack, with a mandatory confirmation
# prompt, a --dry-run validation mode and optional GPG decryption.
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

usage() {
  cat <<EOF
Restore the Infra Pilot PostgreSQL database inside a Kubernetes cluster.

Usage: $(basename "$0") <backup-file.dump[.gpg]> [OPTIONS]
       $(basename "$0") --from-s3 s3://bucket/path.dump [OPTIONS]

Input:
  <backup-file>         Local pg_dump custom-format backup (or .gpg)
  --from-s3 URI         Download the backup from S3 first (requires aws CLI)

Connection:
  --namespace NS        Kubernetes namespace (default: current context namespace)
  --release NAME        Helm release name, used to find the PostgreSQL pod
  --pod POD             Explicit PostgreSQL pod name (skips discovery)
  --container NAME      Container inside the pod (default: postgresql)
  --db NAME             Database name (default: infrapilot)
  --user NAME           Database role (default: infrapilot)
  --secret NAME         Secret holding the password (default: infra-pilot-secrets)
  --password-key KEY    Secret key holding the password (default: db-password)
  --port-forward        Use kubectl port-forward + a local pg_restore instead of
                        'kubectl exec' inside the pod (requires pg_restore locally)
  --local-port PORT     Local port for --port-forward (default: 15432)

Behaviour:
  --yes                 Skip the confirmation prompt (for automation)
  --dry-run             Validate the archive only; never touch the database
  --no-clean            Do not pass --clean --if-exists to pg_restore
  --stop-writers        Scale down release Deployments before restoring
  --start-writers       Scale release Deployments back up after restoring
  --self-test           Run internal self tests (no cluster required) and exit
  --help                Show this help message

Notes:
  - Restoring replaces data (--clean --if-exists by default). Stop the
    services that write to the database first:
      docker compose stop ...            # Compose
      $(basename "$0") --release infra-pilot --stop-writers --start-writers <dump>
  - The restore validates the pg_dump header and, when possible, runs
    'pg_restore --list' before changing anything.
  - GPG-encrypted artifacts are decrypted to a temporary file automatically.
  - See docs/OPERATIONS.md for the disaster-recovery runbook.
EOF
  exit "${1:-0}"
}

BACKUP_FILE=""
FROM_S3=""
NAMESPACE="${KUBE_NAMESPACE:-}"
RELEASE=""
POD=""
CONTAINER="postgresql"
DB_NAME="${POSTGRES_DB:-infrapilot}"
DB_USER="${POSTGRES_USER:-infrapilot}"
SECRET_NAME="infra-pilot-secrets"
PASSWORD_KEY="db-password"
MODE="exec"
LOCAL_PORT="15432"
ASSUME_YES=false
DRY_RUN=false
CLEAN=true
STOP_WRITERS=false
START_WRITERS=false
SELF_TEST=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --from-s3) FROM_S3="$2"; shift 2 ;;
    --namespace) NAMESPACE="$2"; shift 2 ;;
    --release) RELEASE="$2"; shift 2 ;;
    --pod) POD="$2"; shift 2 ;;
    --container) CONTAINER="$2"; shift 2 ;;
    --db) DB_NAME="$2"; shift 2 ;;
    --user) DB_USER="$2"; shift 2 ;;
    --secret) SECRET_NAME="$2"; shift 2 ;;
    --password-key) PASSWORD_KEY="$2"; shift 2 ;;
    --port-forward) MODE="port-forward"; shift ;;
    --local-port) LOCAL_PORT="$2"; shift 2 ;;
    --yes) ASSUME_YES=true; shift ;;
    --dry-run) DRY_RUN=true; shift ;;
    --no-clean) CLEAN=false; shift ;;
    --stop-writers) STOP_WRITERS=true; shift ;;
    --start-writers) START_WRITERS=true; shift ;;
    --self-test) SELF_TEST=true; shift ;;
    --help) usage ;;
    -*) error "Unknown option: $1"; usage 2 ;;
    *)
      if [[ -n "$BACKUP_FILE" ]]; then
        error "Multiple backup files given"
        usage 2
      fi
      BACKUP_FILE="$1"; shift ;;
  esac
done

RESTORE_TMP=""
cleanup() {
  if [[ -n "${PF_PID:-}" ]] && kill -0 "$PF_PID" 2>/dev/null; then
    kill "$PF_PID" 2>/dev/null || true
    wait "$PF_PID" 2>/dev/null || true
  fi
  if [[ -n "$RESTORE_TMP" ]]; then
    rm -f "$RESTORE_TMP"
  fi
}
trap cleanup EXIT

require_cmd() {
  if ! command -v "$1" &> /dev/null; then
    error "$1 not found in PATH${2:+ ($2)}"
    exit 1
  fi
}

is_pgdump_header() {
  local file="$1"
  [[ -f "$file" ]] && [[ "$(head -c 5 "$file" 2>/dev/null || true)" == "PGDMP" ]]
}

resolve_namespace() {
  if [[ -n "$NAMESPACE" ]]; then
    return 0
  fi
  NAMESPACE="$(kubectl config view --minify -o jsonpath='{..namespace}' 2>/dev/null || true)"
  NAMESPACE="${NAMESPACE:-default}"
}

postgres_selector() {
  local selector="app.kubernetes.io/name=postgresql"
  if [[ -n "$RELEASE" ]]; then
    selector="${selector},app.kubernetes.io/instance=${RELEASE}"
  fi
  echo "$selector"
}

discover_pod() {
  kubectl -n "$NAMESPACE" get pods -l "$(postgres_selector)" \
    --field-selector=status.phase=Running \
    -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || true
}

read_secret_key() {
  kubectl -n "$NAMESPACE" get secret "$1" -o "jsonpath={.data.${2}}" 2>/dev/null \
    | base64 --decode 2>/dev/null || true
}

port_open() {
  (exec 3<>"/dev/tcp/127.0.0.1/${1}") 2>/dev/null
}

scaled_state_file() {
  echo "${RESTORE_STATE_FILE:-/tmp/infra-pilot-restore-writers.state}"
}

stop_writers() {
  if [[ -z "$RELEASE" ]]; then
    error "--stop-writers requires --release (deployments are matched by label)"
    exit 1
  fi
  local state
  state="$(scaled_state_file)"
  : > "$state"
  info "Scaling down Deployments for release $RELEASE ..."
  local name replicas
  while read -r name replicas; do
    [[ -z "$name" ]] && continue
    printf '%s %s\n' "$name" "$replicas" >> "$state"
    kubectl -n "$NAMESPACE" scale "deployment/$name" --replicas=0
  done < <(kubectl -n "$NAMESPACE" get deployments \
      -l "app.kubernetes.io/instance=${RELEASE}" \
      -o 'jsonpath={range .items[*]}{.metadata.name}{" "}{.spec.replicas}{"\n"}{end}' 2>/dev/null || true)
  if [[ -s "$state" ]]; then
    success "Scaled down $(wc -l < "$state" | tr -d ' ') Deployment(s); state saved to $state"
  else
    warn "No Deployments found for release $RELEASE."
  fi
}

start_writers() {
  local state
  state="$(scaled_state_file)"
  if [[ ! -f "$state" ]]; then
    warn "No saved writer state at $state; scaling all release Deployments to 1."
    if [[ -n "$RELEASE" ]]; then
      kubectl -n "$NAMESPACE" scale "deployment" -l "app.kubernetes.io/instance=${RELEASE}" --replicas=1
    fi
    return 0
  fi
  info "Scaling Deployments back up ..."
  local name replicas
  while read -r name replicas; do
    [[ -z "$name" ]] && continue
    kubectl -n "$NAMESPACE" scale "deployment/$name" --replicas="$replicas"
  done < "$state"
  success "Restored worker Deployments from $state"
}

self_test() {
  local failures=0
  local tmp
  tmp="$(mktemp -d)"
  trap 'rm -rf "${tmp:-}"' EXIT

  printf 'PGDMPfake' > "$tmp/good.dump"
  printf 'NOTA-dump' > "$tmp/bad.dump"
  if is_pgdump_header "$tmp/good.dump"; then
    info "self-test: header detection (positive) OK"
  else
    error "self-test: header detection (positive) FAILED"
    failures=$((failures + 1))
  fi
  if is_pgdump_header "$tmp/bad.dump"; then
    error "self-test: header detection (negative) FAILED"
    failures=$((failures + 1))
  else
    info "self-test: header detection (negative) OK"
  fi

  RELEASE="demo"
  if [[ "$(postgres_selector)" == *"app.kubernetes.io/instance=demo"* ]]; then
    info "self-test: pod selector OK"
  else
    error "self-test: pod selector FAILED"
    failures=$((failures + 1))
  fi
  RELEASE=""

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

if [[ -n "$BACKUP_FILE" && -n "$FROM_S3" ]]; then
  error "Use either a backup file or --from-s3, not both"
  usage 2
fi

if [[ "$STOP_WRITERS" == true || "$START_WRITERS" == true ]]; then
  require_cmd kubectl
  resolve_namespace
  if [[ "$STOP_WRITERS" == true ]]; then
    stop_writers
  fi
  if [[ "$START_WRITERS" == true ]]; then
    start_writers
  fi
  if [[ -z "$BACKUP_FILE" && -z "$FROM_S3" ]]; then
    exit 0
  fi
fi

if [[ -z "$BACKUP_FILE" && -z "$FROM_S3" ]]; then
  error "Missing backup file (or --from-s3)"
  usage 2
fi

RESTORE_FILE="$BACKUP_FILE"

if [[ -n "$FROM_S3" ]]; then
  require_cmd aws "required for --from-s3"
  RESTORE_TMP="$(mktemp --suffix=.dump)"
  info "Downloading $FROM_S3 ..."
  aws s3 cp "$FROM_S3" "$RESTORE_TMP"
  RESTORE_FILE="$RESTORE_TMP"
fi

if [[ ! -f "$RESTORE_FILE" ]]; then
  error "Backup file not found: $RESTORE_FILE"
  exit 1
fi

if [[ "$RESTORE_FILE" == *.gpg ]]; then
  require_cmd gpg "required to decrypt $RESTORE_FILE"
  decrypted="$(mktemp --suffix=.dump)"
  info "Decrypting $(basename "$RESTORE_FILE") ..."
  gpg --batch --yes --decrypt --output "$decrypted" "$RESTORE_FILE"
  if [[ -n "$RESTORE_TMP" ]]; then
    rm -f "$RESTORE_TMP"
  fi
  RESTORE_TMP="$decrypted"
  RESTORE_FILE="$decrypted"
fi

if ! is_pgdump_header "$RESTORE_FILE"; then
  error "Not a pg_dump custom-format backup: $RESTORE_FILE"
  exit 1
fi

if [[ "$DRY_RUN" == true ]]; then
  if command -v kubectl &> /dev/null; then
    resolve_namespace
    if [[ -z "$POD" ]]; then
      POD="$(discover_pod)"
    fi
  fi
  if [[ -n "$POD" ]]; then
    info "Validating archive with pg_restore --list inside $POD (no database writes) ..."
    kubectl -n "$NAMESPACE" exec -i "$POD" -c "$CONTAINER" -- pg_restore --list - < "$RESTORE_FILE" > /dev/null
    success "Dry-run OK: archive TOC is readable."
  elif command -v pg_restore &> /dev/null; then
    pg_restore --list "$RESTORE_FILE" > /dev/null
    success "Dry-run OK (local pg_restore)."
  else
    warn "No PostgreSQL pod and no local pg_restore; header check only."
    success "Dry-run OK: header looks valid."
  fi
  exit 0
fi

require_cmd kubectl
if [[ "$MODE" == "port-forward" ]]; then
  require_cmd pg_restore "required for --port-forward"
fi
resolve_namespace

if [[ -z "$POD" ]]; then
  info "Discovering PostgreSQL pod ($(postgres_selector)) in namespace $NAMESPACE ..."
  POD="$(discover_pod)"
fi
if [[ -z "$POD" ]]; then
  error "No running PostgreSQL pod found. Pass --pod explicitly."
  exit 1
fi

info "About to restore $(basename "$RESTORE_FILE") into '$DB_NAME' as '$DB_USER'."
info "Target: namespace $NAMESPACE, pod $POD."
if [[ "$CLEAN" == true ]]; then
  warn "Existing objects will be dropped (pg_restore --clean --if-exists)."
fi
info "Stop the services that write to the database first (or use --stop-writers)."

if [[ "$ASSUME_YES" != true ]]; then
  read -r -p "Type 'yes' (or '$DB_NAME') to continue: " answer
  if [[ "$answer" != "yes" && "$answer" != "$DB_NAME" && "$answer" != "y" && "$answer" != "Y" ]]; then
    info "Restore cancelled."
    exit 0
  fi
fi

PGPASSWORD_VALUE="${PGPASSWORD:-}"
if [[ -z "$PGPASSWORD_VALUE" ]]; then
  PGPASSWORD_VALUE="$(read_secret_key "$SECRET_NAME" "$PASSWORD_KEY")"
fi
if [[ -z "$PGPASSWORD_VALUE" ]]; then
  error "Could not read $SECRET_NAME/$PASSWORD_KEY. Pass an existing Secret or export PGPASSWORD."
  exit 1
fi

RESTORE_FLAGS=(--no-owner)
if [[ "$CLEAN" == true ]]; then
  RESTORE_FLAGS=(--clean --if-exists "${RESTORE_FLAGS[@]}")
fi

if [[ "$MODE" == "exec" ]]; then
  info "Restoring via kubectl exec into $POD ..."
  kubectl -n "$NAMESPACE" exec -i "$POD" -c "$CONTAINER" -- \
    env PGPASSWORD="$PGPASSWORD_VALUE" \
    pg_restore "${RESTORE_FLAGS[@]}" -U "$DB_USER" -d "$DB_NAME" - < "$RESTORE_FILE"
else
  info "Starting port-forward 127.0.0.1:${LOCAL_PORT} -> ${POD}:5432 ..."
  kubectl -n "$NAMESPACE" port-forward "pod/$POD" "${LOCAL_PORT}:5432" > /dev/null 2>&1 &
  PF_PID=$!
  for _ in $(seq 1 30); do
    port_open "$LOCAL_PORT" && break
    sleep 1
  done
  PGPASSWORD="$PGPASSWORD_VALUE" pg_restore "${RESTORE_FLAGS[@]}" \
    -h 127.0.0.1 -p "$LOCAL_PORT" -U "$DB_USER" -d "$DB_NAME" "$RESTORE_FILE"
fi

success "Restore completed from: $(basename "$RESTORE_FILE")"
info "Restart the services if you scaled them down (--start-writers)."
info "Verify with: kubectl -n $NAMESPACE exec $POD -- psql -U $DB_USER -d $DB_NAME -c '\\dt'"
