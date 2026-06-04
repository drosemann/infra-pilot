# Feature 30: FinOps Reporting & Compliance

## Overview
Generate comprehensive FinOps reports including executive summaries, cost breakdowns, savings opportunities, budget vs actual, showback/chargeback, and compliance dashboards.

## Components
- `finops_reporting.py` - Report generation and compliance engine
- `finops_reporting_cog.py` - Discord bot commands
- `FinOpsReporting.tsx` - Management panel UI

## Data Models
- **Report**: `id`, `report_type`, `period`, `status`, `generated_at`, `download_url`
- **Allocation**: `id`, `tag_key`, `tag_value`, `cost_pct`, `team`, `project`
- **Dashboard**: KPI data and chart data for pre-built dashboard views

## API Endpoints
- `GET /api/v1/finops/reports` - List reports
- `POST /api/v1/finops/reports/generate` - Generate report
- `GET /api/v1/finops/reports/summary` - Reports summary
- `GET /api/v1/finops/reports/{id}` - Get report
- `GET /api/v1/finops/reports/dashboard/{type}` - Get dashboard
- `GET /api/v1/finops/reports/allocations` - List allocations
- `POST /api/v1/finops/reports/allocations` - Create allocation

## CLI Usage
- `ipilot finops reports list`
- `ipilot finops reports summary`
- `ipilot finops reports generate <type> --period monthly`
- `ipilot finops reports get <report_id>`
- `ipilot finops reports dashboard --type kpi_dashboard`
- `ipilot finops reports allocation --team engineering`
- `ipilot finops reports create-allocation <tag_key> <tag_value> <cost_pct> --team engineering`

## Configuration
```yaml
finops_reporting:
  report_types: [executive_summary, cost_breakdown, savings_opportunity, budget_vs_actual, showback, chargeback, commitment_utilization, waste_analysis, forecast, compliance, kpi_dashboard]
  default_period: monthly
  auto_generate: [weekly, monthly]
  compliance_standards: [iso_27001, soc2, pci_dss]
  allocation_method: proportional
```

## Example
```bash
ipilot finops reports generate executive_summary --period monthly
ipilot finops reports dashboard --type kpi_dashboard
# Returns pre-built dashboard with KPIs and chart data
```
