# Feature 6: Cloud Migration Toolkit

## Overview
Agentless discovery of on-prem workloads. Dependency mapping, migration wave planning, cutover orchestration. Rollback on migration failure.

## Components
- `cloud_migration.py` — Discovery agent, dependency mapper, wave planner
- `CloudMigrationCog` — Discord commands for migration management
- `CloudMigration.tsx` — React migration wizard page
- CLI commands in `cli/ipilot/commands/hybrid_cloud/cloud_migration.py`

## API Endpoints
- `GET /api/migration/workloads` — List discovered workloads
- `POST /api/migration/discover` — Discover new workload
- `GET /api/migration/workloads/:id/assess` — Assess workload compatibility
- `POST /api/migration/waves` — Create migration wave
- `GET /api/migration/waves` — List waves
- `POST /api/migration/waves/:id/execute` — Execute wave
- `POST /api/migration/waves/:id/rollback` — Rollback wave

## Discovery Methods
Agentless, SSH, WinRM, SNMP, API
