# Feature 21: Commitment Discount Optimizer

## Overview
Analyze usage patterns and recommend optimal Reserved Instances / Savings Plans across AWS, Azure, and GCP. Track utilization, identify coverage gaps, and automate commitment purchases.

## Components
- `commitment_optimizer.py` - Core discount optimization engine with usage analysis, recommendation generation, and implementation automation
- `commitment_optimizer_cog.py` - Discord bot commands for commitment management
- `CommitmentOptimizer.tsx` - Management panel UI with coverage heatmap, gap analysis, savings projection

## Data Models
- **Recommendation**: `id`, `provider`, `commitment_type`, `term`, `upfront_cost`, `monthly_cost`, `estimated_savings`, `coverage_pct`, `status`, `risk_level`
- **Commitment**: `id`, `provider`, `type`, `term`, `start_date`, `end_date`, `monthly_cost`, `coverage_pct`, `utilization_pct`, `status`
- **CoverageGap**: `service`, `coverage_pct`, `gap_pct`, `potential_savings`, `recommended_action`

## API Endpoints
- `GET /api/v1/finops/commitment/recommendations` - List recommendations
- `POST /api/v1/finops/commitment/recommendations` - Create recommendation
- `POST /api/v1/finops/commitment/recommendations/{id}/implement` - Implement
- `GET /api/v1/finops/commitment/summary` - Summary statistics
- `GET /api/v1/finops/commitment/commitments` - Active commitments
- `POST /api/v1/finops/commitment/analyze` - Analyze usage patterns
- `GET /api/v1/finops/commitment/coverage-gaps` - Coverage gaps

## CLI Usage
- `ipilot finops commitment list` - List recommendations
- `ipilot finops commitment summary` - Summary
- `ipilot finops commitment implement <rec_id>` - Implement
- `ipilot finops commitment commitments` - Active commitments
- `ipilot finops commitment analyze` - Analyze usage
- `ipilot finops commitment coverage` - Coverage gaps

## Configuration
```yaml
commitment_optimizer:
  providers: [aws, azure, gcp]
  min_savings_threshold: 0.1
  max_recommendations: 50
  auto_implement: false
  analysis_window_days: 90
  risk_tolerance: medium
```

## Example
```bash
ipilot finops commitment list
# Output: table of recommendations with provider, type, term, savings

ipilot finops commitment implement rec-abc123
# Confirms implementation of commitment recommendation
```
