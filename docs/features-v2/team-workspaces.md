# feature 28: team workspaces

| metadata | value |
|----------|-------|
| feature id | 28 |
| feature name | team workspaces |
| primary service | integration service |
| effort estimate | medium (4-6 pt) |
| dependencies | auth service, resource manager, approval engine |
| priority | high |

## 1. overview

team workspaces provide isolated environments where teams manage their infrastructure resources collaboratively. each workspace has its own member roster, resource quotas, activity audit trail, and sharing policies. cross-workspace resource sharing is supported via an approval workflow.

### 1.1 goals

- enable multi-team isolation within a single infra pilot deployment
- provide per-workspace resource quotas (servers, networks, etc.)
- maintain a complete audit log of all workspace activity
- support cross-workspace resource sharing with admin approval
- simplify member management with role-based access

### 1.2 non-goals

- hierarchical workspace nesting (flat model)
- automatic resource rebalancing between workspaces
- cross-workspace secret sharing
- billing or cost allocation per workspace (future)

## 2. architecture

### 2.1 high-level diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         API Gateway                                  │
└────────┬──────────┬──────────┬──────────┬───────────┬───────────────┘
         │          │          │          │           │
         ▼          ▼          ▼          ▼           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     Integration Service                              │
│                                                                     │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────────┐    │
│  │ Workspace    │  │ Membership   │  │ Cross-Workspace         │    │
│  │ Manager      │  │ Manager      │  │ Sharing Controller      │    │
│  │ - CRUD       │  │ - Invites    │  │ - Share requests        │    │
│  │ - Quotas     │  │ - Roles      │  │ - Approval routing      │    │
│  │ - Settings   │  │ - RBAC       │  │ - Revocation            │    │
│  └──────┬───────┘  └──────┬───────┘  └───────────┬─────────────┘    │
│         │                 │                       │                  │
│         ▼                 ▼                       ▼                  │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  Resource Binding Layer                                    │    │
│  │  Associates resources (servers, networks, etc.) with       │    │
│  │  a workspace. Enforces quota limits on creation.           │    │
│  └────────────────────────────────────────────────────────────┘    │
│         │                 │                       │                  │
└─────────┼─────────────────┼───────────────────────┼────────────────┘
          │                 │                       │
          ▼                 ▼                       ▼
┌─────────────┐  ┌──────────────────┐  ┌─────────────────────────┐
│  Database   │  │  Auth Service    │  │  Notification Service   │
│  - Metadata │  │  - Role checks   │  │  - Approval requests    │
│  - Audit    │  │  - Permission    │  │  - Member invites       │
│  - Quotas   │  │    resolution    │  │  - Quota alerts         │
└─────────────┘  └──────────────────┘  └─────────────────────────┘
```

### 2.2 workspace model

each workspace is a top-level organizational unit:

```
Workspace
├── Members (users + roles)
│   ├── Owner (full control)
│   ├── Admin (manage members, modify settings)
│   ├── Member (create/manage own resources)
│   └── Viewer (read-only)
├── Resources
│   ├── Servers (bound to workspace)
│   ├── Networks (bound to workspace)
│   └── Other assets...
├── Quotas
│   ├── max_servers: 10
│   ├── max_cores: 32
│   ├── max_ram_gb: 128
│   └── max_networks: 5
├── Audit Log
│   └── entries: [timestamp, actor, action, detail]
└── Sharing
    ├── Incoming shares (resources shared TO this workspace)
    └── Outgoing shares (resources shared FROM this workspace)
