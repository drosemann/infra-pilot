# ai resource optimizer

feature id: 2
category: ai & intelligence
primary service: orchestrator agent
effort estimate: medium (4-6 pt)
status: planned

## overview

analyze historical cpu, ram, and disk usage trends per vps to generate actionable right-sizing recommendations. the optimizer detects idle and underutilized resources, estimates cost savings, and supports an approval workflow for automated downsizing with a configurable grace period before changes are applied.

### goals

- reduce infrastructure costs by identifying and right-sizing over-provisioned servers
- surface idle resources (zombie servers running without meaningful load)
- provide clear, data-driven recommendations with estimated monthly savings
- enable safe auto-apply with approval windows and rollback capability

## architecture

```
┌──────────────────────────────────────────────────────────┐
│                   Metrics Sources                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐│
│  │ Node     │  │ Docker   │  │ Cloud    │  │ Custom   ││
│  │ Exporter │  │ Stats    │  │ Provider │  │ Agent    ││
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘│
└───────┼──────────────┼────────────┼──────────────┼───────┘
        │              │            │              │
        ▼              ▼            ▼              ▼
┌──────────────────────────────────────────────────────────┐
│              Orchestrator Agent                           │
│                                                           │
│  ┌────────────────────────────────────────────────────┐  │
│  │          Metrics Collection & Aggregation           │  │
│  │  ┌─────────┐  ┌──────────┐  ┌──────────────────┐  │  │
│  │  │ Scrape  │──│  Window  │──│  Aggregation      │  │  │
│  │  │ Engine  │  │  Buffer  │  │  (avg, p95, max)  │  │  │
│  │  └─────────┘  └──────────┘  └────────┬─────────┘  │  │
│  └────────────────────────────────────────────────────┘  │
│                        │                                 │
│                        ▼                                 │
│  ┌────────────────────────────────────────────────────┐  │
│  │          Trend Analysis Engine                      │  │
│  │  ┌──────────────┐  ┌────────────┐  ┌────────────┐ │  │
│  │  │ Linear       │  │ Seasonal   │  │ Changepoint│ │  │
│  │  │ Regression   │  │ Decompose  │  │ Detection  │ │  │
│  │  └──────┬───────┘  └─────┬──────┘  └──────┬─────┘ │  │
│  │         │                │                │        │  │
│  │         ▼                ▼                ▼        │  │
│  │  ┌────────────────────────────────────────────┐    │  │
│  │  │   Recommendation Engine                     │    │  │
│  │  │   Suggests: downsize, upsize, idle, right   │    │  │
│  │  └──────────────────┬─────────────────────────┘    │  │
│  └─────────────────────┼──────────────────────────────┘  │
│                        │                                 │
│                        ▼                                 │
│  ┌────────────────────────────────────────────────────┐  │
│  │          Approval & Auto-Apply                      │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │  │
│  │  │ Approval │──│ Grace    │──│ Apply + Rollback  │ │  │
│  │  │ Workflow │  │ Window   │  │                  │ │  │
│  │  └──────────┘  └──────────┘  └──────────────────┘ │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────┐
│              Management Panel                             │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Recommendation Dashboard                           │  │
│  │  Savings Calculator                                │  │
│  │  One-Click Approve / Dismiss / Schedule            │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

## implementation plan

### phase 1: metrics collection & trend analysis (2 pt)

| step | description | artifacts |
|------|-------------|-----------|
| 1.1 | deploy node-level metric exporters | node exporter + cadvisor for docker hosts |
| 1.2 | implement scrape engine with configurable interval | prometheus-style scrape config, 30s default |
| 1.3 | rolling window aggregation (1h, 24h, 7d, 30d) | timescaledb continuous aggregates |
| 1.4 | trend analysis service | linear regression slope, seasonal decomposition |

**scrape configuration:**

```yaml
# config/metrics_scrape.yaml
scrape:
  interval_seconds: 30
  timeout_seconds: 10
  targets:
    - type: node_exporter
      port: 9100
      metrics:
        - node_cpu_seconds_total
        - node_memory_MemTotal_bytes
        - node_memory_MemAvailable_bytes
        - node_disk_io_time_seconds_total
        - node_network_receive_bytes_total
    - type: cadvisor
      port: 8080
      metrics:
        - container_cpu_usage_seconds_total
        - container_memory_working_set_bytes
        - container_fs_usage_bytes

