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

## API and authentication

| Surface | URL | Notes |
| --- | --- | --- |
| Health | `GET /health`, `GET /api/health` | Used by Compose health checks. |
| OpenAPI | `GET /api/openapi.json` | Current panel API contract. |
| Swagger UI | `GET /api/docs` | Interactive API documentation. |
| WebSocket ticket | `POST /api/ws-token` | Mints a short-lived handshake ticket (authenticated). |
| WebSocket | `ws://host:3001?ticket=<ticket>` | Authenticated logs, metrics, and terminal. |

Setup, health, and documentation endpoints are intentionally reachable without
an application session. Operational `/api/*` routes are protected by the
backend's `verifyAuth` middleware unless explicitly documented otherwise.
 Treat the OpenAPI document and `server/index.ts` as the authoritative
route list.

## Access control (RBAC)

Authorization is layered on top of `verifyAuth` by the RBAC module in
`server/rbac/`:

- **App-scoped routes** (`/api/apps/:id` and everything hanging off it) check
  ownership first (`docker_apps.user_id`), then per-app assignments
  (`rbac_app_roles`: `admin`/`operator`/`viewer`/`custom`), then the
  instance role. Denials return `403 { code: 'rbac_denied', ... }` and are
  audited; unknown apps return `404`.
- **Personal routes** (inventory, secrets, webhooks, API keys, plugins,
  runbooks, customers, notifications, …) apply to the caller's own rows;
  the reachable action set per resource lives in
  `server/rbac/catalog.ts` (`PERSONAL_SELF_ACTIONS`).
- **Instance routes** (template init, RBAC admin routes) require the
  instance `admin` role stored in `rbac_instance_roles`.

Instance roles are managed on **Settings → Access Roles**
(`/settings/roles`) or via `GET/POST /api/rbac/instance-roles` and
`DELETE /api/rbac/instance-roles/:userId` (admin only, audited, last-admin
lockout enforced). The first admin is promoted automatically during
setup. App owners and per-app members are managed per app. The WebSocket
gateway resolves app access through the same RBAC store as the REST API.

## SSO / OIDC

The panel implements the OIDC **authorization-code flow with PKCE** by
hand (`server/sso/` — no OAuth framework dependency). Supported
providers: Google, Microsoft Entra ID, and any generic OIDC issuer
(Keycloak, Authentik, ...). A provider is usable only when its client id
**and** secret env vars are set; see `.env.example`.

What you get:

- `GET /api/sso/login/:provider` → 302 to the IdP (PKCE S256, state,
  nonce; state is single-use and expires after ten minutes).
- `GET /api/sso/callback/:provider` → code exchange, id_token signature
  verification (RS256 via JWKS, iss/aud/exp/nonce checks), JIT
  provisioning with email/domain allowlists, then a redirect to the SPA
  with a panel-session token (URL fragment) plus an `ip_session` cookie.
- Panel sessions are DB rows (`panel_sessions`) — revocable and
  expiring; `verifyAuth` accepts both the Bearer token (`sso_...`) and
  the cookie. `GET /api/sso/session` reports how a caller got in.
- Identity claims map to instance roles via the group table
  (`sso_group_roles`); admin-API at `/api/sso/group-roles`. These mappings
  apply only to users without an already-set (admin-chosen) role.
  Required: `SUPABASE_SERVICE_ROLE_KEY` (identity linking/JIT uses the
  Supabase auth admin API), `SESSION_SECRET`, and `PANEL_PUBLIC_URL` so
  IdP redirect URIs can be registered as
  `<PANEL_PUBLIC_URL>/api/sso/callback/<provider>`.

**SAML is not implemented.** `GET /api/sso/saml` answers `501` with a
roadmap note rather than pretending; a signed-Response SAML verifier is
future work. GitHub's OAuth2 app flow has no id_token and is also not
offered through the OIDC path. Single-instance caveat: authorization
state (`state`/`nonce`) is in-memory per process; horizontal panel
deployments need sticky routing until a shared store lands.

## WebSocket authentication

