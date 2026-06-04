# Feature 37: Automated Runbook Execution

## Overview
Convert DR runbooks to executable workflows with safety checks, manual approval gates, progress visibility, and post-mortem capture.

## Components
- `runbook_executor.py` - Runbook definition, step execution, rollback
- `RunbookExecutorCog` - Discord commands
- `RunbookExecutor.tsx` - Management panel UI

## Step Types
- Command, script, API call
- Approval gate, wait, notification
- Condition, rollback

## API Endpoints
- `GET /api/v1/resiliency/runbooks` - List runbooks
- `POST /api/v1/resiliency/runbooks` - Create runbook
- `POST /api/v1/resiliency/runbooks/{id}/execute` - Execute runbook
- `GET /api/v1/resiliency/runbooks/executions` - List executions
