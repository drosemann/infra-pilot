# PAM (Privileged Access Management) API Reference
## Overview
Just-in-Time (JIT) privileged access with approval workflows, break-glass emergency access, and session recording.

## Base URL: /api/v1/identity/pam

### POST /requests
Create a new privileged access request.
**Request:**
| Field | Required | Type | Description |
|-------|----------|------|-------------|
| user_id | yes | string | Requester user ID |
| resource | yes | string | Target resource identifier |
| role | yes | string | Requested role/privilege level |
| reason | yes | string | Business justification |
| duration | no | int | Requested duration in seconds |
| ip_address | yes | string | Requester IP address |
| additional_approvers | no | string[] | Additional approver IDs |

**Response:**
```json
{
  "request_id": "req_abc123",
  "user_id": "user-001",
  "resource": "prod-db-01",
  "role": "db_admin",
  "status": "pending",
  "created_at": "2024-01-15T10:30:00Z",
  "expires_at": "2024-01-15T11:30:00Z",
  "duration": 3600
}
```

### GET /requests
List access requests with filters.
**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| user_id | string | Filter by requester |
| status | string | pending/approved/denied/cancelled |
| resource | string | Filter by resource |

### GET /requests/{request_id}
Get a specific request with approval history.

### POST /requests/{request_id}/cancel
Cancel a pending request.

### POST /requests/{request_id}/approve
Approve an access request.
**Request:**
| Field | Required | Description |
|-------|----------|-------------|
| approver_id | yes | Approver user ID |
| reason | no | Approval justification |

### POST /requests/{request_id}/deny
Deny an access request.
**Request:**
| Field | Required | Description |
|-------|----------|-------------|
| approver_id | yes | Approver user ID |
| reason | no | Denial reason |

### POST /requests/{request_id}/jit/activate
Activate JIT access after approval.
**Request:**
| Field | Required | Description |
|-------|----------|-------------|
| ip_address | yes | Activation source IP |

### POST /requests/{request_id}/jit/deactivate
Deactivate JIT access.
**Response:**
```json
{
  "status": "expired",
  "deactivated_at": "2024-01-15T11:30:00Z"
}
```

## Break Glass Endpoints

### POST /break-glass
Trigger emergency break-glass access.
**Request:**
| Field | Required | Description |
|-------|----------|-------------|
| user_id | yes | User ID |
| resource | yes | Target resource |
| reason | yes | Emergency justification |
| ip_address | yes | Source IP |

**Response:**
```json
{
  "access_id": "bg_xyz789",
  "status": "active",
  "expires_at": "2024-01-15T11:00:00Z",
  "incident_reported": true,
  "notifications_sent": true
}
```

### POST /break-glass/{access_id}/revoke
Revoke break-glass access.

### GET /break-glass/history
List break-glass access history.

## Session Recording Endpoints

### POST /recordings/start
Start recording a session.
**Request:**
| Field | Required | Description |
|-------|----------|-------------|
| user_id | yes | User being recorded |
| resource | yes | Target resource |
| protocol | yes | ssh/rdp/kubectl/etc |
| ip_address | yes | Source IP |

### POST /recordings/{session_id}/write
Write an event to the recording.
**Request:**
| Field | Required | Description |
|-------|----------|-------------|
| data | yes | Input/output data |
| event_type | yes | input/output/resize |

### POST /recordings/{session_id}/stop
Stop recording.

### GET /recordings/{session_id}
Get recording with playback data (asciicast format v2).

### GET /recordings/user/{user_id}
List recordings for a user.

## Approval Workflows
1. Single approver: Default, one approval needed
2. Multi-approver: Multiple approvals required (configurable threshold)
3. Escalation: Auto-escalate after timeout
4. Break-glass: Bypass approval with incident notification
5. Time-based: Auto-expire JIT access after duration
6. Self-approval prevention: Users cannot approve own requests
