# Session & Device Management API Reference
## Overview
Session management with device fingerprinting, GeoIP tracking, anomaly detection, and activity logging.

## Base URL: /api/v1/identity/sessions

### POST /create
Create a new session with device fingerprint.
**Request:**
| Field | Required | Type | Description |
|-------|----------|------|-------------|
| user_id | yes | string | User identifier |
| ip_address | yes | string | Client IP address |
| user_agent | yes | string | Browser user agent |
| fingerprint_data | yes | object | Device fingerprint data |

**Response:**
```json
{
  "session_id": "sess_abc123",
  "user_id": "user-001",
  "created_at": "2024-01-15T10:30:00Z",
  "expires_at": "2024-01-16T10:30:00Z",
  "is_active": true,
  "is_suspicious": false,
  "anomaly_score": 0.05,
  "device_name": "Chrome on Windows",
  "location": {"city": "New York", "country": "US"},
  "ip_address": "203.0.113.42"
}
```

### GET /{session_id}
Get session details.
**Response:** Returns full session object with activity log.

### POST /{session_id}/activity
Log a session activity event.
**Request:**
| Field | Required | Type | Description |
|-------|----------|------|-------------|
| activity_type | yes | string | Type of activity |
| details | no | object | Activity context data |

### GET /{session_id}/activities
List all activities for a session.

### POST /{session_id}/revoke
Revoke/end a session.
**Request:**
| Field | Required | Description |
|-------|----------|-------------|
| reason | no | Revocation reason |

### GET /user/{user_id}
List all active sessions for a user.

### POST /user/{user_id}/revoke-all
Revoke all active sessions for a user (e.g., password change).

## Fingerprint Endpoints

### POST /fingerprints
Register a device fingerprint.
**Request:**
| Field | Required | Description |
|-------|----------|-------------|
| user_id | yes | User ID |
| fingerprint_data | yes | Device characteristics |

### PUT /fingerprints/{fp_id}/trust
Mark a fingerprint as trusted (skip MFA on next login).

### DELETE /fingerprints/{fp_id}
Remove a device fingerprint.

### GET /fingerprints/user/{user_id}
List all fingerprints for a user.

## GeoIP Endpoints

### POST /geoip
Record a GeoIP location for a user session.
**Request:**
| Field | Required | Description |
|-------|----------|-------------|
| user_id | yes | User ID |
| ip_address | yes | IP address to look up |
| location_data | yes | Location info |

### GET /geoip/{user_id}/last
Get the last known location for a user.

## Session Security
1. Enforce maximum sessions per user (configurable)
2. Detect impossible travel (geographic anomalies)
3. Flag new device logins as suspicious
4. Calculate risk scores based on multiple factors
5. Support session revocation from any client
6. Auto-expire idle sessions after configurable timeout
7. Require re-authentication for sensitive operations
8. Log all session activities for audit trails
