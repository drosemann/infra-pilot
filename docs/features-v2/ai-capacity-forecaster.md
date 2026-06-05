# ai capacity forecaster

| field | value |
|-------|-------|
| id | f-010 |
| name | ai capacity forecaster |
| category | ai & intelligence |
| primary service | orchestrator agent |
| effort | medium (4-6 pt) |
| dependencies | feature 2 (ai resource optimizer), feature 1 (ai log anomaly detector) |
| phase | phase 1 |

## overview

the ai capacity forecaster analyzes historical resource usage data (cpu, ram, disk, network, player counts) across all managed servers to predict future capacity needs at 30, 60, and 90 day horizons. it identifies growth trends, seasonal patterns, and imminent resource exhaustion, then proactively recommends provisioning additional resources or rightsizing existing allocations before performance is impacted.

### goals

- predict resource exhaustion events >=7 days in advance with 90%+ precision
- forecast capacity needs at 30/60/90 day horizons per server and per account
- recommend provisioning actions with cost-benefit analysis
- reduce out-of-capacity incidents by 70%

### non-goals

- not a real-time autoscaler (recommendations require approval)
- does not automatically provision cloud resources
- not a billing or cost management tool (though informs cost planning)
- does not replace existing monitoring alerts

## architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          Data Sources                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Metrics DB   │  │ Usage        │  │ Player Count │  │ Billing      │ │
│  │ (Timescale)  │  │ History      │  │ History      │  │ History      │ │
│  │ CPU/RAM/Disk │  │ (Daily rolls)│  │ (Hourly)     │  │ (Monthly)    │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │
└─────────┼─────────────────┼─────────────────┼─────────────────┼──────────┘
          │                 │                 │                 │
          ▼                 ▼                 ▼                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                      Orchestrator Agent (Primary)                          │
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────┐        │
│  │                     Data Aggregation Layer                       │        │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐    │        │
│  │  │ Metrics        │  │ Anomaly        │  │ Seasonality    │    │        │
│  │  │ Collector      │  │ Detector       │  │ Extractor      │    │        │
│  │  │ (pull from TSDB)│  │ (outliers,     │  │ (daily, weekly,│    │        │
│  │  │                │  │  gaps, spikes) │  │  monthly)      │    │        │
│  │  └────────────────┘  └────────────────┘  └────────────────┘    │        │
│  └──────────────────────────────────────────────────────────────┘        │
│                              │                                            │
│                              ▼                                            │
│  ┌──────────────────────────────────────────────────────────────┐        │
│  │                      Forecasting Engine                          │        │
│  │                                                              │        │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌────────────┐  │        │
│  │  │ Statistical      │  │ ML Model         │  │ Ensemble   │  │        │
│  │  │ Models           │  │ (Prophet /        │  │ Combiner   │  │        │
│  │  │                  │  │  NeuralProphet)   │  │            │  │        │
│  │  │ - ARIMA          │  │                  │  │ - Weighted │  │        │
│  │  │ - Exponential    │  │ - Multi-variate  │  │   average  │  │        │
│  │  │   Smoothing      │  │ - Holiday effects│  │ - Variance │  │        │
│  │  │ - Linear Trend   │  │ - Growth curve   │  │   analysis │  │        │
│  │  └──────────────────┘  └──────────────────┘  └────────────┘  │        │
│  └──────────────────────────────────────────────────────────────┘        │
│                              │                                            │
│                              ▼                                            │
│  ┌──────────────────────────────────────────────────────────────┐        │
│  │                  Analysis & Recommendation Layer                 │        │
│  │                                                              │        │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌────────────┐  │        │
│  │  │ Resource         │  │ Exhaustion       │  │ Cost       │  │        │
│  │  │ Threshold        │  │ Detector         │  │ Analyzer   │  │        │
│  │  │ Analyzer         │  │                  │  │            │  │        │
│  │  │ - Current vs     │  │ - Days until     │  │ - Current  │  │        │
│  │  │   forecast       │  │   OOM             │  │   cost    │  │        │
│  │  │ - Per-resource   │  │ - Disk full date │  │ - Upgrade │  │        │
│  │  │   breakdown      │  │ - Network sat    │  │   cost    │  │        │
│  │  │ - Growth rate    │  │ - Player cap hit │  │ - Savings │  │        │
│  │  └──────────────────┘  └──────────────────┘  └────────────┘  │        │
│  └──────────────────────────────────────────────────────────────┘        │
│                              │                                            │
│                              ▼                                            │
│  ┌──────────────────────────────────────────────────────────────┐        │
│  │                     Provisioning Planner                          │        │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐    │        │
│  │  │ Recommendation │  │ Action Plan    │  │ Schedule       │    │        │
│  │  │ Generator      │  │ Builder        │  │ Optimizer      │    │        │
│  │  │ - Upgrade plan  │  │ - Step-by-step │  │ - Best time    │    │        │
│  │  │ - Downgrade    │  │ - Approvals    │  │ - Maintenance  │    │        │
│  │  │ - Add node     │  │ - Rollback     │  │   window aware │    │        │
│  │  └────────────────┘  └────────────────┘  └────────────────┘    │        │
│  └──────────────────────────────────────────────────────────────┘        │
└──────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                       Management Panel (UI)                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Forecast     │  │ Capacity     │  │ Timeline     │  │ Recommend-   │ │
│  │ Dashboard    │  │ Heatmap      │  │ View         │  │ ations Panel │ │
│  │ - 30/60/90   │  │ - Per-server │  │ - Historical │  │ - Ranked     │ │
│  │ - Per-server │  │ - Per-account │  │ - Predicted  │  │ - Cost-benefit│ │
│  │ - Account    │  │ - Per-region │  │ - Overlay    │  │ - One-click  │ │
│  │   summary    │  │              │  │              │  │   apply      │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
```

### data flow

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ Metrics │───▶│ Clean & │───▶│ Forecast│───▶│ Analyze │───▶│ Recommend│
│ (90d+)  │    │ Resample│    │ (3 models)    │ (thresholds)    │ (actions)│
└─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘
     │              │              │              │              │
     ▼              ▼              ▼              ▼              ▼
  TimescaleDB    Preprocess     Prophet +       Rule Engine     Notifications
                  Pipeline       ARIMA +       Checks          + UI Update
                                ES Model
```

