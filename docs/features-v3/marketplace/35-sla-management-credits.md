# Feature 35: SLA Management & Credits

## Overview
Define SLAs per service tier with automatic uptime tracking, compliance monitoring, credit calculation, and customer-facing SLA dashboard.

## Components

### Integration Service: `marketplace/sla_manager.py`
- `SLAManager` - Core SLA management
  - SLA template definition (uptime %, response time, resolution time)
  - Service tier mapping (basic/business/enterprise)
  - Uptime monitoring and calculation
  - Automatic credit calculation for SLA breaches
  - Credit issuance workflow (approval + application)
  - Customer-facing SLA dashboard
  - SLA compliance reports
  - Incident SLA tracking

### Management Panel: `pages/marketplace/SLAPage.tsx`
- SLA template management
- Service tier configuration
- Uptime dashboard with status indicators
- Credit management (pending/approved/issued)
- SLA compliance reports
- Incident SLA timeline viewer

### CLI Commands
- `ipilot sla list`
- `ipilot sla create --name "Standard" --uptime 99.9`
- `ipilot sla status <service_id>`
- `ipilot sla credits <service_id>`

## API Endpoints
- `GET /api/marketplace/sla/templates` - List SLA templates
- `POST /api/marketplace/sla/templates` - Create SLA template
- `PUT /api/marketplace/sla/templates/{id}` - Update template
- `DELETE /api/marketplace/sla/templates/{id}` - Delete template
- `GET /api/marketplace/sla/services` - Services with SLA
- `GET /api/marketplace/sla/services/{id}` - Service SLA status
- `GET /api/marketplace/sla/services/{id}/uptime` - Uptime history
- `GET /api/marketplace/sla/credits` - List credits
- `POST /api/marketplace/sla/credits/calculate` - Calculate credits
- `POST /api/marketplace/sla/credits/{id}/approve` - Approve credit
- `POST /api/marketplace/sla/credits/{id}/issue` - Issue credit
- `GET /api/marketplace/sla/reports` - SLA reports

## Data Models

### SLATemplate
- id, name, description, tier (basic/business/enterprise)
- uptime_percentage (99.9, 99.99, 99.999)
- max_response_time_minutes, max_resolution_time_minutes
- credit_percentage (per 0.1% below SLA)
- credit_cap_percentage, credit_cap_amount
- exclusions (maintenance, force majeure)

### SLACompliance
- id, service_id, sla_template_id
- period_start, period_end
- uptime_percentage_actual, uptime_percentage_target
- total_downtime_seconds, total_period_seconds
- breaches_count, status (compliant/breached/partial)

### ServiceCredit
- id, service_id, sla_compliance_id
- user_id, amount, currency
- reason (uptime_breach/response_time/resolution_time)
- status (pending/approved/issued/declined)
- issued_at, applied_to_invoice

## Implementation Details
- Uptime calculation from monitoring probes
- SLA breach detection with alerting
- Credit calculation formula: max(credit_pct × breach_pct, cap)
- Automatic credit issuance based on policy
- Maintenance window exclusion handling
- Incident response time tracking
- SLA compliance percentage = (total_time - downtime) / total_time × 100
- Credit application to next invoice
- SLA compliance reports with charting
- Prometheus/grafana integration for uptime

## Testing
- Uptime calculation accuracy
- Credit calculation formulas
- SLA breach detection timing
- Maintenance exclusion logic
- Credit workflow state machine
- Compliance report generation
- Service tier mapping
