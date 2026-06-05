# ai backup validator

feature id: 5
category: ai & intelligence
primary service: integration service
effort estimate: medium (4-6 pt)
status: planned

## overview

restore backups to ephemeral containers and run automated integrity checks to validate backup quality. the validator ensures backups are not just present but usable -- databases have consistent schemas, file hashes match expected values, and applications start correctly in the restored environment.

a validation score is calculated for each backup, and detailed reports are surfaced in the management panel.

### goals

- ensure all backups are actually restorable before the data is needed
- detect silent backup corruption immediately rather than at recovery time
- provide a quantifiable validation score for each backup
- support db consistency checks (postgresql, mysql, mongodb), file integrity verification, and application health probes
- schedule validation automatically after each backup completes

## architecture

```
┌──────────────────────────────────────────────────────────┐
│                  Backup Sources                           │
│  ┌────────────┐  ┌────────────┐  ┌────────────────────┐ │
│  │ Filesystem │  │ PostgreSQL │  │ MySQL / MongoDB    │ │
│  │ Snapshots  │  │ Dumps      │  │ Dumps              │ │
│  └──────┬─────┘  └──────┬─────┘  └────────┬───────────┘ │
└─────────┼────────────────┼──────────────────┼─────────────┘
          │                │                  │
          ▼                ▼                  ▼
┌──────────────────────────────────────────────────────────┐
│              Integration Service                          │
│                                                           │
│  ┌────────────────────────────────────────────────────┐  │
│  │            Ephemeral Restore Engine                  │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │  │
│  │  │ Target   │──│ Restore  │──│ Container         │ │  │
│  │  │ Selection│  │ Executor │  │ Lifecycle Manager │ │  │
│  │  └──────────┘  └──────────┘  └────────┬─────────┘ │  │
│  └────────────────────────────────────────────────────┘  │
│                        │                                 │
│                        ▼                                 │
│  ┌────────────────────────────────────────────────────┐  │
│  │            Integrity Check Engine                    │  │
│  │  ┌──────────────┐  ┌────────────┐  ┌────────────┐ │  │
│  │  │ DB           │  │ File Hash  │  │ Application│ │  │
│  │  │ Consistency  │  │ Verifier   │  │ Health     │ │  │
│  │  │              │  │            │  │ Probe      │ │  │
│  │  └──────┬───────┘  └─────┬──────┘  └──────┬─────┘ │  │
│  │         │                │                │        │  │
│  │         ▼                ▼                ▼        │  │
│  │  ┌────────────────────────────────────────────┐    │  │
│  │  │      Validation Scorer                      │    │  │
│  │  │  Weighted score: 0.0 - 1.0                  │    │  │
│  │  └──────────────────┬─────────────────────────┘    │  │
│  └─────────────────────┼──────────────────────────────┘  │
│                        │                                 │
│                        ▼                                 │
│  ┌────────────────────────────────────────────────────┐  │
│  │            Reporting & Scheduling                    │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │  │
│  │  │ Report   │──│ Schedule │──│ Notification     │ │  │
│  │  │ Generator│  │ Engine   │  │ (on failure)     │ │  │
│  │  └──────────┘  └──────────┘  └──────────────────┘ │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────┐
│              Container Runtime (Docker/K8s)               │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Ephemeral Validation Container (Temporary)         │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │  │
│  │  │ Restored │──│ DB Check │──│ Health Check     │ │  │
│  │  │ Data     │  │ Scripts  │  │ (app start +     │ │  │
│  │  │ Volume   │  │          │  │  HTTP probe)     │ │  │
│  │  └──────────┘  └──────────┘  └──────────────────┘ │  │
│  │  ┌──────────────────────────────────────────────┐ │  │
│  │  │  Results → sent to Integration Service        │ │  │
│  │  └──────────────────────────────────────────────┘ │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

## implementation plan

### phase 1: ephemeral restore engine (1.5-2 pt)

| step | description | artifacts |
|------|-------------|-----------|
| 1.1 | target backup selection logic | latest, specific backup id, or random sampling |
| 1.2 | ephemeral container provisioning | docker api / k8s job creation with restore volume |
| 1.3 | restore executor | download backup, extract, apply to ephemeral environment |
| 1.4 | resource limits & cleanup | cpu/ram limits, ttl-based container cleanup, timeout handling |

**restore workflow:**

```yaml
# config/restore_templates.yaml
restore_templates:
  postgres:
    image: "postgres:16-alpine"
    restore_command: |
      pg_restore -U validator -d postgres /backup/dump.sql
    env:
      POSTGRES_PASSWORD: "{{ .TempPassword }}"
    resources:
      cpu: "1"
      memory: "2Gi"
    timeout_seconds: 300

  filesystem:
    image: "alpine:latest"
    restore_command: |
      tar xzf /backup/archive.tar.gz -C /restored
    resources:
      cpu: "0.5"
      memory: "1Gi"
    timeout_seconds: 600

  mysql:
    image: "mysql:8.0"
    restore_command: |
      mysql -u validator -p"{{ .TempPassword }}" < /backup/dump.sql
    env:
      MYSQL_ROOT_PASSWORD: "{{ .TempPassword }}"
    resources:
      cpu: "1"
      memory: "2Gi"
    timeout_seconds: 300

  mongodb:
    image: "mongo:7"
    restore_command: |
      mongorestore --drop /backup/dump/
    resources:
      cpu: "1"
      memory: "2Gi"
    timeout_seconds: 600