## implementation plan

### phase 1: data collection & aggregation (week 1, 1.5 pt)

1. **metrics collector**
   - pull cpu, ram, disk, network i/o metrics from timescaledb (90+ day window)
   - player count history from minecraft query logs
   - swap usage, disk i/o wait, oom killer events
   - configurable resolution: 1-hour -> 1-day aggregation rollups

2. **data quality pipeline**
   - gap filling (linear interpolation for <6h gaps)
   - anomaly removal (1-time spikes, maintenance windows, backup spikes)
   - stationarity tests (augmented dickey-fuller)
   - seasonal decomposition (stl: seasonal, trend, residual)

3. **aggregation views**
   - pre-computed daily/hourly rollups per server
   - account-level rollups (sum of all servers)
   - group/label rollups (e.g., "production", "staging")

### phase 2: forecasting engine (week 1-3, 2.5 pt)

1. **statistical models**
   - **arima**: autoregressive integrated moving average
     - auto-search (p,d,q) parameters via aic minimization
     - best for: linear trends, stable seasonality
   - **exponential smoothing**: holt-winters
     - best for: clear seasonal patterns
   - **linear regression**: simple trend + seasonal dummies
     - best for: continuous growth with additive seasonality

2. **ml models**
   - **prophet** (meta): handles holidays, changepoints, outliers
   - **neuralprophet**: deep learning extension with auto-regression
   - **lightgbm** (future): multi-variate with external regressors

