# Feature 28: Carbon-Aware Cost Optimization

## Overview
Optimize cloud costs while minimizing carbon footprint. Analyze carbon intensity by region, evaluate cost-carbon tradeoffs, and track sustainability budgets.

## Components
- `carbon_cost_optimizer.py` - Carbon-aware optimization engine
- `carbon_cost_optimizer_cog.py` - Discord bot commands
- `CarbonCostOptimizer.tsx` - Management panel UI

## Data Models
- **Asset**: `id`, `name`, `provider`, `region`, `monthly_cost`, `kwh`
- **CarbonRec**: `id`, `asset_id`, `action`, `carbon_reduction`, `cost_impact`, `priority`
- **Footprint**: `asset_id`, `estimated_kwh_monthly`, `carbon_intensity`, `monthly_tons_co2`, `annual_tons_co2`
- **Tradeoff**: `current_cost`, `current_carbon`, `options` array with cost/carbon/savings

## API Endpoints
- `GET /api/v1/finops/carbon/recommendations` - List carbon recommendations
- `GET /api/v1/finops/carbon/assets` - List assets
- `POST /api/v1/finops/carbon/assets` - Register asset
- `GET /api/v1/finops/carbon/sustainability-budget` - Sustainability budget
- `GET /api/v1/finops/carbon/assets/{id}/footprint` - Asset carbon footprint
- `GET /api/v1/finops/carbon/assets/{id}/tradeoff` - Cost-carbon tradeoff
- `GET /api/v1/finops/carbon/intensity/{region}` - Carbon intensity

## CLI Usage
- `ipilot finops carbon list`
- `ipilot finops carbon assets`
- `ipilot finops carbon register <name> <provider> <region> --monthly-cost 1000 --kwh 5000`
- `ipilot finops carbon sustainability`
- `ipilot finops carbon footprint <asset_id>`
- `ipilot finops carbon tradeoff <asset_id>`
- `ipilot finops carbon intensity <region>`

## Configuration
```yaml
carbon_cost_optimizer:
  intensity_data_source: electricitymaps
  sustainability_budget_annual: 50000
  carbon_weight_in_scoring: 0.3
  low_carbon_regions: [eu-west-1, us-west-2, ca-central-1]
  offset_project: reforestation
```

## Example
```bash
ipilot finops carbon register web-server-prod aws us-east-1 --monthly-cost 2500 --kwh 12000
ipilot finops carbon intensity us-east-1
# Shows carbon intensity and grid mix for the region
```
