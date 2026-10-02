#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()    { echo -e "${YELLOW}${1}${NC}"; }
success() { echo -e "${GREEN}${1}${NC}"; }
error()   { echo -e "${RED}${1}${NC}" >&2; }

usage() {
  cat <<EOF
Restore the Infra Pilot Postgres database from a backup file.

Usage: $(basename "$0") <backup-file.dump[.gpg]> [--yes] [--dry-run] [--redis-file FILE] [--grafana-file FILE]

Options:
  --yes           Skip the confirmation prompt
  --dry-run       Validate header and TOC without touching the database
  --redis-file F  Additionally restore Redis RDB snapshot F into redis_data
  --grafana-file F  Additionally restore Grafana tgz archive F into grafana_data
  --help          Show this help message

Notes:
  - The backup file must be a pg_dump custom-format dump (created by db-backup.sh).
    GPG-encrypted artifacts (*.dump.gpg, requires gpg + your private key)
    are decrypted to a temp file automatically.
  - Stop the services that write to the database (orchestrator-agent, discord-service,
    management-panel) before restoring to avoid data loss.
  - The restore uses --clean --if-exists, so existing tables are dropped and recreated.
  - Redis/Grafana restores stop redis / grafana volumes briefly and copy the
    artifact back (see wiki/12-Backup-Restore.md). Omit both flags for Postgres only.
  - Verify restores with --dry-run (pg_restore --list) before production use.
EOF
  exit "${1:-0}"
}

ASSUME_YES=false
DRY_RUN=false
BACKUP_FILE=""
REDIS_FILE=""
GRAFANA_FILE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --yes) ASSUME_YES=true; shift ;;
    --dry-run) DRY_RUN=true; shift ;;
    --redis-file) REDIS_FILE="$2"; shift 2 ;;
    --grafana-file) GRAFANA_FILE="$2"; shift 2 ;;
    --help) usage ;;
    -*)
      echo "Unknown option: $1" >&2
      usage 2
      ;;
    *)
      if [[ -n "$BACKUP_FILE" ]]; then
        echo "Multiple backup files given" >&2
        usage 2
      fi
      BACKUP_FILE="$1"; shift ;;
  esac
done

if [[ -z "$BACKUP_FILE" ]]; then
  error "Missing backup file argument"
  usage 2
fi

if [[ ! -f "$BACKUP_FILE" ]]; then
  error "Backup file not found: $BACKUP_FILE"
  exit 1
fi

# GPG-encrypted artifacts are decrypted to a temp file (cleaned up on exit).
RESTORE_FILE="$BACKUP_FILE"
if [[ "$BACKUP_FILE" == *.gpg ]]; then
  if ! command -v gpg &> /dev/null; then
    error "gpg not found in PATH (required to decrypt $BACKUP_FILE)"
    exit 1
  fi
  RESTORE_FILE="$(mktemp --suffix=.dump)"
  trap 'rm -f "$RESTORE_FILE"' EXIT
  info "Decrypting $BACKUP_FILE ..."
  gpg --batch --yes --decrypt --output "$RESTORE_FILE" "$BACKUP_FILE"
fi

if [[ $(head -c 5 "$RESTORE_FILE") != "PGDMP" ]]; then
  error "Not a pg_dump custom-format backup: $BACKUP_FILE"
  exit 1
fi

if [[ "$DRY_RUN" == true ]]; then
  if command -v pg_restore &> /dev/null; then
    if ! pg_restore --list "$RESTORE_FILE" > /dev/null; then
      error "pg_restore --list failed for: $BACKUP_FILE"
      exit 1
    fi
  else
    info "pg_restore not found; header check only."
  fi
  success "Dry-run OK: $BACKUP_FILE looks like a valid pg_dump archive."
  exit 0
fi

if ! command -v docker &> /dev/null; then
  error "docker not found in PATH"
  exit 1
fi

POSTGRES_USER="${POSTGRES_USER:-infra_pilot}"
POSTGRES_DB="${POSTGRES_DB:-infra_pilot}"

info "About to restore $BACKUP_FILE into database '$POSTGRES_DB' (user '$POSTGRES_USER')."
info "Existing data will be replaced (--clean --if-exists)."
info "Consider stopping orchestrator-agent, discord-service and management-panel first."
if [[ "$ASSUME_YES" != true ]]; then
  read -r -p "Continue? [y/N] " answer
  if [[ "$answer" != "y" && "$answer" != "Y" ]]; then
    info "Restore cancelled."
    exit 0
  fi
fi

docker compose -f "$ROOT_DIR/docker-compose.yml" exec -T postgres \
  pg_restore --clean --if-exists --no-owner \
  -U "$POSTGRES_USER" -d "$POSTGRES_DB" - < "$RESTORE_FILE"

if [[ -n "$REDIS_FILE" ]]; then
  if [[ ! -f "$REDIS_FILE" ]]; then
    error "Redis snapshot not found: $REDIS_FILE"
    exit 1
  fi
  info "Restoring Redis snapshot $REDIS_FILE into redis_data ..."
  docker compose -f "$ROOT_DIR/docker-compose.yml" stop redis > /dev/null
  docker compose -f "$ROOT_DIR/docker-compose.yml" cp "$REDIS_FILE" redis:/data/dump.rdb
  docker compose -f "$ROOT_DIR/docker-compose.yml" start redis > /dev/null
  success "Redis restore completed from: $REDIS_FILE"
fi

if [[ -n "$GRAFANA_FILE" ]]; then
  if [[ ! -f "$GRAFANA_FILE" ]]; then
    error "Grafana archive not found: $GRAFANA_FILE"
    exit 1
  fi
  info "Restoring Grafana archive $GRAFANA_FILE into grafana_data ..."
  docker run --rm -v infra-pilot_grafana_data:/data \
    -v "$(cd "$(dirname "$GRAFANA_FILE")" && pwd):/in:ro" \
    alpine sh -c "rm -rf /data/* && tar xzf /in/$(basename "$GRAFANA_FILE") -C /data"
  success "Grafana restore completed from: $GRAFANA_FILE"
fi

success "Restore completed from: $BACKUP_FILE"