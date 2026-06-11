#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
JSON_OUTPUT=false
STRICT=false

while [ $# -gt 0 ]; do
  case "$1" in
    --json)
      JSON_OUTPUT=true
      shift
      ;;
    --strict)
      STRICT=true
      shift
      ;;
    *)
      echo "Unknown option: $1" >&2
      echo "Usage: $0 [--json] [--strict]" >&2
      exit 1
      ;;
  esac
done

check_file() {
  local file="$1"
  local label="$2"
  if [ -f "$file" ]; then
    echo "✓ $label"
    return 0
  fi
  echo "✗ $label (missing: $file)"
  return 1
}

check_docker_service() {
  local service="$1"
  local label="$2"
  if command -v docker &> /dev/null; then
    local status
    status=$(docker ps --filter "name=${service}" --format "{{.Status}}" 2>/dev/null || true)
    if [ -n "$status" ]; then
      echo "✓ $label ($status)"
      return 0
    fi
  fi
  echo "⚠ $label (not running)"
  return 1
}

OK=0
WARN=0

echo "Running health checks..."
echo ""

echo "--- File Checks ---"
check_file "$ROOT_DIR/.env.example" ".env example present" && OK=$((OK + 1)) || WARN=$((WARN + 1))
check_file "$ROOT_DIR/docker-compose.yml" "docker compose config present" && OK=$((OK + 1)) || WARN=$((WARN + 1))
check_file "$ROOT_DIR/services/service-core/pom.xml" "service-core Maven manifest present" && OK=$((OK + 1)) || WARN=$((WARN + 1))
check_file "$ROOT_DIR/services/orchestrator-agent/requirements.txt" "orchestrator-agent Python manifest present" && OK=$((OK + 1)) || WARN=$((WARN + 1))
check_file "$ROOT_DIR/services/management-panel/package.json" "management-panel Node manifest present" && OK=$((OK + 1)) || WARN=$((WARN + 1))
check_file "$ROOT_DIR/services/discord-service/package.json" "discord-service package manifest present" && OK=$((OK + 1)) || WARN=$((WARN + 1))
check_file "$ROOT_DIR/services/orchestrator-agent/.env.example" "orchestrator-agent .env.example present" && OK=$((OK + 1)) || WARN=$((WARN + 1))
check_file "$ROOT_DIR/services/management-panel/.env.example" "management-panel .env.example present" && OK=$((OK + 1)) || WARN=$((WARN + 1))
check_file "$ROOT_DIR/services/integration-service/.env.example" "integration-service .env.example present" && OK=$((OK + 1)) || WARN=$((WARN + 1))

echo ""
echo "--- Docker Service Checks ---"
check_docker_service "infra-pilot-postgres" "PostgreSQL" && OK=$((OK + 1)) || WARN=$((WARN + 1))
check_docker_service "infra-pilot-redis" "Redis" && OK=$((OK + 1)) || WARN=$((WARN + 1))
check_docker_service "infra-pilot-management-panel" "Management Panel" && OK=$((OK + 1)) || WARN=$((WARN + 1))
check_docker_service "infra-pilot-orchestrator" "Orchestrator Agent" && OK=$((OK + 1)) || WARN=$((WARN + 1))
check_docker_service "infra-pilot-integration" "Integration Service" && OK=$((OK + 1)) || WARN=$((WARN + 1))
check_docker_service "infra-pilot-discord" "Discord Service" && OK=$((OK + 1)) || WARN=$((WARN + 1))

if [ "$JSON_OUTPUT" = true ]; then
  printf '{"script":"healthcheck","ok":%s,"warn":%s}\n' "$OK" "$WARN"
fi

echo ""
echo "Health summary: ok=$OK warn=$WARN"
if [ "$STRICT" = true ] && [ "$WARN" -gt 0 ]; then
  exit 1
fi
exit 0