3. **ensemble strategy**
   - weighted average of top-3 models (weights based on recent accuracy)
   - confidence intervals: 80% and 95% prediction intervals
   - model selection per server per resource (different servers -> different best models)
   - weekly re-evaluation: test all models on last 14 days, pick best

### phase 3: analysis & recommendations (week 3-4, 1.5 pt)

1. **resource threshold analyzer**
   - compare forecast p95 against configured thresholds:
     - cpu: 80% sustained -> warning, 90% -> critical
     - ram: 85% used -> warning, 95% -> critical
     - disk: 75% -> warning, 90% -> critical
     - network: 70% bandwidth -> warning, 85% -> critical
   - earliest exhaustion date calculation

2. **exhaustion detector**
   - days until resource exhaustion (with confidence)
   - multiple scenario analysis:
     - current trend continues
     - growth accelerates (+20%)
     - growth decelerates (-20%)
   - slack time: days from detection to actual exhaustion

3. **provisioning recommendation engine**
   - for each predicted exhaustion:
     - recommended action (upgrade plan, add node, migrate)
     - cost: current vs. recommended
     - impact: performance improvement, headroom gained
     - timeline: recommended apply-by date
     - alternative options with trade-offs

4. **cost-benefit analyzer**
   - current monthly cost for server(s)
   - projected cost after recommendation
   - cost per unit of resource (e.g., $/gb ram)
   - payback period for upgrade

## api design

### endpoints

all endpoints are prefixed with `/api/v2/capacity-forecast`.

| Method | Path | Description |
|--------|------|-------------|
| `GET`  | `/forecast/{serverId}` | Get 30/60/90 day forecast for a server |
| `GET`  | `/forecast/{serverId}/history` | Get historical + predicted data points |
| `GET`  | `/forecast/account/{accountId}` | Get account-level aggregate forecast |
| `GET`  | `/forecast/group/{tag}` | Get forecast for tagged group of servers |
| `GET`  | `/recommendations` | List all active recommendations |
| `GET`  | `/recommendations/{recId}` | Get specific recommendation details |
| `PATCH`| `/recommendations/{recId}` | Accept/dismiss/modify recommendation |
| `POST` | `/recommendations/{recId}/apply` | Execute recommendation |
| `GET`  | `/models/{serverId}` | Get model metadata for a server |
| `POST` | `/models/{serverId}/retrain` | Force model retraining |
| `GET`  | `/accuracy` | Model accuracy dashboard data |

### request/response examples

**GET /api/v2/capacity-forecast/forecast/srv-mc-42**

