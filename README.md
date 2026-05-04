# 🚀 Infra Pilot

**Infrastructure Orchestration Platform**

[![Build Status](https://img.shields.io/github/actions/workflow/status/DaaanielTV/infra-pilot/ci-core.yml?branch=main)](https://github.com/DaaanielTV/infra-pilot/actions)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python)](https://www.python.org/)
[![Node.js 18+](https://img.shields.io/badge/Node.js-18%2B-brightgreen?logo=node.js)](https://nodejs.org/)
[![Java 8+](https://img.shields.io/badge/Java-8%2B-orange?logo=java)](https://www.oracle.com/java/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0%2B-blue?logo=typescript)](https://www.typescriptlang.org/)

## 📌 Overview

**Infra Pilot** automates infrastructure at scale. Provision game servers, manage VPS lifecycles, and orchestrate multi-cloud resources through Discord, web interfaces, and APIs. Built for reliability and designed for developers.

> **Orchestrate. Automate. Scale.**

### Key Capabilities

- 🎮 **Game Server Management** - Automated provisioning, scaling, and lifecycle management
- ☁️ **VPS Orchestration** - Multi-cloud resource provisioning and billing
- 💬 **Discord Integration** - Native bot commands for infrastructure operations
- 🎛️ **Web Dashboard** - Real-time operations panel with modern UI
- 🔌 **API-First** - Comprehensive REST APIs for custom integrations
- 📊 **Observability** - Built-in monitoring, logging, and alerting
- 🔐 **Enterprise-Ready** - SSL/TLS, RBAC, audit logging

---

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Services](#services)
- [Installation](#installation)
- [Development](#development)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

---

## 🚀 Quick Start

### Docker Panel (NEW) 🆕

The Docker Panel is a new, modern self-hosted Docker management interface with **Personal Mode for self-hosters** and optional Business Mode features.

```bash
cd services/management-panel

# 1. Copy environment template
cp .env.local.example .env.local

# 2. Install dependencies
npm install

# 3. Start frontend + backend (both)
npm run dev
```

Then visit: **http://localhost:5173**
- API runs on: **http://localhost:3001**

**First time?** See [Docker Panel Quick Start](services/management-panel/README-DOCKER-PANEL.md)

---

### Prerequisites

- Docker & Docker Compose (recommended)
- Node.js 18+ (for Docker Panel)
- Git
- 4GB RAM minimum

### Option 1: Docker Compose (All Services)

```bash
# Clone the repository
git clone https://github.com/DaaanielTV/infra-pilot.git
cd infra-pilot

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

Services available:
- **Docker Panel**: http://localhost:5173 (Personal Mode by default)
- **Docker Panel API**: http://localhost:3001
- **Discord Service**: Ready for webhook integration
- **Service Core**: http://localhost:8080
- **Orchestrator API**: http://localhost:8000

### Option 2: Docker Panel Only (Quickest)

```bash
cd services/management-panel
npm install
npm run dev
```

Requires Supabase. See [Database Setup](services/management-panel/docs/DATABASE_SETUP.md)

### Option 3: Local Development (All Services)

```bash
# Clone and setup
git clone https://github.com/DaaanielTV/infra-pilot.git
cd infra-pilot

# Run setup script
./scripts/setup.sh

# Start services individually
cd services/service-core && mvn spring-boot:run &
cd services/orchestrator-agent && python main.py &
cd services/discord-service && npm start &
cd services/management-panel && npm run dev
```

### Option 3: Kubernetes

```bash
# Apply manifests
kubectl apply -f infrastructure/kubernetes/namespace.yaml
kubectl apply -f infrastructure/kubernetes/deployments/

# Port-forward to access
kubectl port-forward -n infra-pilot svc/management-panel 5173:80
```

See [docs/setup/local-development.md](docs/setup/local-development.md) for detailed setup.

---

## 🏗️ Architecture

### System Design

```
┌─────────────────────────────────────┐
│        User Interfaces              │
│  Discord | Web Dashboard | APIs     │
└────────────┬────────────────────────┘
             │
     ┌───────▼────────┐
     │  Orchestrator  │
     │    Agent       │
     │  (Python)      │
     └───────┬────────┘
             │
    ┌────────┴────────┐
    │                 │
┌───▼────┐      ┌────▼────┐
│Service  │      │External  │
│Core     │      │APIs      │
│(Java)   │      │(Cloud)   │
└────┬────┘      └──────────┘
     │
  ┌──▼──────────────┐
  │Infrastructure   │
  │DB, Cache, Etc.  │
  └─────────────────┘
```

### Services Overview

| Service | Purpose | Language | Port |
|---------|---------|----------|------|
| **Management Panel** | Docker Container Management (NEW) | TypeScript/React + Express | 5173/3001 |
| **Orchestrator Agent** | Core logic & provisioning | Python | 8000 |
| **Discord Service** | Discord bot interface | Node.js | - |
| **Service Core** | Server management | Java | 8080 |

See [docs/architecture/overview.md](docs/architecture/overview.md) for detailed architecture documentation.

---

## 📦 Services

### 1. Management Panel (`services/management-panel/`) - Docker Panel
Web-based Docker container management interface for self-hosted deployments.

- **Tech Stack:** React 19, TypeScript, Tailwind CSS, Express.js, Supabase/PostgreSQL
- **Modes:** 
  - **Personal Mode** (default): Simple Docker management for individual users
  - **Business Mode** (optional): Multi-user, billing, white-label, team management
- **Features:** Docker app creation/management, container status monitoring, log viewing, resource allocation
- **Setup:** `cd services/management-panel && npm install && npm run dev`
- **Docs:** [services/management-panel/README.md](services/management-panel/README.md) | [services/management-panel/TRANSFORMATION.md](services/management-panel/TRANSFORMATION.md)
- **Database:** See [services/management-panel/docs/DATABASE_SETUP.md](services/management-panel/docs/DATABASE_SETUP.md)

### 2. Orchestrator Agent (`services/orchestrator-agent/`)
Core provisioning and orchestration engine.

- **Tech Stack:** Python 3.9+, Discord.py, aiohttp
- **Features:** VPS provisioning, resource allocation, billing, webhooks
- **Setup:** `cd services/orchestrator-agent && pip install -r requirements.txt && python main.py`
- **Docs:** [services/orchestrator-agent/README.md](services/orchestrator-agent/README.md)

### 3. Discord Service (`services/discord-service/`)
Discord bot for command-line operations.

- **Tech Stack:** Node.js, Discord.js
- **Features:** Server commands, status checks, provisioning flows
- **Setup:** `cd services/discord-service && npm install && npm start`
- **Docs:** [services/discord-service/README.md](services/discord-service/README.md)

### 4. Service Core (`services/service-core/`)
Game server management and resource lifecycle.

- **Tech Stack:** Java 8+, Maven
- **Features:** Server startup/shutdown, resource tracking, event logging
- **Setup:** `cd services/service-core && mvn clean install && mvn spring-boot:run`
- **Docs:** [services/service-core/README.md](services/service-core/README.md)

---

## 🛠️ Installation

### System Requirements

| Component | Requirement |
|-----------|-------------|
| OS | Linux, macOS, Windows (WSL2) |
| Memory | 4GB minimum (8GB recommended) |
| Disk | 10GB free space |
| Docker | 20.10+ (optional) |

### Full Setup Guide

1. **Prerequisites**
   ```bash
   # Verify Docker
   docker --version
   # Verify Git
   git --version
   ```

2. **Clone Repository**
   ```bash
   git clone https://github.com/DaaanielTV/infra-pilot.git
   cd infra-pilot
   ```

3. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   nano .env
   ```

4. **Start Services**
   ```bash
   # Docker (recommended)
   docker-compose up -d
   
   # OR local development
   ./scripts/setup.sh
   ```

5. **Verify Installation**
   ```bash
   curl http://localhost:5173       # Dashboard
   curl http://localhost:8000/health # Orchestrator API
   ```

See [docs/setup/local-development.md](docs/setup/local-development.md) for detailed instructions.

---

## 👨‍💻 Development

### Getting Started

```bash
# Clone & setup
git clone https://github.com/DaaanielTV/infra-pilot.git
cd infra-pilot

# One-command setup
./scripts/setup.sh

# Run tests
./scripts/test.sh

# Build Docker images
./scripts/docker-build.sh
```

### Development Workflow

1. **Create a branch** from `main`
   ```bash
   git checkout -b feature/your-feature
   ```

2. **Make changes** and test locally
   ```bash
   # For Python changes
   cd services/orchestrator-agent
   pytest tests/

   # For JavaScript changes
   cd services/management-panel
   npm run test

   # For Java changes
   cd services/service-core
   mvn test
   ```

3. **Commit with clear messages**
   ```bash
   git commit -m "feat: add new provisioning command"
   ```

4. **Push and create a pull request**
   ```bash
   git push origin feature/your-feature
   ```

See [CONTRIBUTING.md](CONTRIBUTING.md) for full contribution guidelines.

### Testing

```bash
# Run all tests (local)
./scripts/test.sh

# Run service-specific tests
cd services/orchestrator-agent && pytest tests/
cd services/management-panel && npm run test
cd services/discord-service && npm run test
cd services/service-core && mvn test
```

### CI & Test Scaffolding
- This repository uses GitHub Actions (see .github/workflows/ci-core.yml) to run the core CI suite on push/PRs. The CI runs unit tests, integration tests, linting, and build checks as configured in ci-core.yml.
- Release scaffolding is provided via scripts/release.sh. It can tag releases and optionally update CHANGELOG.md before pushing the tag.
- Integration test scaffolding exists at tests/integration/README.md (skeleton provided for future end-to-end tests).
- Locally, you can mirror CI steps by running per-service tests (pytest for Python services, npm test for Node services, mvn test for Java services) as shown above.

### Code Quality

```bash
# Linting
cd services/management-panel && npm run lint
cd services/orchestrator-agent && pylint cogs/

# Type checking
cd services/management-panel && npm run type-check
```

---

## 📚 Documentation

Complete documentation is available in the [docs/](docs/) directory:

### Architecture & Design
- [System Architecture](docs/architecture/overview.md)
- [Service Specifications](docs/architecture/)
- [Data Flow & Integration](docs/architecture/data-flow.md)

### Setup & Deployment
- [Local Development Setup](docs/setup/local-development.md)
- [Docker Deployment](docs/setup/docker-setup.md)
- [Kubernetes Deployment](docs/setup/kubernetes-deploy.md)
- [Environment Configuration](docs/setup/environment-config.md)

### Operations
- [Deployment Guide](docs/operations/deployment-guide.md)
- [Scaling Strategy](docs/operations/scaling-strategy.md)
- [Monitoring & Observability](docs/operations/monitoring-observability.md)
- [Troubleshooting](docs/operations/troubleshooting.md)
- [Security Hardening](docs/operations/security-hardening.md)

### Development
- [Development Workflow](docs/development/development-workflow.md)
- [Testing Strategy](docs/development/testing-strategy.md)
- [Code Standards](docs/development/code-standards.md)
- [Debugging Tips](docs/development/debugging-tips.md)

### API Reference
- [Service Core API](docs/api/service-core-api.md)
- [Orchestrator Agent API](docs/api/orchestrator-api.md)
- [Discord Webhooks](docs/api/discord-webhooks.md)

---

## 🔍 Key Workflows

### Provision a New Game Server

**Via Web Dashboard:**
1. Login to http://localhost:5173
2. Click "Create Server"
3. Select configuration
4. Click "Deploy"

**Via Discord:**
```
/provision type=gameserver name=my-server size=medium
```

**Via API:**
```bash
curl -X POST http://localhost:8000/api/servers \
  -H "Authorization: Bearer TOKEN" \
  -d '{"name": "my-server", "type": "gameserver"}'
```

### Monitor Infrastructure

```bash
# View all servers
curl http://localhost:8000/api/servers

# View metrics
curl http://localhost:8000/api/metrics

# View logs
docker-compose logs orchestrator-agent
```

### Scale Resources

See [docs/operations/scaling-strategy.md](docs/operations/scaling-strategy.md)

---

## 🐳 Docker

### Build Images

```bash
# Build all services
docker-compose build

# Build specific service
docker-compose build management-panel
```

### Run with Docker Compose

```bash
# Development stack
docker-compose up -d

# Production stack
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose logs -f
```

### Push to Registry

```bash
# Configure registry
export REGISTRY=your-registry.com

# Build and push
docker-compose build
docker-compose push
```

---

## 🚢 Deployment

### Quick Deployment Options

#### Option 1: Docker Compose (Development)
```bash
docker-compose up -d
```

#### Option 2: Kubernetes
```bash
kubectl apply -f infrastructure/kubernetes/
```

#### Option 3: Cloud Provider
Cloud-provider deployment guidance is consolidated in the central deployment documentation:
- [Deployment Guide](docs/operations/deployment-guide.md)
- [Environment Configuration](docs/setup/environment-config.md)

Full deployment guide: [docs/operations/deployment-guide.md](docs/operations/deployment-guide.md)

---

## 📊 Monitoring

Access monitoring stack:

- **Prometheus:** http://localhost:9090
- **Grafana:** http://localhost:3000
- **Logs:** Via `docker-compose logs` or centralized logging

See [docs/operations/monitoring-observability.md](docs/operations/monitoring-observability.md)

---

## 🔐 Security

- SSL/TLS configuration: [docs/setup/ssl-tls-setup.md](docs/setup/ssl-tls-setup.md)
- Security hardening: [docs/operations/security-hardening.md](docs/operations/security-hardening.md)
- Vulnerability reporting: [SECURITY.md](SECURITY.md)

---

## 🤝 Contributing

We welcome contributions! Please read [CONTRIBUTING.md](CONTRIBUTING.md) and our code standards [docs/development/code-standards.md](docs/development/code-standards.md).

### Quick Contribution Steps

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit changes: `git commit -am 'Add my feature'`
4. Push: `git push origin feature/my-feature`
5. Submit a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

## 📝 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

---

## 🆘 Support

- **Documentation:** [docs/](docs/)
- **Issues:** [GitHub Issues](https://github.com/DaaanielTV/infra-pilot/issues)
- **Discussions:** [GitHub Discussions](https://github.com/DaaanielTV/infra-pilot/discussions)
- **Security:** [SECURITY.md](SECURITY.md)

---

**[⬆ back to top](#-infra-pilot)**

## Troubleshooting

- **Bot fails to start**: verify required env vars are set and valid.
- **Discord commands not visible**: ensure bot has correct scopes/permissions and command registration completed.
- **Panel cannot load backend data**: verify Convex deployment credentials/config.
- **Maven build errors**: confirm Java 17 is active (`java -version`).

## Open Source Policies

- License: GNU GPLv3 (`LICENSE`)
- Contributing guide: `CONTRIBUTING.md`
- Code of conduct: `CODE_OF_CONDUCT.md`
