# Feature 26: Resource Right-Sizing

## Overview
Analyze cloud resource utilization and recommend right-sizing actions to eliminate over-provisioning. Support compute, database, and storage resources.

## Components
- `rightsizing.py` - Resource analysis and recommendation engine
- `rightsizing_cog.py` - Discord bot commands
- `Rightsizing.tsx` - Management panel UI

## Data Models
- **Recommendation**: `id`, `resource_id`, `current_size`, `recommended_size`, `utilization_pct`, `estimated_savings`, `confidence`, `status`
- **Resource**: `id`, `name`, `resource_type`, `current_size`, `specs`, `monthly_cost`, `provider`, `region`

## API Endpoints
- `GET /api/v1/finops/rightsizing/recommendations` - List recommendations
- `POST /api/v1/finops/rightsizing/recommendations` - Create recommendation
- `GET /api/v1/finops/rightsizing/summary` - Summary
- `POST /api/v1/finops/rightsizing/recommendations/{id}/approve` - Approve
- `POST /api/v1/finops/rightsizing/recommendations/{id}/implement` - Implement
- `POST /api/v1/finops/rightsizing/recommendations/{id}/dismiss` - Dismiss
- `POST /api/v1/finops/rightsizing/resources` - Register resource
- `POST /api/v1/finops/rightsizing/resources/{id}/analyze` - Analyze resource

## CLI Usage
- `ipilot finops rightsizing list`
- `ipilot finops rightsizing summary`
- `ipilot finops rightsizing approve <rec_id>`
- `ipilot finops rightsizing implement <rec_id>`
- `ipilot finops rightsizing dismiss <rec_id>`
- `ipilot finops rightsizing register <name> <type> <current_size> --monthly-cost 500 --provider aws`
- `ipilot finops rightsizing analyze <resource_id>`

## Configuration
```yaml
rightsizing:
  analysis_frequency_hours: 24
  min_savings_threshold: 10
  supported_types: [compute, database, storage]
  auto_approve_threshold: 50
  utilization_target: 60
```

## Example
```bash
ipilot finops rightsizing list
# Shows all recommendations with savings estimates
ipilot finops rightsizing approve rs-123
# Approves the recommendation for implementation
```
