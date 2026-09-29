#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKUP_SCRIPT="${IPILOT_BACKUP_SCRIPT:-$SCRIPT_DIR/db-backup.sh}"
HEALTH_SCRIPT="${IPILOT_HEALTH_SCRIPT:-$SCRIPT_DIR/healthcheck.sh}"

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()    { echo -e "${BLUE}${1}${NC}"; }
success() { echo -e "${GREEN}${1}${NC}"; }
warn()    { echo -e "${YELLOW}${1}${NC}"; }
error()   { echo -e "${RED}${1}${NC}" >&2; }

usage() {
  cat <<EOF
Safe update flow for Infra Pilot: backup first, then update, keep all data.

Usage: $(basename "$0") [OPTIONS]

Options:
  --check-only        Validate only (no backup, no git pull, no compose changes)
  --skip-backup       Skip the automatic pre-update backup (not recommended)
  --skip-git          Skip 'git pull --ff-only' (e.g. you already updated)
  --backup-args ARGS  Extra args passed to scripts/db-backup.sh (quoted string)
  --compose-args ARGS Extra args passed to 'docker compose up -d --build'
  --yes               Skip the confirmation prompt
  --help              Show this help message

What it does:
  1. Preflight: docker, git, 'docker compose config' validation.
  2. Pre-update backup via scripts/db-backup.sh (unless --skip-backup).
  3. 'git pull --ff-only' (unless --skip-git).
  4. 'docker compose up -d --build' (never with -v/--volumes).
  5. Health check via scripts/healthcheck.sh + volume verification.

Data retention:
  - Named volumes (postgres_data, redis_data, ...) are never deleted.
  - 'docker compose down -v' is refused; use plain 'docker compose down'
    (keeps volumes) and restore from backup if you must roll back.
  - The orchestrator runs 'alembic upgrade head' on startup, so the schema
    migrates forward automatically after the update.

Examples:
  $(basename "$0") --check-only
  $(basename "$0") --yes
  $(basename "$0") --backup-args "--out /mnt/backup --keep 10" --yes

Rollback:
  git log --oneline -5
  git checkout <previous-commit> && docker compose up -d --build
  # or restore a backup: bash scripts/db-restore.sh backups/<stamp>.dump --yes
EOF
  exit "${1:-0}"
}

CHECK_ONLY=false
SKIP_BACKUP=false
SKIP_GIT=false
BACKUP_ARGS=""
COMPOSE_ARGS=""
ASSUME_YES=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --check-only) CHECK_ONLY=true; shift ;;
    --skip-backup) SKIP_BACKUP=true; shift ;;
    --skip-git) SKIP_GIT=true; shift ;;
    --backup-args) BACKUP_ARGS="$2"; shift 2 ;;
    --compose-args) COMPOSE_ARGS="$2"; shift 2 ;;
    --yes) ASSUME_YES=true; shift ;;
    --volumes|-v|--remove-volumes)
      error "Refusing destructive flag '$1': updates never delete volumes."
      error "Use plain 'docker compose down' (keeps data) instead."
      exit 2
      ;;
    --help) usage ;;
    *) echo "Unknown option: $1" >&2; usage 2 ;;
  esac
done

case " $COMPOSE_ARGS " in
  *" --volumes "*|*" down -v "*|*" -v "*)
    error "Refusing --compose-args with volume deletion ('-v'/'--volumes')."
    exit 2
    ;;
esac

if ! command -v docker &> /dev/null; then
  error "docker not found in PATH"
  exit 1
fi

if ! command -v git &> /dev/null; then
  error "git not found in PATH"
  exit 1
fi

if [[ "$CHECK_ONLY" != true && "$SKIP_BACKUP" != true && ! -x "$BACKUP_SCRIPT" ]]; then
  error "Backup script not executable: $BACKUP_SCRIPT"
  exit 1
fi

info "Preflight: validating compose config ..."
docker compose -f "$ROOT_DIR/docker-compose.yml" config > /dev/null

if [[ "$CHECK_ONLY" == true ]]; then
  info "Check-only mode: no changes made."
  if [[ "$SKIP_GIT" != true ]]; then
    info "Checking git remote ..."
    git -C "$ROOT_DIR" fetch origin --dry-run
  fi
  success "Update check passed. Volumes will be kept; backup before updating."
  exit 0
fi

if [[ "$ASSUME_YES" != true ]]; then
  warn "This will backup, pull, rebuild and restart the stack. Data volumes are kept."
  read -r -p "Continue? [y/N] " answer
  if [[ "$answer" != "y" && "$answer" != "Y" ]]; then
    info "Update cancelled."
    exit 0
  fi
fi

if [[ "$SKIP_BACKUP" == true ]]; then
  warn "Skipping pre-update backup (--skip-backup). Not recommended."
else
  info "Step 1/4: pre-update backup ..."
  # shellcheck disable=SC2086
  bash "$BACKUP_SCRIPT" $BACKUP_ARGS
fi

if [[ "$SKIP_GIT" == true ]]; then
  info "Step 2/4: skipping git pull (--skip-git)."
else
  info "Step 2/4: pulling latest changes (fast-forward only) ..."
  git -C "$ROOT_DIR" pull --ff-only
fi

info "Step 3/4: rebuilding and restarting the stack (volumes kept) ..."
# shellcheck disable=SC2086
docker compose -f "$ROOT_DIR/docker-compose.yml" up -d --build $COMPOSE_ARGS

info "Step 4/4: verifying health and data volumes ..."
if ! bash "$HEALTH_SCRIPT" --strict; then
  error "Update failed: health check failed."
  exit 1
fi
PROJECT_NAME="$(docker compose -f "$ROOT_DIR/docker-compose.yml" config --environment | sed -n 's/^COMPOSE_PROJECT_NAME=//p')"
if [[ -z "$PROJECT_NAME" ]]; then
  error "Update failed: could not resolve the Compose project name."
  exit 1
fi
MISSING_VOLUMES=false
for vol in postgres_data redis_data; do
  if docker volume inspect "${PROJECT_NAME}_${vol}" > /dev/null 2>&1; then
    success "Volume present: ${PROJECT_NAME}_${vol}"
  else
    MISSING_VOLUMES=true
    warn "Volume missing: ${PROJECT_NAME}_${vol} (fresh install? restore a backup if data is expected)."
  fi
done

if [[ "$MISSING_VOLUMES" == false ]]; then
  success "Update complete. All checked named volumes are present."
else
  warn "Update complete, but one or more checked volumes are missing."
fi
info "If something is wrong, roll back with:"
info "  git log --oneline -5"
info "  bash scripts/db-restore.sh backups/<stamp>.dump --yes"
