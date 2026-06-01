# Feature 67: Audit Trail Analytics

## Overview
Anomaly detection engine on audit logs using statistical analysis, machine learning, and rule-based detection for identifying suspicious patterns.

## Components
- `audit_analytics.py` - Core analytics engine
- `anomaly_detector.py` - ML-based anomaly detection
- `audit_routes.py` - API endpoints
- `AuditAnalyticsManager` - Manager class
- `audit_dashboard.tsx` - React dashboard for audit analytics

## Detection Methods
- **Statistical**: Standard deviation, z-score, moving averages
- **ML-based**: Isolation Forest, Local Outlier Factor, One-Class SVM
- **Rule-based**: Threshold alerts, pattern matching, sequence detection
- **Temporal**: Time-series analysis, seasonal decomposition

## Analyzed Patterns
- Failed login spikes
- Unusual access times
- Privilege escalation patterns
- Data exfiltration indicators
- Impossible travel
- API abuse patterns
- Configuration drift events

## API Endpoints
- `GET /api/v1/audit/analytics/overview` - Analytics overview
- `GET /api/v1/audit/analytics/anomalies` - Detected anomalies
- `GET /api/v1/audit/analytics/anomalies/{id}` - Anomaly details
- `POST /api/v1/audit/analytics/run` - Run analysis
- `GET /api/v1/audit/analytics/trends` - Trend analysis
- `GET /api/v1/audit/analytics/correlations` - Event correlations
- `GET /api/v1/audit/analytics/patterns` - User behavior patterns

## Anomaly Severity Levels
- `critical` - Immediate attention needed
- `high` - Likely security incident
- `medium` - Suspicious activity
- `low` - Behavioral anomaly
- `info` - Notable event

## Visualization
- Anomaly timeline with severity heatmap
- User behavior baseline comparison
- Correlation graph of related events
- Trend forecasts for key metrics
