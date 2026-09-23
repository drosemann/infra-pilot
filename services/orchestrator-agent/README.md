# Orchestrator Agent

Python/aiohttp service for Docker-backed compute-provider operations, YAML manifest reconciliation, RBAC primitives, and authenticated GitOps/federation HTTP routes. Discord integration is implemented separately in `../discord-service/`.

## Run locally

```bash
cd services/orchestrator-agent
python -m pip install -r requirements.txt
cp .env.example .env
# Set DB_PASSWORD and the webhook/API tokens before a production-like run.
python main.py
```

For the repository's supported local stack, prefer `docker compose up -d` from the repository root. It starts this service on `http://localhost:8500` and supplies its database connection through Compose.

## HTTP contract and authentication

`api_docs/openapi.yaml` is the maintained HTTP contract and is checked by `tests/unit/test_openapi_contract.py`.

| Route group | Auth | Purpose |
|---|---|---|
| `GET /health`, `GET /metrics` | Public | Readiness/health information and Prometheus metrics. |
| `/api/…` | `Authorization: Bearer <FEDERATION_API_TOKEN>` | Federation status, RBAC, provider discovery, and manifest deployment operations. |
| `/webhook/gitops` | `GITOPS_WEBHOOK_TOKEN` HMAC signature with timestamp/replay validation | Trigger a GitOps manifest reconciliation. |

Do not expose probe routes, bearer tokens, or webhook secrets directly to
untrusted networks. Use an ingress, firewall, or private network boundary.

## Configuration

The root `.env.example` is authoritative for the Compose deployment; this
directory's `.env.example` lists standalone defaults.

| Variable | Purpose |
|---|---|
| `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` | PostgreSQL connection settings. |
| `GITOPS_WEBHOOK_PORT` | Listener port; Compose sets it to `8500`. |
| `GITHUB_WEBHOOK_SECRET`, `GITOPS_WEBHOOK_TOKEN` | Signed webhook verification. |
| `FEDERATION_API_TOKEN` | Bearer token for `/api/` routes. |
| `AUTO_SCALE_*`, `SERVER_LIMIT`, `RAM_LIMIT` | Runtime capacity/default settings. |
| `LOG_LEVEL` | Python log level. |

## Code map

| Path | Responsibility |
|---|---|
| `compute/` | Provider interface, registry, and Docker implementation. |
| `manifest/` | Infra-file schema and reconciliation engine. |
| `rbac/`, `rbac_store.py` | Role/organization model and persistence helpers. |
| `webhook_server.py` | aiohttp routing, signatures, auth, and HTTP serialization. |
| `vps_manager.py` | Docker container lifecycle and resource operations. |
| `db.py`, `secrets_manager.py` | Database and secret-management support. |

## Tests

```bash
pytest tests/unit/ -v
pytest tests/smoke/ -v
```

See the repository [architecture guide](../../wiki/06-Architecture.md) and
[authentication matrix](../../wiki/11-Auth-Matrix.md) for the cross-service
view.
