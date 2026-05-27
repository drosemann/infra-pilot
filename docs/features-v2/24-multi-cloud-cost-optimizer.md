# feature 24: multi-cloud cost optimizer

| metadata | value |
|----------|-------|
| feature id | 24 |
| feature name | multi-cloud cost optimizer |
| primary service | orchestrator agent |
| effort estimate | medium (4-6 pt) |
| status | planned |

## 1. overview

a cost intelligence engine that continuously profiles infrastructure workloads and compares pricing across aws, gcp, azure, and hetzner. it delivers actionable migration recommendations -- which region, which provider, and which reserved/pay-as-you-go mix minimizes spend -- and tracks realized savings over time.

### goals

- reduce cloud spend by 15-40% via intelligent cross-provider arbitration
- provide a single pane of glass for multi-cloud pricing comparison
- automate workload right-sizing recommendations
- track savings with auditable before/after reports
- support spot/preemptible instance recommendations where applicable

## 2. architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         Panel (UI)                                │
│  ┌──────────────┐  ┌────────────────┐  ┌──────────────────────┐  │
│  │ Cost Dashboard│  │ Recommendation │  │ Savings Tracker      │  │
│  │ (per-project) │  │ Explorer       │  │ (before/after)       │  │
│  └──────┬───────┘  └───────┬────────┘  └──────────┬───────────┘  │
└─────────┼──────────────────┼──────────────────────┼──────────────┘
          │                  │                      │
          ▼                  ▼                      ▼
┌──────────────────────────────────────────────────────────────────┐
│                     Orchestrator Agent                            │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │                 Workload Profiler                          │   │
│  │  ┌────────────┐ ┌───────────┐ ┌──────────┐ ┌──────────┐  │   │
│  │  │ Inventory  │ │ Usage     │ │ Tagging  │ │ Reserved │  │   │
│  │  │ Collector  │ │ Analyzer  │ │ Enforcer │ │ Instance │  │   │
│  │  │            │ │           │ │          │ │ Planner  │  │   │
│  │  └─────┬──────┘ └─────┬─────┘ └────┬─────┘ └────┬─────┘  │   │
│  └────────┼──────────────┼────────────┼────────────┼─────────┘   │
│           │              │            │            │              │
│  ┌────────▼──────────────▼────────────▼────────────▼─────────┐   │
│  │                  Cost Comparison Engine                    │   │
│  │  ┌────────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │   │
│  │  │ Price      │ │ Instance │ │ Storage  │ │ Data     │   │   │
│  │  │ Scraper    │ │ Matcher  │ │ Cost     │ │ Transfer │   │   │
│  │  │            │ │          │ │ Analyzer │ │ Estimator│   │   │
│  │  └─────┬──────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘   │   │
│  └────────┼─────────────┼────────────┼────────────┼──────────┘   │
└───────────┼─────────────┼────────────┼────────────┼──────────────┘
            │             │            │            │
            ▼             ▼            ▼            ▼
