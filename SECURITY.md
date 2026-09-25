# Security Policy & Threat Model

This document is the security contract for Infra Pilot. It states who can do
what through which interface, what the trust boundaries are, and how to report
problems. **Pre-1.0 status: there are no tagged releases yet; treat every
change as unreleased.**

## Reporting a Vulnerability

**Do not** post security issues in public. Email the maintainers instead
(the address is in the repository profile / commit history).

Please include:

- What the problem is
- Which component and endpoint are affected
- How to reproduce it
- How severe you think it is

**We will:** acknowledge within 48 hours, then provide a fix timeline.
Critical issues (remote code execution, credential disclosure, auth bypass)
get a fix before any other work.

## Threat Model

### Components and trust boundaries

```
                      ┌────────────────────────────┐
   Public Internet ──▶│ Orchestrator Agent          │
                      │  - webhook server (:8500)   │
                      │  - Discord bot              │
                      └──────┬───────────┬──────────┘
                             │           │
             Docker socket   │           │  HTTP/DB
                             ▼           ▼
                     Containers (VPS)   PostgreSQL / Redis
```

| # | Boundary | Assets | Trust |
|---|----------|--------|-------|
| B1 | Internet → webhook server | Container lifecycle, deploy pipeline | Untrusted by default; only HMAC/Bearer-authenticated requests pass |
| B2 | Discord API → bot | Command execution, secrets, VPS lifecycle | Discord session tokens; app commands are scoped by RBAC role checks |
| B3 | Orchestrator → Docker daemon | Host access (socket = root equivalent) | Highest privilege in the system; must be minimized per operation |
| B4 | Orchestrator → PostgreSQL/Redis | Users, backups, rotation metadata | Service credentials only; no interactive logins |
| B5 | Management panel ↔ Supabase | Panel data, auth | Supabase key must never leave the server side |
| B6 | CLI ↔ orchestrator API | API keys, config profiles | TLS in production; token stored in `~/.ipilot/config.json` |

### Who can do what via which API

| Interface | Who | What they can do | Guard |
|-----------|-----|------------------|-------|
| `GET /health`, `GET /api/health` | Anyone | Check liveness (no DB) | No sensitive data returned |
| `GET /ready`, `GET /api/ready` | K8s / load-balancer | Readiness (DB check) | 503 if DB down; used as `readinessProbe` |
| `GET /metrics` | Anyone (network-restricted) | Read operational metrics | Must not leak secrets/container internals; restrict at network layer |
| `POST /webhook/gitops` | CI/CD systems | Reconcile a manifest (deploy) | `X-Signature-256` = HMAC-SHA256 of `X-Timestamp` + body (`GITOPS_WEBHOOK_TOKEN`), one signature per replay window; **fail closed** (503) if unset |
| `GET /api/v1/federation/status` | Other pilot instances | Read federation status | Constant-time federation token check; 503 without token unless `ALLOW_INSECURE_FEDERATION=true` in explicit local envs (`dev`/`development`/`local`) |
| `POST /api/v1/deployments`, `GET /api/v1/providers` | CLI / management panel (federation token holders = platform admins) | Trigger manifest reconciliation | Federation token (fail-closed by default); `user_id`+`org_id` strictly validated and checked against `manifest:deploy` for scoping/audit; `as_platform_admin=true` is asserted by the token holder (accident-prevention, not a privilege boundary — any token holder can set it); admin path is logged |
| `/api/v1/rbac/*` | Federation token holders (platform admins), scoped per-actor | Manage roles/orgs/memberships (create + revoke) | RBAC engine + per-project scoping; `actor_user_id` (query/header/body) is asserted by the token holder for scoping/audit, not independently authenticated; deletions persist via `rbac_store` (store-first, 500 without in-memory mutation on DB failure) so revokes survive restart |
| Discord app commands | Discord users | Manage VPS, backups, deploy, secrets | Bot-level role/permission checks; container names validated against `SAFE_CONTAINER_PATTERN`; health-check targets validated against allow-lists |
| `docker exec`/`docker run` (via bot) | RBAC-authorized users | Run commands in containers | **No `--privileged`, no `--cap-add=ALL`**; never `shell=True`; subprocess args passed as lists; resource limits enforced against `RESOURCE_LIMITS` |

### Secrets and credentials

- Secrets live in environment variables / `.env` files, **never** in code or
  committed files. Placeholders in `.env.example` are `CHANGE_ME`.
- The orchestrator **refuses to start** in production while placeholder
  secrets are set (fail fast).
- Production requires an explicit `POSTGRES_PASSWORD`; no hardcoded defaults.
- The secrets manager encrypts values at rest; keys stay out of the repo.
- Gitleaks scans the full git history on every push; npm audit and pip-audit
  run for dependency CVEs.

### Infrastructure credentials and monitoring

- Terraform state contains the RDS password even though it is omitted from
  outputs. The state bucket requires versioning, default SSE-S3/AES256,
  blocked public access, and restricted IAM access.
- Production deployment reads `infra-pilot-prod-postgres-password` from
  Secrets Manager into `infra-pilot-secrets` under `db-password` before Helm
  runs with `secrets.create=false`. The deployment role needs
  `secretsmanager:GetSecretValue` on that secret, plus `kms:Decrypt` if a
  customer managed KMS key is used. Kubernetes access must permit Secret
  creation and patching in the deployment namespace.
