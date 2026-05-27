# feature 20: multi-region failover

- plan id: #20
- category: advanced infrastructure
- primary service: integration service
- effort: large (7-10 pt)
- dependencies: feature 13 (webhook event bus), feature 25 (disaster recovery orchestrator)

## overview

active-passive multi-region failover for services managed by infra pilot. health-based dns failover automatically redirects traffic from a degraded primary region to a healthy standby region. includes data replication lag monitoring, automatic traffic switching, and scheduled cutover testing.

### key capabilities

| capability | description |
|---|---|
| region health monitoring | multi-probe health checks across regions, composite health scores |
| dns failover | route53 (aws) and cloudflare dns failover policies |
| data replication monitoring | track replication lag, sync status, consistency checks |
| automatic traffic switch | configurable thresholds trigger region switch with rollback |
| cutover testing | scheduled drills with automated validation, report generation |
| traffic draining | graceful connection draining before region switch |

## architecture

### system context

```
                         ┌─────────────────┐
                         │  Global DNS      │
                         │  (Route53 / CF)  │
                         └────────┬─────────┘
                                  │
                 ┌────────────────┼────────────────┐
                 │                │                 │
         ┌───────▼───────┐       │        ┌───────▼───────┐
         │  Region A     │       │        │  Region B     │
         │  (Primary)    │       │        │  (Standby)    │
         │               │       │        │               │
         │  ┌─────────┐  │       │        │  ┌─────────┐  │
         │  │Services │  │       │        │  │Services │  │
         │  └─────────┘  │       │        │  └─────────┘  │
         │  ┌─────────┐  │       │        │  ┌─────────┐  │
         │  │DB       │◄─┼───────┼────────┼──│ DB      │  │
         │  │(Primary)│  │  Async│        │  │(Replica)│  │
         │  └─────────┘  │  Repl │        │  └─────────┘  │
         └───────┬───────┘       │        └───────┬───────┘
                 │               │                │
                 └───────┬───────┘                │
                         │                        │
                  ┌──────▼────────────────────────▼──────┐
                  │     Failover Controller               │
                  │       (Infr Pilot)                    │
                  │                                       │
                  │  ┌─────────────┐   ┌──────────────┐  │
                  │  │ Health       │   │ DNS Manager   │  │
                  │  │ Monitor      │   │ (Route53/CF)  │  │
                  │  └──────┬──────┘   └──────┬────────┘  │
                  │         │                 │            │
                  │  ┌──────▼──────┐   ┌──────▼────────┐  │
                  │  │ Replication │   │ Traffic       │  │
                  │  │ Lag Tracker │   │ Switch Engine │  │
                  │  └─────────────┘   └───────────────┘  │
                  │  ┌─────────────────────────────────┐  │
                  │  │ Cutover Test Scheduler           │  │
                  │  └─────────────────────────────────┘  │
                  └───────────────────────────────────────┘
```

### interaction flow

```
Normal Operation (Active-Passive)

    User Request
        │
        ▼
    DNS (Route53) ───────────▶ Region A (Primary)
                                   │
                                   ├── Serve traffic
                                   ├── DB writes (Primary)
                                   │
                                   └── Async replication ──▶ Region B (Standby)
                                                                │
                                                                ├── Ready to serve
                                                                └── DB reads (Replica)

Failover Trigger

    Health Monitor detects Region A degraded (score < threshold)
        │
        ▼
    Failover Controller:
        1. Verify Region B is healthy
        2. Check replication lag < max allowed
        3. Drain connections from Region A
        4. Promote Region B DB to Primary
        5. Update DNS records → Region B
        6. Send notifications (Slack, Discord, Panel)
        7. Create incident record

Automatic Rollback

    Region A recovers:
        1. Re-sync data from Region B
        2. Run consistency checks
        3. Manual approval (or auto if configured)
        4. Reverse DNS → Region A
        5. Region B back to Standby
```

## implementation plan

### phase 1: health monitoring (2 pt)

| task | description |
|---|---|
| 1.1 | multi-probe health check system (http, tcp, custom checks per region) |
| 1.2 | composite health scoring algorithm (weighted probes, degrading thresholds) |
| 1.3 | health check history store with trend analysis |
| 1.4 | alert integration -- trigger notification when score drops below threshold |

