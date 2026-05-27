# feature 39: alert fatigue reduction

- feature id: 39
- category: advanced observability
- primary service: integration service
- effort: large (7-10 pt)
- dependencies: feature 13 (webhook event bus), feature 30 (incident management), feature 36 (slo tracking)

## overview

implement an intelligent alert management system that dramatically reduces alert fatigue for operators. the system provides real-time deduplication (collapsing identical alerts into single notifications), correlation (grouping related alerts from different sources into a single incident), maintenance window suppression (silencing alerts for planned operations), auto-escalation (escalating unacknowledged alerts through configurable policies), notification throttling (rate-limiting per channel/severity), and digest mode (periodic summary instead of per-alert notifications).

### goals

- reduce total alert volume by 60-80% through deduplication and correlation
- eliminate notification storms from cascading failures via correlation groups
- support scheduled and ad-hoc maintenance windows with automatic alert suppression
- route alerts through escalation policies with time-based and acknowledgement-based triggers
- throttle notifications per severity/channel to prevent channel flooding
- provide periodic digest summaries for non-urgent alert categories

## architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                        Alert Sources                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │Infra     │  │Synthetic │  │SLO/Budget│  │Prometheus│    ... (N)   │
│  │Metrics   │  │Monitor   │  │Alerts    │  │Alert     │              │
│  └─────┬────┘  └─────┬────┘  └─────┬────┘  └─────┬────┘              │
└────────┼──────────────┼──────────────┼──────────────┼────────────────┘
         │              │              │              │
┌────────▼──────────────▼──────────────▼──────────────▼────────────────┐
│                          Integration Service                           │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                         Alert Pipeline                            │  │
│  │                                                                  │  │
│  │  ┌─────────────┐   ┌──────────────┐   ┌──────────────────────┐  │  │
│  │  │ Ingest      │──▶│ Deduplication │──▶│ Correlation Engine   │  │  │
│  │  │ (validate,  │   │ (hash, time,  │   │ (topology, time,    │  │  │
│  │  │ normalize)  │   │  fingerprint) │   │  metric similarity)  │  │  │
│  │  └─────────────┘   └──────────────┘   └───────────┬──────────┘  │  │
│  │                                                    │              │  │
│  │  ┌─────────────────────────────────────────────────▼──────────┐  │  │
│  │  │                  Routing & Policy Engine                    │  │  │
│  │  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐   │  │  │
│  │  │  │ Maintenance   │ │ Escalation   │ │ Notification    │   │  │  │
│  │  │  │ Window Check  │ │ Policy Eval  │ │ Throttle        │   │  │  │
│  │  │  └──────────────┘ └──────────────┘ └──────────────────┘   │  │  │
│  │  └────────────────────────────────┬───────────────────────────┘  │  │
│  │                                   │                               │  │
│  │  ┌────────────────────────────────▼───────────────────────────┐  │  │
│  │  │                    Output Formatter                         │  │  │
│  │  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐   │  │  │
│  │  │  │ Real-Time    │ │ Digest Mode  │ │ Webhook/Api     │   │  │  │
│  │  │  │ Notification │ │ (periodic    │ │ Payload Builder  │   │  │  │
│  │  │  │ Builder      │ │  summary)    │ │                  │   │  │  │
│  │  │  └──────────────┘ └──────────────┘ └──────────────────┘   │  │  │
│  │  └────────────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│                         Notification Channels                            │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────────┐   │
│  │ Discord    │  │ Email      │  │ Webhook    │  │ SMS/PagerDuty  │   │
│  │ (embed)    │  │ (HTML)     │  │ (JSON POST)│  │ (API)          │   │
│  └────────────┘  └────────────┘  └────────────┘  └────────────────┘   │
└────────────────────────────────────────────────────────────────────────┘
```

### alert lifecycle state machine

```
                    ┌──────────┐
                    │  New     │
                    └────┬─────┘
                         │
                    ┌────▼─────┐
              ┌─────│  Open    │──────┐
              │     └────┬─────┘      │
              │          │            │
         ┌────▼───┐  ┌──▼─────┐  ┌───▼────┐
         │Suppress│  │Acknowled│  │Escalate│
         │(maint.)│  │-ged    │  │-ed     │
         └───┬────┘  └──┬─────┘  └───┬────┘
             │          │            │
         ┌───▼──────────▼────────────▼────┐
         │           Resolved              │
         └─────────────────────────────────┘
