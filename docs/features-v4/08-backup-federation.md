# Feature 8: Cloud-Native Backup Federation

## Overview
Backup workloads across cloud boundaries. Restore workload from one cloud to another. Provider-agnostic backup vault with geo-redundancy.

## Components
- `backup_federation.py` — Cross-cloud backup/restore manager
- `BackupFederationCog` — Discord commands for backup federation
- `BackupFederation.tsx` — React cross-cloud backup manager
- CLI commands in `cli/ipilot/commands/hybrid_cloud/backup_federation.py`

## API Endpoints
- `GET /api/backup-federation/backups` — List backups
- `POST /api/backup-federation/backups` — Create backup
- `POST /api/backup-federation/backups/:id/execute` — Execute backup
- `POST /api/backup-federation/restore` — Restore backup
- `GET /api/backup-federation/restores` — List restore jobs
- `GET /api/backup-federation/vaults` — List vaults

## Supported Targets
AWS S3, Azure Blob, GCP Storage, Hetzner Storage Box, OVH Object Storage, Local