- Provision the other required keys (`postgres-password`, `redis-password`,
  and `api-key`) in that Secret through your secret manager before deployment.
  The sync preserves those keys. Passwords must stay out of Helm values,
  Terraform outputs, and deployment logs.
- Compose node-exporter uses the host network namespace and listens only on
  the private Docker bridge address configured by `NODE_EXPORTER_HOST_IP`.
  Prometheus reaches that address from `infra-pilot-net`; port 9100 is not
  bound on public interfaces. This configuration targets Linux Docker hosts.
- Helm allows panel egress and orchestrator ingress on TCP 8500 within the
  same release. When the panel's token Secret is configured, the Secret and
  `orchestrator-api-token` key must exist for the Pod to start.
- Encrypted backups upload only the `.gpg` artifact to S3. Plaintext may
  remain locally unless `--no-plaintext` is set.

### Container isolation (regression contract)

Container spawns MUST NOT:

- run with `--privileged` or `--cap-add=ALL`
- take image/name/command strings built via string interpolation or a shell
- bypass the per-VPS resource limits
- bind host ports `< 1025` (privileged; requires operator override outside
  the manifest), accept `LD_PRELOAD`/`LD_LIBRARY_PATH`/`DOCKER_HOST` env
  vars, or pull images outside the optional `ALLOWED_IMAGES` prefix
  allow-list

Regression tests assert these properties on every CI run
(`test_create_vps_never_spawns_privileged_containers`,
`test_container_name_validation_rejects_injection`,
`services/orchestrator-agent/tests/unit/test_hardening_p0.py`).

### Production deployment notes

- `docker-compose.yml` defaults to the production panel image.
  `compose.override.yml` (auto-loaded) restores HMR dev servers for local
  work only. Before running `docker compose -f docker-compose.yml up -d` in
  production, change the management-panel port mappings to bind to
  `127.0.0.1` (for example, `127.0.0.1:3001:3001` and
  `127.0.0.1:5173:5173`). Alternatively, remove the panel's host port
  mappings and connect the TLS proxy through the Compose network. The
  unmodified file publishes panel ports on all interfaces. Terminate TLS at
  the proxy / ingress; Express and the orchestrator must not serve public
  traffic directly.
- Manifests are strictly validated on the API path (`validate(strict=True)`):
  privileged host ports, denied env vars, oversized payloads
  (`MAX_BODY_BYTES`, default 256 KiB, 413 on excess) and unbounded maps are
  rejected with 400/413 before reconciliation.
- `/api/*` and `/webhook/gitops` are rate-limited per client IP (429 with
  `Retry-After`); limits are intentionally modest on deploy/webhook routes.
- The Docker socket is host-root equivalent. In production never mount
  `/var/run/docker.sock` directly — put an allowlisted socket proxy
  (e.g. `tecnativa/docker-socket-proxy`) in front and point `DOCKER_HOST`
  at it. The direct mount in compose is trusted-dev/lab only.

### Known hardening history

| Date | Issue |
|------|-------|
| 2026-07 | Docker command injection closed; privileged container flags removed |
| 2026-07 | GitHub/GitOps webhooks now verified (HMAC/Bearer), fail closed |
| 2026-07 | Wide-open CORS restricted to configured origins |
| 2026-07 | Hardcoded/placeholder secrets replaced; placeholder secrets rejected in production |
| 2026-08 | Gitleaks + npm audit gates enabled in CI; coverage gates raised |
| 2026-08 | Health-check command injection fixed (allow-list + list exec) and resource limits enforced; federation auth now fail-closed by default (`ALLOW_INSECURE_FEDERATION`) |
| 2026-08 | RBAC revocation persistence fixed (DELETE routes + `rbac_store`); Helm secrets now required (fail-fast), readiness probe `/ready` added; discord-service hardened (read_only, no-new-privileges, cap_drop ALL, :ro) |
| 2026-08 | CI hardened: promtool config check, postgres 16-alpine alignment, coverage gates (orchestrator 50%, panel 35%, discord 20%), bandit/ESLint warnings promoted |
| 2026-09 | P0 production hardening: compose prod-default + dev override, panel
  Express defaults (bounded JSON, security headers, no fingerprint),
  strict manifest/spawn validation, bounded webhook bodies, per-IP rate
  limits on `/api/*` + `/webhook/gitops` |

## Security Best Practices (for contributors)

- Never put passwords or API keys in code. Use environment variables.
- Validate user input; use parameterized database queries everywhere.
- New HTTP endpoints require a guard: HMAC, Bearer token, or RBAC — no
  "trusted by default" routes.
- New container-spawn code paths must keep the isolation contract above.
- Update `SECURITY.md` when you change a trust boundary.

## Tools

| Language   | Tools                           | Gate  |
|------------|---------------------------------|-------|
| Python     | `bandit`, `pip-audit`, `pytest-cov` | CI fails on findings / coverage drop |
| JavaScript | `npm audit`, `node --test`      | CI fails on high+ vulns |
| Everything | `gitleaks` (full history)       | CI fails on leaked secrets |

## Supported Versions

| Version        | Support                       |
|----------------|-------------------------------|
| Pre-1.0 (main) | Patch fixes, no stability promise |
| 1.0+ (planned) | Full security patches         |