```

### correlation strategies

| strategy | method | example |
|---|---|---|
| topology-based | resources related via dependency graph | server down → dependent services alert grouped |
| time-window | alerts within n minutes of same resource | cpu + memory + disk alerts at same time |
| metric similarity | anomalies in related metrics | response time spike + error rate increase |
| cause-effect | root cause inferred from temporal order | host down (cause) → service unreachable (effect) |
| label match | same label dimensions | all alerts with `team: platform, env: prod` |

## data model

### alert event (ingested)

```yaml
alert_event:
  id: "aev-f8a2c9d1"
  source: "prometheus"
  source_id: "ALERT-1745712345"
  fingerprint: "a1b2c3d4e5f6"         # Deterministic hash for dedup
  received_at: 1745712345
  normalized:
    title: "High CPU Usage on web-prod-01"
    description: "CPU usage at 94% for >5 minutes"
    severity: "warning"                # info | warning | critical
    resource_id: "srv-web-prod-01"
    resource_type: "server"
    metric_name: "cpu_usage_percent"
    metric_value: 94.2
    labels:
      team: "platform"
      environment: "production"
      service: "web"
    source_url: "https://prometheus.example.com/alert/cpu-high"
  raw_payload: {}                      # Original source payload
```

### deduplication record

```yaml
dedup_record:
  id: "ddr-abc123"
  fingerprint: "a1b2c3d4e5f6"
  first_seen_at: 1745712345
  last_seen_at: 1745712645
  occurrence_count: 12
  first_alert_id: "aev-f8a2c9d1"
  last_alert_id: "aev-9k2m4n7p"
  status: "grouping"                  # grouping | grouped | resolved
  notification_sent: true
  last_notification_at: 1745712345
  throttle_until: 1745712545          # Next allowed notification time
```

### correlation group (incident)

```yaml
correlation_group:
  id: "cg-infra-20260512-001"
  title: "Production Web Cluster Degradation"
  description: "Multiple alerts indicate web cluster health issue"
  created_at: 1745712360
  updated_at: 1745712660
  status: "open"                      # open | acknowledged | escalating | resolved
  severity: "critical"
  alert_ids:
    - "aev-f8a2c9d1"                  # High CPU
    - "aev-f8a2c9d2"                  # High Memory
    - "aev-f8a2c9d3"                  # 5xx Error Rate Spike
  primary_alert: "aev-f8a2c9d1"
  root_cause_alert: "aev-f8a2c9d1"    # Updated after analysis
  correlation_strategy: "topology"
  resources_affected:
    - "srv-web-prod-01"
    - "srv-web-prod-02"
  services_affected:
    - "web-api"
    - "web-frontend"
  timeline:
    - timestamp: 1745712345
      event: "alert_received"
      detail: "High CPU on web-prod-01"
    - timestamp: 1745712360
      event: "group_created"
      detail: "Correlated 3 related alerts"
    - timestamp: 1745712400
      event: "notification_sent"
      detail: "Discord notification sent"
    - timestamp: 1745712600
      event: "acknowledged"
      detail: "Acknowledged by user@example.com"
```

### maintenance window

```yaml
maintenance_window:
  id: "mw-deploy-20260512"
  title: "Production Web Deploy Window"
  description: "Scheduled deployment of web v2.4.1"
  created_by: "user@example.com"
  starts_at: 1745712000
  ends_at: 1745719200                  # 2 hour window
  timezone: "UTC"
  scope:
    type: "label_selector"
    selectors:
      - "team=platform"
      - "environment=production"
      - "service=web"
    resources:
      - "srv-web-prod-01"
      - "srv-web-prod-02"
  suppression_rules:
    severities: ["info", "warning"]   # critical still fires
    alert_types: ["cpu", "memory", "response_time"]
    alert_sources: ["prometheus"]
  status: "active"                    # scheduled | active | completed | cancelled
  notification:
    notify_on_start: true
    notify_on_end: true
    channels: ["discord"]
```

### escalation policy

```yaml
escalation_policy:
  id: "ep-platform-critical"
  name: "Platform Critical Escalation"
  description: "Escalation for critical platform alerts"
  applies_to:
    severities: ["critical"]
    labels:
      team: "platform"
  steps:
    - level: 1
      name: "Primary On-Call"
      notify:
        - type: "schedule"
          schedule_id: "schedule-platform-primary"
      timeout_minutes: 15
      repeat_count: 2
      channels: ["discord", "pagerduty"]
    - level: 2
      name: "Secondary On-Call"
      notify:
        - type: "schedule"
          schedule_id: "schedule-platform-secondary"
      timeout_minutes: 10
      channels: ["discord", "sms"]
    - level: 3
      name: "Engineering Manager"
      notify:
        - type: "user"
          user_id: "user-mgr-001"
      timeout_minutes: 5
      channels: ["sms", "phone"]
    - level: 4
      name: "VP Engineering"
      notify:
        - type: "user"
          user_id: "user-vp-001"
      channels: ["phone"]
  acknowledgement_resets: true        # Ack at level 1 stops escalation
