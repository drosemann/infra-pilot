# Feature 71: Workflow Studio

## Overview
Visual drag-and-drop workflow builder for creating automation workflows with a React-based canvas, node palette, and execution engine.

## Components
- `workflow_builder.py` - Backend workflow engine
- `workflow_executor.py` - Workflow execution runtime
- `workflow_routes.py` - API endpoints
- `workflow_canvas.tsx` - React drag-and-drop canvas
- `WorkflowManager` - Manager class

## Node Types
- **Triggers**: Webhook, Schedule, Event, Manual
- **Actions**: HTTP Request, SSH Command, Docker, Kubernetes, Script
- **Logic**: Condition, Switch, Loop, Delay, Parallel
- **Integration**: Discord, Slack, Email, PagerDuty, Jira
- **Transform**: JSON Path, JQ, Template

## Workflow Execution
- Directed Acyclic Graph (DAG) execution
- Parallel branch support
- Retry with backoff
- Timeout configuration
- Error handling branches
- Execution history and logs

## API Endpoints
- `GET /api/v1/workflows` - List workflows
- `POST /api/v1/workflows` - Create workflow
- `GET /api/v1/workflows/{id}` - Get workflow
- `PUT /api/v1/workflows/{id}` - Update workflow
- `DELETE /api/v1/workflows/{id}` - Delete workflow
- `POST /api/v1/workflows/{id}/execute` - Execute workflow
- `GET /api/v1/workflows/{id}/executions` - Execution history
- `GET /api/v1/workflows/{id}/executions/{exec_id}` - Execution details
- `POST /api/v1/workflows/{id}/toggle` - Enable/disable

## Workflow Definition (JSON)
```json
{
  "id": "uuid",
  "name": "Deploy and Notify",
  "nodes": [
    {"id": "n1", "type": "webhook_trigger", "config": {"path": "/deploy-webhook", "method": "POST"}},
    {"id": "n2", "type": "docker_deploy", "config": {"image": "nginx:latest", "port": 80}},
    {"id": "n3", "type": "discord_notify", "config": {"channel": "deployments", "message": "Deploy complete"}}
  ],
  "edges": [
    {"source": "n1", "target": "n2"},
    {"source": "n2", "target": "n3"}
  ]
}
```
