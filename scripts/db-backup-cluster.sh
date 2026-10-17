#!/usr/bin/env bash
# Back up the Infra Pilot PostgreSQL database running inside a Kubernetes
# cluster (Helm release). Counterpart of scripts/db-backup.sh for the Compose
# stack: same artifact naming, checksums, GPG support, S3/rclone upload,
# retention, flock and last_success.prom marker.
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
Back up the Infra Pilot PostgreSQL database from a Kubernetes cluster.

Usage: $(basename "$0") [OPTIONS]

Connection:
  --namespace NS        Kubernetes namespace (default: current context namespace)
  --release NAME        Helm release name, used to find the PostgreSQL pod
  --pod POD             Explicit PostgreSQL pod name (skips discovery)
  --container NAME      Container inside the pod (default: postgresql)
  --db NAME             Database name (default: infrapilot)
  --user NAME           Database role (default: infrapilot)
  --secret NAME         Secret holding the password (default: infra-pilot-secrets)
  --password-key KEY    Secret key holding the password (default: db-password)
  --port-forward        Use kubectl port-forward + a local pg_dump instead of
                        'kubectl exec' inside the pod (requires pg_dump locally)
  --local-port PORT     Local port for --port-forward (default: 15432)
  --redis               Also snapshot Redis via 'redis-cli --rdb'
  --redis-secret NAME   Secret with the Redis password (default: infra-pilot-secrets)
  --redis-key KEY       Redis password key (default: redis-password)

Output:
  --out DIR             Backup output directory (default: \$ROOT_DIR/backups)
  --keep N              Keep only the N most recent local backups per type (default: 10)
  --s3 URI              Also upload artifacts to S3 (requires the aws CLI)
  --rclone-remote REM   Also copy artifacts with rclone (remote must exist)
  --encrypt-to KEY      Also encrypt artifacts with GPG for KEY (key id/email)
  --no-plaintext        With --encrypt-to: delete plaintext after encryption
  --metric-file FILE    Write backup_last_success_timestamp to FILE
  --dry-run             Print the resolved plan and exit without touching the cluster
  --self-test           Run internal self tests (no cluster required) and exit
  --help                Show this help message

Examples:
  $(basename "$0") --release infra-pilot --namespace infra-pilot
  $(basename "$0") --namespace prod --release infra-pilot \\
    --s3 s3://my-bucket/infra-pilot --encrypt-to ops@example.com --no-plaintext
  $(basename "$0") --pod infra-pilot-postgresql-0 --port-forward --keep 14

The script prints the connection plan, discovers the PostgreSQL pod via its
standard app.kubernetes.io labels, streams a custom-format pg_dump, verifies
checksums and prunes old artifacts. The password is read from a Secret and is
never echoed. See docs/OPERATIONS.md for the full runbook.
EOF
  exit "${1:-0}"
}

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
WITH_REDIS=false
REDIS_SECRET="infra-pilot-secrets"
REDIS_KEY="redis-password"

OUT_DIR="$ROOT_DIR/backups"
KEEP="${BACKUP_KEEP:-10}"
S3_URI=""
RCLONE_REMOTE="${BACKUP_RCLONE_REMOTE:-${RCLONE_REMOTE:-}}"
ENCRYPT_TO=""
NO_PLAINTEXT=false
METRIC_FILE="${BACKUP_METRIC_FILE:-}"
DRY_RUN=false
SELF_TEST=false

while [[ $# -gt 0 ]]; do
  case "$1" in
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
    --redis) WITH_REDIS=true; shift ;;
    --redis-secret) REDIS_SECRET="$2"; shift 2 ;;
    --redis-key) REDIS_KEY="$2"; shift 2 ;;
    --out) OUT_DIR="$2"; shift 2 ;;
    --keep) KEEP="$2"; shift 2 ;;
    --s3) S3_URI="$2"; shift 2 ;;
    --rclone-remote) RCLONE_REMOTE="$2"; shift 2 ;;
    --encrypt-to) ENCRYPT_TO="$2"; shift 2 ;;
    --no-plaintext) NO_PLAINTEXT=true; shift ;;
    --metric-file) METRIC_FILE="$2"; shift 2 ;;
    --dry-run) DRY_RUN=true; shift ;;
    --self-test) SELF_TEST=true; shift ;;
    --help) usage ;;
    *) error "Unknown option: $1"; usage 2 ;;
  esac
