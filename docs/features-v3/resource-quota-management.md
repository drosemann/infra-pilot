# Feature 75: Resource Quota Management

## Overview
Hierarchical resource quota management with per-team and per-project limits on CPU, memory, storage, network, and container counts with enforcement and usage tracking.

## Components
- `quota_manager.py` - Core quota management
- `quota_enforcer.py` - Resource usage enforcement
- `quota_routes.py` - API endpoints
- `QuotaManager` - Manager class

## Quota Dimensions
- CPU cores (limit and reservation)
- Memory (limit and reservation)
- Storage (persistent volumes, backups)
- Network (bandwidth, public IPs, ports)
- Containers (count per project)
- Load balancers (count, rules)
- Databases (count, storage)

## Hierarchical Model
```
Organization
  ├── Team A (CPU: 32 cores, Memory: 128GB)
  │   ├── Project A1 (CPU: 16 cores, Memory: 64GB)
  │   └── Project A2 (CPU: 16 cores, Memory: 64GB)
  └── Team B (CPU: 16 cores, Memory: 64GB)
      └── Project B1 (CPU: 16 cores, Memory: 64GB)
```

## API Endpoints
- `GET /api/v1/quotas` - List quotas
- `POST /api/v1/quotas` - Create quota
- `GET /api/v1/quotas/{id}` - Get quota details
- `PUT /api/v1/quotas/{id}` - Update quota
- `DELETE /api/v1/quotas/{id}` - Delete quota
- `GET /api/v1/quotas/{id}/usage` - Current usage
- `GET /api/v1/quotas/hierarchy` - Quota hierarchy
- `POST /api/v1/quotas/{id}/request` - Request increase
- `GET /api/v1/quotas/requests` - Pending requests
- `POST /api/v1/quotas/requests/{id}/approve` - Approve request
- `POST /api/v1/quotas/requests/{id}/deny` - Deny request

## Enforcement Modes
- `hard` - Strictly enforce (reject if exceeded)
- `soft` - Warn but allow with alerting
- `audit` - Log only, no enforcement
- `parent` - Enforce only at parent level, child inherits
