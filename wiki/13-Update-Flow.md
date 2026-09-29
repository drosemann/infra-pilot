# Update Flow (new version, keep all data)

`scripts/update.sh` is the supported path from one version to the
next. It backs up first, pulls fast-forward only, rebuilds, and
verifies health — without ever deleting named volumes.

## Quick start

```bash
# Validate only (no changes)
bash scripts/update.sh --check-only

# Full update, keep all data
bash scripts/update.sh --yes

# Self-hosted offsite backup as part of the update
bash scripts/update.sh \
  --backup-args "--borg-repo /mnt/backup/borg" --yes
```

## What happens step by step

1. **Preflight.** Checks `docker`, `git`, and
   `docker compose config`. Fails fast on invalid compose files.
2. **Pre-update backup.** Runs `scripts/db-backup.sh` (Postgres
   dump + Redis snapshot + Grafana archive). Skip only with
   `--skip-backup` (not recommended). Extra backup flags go via
   `--backup-args "..."` (e.g. `--borg-repo`, `--rclone-remote`,
   `--encrypt-to`).
3. **Git pull.** `git pull --ff-only` so a diverged checkout never
   auto-merges. Skip with `--skip-git` if you already updated.
4. **Rebuild + restart.**
   `docker compose up -d --build` plus optional `--compose-args`.
   The script refuses `-v` / `--volumes` / `down -v` — updates
   never delete `postgres_data`, `redis_data`, `prometheus_data`,
   or `grafana_data`.
5. **Verify.** Runs `scripts/healthcheck.sh --dry-run` and checks
   `infra-pilot_postgres_data` / `infra-pilot_redis_data` with
   `docker volume inspect`. The orchestrator runs
   `alembic upgrade head` on startup, so the schema migrates
   forward automatically.

## Data-retention guarantees (tested)

- `down -v` is never executed by the script; the flags `--volumes`,
  `-v`, and `--compose-args "down -v"` exit with code `2`.
- `docker compose down` (without `-v`) is safe: it keeps volumes.
- Alembic migrations run forward on orchestrator start; restores
  also converge via `alembic upgrade head`.
- Tests: `tests/scripts/test_update_flow.py` covers help text,
  volume-deletion refusal, check-only purity, full backup →
  pull → rebuild → health ordering, and missing-docker fail-fast.

## Rollback

```bash
# Option A: go back to the previous commit, keep data
git log --oneline -5
git checkout <previous-commit>
docker compose up -d --build

# Option B: restore the pre-update backup (data as of backup time)
bash scripts/db-restore.sh backups/infra-pilot_<stamp>.dump --yes
docker compose up -d
```

If the panel or orchestrator fails health checks after an update,
see [10-Troubleshooting](./10-Troubleshooting.md) and the
`docker compose logs -f management-panel orchestrator-agent`
output before rolling back.

## Automation

```bash
# Weekly unattended update with borg offsite (example cron, Sun 04:00)
0 4 * * 0 /opt/infra-pilot/scripts/update.sh \
  --yes --backup-args "--borg-repo /mnt/backup/borg" \
  >> /var/log/infra-pilot-update.log 2>&1
```

Unattended updates still need a clean git checkout (no local
modifications) because `pull --ff-only` refuses to merge.