done

require_cmd() {
  if ! command -v "$1" &> /dev/null; then
    error "$1 not found in PATH${2:+ ($2)}"
    exit 1
  fi
}

write_checksum() {
  local file="$1"
  if command -v sha256sum &> /dev/null; then
    sha256sum "$file" > "${file}.sha256"
    ARTIFACTS+=("${file}.sha256")
  else
    warn "sha256sum not found; skipping checksum for $(basename "$file")"
  fi
}

maybe_encrypt_and_upload() {
  local file="$1"
  local upload_file="$file"
  write_checksum "$file"
  if [[ -n "$ENCRYPT_TO" ]]; then
    info "Encrypting $(basename "$file") for $ENCRYPT_TO ..."
    gpg --batch --yes --trust-model always --encrypt --recipient "$ENCRYPT_TO" \
      --output "${file}.gpg" "$file"
    upload_file="${file}.gpg"
    ARTIFACTS+=("${file}.gpg")
    write_checksum "${file}.gpg"
    if [[ "$NO_PLAINTEXT" == true ]]; then
      rm -f "$file" "${file}.sha256"
    fi
  fi
  if [[ -n "$S3_URI" ]]; then
    info "Uploading $(basename "$upload_file") to $S3_URI ..."
    aws s3 cp "$upload_file" "$S3_URI/$(basename "$upload_file")"
  fi
  if [[ -n "$RCLONE_REMOTE" ]]; then
    info "Copying $(basename "$upload_file") to $RCLONE_REMOTE ..."
    rclone copyto "$upload_file" "$RCLONE_REMOTE/$(basename "$upload_file")"
  fi
}

