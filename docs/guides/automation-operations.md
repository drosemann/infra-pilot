# Infra Pilot User Guide: Automation & Operations

## Overview
Infra Pilot's automation suite provides workflow automation, infrastructure CI/CD pipelines, configuration drift detection, resource quotas, auto-remediation, maintenance planning, runbook templates, chaos engineering, and self-healing infrastructure.

## Getting Started

### 1. Workflow Automation

**Create a deployment notification workflow:**
```bash
curl -X POST https://api.infra-pilot.io/api/v1/orchestration/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Deploy Notification",
    "description": "Send notifications when deployments complete",
    "nodes": [
      {
        "node_id": "trigger",
        "type": "trigger_webhook",
        "label": "Deploy Webhook",
        "config": {"path": "/webhook/deploy"}
      },
      {
        "node_id": "slack",
        "type": "action_slack",
        "label": "Notify Slack",
        "config": {
          "webhook_url": "https://hooks.slack.com/services/...",
          "message": "Deployment of {{trigger.service}} completed"
        }
      },
      {
        "node_id": "email",
        "type": "action_email",
        "label": "Email Team",
        "config": {
          "to": ["team@example.com"],
          "subject": "Deploy: {{trigger.service}}",
          "body": "Version {{trigger.version}} deployed to {{trigger.environment}}"
        }
      }
    ],
    "edges": [
      {"edge_id": "e1", "source": "trigger", "target": "slack"},
      {"edge_id": "e2", "source": "slack", "target": "email"}
    ]
  }'
```

**Activate and test the workflow:**
```bash
# Activate
curl -X POST https://api.infra-pilot.io/api/v1/orchestration/workflows/wf_abc123/activate

# Test with sample data
curl -X POST https://api.infra-pilot.io/api/v1/orchestration/workflows/wf_abc123/execute \
  -H "Content-Type: application/json" \
  -d '{
    "trigger_data": {
      "service": "api-gateway",
      "version": "v2.3.1",
      "environment": "production"
    }
  }'
```

### 2. Infrastructure Pipelines

**Create a Terraform CI/CD pipeline:**
```bash
curl -X POST https://api.infra-pilot.io/api/v1/orchestration/pipelines \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production Infrastructure",
    "description": "Infrastructure as Code pipeline for production",
    "repo_url": "https://github.com/org/infrastructure",
    "branch": "main",
    "terraform_dir": "/terraform/production",
    "auto_apply": false,
    "approval_required": true,
    "notifications": {
      "slack_channel": "#infra-deployments",
      "email": ["infra-team@example.com"]
    }
  }'
```

**Run the pipeline:**
```bash
ipilot infra-pipeline run pipeline_001 --branch main
```

**Approve the plan:**
```bash
curl -X POST https://api.infra-pilot.io/api/v1/orchestration/pipelines/runs/run_001/approve \
  -H "Content-Type: application/json" \
  -d '{"approver_id": "sre-lead", "comments": "Plan looks good, approved"}'
```

### 3. Configuration Drift Detection

**Run a drift scan:**
```bash
ipilot drift scan
```

**View drift results:**
```bash
ipilot drift list
```

**Suppress known drift:**
```bash
curl -X POST https://api.infra-pilot.io/api/v1/orchestration/drift/drifts/d_001/suppress \
  -H "Content-Type: application/json" \
  -d '{"reason": "Planned upgrade, will be resolved next deploy"}'
```

### 4. Resource Quotas

**Create a team quota:**
```bash
curl -X POST https://api.infra-pilot.io/api/v1/orchestration/quotas \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Engineering Team",
    "entity_type": "team",
    "entity_id": "team-engineering",
    "limits": {
      "cpu_cores": 64,
      "memory_gb": 256,
      "containers": 100,
      "storage_gb": 5000,
      "gpu_units": 8
    },
    "enforcement_mode": "hard"
  }'
```

**Check quota before creating resources:**
```bash
curl -X POST https://api.infra-pilot.io/api/v1/orchestration/quotas/check \
  -H "Content-Type: application/json" \
  -d '{
    "entity_type": "team",
    "entity_id": "team-engineering",
    "resources": {"cpu_cores": 8, "memory_gb": 32}
  }'
```

**Request a quota increase:**
```bash
curl -X POST https://api.infra-pilot.io/api/v1/orchestration/quotas/increase \
  -H "Content-Type: application/json" \
  -d '{
    "entity_type": "team",
    "entity_id": "team-engineering",
    "new_limits": {"cpu_cores": 128, "memory_gb": 512},
    "reason": "Expanding ML training infrastructure"
  }'
```

