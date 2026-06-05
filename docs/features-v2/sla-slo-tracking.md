# feature 36: sla / slo tracking

- feature id: 36
- category: advanced observability
- primary service: integration service
- effort: medium (4-6 pt)
- dependencies: feature 34 (distributed tracing), feature 17 (opentelemetry export)

## overview

define, measure, and report service level agreements (slas) and service level objectives (slos) for infrastructure resources. track uptime, response time, backup success rate, and other custom slis. compute error budgets in real time, fire burn rate alerts when budgets deplete faster than planned, and generate compliance reports for internal or external auditing.

### goals

- allow operators to define slos per server, service, or team workspace
- collect sli measurements from existing monitoring pipelines (prometheus, opentelemetry)
- compute real-time error budgets with configurable burn rate thresholds
- alert when error budget consumption exceeds safe limits
- generate monthly compliance reports (pdf/csv) for auditor review

## architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        External Consumers                       │
│  Management Panel  │  Discord Bot  │  API Clients  │  Webhooks  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                     Integration Service                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  SLO Definition  │  │  SLI Collector   │  │  Error Budget   │ │
│  │  Manager         │  │  Engine          │  │  Calculator     │ │
│  │  - CRUD SLOs     │  │  - Query SLIs    │  │  - Remaining %  │ │
│  │  - Target %      │  │  - Windows: 7/30 │  │  - Burn rate    │ │
│  │  - Windows       │  │  - Data source    │  │  - Forecast     │ │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬────────┘ │
│           │                     │                      │          │
│  ┌────────▼─────────────────────▼──────────────────────▼────────┐ │
│  │                     SLO Engine Core                          │ │
│  │  ┌─────────────┐ ┌──────────────┐ ┌──────────────────────┐  │ │
│  │  │ MultiWindow │ │ Burn Rate    │ │ Compliance Report    │  │ │
│  │  │ Evaluator   │ │ Detector     │ │ Generator            │  │ │
│  │  └─────────────┘ └──────────────┘ └──────────────────────┘  │ │
│  └──────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                     Data Sources                                  │
│  ┌──────────────┐  ┌──────────────────┐  ┌────────────────────┐ │
│  │ Prometheus    │  │ OpenTelemetry    │  │ Backup Service     │ │
│  │ (uptime, cpu) │  │ (latency, errors)│  │ (success rate)     │ │
│  └──────────────┘  └──────────────────┘  └────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

### component responsibilities

| component | service | role |
|---|---|---|
| slo definition manager | integration service | crud for slo targets, windows, alert thresholds |
| sli collector engine | integration service | pull metrics from data sources, compute sli ratios |
| error budget calculator | integration service | track remaining budget, burn rate, days to depletion |
| compliance report generator | integration service | monthly pdf/csv reports, audit trail |
| alert manager | integration service | route burn rate alerts to notification channels |

## data model

### slo definition

```yaml
slo:
  id: "slo-uptime-web-prod"
  name: "Web Production Uptime"
  description: "Uptime SLO for production web servers"
  target:
    value: 99.9
    unit: "%"
  window:
    type: "rolling"          # rolling | calendar_month
    duration_days: 30
  sli:
    source: "prometheus"
    query: "up{job='web-prod',env='production'}"
    type: "good_bad"         # good_bad | ratio | latency_bucket
    good_condition: "value == 1"
  error_budget:
    initial_ttd_days: 30
    burn_rate_alerts:
      - severity: "warning"
        threshold: 2.0       # 2x burn rate = warning
        window_minutes: 60
      - severity: "critical"
        threshold: 5.0       # 5x burn rate = critical
        window_minutes: 30
  labels:
    team: "platform"
    environment: "production"
    service: "web"
```

### sli measurement

```yaml
sli_measurement:
  id: "sli-1745712000-srv-001"
  slo_id: "slo-uptime-web-prod"
  timestamp: 1745712000
  window_start: 1745712000
  window_end: 1745798400
  total_events: 86400
  good_events: 86350
  bad_events: 50
  sli_value: 99.942
  source_query: "up{job='web-prod',env='production'}"
```

### error budget snapshot

```yaml
error_budget:
  slo_id: "slo-uptime-web-prod"
  snapshot_at: 1745712000
  total_budget_seconds: 2592000       # 30 days
  consumed_seconds: 43200              # 12 hours downtime
  remaining_seconds: 2548800
  remaining_percent: 98.33
  burn_rate_1h: 0.45                   # 1-hour burn rate
  burn_rate_24h: 0.62                  # 24-hour burn rate
  estimated_depletion_days: 85
  status: "healthy"                    # healthy | warning | critical | exhausted
```

### compliance report

```yaml
compliance_report:
  id: "cr-2026-05"
  period:
    start: "2026-05-01T00:00:00Z"
    end: "2026-05-31T23:59:59Z"
  generated_at: "2026-06-01T01:00:00Z"
  organization_id: "org-acme"
  slos:
    - slo_id: "slo-uptime-web-prod"
      target: 99.9
      achieved: 99.94
      status: "met"
      error_budget_remaining: 83.4
      outages:
        - date: "2026-05-12"
          duration_minutes: 14
          reason: "DNS propagation delay"
    - slo_id: "slo-response-api"
      target: 99.5
      achieved: 99.72
      status: "met"
      error_budget_remaining: 67.8
```

## api design

### slo definitions

#### list slos

```
GET /api/v2/slos
  ?status=active
  &team=platform
  &environment=production
  &page=1
  &per_page=50
```

