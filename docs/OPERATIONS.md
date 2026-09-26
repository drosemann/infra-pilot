# Operations guide

Practical companion to the wiki for operators. For background,
start with [wiki/Home](../wiki/Home.md).

---

## Environments

| Environment | Command | Notes |
| --- | --- | --- |
| Local full stack (dev) | `docker compose up -d` | Auto-loads `compose.override.yml` (HMR dev servers) |
| Production compose | `docker compose -f docker-compose.yml up -d` | Prod panel image, no dev override; TLS via reverse proxy |
| Monitoring | `docker compose --profile monitoring up -d` | Prometheus, Grafana, postgres-exporter, node-exporter |
| Discord | `docker compose --profile discord up -d` | Needs Discord credentials; trusted lab only (socket mount) |
| Load test | `make load-smoke` | k6 smoke scenario |

---

## Configuration checklist

1. Copy `.env.example` to `.env`.
2. Run `bash scripts/generate-env.sh`.
3. Set `POSTGRES_PASSWORD`, `GITOPS_WEBHOOK_TOKEN`,
   and `FEDERATION_API_TOKEN`.
4. Review `CORS_ORIGINS` and `VITE_API_URL`.
5. Keep `.env` out of git. Prefer secret managers in
   production.

---

## Health checks

```bash
curl -s http://localhost:3001/health
curl -s http://localhost:8500/health
docker compose ps
bash scripts/healthcheck.sh
```

Expected: HTTP `200` from both health endpoints and
`healthy` services in Compose output.

---

## Backups

```bash
# Local only (Postgres + Redis snapshot + Grafana volume archive)
bash scripts/db-backup.sh

# Production: encrypted + offsite (cron daily 02:00 recommended)
bash scripts/db-backup.sh --s3 s3://my-bucket/infra-pilot \
  --encrypt-to ops@example.com --no-plaintext

# Restore (decrypts .gpg automatically; confirm prompt unless --yes)
bash scripts/db-restore.sh backups/infra-pilot_<stamp>.dump --yes
```

Retention defaults: daily 7, weekly 4, monthly 6.
Keep an off-host copy. Test restores regularly.
Redis/Grafana artifacts restore by copying back into the `redis_data` /
`grafana_data` volumes while the stack is stopped.
Details: [wiki/12-Backup-Restore](../wiki/12-Backup-Restore.md).

---

## Production checklist (P0/P1 hardening)

1. Deploy without the dev override:
   `docker compose -f docker-compose.yml up -d`; terminate TLS at a
   reverse proxy / ingress — Express (`:3001`) and the orchestrator
   (`:8500`) never serve public traffic directly.
2. Secrets: `bash scripts/generate-env.sh` fills `POSTGRES_PASSWORD`,
   `GITOPS_WEBHOOK_TOKEN`, `FEDERATION_API_TOKEN` and
   `GRAFANA_ADMIN_PASSWORD` with random values. Never mount
   `/var/run/docker.sock` directly in production — use an allowlisted
   socket proxy and point `DOCKER_HOST` at it.
3. Container spawns reject privileged host ports (`< 1025`),
   `LD_PRELOAD`/`DOCKER_HOST` env vars and off-allow-list images
   (optional `ALLOWED_IMAGES` prefix list); oversized manifests get
   400/413 (`MAX_BODY_BYTES`, default 256 KiB).
4. Kubernetes: the chart deploys orchestrator + management panel with
   probes, HPA, NetworkPolicies and `existingSecret`
   (`infra-pilot-secrets`); Terraform keeps the RDS password in Secrets
   Manager (ARN output) and uses immutable ECR tags.
5. Observe: Prometheus scrapes orchestrator `/metrics` (includes
   `orchestrator_auth_failures_total{outcome=...}`), postgres-exporter
   and node-exporter; Grafana admin password is generated, not `admin`.
   Alert on rising `federation_401`/`webhook_401` (brute force) and
   `federation_503` (token misconfiguration).

---

## Troubleshooting entry points

- [wiki/10-Troubleshooting](../wiki/10-Troubleshooting.md)
- [wiki/09-FAQ](../wiki/09-FAQ.md)
- `docker compose logs -f management-panel orchestrator-agent`
- Panel doctor and diagnostics endpoints

---

## Release hygiene

- `bash scripts/verify.sh` before pushing branches.
- `bash scripts/test.sh --coverage` for full suites.
- Helm: `helm lint` and `helm template` before chart changes.
- Never commit secrets, tokens, `.env`, or private keys.
