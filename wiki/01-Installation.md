# Installation

## Prerequisites

| Tool | Required for | Notes |
|---|---|---|
| Docker Engine with Compose v2 | Full local stack | `docker compose version` should succeed. |
| Python 3.10+ | CLI and orchestrator development | The CLI package declares Python 3.10 as its minimum. |
| Node.js and npm | Management-panel development | Not required when using the panel's Compose image. |

## Full local stack

```bash
git clone https://github.com/drosemann/infra-pilot.git
cd infra-pilot
cp .env.example .env
bash scripts/generate-env.sh
docker compose up -d
```

The default Compose project starts PostgreSQL, Redis, the management panel, and the orchestrator. The panel UI is at `http://localhost:5173`; its API is at `http://localhost:3001`; the orchestrator is at `http://localhost:8500`.

Preview the panel in `docs/screenshots/` before starting if you want to know what awaits you.

`POSTGRES_PASSWORD`, `GITOPS_WEBHOOK_TOKEN`, and `FEDERATION_API_TOKEN`
are required by Compose. The generator fills blank values; alternatively,
set secure values yourself before `docker compose up`.

```bash
docker compose ps
docker compose logs -f management-panel orchestrator-agent
```

## Optional profiles

```bash
# Prometheus, Grafana, and the PostgreSQL exporter
docker compose --profile monitoring up -d

# Discord/Pterodactyl integration (requires its credentials in .env)
docker compose --profile discord up -d

# k6 load-test runner; use the Make targets for the supported scenarios
make load-smoke
```

## CLI only

```bash
pip install ./cli
ipilot --version
ipilot --help
```

For editable development installation, use `pip install -e ./cli`. The CLI defaults to the panel API at `http://localhost:3001`; configure credentials with `ipilot login <api-key>`.

## Updating and stopping

```bash
git pull
docker compose up -d --build
docker compose down
```

`docker compose down` preserves named volumes. Use `docker compose down -v`
only when you intend to remove local PostgreSQL, Redis, Prometheus, and
Grafana data.
