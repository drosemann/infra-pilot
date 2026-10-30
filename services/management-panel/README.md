# Management Panel

React/TypeScript frontend and Express/WebSocket backend for operating Docker
applications, backups, configuration, monitoring, and the panel-facing Infra
Pilot API.

## Screenshots

Conceptual UI previews with demo data (see `docs/screenshots/`).
Illustrations of the intended UI, not captures of a running release:

See the root README's [Screenshots section](../../README.md#screenshots) for
the Dashboard and Monitoring previews.

Full set: dashboard, monitoring, applications, backups, CLI/GitOps, and
deployments, plus an animated `tour.gif`. Regeneration instructions live in
`docs/screenshots/README.md`.

## Start locally

```bash
cd services/management-panel
cp .env.example .env.local
npm install
npm run dev
```

`npm run dev` starts Vite on `http://localhost:5173` and the backend on `http://localhost:3001`. The first
visit uses the setup flow. For the complete dependency stack, start the repository root with `docker compose
up -d` instead.

## Git blame

Blame-aware GitOps page at `/git-blame` (sidebar: Git Blame). Shows who last
touched each server resource in a repo-relative YAML config, plus ownership
risk flags (`uncommitted`, `stale`, `many-hands`, `unknown`):

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/gitops/blame?path=<file>&staleDays=<n>` | Blame annotations per server resource. |

`path` must be a repo-relative `.yaml`/`.yml` file inside `GITOPS_REPO_DIR`
(defaults to the panel working directory); traversal and absolute paths are
rejected. `staleDays` (default 180) sets the freshness threshold. The CLI
counterpart is `ipilot gitops blame` / `gitops plan --blame`.

## API and authentication

| Surface | URL | Notes |
| --- | --- | --- |
| Health | `GET /health`, `GET /api/health` | Used by Compose health checks. |
| OpenAPI | `GET /api/openapi.json` | Current panel API contract. |
| Swagger UI | `GET /api/docs` | Interactive API documentation. |
| WebSocket | `ws://host:3001?appId=<id>` | Live application logs and metrics. |

Setup, health, and documentation endpoints are intentionally reachable without
an application session. Operational `/api/*` routes are protected by the
backend's `verifyAuth` middleware unless explicitly documented otherwise.
Treat the OpenAPI document and `server/index.ts` as the authoritative
route list.

## Configuration

Copy `.env.example` to `.env.local` for standalone development. The root `.env.example` controls Compose deployments.

| Variable | Purpose |
| --- | --- |
| `PORT` | Backend listener (default `3001`). |
| `VITE_API_URL`, `VITE_ENVIRONMENT` | Frontend API target and environment label. |
| `VITE_PUBLIC_WEBHOOK_URL` | Full public HTTPS webhook URL shown and copied in Git Deployments. |
| `DATABASE_URL`, `REDIS_URL` | Backend service connections. |
| `CORS_ORIGINS` | Comma-separated permitted browser origins. |
| `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY` | Optional hosted-feature configuration. |
| `ORCHESTRATOR_URL`, `ORCHESTRATOR_API_TOKEN` | Orchestrator forwarding and the Living Fleet proxy (`/api/fleet/creatures`); unset disables both. Dashboard cards show a creature pet with a collapsed why-detail when available. |

## Code map

| Path | Responsibility |
| --- | --- |
| `src/` | React UI, routes, components, hooks, and browser API clients. |
| `server/index.ts` | Express routes, authentication, WebSocket integration, and service startup. |
| `server/openapi.ts` | Panel OpenAPI specification. |
| `server/*.ts` | Focused backend helpers such as reports, GraphQL, assistant, doctor, and audit sanitisation. |
| `docs/` | Longer-lived design and setup notes. |

## Deployments

Stable panel page at `/deployments` (no beta badge). Connects Git
repositories to containers for GitOps auto-deploy:

- Create a deployment with name, repository URL (`https://`, `http://`,
  or `git@`), branch, target container, target directory, and optional
  install/restart commands. Invalid URLs are rejected with a toast.
- Enable/disable auto-deploy per deployment; delete with confirmation.
- Select a deployment to see its webhook URL (with copy button),
  HMAC auth note (`GITOPS_WEBHOOK_TOKEN` over `X-Timestamp` + body),
  repository/branch/target details, and push history.
- Every action maps to the panel API below; failures surface as toasts
  and the list reloads from the server.

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/deployments` | List the caller's deployments. |
| `POST` | `/api/deployments` | Create (`name` + `repoUrl` required). |
| `PATCH` | `/api/deployments/:id/toggle` | Flip `enabled`. |
| `GET` | `/api/deployments/:id/history` | Push history for one deployment. |
| `DELETE` | `/api/deployments/:id` | Remove a deployment. |

Pushes arrive via the orchestrator's `POST /webhook/gitops`
(see the root README's GitOps example and `wiki/08-Security.md`).

Set `VITE_PUBLIC_WEBHOOK_URL` to the HTTPS ingress host and public webhook
route for your deployment. With the example Helm ingress, this is
`https://api.infra-pilot.example.com/webhook/gitops`; replace the host with
your configured ingress host and include any public path prefix. The panel
shows this URL verbatim (after trimming whitespace). If unset, it shows
"Webhook URL not configured" and disables Copy.

Vite embeds this setting at build time. Set it in `.env.local` before
starting Vite or building the standalone panel. For production Compose, set it in
the root `.env` and rebuild the panel with
`docker compose -f docker-compose.yml build management-panel`, then recreate
its container with `docker compose -f docker-compose.yml up -d management-panel`.
For a direct Docker build, pass `--build-arg VITE_PUBLIC_WEBHOOK_URL=<url>`.
Changing only the environment of a production container does not update
the built frontend.

## Development checks

```bash
npm run lint
npm test
npm run build
```

The project also contains Playwright and accessibility tests; see `package.json` and `tests/` for the exact commands.

## Docker integration

The panel invokes Docker operations for application lifecycle actions, logs,
stats, and terminal-related features. Give Docker access only to trusted
deployments, because the Docker socket is privileged.
