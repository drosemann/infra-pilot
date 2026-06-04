# Feature 27: Cloud Waste Detection

## Overview
Identify idle, underutilized, and orphaned cloud resources. Categorize waste by type and severity, and take automated remediation actions.

## Components
- `waste_detection.py` - Waste detection scanning engine
- `waste_detection_cog.py` - Discord bot commands
- `WasteDetection.tsx` - Management panel UI

## Data Models
- **Finding**: `id`, `category`, `resource`, `estimated_waste`, `severity`, `status`, `description`
- **WasteSummary**: `total`, `total_waste`, `categories` breakdown

## API Endpoints
- `GET /api/v1/finops/waste/findings` - List findings (with optional `category`, `severity`)
- `GET /api/v1/finops/waste/summary` - Summary
- `POST /api/v1/finops/waste/scan` - Run waste scan
- `POST /api/v1/finops/waste/findings/{id}/approve` - Approve cleanup
- `POST /api/v1/finops/waste/findings/{id}/cleanup` - Execute cleanup
- `POST /api/v1/finops/waste/findings/{id}/dismiss` - Dismiss finding

## CLI Usage
- `ipilot finops waste list --category idle_resources --severity high`
- `ipilot finops waste summary`
- `ipilot finops waste scan`
- `ipilot finops waste approve <finding_id>`
- `ipilot finops waste cleanup <finding_id>`
- `ipilot finops waste dismiss <finding_id>`

## Configuration
```yaml
waste_detection:
  scan_schedule: daily
  categories: [idle_resources, unattached_storage, over_provisioned, orphaned_resources]
  auto_cleanup_threshold: 50
  min_waste_for_alert: 100
  excluded_resource_types: []
```

## Example
```bash
ipilot finops waste scan
# Scans for waste and returns findings
ipilot finops waste list --severity high
# Shows high-severity waste findings
```
