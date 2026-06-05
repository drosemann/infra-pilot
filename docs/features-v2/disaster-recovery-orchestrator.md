# feature 25: disaster recovery orchestrator

| metadata | value |
|----------|-------|
| feature id | 25 |
| feature name | disaster recovery orchestrator |
| primary service | orchestrator agent |
| effort estimate | large (7-10 pt) |
| status | planned |

## 1. overview

a comprehensive disaster recovery (dr) orchestration framework that enables users to define, test, and execute recovery plans across multiple regions or providers. supports three dr topologies -- **active-passive**, **pilot light**, and **warm standby** -- with one-click drill execution, automated rto/rpo measurement, and compliance reporting.

### goals

- reduce recovery time from hours to minutes via automated runbooks
- provide auditable, repeatable dr drills with zero production impact
- track and report rto (recovery time objective) and rpo (recovery point objective) per application
- support heterogeneous dr topologies within the same organisation
- generate compliance-ready reports for soc2, iso 27001, pci-dss

## 2. architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Panel (UI)                                  │
│  ┌────────────┐  ┌──────────────┐  ┌────────────┐  ┌────────────┐  │
│  │ DR Plan    │  │ DR Drill     │  │ RTO/RPO    │  │ Compliance │  │
│  │ Designer   │  │ Console      │  │ Dashboard  │  │ Reports    │  │
│  └─────┬──────┘  └──────┬───────┘  └──────┬─────┘  └─────┬──────┘  │
└────────┼────────────────┼──────────────────┼──────────────┼─────────┘
         │                │                  │              │
         ▼                ▼                  ▼              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     Orchestrator Agent (DR Engine)                   │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                     DR Plan Manager                           │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐  │   │
│  │  │ Topology     │ │ Replication  │ │ Runbook / Step       │  │   │
│  │  │ Validator    │ │ Configurator │ │ Generator            │  │   │
│  │  └──────┬───────┘ └──────┬───────┘ └──────────┬───────────┘  │   │
│  └─────────┼────────────────┼────────────────────┼───────────────┘   │
│            │                │                    │                   │
│  ┌─────────▼────────────────▼────────────────────▼───────────────┐   │
│  │                     Drill Engine                               │   │
│  │  ┌──────────┐ ┌───────────┐ ┌──────────┐ ┌─────────────────┐  │   │
│  │  │ Failover │ │ Failback  │ │ Snapshot │ │ Validation      │  │   │
│  │  │ Executor │ │ Executor  │ │ Manager  │ │ & Rollback      │  │   │
│  │  └────┬─────┘ └─────┬─────┘ └────┬─────┘ └───────┬─────────┘  │   │
│  └───────┼─────────────┼────────────┼────────────────┼────────────┘   │
│          │             │            │                │                │
│  ┌───────▼─────────────▼────────────▼────────────────▼────────────┐   │
│  │  RTO/RPO Measurement & Compliance Engine                       │   │
│  │  ┌────────────┐ ┌──────────────┐ ┌──────────┐ ┌────────────┐  │   │
│  │  │ Timer /    │ │ Data Lag     │ │ Audit    │ │ Report     │  │   │
│  │  │ Clock      │ │ Monitor      │ │ Logger   │ │ Generator  │  │   │
│  │  └────────────┘ └──────────────┘ └──────────┘ └────────────┘  │   │
│  └───────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
         │                │                  │              │
         ▼                ▼                  ▼              ▼
┌────────────┐   ┌────────────┐   ┌────────────┐  ┌──────────────┐
│ Primary    │   │ DR (DR)    │   │ DNS /      │  │ Cloud       │
│ Region /   │   │ Region /   │   │ Traffic    │  │ Provider    │
│ Provider   │   │ Provider   │   │ Router     │  │ APIs        │
└────────────┘   └────────────┘   └────────────┘  └──────────────┘
```

### component responsibilities

| component | role |
|-----------|------|
| dr plan manager | defines topology, replication config, and step-by-step runbooks |
| topology validator | validates the dr plan for correctness and resource coverage |
| replication configurator | sets up database sync, volume replication, log shipping |
| drill engine | executes failover, failback, with snapshotting and rollback |
| rto/rpo engine | measures elapsed time and data loss during drills |
| compliance reporter | generates audit-ready dr reports |

## 3. dr topologies

### 3.1 active-passive

```

[Primary] ── replication ── [Standby]
  ▲                              │
  │                              │
  └────────── failover ──────────┘

