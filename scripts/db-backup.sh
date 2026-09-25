#!/usr/bin/env bash
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
Create backups of the Infra Pilot state (Postgres, Redis, Grafana data).

Usage: $(basename "$0") [OPTIONS]

Options:
  --keep N          Keep only the N most recent backups per type (default: 10)
  --out DIR         Backup output directory (default: \$ROOT_DIR/backups)
  --s3 URI          Additionally upload finished artifacts to S3
                    (e.g. s3://my-bucket/infra-pilot); requires the aws CLI
  --encrypt-to KEY  Additionally encrypt artifacts with GPG for KEY
                    (key id, fingerprint or email); requires gpg.
                    Encrypted copies get a .gpg suffix; plaintext is kept
                    unless --no-plaintext is given
  --no-plaintext    With --encrypt-to: delete plaintext after encryption
  --skip-redis      Skip the Redis snapshot
  --skip-grafana    Skip the Grafana data archive
  --help            Show this help message

Scheduling (example cron, daily 02:00, offsite via S3):
  0 2 * * *  /opt/infra-pilot/scripts/db-backup.sh --s3 s3://my-bucket/infra-pilot >> /var/log/infra-pilot-backup.log 2>&1

Restore: see scripts/db-restore.sh (supports .gpg artifacts).
EOF
  exit "${1:-0}"
}

KEEP=10
OUT_DIR="$ROOT_DIR/backups"
S3_URI=""
ENCRYPT_TO=""
NO_PLAINTEXT=false
WITH_REDIS=true
WITH_GRAFANA=true

while [[ $# -gt 0 ]]; do
  case "$1" in
    --keep) KEEP="$2"; shift 2 ;;
    --out) OUT_DIR="$2"; shift 2 ;;
    --s3) S3_URI="$2"; shift 2 ;;
    --encrypt-to) ENCRYPT_TO="$2"; shift 2 ;;
    --no-plaintext) NO_PLAINTEXT=true; shift ;;
    --skip-redis) WITH_REDIS=false; shift ;;
    --skip-grafana) WITH_GRAFANA=false; shift ;;
    --help) usage ;;
    *) echo "Unknown option: $1" >&2; usage 2 ;;
  esac
done

POSTGRES_USER="${POSTGRES_USER:-infra_pilot}"
POSTGRES_DB="${POSTGRES_DB:-infra_pilot}"

if ! command -v docker &> /dev/null; then
  error "docker not found in PATH"
  exit 1
fi

if [[ -n "$S3_URI" ]] && ! command -v aws &> /dev/null; then
  error "aws CLI not found in PATH (required for --s3)"
  exit 1
fi

if [[ -n "$ENCRYPT_TO" ]] && ! command -v gpg &> /dev/null; then
  error "gpg not found in PATH (required for --encrypt-to)"
  exit 1
fi

COMPOSE=(docker compose -f "$ROOT_DIR/docker-compose.yml")

if ! docker compose ls 2>/dev/null | grep -q infra-pilot; then
  info "Infra Pilot stack is not running, starting postgres and redis..."
  "${COMPOSE[@]}" up -d postgres redis
  info "Waiting for postgres to become healthy..."
  for _ in $(seq 1 30); do
    if "${COMPOSE[@]}" exec -T postgres pg_isready -U "$POSTGRES_USER" > /dev/null 2>&1; then
      break
    fi
    sleep 2
  done
fi

mkdir -p "$OUT_DIR"
OUT_DIR="$(cd "$OUT_DIR" && pwd)"
stamp=$(date +%Y%m%d_%H%M%S)
ARTIFACTS=()

maybe_encrypt_and_upload() {
  local file="$1"
  local upload_file="$file"
  if [[ -n "$ENCRYPT_TO" ]]; then
    info "Encrypting $file for $ENCRYPT_TO ..."
    gpg --batch --yes --trust-model always --encrypt --recipient "$ENCRYPT_TO" \
      --output "${file}.gpg" "$file"
    upload_file="${file}.gpg"
    ARTIFACTS+=("${file}.gpg")
    if [[ "$NO_PLAINTEXT" == true ]]; then
      rm -f "$file"
    fi
  fi
  if [[ -n "$S3_URI" ]]; then
    info "Uploading $upload_file to $S3_URI ..."
    aws s3 cp "$upload_file" "$S3_URI/$(basename "$upload_file")"
  fi
}

prune() {
  local pattern="$1"
  local kept="$2"
  # $pattern is intentionally a glob.
  # shellcheck disable=SC2086
  mapfile -t old_files < <(ls -1t "$OUT_DIR"/$pattern 2>/dev/null | tail -n +"$((kept + 1))" || true)
  if [[ ${#old_files[@]} -gt 0 ]]; then
    info "Removing ${#old_files[@]} old file(s) of $pattern (keep=$kept)..."
    for f in "${old_files[@]}"; do
      info "  - $f"
      rm -f "$f"
    done
  fi
}

# --- Postgres (custom-format dump) ---
backup_file="$OUT_DIR/infra-pilot_${stamp}.dump"
info "Creating Postgres backup: $backup_file"
"${COMPOSE[@]}" exec -T postgres \
  pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc > "$backup_file"
ARTIFACTS+=("$backup_file")
size=$(du -h "$backup_file" | cut -f1)
success "Postgres backup created ($size): $backup_file"
maybe_encrypt_and_upload "$backup_file"
prune "infra-pilot_*.dump" "$KEEP"
prune "infra-pilot_*.dump.gpg" "$KEEP"

# --- Redis (RDB snapshot; AOF persists in redis_data volume) ---
if [[ "$WITH_REDIS" == true ]]; then
  redis_file="$OUT_DIR/redis_${stamp}.rdb"
  info "Creating Redis snapshot: $redis_file"
  if "${COMPOSE[@]}" exec -T redis redis-cli --rdb /tmp/snap.rdb > /dev/null 2>&1 \
    && "${COMPOSE[@]}" cp redis:/tmp/snap.rdb "$redis_file" > /dev/null 2>&1; then
    ARTIFACTS+=("$redis_file")
    success "Redis snapshot created: $redis_file"
    maybe_encrypt_and_upload "$redis_file"
  else
    warn "Redis snapshot failed (service may be stopped); skipping."
    rm -f "$redis_file"
  fi
  prune "redis_*.rdb" "$KEEP"
  prune "redis_*.rdb.gpg" "$KEEP"
fi

# --- Grafana data volume (dashboards provisioned from repo; archive covers
# user edits, sessions and plugin state) ---
if [[ "$WITH_GRAFANA" == true ]]; then
  grafana_file="$OUT_DIR/grafana_${stamp}.tgz"
  info "Archiving Grafana volume: $grafana_file"
  if docker volume inspect infra-pilot_grafana_data > /dev/null 2>&1 \
    && docker run --rm \
    -v infra-pilot_grafana_data:/data:ro \
    -v "$OUT_DIR:/out" \
    alpine tar czf "/out/$(basename "$grafana_file")" -C /data . > /dev/null 2>&1; then
    ARTIFACTS+=("$grafana_file")
    success "Grafana archive created: $grafana_file"
    maybe_encrypt_and_upload "$grafana_file"
  else
    warn "Grafana volume not found (monitoring profile never started?); skipping."
    rm -f "$grafana_file"
  fi
  prune "grafana_*.tgz" "$KEEP"
  prune "grafana_*.tgz.gpg" "$KEEP"
fi

success "Done. Artifacts:"
for a in "${ARTIFACTS[@]}"; do
  info "  - $a"
done
