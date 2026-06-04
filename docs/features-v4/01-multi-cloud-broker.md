# Feature 1: Multi-Cloud Resource Broker

## Overview
Abstract resource provisioning across AWS, Azure, GCP, Hetzner, OVH, and DigitalOcean. Unified API with provider scoring by cost/latency/region. Auto-failover between clouds.

## Components
- `multi_cloud_broker.py` — Broker class with provider abstraction, resource CRUD, pricing models
- `MultiCloudBrokerCog` — Discord commands for cloud resource management
- `MultiCloudBroker.tsx` — React dashboard for cloud resource management
- CLI commands in `cli/ipilot/commands/hybrid_cloud/multi_cloud_broker.py`

## API Endpoints
- `GET /api/cloud/resources` — List all cloud resources
- `POST /api/cloud/resources` — Provision new resource
- `GET /api/cloud/resources/:id` — Get resource status
- `DELETE /api/cloud/resources/:id` — Delete resource
- `GET /api/cloud/providers` — List configured providers
- `GET /api/cloud/scores` — Score providers by requirements

## Provider Scoring
Scores are calculated based on:
- Cost (weight: 40%) — base hourly rate vs budget
- Latency (weight: 30%) — region proximity
- Region coverage (weight: 15%) — desired region availability
- Availability (weight: 15%) — historical uptime SLA

## Auto-Failover
When a resource fails, the broker automatically selects the best alternative provider with score >= 70% threshold.
