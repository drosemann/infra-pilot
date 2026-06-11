# infra-pilot

[![CI](https://github.com/d5niel-lgtm/infra-pilot/actions/workflows/ci.yml/badge.svg)](https://github.com/d5niel-lgtm/infra-pilot/actions/workflows/ci.yml)

Container management and server provisioning platform with a React dashboard, Python orchestrator, and Discord bot integration for self-hosted infrastructure.

## Quick start

```bash
git clone https://github.com/DaaanielTV/infra-pilot.git
cd infra-pilot
cp .env.example .env
docker compose up -d
```

Access the management panel at `http://localhost:5173`.

## Services

| Service | Stack | Purpose |
|---------|-------|---------|
| **management-panel** | React 19, Express, PostgreSQL | Web dashboard for container and server management |
| **orchestrator-agent** | Python (discord.py) | Server provisioning, health monitoring, automation |
| **discord-service** | Node.js (discord.js) | Discord bot for server creation and management |
| **integration-service** | Python (aiohttp) | Cross-service communication hub |
| **service-core** | Java (Paper/Bukkit) | Minecraft server plugin |

## Default ports

| Port | Service |
|------|---------|
| 5173 | Management Panel (Frontend) |
| 3001 | Management Panel (Backend) |
| 8500 | Orchestrator Agent |
| 9000 | Integration Service |
| 3002 | Discord Service |
| 5432 | PostgreSQL |
| 6379 | Redis |
| 9090 | Prometheus |
| 3000 | Grafana |

## Repository structure

```
.
├── services/
│   ├── management-panel/     # React + Express dashboard
│   ├── orchestrator-agent/   # Python provisioning agent
│   ├── discord-service/      # Discord bot
│   ├── integration-service/  # Cross-platform hub
│   └── service-core/         # Minecraft plugin (Java)
├── cli/                      # Python CLI tool (ipilot)
├── mobile/                   # React Native (Expo) mobile app
├── infra/                    # Provider-neutral naming, Terraform
├── infrastructure/           # Monitoring configs (Prometheus, Grafana)
├── tests/                    # Unit, integration, and smoke tests
├── docs/                     # Architecture and development docs
├── wiki/                     # User-facing documentation
└── scripts/                  # Build, test, and setup helpers
```

## Requirements

- Docker and Docker Compose (for stack deployment)
- Node.js 18+ (management panel, discord service)
- Python 3.9+ (orchestrator agent, integration service)
- Java/Maven (service core)

## License

MIT
