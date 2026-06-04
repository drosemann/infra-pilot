# Feature 29: Multi-Cloud Discount Arbitrage

## Overview
Compare costs across cloud providers for a given workload specification. Identify the most cost-effective provider and generate migration recommendations.

## Components
- `discount_arbitrage.py` - Cross-provider cost comparison engine
- `discount_arbitrage_cog.py` - Discord bot commands
- `DiscountArbitrage.tsx` - Management panel UI

## Data Models
- **Workload**: `id`, `name`, `cpu_cores`, `memory_gb`, `storage_gb`, `data_transfer_gb`, `current_provider`, `current_cost`
- **Comparison**: `id`, `workload_id`, alternative provider costs and savings
- **Savings**: `total_comparisons`, `total_potential_savings`, `best_provider`, `average_savings_pct`

## API Endpoints
- `GET /api/v1/finops/arbitrage/workloads` - List workloads
- `POST /api/v1/finops/arbitrage/workloads` - Register workload
- `GET /api/v1/finops/arbitrage/comparisons` - List comparisons
- `POST /api/v1/finops/arbitrage/comparisons` - Create comparison
- `GET /api/v1/finops/arbitrage/savings` - Savings summary
- `GET /api/v1/finops/arbitrage/workloads/{id}/compare` - Provider comparison
- `POST /api/v1/finops/arbitrage/workloads/{id}/migrate` - Migration recommendation

## CLI Usage
- `ipilot finops arbitrage workloads`
- `ipilot finops arbitrage comparisons`
- `ipilot finops arbitrage savings`
- `ipilot finops arbitrage register <name> <cpu> <memory> <storage> <transfer> <provider> <cost>`
- `ipilot finops arbitrage compare <workload_id>`
- `ipilot finops arbitrage migrate <workload_id>`

## Configuration
```yaml
discount_arbitrage:
  providers: [aws, azure, gcp, hetzner, ovh, digitalocean]
  currency: USD
  pricing_data_refresh_hours: 24
  min_savings_pct: 5
  include_transfer_costs: true
```

## Example
```bash
ipilot finops arbitrage register web-app 8 32 200 500 aws 1500
ipilot finops arbitrage compare wl-abc
# Shows cost comparison across all supported providers
```
