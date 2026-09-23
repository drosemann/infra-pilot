# Operations guide

Practical companion to the wiki for operators. For background,
start with [wiki/Home](../wiki/Home.md).

---

## Environments

| Environment | Command | Notes |
| --- | --- | --- |
| Local full stack | `docker compose up -d` | Panel, orchestrator, PG, Redis |
| Monitoring | `docker compose --profile monitoring up -d` | Prometheus, Grafana, exporter |
| Discord | `docker compose --profile discord up -d` | Needs Discord credentials |
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
bash scripts/db-backup.sh
bash scripts/db-restore.sh --dry-run
```

Retention defaults: daily 7, weekly 4, monthly 6.
Keep an off-host copy. Test restores regularly.
Details: [wiki/12-Backup-Restore](../wiki/12-Backup-Restore.md).

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
