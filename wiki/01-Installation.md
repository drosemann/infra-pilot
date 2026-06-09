# 01 – Installation

## Voraussetzungen

| Komponente | Version | Warum? |
|------------|---------|--------|
| Git | beliebig | Repository klonen |
| Docker & Docker Compose | Docker 24+ / Compose v2 | Full-Stack-Betrieb |
| Python | 3.9+ | CLI (`ipilot`) + Orchestrator |
| Node.js | 18+ | Management Panel + Discord Service |

Optional:
- **Go 1.21+** – Terraform Provider
- **Java 8+ / Maven** – Service Core (Minecraft-Plugin)
- **Zig 0.16.0+** – Native Desktop Shell

## Full-Stack (Docker Compose) – Empfohlen

```bash
git clone https://github.com/DaaanielTV/infra-pilot.git
cd infra-pilot
cp .env.example .env
# .env anpassen (mindestens DISCORD_TOKEN, DATABASE_URL)
docker compose up -d
```

Das startet: PostgreSQL 16, Redis 7, Orchestrator Agent, Integration Service, Management Panel, Discord Service.

Profile für optionale Services:
```bash
docker compose --profile monitoring up -d   # + Prometheus, Grafana
docker compose --profile minecraft up -d    # + Service Core
docker compose --profile cli up -d          # + ipilot CLI Container
```

## CLI (ipilot) – Standalone

```bash
cd cli
pip install -e .
ipilot --version
# → 1.0.0
```

Alternativ via Docker:
```bash
docker compose run --rm ipilot-cli ipilot health
```

## Management Panel – Manuell

```bash
cd services/management-panel
npm install
npm run dev
# Frontend: http://localhost:5173
# API: http://localhost:3001
```

## Discord Service

```bash
cd services/discord-service
npm install
npm start
```

Vorher `DISCORD_TOKEN` und Channel-IDs in der `.env` setzen.

## Nächste Schritte

Nach der Installation geht's weiter mit dem [ersten Deployment](02-First-Deployment).

---

*Stand: Mai 2026*