┌───────────┐ ┌───────────┐ ┌───────────┐ ┌────────────┐
│ AWS       │ │ GCP       │ │ Azure     │ │ Hetzner    │
│ Pricing   │ │ Pricing   │ │ Pricing   │ │ Pricing    │
│ API       │ │ API       │ │ API       │ │ API        │
└───────────┘ └───────────┘ └───────────┘ └────────────┘
```

### component responsibilities

| component | role |
|-----------|------|
| orchestrator agent (core) | workload profiling, price comparison, recommendation engine |
| inventory collector | pulls running resources from each cloud provider via their apis |
| usage analyzer | reads cloudwatch/stackdriver/azure monitor metrics for cpu, ram, network |
| price scraper | fetches on-demand, reserved, and spot pricing from provider apis |
| instance matcher | maps cross-provider instance families by vcpu, ram, network, gpu |
| cost comparison engine | computes total monthly cost per provider for a given workload |
| savings tracker | stores baseline costs and compares after migration |

## 3. data model

### `cloud_providers`

| field | type | description |
|-------|------|-------------|
| id | uuid | primary key |
| name | varchar | e.g. "aws", "gcp", "azure", "hetzner" |
| display_name | varchar | |
| enabled | boolean | |
| pricing_api_config | jsonb | endpoint urls, api keys (encrypted) |

### `inventory_resources`

| field | type | description |
|-------|------|-------------|
| id | uuid | primary key |
| provider_id | uuid | fk to cloud_providers.id |
| environment_id | uuid | fk to environments.id |
| resource_type | varchar | "compute", "storage", "database", "network" |
| provider_resource_id | varchar | original resource id from provider |
| region | varchar | |
| instance_type | varchar | e.g. "t3.medium", "e2-standard-2" |
| specs | jsonb | vcpu, ram gb, gpu, network throughput |
| tags | jsonb | user-defined tags |
| status | varchar | running, stopped, terminated |
| created_at | timestamptz | |
| updated_at | timestamptz | |

### `usage_metrics`

| field | type | description |
|-------|------|-------------|
| id | uuid | primary key |
| resource_id | uuid | fk to inventory_resources.id |
| timestamp | timestamptz | |
| cpu_avg_pct | float | |
| cpu_max_pct | float | |
| memory_avg_pct | float | |
| memory_max_pct | float | |
| network_in_bytes | bigint | |
| network_out_bytes | bigint | |
| disk_read_bytes | bigint | |
| disk_write_bytes | bigint | |

### `price_catalog`

| field | type | description |
|-------|------|-------------|
| id | uuid | primary key |
| provider | varchar | |
| region | varchar | |
| instance_type | varchar | |
| pricing_model | enum | on_demand, reserved_1y, reserved_3y, spot |
| unit | varchar | "hour", "month" |
| price | decimal(10,6) | |
| effective_date | date | |
| created_at | timestamptz | |

### `cost_recommendations`

| field | type | description |
|-------|------|-------------|
| id | uuid | primary key |
| environment_id | uuid | fk to environments.id |
| resource_id | uuid | fk to inventory_resources.id |
| current_provider | varchar | |
| current_cost_monthly | decimal(10,2) | |
| target_provider | varchar | |
| target_region | varchar | |
| target_instance_type | varchar | |
| target_cost_monthly | decimal(10,2) | |
| estimated_savings_pct | float | |
| savings_monthly | decimal(10,2) | |
| migration_effort | enum | low, medium, high |
| confidence | float | 0.0 - 1.0 |
| status | enum | pending, applied, dismissed, expired |
| created_at | timestamptz | |
| applied_at | timestamptz | |

### `savings_reports`

| field | type | description |
|-------|------|-------------|
| id | uuid | primary key |
| environment_id | uuid | fk to environments.id |
| report_month | date | first day of the month |
| baseline_cost | decimal(10,2) | cost before any recommendations |
| actual_cost | decimal(10,2) | cost after applying recommendations |
| savings_amount | decimal(10,2) | |
| savings_pct | float | |
| details | jsonb | breakdown by resource / provider |
| created_at | timestamptz | |

## 4. api design

### workload inventory

```
GET    /api/v2/cost/inventory                    — List all inventoried resources
GET    /api/v2/cost/inventory/:id                — Get resource details + usage profile
PUT    /api/v2/cost/inventory/:id/tags           — Update resource tags
POST   /api/v2/cost/inventory/refresh            — Trigger full inventory resync
```

### pricing & comparison

```
GET    /api/v2/cost/prices                       — List price catalog (filterable by provider/region/type)
GET    /api/v2/cost/compare                      — Compare pricing for a given workload spec
POST   /api/v2/cost/compare/batch                — Batch comparison for multiple resources
```

query parameters for `GET /api/v2/cost/compare`:

| param | type | description |
|-------|------|-------------|
| vcpu | int | number of vcpus |
| memory_gb | int | ram in gb |
| gpu | string | gpu type (optional) |
| region | string | current region (optional, for filtering) |
| providers | string | comma-separated list of providers to compare |
| pricing_model | string | on_demand, reserved, spot |

### recommendations

```
GET    /api/v2/cost/recommendations              — List all recommendations
GET    /api/v2/cost/recommendations/:id          — Get recommendation details
POST   /api/v2/cost/recommendations/:id/apply    — Mark as applied / trigger migration
POST   /api/v2/cost/recommendations/:id/dismiss  — Dismiss recommendation
POST   /api/v2/cost/recommendations/generate     — Run full recommendation engine
```

### savings tracking

```
GET    /api/v2/cost/savings                      — Monthly savings summary
GET    /api/v2/cost/savings/:year/:month         — Detailed report for a specific month
GET    /api/v2/cost/savings/trend                 — Savings over time (json time-series)
```

## 5. implementation plan

### phase 1 -- provider pricing integration (1.5 pt)

• implement `pricescraper` with adapters for each provider's pricing api:
   - **aws**: `pricing.<region>.amazonaws.com` -- sku-based, sax-parsed
   - **gcp**: cloud billing catalog api
   - **azure**: retail prices api
   - **hetzner**: json pricing endpoint
• build `price_catalog` table and periodic sync job (daily)
• implement `instancematcher` -- normalizes instance families across providers

### phase 2 -- workload profiling (1.5 pt)

• `inventorycollector` -- pulls running resources from each provider's compute api
• `usageanalyzer` -- fetches metrics (cpu, ram, network) from monitoring apis
• build `usage_metrics` aggregation pipeline (hourly to daily to monthly rollup)
• profile tagging and right-sizing analysis (over-provisioned detection)

### phase 3 -- cost comparison engine (1 pt)

• implement comparison algorithm:
   - match workload profile to candidate instances per provider
   - compute total cost: compute + storage + data transfer + license
   - apply discount factors (reserved, committed use, spot)
   - score by cost, region proximity, and migration effort
• build `/cost/compare` and `/cost/compare/batch` endpoints

### phase 4 -- recommendations & savings tracking (1 pt)

• build recommendation generator -- scheduled + on-demand
• implement confidence scoring based on usage stability
• build savings reports -- monthly baseline vs. actual
• email/digest notifications for new high-savings opportunities

### phase 5 -- ui & polish (0.5-1 pt)

• cost dashboard with provider breakdown
• recommendation explorer with apply/dismiss workflow
• savings tracker with trend chart
• export to csv/pdf for procurement reviews

## 6. configuration examples

### workload spec for comparison (post /api/v2/cost/compare/batch)

```json
{
  "resources": [
    {
      "name": "web-server-group",
      "vcpu": 4,
      "memory_gb": 16,
      "gpu": null,
      "storage_gb": 100,
      "storage_type": "ssd",
      "monthly_network_egress_gb": 500,
      "current_provider": "aws",
      "current_region": "us-east-1",
      "current_instance": "t3.xlarge",
      "pricing_models": ["on_demand", "reserved_1y", "spot"],
      "min_uptime_pct": 99.5
    }
  ],
  "target_providers": ["aws", "gcp", "azure", "hetzner"],
  "target_regions": ["us-east-1", "us-central1", "eastus", "nbg1-dc1"]
}
```

### response excerpt

```json
{
  "comparisons": [
    {
      "resource": "web-server-group",
      "current": {
        "provider": "aws",
        "region": "us-east-1",
        "instance": "t3.xlarge",
        "monthly_cost": 216.32
      },
      "alternatives": [
        {
          "provider": "gcp",
          "region": "us-central1",
          "instance": "e2-standard-4",
          "monthly_cost": 152.18,
          "savings_pct": 29.7,
          "effort": "low"
        },
        {
          "provider": "hetzner",
          "region": "nbg1-dc1",
          "instance": "CX51",
          "monthly_cost": 89.46,
          "savings_pct": 58.6,
          "effort": "medium"
        }
      ]
    }
  ]
}
```

### recommendation generation (post /api/v2/cost/recommendations/generate)

```json
{
  "environments": ["env-001", "env-002"],
  "min_savings_pct": 10,
  "excluded_providers": [],
  "include_spot": true,
  "max_recommendations": 50
}
```

## 7. service assignments

| service | responsibilities |
|---------|------------------|
| **orchestrator agent** | core: workload profiler, price scraper, instance matcher, comparison engine, recommendation generator, savings tracker |
| **integration service** | provider-specific pricing api clients, inventory collectors |
| **panel** | cost dashboard, recommendation explorer, savings reports |
| **database** | `price_catalog`, `usage_metrics`, `cost_recommendations`, `savings_reports` |
| **scheduler** | daily price sync, hourly usage collection, weekly recommendation generation |

## 8. effort breakdown

| task | pt | dependencies |
|------|----|-------------|
| `pricescraper` base + aws adapter | 0.5 | -- |
| `pricescraper` gcp adapter | 0.25 | base scraper |
| `pricescraper` azure adapter | 0.25 | base scraper |
| `pricescraper` hetzner adapter | 0.25 | base scraper |
| `instancematcher` + normalization table | 0.5 | -- |
| `inventorycollector` + `usageanalyzer` | 1.0 | provider read apis |
| cost comparison algorithm | 1.0 | matcher + prices |
| recommendation generator | 0.5 | comparison engine |
| savings tracker + monthly reports | 0.5 | recommendations |
| ui (dashboard, explorer, savings) | 1.0 | all apis |
| documentation & tests | 0.5 | -- |

## 9. instance matching table (normalization)

| category | aws | gcp | azure | hetzner |
|----------|-----|-----|-------|---------|
| 2 vcpu / 8 gb | t3.large | e2-standard-2 | d2s v3 | cx42 |
| 4 vcpu / 16 gb | t3.xlarge | e2-standard-4 | d4s v3 | cx52 |
| 8 vcpu / 32 gb | t3.2xlarge | e2-standard-8 | d8s v3 | cx62 |
| 16 vcpu / 64 gb | m5.4xlarge | e2-standard-16 | d16s v3 | -- |

## 10. risks & mitigations

| risk | impact | mitigation |
|------|--------|------------|
| pricing api becomes stale | stale recommendations, over/under-estimated savings | daily sync + freshness indicator on price records |
| reserved instance math is complex | inaccurate comparisons for ris | model ri as upfront + hourly; use provider sdks for accurate amortization |
| data transfer costs vary wildly | wrong total cost estimation | include egress pricing in comparison; flag when egress > 50% of total |
| hetzner lacks equivalent gpu instances | gaps in recommendation for ml workloads | graceful degradation -- exclude providers without matching skus |