```json
{
  "server_id": "srv-mc-42",
  "generated_at": "2026-05-27T06:00:00Z",
  "data_window": {
    "start": "2025-11-27T00:00:00Z",
    "end": "2026-05-27T00:00:00Z",
    "total_days": 181,
    "data_quality": 0.97
  },
  "forecasts": {
    "cpu": {
      "resource": "cpu",
      "unit": "percent",
      "current_value": 45.2,
      "trend": "increasing",
      "growth_rate": "1.8%/month",
      "models": {
        "primary": "prophet",
        "secondary": "arima",
        "ensemble_weights": { "prophet": 0.5, "arima": 0.3, "linear": 0.2 }
      },
      "predictions": {
        "30d": {
          "p50": 52.3,
          "p95": 68.1,
          "p05": 38.2,
          "confidence": 0.89
        },
        "60d": {
          "p50": 59.8,
          "p95": 78.4,
          "p05": 42.5,
          "confidence": 0.82
        },
        "90d": {
          "p50": 67.2,
          "p95": 89.6,
          "p05": 47.1,
          "confidence": 0.74
        }
      },
      "exhaustion": {
        "threshold": 90,
        "days_until_exhaustion_p50": 87,
        "days_until_exhaustion_p95": 42,
        "exhaustion_date_p95": "2026-07-08",
        "status": "watch"
      }
    },
    "ram": {
      "resource": "ram",
      "unit": "percent",
      "current_value": 72.0,
      "trend": "increasing",
      "growth_rate": "2.5%/month",
      "predictions": {
        "30d": { "p50": 79.5, "p95": 88.3, "p05": 72.1, "confidence": 0.92 },
        "60d": { "p50": 87.2, "p95": 96.4, "p05": 79.8, "confidence": 0.85 },
        "90d": { "p50": 94.8, "p95": 103.2, "p05": 86.5, "confidence": 0.76 }
      },
      "exhaustion": {
        "threshold": 95,
        "days_until_exhaustion_p50": 52,
        "days_until_exhaustion_p95": 28,
        "exhaustion_date_p95": "2026-06-24",
        "status": "critical"
      }
    },
    "disk": {
      "resource": "disk",
      "unit": "percent",
      "current_value": 55.0,
      "trend": "stable",
      "growth_rate": "0.3%/month",
      "predictions": {
        "30d": { "p50": 56.1, "p95": 58.4, "p05": 54.0, "confidence": 0.95 },
        "60d": { "p50": 57.2, "p95": 60.8, "p05": 54.5, "confidence": 0.93 },
        "90d": { "p50": 58.3, "p95": 63.2, "p05": 55.1, "confidence": 0.91 }
      },
      "exhaustion": null
    },
    "players": {
      "resource": "players",
      "unit": "count",
      "current_value": 45,
      "trend": "increasing",
      "growth_rate": "3.2 players/month",
      "predictions": {
        "30d": { "p50": 52, "p95": 62, "p05": 43, "confidence": 0.87 },
        "60d": { "p50": 58, "p95": 72, "p05": 47, "confidence": 0.79 },
        "90d": { "p50": 65, "p95": 84, "p05": 51, "confidence": 0.71 }
      },
      "exhaustion": {
        "threshold": 80,
        "days_until_exhaustion_p50": 68,
        "days_until_exhaustion_p95": 38,
        "exhaustion_date_p95": "2026-07-04",
        "status": "warning"
      }
    }
  },
  "overall_status": "critical"
}
```

**GET /api/v2/capacity-forecast/recommendations**

```json
{
  "recommendations": [
    {
      "id": "rec-cap-001",
      "server_id": "srv-mc-42",
      "resource": "ram",
      "severity": "critical",
      "title": "RAM exhaustion predicted within 28 days",
      "description": "Server srv-mc-42 will exhaust available RAM within 28 days (p95) under current growth trajectory. Current: 72% (7.2 GB / 10 GB).",
      "current_specs": {
        "plan": "game-10gb",
        "ram_gb": 10,
        "cpu_cores": 4,
        "disk_gb": 100
      },
      "recommended_specs": {
        "plan": "game-16gb",
        "ram_gb": 16,
        "cpu_cores": 6,
        "disk_gb": 100
      },
      "cost_analysis": {
        "current_monthly": 29.99,
        "recommended_monthly": 44.99,
        "monthly_increase": 15.00,
        "cost_per_gb_saved": "optimal",
        "recommended_apply_date": "2026-06-10"
      },
      "alternatives": [
        {
          "plan": "game-24gb",
          "ram_gb": 24,
          "monthly": 64.99,
          "pro": "Longer runway (~18 months before next upgrade)",
          "con": "Higher upfront cost increase"
        },
        {
          "action": "optimize_jvm",
          "description": "Apply JVM memory optimization flags to reduce memory pressure by ~15%",
          "pro": "No cost increase",
          "con": "Extends runway by ~45 days only"
        }
      ],
      "status": "open",
      "created_at": "2026-05-27T06:00:00Z",
      "expires_at": "2026-06-10T06:00:00Z"
    }
  ],
  "summary": {
    "total": 12,
    "critical": 2,
    "warning": 5,
    "info": 5,
    "total_monthly_increase_if_applied": 68.50
  }
}
```

## data model

