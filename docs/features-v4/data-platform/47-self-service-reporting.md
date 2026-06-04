# Feature 47: Self-Service Reporting

## Overview
Drag-and-drop report builder with visual and SQL modes, interactive widgets, scheduled delivery, and multi-format export for business users.

## Components
- `self_service_reporting.py` - Report builder with execution and scheduling
- `cog_self_service_reporting.py` - Discord bot commands for reporting operations

## Data Models
- Report - Report with name, description, widgets list, parameters, mode (visual/sql)
- Widget - Widget with type (chart/table/metric), query, visualization config
- Schedule - Schedule with frequency, recipients, format, enabled flag

## API Endpoints
- `GET /api/v4/data/reports` - List reports
- `POST /api/v4/data/reports` - Create report
- `POST /api/v4/data/reports/:id/execute` - Execute report
- `POST /api/v4/data/reports/:id/export` - Export report
- `POST /api/v4/data/reports/:id/schedules` - Schedule report

## Metrics
- Reports created
- Scheduled deliveries
- Export formats used

## Discord Commands
- `/report list` - List reports
- `/report create` - Create report
- `/report execute` - Run report
- `/report export` - Export report
- `/report schedule` - Schedule recurring delivery
