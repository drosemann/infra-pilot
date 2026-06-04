# Feature 2: Cloud Bursting Gateway

## Overview
Seamlessly burst on-prem workloads to public cloud during peak. Automatic network stitching, data sync, load distribution. Tear-down when demand subsides.

## Components
- `cloud_bursting.py` — Burst manager, network stitching, load distribution
- `CloudBurstingCog` — Discord commands for burst management
- `CloudBursting.tsx` — React burst configuration panel
- CLI commands in `cli/ipilot/commands/hybrid_cloud/cloud_bursting.py`

## API Endpoints
- `GET /api/burst/workloads` — List registered workloads
- `POST /api/burst/workloads` — Register new workload
- `GET /api/burst/check` — Check burst readiness
- `POST /api/burst/start` — Initiate cloud burst
- `POST /api/burst/:id/drain` — Drain and tear down burst
- `GET /api/burst/active` — List active bursts

## Load Distribution Strategies
- Round Robin — evenly distribute across targets
- Least Connections — route to least loaded target
- Latency Based — prefer lowest latency target
- Weighted — distribute based on workload priority
