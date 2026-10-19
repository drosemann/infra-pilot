# Auth Matrix

Every HTTP route in the project with its auth layer, status and notes.
"Status" reflects the last security pass; anything not listed here is a
finding and must be fixed or explicitly accepted.

> **How to keep this current:** every PR that adds or changes a route
> must update this table in the same commit.

## Conventions

| Term | Meaning |
| ------ | --------- |
| `verifyAuth` | Express middleware: Supabase JWT, falls back to scrypt-hashed API key |
| `requireSelfPermission` | `verifyAuth` + RBAC check against the caller's own personal resources (`server/rbac/`) |
| `requireAppId` | `verifyAuth` + RBAC app-scope decision (ownership → app assignment → instance role) |
| `requireInstancePermission` | `verifyAuth` + RBAC check granted by instance role only |
| federation token | Bearer token, constant-time compare, **fails closed in production** |
| HMAC-SHA256 | GitHub webhook signature, fails closed (503) when secret unset |
| public | No auth by design; must be documented here |

## RBAC model (`server/rbac/`, PROMPT 2)

All protected management-panel routes now sit behind the shared RBAC
enforcement layer. One decision engine (`server/rbac/store.ts`) issues
grants for HTTP and the WebSocket gateway alike:

| Scope | Resources | Decision order |
| ------ | --------- | -------------- |
| app | `app`, `backup`, `deployment`, `config`, `metrics`, `maintenance`, `members` | owner (`docker_apps.user_id`) → app assignment (`rbac_app_roles`: admin/operator/viewer/custom) → instance role (`rbac_instance_roles`, only `admin` covers app actions) |
| personal | `inventory`, `databases`, `webhooks`, `plugins`, `ssh`, `secrets`, `billing`, `runbooks`, `audit`, `notifications`, `apikeys`, `customers`, `reports` | caller's own rows (`user_id`); `PERSONAL_SELF_ACTIONS` lists which actions the self path confers; app `owner` is implicit via `user_id` and never persisted |
| instance | `templates`, `settings` | role-gated only (admins get `*`; operators/viewers get the `read`/`templates:read`/`settings:read` entries in `INSTANCE_ROLE_GRANTS`) |

Additional rules:

- Denials return `403 { error, code: 'rbac_denied', resourceType, action, reason }`
  and emit an `rbac:denied` audit event without payload contents.
- Unknown apps return `404` (not 403) for app-scoped routes.
- Store/cache failures fail closed (`503 rbac_unavailable`).
- Legacy per-app boolean permissions (`ServerPermissionSet`) are mapped to
  equivalent grants by `SERVER_PERMISSION_MAP` so old clients keep working.
- WebSocket access (`resolveWsAppAccess`) delegates to the same store:
  terminal/exec needs console access, `logs:read` needs console or files,
  `metrics:read` needs any assignment or ownership.
- Last-admin safety: demoting or revoking the final instance admin is
  refused with `409`.

## Orchestrator Agent (`services/orchestrator-agent`, port 8500)

| Route | Method | Auth | Status | Notes |
| ------- | -------- | ------ | -------- | ------- |
| `/health` | GET | public | ok | Docker healthcheck |
| `/api/health` | GET | public | ok | CLI compatibility |
| `/metrics` | GET | public | ok | Prometheus scrape, no sensitive data |
| `/api/v1/federation/status` | GET | federation token | ok | Info only |
| `/api/v1/rbac/roles` | GET/POST | federation token | ok | |
| `/api/v1/rbac/orgs` | GET/POST | federation token | ok | |
| `/api/v1/rbac/assign` | POST | federation token | ok | |
| `/api/v1/rbac/orgs/{org_id}/permissions` | GET | federation token | ok | |
| `/api/v1/rbac/orgs/{org_id}/members` | GET | federation token | ok | |
| `/webhook/github[/{deploy_id}]` | POST | HMAC-SHA256 | ok | Only mounted when `GitDeployer` cog is loaded |
| `/webhook/gitops` | POST | HMAC-SHA256 (`GITOPS_WEBHOOK_TOKEN` over `X-Timestamp` + body) | ok | Mounted unconditionally; one signature per replay window |

**Production default:** without `FEDERATION_API_TOKEN` every `/api/` route
returns 503. In development a missing token logs a warning and allows
requests (matches `validate_secrets` convention in `config.py`).

## Management Panel (`services/management-panel`, port 3001)

Two layers: `verifyAuth` (authentication) then RBAC guards
(authorization). RBAC-denied writes are audited; every guard order is
`verifyAuth` → limiter → RBAC guard.

### Public (by design)

