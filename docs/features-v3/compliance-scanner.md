# Feature 66: Compliance Scanner

## Overview
Automated compliance scanning against CIS benchmarks, NIST 800-53, and BSI Grundschutz standards for infrastructure hardening assessment.

## Components
- `compliance_scanner.py` - Core scanning engine
- `cis_benchmarks.py` - CIS benchmark checks
- `nist_checks.py` - NIST 800-53 control checks
- `bsi_checks.py` - BSI Grundschutz checks
- `scan_scheduler.py` - Scheduled scan management
- `compliance_routes.py` - API endpoints
- `ComplianceScanner` - Manager class

## Supported Standards
- CIS Benchmarks for Linux, Docker, Kubernetes, PostgreSQL, Nginx
- NIST SP 800-53 (moderate baseline)
- BSI IT-Grundschutz (module INF.1, SYS.1.3, NET.1.1, APP.3.7)
- Custom compliance frameworks

## Scan Types
- `full` - Complete compliance scan
- `incremental` - Changed resources only
- `scheduled` - Cron-based recurring scans
- `on-demand` - Triggered by events

## API Endpoints
- `POST /api/v1/compliance/scan` - Trigger scan
- `GET /api/v1/compliance/scan/{id}` - Get scan results
- `GET /api/v1/compliance/scans` - List scans
- `GET /api/v1/compliance/report/{scan_id}` - Generate report
- `GET /api/v1/compliance/standards` - List supported standards
- `GET /api/v1/compliance/status` - Overall compliance status
- `GET /api/v1/compliance/waivers` - List active waivers
- `POST /api/v1/compliance/waivers` - Create waiver

## Compliance Report Format
```json
{
  "scan_id": "uuid",
  "standard": "CIS_Docker_1.6",
  "timestamp": "2025-01-01T00:00:00Z",
  "summary": {
    "total_checks": 120,
    "passed": 95,
    "failed": 15,
    "waived": 10,
    "compliance_score": 79.2
  },
  "results": [
    {
      "check_id": "CIS_DOCKER_1.2.1",
      "description": "Ensure container hostname is set",
      "status": "passed",
      "severity": "medium",
      "remediation": "docker run --hostname '...'"
    }
  ]
}
```
