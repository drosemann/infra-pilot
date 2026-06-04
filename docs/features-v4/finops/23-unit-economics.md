# Feature 23: Unit Economics Dashboard

## Overview
Track and analyze cost per customer, per feature, or per dimension. Set targets, monitor violations, and optimize unit-level costs.

## Components
- `unit_economics.py` - Unit economics tracking and analysis engine
- `unit_economics_cog.py` - Discord bot commands
- `UnitEconomics.tsx` - Management panel UI

## Data Models
- **Metric**: `id`, `customer_id`, `metric_name`, `value`, `dimension`, `recorded_at`
- **Target**: `id`, `metric_name`, `target_value`, `threshold_pct`, `created_at`
- **Violation**: Metric values exceeding target thresholds

## API Endpoints
- `GET /api/v1/finops/unit-economics/metrics` - List metrics
- `POST /api/v1/finops/unit-economics/metrics` - Record metric
- `GET /api/v1/finops/unit-economics/targets` - List targets
- `POST /api/v1/finops/unit-economics/targets` - Set target
- `GET /api/v1/finops/unit-economics/violations` - List violations
- `GET /api/v1/finops/unit-economics/overview` - Overview

## CLI Usage
- `ipilot finops uoe metrics --customer-id <id> --dimension compute`
- `ipilot finops uoe record <customer_id> <metric_name> <value> --dimension compute`
- `ipilot finops uoe targets`
- `ipilot finops uoe set-target <metric_name> <target_value> --threshold 10`
- `ipilot finops uoe violations`
- `ipilot finops uoe overview`

## Configuration
```yaml
unit_economics:
  default_dimension: general
  violation_alert_channels: [email, slack]
  metric_retention_days: 365
  target_threshold_default: 10
```

## Example
```bash
ipilot finops uoe record cust-abc cost_per_user 12.50 --dimension compute
ipilot finops uoe violations
# Lists all metrics exceeding target thresholds
```