### phase 2: dns failover engine (2 pt)

| task | description |
|---|---|
| 2.1 | route53 failover routing policy manager (weighted, failover, latency) |
| 2.2 | cloudflare dns failover via api (load balancing pools, monitors) |
| 2.3 | ttl management -- automatic ttl reduction during failover events |
| 2.4 | multi-provider dns abstraction layer |

### phase 3: replication monitoring (2 pt)

| task | description |
|---|---|
| 3.1 | postgresql replication lag monitoring (wal position tracking) |
| 3.2 | mysql/mariadb replication lag monitoring (seconds_behind_master) |
| 3.3 | redis replication sync status monitoring |
| 3.4 | custom replication check api for arbitrary data stores |
| 3.5 | lag threshold alerting and pre-failover lag validation |

### phase 4: traffic switching & draining (1.5 pt)

| task | description |
|---|---|
| 4.1 | connection draining strategy per service type (lb, app, db) |
| 4.2 | automatic database promotion (replica → primary) |
| 4.3 | graceful traffic cutover with canary verification |
| 4.4 | rollback mechanism -- automated reversion on failure |

### phase 5: cutover testing (1.5 pt)

| task | description |
|---|---|
| 5.1 | scheduled failover drill executor |
| 5.2 | pre-flight checklists (dns propagation, db lag, service health) |
| 5.3 | automated test validation (end-to-end smoke tests after cutover) |
| 5.4 | drill report generation (rto/rpo metrics, pass/fail status) |

## api design

### endpoints

all endpoints are prefixed with `/api/v2/failover`.

#### region configuration

```
GET    /api/v2/failover/regions                    — List configured regions
POST   /api/v2/failover/regions                    — Add region
GET    /api/v2/failover/regions/{region_id}         — Get region details
PATCH  /api/v2/failover/regions/{region_id}         — Update region config
DELETE /api/v2/failover/regions/{region_id}         — Remove region
```

#### health

```
GET    /api/v2/failover/health                     — Current health scores all regions
GET    /api/v2/failover/health/{region_id}          — Health details for one region
GET    /api/v2/failover/health/history?region=X&window=24h  — Health history
```

#### failover

```
POST   /api/v2/failover/switch                     — Trigger failover to standby region
POST   /api/v2/failover/rollback                   — Rollback to original primary
GET    /api/v2/failover/status                     — Current failover state
GET    /api/v2/failover/history                    — Failover event history
```

#### replication

```
GET    /api/v2/failover/replication/{region_id}    — Replication status
GET    /api/v2/failover/replication/lag            — All regions lag metrics
```

#### cutover tests

```
GET    /api/v2/failover/drills                     — List cutover drills
POST   /api/v2/failover/drills                     — Schedule/start drill
GET    /api/v2/failover/drills/{drill_id}          — Drill results
```

### request/response examples

#### configure region

```json
POST /api/v2/failover/regions

{
  "name": "eu-west-1",
  "role": "primary",
  "dns_zone": "app.infra-pilot.io",
  "health_endpoints": [
    {
      "url": "https://app.infra-pilot.io/health",
      "type": "http",
      "interval_seconds": 15,
      "timeout_seconds": 5,
      "expected_status": 200
    },
    {
      "url": "https://api.infra-pilot.io/healthz",
      "type": "http",
      "interval_seconds": 10,
      "timeout_seconds": 3
    }
  ],
  "database": {
    "type": "postgresql",
    "host": "db.primary.infra-pilot.io",
    "replication_slot": "standby_region_b"
  },
  "dns_provider": {
    "type": "route53",
    "zone_id": "Z123456789",
    "record_name": "app.infra-pilot.io",
    "health_check_id": "hc-abc123"
  }
}
```

response:

```json
{
  "region_id": "reg-euw1",
  "name": "eu-west-1",
  "role": "primary",
  "status": "active",
  "health_score": 0.98,
  "created_at": "2026-05-27T10:30:00Z"
}
```

#### trigger failover