response:
```json
{
  "slos": [
    {
      "id": "slo-uptime-web-prod",
      "name": "Web Production Uptime",
      "target": 99.9,
      "current_sli": 99.94,
      "error_budget_remaining": 83.4,
      "status": "healthy"
    }
  ],
  "total": 12,
  "page": 1
}
```

#### create slo

```
POST /api/v2/slos
```

```json
{
  "name": "Web Production Uptime",
  "description": "Uptime SLO for production web servers",
  "target": 99.9,
  "window_days": 30,
  "sli": {
    "source": "prometheus",
    "query": "up{job='web-prod',env='production'}",
    "type": "good_bad",
    "good_condition": "value == 1"
  },
  "error_budget": {
    "burn_rate_alerts": [
      { "severity": "warning", "threshold": 2.0, "window_minutes": 60 },
      { "severity": "critical", "threshold": 5.0, "window_minutes": 30 }
    ]
  },
  "labels": {
    "team": "platform",
    "environment": "production"
  }
}
```

response `201`:
```json
{
  "id": "slo-uptime-web-prod",
  "status": "active",
  "created_at": "2026-05-01T00:00:00Z"
}
```

#### get slo details

```
GET /api/v2/slos/{slo_id}
```

#### update slo

```
PATCH /api/v2/slos/{slo_id}
```

#### delete slo

```
DELETE /api/v2/slos/{slo_id}
```

### error budget

#### get error budget

```
GET /api/v2/slos/{slo_id}/error-budget
```

```json
{
  "slo_id": "slo-uptime-web-prod",
  "total_budget_seconds": 2592000,
  "consumed_seconds": 43200,
  "remaining_seconds": 2548800,
  "remaining_percent": 98.33,
  "burn_rate_1h": 0.45,
  "burn_rate_24h": 0.62,
  "estimated_depletion_days": 85,
  "status": "healthy"
}
```

#### get burn rate history

```
GET /api/v2/slos/{slo_id}/burn-rate
  ?window=7d
  &granularity=1h
```

### compliance reports

#### list reports

```
GET /api/v2/compliance-reports
  ?period=2026-05
  &format=json
```

#### generate report

```
POST /api/v2/compliance-reports/generate
```

```json
{
  "period": "2026-05",
  "format": "pdf",
  "include_details": true,
  "slos": ["slo-uptime-web-prod", "slo-response-api"]
}
```

response `202`:
```json
{
  "report_id": "cr-2026-05",
  "status": "generating",
  "estimated_seconds": 15
}
```

#### download report

```
GET /api/v2/compliance-reports/{report_id}/download
  ?format=pdf
```

### sli data

#### query sli raw data

```
GET /api/v2/slos/{slo_id}/sli-data
  ?start=2026-05-01T00:00:00Z
  &end=2026-05-31T23:59:59Z
  &granularity=1h
```

## implementation plan

### phase 1: core slo engine (pt 1-2)

| step | description | artifacts |
|---|---|---|
| 1.1 | slo crud endpoints and database schema | `models/slo.py`, `routes/slos.py` |
| 1.2 | sli collector: prometheus query adapter | `services/sli_collector.py` |
| 1.3 | error budget calculator with multi-window evaluation | `services/error_budget.py` |
| 1.4 | unit tests for budget math and burn rate detection | `tests/test_error_budget.py` |

### phase 2: alerting & reporting (pt 3-4)

| step | description | artifacts |
|---|---|---|
| 2.1 | burn rate alert evaluator + notification dispatch | `services/burn_rate_detector.py` |
| 2.2 | compliance report generation (pdf via weasyprint, csv) | `services/report_generator.py` |
| 2.3 | rest api endpoints for reports and sli queries | `routes/compliance.py` |
| 2.4 | integration tests with mock prometheus data | `tests/test_compliance.py` |

### phase 3: panel ui & polish (pt 5-6)

| step | description | artifacts |
|---|---|---|
| 3.1 | slo dashboard panel: list, detail, burn rate chart | panel components |
| 3.2 | slo creation/edit form with sli query builder | panel components |
| 3.3 | compliance report viewer/download page | panel components |
| 3.4 | websocket live updates for error budget changes | event stream |

## service assignments

| service | responsibility |
|---|---|
| integration service (primary) | slo crud, sli collection, error budget calculation, burn rate detection, compliance report generation, rest api |
| management panel | slo dashboard, creation forms, burn rate charts, report viewer/download |
| discord service | burn rate alert notifications via discord embed |
| orchestrator agent | provide sli source data (uptime stats, response time metrics) |

## effort estimate: medium (4-6 pt)

| area | pt estimate |
|---|---|
| slo definition crud + db schema | 1.0 |
| sli collector engine + prometheus adapter | 1.0 |
| error budget calculator + burn rate detection | 1.5 |
| compliance report generator | 1.0 |
| rest api endpoints | 0.5 |
| panel ui (dashboard, forms, reports) | 1.0 |
| integration + e2e tests | 0.5 |
| documentation | 0.5 |
| total | **6.0 pt** |

### risk factors

- prometheus query language complexity for custom slis may require additional iteration
- burn rate alert tuning (threshold calibration) needs production data feedback loop
- pdf generation for compliance reports may require extra effort for branded templates

## key metrics

| metric | target |
|---|---|
| sli evaluation latency | < 30s from metric ingestion |
| error budget calculation interval | every 60s |
| compliance report generation | < 30s per report |
| supported slos per organization | unlimited (paginated api) |
| api throughput | 100 req/s per slo endpoint |