aggregation:
  windows:
    - duration: 1h
      retain_days: 30
    - duration: 24h
      retain_days: 90
    - duration: 7d
      retain_days: 365
```

### phase 2: recommendation engine (1.5 pt)

| step | description | artifacts |
|------|-------------|-----------|
| 2.1 | resource profiling algorithm | profile per server: `{p50, p95, max, trend}` |
| 2.2 | right-sizing recommendation logic | target plan calculation based on headroom policy |
| 2.3 | idle resource detection heuristic | no significant traffic for 14d + low cpu/ram |
| 2.4 | cost savings estimator | price book lookup from current vs. recommended plan |
| 2.5 | recommendation persistence | `recommendations` table in postgresql |

**recommendation logic (pseudocode):**

```python
def generate_recommendation(server_id, metrics, plans):
    cpu_p95 = metrics.cpu.p95_over_7d
    ram_p95 = metrics.ram.p95_over_7d
    disk_p95 = metrics.disk.p95_over_7d

    # Classify current utilization
    if cpu_p95 < 10 and ram_p95 < 10 and metrics.traffic_avg_14d < MIN_TRAFFIC:
        return Recommendation(
            type="idle",
            action="stop_or_downsize",
            savings=plans.current.cost - plans.minimum.cost,
            confidence=0.95,
        )

    # Find cheapest plan that fits with headroom
    headroom_cpu = 1.5  # 50% headroom
    headroom_ram = 1.3
    required_cpu = cpu_p95 * headroom_cpu
    required_ram = ram_p95 * headroom_ram

    best_plan = min(
        (p for p in plans if p.cpu >= required_cpu and p.ram >= required_ram),
        key=lambda p: p.cost,
    )

    if best_plan.cpu < plans.current.cpu or best_plan.ram < plans.current.ram:
        # Trending up? Don't downsize.
        if metrics.cpu.trend_slope > 0.05:
            return Recommendation(type="monitor", action="no_change")

        return Recommendation(
            type="downsize",
            current_plan=plans.current,
            recommended_plan=best_plan,
            savings=plans.current.cost - best_plan.cost,
            confidence=calculate_confidence(metrics),
        )

    return Recommendation(type="optimal", action="no_change")
```

### phase 3: approval workflow & auto-apply (1.5 pt)

| step | description | artifacts |
|------|-------------|-----------|
| 3.1 | approval workflow state machine | `pending → approved → applying → applied / rolled_back` |
| 3.2 | grace period timer (configurable: 24h-72h) | scheduled job, cancellation support |
| 3.3 | plan change executor | cloud provider api call with pre/post health check |
| 3.4 | rollback procedure | snapshot before change, revert on failure |
| 3.5 | notification on each state transition | discord, slack, email, panel toast |

**approflow state machine:**

```
┌─────────┐     approve     ┌──────────┐   timer expires   ┌──────────┐
│ Pending │──────────────▶  │ Approved │─────────────────▶  │ Applying │
│         │                  │ [grace]  │                   │          │
└────┬────┘                  └──────────┘                   └────┬─────┘
     │                           │                              │
     │ dismiss                   │ cancel                       │ success / fail
     ▼                           ▼                              ▼
┌─────────┐               ┌──────────┐                  ┌──────────────┐
│Dismissed│               │ Cancelled│                  │ Applied /    │
└─────────┘               └──────────┘                  │ Rolled Back  │
                                                          └──────────────┘
```

## api design

### rest api

#### list recommendations

```
GET /api/v1/recommendations
  ?type=downsize,idle
  &server_id=srv-001
  &status=pending,approved,applied,dismissed
  &min_savings=10
  &limit=50
