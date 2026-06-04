# Feature 34: Chaos Recovery Validation

## Overview
Scheduled chaos experiments that validate DR procedures. Kill the primary database — does failover complete within RTO?

## Components
- `chaos_validation.py` - Experiment lifecycle, fault injection, DR response measurement
- `ChaosValidationCog` - Discord commands with scheduler
- `ChaosValidation.tsx` - Management panel UI

## API Endpoints
- `GET /api/v1/resiliency/chaos/experiments` - List experiments
- `POST /api/v1/resiliency/chaos/experiments` - Create experiment
- `POST /api/v1/resiliency/chaos/experiments/{id}/run` - Run experiment
- `GET /api/v1/resiliency/chaos/dashboard` - Dashboard summary
