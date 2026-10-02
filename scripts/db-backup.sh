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
  --keep N          Keep only the N most recent local backups per type (default: 10)
  --keep-daily N    Borg daily retention (default: 7)
  --keep-weekly N   Borg weekly retention (default: 4)
  --keep-monthly N  Borg monthly retention (default: 6)
  --out DIR         Backup output directory (default: \$ROOT_DIR/backups)
  --s3 URI          Additionally upload finished artifacts to S3
                    (e.g. s3://my-bucket/infra-pilot); requires the aws CLI
  --borg-repo REPO  Additionally archive finished artifacts with borgbackup
                    (e.g. /mnt/backup/borg or ssh://user@host/./infra-pilot);
                    requires borg. Repo must exist or be initialisable;
                    encryption via BORG_PASSPHRASE / BORG_REPO env.
  --rclone-remote REMOTE
                    Additionally copy finished artifacts with rclone
                    (e.g. myremote:infra-pilot or minio:backups/infra-pilot);
                    requires rclone with a configured remote.
  --encrypt-to KEY  Additionally encrypt artifacts with GPG for KEY
                    (key id, fingerprint or email); requires gpg.
                    Encrypted copies get a .gpg suffix; plaintext is kept
                    unless --no-plaintext is given
  --no-plaintext    With --encrypt-to: delete plaintext after encryption
  --skip-redis      Skip the Redis snapshot
  --skip-grafana    Skip the Grafana data archive
  --help            Show this help message

Self-hosted offsite (no S3 needed):
  /opt/infra-pilot/scripts/db-backup.sh --borg-repo /mnt/backup/borg
  /opt/infra-pilot/scripts/db-backup.sh --rclone-remote hetzner-box:infra-pilot
  /opt/infra-pilot/scripts/db-backup.sh --borg-repo /mnt/backup/borg \\
    --rclone-remote hetzner-box:infra-pilot --encrypt-to ops@example.com

  Env fallbacks: BACKUP_BORG_REPO / BORG_REPO, BACKUP_RCLONE_REMOTE.

Scheduling (example cron, daily 02:00, self-hosted via borg):
  0 2 * * *  /opt/infra-pilot/scripts/db-backup.sh --borg-repo /mnt/backup/borg >> /var/log/infra-pilot-backup.log 2>&1

Restore: see scripts/db-restore.sh (supports .gpg artifacts).
EOF
  exit "${1:-0}"
}

KEEP=10
KEEP_DAILY="${BACKUP_KEEP_DAILY:-7}"
KEEP_WEEKLY="${BACKUP_KEEP_WEEKLY:-4}"
KEEP_MONTHLY="${BACKUP_KEEP_MONTHLY:-6}"
OUT_DIR="$ROOT_DIR/backups"
S3_URI=""
BORG_REPO="${BACKUP_BORG_REPO:-${BORG_REPO:-}}"
RCLONE_REMOTE="${BACKUP_RCLONE_REMOTE:-${RCLONE_REMOTE:-}}"
ENCRYPT_TO=""
NO_PLAINTEXT=false
WITH_REDIS=true
WITH_GRAFANA=true

while [[ $# -gt 0 ]]; do
  case "$1" in
    --keep) KEEP="$2"; shift 2 ;;
    --keep-daily) KEEP_DAILY="$2"; shift 2 ;;
    --keep-weekly) KEEP_WEEKLY="$2"; shift 2 ;;
    --keep-monthly) KEEP_MONTHLY="$2"; shift 2 ;;
    --out) OUT_DIR="$2"; shift 2 ;;
    --s3) S3_URI="$2"; shift 2 ;;
    --borg-repo) BORG_REPO="$2"; shift 2 ;;
    --rclone-remote) RCLONE_REMOTE="$2"; shift 2 ;;
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

if [[ -n "$S3_URI" ]] && ! command -v aws &> /dev/null; then
  error "aws CLI not found in PATH (required for --s3)"
  exit 1
fi

if [[ -n "$BORG_REPO" ]] && ! command -v borg &> /dev/null; then
  error "borg not found in PATH (required for --borg-repo)"
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

if ! command -v docker &> /dev/null; then
  error "docker not found in PATH"
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
  if [[ -n "$RCLONE_REMOTE" ]]; then
    info "Copying $upload_file to $RCLONE_REMOTE with rclone ..."
    rclone copyto "$upload_file" "$RCLONE_REMOTE/$(basename "$upload_file")"
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

# --- Borg self-hosted deduplicated archive (optional) ---
if [[ -n "$BORG_REPO" ]]; then
  info "Archiving ${#ARTIFACTS[@]} artifact(s) to borg repo $BORG_REPO ..."
  if [[ -z "${BORG_PASSPHRASE:-}" ]]; then
    warn "BORG_PASSPHRASE is unset; borg init/create may prompt or fail for encrypted repos."
  fi
  if ! borg info "$BORG_REPO" > /dev/null 2>&1; then
    info "Borg repo not found, initialising $BORG_REPO ..."
    borg init --encryption=repokey-blake2 "$BORG_REPO"
  fi
  # shellcheck disable=SC2068
  borg create --stats --compression lz4 \
    "$BORG_REPO::infra-pilot-${stamp}" ${ARTIFACTS[@]}
  borg prune --list --keep-daily="$KEEP_DAILY" --keep-weekly="$KEEP_WEEKLY" \
    --keep-monthly="$KEEP_MONTHLY" "$BORG_REPO"
  success "Borg archive created: infra-pilot-${stamp}"
fi

success "Done. Artifacts:"
for a in "${ARTIFACTS[@]}"; do
  info "  - $a"
done
