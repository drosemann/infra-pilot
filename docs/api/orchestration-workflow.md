# Workflow Studio API Reference
## Overview
Visual DAG-based workflow automation engine with 15+ node types, template variables, and execution history.

## Base URL: /api/v1/orchestration/workflows

### POST /
Create a new workflow.
**Request:**
| Field | Required | Type | Description |
|-------|----------|------|-------------|
| name | yes | string | Workflow name |
| description | yes | string | Workflow description |
| nodes | yes | array | Array of workflow nodes |
| edges | yes | array | Array of workflow edges |
| tags | no | string[] | Workflow tags |

**Node Schema:**
```json
{
  "node_id": "n1",
  "type": "action_webhook",
  "label": "Send Slack Notification",
  "config": {
    "url": "https://hooks.slack.com/...",
    "method": "POST",
    "headers": {"Content-Type": "application/json"},
    "body": "{\"text\": \"{{trigger.message}}\"}"
  },
  "position": {"x": 100, "y": 200}
}
```

**Edge Schema:**
```json
{
  "edge_id": "e1",
  "source": "n1",
  "target": "n2",
  "label": "on_success",
  "condition": "{{result.status}} == 'success'"
}
```

**Response:**
```json
{
  "workflow_id": "wf_abc123",
  "name": "Deploy Notification",
  "status": "draft",
  "nodes": [...],
  "edges": [...],
  "created_at": "2024-01-15T10:30:00Z",
  "version": 1
}
```

### GET /
List workflows. Query: status, tag, page, per_page

### GET /{workflow_id}
Get workflow with full node/edge definitions.

### PUT /{workflow_id}
Update workflow definition.

### DELETE /{workflow_id}
Delete workflow.

### POST /{workflow_id}/activate
Activate workflow for execution.

### POST /{workflow_id}/deactivate
Deactivate workflow.

### POST /{workflow_id}/execute
Execute workflow with trigger data.
**Request:** { "trigger_data": { "source": "webhook", "message": "Deploy complete" } }

### GET /{workflow_id}/executions
List execution history for workflow.

### GET /executions/{execution_id}
Get execution details with node-level status.

### GET /node-types
List available node types.

## Node Types

### Trigger Nodes
1. **trigger_manual** - Manual trigger via UI/API
2. **trigger_webhook** - Incoming webhook
3. **trigger_schedule** - Cron-based scheduling
4. **trigger_event** - Event-driven (deploy, alert, etc.)
5. **trigger_webhook_response** - Respond to webhook caller

### Action Nodes
6. **action_webhook** - Send HTTP request
7. **action_slack** - Send Slack message
8. **action_email** - Send email
9. **action_pagerduty** - Trigger PagerDuty alert
10. **action_script** - Execute shell script
11. **action_ansible** - Run Ansible playbook
12. **action_pipeline** - Trigger infra pipeline

### Logic Nodes
13. **condition** - If/else branching
14. **delay** - Wait for specified duration
15. **transform** - Transform data with template
16. **loop** - Iterate over array
17. **parallel** - Execute branches in parallel
18. **sub_workflow** - Execute another workflow
19. **switch** - Multi-branch switch

## Infrastructure Pipelines API Reference
## Base URL: /api/v1/orchestration/pipelines

### POST /
Create a pipeline.
**Request:** { "name", "description", "repo_url", "branch", "terraform_dir", "auto_apply": false }

### GET /
List pipelines.

### GET /{pipeline_id}
Get pipeline details.

### PUT /{pipeline_id}
Update pipeline.

### DELETE /{pipeline_id}
Delete pipeline.

### POST /{pipeline_id}/run
Trigger a pipeline run.
**Request:** { "triggered_by", "commit_sha", "branch" }

### GET /runs/{run_id}
Get run details with stage status.

### POST /runs/{run_id}/approve
Approve pipeline at approval gate.
**Request:** { "approver_id", "comments" }

### POST /runs/{run_id}/reject
Reject pipeline at approval gate.
**Request:** { "approver_id", "reason" }

### GET /{pipeline_id}/runs
List runs for pipeline.

## Pipeline Stages
1. **validate** - Validate configuration/terraform
2. **lint** - Run linters (tflint, checkov)
3. **plan** - Generate execution plan
4. **approve** - Manual approval gate
5. **apply** - Execute infrastructure changes
6. **verify** - Post-deployment verification
