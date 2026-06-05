# feature 38: cost allocation & chargeback

- feature id: 38
- category: advanced observability
- primary service: integration service
- effort: medium (4-6 pt)
- dependencies: feature 24 (multi-cloud cost optimizer), feature 28 (team workspaces)

## overview

implement a comprehensive cost allocation and chargeback system that enables organizations to track cloud infrastructure spending by team, project, customer, or any custom dimension. supports both showback (informational) and chargeback (actual billing) models. generate monthly pdf and csv reports with per-tag cost breakdowns. integrate with cloud provider billing apis (aws cost explorer, gcp billing, azure cost management) and reconcile against provisioned resource inventory.

### goals

- tag all resources (servers, databases, networks, storage) with metadata dimensions
- pull cost data from cloud provider billing apis and reconcile with inventory
- compute per-tag cost breakdowns with support for hierarchy and aggregation
- support showback (view-only) and chargeback (cross-charge) models
- generate monthly chargeback reports in pdf and csv formats
- track budgets per tag dimension and alert on overspend
- expose cost data via rest api for integration with external billing systems

## architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Data Sources                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ AWS Cost     │  │ GCP Billing  │  │ Azure Cost   │              │
│  │ Explorer     │  │ Export       │  │ Management   │              │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
│         │                 │                 │                        │
│  ┌──────▼─────────────────▼─────────────────▼───────┐              │
│  │           Cloud Billing Ingestion Layer            │              │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  │              │
│  │  │ AWS        │  │ GCP        │  │ Azure      │  │              │
│  │  │ Adapter    │  │ Adapter    │  │ Adapter    │  │              │
│  │  └────────────┘  └────────────┘  └────────────┘  │              │
│  └──────────────────────┬────────────────────────────┘              │
│                         │                                            │
│  ┌──────────────────────▼────────────────────────────┐              │
│  │              Integration Service                     │              │
│  │  ┌──────────────────┐  ┌────────────────────────┐  │              │
│  │  │ Tag Engine        │  │ Cost Allocation        │  │              │
│  │  │ - Tag propagation │  │ Engine                  │  │              │
│  │  │ - Tag validation  │  │ - Per-tag cost calc    │  │              │
│  │  │ - Auto-tagging    │  │ - Showback/chargeback  │  │              │
│  │  │ rules             │  │ - Amortization         │  │              │
│  │  └────────┬─────────┘  └───────────┬────────────┘  │              │
│  │           │                        │                │              │
│  │  ┌────────▼────────────────────────▼────────────┐  │              │
│  │  │              Reconciliation Engine            │  │              │
│  │  │  - Match billing line items to inventory     │  │              │
│  │  │  - Detect untagged resources                 │  │              │
│  │  │  - Flag cost anomalies                        │  │              │
│  │  └──────────────────────┬────────────────────────┘  │              │
│  └─────────────────────────┬───────────────────────────┘              │
│                            │                                          │
┌────────────────────────────┼──────────────────────────────────────────┐
│                    ┌───────▼────────┐                                 │
│                    │  Report Engine  │                                 │
│                    │  - PDF (HTML→  │                                 │
│                    │    WeasyPrint) │                                 │
│                    │  - CSV export  │                                 │
│                    │  - Schedule    │                                 │
│                    │    monthly     │                                 │
│                    └───────┬────────┘                                 │
│                            │                                          │
│  ┌─────────────────────────▼──────────────────────────────────────┐  │
│  │                     Storage Layer                                │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │  │
│  │  │ PostgreSQL   │  │ Redis Cache  │  │ Object Store        │  │  │
│  │  │ (tags, costs, │  │ (aggregated  │  │ (reports, invoices)  │  │  │
│  │  │  budgets)    │  │  cost views) │  │                      │  │  │
│  │  └──────────────┘  └──────────────┘  └──────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
```

### tag propagation strategy

```
Cloud Provider Tag ──▶ Orchestrator Resource ──▶ Inventory Record
     applied at              inherits from              enriched with
   provisioning             parent resource              computed tags
       │                         │                           │
       ▼                         ▼                           ▼
  Team: "platform"          Team: "platform"          Team: "platform"
  Project: "infra"          Project: "infra"          Project: "infra"
  Env: "prod"               Env: "prod"               Env: "prod"
                                                        Cost Center: "eng-42"
                                                        Budget: "platform-prod"
```

### showback vs chargeback models

| feature | showback | chargeback |
|---|---|---|
| purpose | awareness & accountability | cross-charge between teams |
| financial impact | informational only | actual invoice adjustment |
| granularity | per-team/project breakdown | per-consumer with unit pricing |
| approval needed | no | yes (finance/admin) |
| report type | dashboard + csv | formal pdf invoice |
| implementation | computed costs displayed | costs applied via credit/debit |

## data model

### cost tag definition

```yaml
cost_tag:
  id: "tag-team-platform"
  key: "team"
  value: "platform"
  description: "Platform engineering team"
  hierarchy:
    parent: null
    children:
      - "team-platform-infra"
      - "team-platform-sre"
  propagation: "inherited"       # inherited | explicit | computed
  compliance:
    required: true
    allowed_values:
      - "platform"
      - "games"
      - "business"
      - "internal"
  budget:
    monthly_limit: 5000.00
    currency: "USD"
    alert_thresholds:
      - at_percent: 80
        severity: "warning"
      - at_percent: 100
        severity: "critical"
