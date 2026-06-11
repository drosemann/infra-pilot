#!/bin/bash
#
# Infra Pilot - Development Environment Setup Script
#
# This script sets up all services for local development.
# Supports multiple languages: Java, Python, Node.js, TypeScript

set -euo pipefail

echo "🚀 Infra Pilot Development Setup"
echo "=================================="

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

OFFLINE=false
for arg in "$@"; do
  case "$arg" in
    --offline)
      OFFLINE=true
      ;;
    *)
      echo "Unknown option: $arg"
      echo "Usage: $0 [--offline]"
      exit 1
      ;;
  esac
done

# Configuration
SERVICES=(
    "services/service-core"
    "services/orchestrator-agent"
    "services/discord-service"
    "services/management-panel"
)

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}✗ $1${NC}"
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "$1 is not installed"
        return 1
    fi
    return 0
}

# Check prerequisites
echo ""
log_info "Checking prerequisites..."
if [ "$OFFLINE" = true ]; then
    log_info "Offline mode enabled: package installation steps are skipped"
fi

MISSING_DEPS=0

if ! check_command git; then MISSING_DEPS=1; fi
if ! check_command docker; then log_warning "Docker not found - using local setup"; fi

if ! check_command java; then log_warning "Java not found - skipping service-core setup"; fi
if ! check_command mvn; then log_warning "Maven not found - skipping service-core setup"; fi
if ! check_command python3; then log_warning "Python 3 not found - skipping orchestrator-agent setup"; fi
if ! check_command node; then log_warning "Node.js not found - skipping Node.js services setup"; fi
if ! check_command npm; then log_warning "npm not found - skipping Node.js services setup"; fi

if [ "$MISSING_DEPS" -eq 1 ]; then
    log_error "Missing critical dependencies"
    exit 1
fi

log_success "Prerequisites check passed"

# Validate key infrastructure files
echo ""
log_info "Validating infrastructure files..."

INFRA_FILES=(
    "docker-compose.yml"
    ".env.example"
    "infrastructure/prometheus/prometheus.yml"
    "infrastructure/grafana/provisioning/datasources/prometheus.yml"
)

for file in "${INFRA_FILES[@]}"; do
    if [ -f "$file" ]; then
        log_success "Found $file"
    else
        log_warning "Missing $file - some features may not work"
    fi
done

# Setup each service
echo ""
log_info "Setting up services..."

for service in "${SERVICES[@]}"; do
    if [ ! -d "$service" ]; then
        log_warning "Service directory not found: $service"
        continue
    fi

    SERVICE_NAME=$(basename "$service")
    echo ""
    log_info "Setting up $SERVICE_NAME..."

    # Determine setup based on service
    if [ "$SERVICE_NAME" == "service-core" ]; then
        # Java/Maven setup
        if command -v mvn &> /dev/null && command -v java &> /dev/null; then
            pushd "$service" > /dev/null
            if [ "$OFFLINE" = false ]; then
                log_info "Installing Maven dependencies..."
                mvn clean install -q -DskipTests || log_warning "Maven setup failed for $SERVICE_NAME"
            else
                log_warning "Offline mode: skipping Maven dependency install"
            fi
            log_success "$SERVICE_NAME setup complete"
            popd > /dev/null
        else
            log_warning "Skipping $SERVICE_NAME (Java/Maven not available)"
        fi

    elif [ "$SERVICE_NAME" == "orchestrator-agent" ]; then
        # Python setup
        if command -v python3 &> /dev/null; then
            pushd "$service" > /dev/null
            log_info "Creating Python virtual environment..."
            python3 -m venv venv || log_warning "Could not create venv"

            if [ "$OFFLINE" = false ] && [ -f "venv/bin/activate" ]; then
                # shellcheck disable=SC1091
                source venv/bin/activate
                log_info "Installing Python dependencies..."
                pip install -r requirements.txt || log_warning "pip install failed"
                deactivate
            elif [ "$OFFLINE" = true ]; then
                log_warning "Offline mode: skipping Python dependency install"
            fi

            log_success "$SERVICE_NAME setup complete"
            popd > /dev/null
        else
            log_warning "Skipping $SERVICE_NAME (Python not available)"
        fi

    elif [ "$SERVICE_NAME" == "discord-service" ] || [ "$SERVICE_NAME" == "management-panel" ]; then
        # Node.js/npm setup
        if command -v npm &> /dev/null; then
            pushd "$service" > /dev/null
            if [ ! -f "package.json" ]; then
                log_warning "No package.json found for $SERVICE_NAME, skipping npm setup"
                popd > /dev/null
                continue
            fi
            if [ "$OFFLINE" = false ]; then
                log_info "Installing npm dependencies..."
                if [ -f "package-lock.json" ]; then
                    npm ci || log_warning "npm ci failed"
                else
                    npm install || log_warning "npm install failed"
                fi
            else
                log_warning "Offline mode: skipping npm install"
            fi
            log_success "$SERVICE_NAME setup complete"
            popd > /dev/null
        else
            log_warning "Skipping $SERVICE_NAME (Node.js/npm not available)"
        fi
    fi
done

# Environment file setup
echo ""
log_info "Setting up environment files..."

if [ -f ".env.example" ] && [ ! -f ".env" ]; then
    log_info "Creating .env from .env.example"
    cp .env.example .env
    log_warning "Please configure .env with your settings"
elif [ -f ".env" ]; then
    log_success ".env already exists"
else
    log_warning "No .env.example found - you may need to create .env manually"
fi

# Summary
echo ""
echo "=================================="
log_success "Setup complete!"
echo ""
log_info "Next steps:"
echo "  1. Configure .env if needed"
echo "  2. Run tests: ./scripts/test.sh"
echo "  3. Start services: docker-compose up -d"
echo "  4. Or run individually from services/ directories"
echo ""
log_info "For more info, see: README.md"
echo ""