```

## 3. implementation plan

### phase 1: core workspace crud (pt 1.5-2)

| task | description |
|------|-------------|
| 1.1 | define data models and migrations (workspaces, memberships, roles) |
| 1.2 | implement workspace crud endpoints |
| 1.3 | implement member management (add, remove, role change) |
| 1.4 | rbac enforcement on all workspace-scoped operations |
| 1.5 | workspace-scoped resource creation (bind resource to workspace) |

### phase 2: quotas & audit (pt 1.5-2)

| task | description |
|------|-------------|
| 2.1 | quota definition and enforcement middleware |
| 2.2 | quota usage tracking (aggregated counts per resource type) |
| 2.3 | audit log ingestion pipeline (intercept create/update/delete) |
| 2.4 | audit log query api with filters (actor, action, time range) |
| 2.5 | quota alerting (warn at 80%, block at 100%) |

### phase 3: cross-workspace sharing (pt 1-2)

| task | description |
|------|-------------|
| 3.1 | share request api (source workspace to target workspace) |
| 3.2 | approval workflow integration (target workspace admin approves) |
| 3.3 | resource access delegation at the iam/cloud level |
| 3.4 | share revocation and cleanup |
| 3.5 | ui: sharing dashboard, pending requests, shared resources view |

## 4. api design

### 4.1 workspace endpoints

```
POST   /api/v2/workspaces                          Create workspace
GET    /api/v2/workspaces                           List user's workspaces
GET    /api/v2/workspaces/:id                       Get workspace details
PUT    /api/v2/workspaces/:id                       Update workspace settings
DELETE /api/v2/workspaces/:id                       Delete workspace (empty only)

POST   /api/v2/workspaces/:id/members               Add member
GET    /api/v2/workspaces/:id/members               List members
PUT    /api/v2/workspaces/:id/members/:userId       Change role
DELETE /api/v2/workspaces/:id/members/:userId       Remove member

GET    /api/v2/workspaces/:id/quotas                Get quota limits & usage
PUT    /api/v2/workspaces/:id/quotas                Update quota limits (admin)

GET    /api/v2/workspaces/:id/audit                 Query audit log
```

### 4.2 cross-workspace sharing endpoints

```
POST   /api/v2/workspace-shares                     Create share request
GET    /api/v2/workspace-shares                      List shares (in/out)
GET    /api/v2/workspace-shares/:id                  Get share details
PUT    /api/v2/workspace-shares/:id/approve          Approve share
PUT    /api/v2/workspace-shares/:id/reject           Reject share
DELETE /api/v2/workspace-shares/:id                  Revoke/withdraw share
```

### 4.3 request/response examples

**create workspace:**
```json
POST /api/v2/workspaces
{
  "name": "production-sre",
  "display_name": "Production SRE Team",
  "description": "Workspace for the Production SRE squad",
  "settings": {
    "default_resource_ttl_hours": 48,
    "require_approval_for_destructive_actions": true
  }
}

Response 201:
{
  "id": "ws_prod_sre",
  "name": "production-sre",
  "display_name": "Production SRE Team",
  "created_by": "u_admin",
  "created_at": "2026-05-27T12:00:00Z",
  "member_count": 1,
  "quota_usage": { "servers": 0, "cores": 0, "ram_gb": 0 }
}
```

**add member:**
```json
POST /api/v2/workspaces/ws_prod_sre/members
{
  "user_id": "u_alice",
  "role": "member"
}

Response 201:
{
  "workspace_id": "ws_prod_sre",
  "user_id": "u_alice",
  "role": "member",
  "added_by": "u_admin",
  "added_at": "2026-05-27T12:05:00Z"
}
```

**create share request:**
```json
POST /api/v2/workspace-shares
{
  "source_workspace_id": "ws_dev_team",
  "target_workspace_id": "ws_prod_sre",
  "resource_type": "server",
  "resource_id": "srv-dev-db-01",
  "permissions": ["read"],
  "reason": "Production SRE needs read access to debug DB latency",
  "expires_at": "2026-06-27T00:00:00Z"
}

Response 201:
{
  "id": "share_xyz789",
  "status": "pending_approval",
  "requested_by": "u_bob",
  "created_at": "2026-05-27T12:10:00Z"
}
```

**list audit log:**
```json
GET /api/v2/workspaces/ws_prod_sre/audit?limit=10&offset=0

