# Feature 13: Service Catalog

## Overview
Comprehensive service registry with automated readiness scoring based on metadata completeness and best practice checks.

## Components
- `service_catalog.py` - Service catalog manager with scoring engine
- `service_catalog_cog.py` - Discord bot commands

## Data Models
- `CatalogService` - Service entry with metadata
- `ReadinessCheck` - Individual check definition
- `ReadinessScore` - Aggregated scoring result

## Scoring Criteria (15 checks)
- Has description, owner, domain, SLA, documentation, CI/CD, monitoring, on-call, backup strategy, security review, compliance tags, cost center, dependencies, API spec, and runbook.

## CLI Commands
- `ipilot service-catalog list` - List services
- `ipilot service-catalog register` - Register service
- `ipilot service-catalog get` - Get details
- `ipilot service-catalog score` - Score readiness
- `ipilot service-catalog summary` - Summary stats