```json
POST /api/v2/failover/switch

{
  "target_region": "us-east-1",
  "reason": "manual",
  "drain_timeout_seconds": 120,
  "auto_rollback_minutes": 30,
  "skip_validation": false
}
```

response:

```json
{
  "failover_id": "fo-7f2a1b",
  "status": "in_progress",
  "stages": [
    { "name": "validation", "status": "completed", "duration_ms": 3200 },
    { "name": "draining", "status": "in_progress", "duration_ms": 15000 },
    { "name": "db_promotion", "status": "pending", "duration_ms": null },
    { "name": "dns_update", "status": "pending", "duration_ms": null },
    { "name": "verification", "status": "pending", "duration_ms": null }
  ],
  "estimated_completion": "2026-05-27T10:35:00Z"
}
```

## data model

### region

```sql
CREATE TABLE failover_regions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(128) NOT NULL UNIQUE,
    role            VARCHAR(10) NOT NULL CHECK (role IN ('primary', 'standby')),
    status          VARCHAR(20) NOT NULL DEFAULT 'active'
                    CHECK (status IN ('active', 'degraded', 'inactive', 'promoting')),
    dns_zone        VARCHAR(256) NOT NULL,
    dns_provider    JSONB NOT NULL,
    health_endpoints JSONB NOT NULL,
    database_config  JSONB NOT NULL DEFAULT '{}',
    health_score    DECIMAL(5,2) DEFAULT 1.00,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### health checks

```sql
CREATE TABLE failover_health_checks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    region_id       UUID NOT NULL REFERENCES failover_regions(id) ON DELETE CASCADE,
    endpoint_url    VARCHAR(512) NOT NULL,
    check_type      VARCHAR(20) NOT NULL CHECK (check_type IN ('http', 'tcp', 'custom')),
    status          VARCHAR(20) NOT NULL CHECK (status IN ('up', 'degraded', 'down')),
    response_time_ms INTEGER,
    http_status     INTEGER,
    error_message   TEXT,
    checked_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_health_checks_region_time
    ON failover_health_checks (region_id, checked_at DESC);