```

### resource cost allocation

```yaml
resource_cost:
  resource_id: "srv-web-01"
  resource_type: "server"
  provider: "aws"
  provider_resource_id: "i-0abcd1234efgh5678"
  period:
    start: "2026-05-01T00:00:00Z"
    end: "2026-05-31T23:59:59Z"
  line_items:
    - category: "compute"
      service: "EC2"
      usage_type: "t3.large"
      quantity: 744                       # hours
      unit: "Hrs"
      cost: 248.32
    - category: "storage"
      service: "EBS"
      usage_type: "gp3"
      quantity: 100                       # GB-months
      unit: "GB-Mo"
      cost: 8.00
    - category: "network"
      service: "DataTransfer"
      usage_type: "Out-Bytes"
      quantity: 50                        # GB
      unit: "GB"
      cost: 4.50
  total_cost: 260.82
  tags:
    team: "platform"
    project: "infra"
    environment: "production"
    cost_center: "cc-eng-42"
  allocation:
    method: "direct"                     # direct | proportional | prorated
    proportion: 1.0
```

### budget & chargeback report

```yaml
chargeback_report:
  id: "cbr-2026-05"
  type: "monthly"
  period:
    start: "2026-05-01T00:00:00Z"
    end: "2026-05-31T23:59:59Z"
  generated_at: "2026-06-01T02:00:00Z"
  organization_id: "org-acme"
  model: "showback"                      # showback | chargeback
  currency: "USD"
  summary:
    total_cost: 45230.12
    total_untagged_cost: 1230.45
    tagged_percentage: 97.28
    budget_variance: -230.12             # negative = under budget
  breakdowns:
    by_team:
      - dimension: "team:platform"
        total: 18450.00
        percentage: 40.8
        servers: 23
        budget: 20000.00
        variance: -1550.00
      - dimension: "team:games"
        total: 12500.00
        percentage: 27.6
        servers: 18
        budget: 15000.00
        variance: -2500.00
      - dimension: "team:business"
        total: 13049.67
        percentage: 28.9
        servers: 12
        budget: 10000.00
        variance: 3049.67
    by_environment:
      - dimension: "env:production"
        total: 31200.00
        percentage: 69.0
      - dimension: "env:staging"
        total: 8540.12
        percentage: 18.9
      - dimension: "env:development"
        total: 5489.55
        percentage: 12.1
    by_service:
      - dimension: "service:compute"
        total: 28100.00
        percentage: 62.1
      - dimension: "service:storage"
        total: 9230.12
        percentage: 20.4
      - dimension: "service:network"
        total: 6400.00
        percentage: 14.2
      - dimension: "service:other"
        total: 1499.55
        percentage: 3.3
```

### reconciliation record

```yaml
reconciliation:
  id: "rec-2026-05"
  period: "2026-05"
  provider: "aws"
  billing_total: 45230.12
  inventory_total: 43999.67
  discrepancy: 1230.45
  discrepancy_percent: 2.72
  untagged_resources:
    - resource_id: "i-abcdef123456"
      resource_type: "ec2"
      estimated_cost: 89.50
      missing_tags: ["team", "project"]
  reconciled_at: "2026-06-01T01:30:00Z"
  status: "partial"                     # complete | partial | failed
```

## api design

### tag management

#### list tags

```
GET /api/v2/cost/tags
  ?key=team
  &page=1
  &per_page=50
```

#### create tag definition

```
POST /api/v2/cost/tags
```

```json
{
  "key": "cost_center",
  "value": "cc-eng-42",
  "description": "Engineering cost center code",
  "propagation": "inherited",
  "compliance": {
    "required": true,
    "allowed_values": ["cc-eng-42", "cc-games-01", "cc-business-07"]
  },
  "budget": {
    "monthly_limit": 20000.00,
    "currency": "USD",
    "alert_thresholds": [
      { "at_percent": 80, "severity": "warning" },
      { "at_percent": 100, "severity": "critical" }
    ]
  }
}
```

### resource costs

#### get resource cost

```
GET /api/v2/cost/resources/{resource_id}/cost
  ?period=2026-05
```

#### list resource costs by tag

```
GET /api/v2/cost/by-tag
  ?tag=team:platform
  &period=2026-05
  &granularity=daily
```

### chargeback reports

#### list reports

```
GET /api/v2/cost/reports
  ?period=2026-05
  &type=showback
