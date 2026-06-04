# Feature 25: Budget & Forecast Engine

## Overview
Create and manage budgets across teams and services. Generate forecasts, run what-if scenarios, and track spend variance in real-time.

## Components
- `budget_forecast.py` - Budget planning and ML-based forecasting
- `budget_forecast_cog.py` - Discord bot commands
- `BudgetForecast.tsx` - Management panel UI

## Data Models
- **Budget**: `id`, `name`, `amount`, `period`, `scope`, `spent`, `status`
- **Forecast**: `budget_id`, `forecasted_spend`, `remaining`, `at_risk`
- **Scenario**: `budget_id`, `changes`, `current_forecast`, `scenario_forecast`, `recommendation`
- **Variance**: `budgeted`, `actual`, `variance`, `variance_pct`, `status`

## API Endpoints
- `GET /api/v1/finops/budget` - List budgets
- `POST /api/v1/finops/budget` - Create budget
- `GET /api/v1/finops/budget/{id}` - Get budget
- `POST /api/v1/finops/budget/{id}/spend` - Record spend
- `GET /api/v1/finops/budget/{id}/forecast` - Get forecast
- `POST /api/v1/finops/budget/{id}/scenario` - What-if scenario
- `GET /api/v1/finops/budget/summary` - Summary
- `GET /api/v1/finops/budget/{id}/variance` - Variance analysis

## CLI Usage
- `ipilot finops budget list`
- `ipilot finops budget create <name> <amount> --period monthly --scope team-eng`
- `ipilot finops budget get <budget_id>`
- `ipilot finops budget spend <budget_id> <amount>`
- `ipilot finops budget forecast <budget_id>`
- `ipilot finops budget scenario <budget_id> '{"ec2_growth": 0.15}'`
- `ipilot finops budget summary`
- `ipilot finops budget variance <budget_id>`

## Configuration
```yaml
budget_forecast:
  default_period: monthly
  forecast_algorithm: arima
  scenario_limit: 10
  alert_at_utilization: [75, 90, 100]
  rollover_unused: false
```

## Example
```bash
ipilot finops budget create eng-budget 50000 --period monthly --scope engineering
ipilot finops budget forecast eng-budget-id
# Shows projected spend and at-risk status
```
