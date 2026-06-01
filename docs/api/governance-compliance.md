# Compliance Scanner API Reference
## Overview
Automated compliance scanning against CIS Docker, CIS Kubernetes, NIST 800-53, and BSI Grundschutz benchmarks.

## Base URL: /api/v1/governance/compliance

### POST /scan
Run a compliance scan.
**Request:**
| Field | Required | Type | Description |
|-------|----------|------|-------------|
| benchmarks | no | string[] | Benchmarks to run (default: all enabled) |
| apply_waivers | no | boolean | Apply active waivers (default: true) |

**Response:**
```json
{
  "scan_id": "scan_abc123",
  "benchmark": "cis_docker",
  "status": "completed",
  "total_checks": 32,
  "passed": 28,
  "failed": 3,
  "warning": 1,
  "error": 0,
  "compliance_score": 87.5,
  "passed_percentage": 87.5,
  "started_at": "2024-01-15T10:30:00Z",
  "completed_at": "2024-01-15T10:30:05Z",
  "duration_ms": 5234
}
```

### GET /scans
List scan history.
**Query Parameters:** limit (default: 20), benchmark, status

### GET /scans/{scan_id}
Get scan details with individual check results.

### GET /checks
List available compliance checks.
**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| benchmark | string | Filter by benchmark |
| severity | string | Filter by severity |
| category | string | Filter by category |

### GET /checks/{check_id}
Get specific check details.

### POST /waivers
Add a compliance check waiver.
**Request:**
| Field | Required | Description |
|-------|----------|-------------|
| check_id | yes | Check to waive |
| reason | yes | Waiver justification |
| created_by | yes | Creator user ID |
| expires_in_days | no | Expiration in days (default: 90) |

### GET /waivers
List active waivers.

### DELETE /waivers/{waiver_id}
Revoke a waiver.

### GET /report/{scan_id}
Generate a formatted compliance report.
**Query Parameters:** include_recommendations (boolean)

## Benchmarks

### CIS Docker Benchmark (32 checks)
- 1.x: Host Configuration (7 checks)
- 2.x: Docker Daemon Configuration (5 checks)
- 3.x: Docker Daemon Files (3 checks)
- 4.x: Container Images (4 checks)
- 5.x: Container Runtime (8 checks)
- 6.x: Docker Security Operations (3 checks)
- 7.x: Docker Swarm (2 checks)

### CIS Kubernetes Benchmark (25 checks)
- 1.x: Control Plane (8 checks)
- 2.x: Worker Nodes (5 checks)
- 3.x: Network Policies (4 checks)
- 4.x: Pod Security (5 checks)
- 5.x: Logging and Monitoring (3 checks)

### NIST 800-53 (50+ checks)
- AC: Access Control (8 checks)
- AU: Audit and Accountability (5 checks)
- CM: Configuration Management (4 checks)
- IA: Identification and Authentication (5 checks)
- SC: System and Communications Protection (6 checks)
- SI: System and Information Integrity (7 checks)
- CP: Contingency Planning (3 checks)
- IR: Incident Response (4 checks)
- RA: Risk Assessment (2 checks)
- CA: Security Assessment (3 checks)
- PL: Planning (2 checks)
- AT: Awareness and Training (2 checks)
- MA: Maintenance (2 checks)
- MP: Media Protection (2 checks)
- PE: Physical Protection (2 checks)
- SA: System Acquisition (2 checks)

### BSI Grundschutz (25 checks)
- 1.x: Information Security Management (6 checks)
- 2.x: Personnel (4 checks)
- 3.x: Organization (4 checks)
- 4.x: Identity and Access (5 checks)
- 5.x: Network Security (3 checks)
- 6.x: Application Security (3 checks)

## Audit Analytics API Reference
## Base URL: /api/v1/governance/audit

### POST /events
Ingest audit events (single or batch).
**Single:** { "user_id", "action", "details", "ip_address" }
**Batch:** [{ "user_id", "action", ... }, ...]

### GET /events
Search audit events.
**Query Parameters:** user_id, action, from_date, to_date, page, limit

### GET /events/{event_id}
Get specific event details.

### GET /anomalies
List detected anomalies.
**Query Parameters:** threshold (default: 0.7), severity, user_id, limit

### GET /anomalies/trend/{user_id}
Get anomaly trend for a user.

### GET /anomalies/travel
Detect impossible travel events.

### GET /summary
Get audit summary statistics.

### GET /users/{user_id}/baseline
Get user behavior baseline.

### GET /users/{user_id}/report
Generate user audit report.

### GET /correlate/ip/{ip_address}
Find all events correlated by IP address.

### GET /correlate/action/{action}
Find all events with a specific action.

## Anomaly Detection Methods
1. **Isolation Forest**: Unsupervised ML for outlier detection
2. **Statistical Analysis**: Z-score based deviation detection
3. **Impossible Travel**: Geographic velocity calculation
4. **User Baseline**: Behavior pattern comparison
5. **Peer Comparison**: Cross-user anomaly comparison
6. **Time Series Analysis**: Temporal pattern deviation

## Data Classification API Reference
## Base URL: /api/v1/governance/classify

### POST /scan
Scan text for sensitive data patterns.
**Request:** { "text": "string", "min_confidence": 0.5 }
**Response:** { "scan_id", "classification", "findings": [...], "confidence" }

### POST /scan/file
Scan file content for sensitive data.
**Request:** { "file_name": "string", "content": "base64", "content_type": "string" }

### GET /inventory
List classified data inventory.

### POST /inventory
Add item to data inventory.
**Request:** { "path", "category", "classification", "patterns" }

### PUT /inventory/{item_id}
Update inventory item.

### DELETE /inventory/{item_id}
Remove inventory item.

### POST /scan/database
Scan database table for sensitive columns.
**Request:** { "table_name": "string", "rows": [{...}] }

## Pattern Types
- **PII**: email, phone, ssn, passport, driver_license, ip_address
- **PHI**: medical_record, health_insurance, diagnosis_code
- **PCI**: credit_card, bank_account, bank_routing
- **Credentials**: api_key, password, aws_access_key, jwt_token, private_key
- **Financial**: bank_account, credit_card, routing_number
