# Feature 4: Unified Cloud Cost Control

## Overview
Aggregate billing from all providers into single view. Anomaly detection on cross-provider spend. Budget enforcement with auto-shutdown.

## Components
- `cloud_cost_control.py` — Cost aggregator, anomaly detection, budget enforcement
- `CloudCostControlCog` — Discord commands for cost control
- `CloudCostControl.tsx` — React cost control dashboard
- CLI commands in `cli/ipilot/commands/hybrid_cloud/cloud_cost_control.py`

## API Endpoints
- `GET /api/cost/summary` — Get cost summary
- `POST /api/cost/record` — Record cost entry
- `GET /api/cost/budgets` — List budgets
- `POST /api/cost/budgets` — Create budget
- `GET /api/cost/anomalies` — List anomalies
- `GET /api/cost/forecast` — Get cost forecast

## Anomaly Detection
Uses statistical deviation analysis: when a cost record deviates >150% from the mean of recent records, an anomaly is created with severity based on deviation magnitude.
