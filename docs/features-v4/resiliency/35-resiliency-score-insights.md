# Feature 35: Resiliency Score & Insights

## Overview
Score every service on resiliency across 8 dimensions: redundancy, backup coverage, DR tested, circuit breakers, auto-scaling, load balancing, monitoring, chaos validation.

## Components
- `resiliency_scoring.py` - Scoring engine with dimension weights and recommendations
- `ResiliencyScoringCog` - Discord scoring commands
- `ResiliencyScore.tsx` - Management panel UI

## Scoring Dimensions
- Redundancy (multi-AZ, replicas)
- Backup coverage and RPO/RTO adherence
- DR plan existence and testing frequency
- Circuit breaker configuration
- Auto-scaling capability
- Load balancing and distribution
- Monitoring and alerting coverage
- Chaos engineering validation

## API Endpoints
- `POST /api/v1/resiliency/score/{service_id}` - Score a service
- `GET /api/v1/resiliency/scores` - List all scores
- `GET /api/v1/resiliency/scores/org-summary` - Organization summary