```yaml
Forecast:
  id: string (UUID)
  server_id: string
  generated_at: datetime
  data_window_start: datetime
  data_window_end: datetime
  data_quality: float
  resources: ResourceForecast[]
  overall_status: "healthy" | "watch" | "warning" | "critical"

ResourceForecast:
  resource: "cpu" | "ram" | "disk" | "network" | "players"
  unit: string
  current_value: float
  current_timestamp: datetime
  trend: "increasing" | "decreasing" | "stable"
  growth_rate: string
  model_metadata: ModelMetadata
  predictions: TimeHorizonPredictions
  exhaustion: ExhaustionPrediction | null

ModelMetadata:
  primary: string
  secondary: string
  ensemble_weights: dict
  accuracy_last_14d: float
  last_retrained: datetime
  training_duration_ms: integer

TimeHorizonPredictions:
  30d: HorizonPrediction
  60d: HorizonPrediction
  90d: HorizonPrediction

HorizonPrediction:
  p50: float
  p95: float
  p05: float
  confidence: float

ExhaustionPrediction:
  threshold: float
  days_until_exhaustion_p50: integer
  days_until_exhaustion_p95: integer
  exhaustion_date_p50: date
  exhaustion_date_p95: date
  status: "ok" | "watch" | "warning" | "critical"

Recommendation:
  id: string (UUID)
  server_id: string
  resource: string
  severity: "critical" | "warning" | "info"
  status: "open" | "accepted" | "dismissed" | "applied" | "expired"
  title: string
  description: string
  current_specs: ServerSpecs
  recommended_specs: ServerSpecs
  cost_analysis: CostAnalysis
  alternatives: AlternativeAction[]
  triggered_by_forecast_id: string
  created_at: datetime
  expires_at: datetime
  applied_at: datetime | null
  applied_by: string | null

ServerSpecs:
  plan: string
  cpu_cores: integer
  ram_gb: integer
  disk_gb: integer
  bandwidth_tb: integer

CostAnalysis:
  current_monthly: float
  recommended_monthly: float
  monthly_increase: float
  payback_period_months: float | null
  cost_efficiency: "optimal" | "underprovisioned" | "overprovisioned"

AlternativeAction:
  type: "upgrade" | "downgrade" | "optimize" | "migrate" | "add_node"
  description: string
  pro: string
  con: string

TrainingMetrics:
  id: string (UUID)
  server_id: string
  model_name: string
  trained_at: datetime
  training_duration_ms: integer
  mape: float
  mae: float
  rmse: float
  mase: float
  training_data_points: integer
  features_used: string[]
```

## service assignments

| Service | Responsibility |
|---------|---------------|
| orchestrator agent | primary: data collection, forecasting engine, analysis, recommendation generation, model training |
| management panel | secondary: ui for forecast dashboard, heatmap, timeline, recommendations panel, cost analysis |
| integration service | secondary: alert/notification dispatch when critical recommendations generated, scheduled report delivery |
| service core | none directly; authentication, server metadata, account hierarchy |

## effort estimate

| Phase | Task | PT | Owner |
|-------|------|----|-------|
| P1 | Metrics collector + aggregation pipeline | 0.75 | Backend |
| P1 | Data quality checks + gap filling | 0.5 | Backend |
| P1 | Pre-computed rollup views | 0.25 | Backend |
| P2 | Statistical models (ARIMA, Holt-Winters, Linear) | 1.0 | Backend/ML |
| P2 | Prophet/NeuralProphet integration | 1.0 | ML |
| P2 | Ensemble model combiner + model selection | 0.5 | ML |
| P3 | Resource threshold analyzer + exhaustion detector | 0.5 | Backend |
| P3 | Provisioning recommendation engine | 0.5 | Backend |
| P3 | Cost-benefit analysis | 0.25 | Backend |
| P3 | Forecast dashboard + recommendations UI | 0.75 | Frontend |
| P3 | Scheduled report generation | 0.25 | Backend |
| total | | 5.75 pt | |

