# Feature 80: Customer Success Automation

## Overview
Automated success play engine that executes trigger-based workflows for onboarding, renewal, expansion, and re-engagement. Rules engine with cooldown management.

## Components
- `success_automation.py` - Trigger-based success play execution
- `cx_cogs.py` - SuccessAutomationCog Discord commands

## Data Models
- `SuccessPlay` - Automated play with trigger and actions
- `PlayExecution` - Execution record with status and results
- `TriggerCondition` - Conditions for play evaluation

## API Endpoints
- `GET /api/v1/cx/success/plays` - List plays
- `POST /api/v1/cx/success/plays` - Create play
- `PATCH /api/v1/cx/success/plays/{id}/status` - Update play status
- `POST /api/v1/cx/success/trigger` - Evaluate trigger
- `GET /api/v1/cx/success/executions` - List executions
- `GET /api/v1/cx/success/stats` - Success automation stats

## Metrics
- Plays triggered, execution success rate, customer re-engagement rate
