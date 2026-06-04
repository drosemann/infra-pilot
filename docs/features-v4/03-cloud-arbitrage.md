# Feature 3: Cloud Arbitrage Engine

## Overview
Continuously compare spot/preemptible pricing across providers. Migrate workloads to cheapest region in real-time. Savings tracking dashboard.

## Components
- `cloud_arbitrage.py` — Pricing comparator, migration scheduler
- `CloudArbitrageCog` — Discord commands for arbitrage optimization
- `CloudArbitrage.tsx` — React arbitrage opportunities page
- CLI commands in `cli/ipilot/commands/hybrid_cloud/cloud_arbitrage.py`

## API Endpoints
- `GET /api/arbitrage/opportunities` — List arbitrage opportunities
- `GET /api/arbitrage/compare` — Compare pricing across providers
- `POST /api/arbitrage/migrate/:id` — Execute migration
- `GET /api/arbitrage/migrations` — List migrations
- `GET /api/arbitrage/savings` — Get total savings

## Configuration
Minimum savings threshold: 15% or $0.10/hr. Auto-migrate option available.