The realtime gateway (`server/ws/`) requires every WebSocket connection to
authenticate with a short-lived, single-use ticket before any feature message
is honored. Per-app actions (log streaming, metrics, terminal input/exec) are
then authorized against app ownership and role assignments — deny by default.

Handshake:

1. `POST /api/ws-token` (same `verifyAuth` as the rest of the API) returns
   `{ ticket, expiresIn, appScope }`. Pass `{ "appId": "..." }` to scope the
   ticket to one app; scoping requires access to that app.
2. Connect to `ws://host:3001/?ticket=<ticket>` (or connect without a ticket
   and answer the `auth_challenge` frame with `{ "type": "auth", "ticket" }`
   within `WS_AUTH_TIMEOUT_MS`).
3. The server replies `{ "type": "ready", sessionId, userId, appScope, mode }`;
   only then may the client send `subscribe`, `subscribe:metrics`, `join`,
   `terminal-input`, `exec`, and related messages.

Tickets are HMAC-signed, bound to the user (and optionally one app), expire
within five minutes, and can be revoked:

- `POST /api/ws-token/revoke` with `{ "ticket": "..." }` revokes one ticket.
- `POST /api/ws-token/revoke` with `{ "all": true }` revokes every ticket for
  the caller and closes their live sessions.

Connections that fail authentication are closed with codes 4001-4003;
authorization and policy failures use 4004, 4008, 4009, 4013, and 4014 (see
`server/ws/types.ts` and `wiki/15-WS-Auth.md` for the full table). Tickets are
single-use: reconnecting requires minting a new one. Ticket strings are never
written to logs or audit records. Sessions idle for `WS_IDLE_TIMEOUT_SECONDS`
(default 30 minutes) are terminated, and each user may hold at most
`WS_MAX_SESSIONS_PER_USER` concurrent sessions.

The gateway enforces per-connection and per-user rate limits with token
buckets (`WS_MAX_MESSAGES_PER_MINUTE`, `WS_MAX_SUBSCRIBES_PER_MINUTE`);
denied attempts receive a structured `rate_limited` error with `retryAfterMs`
and repeated strikes close the connection. Every subscription, terminal
action, denial, and rate-limit event is recorded through the panel's audit
log (`ws:*` actions).

Threat model notes: the ticket is a bearer credential for at most five
minutes; compromise of `WS_TICKET_SECRET` allows ticket forgery, so keep it
server-side only and rotate by restarting without the var or by redeploying.
Ticket presentation is logged as an audit event without the ticket value.
See `wiki/15-WS-Auth.md` for the protocol reference and `SECURITY.md` for the
trust-boundary statement.

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
| `WS_TICKET_SECRET` | HMAC key for WebSocket handshake tickets (min 32 chars; ephemeral when unset). |
| `WS_TICKET_TTL_SECONDS`, `WS_TICKET_SKEW_SECONDS` | Ticket lifetime (max 300) and clock-skew tolerance. |
| `WS_AUTH_TIMEOUT_MS`, `WS_IDLE_TIMEOUT_SECONDS`, `WS_HEARTBEAT_INTERVAL_SECONDS` | Connection lifecycle windows. |
| `WS_MAX_SESSIONS_PER_USER`, `WS_SESSION_LIMIT_POLICY` | Per-user session cap and eviction policy. |
| `WS_MAX_MESSAGES_PER_MINUTE`, `WS_MAX_SUBSCRIBES_PER_MINUTE` | Gateway rate limits. |
| `WS_MAX_RATE_STRIKES`, `WS_MAX_VIOLATIONS`, `WS_MAX_MESSAGE_BYTES` | Escalation and frame-size limits. |

## Code map

| Path | Responsibility |
| --- | --- |
| `src/` | React UI, routes, components, hooks, and browser API clients. |
| `server/index.ts` | Express routes, authentication, WebSocket gateway wiring, and service startup. |
| `server/ws/` | Authenticated WebSocket gateway: tickets, ACL, sessions, rate limits, audit. |
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
