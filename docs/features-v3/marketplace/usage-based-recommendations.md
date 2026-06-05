# Feature 38: Usage-Based Recommendations

## Overview
Analyze user consumption patterns and recommend optimal plans. Smart suggestions like "You used 80% of your RAM 90% of the time — upgrading could save you 15%".

## Components

### Integration Service: `marketplace/recommendations.py`
- `UsageRecommendationEngine` - Core recommendation engine
  - Usage pattern analysis (CPU, RAM, disk, bandwidth)
  - Plan comparison with current usage
  - Savings opportunity identification
  - Upgrade/downgrade timing recommendations
  - Addon suggestion based on usage gaps
  - Periodic recommendation generation
  - User notification delivery
  - A/B testing of recommendation models

### Management Panel: `pages/marketplace/RecommendationsPage.tsx`
- Personalized recommendation cards
- Usage vs. plan comparison chart
- Savings calculator
- Recommendation history
- Dismiss/apply recommendation actions
- Recommendation settings

### CLI Commands
- `ipilot recommend analyze`
- `ipilot recommend list`
- `ipilot recommend apply <rec_id>`

## API Endpoints
- `GET /api/marketplace/recommendations` - List recommendations
- `GET /api/marketplace/recommendations/{id}` - Get recommendation
- `POST /api/marketplace/recommendations/{id}/dismiss` - Dismiss
- `POST /api/marketplace/recommendations/{id}/apply` - Apply
- `GET /api/marketplace/recommendations/analysis` - Current analysis
- `GET /api/marketplace/recommendations/settings` - Get settings
- `PUT /api/marketplace/recommendations/settings` - Update settings

## Data Models

### UsageRecommendation
- id, user_id, type (upgrade/downgrade/addon/switch)
- current_plan_id, recommended_plan_id
- confidence_score (0-100), potential_savings
- savings_currency, reasons list
- metrics_analyzed (JSON: {cpu_avg, cpu_p95, ram_avg, ...})
- status (active/dismissed/applied/expired)
- created_at, applied_at

### UsageProfile
- user_id, period_days, sample_count
- resource_usage (JSON: {
    cpu: {avg, p50, p95, p99, max},
    ram: {avg, p50, p95, p99, max},
    disk: {avg, p50, p95, p99, max},
    bandwidth: {avg, p95, p99, total}
  })
- active_hours_pattern (JSON: hourly_avg array)
- growth_rate (estimated resource growth % per month)
- analyzed_at

## Implementation Details
- Usage data aggregation from Prometheus/influxdb
- Percentile calculations (p50, p95, p99)
- Savings = (current_plan_cost - recommended_plan_cost) + addon_savings
- Confidence scoring based on data quality and pattern stability
- Resource growth trend analysis (linear regression)
- Seasonal pattern detection
- Time-of-day usage analysis for burstable plans
- Recommendation grouping and deduplication
- User notification via in-app + email
- A/B testing framework for recommendation models

## Testing
- Usage profile generation accuracy
- Savings calculation correctness
- Recommendation relevance scoring
- Percentile calculation precision
- Growth trend analysis
- Notification delivery
- Dismiss/apply workflow
