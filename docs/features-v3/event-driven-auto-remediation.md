# Feature 76: Event-driven Auto-remediation

## Overview
Rule engine for automated remediation actions triggered by events, alerts, and metrics with a condition-action framework supporting complex rule chains.

## Components
- `remediation_engine.py` - Core rule engine
- `rule_evaluator.py` - Rule condition evaluation
- `action_executor.py` - Remediation action execution
- `remediation_routes.py` - API endpoints
- `RemediationManager` - Manager class

## Rule Structure
```json
{
  "id": "uuid",
  "name": "Restart unhealthy container",
  "description": "Auto-restart container if health check fails 3 times",
  "enabled": true,
  "conditions": {
    "all": [
      {"type": "metric", "metric": "container.health", "operator": "eq", "value": "unhealthy"},
      {"type": "threshold", "metric": "container.health_failures", "operator": "gte", "value": 3},
      {"type": "time_window", "window": "5m"}
    ]
  },
  "actions": [
    {"type": "docker_restart", "config": {"container": "{{event.container_id}}", "grace_period": 10}},
    {"type": "discord_notify", "config": {"channel": "remediation", "message": "Container restarted"}},
    {"type": "create_ticket", "config": {"priority": "low", "assignee": "sre-team"}}
  ],
  "cooldown": 300,
  "max_executions": 5
}
```

## Available Conditions
- **Metric**: Compare metric value (CPU, memory, disk, health)
- **Event**: Match event type and attributes
- **Threshold**: Cross threshold (above/below)
- **Time**: Time-based conditions (maintenance window, business hours)
- **Composite**: AND/OR/NOT logical operators
- **Script**: Custom script evaluation

## Available Actions
- Docker: restart, stop, start, recreate, scale
- Kubernetes: rollout restart, scale, delete pod
- System: restart service, run script, reboot
- Notification: Discord, Slack, Email, PagerDuty
- Integration: Webhook, Jira ticket, Ansible playbook
- Remediation: rollback deployment, increase resources

## API Endpoints
- `GET /api/v1/remediation/rules` - List rules
- `POST /api/v1/remediation/rules` - Create rule
- `GET /api/v1/remediation/rules/{id}` - Get rule
- `PUT /api/v1/remediation/rules/{id}` - Update rule
- `DELETE /api/v1/remediation/rules/{id}` - Delete rule
- `POST /api/v1/remediation/rules/{id}/test` - Test rule
- `GET /api/v1/remediation/executions` - Execution history
- `GET /api/v1/remediation/executions/{id}` - Execution details