### 5. Auto-Remediation

**Create a remediation rule from template:**
```bash
curl -X POST https://api.infra-pilot.io/api/v1/orchestration/remediation/rules \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Restart Unhealthy Containers",
    "description": "Auto-restart containers that fail health checks",
    "trigger_type": "container_health",
    "condition": {
      "health_status": "unhealthy",
      "failure_count": {"gte": 3}
    },
    "action_type": "container_restart",
    "action_config": {"grace_period": 10, "max_restarts": 5},
    "cooldown_seconds": 300
  }'
```

**View remediation history:**
```bash
ipilot remediate history
```

### 6. Maintenance Windows

**Schedule a maintenance window:**
```bash
curl -X POST https://api.infra-pilot.io/api/v1/orchestration/maintenance/windows \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Database Upgrade - v15",
    "description": "Upgrade PostgreSQL from v14 to v15",
    "start_time": "2024-02-01T02:00:00Z",
    "end_time": "2024-02-01T06:00:00Z",
    "affected_systems": ["prod-db-01", "prod-db-02"],
    "risk_level": "high"
  }'
```

**Start and complete a window:**
```bash
# Start
curl -X POST https://api.infra-pilot.io/api/v1/orchestration/maintenance/windows/mw_001/start

# Complete
curl -X POST https://api.infra-pilot.io/api/v1/orchestration/maintenance/windows/mw_001/complete \
  -H "Content-Type: application/json" \
  -d '{"completion_notes": "Upgrade completed successfully, replication verified"}'
```

### 7. Runbook Templates

**View available runbook templates:**
```bash
ipilot runbook list
```

**Use a runbook (e.g., Database Rollback):**
```bash
ipilot runbook use db_rollback \
  --vars '{"db_name": "prod_db", "backup_file": "/backups/prod_db_20240115.sql"}'
```

### 8. Chaos Engineering

**Create a chaos experiment:**
```bash
curl -X POST https://api.infra-pilot.io/api/v1/orchestration/chaos/experiments \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Web Tier CPU Spike",
    "description": "Test autoscaling under CPU pressure",
    "target": {
      "type": "container",
      "selector": "app=web-server",
      "namespace": "staging"
    },
    "faults": [
      {
        "type": "cpu_stress",
        "parameters": {"cores": 4, "duration": 120, "load_percentage": 100}
      }
    ],
    "blast_radius": {
      "max_containers": 2,
      "exclude": ["health-checker"]
    }
  }'
```

**Run and monitor:**
```bash
ipilot chaos run experiment_001
ipilot chaos experiments
```

### 9. Self-Healing

**View healing system status:**
```bash
ipilot heal status
```

**Test a remediation scenario:**
```bash
curl -X POST https://api.infra-pilot.io/api/v1/orchestration/healing/remediate \
  -H "Content-Type: application/json" \
  -d '{
    "context": {
      "container": "web-01",
      "restart_count": 8,
      "cpu_percent": 95,
      "memory_percent": 80,
      "health": "unhealthy"
    }
  }'
```

**Retrain the healing model:**
```bash
ipilot heal retrain
```

## Configuration Reference

### Workflow Studio
```yaml
workflow_studio:
  max_nodes_per_workflow: 50
  execution_timeout: 3600
  max_concurrent_executions: 10
  variable_syntax: "{{variable.path}}"
```

### Infrastructure Pipelines
```yaml
infrastructure_pipelines:
  stages:
    - validate
    - lint
    - plan
    - approve
    - apply
    - verify
  terraform_version: "1.6.x"
  max_plan_timeout: 300
  approval_timeout: 86400
```

### Drift Detector
```yaml
drift_detector:
  scan_interval_minutes: 60
  resource_types:
    - docker_container
    - kubernetes_pod
    - system_package
    - file_content
  severity_thresholds:
    critical: 10
    high: 5
    medium: 3
```

### Auto-Remediation
```yaml
auto_remediation:
  global_cooldown_seconds: 60
  max_concurrent_actions: 5
  notify_on_action: true
  notify_channel: "#infra-alerts"
  escalation_after_failures: 3
```

### Self-Healing
```yaml
self_healing:
  confidence_thresholds:
    auto_remediate: 0.85
    suggest: 0.65
    log_only: 0.40
  model_type: q_learning
  learning_rate: 0.1
  discount_factor: 0.9
  exploration_rate: 0.1
  retrain_interval_hours: 24
  feedback_required: true
```
