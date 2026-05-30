# Maintenance Planner API Reference
## Overview
Calendar-based maintenance window scheduling with blackout periods, conflict detection, and auto-approval workflows.

## Base URL: /api/v1/orchestration/maintenance

### POST /windows
Schedule a maintenance window.
**Request:**
| Field | Required | Type | Description |
|-------|----------|------|-------------|
| name | yes | string | Window display name |
| description | no | string | Detailed description |
| start_time | yes | datetime | ISO 8601 start time |
| end_time | yes | datetime | ISO 8601 end time |
| affected_systems | yes | string[] | System/component IDs |
| risk_level | no | string | low/medium/high/critical |
| created_by | no | string | Creator user ID |
| approval_required | no | boolean | Require approval before execution |
| notify_channels | no | string[] | Notification channels |

**Response:**
```json
{
  "window_id": "mw_abc123",
  "name": "Database Upgrade",
  "status": "scheduled",
  "start_time": "2024-01-20T02:00:00Z",
  "end_time": "2024-01-20T06:00:00Z",
  "affected_systems": ["prod-db-01", "prod-db-02"],
  "risk_level": "high",
  "created_by": "sre-team",
  "duration_hours": 4,
  "approval_status": "pending"
}
```

### GET /windows
List maintenance windows.
**Query Parameters:** status (scheduled/in_progress/completed/cancelled), from_date, to_date, system

### GET /windows/{window_id}
Get window details.

### PUT /windows/{window_id}
Update window (reschedule, change scope).

### DELETE /windows/{window_id}
Delete/cancel window.

### POST /windows/{window_id}/start
Start maintenance window.
**Response:** { "status": "in_progress", "started_at": "..." }

### POST /windows/{window_id}/complete
Mark window as completed.
**Request:** { "completion_notes": "Upgrade successful, replication lag resolved" }

### POST /windows/{window_id}/cancel
Cancel window.
**Request:** { "reason": "No longer needed" }

### POST /windows/{window_id}/extend
Extend window duration.
**Request:** { "additional_minutes": 120 }

### POST /windows/{window_id}/approve
Approve maintenance window.
**Request:** { "approver_id": "manager-001", "comments": "Approved" }

### POST /windows/{window_id}/reject
Reject maintenance window.
**Request:** { "approver_id": "manager-001", "reason": "Conflict with other maintenance" }

### GET /calendar
Get calendar view of maintenance events.
**Query Parameters:** start_date, end_date

## Blackout Periods

### POST /blackouts
Create blackout period.
**Request:** { "name", "start_time", "end_time", "affected_systems": ["prod-*"] }

### GET /blackouts
List blackout periods.

### DELETE /blackouts/{blackout_id}
Remove blackout.

### GET /check/{system_id}
Check if a system is in a blackout period.

## Status Machine
scheduled -> in_progress -> completed
                        -> failed
                        -> cancelled (from scheduled or in_progress)
                        -> extended (from in_progress)

# Runbook Library API Reference
## Base URL: /api/v1/orchestration/runbook-templates

### GET /
List runbook templates.
**Query Parameters:** category, search, difficulty, sort_by

### GET /{template_id}
Get template with full step definitions.

### POST /{template_id}/instantiate
Create a runbook instance from template.
**Request:**
| Field | Required | Description |
|-------|----------|-------------|
| variables | yes | Template variable values |
| initiated_by | yes | User ID starting the runbook |

**Response:**
```json
{
  "instance_id": "rb_inst_001",
  "template_id": "db_rollback",
  "status": "in_progress",
  "current_step": 0,
  "total_steps": 8,
  "variables": {...},
  "steps": [
    {"step_number": 1, "description": "Verify backup exists", "status": "completed"},
    {"step_number": 2, "description": "Stop application", "status": "in_progress"},
    {"step_number": 3, "description": "Restore database from backup", "status": "pending"}
  ],
  "started_at": "2024-01-15T10:30:00Z"
}
```

### GET /instances/{instance_id}
Get instance status and progress.

### POST /instances/{instance_id}/steps/{step_number}/complete
Mark a step as complete.
**Request:** { "output": "Backup verified: size 2.3GB, checksum valid" }

### POST /instances/{instance_id}/steps/{step_number}/fail
Mark a step as failed.
**Request:** { "error": "Backup file corrupted", "resolution": "Try alternative backup" }

### GET /instances/{instance_id}/progress
Get progress summary.

### POST /{template_id}/vote
Vote on a template.
**Request:** { "user_id", "rating": 1-5 }

## Community Templates
1. **Database Rollback** - Roll back database to previous version
2. **SSL Certificate Renewal** - Renew expiring SSL certificates
3. **Incident Response** - Structured incident response workflow
4. **Vulnerability Remediation** - Patch critical vulnerabilities
5. **Backup Restore** - Restore from backup with verification
6. **Node Drain** - Safely drain Kubernetes node for maintenance
