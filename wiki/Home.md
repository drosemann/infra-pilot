# Infra Pilot

Infra Pilot is a learning project for operating Docker-backed infrastructure through a Python CLI, a React/Express management panel, an aiohttp orchestrator, and an optional Discord/Pterodactyl integration.

## Start here

```bash
git clone https://github.com/drosemann/infra-pilot.git
cd infra-pilot
cp .env.example .env
bash scripts/generate-env.sh
docker compose up -d
```

| Service | Default URL | Profile |
|---|---|---|
| Management panel | http://localhost:5173 | default |
| Panel API / Swagger | http://localhost:3001/api/docs | default |
| Orchestrator health | http://localhost:8500/health | default |
| Prometheus / Grafana | http://localhost:9090 / http://localhost:3000 | `monitoring` |
| Discord health | http://localhost:3002/health | `discord` |

## What it looks like

Conceptual UI previews with demo data
(see `docs/screenshots/` in the repository).
Illustrations of the intended UI, not captures of a running release:

- Dashboard: fleet overview, key metrics, launch actions.
- Monitoring: throughput, health checks, live logs.
- Applications: status, resources, uptime, ports.
- Backups: retention policy and recent runs.
- CLI and GitOps: `ipilot` plus signed webhook flow.

Start with Installation below, then open
`http://localhost:5173` after `docker compose up -d`.

## Documentation map

- [Installation](01-Installation) — prerequisites, required secrets, Compose profiles, and shutdown.
- [Configuration](03-Configuration) — environment variables, CLI configuration, and authentication boundaries.
- [First Deployment](02-First-Deployment) — a minimal CLI workflow.
- [Usage Examples](04-Usage-Examples) and [CLI Reference](05-CLI-Reference) — user-facing command guidance.
- [Architecture](06-Architecture) and [Auth Matrix](11-Auth-Matrix) — service boundaries and protected interfaces.
- [Backup & Restore](12-Backup-Restore),
  [Troubleshooting](10-Troubleshooting), and [Security](08-Security) —
  operational guidance.

The checked-in source of truth for public APIs is
`services/orchestrator-agent/api_docs/openapi.yaml` for the orchestrator and
the running panel's `/api/openapi.json` for the panel. Run `ipilot --help`
for the CLI installed in your environment.
