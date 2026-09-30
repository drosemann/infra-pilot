# Backup & Restore

All Infra Pilot services share a single PostgreSQL database (`infra_pilot` by
default), so one backup covers the orchestrator (Alembic-managed schema),
Discord service (`server_limits`, statistics), and management panel data.

## Backup

```bash
./scripts/db-backup.sh
```

This creates a `pg_dump` custom-format backup at
`backups/infra-pilot_<timestamp>.dump` and keeps only the 10 most recent files.

Options:

| Option        | Description                              |
|---------------|------------------------------------------|
| `--keep N`    | Keep only the N most recent backups      |
| `--out DIR`   | Use a different output directory         |

The script starts the `postgres` container via `docker compose` if the stack
is not running.

## Restore

```bash
./scripts/db-restore.sh backups/infra-pilot_20260701_091500.dump
```

What happens:

1. The script verifies the file is a `pg_dump` custom-format backup.
2. You get a confirmation prompt (skip with `--yes`).
3. It restores into the running `postgres` container using
   `pg_restore --clean --if-exists --no-owner`, i.e. existing tables are
   dropped and recreated from the backup.

### Before restoring

Stop the services that write to the database to avoid conflicts:

```bash
docker compose stop orchestrator-agent discord-service management-panel
```

Restart them after the restore:

```bash
docker compose start orchestrator-agent discord-service management-panel
```

The orchestrator runs `alembic upgrade head` on startup, so the schema is
brought up to date automatically after a restore.

## Cron example

```bash
# docker-compose.yml gets a backup job, or on the host:
0 3 * * * /path/to/infra-pilot/scripts/db-backup.sh --keep 14 >> /var/log/infra-pilot-backup.log 2>&1
```

## Self-hosted offsite: borgbackup + rclone (no S3 needed)

For self-hosters without S3, `db-backup.sh` supports deduplicated
borg archives and `rclone copyto` to any configured remote
(Hetzner Storage Box, NAS, MinIO, Nextcloud via WebDAV, etc.).

```bash
# One-time: install tools + init repo + configure rclone remote
sudo apt install borgbackup rclone
borg init --encryption=repokey-blake2 /mnt/backup/borg
rclone config  # create e.g. "hetzner-box" (sftp) or "nas" (smb/webdav/sftp)

# Encrypted borg repo needs a passphrase (borg convention):
export BORG_PASSPHRASE='long-random-passphrase'
export BORG_REPO=/mnt/backup/borg

# Daily backup: local artifacts + borg + rclone
bash scripts/db-backup.sh \
  --borg-repo /mnt/backup/borg \
  --rclone-remote hetzner-box:infra-pilot \
  --keep 10

# Via env fallbacks (e.g. in cron or .env):
BACKUP_BORG_REPO=/mnt/backup/borg \
BACKUP_RCLONE_REMOTE=hetzner-box:infra-pilot \
bash scripts/db-backup.sh --keep 14
```

What happens with `--borg-repo`:

1. Local `pg_dump` / Redis / Grafana artifacts are created as usual.
2. `borg info <repo>` is checked; a missing repo is initialised
   with `borg init --encryption=repokey-blake2`.
3. All artifacts go into one archive
   `borg create <repo>::infra-pilot-<stamp> <files>`
   with `--compression lz4`.
4. `borg prune --keep-last <N>` applies the same `--keep` retention.

What happens with `--rclone-remote`:

- Every finished artifact (or its `.gpg` copy when
  `--encrypt-to` is used) is copied with
  `rclone copyto <file> <remote>/<basename>`.
- Combine with `--encrypt-to ops@example.com --no-plaintext`
  to store only GPG-encrypted copies offsite.

Cron examples:

```bash
# borg only, daily 02:00, self-hosted disk / NAS mount
0 2 * * * /opt/infra-pilot/scripts/db-backup.sh \
  --borg-repo /mnt/backup/borg \
  >> /var/log/infra-pilot-backup.log 2>&1

# rclone only, to Hetzner Storage Box / NAS / MinIO
0 2 * * * /opt/infra-pilot/scripts/db-backup.sh \
  --rclone-remote hetzner-box:infra-pilot \
  >> /var/log/infra-pilot-backup.log 2>&1
```

Restore from self-hosted copies:

```bash
# List borg archives, extract a Postgres dump, restore it
borg list /mnt/backup/borg
borg extract /mnt/backup/borg::infra-pilot_<stamp>
bash scripts/db-restore.sh backups/infra-pilot_<stamp>.dump --yes

# Fetch back from an rclone remote first
rclone copyto hetzner-box:infra-pilot/infra-pilot_<stamp>.dump \
  backups/infra-pilot_<stamp>.dump
bash scripts/db-restore.sh backups/infra-pilot_<stamp>.dump --yes
```

Tips:

- Keep `BORG_PASSPHRASE` in a password manager, not in shell
  history. Without it an encrypted repo cannot be restored.
- Test `borg extract` + `db-restore.sh --dry-run` style checks
  (`pg_restore --list`) before you rely on the cron job.
- rclone remotes are configured once with `rclone config`;
  verify with `rclone lsd <remote>:` before scheduling.

## Restoring a fresh database

After `docker compose down -v`, start `postgres`, then restore:

```bash
docker compose up -d postgres
./scripts/db-restore.sh backups/infra-pilot_<timestamp>.dump --yes
docker compose up -d
```