```

### phase 2: integrity checks (1.5-2 pt)

| step | description | artifacts |
|------|-------------|-----------|
| 2.1 | db consistency checks | `pg_checksums`, `mysqlcheck`, `mongodb validate` |
| 2.2 | schema integrity verification | compare restored schema to expected baseline |
| 2.3 | table row counts & data sampling | validate record counts match backup manifest |
| 2.4 | file hash verification | sha-256 checksum comparison against backup manifest |
| 2.5 | application health probes | http/s start check, port binding verification |

**integrity check scripts:**

```python
# pseudocode: integrity_checks.py
class IntegrityChecker:
    async def check_database(self, db_type: str, conn_string: str) -> CheckResult:
        checks = []
        score = 0.0

        if db_type == "postgres":
            # Check database consistency
            result = await self._run_sql(conn_string, "SELECT count(*) FROM pg_class WHERE relkind = 'r'")
            table_count = result[0][0]
            checks.append(Check("table_count", table_count > 0, {"tables": table_count}))

            # Check for corruption
            corrupt = await self._run_shell(f"pg_checksums -c {conn_string}")
            checks.append(Check("no_corruption", corrupt.exit_code == 0, {"output": corrupt.stdout}))

            # Check schema against baseline
            schema = await self._get_schema(conn_string)
            baseline = await self._load_baseline(self.backup_id)
            schema_match = self._compare_schema(schema, baseline)
            checks.append(Check("schema_matches_baseline", schema_match, {"diff": schema.diff}))

        # ... similar for mysql, mongodb

        return CheckResult(checks=checks, score=sum(c.weight for c in checks if c.passed) / len(checks))

    async def check_files(self, backup_manifest: dict, restored_path: str) -> CheckResult:
        checks = []
        verified = 0
        failed = 0

        for entry in backup_manifest["files"]:
            expected_hash = entry["sha256"]
            actual_hash = self._compute_hash(f"{restored_path}/{entry['path']}")
            if actual_hash == expected_hash:
                verified += 1
            else:
                failed += 1
                checks.append(Check(
                    f"hash_{entry['path']}",
                    False,
                    {"expected": expected_hash, "actual": actual_hash}
                ))

        checks.append(Check("file_integrity", failed == 0, {
            "verified": verified, "failed": failed, "total": verified + failed
        }))
        return CheckResult(checks=checks, score=verified / (verified + failed) if (verified + failed) > 0 else 0)
```

### phase 3: scoring & reporting (1 pt)

| step | description | artifacts |
|------|-------------|-----------|
| 3.1 | validation score calculation | weighted combination of individual checks |
| 3.2 | report generation | structured json report + human-readable summary |
| 3.3 | trend tracking over time | per-backup, per-server validation history |
| 3.4 | notification on failure | critical alert if score < threshold |

**scoring formula:**

```
Validation Score = 0.0 - 1.0

Weights (configurable):
  Database consistency:      0.35
  Schema integrity:          0.20
  File hash verification:    0.25
  Application health probe:  0.20

