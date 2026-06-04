# Feature 22: Spot/Preemptible Manager

## Overview
Manage spot/preemptible instance fleets across AWS, Azure, and GCP. Monitor savings, handle interruptions, and optimize fleet composition.

## Components
- `spot_manager.py` - Spot instance fleet management with interruption handling
- `spot_manager_cog.py` - Discord bot commands for spot management
- `SpotManager.tsx` - Management panel UI with fleet monitoring

## Data Models
- **Fleet**: `id`, `name`, `instance_types`, `target_capacity`, `regions`, `status`, `running_instances`, `savings_pct`
- **Instance**: `id`, `fleet_id`, `instance_type`, `region`, `status`, `launched_at`, `interruption_count`
- **SavingsSummary**: `total_savings`, `savings_pct`, `instance_count`, `fleets_count`

## API Endpoints
- `GET /api/v1/finops/spot/fleets` - List fleets
- `POST /api/v1/finops/spot/fleets` - Create fleet
- `GET /api/v1/finops/spot/fleets/{id}` - Get fleet
- `PATCH /api/v1/finops/spot/fleets/{id}` - Update fleet
- `GET /api/v1/finops/spot/fleets/{id}/instances` - List instances
- `GET /api/v1/finops/spot/savings` - Savings summary
- `POST /api/v1/finops/spot/fleets/{id}/launch` - Launch instances
- `POST /api/v1/finops/spot/instances/{id}/interrupt` - Simulate interruption

## CLI Usage
- `ipilot finops spot list` - List fleets
- `ipilot finops spot create <name> <instance_types> --target-capacity 2 --regions us-east-1`
- `ipilot finops spot get <fleet_id>` - Fleet details
- `ipilot finops spot instances <fleet_id>` - List instances
- `ipilot finops spot savings` - Savings summary
- `ipilot finops spot launch <fleet_id> --count 3`
- `ipilot finops spot interrupt <instance_id>`
- `ipilot finops spot update <fleet_id> <capacity>`

## Configuration
```yaml
spot_manager:
  default_regions: [us-east-1, us-west-2, eu-west-1]
  max_fleets: 20
  interruption_buffer: 0.3
  savings_threshold: 0.5
  auto_rebalance: true
```

## Example
```bash
ipilot finops spot create my-fleet m5.large,m5.xlarge --target-capacity 5
ipilot finops spot list
# Fleet table with savings percentages
```
