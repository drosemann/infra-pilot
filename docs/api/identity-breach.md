# Breach Notification (GDPR) API Reference
## Overview
End-to-end breach management lifecycle: detection, containment, investigation, notification, and resolution. Compliant with GDPR Articles 33 and 34.

## Base URL: /api/v1/identity/breaches

### POST /
Report a new data breach.
**Request:**
| Field | Required | Type | Description |
|-------|----------|------|-------------|
| detected_by | yes | string | Detecting user/system |
| description | yes | string | Breach description |
| affected_data_types | yes | string[] | Types of data affected |
| affected_users_count | yes | int | Number of affected subjects |
| suspected_cause | yes | string | Suspected root cause |
| systems_affected | yes | string[] | Affected system IDs |

**Response:**
```json
{
  "breach_id": "br_001234",
  "status": "detected",
  "severity": "critical",
  "detected_at": "2024-01-15T10:30:00Z",
  "gdpr_72h_deadline": "2024-01-18T10:30:00Z",
  "affected_users_count": 1250,
  "affected_data_types": ["pii", "credentials"],
  "suspected_cause": "phishing_attack",
  "notifications_sent": 0,
  "is_escalated": true
}
```

### GET /
List breaches with filters.
**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| status | string | detected/investigating/contained/resolved |
| severity | string | low/medium/high/critical |
| from_date | string | ISO date filter start |
| to_date | string | ISO date filter end |

### GET /{breach_id}
Get breach details, timeline, evidence, and notifications.

### PATCH /{breach_id}/status
Update breach status.
**Request:** { "status": "investigating" }

### PATCH /{breach_id}/severity
Update breach severity.
**Request:** { "severity": "high" }

### POST /{breach_id}/contain
Contain a breach with specific actions.
**Request:**
| Field | Required | Description |
|-------|----------|-------------|
| actions | yes | Array of containment actions |
| notes | no | Containment notes |

### POST /{breach_id}/resolve
Mark breach as resolved.
**Request:**
| Field | Required | Description |
|-------|----------|-------------|
| root_cause | yes | Identified root cause |
| remediation | yes | Applied remediation |

### POST /{breach_id}/timeline
Add timeline entry.
**Request:**
| Field | Required | Description |
|-------|----------|-------------|
| description | yes | Entry description |
| entry_type | yes | detection/investigation/containment/notification/resolution |
| author | yes | Author user ID |

### GET /{breach_id}/timeline
Get full investigation timeline.

### POST /{breach_id}/evidence
Add evidence file reference.
**Request:**
| Field | Required | Description |
|-------|----------|-------------|
| file_name | yes | Evidence file name |
| file_type | yes | File type/category |
| metadata | no | Additional context |

### GET /{breach_id}/evidence
List all evidence.

### POST /{breach_id}/notify/authority
Send Article 33 notification to supervisory authority.
**Request:**
| Field | Required | Description |
|-------|----------|-------------|
| authority_name | yes | Authority name |
| authority_email | yes | Authority contact email |
| notification_body | yes | Notification content |

### POST /{breach_id}/notify/subjects
Send Article 34 notification to affected subjects.
**Request:**
| Field | Required | Description |
|-------|----------|-------------|
| subject_count | yes | Number of subjects |
| notification_body | yes | Notification content |
| method | yes | email/sms/in-app |
| contact_details | no | Contact info for delivery |

### GET /{breach_id}/notifications
Get notification history.

### GET /{breach_id}/report
Generate comprehensive breach report.

### GET /{breach_id}/deadline
Check GDPR 72-hour notification deadline status.

## Severity Classification
| Score | Severity | Criteria |
|-------|----------|----------|
| 0-3 | low | <100 users, non-sensitive data |
| 4-6 | medium | 100-1000 users, some sensitive data |
| 7-8 | high | 1000-10000 users, PII/PHI involved |
| 9-10 | critical | >10000 users, financial/health data |

## Escalation Rules
1. Automatic escalation after 48 hours without containment
2. Critical severity always escalates
3. High severity escalates if >1000 affected users
4. Escalation notifies: CISO, Legal, Compliance team
5. Board notification for critical breaches