```

- **primary**: handles all production traffic
- **standby**: idle replica, receives continuous replication
- **rto**: 5-15 minutes | **rpo**: < 1 minute
- **replication**: synchronous or semi-synchronous database replication

### 3.2 pilot light

```

[Primary] ── [S3/GCS Bucket] ── [Minimal DR Stack]
  ▲                                        │
  │                                        │
  └───────── scale-up + redirect ──────────┘

```

- **primary**: full production stack
- **dr**: core data (db snapshots + s3) replicated; compute scaled to zero
- **on failover**: auto-scale dr compute, restore from snapshots, redirect dns
- **rto**: 15-45 minutes | **rpo**: 5-15 minutes

### 3.3 warm standby

```

[Primary] ── replication ── [DR with reduced capacity]
  ▲                                      │
  │                                      │
  └────────── scale-up + failover ────────┘

```

- **dr**: runs with a smaller instance count but fully operational
- **on failover**: scale up dr, redirect traffic
- **rto**: 5-15 minutes | **rpo**: < 5 minutes

## 4. data model

### `dr_plans`

| field | type | description |
|-------|------|-------------|
| id | uuid | primary key |
| environment_id | uuid | fk to environments.id |
| name | varchar | human-readable plan name |
| description | text | |
| topology | enum | active_passive, pilot_light, warm_standby |
| status | enum | draft, validated, active, archived |
| primary_region | varchar | e.g. "us-east-1" or "gcp-us-central1" |
| dr_region | varchar | e.g. "eu-west-1" or "gcp-europe-west1" |
| provider | enum | aws, gcp, azure, hetzner, multi |
| rpo_seconds | int | target recovery point objective |
| rto_seconds | int | target recovery time objective |
| config | jsonb | provider-specific dr config |
| created_at | timestamptz | |
| updated_at | timestamptz | |

### `dr_plan_steps`

| field | type | description |
|-------|------|-------------|
| id | uuid | primary key |
| plan_id | uuid | fk to dr_plans.id |
| step_order | int | execution order |
| name | varchar | e.g. "stop primary app", "promote replica" |
| action_type | enum | script, api_call, dns_update, wait, manual |
| action_config | jsonb | script path, api endpoint, dns record, timeout |
| timeout_seconds | int | max execution time before failure |
| retry_count | int | how many retries on failure |
| critical | boolean | if true, abort entire drill on failure |
| created_at | timestamptz | |

### `dr_replication_configs`

| field | type | description |
|-------|------|-------------|
| id | uuid | primary key |
| plan_id | uuid | fk to dr_plans.id |
| resource_type | varchar | "database", "storage", "volume", "config" |
| source | varchar | source identifier |
| target | varchar | target identifier |
| method | varchar | "streaming_replication", "s3_cross_region", "rsync", "acm" |
| schedule | varchar | cron expression for sync (pilot light) |
| monitoring | jsonb | lag threshold alerts |
| enabled | boolean | |
| created_at | timestamptz | |

### `dr_drills`

| field | type | description |
|-------|------|-------------|
| id | uuid | primary key |
| plan_id | uuid | fk to dr_plans.id |
| name | varchar | e.g. "q3 dr drill -- active-passive" |
| status | enum | running, completed_success, completed_with_issues, failed, rolled_back |
| started_at | timestamptz | |
| completed_at | timestamptz | |
| measured_rto_seconds | int | actual rto achieved |
| measured_rpo_seconds | int | actual rpo achieved |
| rto_met | boolean | |
| rpo_met | boolean | |
| results | jsonb | step-by-step results and logs |
| initiated_by | uuid | fk to users.id |
| notes | text | |

### `dr_audit_log`

| field | type | description |
|-------|------|-------------|
| id | uuid | primary key |
| drill_id | uuid | fk to dr_drills.id |
| plan_id | uuid | fk to dr_plans.id |
| step_id | uuid | fk to dr_plan_steps.id (nullable) |
| action | varchar | |
| status | varchar | |
| message | text | |
| duration_ms | int | |
| timestamp | timestamptz | |

## 5. api design

### dr plans

```
POST   /api/v2/dr/plans                      — Create DR plan
GET    /api/v2/dr/plans                       — List DR plans
GET    /api/v2/dr/plans/:id                   — Get plan details
PUT    /api/v2/dr/plans/:id                   — Update plan
DELETE /api/v2/dr/plans/:id                   — Archive plan
POST   /api/v2/dr/plans/:id/validate          — Validate topology & config
```

### plan steps

```
GET    /api/v2/dr/plans/:id/steps             — List steps
POST   /api/v2/dr/plans/:id/steps             — Add step
PUT    /api/v2/dr/plans/:id/steps/:sid        — Update step
DELETE /api/v2/dr/plans/:id/steps/:sid        — Remove step
POST   /api/v2/dr/plans/:id/steps/reorder     — Reorder steps
```

### replication

```
GET    /api/v2/dr/plans/:id/replication       — List replication configs
POST   /api/v2/dr/plans/:id/replication       — Add replication config
PUT    /api/v2/dr/plans/:id/replication/:rid   — Update
DELETE /api/v2/dr/plans/:id/replication/:rid   — Remove
POST   /api/v2/dr/plans/:id/replication/sync  — Trigger manual sync (pilot light)
```

### drills

```
POST   /api/v2/dr/plans/:id/drills            — Start a DR drill
GET    /api/v2/dr/plans/:id/drills            — List past drills
GET    /api/v2/dr/drills/:did                 — Get drill details & logs
POST   /api/v2/dr/drills/:did/cancel          — Cancel running drill
POST   /api/v2/dr/drills/:did/rollback        — Roll back to pre-drill state
```

### rto/rpo & compliance

```
GET    /api/v2/dr/plans/:id/compliance        — Compliance report for a plan
GET    /api/v2/dr/drills/:did/compliance      — Drill compliance details
GET    /api/v2/dr/compliance/summary          — Org-wide compliance summary
GET    /api/v2/dr/compliance/export           — Export as PDF/CSV
```

## 6. implementation plan

### phase 1 -- dr plan definition & validation (2 pt)

• define `dr_plans`, `dr_plan_steps`, `dr_replication_configs` tables and crud
• implement `topologyvalidator`:
   - checks that primary and dr regions are distinct
   - validates network connectivity between sites
   - ensures required resources exist in dr region
• build dr plan designer ui -- drag-and-drop topology selection, step builder

### phase 2 -- replication configuration (2 pt)

• implement `replicationconfigurator`:
   - database replication (postgresql streaming, mysql binlog, cross-region rds)
   - volume/block storage replication (ebs snapshots, persistent disk snapshots)
   - object storage cross-region replication (s3 crr, gcs object retention)
• build sync status monitoring with lag alerts
• add manual sync trigger for pilot-light topology

### phase 3 -- drill engine (3 pt)

• implement `failoverexecutor`:
   - executes each step in order with timeout and retry
   - promotes replica database to primary
   - updates dns / traffic routing
   - switches monitoring and alerting to dr region
• implement `failbackexecutor`:
   - reverses the failover process
   - resyncs data back to the original primary
   - restores dns to primary
• implement `snapshotmanager` -- takes pre-drill snapshots for rollback
• implement `validationandrollback` -- post-step validation hooks + full rollback on critical failure

### phase 4 -- rto/rpo measurement (1 pt)

• `rtotimer` -- starts on drill initiation, stops when application health check passes on dr
• `rpomonitor` -- measures data lag by comparing latest replicated record timestamps
• store measured metrics in `dr_drills` and compare against targets
• alert on rto/rpo breach

### phase 5 -- compliance reporting (0.5 pt)

• build report templates for soc2, iso 27001, pci-dss
• generate pdf reports with drill history, rto/rpo summaries, and step logs
• export as csv for siem ingestion

### phase 6 -- ui & polish (1-1.5 pt)

• dr plan designer (visual topology picker)
• drill console (real-time step log streaming)
• rto/rpo dashboard with historical trends
• compliance report viewer
• scheduled drill capability (e.g., first sunday of every quarter)

## 7. configuration examples

### dr plan definition (post /api/v2/dr/plans)

```json
{
  "name": "Production — Warm Standby",
  "environment_id": "env-prod-001",
  "topology": "warm_standby",
  "primary_region": "aws:us-east-1",
  "dr_region": "aws:eu-west-1",
  "rpo_seconds": 300,
  "rto_seconds": 900,
  "config": {
    "auto_failback": true,
    "failback_cooldown_minutes": 60,
    "dns_ttl": 60,
    "health_check_endpoint": "https://app.example.com/health",
    "dr_scale_up_size": "same",
    "notify_on_completion": ["ops@example.com"]
  }
}
```

### drill runbook step example

```json
{
  "plan_id": "plan-001",
  "steps": [
    {
      "step_order": 1,
      "name": "Validate DR prerequisites",
      "action_type": "script",
      "action_config": {
        "script": "dr-validate-prereqs.sh",
        "params": {"region": "eu-west-1"}
      },
      "timeout_seconds": 120,
      "critical": true
    },
    {
      "step_order": 2,
      "name": "Stop primary application traffic",
      "action_type": "dns_update",
      "action_config": {
        "record": "app.example.com",
        "ttl": 60,
        "weight": {"primary": 0, "dr": 100}
      },
      "timeout_seconds": 60,
      "critical": true
    },
    {
      "step_order": 3,
      "name": "Promote DR database to primary",
      "action_type": "api_call",
      "action_config": {
        "endpoint": "/api/v2/database/promote",
        "method": "POST",
        "body": {"cluster_id": "db-dr-eu-west-1"}
      },
      "timeout_seconds": 300,
      "critical": true
    },
    {
      "step_order": 4,
      "name": "Scale up DR compute",
      "action_type": "api_call",
      "action_config": {
        "endpoint": "/api/v2/compute/scale-up",
        "method": "POST",
        "body": {"group": "dr-app-group", "count": 6}
      },
      "timeout_seconds": 180,
      "critical": false
    },
    {
      "step_order": 5,
      "name": "Validate application health on DR",
      "action_type": "script",
      "action_config": {
        "script": "dr-health-check.sh",
        "params": {"url": "https://dr.app.example.com/health"}
      },
      "timeout_seconds": 120,
      "critical": true
    }
  ]
}
```

### drill result (get /api/v2/dr/drills/:did)

```json
{
  "id": "drill-2026-q2-001",
  "plan_id": "plan-001",
  "status": "completed_success",
  "started_at": "2026-03-15T02:00:00Z",
  "completed_at": "2026-03-15T02:12:34Z",
  "measured_rto_seconds": 754,
  "measured_rpo_seconds": 42,
  "rto_met": true,
  "rpo_met": true,
  "results": {
    "steps": [
      {"step": 1, "status": "passed", "duration_ms": 3400},
      {"step": 2, "status": "passed", "duration_ms": 5200},
      {"step": 3, "status": "passed", "duration_ms": 124500},
      {"step": 4, "status": "passed", "duration_ms": 45000},
      {"step": 5, "status": "passed", "duration_ms": 2400}
    ],
    "total_duration_ms": 754000,
    "max_data_lag_seconds": 42,
    "rollback_status": "not_required"
  }
}
```

## 8. service assignments

| service | responsibilities |
|---------|------------------|
| **orchestrator agent** | dr plan engine, drill orchestration, rto/rpo measurement, compliance report generation |
| **integration service** | provider-specific replication setup (db, storage, dns) |
| **panel** | dr plan designer, drill console, rto/rpo dashboard, compliance reports |
| **database** | `dr_plans`, `dr_plan_steps`, `dr_replication_configs`, `dr_drills`, `dr_audit_log` |
| **scheduler** | scheduled drills, periodic sync operations, compliance report generation |
| **notification service** | drill start/completion/failure alerts |

## 9. effort breakdown

| task | pt | dependencies |
|------|----|-------------|
| data model + crud for dr plans, steps, replication | 0.5 | -- |
| topology validator | 0.5 | data model |
| dr plan designer ui | 1.0 | crud apis |
| replication configurator (db, storage, dns) | 1.5 | -- |
| replication monitoring + lag alerts | 0.5 | replication config |
| failover executor | 1.5 | step model |
| failback executor | 1.0 | failover executor |
| snapshot manager + rollback | 0.5 | provider apis |
| drill console + real-time logs | 1.0 | drill engine |
| rto/rpo measurement engine | 1.0 | drill engine |
| compliance report generator | 0.5 | audit log |
| rto/rpo dashboard | 0.5 | measurement engine |
| documentation & tests | 0.5 | -- |

## 10. risks & mitigations

| risk | impact | mitigation |
|------|--------|------------|
| failover damages primary due to split-brain | data loss / corruption | implement health-check fencing; never promote dr if primary is reachable |
| replication lag exceeds rpo during a real disaster | data loss beyond acceptable threshold | hard rpo enforcement -- alert + auto-throttle source writes |
| dns propagation delay invalidates rto target | rto breach despite fast app startup | use low-ttl dns (60s), traffic manager / global load balancer |
| rollback fails after failed drill | stuck in partial failover state | each step has a rollback plan; always test rollback in drills |
