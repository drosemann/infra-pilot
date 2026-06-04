# Feature 32: Multi-Region Active-Active Setup

## Overview
Active-active deployment across regions with global load balancing, data replication conflict resolution, and user stickiness with failover.

## Components
- `active_active.py` - Region management, traffic routing, conflict resolution
- `ActiveActiveCog` - Discord commands for region management
- `ActiveActive.tsx` - Management panel UI

## API Endpoints
- `GET /api/v1/resiliency/active-active/regions` - List regions
- `POST /api/v1/resiliency/active-active/regions` - Register region
- `POST /api/v1/resiliency/active-active/regions/{id}/health` - Health check
- `POST /api/v1/resiliency/active-active/regions/{id}/weight` - Update traffic weight
- `GET /api/v1/resiliency/active-active/global-status` - Global status