```

response:
```json
{
  "recommendations": [
    {
      "id": "rec-20260527-001",
      "server_id": "srv-001",
      "server_name": "web-01",
      "type": "downsize",
      "status": "pending",
      "current_plan": {
        "name": "dedicated-8",
        "cpu": 8,
        "ram_gb": 32,
        "disk_gb": 200,
        "monthly_cost": 80.00
      },
      "recommended_plan": {
        "name": "dedicated-4",
        "cpu": 4,
        "ram_gb": 16,
        "disk_gb": 100,
        "monthly_cost": 45.00
      },
      "savings_per_month": 35.00,
      "savings_percent": 43.75,
      "confidence": 0.88,
      "metrics_snapshot": {
        "cpu_p95_7d": 35.2,
        "ram_p95_7d": 8.1,
        "disk_p95_7d": 45.3,
        "cpu_trend": "stable",
        "ram_trend": "stable"
      },
      "created_at": "2026-05-27T00:00:00Z",
      "grace_period_ends": "2026-05-28T12:00:00Z"
    }
  ],
  "total": 12,
  "savings_total_per_month": 210.00
}
```

#### approve recommendation

```
POST /api/v1/recommendations/{id}/approve
```

request:
```json
{
  "approved_by": "admin@example.com",
  "schedule_immediately": false,
  "grace_period_hours": 48
}
```

#### dismiss recommendation

```
POST /api/v1/recommendations/{id}/dismiss
```

request:
```json
{
  "reason": "expected_traffic_increase",
  "dismissed_by": "admin@example.com"
}
```

#### get savings summary

```
GET /api/v1/recommendations/savings-summary
```

response:
```json
{
  "total_current_monthly": 4520.00,
  "total_optimized_monthly": 3850.00,
  "potential_savings": 670.00,
  "realized_savings": 320.00,
  "servers_analyzed": 48,
  "servers_with_recommendations": 12,
  "idle_servers": 3,
  "by_category": {
    "downsize": {
      "count": 7,
      "potential_savings": 450.00,
      "realized_savings": 200.00
    },
    "idle": {
      "count": 3,
      "potential_savings": 180.00,
      "realized_savings": 100.00
    },
    "upsize": {
      "count": 2,
      "potential_cost_increase": 40.00,
      "realized": 20.00
    }
  }
}
```

## data model

```python
# models/resource_optimizer.py
@dataclass
class ResourceMetrics:
    server_id: str
    timestamp: datetime
    cpu_percent: float
    ram_percent: float
    ram_used_bytes: int
    disk_percent: float
    disk_used_bytes: int
    network_rx_bytes: int
    network_tx_bytes: int
    load_avg_1m: float
    load_avg_5m: float

@dataclass
class AggregatedProfile:
    server_id: str
    window: str  # 1h, 24h, 7d, 30d
    cpu: ProfileStats
    ram: ProfileStats
    disk: ProfileStats
    network_traffic_avg: float

@dataclass
class ProfileStats:
    p50: float
    p95: float
    p99: float
    max: float
    avg: float
    trend_slope: float  # positive = increasing, negative = decreasing
    trend_stability: float  # lower = more stable

@dataclass
class Recommendation:
    id: str
    server_id: str
    server_name: str
    type: str  # downsize / upsize / idle / optimal
    status: str  # pending / approved / applying / applied / dismissed / cancelled / rolled_back
    current_plan: Plan
    recommended_plan: Plan | None
    savings_per_month: float
    confidence: float
    metrics_snapshot: dict
    created_at: datetime
    approved_by: str | None
    approved_at: datetime | None
    grace_period_ends: datetime | None
    applied_at: datetime | None
    dismissed_reason: str | None
    rollback_initiated: bool
```

**database schema:**

```sql
-- Aggregated resource profiles
CREATE TABLE resource_profiles (
    server_id   TEXT NOT NULL,
    window      TEXT NOT NULL,          -- '1h', '24h', '7d', '30d'
    window_start TIMESTAMPTZ NOT NULL,
    cpu_p50     DOUBLE PRECISION,
    cpu_p95     DOUBLE PRECISION,
    cpu_max     DOUBLE PRECISION,
    cpu_trend_slope DOUBLE PRECISION,
    ram_p50     DOUBLE PRECISION,
    ram_p95     DOUBLE PRECISION,
    ram_max     DOUBLE PRECISION,
    ram_trend_slope DOUBLE PRECISION,
    disk_p50    DOUBLE PRECISION,
    disk_p95    DOUBLE PRECISION,
    disk_max    DOUBLE PRECISION,
    PRIMARY KEY (server_id, window, window_start)
);

