# Policy as Code Engine API Reference
## Overview
Rule-based policy evaluation engine supporting RBAC, resource quotas, cost controls, and compliance requirements. Policies are evaluated in order with deny-overrides semantics.

## Base URL: /api/v1/governance/policies

### POST /
Create a new policy.
**Request:**
| Field | Required | Type | Description |
|-------|----------|------|-------------|
| name | yes | string | Unique policy name |
| description | yes | string | Human-readable description |
| category | yes | string | security/compliance/rbac/quota/cost |
| enabled | no | boolean | Default: true |
| rules | yes | array | Policy rule definitions |

**Rule Schema:**
```json
{
  "id": "unique-rule-id",
  "effect": "allow|deny|require_mfa|require",
  "resource": "service:resource:*",
  "condition": {
    "field": "value",
    "field__gt": 10,
    "field__in": ["a", "b"]
  }
}
```

**Response:**
```json
{
  "policy_id": "pol_abc123",
  "name": "require_mfa",
  "description": "Require MFA for admin actions",
  "category": "security",
  "enabled": true,
  "rules": [...],
  "created_at": "2024-01-15T10:30:00Z",
  "version": 1
}
```

### GET /
List policies.
**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| category | string | Filter by category |
| enabled_only | boolean | Only enabled policies |

### GET /{policy_id}
Get policy details with full rule set.

### PUT /{policy_id}
Update policy.
**Request:** Partial update with any supported fields.

### DELETE /{policy_id}
Delete a policy.

### POST /evaluate
Evaluate a resource action against all enabled policies.
**Request:**
| Field | Required | Description |
|-------|----------|-------------|
| resource | yes | Resource identifier (e.g., "server:prod-db") |
| action | yes | Action to evaluate (e.g., "delete") |
| context | yes | Evaluation context object |

**Response:**
```json
{
  "decision": "deny",
  "matched_policies": ["require_mfa"],
  "matched_rules": [
    {
      "policy": "require_mfa",
      "rule_id": "mfa-1",
      "effect": "deny"
    }
  ],
  "context": {
    "user": "alice@example.com",
    "role": "viewer",
    "mfa_verified": false
  }
}
```

### POST /evaluate/rule
Evaluate a single rule directly.
**Request:**
| Field | Required | Description |
|-------|----------|-------------|
| rule | yes | Rule definition object |
| resource | yes | Resource to match |
| action | yes | Action to evaluate |
| context | yes | Evaluation context |

### POST /sync
Bulk sync policies.
**Request:** Array of policy objects.

### GET /export
Export all policies as JSON array.

## Condition Operators
| Operator | Description | Example |
|----------|-------------|---------|
| eq / = | Equals | {"role": "admin"} |
| neq / != | Not equals | {"env": {"neq": "production"}} |
| gt | Greater than | {"usage.cpu": {"gt": 80}} |
| gte | Greater or equal | {"count": {"gte": 10}} |
| lt | Less than | {"cpu": {"lt": 2}} |
| lte | Less or equal | {"priority": {"lte": 3}} |
| in | In array | {"role": {"in": ["admin", "operator"]}} |
| contains | String contains | {"name": {"contains": "prod"}} |
| exists | Field exists | {"email": {"exists": true}} |

## Default Policies
1. RBAC: Role-based access control (admin/operator/viewer)
2. Quota: Resource usage limits
3. Cost Control: Budget enforcement
4. Compliance: Regulatory requirements
5. Security: MFA requirements and security controls

## Performance
- Rule evaluation: <1ms per rule (in-memory)
- Policy caching: 300s TTL
- Max evaluation depth: 10 nested conditions
- Batch evaluation: up to 100 requests per call