| Route | Method | Status | Notes |
| ------- | -------- | -------- | ------- |
| `/health` | GET | ok | Docker healthcheck |
| `/api/health` | GET | ok | CLI compatibility |
| `/api/setup/status` | GET | ok | First-run check |
| `/api/setup/init` | POST | ok | Creates first admin; `loginLimiter` applied; refuses re-init; bootstraps RBAC admin role |
| `/api/auth/login` | POST | ok | API key login; `loginLimiter` applied |
| `/api/auth/logout` | POST | ok | No server state to revoke |
| `/api/validate/discord-token` | POST | ok | Validates a Discord token; no data returned |
| `/api/demo/flag` | GET | ok | Feature-gating flag, no data leak |
| `/api/sso/providers` | GET | ok | Only enabled booleans + ids, no secrets |
| `/api/sso/login/:provider` | GET | ok | OIDC redirect (PKCE + single-use state); `loginLimiter` applied |
| `/api/sso/callback/:provider` | GET | ok | State consumed before any lookup; id_token verified (RS256/JWKS); redirects only, never returns tokens in the body |
| `/api/sso/saml` | GET | ok | Explicit `501`: SAML is not implemented (documented, not faked) |
| `/api/openapi.json`, `/api/docs` | GET | ok | API surface is public by design |
| `/api/auth/2fa/verify` | POST | ok | Pre-auth step of login flow |
| `/api/auth/2fa/verify-backup` | POST | ok | Pre-auth step of login flow |

### Protected (`verifyAuth` + RBAC guard)

`verifyAuth` accepts, in order: a Supabase JWT, an SSO panel session
(Bearer `sso_...` or the `ip_session` cookie — DB-backed, revocable), or
a scrypt-hashed API key. An invalid `sso_` Bearer token never falls
through to JWT/API-key matching.

A route-level table is generated from the source; the contract below is
what each guard guarantees:

| Guard family | Routes | Who passes |
| ------- | ------ | ----------- |
| `requireAppId` | `/api/apps/:id` (read/write/delete), lifecycle, clone, snapshots, logs, status, autopilot, billing, plugins install, config + versions + rollback, metrics (also unscoped aggregates via `{ optional: true }`), maintenance-windows, scheduled-tasks, backup-jobs/artifacts/restore, modpacks, deployments, alert-configs/history, health-checks, reports + export, databases, roles endpoints | app owner; assigned app role (`admin`/**`operator`**/**`viewer`**/`custom` via legacy booleans); instance `admin` |
| `requireSelfPermission` | inventory, secrets (+rotation/access), webhooks (+test/logs), api-keys, plugins catalog/update, templates deploy, changes/undo/rollback, runbooks, customers (+seed-demo), notification-channels, 2FA setup/verify-setup/disable (also verifies body `user_id` = caller) | any authenticated user acting on **their own** rows; personal actions map in `server/rbac/catalog.ts` |
| `requireInstancePermission('settings', …)` | `/api/templates/init` (write), `/api/rbac/instance-roles` GET (read) / POST+DELETE (write), `/api/sso/group-roles` GET (read) / PUT+DELETE (write) | instance `admin` (operators/viewers only have settings `read`) |

Related authority rules:

- `/api/apps/:id/roles` management requires the caller to own the app or
  hold instance admin; assignments use `rbac_app_roles` and principals
  may be `user:<uuid>` or `discord:<id>`.
- Only the app owner (or instance admin) may assign roles for an app;
  the `owner` role itself is never persisted.
- The WebSocket gateway re-checks every message against the same store;
  tickets from `/api/ws-token` are bound to the caller and optionally to
  one app. See [15-WS-Auth](./15-WS-Auth.md).
- `/api/rbac/me` returns the caller's instance role and memberships for
  frontend navigation; it never elevates anything.

### Findings (open)

None at this pass. The former finding (runbooks GET lacked `verifyAuth`)
was closed by the RBAC pass; `GET /api/runbooks` now sits behind
`verifyAuth` + `requireSelfPermission('runbooks','read')`.

### Pre-auth by design (rate-limited, no bearer)

| Route | Method | Guard | Notes |
|-------|--------|-------|-------|
| `/api/auth/2fa/verify` | POST | `loginLimiter` | TOTP login step `{ temp_token, totp_code }` |
| `/api/auth/2fa/verify-backup` | POST | `loginLimiter` | Backup-code login step `{ temp_token, backup_code }` |

Full user flow: [14-Two-Factor-Auth](./14-Two-Factor-Auth.md).
SSO session endpoints (`/api/sso/session`, `/api/sso/logout`,
`/api/sso/group-roles`) sit behind `verifyAuth` and the RBAC instance
guard; see the SSO row in the guard-family table. SAML is explicitly
not implemented (`/api/sso/saml` answers 501, documented as roadmap
work).

## Update History

- 2026-10-19: SSO/OIDC authorization-code + PKCE flow (`server/sso/`)
  with JWKS-verified id_tokens, JIT provisioning behind email/domain
  allowlists, DB-backed revocable panel sessions accepted by
  `verifyAuth` (Bearer `sso_` / `ip_session` cookie), group→role
  mapping admin API. SAML documented as future work (explicit 501,
  never faked).
- 2026-10-19: RBAC enforcement layer (`server/rbac/`) wired across all
  protected routes; WS gateway delegated to the same decision store;
  `GET /api/runbooks` finding closed by the same work; `/api/rbac/*`
  admin routes added (last-admin lockout enforced).
- 2026-09-29: 2FA setup/verify-setup/disable confirmed behind
  `verifyAuth`, verify/verify-backup confirmed pre-auth with
  `loginLimiter`; added unit (`two-factor-auth-flow`) and
  integration contract tests.
- 2026-08-08: initial matrix; federated `/api/` made fail-closed in
  production; runbooks GET and 2FA setup/verify-setup/disable flagged
  and fixed; audit payloads centrally sanitized (no tokens, secrets,
  env vars or webhook URLs in audit events).