Response 200:
{
  "entries": [
    {
      "timestamp": "2026-05-27T12:05:00Z",
      "actor": "u_admin",
      "action": "member.add",
      "detail": { "target_user": "u_alice", "role": "member" }
    },
    {
      "timestamp": "2026-05-27T11:00:00Z",
      "actor": "u_admin",
      "action": "workspace.create",
      "detail": { "name": "production-sre" }
    }
  ],
  "total": 2
}
```

## 5. data model

### 5.1 `workspaces`

| column | type | description |
|--------|------|-------------|
| id | varchar(32) (pk) | human-readable slug (e.g., `ws_prod_sre`) |
| name | varchar(128) | display name |
| description | text | optional description |
| settings | jsonb | feature flags, ttls, policies |
| created_by | uuid (fk to users) | creator |
| created_at | timestamptz | creation timestamp |
| updated_at | timestamptz | last modification |
| deleted_at | timestamptz | soft delete (nullable) |

### 5.2 `workspace_members`

| column | type | description |
|--------|------|-------------|
| id | uuid (pk) | auto-generated |
| workspace_id | varchar(32) (fk) | parent workspace |
| user_id | uuid (fk to users) | member |
| role | enum | `owner`, `admin`, `member`, `viewer` |
| invited_by | uuid (fk to users) | who invited |
| joined_at | timestamptz | when membership was activated |
| updated_at | timestamptz | role change timestamp |

### 5.3 `workspace_quotas`

| column | type | description |
|--------|------|-------------|
| workspace_id | varchar(32) (pk/fk) | parent workspace |
| max_servers | int | default: 10 |
| max_cores | int | default: 32 |
| max_ram_gb | int | default: 128 |
| max_networks | int | default: 5 |
| max_storage_gb | int | default: 500 |
| updated_by | uuid (fk to users) | last modifier |
| updated_at | timestamptz | last modification |

### 5.4 `workspace_audit_log`

| column | type | description |
|--------|------|-------------|
| id | bigserial (pk) | auto-increment |
| workspace_id | varchar(32) (fk) | parent workspace |
| actor_id | uuid (fk to users) | who performed the action |
| action | varchar(64) | e.g., `workspace.create`, `member.add`, `resource.delete` |
| detail | jsonb | action-specific payload |
| ip_address | inet | originating ip |
| created_at | timestamptz | when action occurred |

### 5.5 `workspace_shares`

| column | type | description |
|--------|------|-------------|
| id | uuid (pk) | auto-generated |
| source_workspace_id | varchar(32) (fk) | owning workspace |
| target_workspace_id | varchar(32) (fk) | receiving workspace |
| resource_type | varchar(64) | e.g., `server`, `network` |
| resource_id | varchar(128) | identifier of shared resource |
| permissions | text[] | array of granted permissions |
| status | enum | `pending_approval`, `approved`, `rejected`, `revoked` |
| requested_by | uuid (fk to users) | requester |
| approved_by | uuid (fk to users, nullable) | approver |
| approved_at | timestamptz | when approved |
| expires_at | timestamptz | when share auto-revokes |
| reason | text | justification for share |
| created_at | timestamptz | creation timestamp |

## 6. service assignments

| service | responsibilities |
|---------|-----------------|
| **integration service** (primary) | workspace crud, member management, quota enforcement, audit pipeline, cross-workspace sharing logic |
| **auth service** | role resolution, permission checks for workspace-scoped actions |
| **resource manager** | resource-to-workspace binding, quota validation on resource creation |
| **notification service** | invite emails, approval request notifications, quota warning alerts |
| **database** | all workspace metadata, membership, quotas, audit log, share records |

## 7. quota enforcement flow

```
Request: Create Server in Workspace "ws_prod_sre"
  │
  ▼
1. Resource Manager calls Integration Service: check_quota(ws_prod_sre, "server")
  │
  ▼
2. Integration Service reads current usage:
     SELECT COUNT(*) FROM resources WHERE workspace_id = 'ws_prod_sre' AND type = 'server'
  │
  ▼
3. Compare against workspace_quotas.max_servers for ws_prod_sre
  │
  ▼
4. If usage < quota → allow; else → return 403 with quota_exceeded error
```

## 8. effort estimate

| phase | person-days |
|-------|-------------|
| phase 1: core workspace crud | 1.5-2 pt |
| phase 2: quotas & audit | 1.5-2 pt |
| phase 3: cross-workspace sharing | 1-2 pt |
| **total** | **4-6 pt** |

## 9. future enhancements

- hierarchical workspaces (sub-workspaces with inherited quotas)
- usage dashboards with billing/cost allocation
- workspace templates (pre-configured quotas + member roles)
- saml/scim group sync for workspace membership
- automated resource cleanup based on ttl policies
