# Feature 29: Network Cost Analyzer

## Overview
Track bandwidth costs per provider, per region, per server. Egress cost alerts and optimization suggestions including peering recommendations and compression enablement.

## Components

### Integration Service: `networking/cost_analyzer.py`
- `NetworkCostAnalyzer` - Core network cost analysis
  - Bandwidth usage collection (per interface, per server)
  - Provider pricing model management
  - Cost calculation (per-GB, percentile-based, committed)
  - Regional cost comparison
  - Egress cost alerting
  - Optimization suggestions
  - Cost forecasting (30/60/90 day)
  - Peering cost comparison

### Management Panel: `pages/networking/CostAnalyzerPage.tsx`
- Cost dashboard with sparklines
- Per-provider cost breakdown
- Regional heatmap of bandwidth costs
- Alert configuration for cost thresholds
- Optimization suggestion cards
- Cost forecast charts
- Export cost reports (CSV/PDF)

### CLI Commands
- `ipilot network cost report --period monthly`
- `ipilot network cost analyze --server <id>`
- `ipilot network cost alert set --threshold <amount>`

## API Endpoints
- `GET /api/networking/cost/usage` - Bandwidth usage
- `GET /api/networking/cost/breakdown` - Cost breakdown
- `GET /api/networking/cost/by-provider` - Per-provider costs
- `GET /api/networking/cost/by-region` - Per-region costs
- `GET /api/networking/cost/by-server` - Per-server costs
- `GET /api/networking/cost/forecast` - Cost forecast
- `GET /api/networking/cost/alerts` - Cost alerts
- `POST /api/networking/cost/alerts` - Create cost alert
- `GET /api/networking/cost/optimizations` - Optimization suggestions
- `GET /api/networking/cost/providers` - Provider pricing models
- `POST /api/networking/cost/providers` - Add provider pricing

## Data Models

### BandwidthUsage
- id, server_id, interface_name, provider
- region, timestamp, bytes_in, bytes_out
- bytes_total, cost_in, cost_out, cost_total
- billing_period, meter_type (per_gb/percentile95/committed)

### ProviderPricing
- id, provider_name, region, service_tier
- ingress_price_per_gb, egress_price_per_gb
- committed_volume_gb, committed_price
- percentile_95_commit, percentile_95_price
- free_tier_gb, currency

### CostAlert
- id, name, metric (egress_cost/total_cost/bandwidth)
- threshold_value, threshold_direction (above/below)
- period (daily/weekly/monthly), enabled
- notification_channels, last_fired

### CostOptimization
- id, type (provider_switch/compression/peering/caching)
- description, estimated_savings_monthly
- implementation_cost, roi_months
- status (identified/in_progress/completed/dismissed)
- steps (list of action steps)

## Implementation Details
- Bandwidth collection from netdata/librenms API
- Cloud provider pricing APIs (AWS, Azure, GCP, DO, Vultr, Hetzner)
- 95th percentile calculation
- Cost allocation tags
- Prometheus metrics export for bandwidth
- Alert evaluation on schedule
- Optimization engine with rule-based suggestions
- Compression benefit estimation
- CDN caching savings calculation
- Peering cost comparison (public vs private peering)

## Testing
- Bandwidth usage collection
- Cost calculation accuracy
- Provider pricing model CRUD
- Cost alert evaluation
- Optimization suggestion relevance
- Forecast accuracy validation
- Report generation correctness
