# Architecture

## Runtime topology

```
CLI (ipilot) ───────────────► Management panel API (:3001) ◄── React UI (:5173)
                                      │
                                      ├── PostgreSQL (:5432)
                                      └── Redis (:6379)

GitOps webhook / federation clients ─► Orchestrator agent (:8500)
                                            │
                                            ├── PostgreSQL
                                            └── Docker-backed compute provider

Discord (optional profile) ──────────► Discord service (:3002) ─► Pterodactyl / Docker socket
Monitoring (optional profile) ───────► Prometheus (:9090) ──────► Grafana (:3000)
```

The panel and orchestrator are separate services. The CLI's default URL is the panel API (`http://localhost:3001`); it does not directly target the orchestrator by default. The Discord and monitoring services are disabled unless their Compose profiles are requested.

## Service responsibilities

| Service | Implementation | Public interface | Notes |
|---|---|---|---|
| Management panel | `services/management-panel` | UI `:5173`, API `:3001` | React frontend with Express/WebSocket backend; exposes OpenAPI and Swagger UI. |
| Orchestrator agent | `services/orchestrator-agent` | HTTP `:8500` | aiohttp server for probes, signed GitOps callbacks, federation/RBAC APIs, and manifest reconciliation. |
| Discord service | `services/discord-service` | HTTP health `:3002` | Optional Node.js service for Discord/Pterodactyl workflows. |
| PostgreSQL / Redis | Compose services | `:5432` / `:6379` | Shared backing services started by the default profile. |
| Prometheus / Grafana | Compose `monitoring` profile | `:9090` / `:3000` | Optional metrics storage and dashboards. |

## Orchestrator boundaries

The agent's maintained modules are deliberately small and independently testable:

| Path | Responsibility |
|---|---|
| `compute/` | `ComputeProvider` abstraction, registry, and Docker provider implementation. |
| `manifest/` | YAML infra-file schema and reconciliation engine. |
| `rbac/`, `rbac_store.py` | Role/organization model, permission evaluation, and persistence helpers. |
| `webhook_server.py` | aiohttp routes, authentication middleware, GitOps signature verification, and HTTP responses. |
| `vps_manager.py`, `db.py`, `secrets_manager.py` | Docker lifecycle helpers, PostgreSQL access, and secret-management support. |

The OpenAPI contract in `services/orchestrator-agent/api_docs/openapi.yaml` is
verified by the agent test suite and is the route-level source of truth.

## Request and deployment flow

1. A user operates the panel or CLI; panel API authentication protects operational panel routes.
2. A GitOps caller sends a signed request to the orchestrator's `/webhook/gitops` endpoint.
3. The agent validates the signature/timestamp, parses the manifest, and asks a
   registered compute provider to reconcile desired state.
4. `/health` and `/metrics` remain probe-facing; `/api/` requires the configured federation bearer token.
5. Prometheus can scrape metrics, and Grafana reads its provisioned Prometheus
   data source when the monitoring profile is active.

## Authentication and security

| Surface | Mechanism |
|---|---|
| Panel operational API | Panel authentication middleware (`verifyAuth`). |
| Orchestrator `/api/` | `Authorization: Bearer <FEDERATION_API_TOKEN>`; fails closed if the token is not configured. |
| GitOps webhook | HMAC signature and replay-protection headers using `GITOPS_WEBHOOK_TOKEN`. |
| GitHub webhook | GitHub HMAC secret when that webhook route is enabled. |
| Health and metrics | Public by design for local probes/scraping; protect exposure at the network layer. |

Refer to [Auth Matrix](11-Auth-Matrix.md), the orchestrator OpenAPI file, and
[Security](08-Security.md) before exposing services outside a trusted network.
