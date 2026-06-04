# Feature 84: SIEM Platform

## Overview
Security Information and Event Management platform for log collection, correlation, alerting, and compliance.

## Components
- **Data Sources**: 34 log sources (servers, network devices, cloud, apps)
- **Correlation Rules**: 78 detection rules mapping to MITRE ATT&CK
- **Alerts**: Real-time alerting with severity classification
- **Storage**: 180-day retention with hot/warm/cold tiers

## Data Models
- Source: id, name, type, status, logs_per_sec
- Alert: id, title, severity, source, rule_id, timestamp, status
- Rule: id, name, query, severity, enabled, mitre_mapping

## API Endpoints
- GET /api/soc/siem/sources - List sources
- GET /api/soc/siem/alerts - List alerts
- GET /api/soc/siem/alerts/:id - Get alert details
- POST /api/soc/siem/rules - Create rule
- PUT /api/soc/siem/rules/:id - Update rule
- DELETE /api/soc/siem/rules/:id - Delete rule
- POST /api/soc/siem/search - Execute search query

## Metrics
- Sources: 34 (32 online)
- Events/Day: 1.2B
- Alerts (24h): 156 (3 critical)
- Rules: 78 (72 enabled)
- MITRE Coverage: 62%
- Avg Query Time: 2.4s

## Discord Commands
- /siem - View SIEM summary
- /siem sources - List sources
- /siem alerts - List alerts
- /siem rules - List rules
- /siem stats - View statistics