Thresholds:
  Pass:  >= 0.90
  Warning: 0.70 - 0.89
  Fail:   < 0.70
```

**validation report:**

```json
{
  "validation_id": "val-20260527-001",
  "backup_id": "bkp-20260527-003",
  "server_id": "srv-001",
  "server_name": "db-primary",
  "backup_type": "postgres",
  "started_at": "2026-05-27T03:00:00Z",
  "completed_at": "2026-05-27T03:12:34Z",
  "duration_seconds": 754,
  "overall_score": 0.94,
  "status": "pass",
  "checks": {
    "database_consistency": {
      "score": 1.0,
      "weight": 0.35,
      "checks": [
        {"name": "table_count", "passed": true, "detail": "42 tables found"},
        {"name": "no_corruption", "passed": true, "detail": "pg_checksums: no corruption detected"},
        {"name": "index_validity", "passed": true, "detail": "All indexes valid"}
      ]
    },
    "schema_integrity": {
      "score": 0.85,
      "weight": 0.20,
      "checks": [
        {"name": "schema_vs_baseline", "passed": true, "detail": "Schema matches baseline"},
        {"name": "row_count_accuracy", "passed": false,
         "detail": "Table 'sessions' has 1,234,567 rows vs expected 1,250,000 (98.8%)",
         "actual": 1234567, "expected": 1250000}
      ]
    },
    "file_integrity": {
      "score": 1.0,
      "weight": 0.25,
      "checks": [
        {"name": "file_hash_verification", "passed": true,
         "detail": "All 1,248 files verified, 0 mismatches"}
      ]
    },
    "application_health": {
      "score": 0.9,
      "weight": 0.20,
      "checks": [
        {"name": "postgres_accepts_connections", "passed": true,
         "detail": "Connection pool test: 10/10 connections established"},
        {"name": "query_performance", "passed": true,
         "detail": "Sample query completed in 4ms (baseline: 5ms)"},
        {"name": "replication_slot_check", "passed": false,
         "detail": "1 stale replication slot found (slot_name: 'old_slot', not in use)"}
      ]
    }
  },
  "recommendations": [
    "Investigate table 'sessions' row count discrepancy",
    "Drop stale replication slot 'old_slot' on db-primary"
  ]
}
```

### phase 4: scheduling & automation (1 pt)

| step | description | artifacts |
|------|-------------|-----------|
| 4.1 | post-backup trigger | webhook or event subscription: on backup complete → validate |
| 4.2 | scheduled validation | cron-based periodic re-validation of critical backups |
| 4.3 | random sampling | validate random n% of backups even without explicit trigger |
| 4.4 | retention of validation results | store last n validation reports, purge old artifacts |

## api design

### rest api

#### trigger validation

```
POST /api/v1/validations
```

request:
```json
{
  "backup_id": "bkp-20260527-003",
  "server_id": "srv-001",
  "checks": ["database", "files", "health"],
  "priority": "high",
  "notify_on_completion": true
}
```

response:
```json
{
  "validation_id": "val-20260527-001",
  "status": "running",
  "estimated_duration_seconds": 600
}
```

#### get validation result

```
GET /api/v1/validations/{id}
```

response: (full report json as shown above)

#### list validations

```
GET /api/v1/validations
  ?server_id=srv-001
  &status=pass,fail
  &from=2026-05-01T00:00:00Z
  &to=2026-05-27T23:59:59Z
  &min_score=0.9
  &limit=50
```

#### get validation summary (dashboard)

```
GET /api/v1/validations/summary
  ?server_id=srv-001
  &days=30
```

response:
```json
{
  "total_validations": 45,
  "passed": 40,
  "warning": 3,
  "failed": 2,
  "average_score": 0.93,
  "trend": "stable",
  "latest_scores": [
    {"date": "2026-05-27", "score": 0.94},
    {"date": "2026-05-26", "score": 0.91},
    {"date": "2026-05-25", "score": 0.95}
  ],
  "latest_failures": [
    {
      "backup_id": "bkp-20260525-001",
      "server_name": "db-primary",
      "score": 0.45,
      "reason": "pg_checksums: corruption detected in table 'orders'",
      "validated_at": "2026-05-25T04:00:00Z"
    }
  ]
}
```

#### schedule validation policy

```
PUT /api/v1/validations/policies/{server_id}
```

request:
```json
{
  "enabled": true,
  "trigger_on_backup": true,
  "schedule_cron": "0 5 * * *",
  "checks": ["database", "files", "health"],
  "score_threshold_warning": 0.85,
  "score_threshold_fail": 0.70,
  "notify_on": ["fail", "warning"],
  "retention_days": 90
}
```

## data model

```python
# models/backup_validator.py
@dataclass
class ValidationRequest:
    backup_id: str
    server_id: str
    checks: list[str]        # database, files, health
    priority: str            # low / normal / high
    notify_on_completion: bool