```

### replication lag

```sql
CREATE TABLE failover_replication_lag (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    region_id       UUID NOT NULL REFERENCES failover_regions(id) ON DELETE CASCADE,
    source_region   VARCHAR(128) NOT NULL,
    lag_bytes       BIGINT,
    lag_seconds     NUMERIC(10,2),
    wal_position    VARCHAR(64),
    status          VARCHAR(20) NOT NULL CHECK (status IN ('streaming', 'catchup', 'error')),
    checked_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### failover events

```sql
CREATE TABLE failover_events (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type            VARCHAR(20) NOT NULL
                    CHECK (type IN ('automatic', 'manual', 'drill', 'rollback')),
    status          VARCHAR(20) NOT NULL DEFAULT 'in_progress'
                    CHECK (status IN ('in_progress', 'completed', 'failed', 'rolled_back')),
    from_region     UUID NOT NULL REFERENCES failover_regions(id),
    to_region       UUID NOT NULL REFERENCES failover_regions(id),
    trigger_reason  TEXT,
    rto_seconds     INTEGER,
    rpo_seconds     INTEGER,
    stages          JSONB NOT NULL DEFAULT '[]',
    started_by      UUID REFERENCES users(id),
    started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMPTZ,
    rollback_event  UUID REFERENCES failover_events(id)
);
```

### cutover drills

```sql
CREATE TABLE failover_drills (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(256) NOT NULL,
    schedule        VARCHAR(64),  -- cron expression
    status          VARCHAR(20) NOT NULL DEFAULT 'scheduled'
                    CHECK (status IN ('scheduled', 'running', 'passed', 'failed')),
    config          JSONB NOT NULL DEFAULT '{}',
    last_run_at     TIMESTAMPTZ,
    last_result     JSONB,
    report          TEXT,
    created_by      UUID NOT NULL REFERENCES users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### state machine

```
                     ┌──────────┐
                     │  Active  │
                     │ (Primary)│
                     └────┬─────┘
                          │
              ┌───────────┼───────────┐
              │           │           │
              ▼           ▼           ▼
        ┌──────────┐ ┌────────┐ ┌──────────┐
        │Degraded  │ │Promoti-│ │Rollback  │
        │(Primary) │ │ng      │ │(to this) │
        └────┬─────┘ │(Standby│ └────┬─────┘
             │       │→Primary│      │
             │        └───┬────┘      │
             │            ▼           │
             │      ┌──────────┐      │
             └──────│  Active  │──────┘
                    │ (Standby)│
                    └──────────┘
```

## service assignments

| component | service | responsibilities |
|---|---|---|
| health monitor | **integration service** | multi-probe health checks, scoring, alerting |
| dns manager | **integration service** | route53/cloudflare api, failover routing policies |
| replication monitor | **integration service** | lag tracking, consistency checks |
| traffic switch engine | **integration service** | connection draining, db promotion, dns cutover |
| cutover test scheduler | **integration service** | drill scheduling, execution, report generation |
| failover ui | **management panel** | region config, health dashboards, failover controls |
| notifications | **integration service** | slack/discord/email alerts on failover events |
| dr integration | **orchestrator agent** (+ feature 25) | dr plan definition, cross-feature coordination |

## effort estimate

| phase | tasks | pt |
|---|---|---|
| phase 1: health monitoring | 1.1–1.4 | 2 |
| phase 2: dns failover engine | 2.1–2.4 | 2 |
| phase 3: replication monitoring | 3.1–3.5 | 2 |
| phase 4: traffic switching & draining | 4.1–4.4 | 1.5 |
| phase 5: cutover testing | 5.1–5.4 | 1.5 |
| **total** | **21 tasks** | **9 pt** |

### risk factors

| risk | mitigation |
|---|---|
| dns propagation delay undermines rto | use low ttl (60s) during normal ops, route53 health checks for near-instant failover |
| replication lag too high at failover time | pre-failover lag check with configurable max threshold; abort if exceeded |
| data inconsistency after split-brain | use strict active-passive model; automated fencing of old primary |
| cutover drill causes real disruption | drills run in isolated test region first; production drills during maintenance windows |
| multi-provider dns inconsistencies | abstract via unified dns provider interface with provider-specific adapters |

## monitoring & observability

### prometheus metrics

```python
# Health
failover_region_health_score{region}         # Gauge — 0.0 to 1.0 score
failover_health_check_status{region,endpoint} # Gauge — 1 (up) / 0 (down)
failover_health_check_duration_ms             # Histogram — probe response time

# Replication
failover_replication_lag_seconds{region}     # Gauge — current lag in seconds
failover_replication_lag_bytes{region}       # Gauge — current lag in bytes
failover_replication_status{region}          # Gauge — 1 streaming / 0 error

# Failover
failover_events_total{type,status}           # Counter — failover events
failover_rto_seconds                         # Histogram — actual RTO achieved
failover_rpo_seconds                         # Histogram — actual RPO achieved

# Drills
failover_drill_total{status}                 # Counter — drill outcomes
failover_drill_duration_seconds              # Histogram — drill duration
```

### logging

```json
{
  "event": "failover.started",
  "failover_id": "fo-7f2a1b",
  "from_region": "eu-west-1",
  "to_region": "us-east-1",
  "reason": "health_degradation_score_0.35",
  "trigger": "automatic"
}

{
  "event": "failover.completed",
  "failover_id": "fo-7f2a1b",
  "status": "completed",
  "rto_seconds": 85,
  "rpo_seconds": 12,
  "dns_propagation_ms": 42000
}

{
  "event": "replication.lag_alert",
  "region": "us-east-1",
  "lag_seconds": 120.5,
  "threshold": 30,
  "status": "critical"
}
```

## related documents

- [architecture overview](../architecture/overview.md)
- [feature 13: webhook event bus](13-webhook-event-bus.md)
- [feature 25: disaster recovery orchestrator](25-disaster-recovery-orchestrator.md)
- [feature 38: cost allocation & chargeback](38-cost-allocation-chargeback.md)
- [implementation plan v2](../feature-implementation-plan-v2.md)

**last updated:** may 2026