```

### digest configuration

```yaml
digest_config:
  id: "digest-daily-platform"
  name: "Daily Platform Digest"
  schedule: "0 9 * * *"               # Daily at 09:00 UTC
  timezone: "UTC"
  scope:
    severity: ["info", "warning"]
    labels:
      team: "platform"
  format: "discord_embed"
  max_alerts: 25
  include_previous_resolved: false
  channels: ["discord-digest"]
```

## api design

### alerts

#### ingest alert

```
POST /api/v2/alerts/ingest
```

```json
{
  "source": "prometheus",
  "source_id": "ALERT-1745712345",
  "title": "High CPU Usage on web-prod-01",
  "description": "CPU usage at 94% for >5 minutes",
  "severity": "warning",
  "resource_id": "srv-web-prod-01",
  "resource_type": "server",
  "metric_name": "cpu_usage_percent",
  "metric_value": 94.2,
  "labels": {
    "team": "platform",
    "environment": "production",
    "service": "web"
  },
  "raw_payload": {}
}
```

response `200`:
```json
{
  "alert_id": "aev-f8a2c9d1",
  "fingerprint": "a1b2c3d4e5f6",
  "dedup_status": "grouping",
  "occurrence_count": 12,
  "correlation_group_id": "cg-infra-20260512-001",
  "will_notify": false,
  "reason": "Throttled: last notification 40s ago"
}
```

#### get alert details

```
GET /api/v2/alerts/{alert_id}
```

#### list alerts

```
GET /api/v2/alerts
  ?status=open
  &severity=critical
  &resource_id=srv-web-prod-01
  &from=2026-05-01T00:00:00Z
  &to=2026-05-31T23:59:59Z
  &page=1
  &per_page=50
```

#### acknowledge alert

```
POST /api/v2/alerts/{alert_id}/acknowledge
```

```json
{
  "user_id": "user@example.com",
  "note": "Investigating CPU spike"
}
```

#### resolve alert

```
POST /api/v2/alerts/{alert_id}/resolve
```

```json
{
  "user_id": "user@example.com",
  "resolution": "Auto-scaling added new instance, CPU normalized",
  "root_cause": "Traffic spike from marketing campaign"
}
```

### correlation groups

#### list groups

```
GET /api/v2/alerts/groups
  ?status=open
  &severity=critical
  &page=1
  &per_page=20
```

#### get group details

```
GET /api/v2/alerts/groups/{group_id}
```

### maintenance windows

#### list windows

```
GET /api/v2/maintenance-windows
  ?status=active
  &upcoming=true
```

#### create window

```
POST /api/v2/maintenance-windows
```

```json
{
  "title": "Production Web Deploy Window",
  "description": "Scheduled deployment of web v2.4.1",
  "starts_at": "2026-05-12T22:00:00Z",
  "ends_at": "2026-05-13T00:00:00Z",
  "scope": {
    "type": "label_selector",
    "selectors": [
      "team=platform",
      "environment=production"
    ]
  },
  "suppression_rules": {
    "severities": ["info", "warning"],
    "alert_types": ["cpu", "memory"]
  },
  "notification": {
    "notify_on_start": true,
    "notify_on_end": true,
    "channels": ["discord"]
  }
}
```

### escalation policies

#### list policies

```
GET /api/v2/escalation-policies
```

#### create policy

```
POST /api/v2/escalation-policies
```

```json
{
  "name": "Platform Critical Escalation",
  "applies_to": {
    "severities": ["critical"],
    "labels": {
      "team": "platform"
    }
  },
  "steps": [
    {
      "level": 1,
      "name": "Primary On-Call",
      "notify": [
        { "type": "schedule", "schedule_id": "schedule-platform-primary" }
      ],
      "timeout_minutes": 15,
      "channels": ["discord", "pagerduty"]
    },
    {
      "level": 2,
      "name": "Secondary On-Call",
      "notify": [
        { "type": "schedule", "schedule_id": "schedule-platform-secondary" }
      ],
      "timeout_minutes": 10,
      "channels": ["discord", "sms"]
    }
  ],
  "acknowledgement_resets": true
}
```

### digests

#### list digests

```
GET /api/v2/alerts/digests
```

#### create digest config

```
POST /api/v2/alerts/digests
```

```json
{
  "name": "Daily Platform Digest",
  "schedule": "0 9 * * *",
  "timezone": "UTC",
  "scope": {
    "severity": ["info", "warning"],
    "labels": { "team": "platform" }
  },
  "format": "discord_embed",
  "max_alerts": 25,
  "channels": ["discord-digest"]
}
```

### statistics

#### get alert reduction stats

```
GET /api/v2/alerts/stats
  ?window=7d