@dataclass
class ValidationResult:
    id: str
    backup_id: str
    server_id: str
    server_name: str
    backup_type: str         # postgres / mysql / mongodb / filesystem
    started_at: datetime
    completed_at: datetime | None
    duration_seconds: int | None
    overall_score: float
    status: str              # running / pass / warning / fail / error
    checks: dict[str, CheckCategory]
    recommendations: list[str]
    container_id: str | None
    error: str | None

@dataclass
class CheckCategory:
    score: float
    weight: float
    checks: list[Check]

@dataclass
class Check:
    name: str
    passed: bool
    detail: str
    actual: Any | None
    expected: Any | None

@dataclass
class ValidationPolicy:
    server_id: str
    enabled: bool
    trigger_on_backup: bool
    schedule_cron: str | None
    checks: list[str]
    score_threshold_warning: float
    score_threshold_fail: float
    notify_on: list[str]
    retention_days: int
```

**database schema:**

```sql
-- Validation results
CREATE TABLE validation_results (
    id              TEXT PRIMARY KEY,
    backup_id       TEXT NOT NULL,
    server_id       TEXT NOT NULL,
    server_name     TEXT NOT NULL,
    backup_type     TEXT NOT NULL,
    started_at      TIMESTAMPTZ NOT NULL,
    completed_at    TIMESTAMPTZ,
    duration_seconds INTEGER,
    overall_score   DOUBLE PRECISION,
    status          TEXT NOT NULL DEFAULT 'running',
    checks          JSONB,
    recommendations JSONB DEFAULT '[]',
    container_id    TEXT,
    error           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_val_server ON validation_results(server_id);
CREATE INDEX idx_val_status ON validation_results(status);
CREATE INDEX idx_val_score ON validation_results(overall_score);
CREATE INDEX idx_val_backup ON validation_results(backup_id);

-- Validation policies
CREATE TABLE validation_policies (
    server_id       TEXT PRIMARY KEY,
    enabled         BOOLEAN DEFAULT TRUE,
    trigger_on_backup BOOLEAN DEFAULT TRUE,
    schedule_cron   TEXT,
    checks          JSONB DEFAULT '["database", "files", "health"]',
    score_threshold_warning DOUBLE PRECISION DEFAULT 0.85,
    score_threshold_fail DOUBLE PRECISION DEFAULT 0.70,
    notify_on       JSONB DEFAULT '["fail"]',
    retention_days  INTEGER DEFAULT 90,
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Backup integrity metadata (file manifest)
CREATE TABLE backup_manifests (
    backup_id       TEXT PRIMARY KEY,
    server_id       TEXT NOT NULL,
    backup_type     TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL,
    file_count      INTEGER NOT NULL,
    total_size_bytes BIGINT NOT NULL,
    files           JSONB,    -- array of {path, sha256, size_bytes}
    db_metadata     JSONB     -- table schemas, row counts for DB backups
);
```

## service assignments

| service | responsibility |
|---------|---------------|
| integration service | ephemeral restore orchestration, integrity check engine, validation scorer, reporting, scheduling engine, policy management |
| orchestrator agent | backup event hooks, ephemeral container provisioning on compute nodes, network isolation for validation containers |
| management panel | validation dashboard, report viewer (pass/warning/fail), policy configuration ui, trend chart, failure drill-down |

## configuration reference

```yaml
# config/backup_validator.yaml
restore:
  container_ttl_minutes: 30
  max_concurrent_validations: 5
  resource_limits:
    default:
      cpu: "1"
      memory: "2Gi"
    large_backup:
      cpu: "4"
      memory: "8Gi"
      threshold_bytes: 10737418240  # 10 GB
  network_isolated: true
  cleanup_on_completion: true

checks:
  database:
    postgres:
      consistency_tool: "pg_checksums"
      schema_comparison: true
      row_count_accuracy: true
      row_count_tolerance_percent: 5.0
    mysql:
      consistency_tool: "mysqlcheck"
      schema_check: true
    mongodb:
      validation: true
      index_check: true

  files:
    hash_algorithm: "sha256"
    verify_all_files: true
    sample_size: null       # null = all files, else percentage

  health:
    probe_timeout_seconds: 30
    retry_count: 3
    required_checks:
      - port_open
      - process_running
      - connection_test

scoring:
  weights:
    database_consistency: 0.35
    schema_integrity: 0.20
    file_integrity: 0.25
    application_health: 0.20
  thresholds:
    pass: 0.90
    warning: 0.70
    fail: 0.00

scheduling:
  post_backup_trigger: true
  cron_schedule: "0 6 * * *"
  random_sample_percent: 10
  retention_days: 90

notifications:
  on_pass: false
  on_warning: true
  on_fail: true
  on_error: true
  channels: ["panel", "discord"]
```

**docker compose for ephemeral validator container:**

```yaml
# docker/validator-compose.yaml
version: "3.8"
services:
  validator:
    image: infrapilot/backup-validator:latest
    restart: "no"
    environment:
      VALIDATION_ID: "${VALIDATION_ID}"
      BACKUP_STORAGE_URL: "${BACKUP_STORAGE_URL}"
      BACKUP_TYPE: "${BACKUP_TYPE}"
      CHECK_TYPES: "${CHECK_TYPES}"
      REPORT_CALLBACK_URL: "http://integration-service:8000/api/v1/validations/${VALIDATION_ID}/callback"
    volumes:
      - restored-data:/restored
    networks:
      - isolated-validation
    deploy:
      resources:
        limits:
          cpus: "1.0"
          memory: 2G

volumes:
  restored-data:

networks:
  isolated-validation:
    internal: true
```

## effort breakdown

| phase | task | pt | dependencies |
|-------|------|----|-------------|
| 1.1 | backup selection logic | 0.5 | backup catalog |
| 1.2 | ephemeral container provisioning | 1 | docker/k8s access |
| 1.3 | restore executor | 0.5 | container runtime |
| 1.4 | resource limits & cleanup | 0.5 | container runtime |
| 2.1 | db consistency checks | 1 | database tools |
| 2.2 | schema integrity verification | 0.5 | baseline schema store |
| 2.3 | row count validation | 0.25 | db access |
| 2.4 | file hash verification | 0.5 | hash computation |
| 2.5 | application health probes | 0.5 | http client |
| 3.1 | score calculation | 0.25 | check results |
| 3.2 | report generation | 0.5 | score output |
| 3.3 | trend tracking | 0.25 | time-series storage |
| 3.4 | failure notification | 0.25 | notifier service |
| 4.1 | post-backup trigger | 0.25 | event bus |
| 4.2 | scheduled validation | 0.25 | cron scheduler |
| 4.3 | random sampling | 0.25 | sampling logic |
| 4.4 | retention & cleanup | 0.25 | scheduler |
| | total | 6.25 | |

## risks & mitigations

| risk | impact | mitigation |
|------|--------|------------|
| ephemeral restore impacts production | resource contention | strict resource limits, dedicated node pool for validation, throttle concurrent validations |
| restore takes too long | validation delays | configurable timeout, incremental restore for large backups, streaming validation |
| false positive (valid backup flagged bad) | unnecessary re-backup | configurable thresholds, manual review option, multiple check types with redundancy |
| false negative (corrupted backup passes) | data loss at recovery | multi-layered checks (hashes + db consistency + health), checksum verification against backup manifest |
| validation container security | attack surface | network isolation, no persistent storage, temp credentials, automatic cleanup |

## metrics & kpis

| metric | target | measurement |
|--------|--------|-------------|
| backup validation coverage | > 90% of all backups | validated backups / total backups |
| mean validation time | < 10 min | duration per validation |
| recovery confidence score | > 0.95 | average score across all validations |
| undetected corruption rate | < 0.1% | corrupt backups missed / total corrupt |
| validation failure rate | < 5% | failed validations / total validations |
| time from backup to validation | < 30 min | time from backup completion to validation start |
