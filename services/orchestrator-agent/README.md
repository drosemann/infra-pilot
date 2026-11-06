# Orchestrator Agent

Python/aiohttp service for Docker-backed compute-provider operations, YAML manifest reconciliation, RBAC
primitives, and authenticated GitOps/federation HTTP routes. Discord integration is implemented separately in
`../discord-service/`.

## Run locally

```bash
cd services/orchestrator-agent
python -m pip install -r requirements.txt
cp .env.example .env
# Set DB_PASSWORD and the webhook/API tokens before a production-like run.
python main.py
```

For the repository's supported local stack, prefer `docker compose up -d` from the repository root. It starts
this service on `http://localhost:8500` and supplies its database connection through Compose.

## HTTP contract and authentication

`api_docs/openapi.yaml` is the maintained HTTP contract and is checked by `tests/unit/test_openapi_contract.py`.

| Route group | Auth | Purpose |
| --- | --- | --- |
| `GET /health`, `GET /metrics` | Public | Readiness/health information and Prometheus metrics. |
| `/api/…` | `Authorization: Bearer <FEDERATION_API_TOKEN>` | Federation status, RBAC, provider discovery, and manifest deployment operations. |
| `/webhook/gitops` | `GITOPS_WEBHOOK_TOKEN` HMAC signature with timestamp/replay validation | Trigger a GitOps manifest reconciliation. |
| `POST/GET /api/v1/incidents*` | `Authorization: Bearer <FEDERATION_API_TOKEN>` | Incident workflow: duty routing, escalation chain, postmortem drafts ([docs/INCIDENTS.md](../../docs/INCIDENTS.md)). |
| `GET /api/v1/fleet/creatures[/{id}]`, `POST …/rename` | `Authorization: Bearer <FEDERATION_API_TOKEN>` | Living Fleet creature views (SQLite store) and rename-only mutation. Disabled (404) unless `LIVING_FLEET_ENABLED=true`. |

Do not expose probe routes, bearer tokens, or webhook secrets directly to
untrusted networks. Use an ingress, firewall, or private network boundary.

## Configuration

The root `.env.example` is authoritative for the Compose deployment; this
directory's `.env.example` lists standalone defaults.

| Variable | Purpose |
| --- | --- |
| `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` | PostgreSQL connection settings. |
| `GITOPS_WEBHOOK_PORT` | Listener port; Compose sets it to `8500`. |
| `GITHUB_WEBHOOK_SECRET`, `GITOPS_WEBHOOK_TOKEN` | Signed webhook verification. |
| `FEDERATION_API_TOKEN` | Bearer token for `/api/` routes. |
| `LIVING_FLEET_ENABLED`, `LIVING_FLEET_INTERVAL_S`, `LIVING_FLEET_DB` | Living Fleet collector toggle, collection interval in seconds, and SQLite path (one-way import from the legacy JSON store). |
| `INCIDENTS_STORE`, `INCIDENTS_ESCALATION`, `INCIDENTS_ESCALATE_AFTER_S`, `INCIDENTS_QUIET_HOURS` | Incident JSON store, rota levels (`alice|bob;carol`), escalation deadline, quiet hours. |
| `AUTO_SCALE_*`, `SERVER_LIMIT`, `RAM_LIMIT` | Runtime capacity/default settings. |
| `LOG_LEVEL` | Python log level. |

## Code map

| Path | Responsibility |
| --- | --- |
| `compute/` | Provider interface, registry, and Docker implementation. |
| `manifest/` | Infra-file schema and reconciliation engine. |
| `rbac/`, `rbac_store.py` | Role/organization model and persistence helpers. |
| `webhook_server.py` | aiohttp routing, signatures, auth, and HTTP serialization. |
| `incidents.py` | Incident & on-call logic: duty routing, escalation chain, postmortem drafts, JSON store. |
| `vps_manager.py` | Compatibility entry point for VPS manager imports. |
| `vps_docker_support.py` | VPS configuration, validation, and shared Docker helpers. |
| `vps_instance_persistence.py` | VPS inventory and database persistence. |
| `vps_container_lifecycle.py` | Container creation, lifecycle, and resource management. |
| `vps_backup_snapshots.py` | Backup and snapshot creation, rotation, and restoration. |
| `vps_health_monitoring.py` | Container cloning/migration, health checks, metrics, and usage history. |
| `db.py`, `secrets_manager.py` | Database and secret-management support. |

## Tests

```bash
pytest tests/unit/ -v
pytest tests/smoke/ -v
```

See the repository [architecture guide](../../wiki/06-Architecture.md) and
[authentication matrix](../../wiki/11-Auth-Matrix.md) for the cross-service
view.
