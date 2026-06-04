# Feature 24: Real-Time Cost Anomaly Detection

## Overview
Detect unusual spending patterns in real-time using statistical, ML-based, and adaptive thresholding methods. Investigate and resolve anomalies with automated root cause analysis.

## Components
- `cost_anomaly.py` - Anomaly detection engine with multiple methods
- `cost_anomaly_cog.py` - Discord bot commands
- `CostAnomaly.tsx` - Management panel UI

## Data Models
- **Anomaly**: `id`, `service`, `amount`, `region`, `severity`, `status`, `detected_at`, `excess_amount`, `investigation`
- **Profile**: `id`, `name`, `detection_method`, `sensitivity`, `created_at`
- **IngestRecord**: `service`, `amount`, `region`, `timestamp`

## API Endpoints
- `GET /api/v1/finops/anomaly/detections` - List detections
- `GET /api/v1/finops/anomaly/summary` - Summary
- `POST /api/v1/finops/anomaly/detections/{id}/investigate` - Investigate
- `POST /api/v1/finops/anomaly/detections/{id}/resolve` - Resolve
- `GET /api/v1/finops/anomaly/profiles` - List profiles
- `POST /api/v1/finops/anomaly/profiles` - Create profile
- `POST /api/v1/finops/anomaly/ingest` - Ingest spend record

## CLI Usage
- `ipilot finops anomaly list --severity high`
- `ipilot finops anomaly summary`
- `ipilot finops anomaly investigate <anomaly_id>`
- `ipilot finops anomaly resolve <anomaly_id>`
- `ipilot finops anomaly profiles`
- `ipilot finops anomaly create-profile <name> --method zscore --sensitivity 2.0`
- `ipilot finops anomaly ingest <service> <amount> --region us-east-1`

## Configuration
```yaml
cost_anomaly:
  detection_methods: [zscore, mad, iqr, adaptive]
  default_sensitivity: 2.0
  evaluation_window_minutes: 5
  alert_on_severity: [critical, high]
  auto_resolve_after_hours: 72
```

## Example
```bash
ipilot finops anomaly ingest EC2 15200 --region us-east-1
ipilot finops anomaly list --severity critical
# Shows critical anomalies requiring immediate attention
```
