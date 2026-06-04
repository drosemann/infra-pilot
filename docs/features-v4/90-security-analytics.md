# Feature 90: Security Analytics

## Overview
Advanced security analytics with UEBA, dashboards, reporting, and ML-based anomaly detection for comprehensive visibility.

## Components
- **Dashboards**: 8 pre-built dashboards (Overview, Threat, Compliance, IR, Vuln Trends, User Activity)
- **Reports**: 6 scheduled report types (Executive, Threat Intel Brief, Compliance)
- **UEBA**: User and Entity Behavior Analytics with ML models
- **Metrics**: MTTD, MTTR, detection rate, false positive rate, security score

## Data Models
- Dashboard: id, name, widgets, created_by, last_modified
- Report: id, name, type, schedule, recipients, last_generated
- Anomaly: id, type, entity, score, timestamp, status
- Metric: id, name, value, unit, timestamp, entity_type

## API Endpoints
- GET /api/soc/analytics/dashboards - List dashboards
- POST /api/soc/analytics/dashboards - Create dashboard
- GET /api/soc/analytics/dashboards/:id - Get dashboard
- PUT /api/soc/analytics/dashboards/:id - Update dashboard
- DELETE /api/soc/analytics/dashboards/:id - Delete dashboard
- GET /api/soc/analytics/reports - List reports
- POST /api/soc/analytics/reports/generate - Generate report
- GET /api/soc/analytics/anomalies - List anomalies
- GET /api/soc/analytics/metrics - Get security metrics

## Metrics
- Dashboards: 8 active
- Reports: 6 scheduled (24 generated/30d)
- MTTD: 14 minutes
- MTTR: 42 minutes
- Detection Rate: 96.2%
- False Positive Rate: 11.4%
- Security Score: 82/100
- Data Points (30d): 1.2B processed

## Discord Commands
- /secanalytics - View analytics summary
- /secanalytics dashboards - List dashboards
- /secanalytics reports - List reports
- /secanalytics anomalies - View anomalies
- /secanalytics metrics - View security metrics
- /secanalytics stats - View statistics