```

```json
{
  "window_days": 7,
  "raw_alerts_ingested": 14823,
  "after_dedup": 2452,
  "after_correlation": 412,
  "suppressed_by_maintenance": 893,
  "notifications_sent": 412,
  "dedup_ratio": 83.5,
  "correlation_ratio": 97.2,
  "overall_reduction_percent": 97.2,
  "by_severity": {
    "critical": { "ingested": 234, "sent": 42, "reduction": 82.1 },
    "warning": { "ingested": 2890, "sent": 145, "reduction": 95.0 },
    "info": { "ingested": 11699, "sent": 225, "reduction": 98.1 }
  }
}
```

## implementation plan

### phase 1: deduplication & ingestion pipeline (pt 1-3)

| step | description | artifacts |
|---|---|---|
| 1.1 | alert normalization layer: validate, normalize, fingerprint | `services/alert_normalizer.py` |
| 1.2 | deduplication engine: hash-based, time-window, state tracking | `services/dedup_engine.py` |
| 1.3 | alert ingest api endpoint with dedup response | `routes/alerts.py` |
| 1.4 | persistent storage for dedup state, alert events | `models/alert.py`, `models/dedup.py` |

### phase 2: correlation & escalation engine (pt 4-6)

| step | description | artifacts |
|---|---|---|
| 2.1 | correlation engine: topology, time-window, label matching | `services/correlation_engine.py` |
| 2.2 | correlation group lifecycle management | `services/group_manager.py` |
| 2.3 | escalation policy engine with timer-based step progression | `services/escalation_engine.py` |
| 2.4 | escalation policy crud + schedule/on-call integration | `routes/escalation.py`, `models/escalation.py` |

### phase 3: suppression, throttling, digest & panel (pt 7-10)

| step | description | artifacts |
|---|---|---|
| 3.1 | maintenance window crud + automatic alert suppression | `services/maintenance_window.py`, `routes/maintenance.py` |
| 3.2 | notification throttle: per-channel, per-severity rate limit | `services/throttle_engine.py` |
| 3.3 | digest mode: cron-based summary generation, formatting | `services/digest_engine.py` |
| 3.4 | panel ui: alert list, correlation group view, timeline | panel components |
| 3.5 | panel ui: maintenance window scheduler, escalation policy editor | panel components |
| 3.6 | panel ui: digest config, reduction statistics dashboard | panel components |

## service assignments

| service | responsibility |
|---|---|
| integration service (primary) | alert ingestion, deduplication, correlation engine, escalation engine, maintenance windows, notification throttling, digest mode, rest api |
| management panel | alert dashboard, correlation group timeline, maintenance window scheduler, escalation policy editor, digest config, reduction stats |
| discord service | alert notification delivery (embed format), digest delivery, escalation channel messages |
| orchestrator agent | provide topology/relationship data for correlation engine, trigger maintenance windows from deployment workflows |
| incident management (f30) | receive resolved correlation groups as incidents, integrate escalation policies |

## effort estimate: large (7-10 pt)

| area | pt estimate |
|---|---|
| alert ingestion + normalization pipeline | 1.0 |
| deduplication engine (fingerprinting, state) | 1.5 |
| correlation engine (topology, time, label) | 2.0 |
| escalation policy engine (timer, steps, schedules) | 1.5 |
| maintenance window suppression | 1.0 |
| notification throttling | 0.5 |
| digest mode (scheduling, formatting) | 1.0 |
| rest api endpoints | 1.0 |
| panel ui (alert list, groups, maintenance, escalation, stats) | 2.0 |
| integration + e2e tests | 1.0 |
| documentation | 0.5 |
| total | **13.0 pt (rounded to 10 with framework reuse)** |

### risk factors

- correlation accuracy depends on resource topology graph completeness; initial correlations may be noisy
- escalation policy timing requires robust scheduler (consider celery/apscheduler)
- digest mode formatting varies significantly by channel (discord embed vs html email)
- alert dedup fingerprint collisions require careful hash design
- throttling logic must balance between reducing noise and not silencing real issues

## key metrics

| metric | target |
|---|---|
| alert volume reduction | > 95% (raw alerts → notifications sent) |
| deduplication latency | < 500ms per alert |
| correlation latency | < 5s from alert ingest to group assignment |
| escalation step accuracy | 100% (no missed steps) |
| maintenance window suppression | 100% of scope-matched alerts during window |
| digest delivery | within 5 minutes of scheduled time |
| api throughput | 200 req/s for alert ingestion |
