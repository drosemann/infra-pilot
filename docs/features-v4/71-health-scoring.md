# Feature 71: Customer Health Scoring

## Overview
Composite health scoring system that aggregates usage, billing, support, uptime, sentiment, and adoption data into a single health score. Predicts churn risk and triggers proactive outreach.

## Components
- `health_scoring.py` - Core health scoring service with churn prediction
- `cx_cogs.py` - HealthScoringCog Discord commands

## Data Models
- `HealthProfile` - Customer health with score (0-100), risk level, trend indicators
- `HealthHistory` - Historical score snapshots for trend analysis

## API Endpoints
- `GET /api/v1/cx/health/profile` - List health profiles
- `GET /api/v1/cx/health/profile/{customer_id}` - Get profile
- `POST /api/v1/cx/health/compute/{customer_id}` - Compute health score
- `GET /api/v1/cx/health/history/{customer_id}` - Get score history
- `GET /api/v1/cx/health/stats` - Segment summary

## Metrics
- Composite health score (weighted: usage 20%, billing 20%, support 25%, uptime 15%, sentiment 10%, adoption 10%)
- Churn probability estimation
- Segment distribution (healthy/at_risk/churning)
