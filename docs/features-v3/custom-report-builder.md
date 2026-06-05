# Feature 82: Custom Report Builder

## Overview
Drag-and-drop report designer with scheduled delivery to email, Slack, Discord, and webhooks.

## Components
- Visual report designer with canvas
- Draggable widgets: charts, tables, metrics, text blocks
- Data source selection and filtering
- Report scheduling (one-time, daily, weekly, monthly, cron)
- Delivery channels: email, Slack, Discord, webhook, PDF export
- Template library with pre-built templates
- CSV/Excel/PDF export formats

## Backend API
- `POST /api/reports/designs` - create report design
- `GET /api/reports/designs` - list designs
- `PUT /api/reports/designs/:id` - update design
- `DELETE /api/reports/designs/:id` - delete design
- `POST /api/reports/generate` - generate report now
- `POST /api/reports/schedules` - create schedule
- `GET /api/reports/schedules` - list schedules
- `DELETE /api/reports/schedules/:id` - delete schedule
- `GET /api/reports/deliveries` - view delivery history

## Widget Types
- Line chart, bar chart, pie chart, area chart
- Data table with sorting/filtering
- Metric cards (single number with trend)
- Text/HTML block
- Image block
- Status indicator