```

#### generate report

```
POST /api/v2/cost/reports/generate
```

```json
{
  "period": "2026-05",
  "type": "chargeback",
  "format": "pdf",
  "include_breakdowns": ["by_team", "by_environment", "by_service"],
  "tag_dimensions": ["team", "project", "environment"]
}
```

response `202`:
```json
{
  "report_id": "cbr-2026-05",
  "status": "generating",
  "estimated_seconds": 30
}
```

#### download report

```
GET /api/v2/cost/reports/{report_id}/download
  ?format=pdf
```

### budget tracking

#### list budgets

```
GET /api/v2/cost/budgets
```

#### get budget status

```
GET /api/v2/cost/budgets/{tag_id}
```

```json
{
  "tag_id": "tag-team-platform",
  "monthly_limit": 20000.00,
  "current_spend": 18450.00,
  "remaining": 1550.00,
  "utilization_percent": 92.25,
  "status": "warning",
  "forecast_spend": 19500.00,
  "days_remaining_in_period": 5,
  "alerts_triggered": [
    {
      "threshold": 80,
      "triggered_at": "2026-05-20T14:30:00Z",
      "spend_at_trigger": 16050.00
    }
  ]
}
```

### reconciliation

#### run reconciliation

```
POST /api/v2/cost/reconciliation/run
```

```json
{
  "period": "2026-05",
  "providers": ["aws", "gcp"]
}
```

#### list reconciliations

```
GET /api/v2/cost/reconciliation
  ?period=2026-05
  &status=partial
```

## implementation plan

### phase 1: tag engine & cost ingestion (pt 1-2)

| step | description | artifacts |
|---|---|---|
| 1.1 | tag crud endpoints, validation, propagation rules | `models/cost_tags.py`, `routes/cost.py` |
| 1.2 | cloud billing adapters: aws cost explorer sdk | `adapters/aws_billing.py` |
| 1.3 | cloud billing adapters: gcp billing + azure cost mgmt | `adapters/gcp_billing.py`, `adapters/azure_billing.py` |
| 1.4 | inventory-to-billing reconciliation engine | `services/reconciliation.py` |

### phase 2: cost allocation engine (pt 3-4)

| step | description | artifacts |
|---|---|---|
| 2.1 | per-tag cost calculation with hierarchy support | `services/cost_allocation.py` |
| 2.2 | showback vs chargeback models + budget tracking | `services/budget_tracker.py` |
| 2.3 | rest api: cost queries, budgets, reports | `routes/cost.py` (extend) |
| 2.4 | unit tests for tag propagation and cost math | `tests/test_cost_allocation.py` |

### phase 3: reporting & panel ui (pt 5-6)

| step | description | artifacts |
|---|---|---|
| 3.1 | pdf report generator with charts and tables | `services/report_generator.py` |
| 3.2 | csv export for raw cost data | `services/csv_exporter.py` |
| 3.3 | panel ui: cost dashboard, tag explorer, budget gauges | panel components |
| 3.4 | panel ui: report viewer, reconciliation summary | panel components |

## service assignments

| service | responsibility |
|---|---|
| integration service (primary) | tag management, cloud billing ingestion, cost allocation engine, reconciliation, budget tracking, report generation, rest api |
| management panel | cost dashboard, tag management ui, budget gauge widgets, report viewer/download, untagged resources view |
| orchestrator agent | tag propagation to provisioned resources, tag input during server create/update workflows |
| discord service | budget overspend alerts, monthly cost summary notifications |

## effort estimate: medium (4-6 pt)

| area | pt estimate |
|---|---|
| tag engine (crud, validation, propagation) | 1.0 |
| cloud billing adapters (aws, gcp, azure) | 1.5 |
| reconciliation engine | 0.5 |
| cost allocation engine (per-tag calc, showback/chargeback) | 1.0 |
| budget tracking + alerts | 0.5 |
| report generation (pdf + csv) | 0.5 |
| rest api endpoints | 0.5 |
| panel ui (dashboard, tag explorer, reports) | 1.5 |
| integration + e2e tests | 0.5 |
| documentation | 0.5 |
| total | **8.0 pt (rounded to 6 with billing sdk reuse)** |

### risk factors

- cloud billing apis have different data freshness slas (aws ~24h, gcp ~48h, azure ~24h)
- currency conversion and amortization (ri/sp) adds complexity for multi-provider setups
- tag propagation lag: cloud tags applied at provisioning may take hours to appear in billing data
- pdf report formatting is time-consuming to get right across different page sizes/locales

## key metrics

| metric | target |
|---|---|
| cost data freshness | < 24h from cloud provider cut-off |
| reconciliation accuracy | > 99% match between billing and inventory |
| report generation time | < 30s per monthly report |
| supported tag dimensions | unlimited (key-value pairs) |
| api throughput | 100 req/s for cost queries |
| max resources tracked | 50,000 per organization |
