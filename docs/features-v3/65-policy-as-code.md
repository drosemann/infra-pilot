# Feature 65: Policy as Code

## Overview
OPA (Open Policy Agent)/Rego integration for policy enforcement with git-versioned policy management.

## Components
- `policy_engine.py` - OPA Rego policy evaluation engine
- `policy_store.py` - Policy storage and versioning
- `policy_routes.py` - Policy management API
- `policy_sync.py` - Git-based policy synchronization
- `PolicyManager` - Manager class

## Policy Lifecycle
1. Policies written in Rego
2. Stored in Git repository
3. Synced to policy engine
4. Evaluated against input data
5. Results returned with decision and explanation

## Policy Types
- `validation` - Validate resource configuration
- `compliance` - Check compliance requirements
- `rbac` - Authorization decisions
- `quota` - Resource quota enforcement
- `cost` - Cost control policies

## API Endpoints
- `GET /api/v1/policies` - List policies
- `GET /api/v1/policies/{id}` - Get policy details
- `PUT /api/v1/policies/{id}` - Create/update policy
- `DELETE /api/v1/policies/{id}` - Delete policy
- `POST /api/v1/policies/{id}/evaluate` - Evaluate policy
- `GET /api/v1/policies/{id}/history` - Policy version history
- `POST /api/v1/policies/sync` - Sync from Git

## Example Rego Policy
```rego
package infra_pilot.auth

default allow = false

allow {
  input.method == "GET"
  input.path == ["api", "v1", "health"]
}

allow {
  input.method == "GET"
  input.user.role == "admin"
}

allow {
  input.method == "POST"
  input.path[0] == "api"
  input.user.role == "admin"
  input.resource.owner == input.user.id
}
```

## Git Sync
- Supports GitHub, GitLab, Bitbucket
- Webhook-triggered sync
- Scheduled sync (cron)
- Policy versioning with semantic tags
- Rollback to previous versions
