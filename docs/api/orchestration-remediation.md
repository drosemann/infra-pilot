# Drift Detector API Reference
## Overview
Detect configuration drift between desired state (IaC/config files) and actual runtime state.

## Base URL: /api/v1/orchestration/drift

### POST /scan
Run a drift scan across all resource types.
**Response:**
```json
{
  "scan_id": "ds_abc123",
  "total_resources": 45,
  "drifted_resources": 7,
  "compliant_resources": 38,
  "compliance_pct": 84.4,
  "drifts": [
    {
      "drift_id": "d_001",
      "resource_id": "container:web-01",
      "resource_type": "container",
      "field": "memory_limit",
      "expected": "512m",
      "actual": "1g",
      "severity": "medium",
      "status": "open",
      "detected_at": "2024-01-15T10:30:00Z"
    }
  ],
  "scanned_at": "2024-01-15T10:30:00Z"
}
```

### GET /scans
List scan history.

### GET /scans/{scan_id}
Get scan results with drift details.

### GET /drifts
List all drifts. Query: severity, status, resource_type

### GET /drifts/{drift_id}
Get drift details.

### POST /drifts/{drift_id}/suppress
Suppress a drift alert.
**Request:** { "reason": "Planned change, will be resolved in next deploy" }

### POST /drifts/{drift_id}/unsuppress
Remove suppression.

### GET /suppressions
List active suppressions.

# Resource Quota Management API Reference
## Base URL: /api/v1/orchestration/quotas

### POST /
Create a resource quota.
**Request:**
| Field | Required | Description |
|-------|----------|-------------|
| name | yes | Quota name |
| entity_type | yes | org/team/project |
| entity_id | yes | Entity identifier |
| limits | yes | Resource limits object |
| enforcement_mode | no | hard/soft/audit (default: hard) |

**Limits Schema:**
```json
{
  "cpu_cores": 32,
  "memory_gb": 128,
  "containers": 50,
  "storage_gb": 2000,
  "gpu_units": 4,
  "load_balancers": 10,
  "static_ips": 20,
  "snapshots": 50,
  "backup_storage_gb": 500,
  "network_bandwidth_mbps": 10000
}
```

### GET /
List quotas. Query: entity_type, entity_id

### GET /{quota_id}
Get quota details with current usage.

### PUT /{quota_id}
Update quota limits.

### DELETE /{quota_id}
Delete quota.

### POST /check
Check if a resource request is within quota.
**Request:** { "entity_type", "entity_id", "resources": { "cpu_cores": 4, "memory_gb": 16 } }
**Response:** { "allowed": true/false, "exceeded": ["cpu_cores"], "current_usage": {...}, "limits": {...} }

### POST /usage
Track resource usage against quota.
**Request:** { "entity_type", "entity_id", "resources": { "cpu_cores": 2 } }

### POST /increase
Request a quota increase.
**Request:** { "entity_type", "entity_id", "new_limits": {...}, "reason": "string" }
**Response:** { "request_id", "status": "pending" }

### POST /increase/{request_id}/approve
Approve increase request.
**Request:** { "approver_id": "admin-001" }

### POST /increase/{request_id}/deny
Deny increase request.
**Request:** { "approver_id": "admin-001", "reason": "Not enough capacity" }

## Enforcement Modes
| Mode | Description |
|------|-------------|
| hard | Deny requests that exceed quota |
| soft | Allow but warn when quota exceeded |
| audit | Log overages but allow |

# Auto-Remediation API Reference
## Base URL: /api/v1/orchestration/remediation

### POST /rules
Create remediation rule.
**Request:** { "name", "description", "trigger_type", "condition", "action_type", "action_config", "cooldown_seconds" }

**Trigger Types:** container_health, cpu_high, memory_high, disk_space, crash_loop, ssl_expiry

**Action Types:** container_restart, scale_up, scale_down, memory_cleanup, disk_cleanup, certificate_renew, kill_container

### GET /rules
List remediation rules.

### GET /rules/{rule_id}
Get rule details.

### PUT /rules/{rule_id}
Update rule.

### DELETE /rules/{rule_id}
Delete rule.

### POST /rules/{rule_id}/enable
Enable rule.

### POST /rules/{rule_id}/disable
Disable rule.

### POST /evaluate
Manually evaluate rules against context.
**Request:** { "trigger_type": "cpu_high", "context": {...} }
**Response:** { "triggered": true, "action": "scale_up", "execution_id": "exec_001" }

### GET /history
List remediation action history.

### GET /history/{execution_id}
Get execution details.

### GET /templates
List built-in rule templates.

## Rule Templates
1. Container Restart: Restart unhealthy containers
2. Scale Up Service: Scale up when CPU > 80%
3. Memory Leak Detection: Restart on memory growth
4. Crash Loop Backoff: Exponential backoff restart
5. Disk Cleanup: Remove old logs/cache
6. SSL Certificate Renewal: Auto-renew expiring certs