-- Recommendations
CREATE TABLE recommendations (
    id                  TEXT PRIMARY KEY,
    server_id           TEXT NOT NULL,
    server_name         TEXT NOT NULL,
    type                TEXT NOT NULL,
    status              TEXT NOT NULL DEFAULT 'pending',
    current_plan        JSONB NOT NULL,
    recommended_plan    JSONB,
    savings_per_month   DOUBLE PRECISION DEFAULT 0,
    confidence          DOUBLE PRECISION,
    metrics_snapshot    JSONB,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    approved_by         TEXT,
    approved_at         TIMESTAMPTZ,
    grace_period_ends   TIMESTAMPTZ,
    applied_at          TIMESTAMPTZ,
    dismissed_reason    TEXT,
    rollback_initiated  BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_rec_server ON recommendations(server_id);
CREATE INDEX idx_rec_status ON recommendations(status);
CREATE INDEX idx_rec_type ON recommendations(type);
```

## service assignments

| service | responsibility |
|---------|---------------|
| orchestrator agent | metrics scrape engine, aggregation, trend analysis, recommendation engine, approval workflow, plan change executor |
| integration service | cloud provider price book api, notification dispatch (discord/slack) |
| management panel | recommendation dashboard, savings calculator, approve/dismiss ui, history view |

## configuration reference

```yaml
# config/resource_optimizer.yaml
analysis:
  schedule: "0 */6 * * *"    # every 6 hours
  windows:
    short: 1h
    medium: 24h
    long: 7d
    trend: 30d
  idle_detection:
    cpu_threshold_percent: 5
    ram_threshold_percent: 5
    traffic_threshold_bytes: 1048576  # 1 MB/day
    idle_days: 14

recommendations:
  headroom:
    cpu_factor: 1.5
    ram_factor: 1.3
    disk_factor: 1.2
  min_confidence: 0.6
  min_savings_usd: 5.00

auto_apply:
  enabled: false                   # opt-in per environment
  default_grace_hours: 48
  max_grace_hours: 168            # 7 days
  require_approval: true
  rollback_on_failure: true
  pre_check_health: true
  health_check_timeout_seconds: 120

notifications:
  on_recommendation: true
  on_approval_needed: true
  on_applied: true
  on_rollback: true
  channels: ["panel", "discord"]
```

## effort breakdown

| phase | task | pt | dependencies |
|-------|------|----|-------------|
| 1.1 | metric exporter deployment | 0.5 | node access |
| 1.2 | scrape engine | 0.5 | metrics pipeline |
| 1.3 | window aggregation | 0.5 | time-series storage |
| 1.4 | trend analysis | 0.5 | aggregation data |
| 2.1 | resource profiling | 0.5 | trend analysis |
| 2.2 | right-sizing logic | 0.5 | plan catalog |
| 2.3 | idle detection | 0.25 | profiling output |
| 2.4 | savings estimator | 0.25 | price book |
| 2.5 | persistence layer | 0.25 | db schema |
| 3.1 | approval state machine | 0.5 | workflow engine |
| 3.2 | grace period timer | 0.25 | scheduled jobs |
| 3.3 | plan change executor | 0.5 | cloud api |
| 3.4 | rollback procedure | 0.25 | snapshot infra |
| 3.5 | notifications | 0.25 | notifier service |
| | total | 5.75 | |

## risks & mitigations

| risk | impact | mitigation |
|------|--------|------------|
| downsize during traffic spike | performance degradation | trend analysis prevents downsizing on upward trends; health check pre/post apply |
| idle server is actually standby | service disruption | allow exclusion tags (`infrapilot/optimizer=exclude`), require approval for idle actions |
| price book out of date | incorrect savings estimates | sync price book daily from cloud provider apis |
| insufficient metrics history | cold start, no recommendations | collect 7 days of metrics before generating first recommendation |

## metrics & kpis

| metric | target | measurement |
|--------|--------|-------------|
| cost savings realized | > 15% of total compute spend | monthly savings / total monthly cost |
| recommendation accuracy | > 90% no regression after apply | compare post-apply performance to pre-apply |
| time to apply (auto) | < 5 minutes | from grace expiry to plan change complete |
| user adoption | > 60% of servers with recommendations reviewed | reviewed count / total recommendations |