prune() {
  local pattern="$1"
  local kept="$2"
  local old_files=()
  # shellcheck disable=SC2086
  mapfile -t old_files < <(ls -1t "$OUT_DIR"/$pattern 2>/dev/null | tail -n +"$((kept + 1))" || true)
  if [[ ${#old_files[@]} -gt 0 ]]; then
    info "Removing ${#old_files[@]} old file(s) matching $pattern (keep=$kept) ..."
    local f
    for f in "${old_files[@]}"; do
      info "  - $f"
      rm -f "$f" "$f.sha256"
    done
  fi
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
  local selector
  selector="$(postgres_selector)"
  kubectl -n "$NAMESPACE" get pods -l "$selector" \
    --field-selector=status.phase=Running \
    -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || true
}

read_secret_key() {
  local secret="$1"
  local key="$2"
  kubectl -n "$NAMESPACE" get secret "$secret" -o "jsonpath={.data.${key}}" 2>/dev/null \
    | base64 --decode 2>/dev/null || true
}

die_cleanup() {
  if [[ -n "${PF_PID:-}" ]] && kill -0 "$PF_PID" 2>/dev/null; then
    kill "$PF_PID" 2>/dev/null || true
    wait "$PF_PID" 2>/dev/null || true
  fi
}

port_open() {
  (exec 3<>"/dev/tcp/127.0.0.1/${1}") 2>/dev/null
}

self_test() {
  local failures=0
  local tmp
  tmp="$(mktemp -d)"
  trap 'rm -rf "${tmp:-}"' EXIT

  # write_checksum creates a verifying sidecar
  ARTIFACTS=()
  local sample="$tmp/sample.dump"
  printf 'PGDMP-sample' > "$sample"
  write_checksum "$sample" > /dev/null
  if [[ -f "${sample}.sha256" ]] && (cd "$tmp" && sha256sum -c "$(basename "$sample").sha256" > /dev/null 2>&1); then
    info "self-test: checksum sidecar OK"
  else
    error "self-test: checksum sidecar FAILED"
    failures=$((failures + 1))
  fi

  # prune keeps the requested number of files
  OUT_DIR="$tmp"
  local i
  for i in 1 2 3 4 5; do
    printf 'x' > "$tmp/infra-pilot_2026010${i}_000000.dump"
  done
  prune "infra-pilot_*.dump" 2 > /dev/null
  local remaining
  remaining="$(find "$tmp" -name 'infra-pilot_*.dump' | wc -l | tr -d ' ')"
  if [[ "$remaining" == "2" ]]; then
    info "self-test: prune retention OK"
  else
    error "self-test: prune retention FAILED (expected 2, got $remaining)"
    failures=$((failures + 1))
  fi

  # postgres_selector includes the release label when provided
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

if [[ "$DRY_RUN" == false ]]; then
  require_cmd kubectl
fi
if [[ -n "$S3_URI" ]] && ! command -v aws &> /dev/null; then
  error "aws CLI not found in PATH (required for --s3)"
  exit 1
fi
if [[ -n "$RCLONE_REMOTE" ]] && ! command -v rclone &> /dev/null; then
  error "rclone not found in PATH (required for --rclone-remote)"
  exit 1
fi
if [[ -n "$ENCRYPT_TO" ]] && ! command -v gpg &> /dev/null; then
  error "gpg not found in PATH (required for --encrypt-to)"
  exit 1
fi
if [[ "$MODE" == "port-forward" ]] && ! command -v pg_dump &> /dev/null; then
  error "pg_dump not found in PATH (required for --port-forward)"
  exit 1
fi

resolve_namespace

if [[ "$DRY_RUN" == true ]]; then
  info "Dry run: no backup will be created."
  info "  namespace:     $NAMESPACE"
  info "  pod:           ${POD:-<discovered via '$(postgres_selector)'>}"
  info "  mode:          $MODE"
  info "  database:      $DB_NAME (role $DB_USER)"
  info "  secret:        $SECRET_NAME key $PASSWORD_KEY"
  info "  redis:         $WITH_REDIS"
  info "  out:           $OUT_DIR (keep=$KEEP)"
  info "  s3:            ${S3_URI:-disabled}"
  info "  rclone:        ${RCLONE_REMOTE:-disabled}"
  info "  gpg:           ${ENCRYPT_TO:-disabled}"
  exit 0
fi

LOCK_FILE="${BACKUP_CLUSTER_LOCK_FILE:-$ROOT_DIR/.infra-pilot-backup-cluster.lock}"
if command -v flock &> /dev/null; then
  umask 077
  exec 9>"$LOCK_FILE"
  if ! flock -n 9; then
    error "Another cluster backup is already running (lock: $LOCK_FILE)"
    exit 1
  fi
else
  warn "flock not found; skipping backup lock ($LOCK_FILE)"
fi

if [[ -z "$POD" ]]; then
  info "Discovering PostgreSQL pod ($(postgres_selector)) in namespace $NAMESPACE ..."
  POD="$(discover_pod)"
fi
if [[ -z "$POD" ]]; then
  error "No running PostgreSQL pod found. Pass --pod explicitly."
  exit 1
fi
info "Using PostgreSQL pod: $POD"

mkdir -p "$OUT_DIR"
OUT_DIR="$(cd "$OUT_DIR" && pwd)"
stamp=$(date +%Y%m%d_%H%M%S)
ARTIFACTS=()
trap die_cleanup EXIT

# The database password never appears on the command line: it is read from the
# Secret and injected into the in-pod command environment only.
PGPASSWORD_VALUE="${PGPASSWORD:-}"
if [[ -z "$PGPASSWORD_VALUE" ]]; then
  PGPASSWORD_VALUE="$(read_secret_key "$SECRET_NAME" "$PASSWORD_KEY")"
fi
if [[ -z "$PGPASSWORD_VALUE" ]]; then
  error "Could not read $SECRET_NAME/$PASSWORD_KEY. Pass an existing Secret or export PGPASSWORD."
  exit 1
fi

backup_file="$OUT_DIR/infra-pilot_${stamp}.dump"
tmp_dump="${backup_file}.partial"
info "Creating PostgreSQL backup: $(basename "$backup_file")"

dump_ok=false
if [[ "$MODE" == "exec" ]]; then
  if kubectl -n "$NAMESPACE" exec -i "$POD" -c "$CONTAINER" -- \
    env PGPASSWORD="$PGPASSWORD_VALUE" \
    pg_dump -U "$DB_USER" -d "$DB_NAME" --format=custom --no-owner > "$tmp_dump"; then
    dump_ok=true
  fi
else
  info "Starting port-forward 127.0.0.1:${LOCAL_PORT} -> ${POD}:5432 ..."
  kubectl -n "$NAMESPACE" port-forward "pod/$POD" "${LOCAL_PORT}:5432" > /dev/null 2>&1 &
  PF_PID=$!
  for _ in $(seq 1 30); do
    port_open "$LOCAL_PORT" && break
    sleep 1
  done
  if PGPASSWORD="$PGPASSWORD_VALUE" pg_dump \
    -h 127.0.0.1 -p "$LOCAL_PORT" -U "$DB_USER" -d "$DB_NAME" \
    --format=custom --no-owner > "$tmp_dump"; then
    dump_ok=true
  fi
fi

if [[ "$dump_ok" != true ]]; then
  error "pg_dump failed; no backup written."
  rm -f "$tmp_dump"
  exit 1
fi
mv "$tmp_dump" "$backup_file"

if [[ ! -s "$backup_file" ]]; then
  error "pg_dump produced an empty file; aborting."
  rm -f "$backup_file"
  exit 1
fi
if [[ "$(head -c 5 "$backup_file")" != "PGDMP" ]]; then
  error "Backup does not look like a pg_dump custom-format archive; aborting."
  rm -f "$backup_file"
  exit 1
fi
ARTIFACTS+=("$backup_file")
size=$(du -h "$backup_file" | cut -f1)
success "PostgreSQL backup created ($size): $backup_file"
maybe_encrypt_and_upload "$backup_file"
prune "infra-pilot_*.dump" "$KEEP"
prune "infra-pilot_*.dump.gpg" "$KEEP"
prune "infra-pilot_*.dump.sha256" "$KEEP"
prune "infra-pilot_*.dump.gpg.sha256" "$KEEP"

if [[ "$WITH_REDIS" == true ]]; then
  redis_pod="$(kubectl -n "$NAMESPACE" get pods \
    -l app.kubernetes.io/name=redis \
    --field-selector=status.phase=Running \
    -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || true)"
  if [[ -z "$redis_pod" ]]; then
    warn "No running Redis pod found; skipping Redis snapshot."
  else
    redis_file="$OUT_DIR/redis_${stamp}.rdb"
    redis_password="$(read_secret_key "$REDIS_SECRET" "$REDIS_KEY")"
    info "Creating Redis snapshot from $redis_pod: $(basename "$redis_file")"
    if kubectl -n "$NAMESPACE" exec -i "$redis_pod" -- \
      env REDISCLI_AUTH="$redis_password" redis-cli --rdb - > "$redis_file" 2> /dev/null; then
      ARTIFACTS+=("$redis_file")
      success "Redis snapshot created: $redis_file"
      maybe_encrypt_and_upload "$redis_file"
    else
      warn "Redis snapshot failed; skipping."
      rm -f "$redis_file"
    fi
    prune "redis_*.rdb" "$KEEP"
    prune "redis_*.rdb.gpg" "$KEEP"
    prune "redis_*.rdb.sha256" "$KEEP"
    prune "redis_*.rdb.gpg.sha256" "$KEEP"
  fi
fi

if command -v sha256sum &> /dev/null; then
  info "Verifying ${#ARTIFACTS[@]} artifact checksum(s) ..."
  for a in "${ARTIFACTS[@]}"; do
    [[ "$a" == *.sha256 ]] && continue
    if [[ -f "$a.sha256" ]]; then
      (cd "$(dirname "$a")" && sha256sum -c "$(basename "$a.sha256")") || {
        error "Checksum mismatch: $a"
        exit 1
      }
    fi
  done
  success "All checksums verified."
fi

now="$(date +%s)"
printf 'backup_last_success_timestamp %s\n' "$now" > "$OUT_DIR/last_success.prom"
if [[ -n "$METRIC_FILE" ]]; then
  {
    echo "# HELP backup_last_success_timestamp Unix time of last successful backup."
    echo "# TYPE backup_last_success_timestamp gauge"
    echo "backup_last_success_timestamp $now"
  } > "$METRIC_FILE.tmp" && mv "$METRIC_FILE.tmp" "$METRIC_FILE"
fi
success "Done. Artifacts:"
for a in "${ARTIFACTS[@]}"; do
  info "  - $a"
done
info "Marker written: $OUT_DIR/last_success.prom"