## risks & mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| insufficient historical data (<30 days) | high | fallback to linear trend; output with reduced confidence; flag for data collection |
| sudden traffic spikes (e.g., minecraft youtuber effect) | medium | anomaly detection excludes spikes; confidence intervals widen with uncertainty |
| model drift over time (forecast accuracy degrades) | medium | weekly accuracy evaluation; auto-retrain on threshold breach; model versioning |
| seasonality changes (e.g., summer vs. school year) | low | multi-year seasonality support in prophet; manual holiday/event calendar input |
| resource limits not well-understood (e.g., disk i/o) | medium | focus on clear resources first (ram, disk); add complex resources in v2 |
| over-provisioning leads to unnecessary spend | medium | conservative recommendations; explicit cost-benefit displayed; approval required |
| cold start for new servers | high | use account-level aggregates as baseline; populate with similar-server profiles |

## forecast accuracy tracking

```
┌─────────────────────────────────────────────────────────────────┐
│                      Model Accuracy Dashboard                      │
│                                                                   │
│  Resource │ Last 7d │ Last 14d │ Last 30d │ Best Model (14d)     │
│  ─────────┼─────────┼──────────┼──────────┼───────────────────── │
│  CPU      │  4.2%   │   5.1%   │   6.8%   │ Prophet              │
│  RAM      │  3.8%   │   4.5%   │   5.2%   │ NeuralProphet        │
│  Disk     │  1.2%   │   1.5%   │   2.1%   │ Linear (stable)      │
│  Players  │  8.7%   │  10.2%   │  14.5%   │ ARIMA                │
│  Network  │  6.3%   │   7.8%   │   9.1%   │ Prophet              │
│  ─────────┼─────────┼──────────┼──────────┼───────────────────── │
│  Overall  │  4.8%   │   5.8%   │   7.5%   │ Ensemble             │
└─────────────────────────────────────────────────────────────────┘

Accuracy metric: MAPE (Mean Absolute Percentage Error)
Retrain trigger: MAPE > 10% over 14 days
```

## configuration

### yaml configuration example

```yaml
# orchestrator-agent/config/capacity-forecaster.yml
capacity_forecast:
  enabled: true
  schedule: "0 6 * * *"

  data:
    min_history_days: 30
    max_history_days: 365
    aggregation: "1h"
    gap_fill_max_hours: 6
    anomaly_std_dev_threshold: 3.0

  models:
    ensemble:
      enabled: true
      evaluation_window_days: 14
      min_accuracy: 0.7
    prophet:
      enabled: true
      uncertainty_samples: 1000
      changepoint_prior_scale: 0.05
      seasonality_prior_scale: 10.0
      holidays: "minecraft-release-dates.csv"
    arima:
      enabled: true
      auto_search: true
      max_p: 5
      max_d: 2
      max_q: 5
    exponential_smoothing:
      enabled: true
      seasonal_periods: [7, 30]

  thresholds:
    cpu:
      warning: 80
      critical: 90
    ram:
      warning: 85
      critical: 95
    disk:
      warning: 75
      critical: 90
    network:
      warning: 70
      critical: 85
    players:
      warning: 75
      critical: 90

  recommendations:
    max_per_server: 3
    auto_dismiss_days: 30
    min_slack_days: 7
    cost_savings_threshold: 5.0

  notifications:
    critical:
      - type: "discord"
        channel: "capacity-alerts"
      - type: "email"
        to: ["ops@company.com"]
    weekly_report:
      enabled: true
      day: "monday"
      format: "pdf"
```

## future enhancements

- v2.0: multi-variate forecasting (cpu depends on players, ram depends on plugins)
- v2.1: cross-server migration recommendations (consolidate under-utilized servers)
- v2.2: auto-scaling integration with cloud provider apis
- v2.3: budget-aware capacity planning (recommend within cost constraints)
- v2.4: hardware lifecycle prediction (ssd wear, ecc error rates)
- v2.5: predictive auto-scaling with approval workflow + automated execution
