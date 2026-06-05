# feature 29: change approval workflow

| metadata | value |
|----------|-------|
| feature id | 29 |
| feature name | change approval workflow |
| primary service | management panel |
| effort estimate | medium (4-6 pt) |
| dependencies | auth service, notification service, slack/discord bot |
| priority | high |

## 1. overview

the change approval workflow introduces a mandatory second-person approval gate for destructive or sensitive infrastructure actions. when a user attempts an action covered by policy (e.g., deleting a server, modifying a firewall, restarting a production service), a change request is created and routed to designated approvers via slack or discord interactive buttons. an emergency break-glass mechanism bypasses approval for critical incidents.

### 1.1 goals

- prevent accidental destructive actions via mandatory peer review
- support flexible approval policies (action-based, resource-based, tag-based)
- integrate approvals into slack/discord where operators already work
- maintain a complete, immutable audit trail of all change requests
- provide emergency break-glass with justification logging

### 1.2 non-goals

- replace ci/cd pipelines or change management systems (servicenow, etc.)
- support multi-step or sequential approval chains (single approval required)
- automated rollback on approval denial
- approval based on scheduled maintenance windows

## 2. architecture

### 2.1 high-level diagram

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────┐
│   User       │     │  Management      │     │  Approver    │
│   (Browser)  │     │  Panel           │     │  (Slack/DM)  │
└──────┬───────┘     └──────┬───────────┘     └──────┬────────┘
       │                    │                         │
       │  1. Destructive    │                         │
       │     action request │                         │
       │───────────────────►│                         │
       │                    │  2. Check policy        │
       │                    │  ───────►               │
       │                    │                         │
       │                    │  3. If requires approval│
       │                    │  ┌─────────────────┐    │
       │                    │  │ Change Request   │    │
       │                    │  │ Engine           │    │
       │                    │  │  - Create ticket │    │
       │                    │  │  - Route to      │    │
       │                    │  │    approver(s)   │    │
       │                    │  │  - Set status    │    │
       │                    │  │    = pending     │    │
       │                    │  └────────┬────────┘    │
       │                    │           │              │
       │                    │           │  4. Notification
       │                    │           │  (Slack/Discord)
       │                    │           │────────────►│
       │                    │           │              │
       │                    │           │  5. Approve/Reject
       │                    │           │  (button click)
       │                    │           │◄─────────────│
       │                    │           │              │
       │                    │  6. Webhook callback     │
       │                    │  ◄────────               │
       │                    │                          │
       │  7. Execute/Deny   │                          │
       │◄───────────────────┤                          │
       │                    │                          │
```

### 2.2 component descriptions

| component | role | technology |
|-----------|------|------------|
| policy engine | evaluates whether an action requires approval | go / node.js rules engine |
| change request engine | manages request lifecycle (create, approve, reject, cancel) | management panel |
| notification adapter | sends approval requests to slack/discord via webhooks | integration service |
| interactive message handler | receives button-clicks from slack/discord | webhook endpoint |
| break-glass controller | handles emergency bypass with justification | management panel |
| audit recorder | immutable log of all change requests and decisions | database |

### 2.3 approval policy model

policies are evaluated in order. the first matching policy determines the action:

```yaml
policies:
  - name: "block-prod-server-delete"
    match:
      action: "server.delete"
      resource_tags:
        environment: "production"
    requires_approval: true
    approver_roles: ["admin", "owner"]
    notification_channels: ["slack", "discord"]
    cooldown_seconds: 300  # Re-approval needed within this window

  - name: "block-firewall-modify"
    match:
      action: "firewall.modify"
    requires_approval: true
    approver_roles: ["admin"]
    notification_channels: ["slack"]

  - name: "block-prod-restart"
    match:
      action: "server.restart"
      resource_tags:
        environment: "production"
        criticality: "high"
    requires_approval: true
    approver_roles: ["admin", "owner"]
    notification_channels: ["slack", "discord"]
```

## 3. implementation plan

### phase 1: policy engine & change request crud (pt 1.5-2)

| task | description |
|------|-------------|
| 1.1 | design data models for approval policies and change requests |
| 1.2 | implement policy definition crud (yaml/json stored in db) |
| 1.3 | build policy evaluation engine (action + resource attributes to match) |
| 1.4 | implement change request lifecycle (create, get, list, cancel) |
| 1.5 | add approval interceptor middleware in management panel action execution |

### phase 2: slack/discord integration (pt 1.5-2)

| task | description |
|------|-------------|
| 2.1 | build slack block kit message builder for approval requests |
| 2.2 | build discord embed builder for approval requests |
| 2.3 | implement interactive webhook endpoint (slack `interactivity` + discord `interaction`) |
| 2.4 | map button clicks to approve/reject/cancel actions |
| 2.5 | handle notification failures (timeout, fallback to in-app approval) |

### phase 3: audit, break-glass & ui (pt 1-2)

| task | description |
|------|-------------|
| 3.1 | immutable audit log for all change requests + decisions |
| 3.2 | break-glass mechanism: justification form to bypass to audit record |
| 3.3 | in-app approval dashboard (pending/approved/rejected requests) |
| 3.4 | policy management ui (create/edit/test policies) |
| 3.5 | cooldown/cache layer to prevent duplicate approvals within window |

## 4. api design

### 4.1 approval policy endpoints

```
POST   /api/v2/approval-policies                 Create policy
GET    /api/v2/approval-policies                  List policies
GET    /api/v2/approval-policies/:id              Get policy details
PUT    /api/v2/approval-policies/:id              Update policy
DELETE /api/v2/approval-policies/:id              Delete policy
POST   /api/v2/approval-policies/:id/test         Dry-run: test action against policy
```

### 4.2 change request endpoints

```
POST   /api/v2/change-requests                   Create change request (auto-triggered)
GET    /api/v2/change-requests                    List user's change requests
GET    /api/v2/change-requests/:id                Get request details
POST   /api/v2/change-requests/:id/approve        Approve
POST   /api/v2/change-requests/:id/reject         Reject
POST   /api/v2/change-requests/:id/cancel         Cancel own request
POST   /api/v2/change-requests/:id/break-glass    Emergency bypass
```

### 4.3 slack/discord webhook endpoints

```
POST   /api/v2/webhooks/slack/interactive         Slack interactivity payload
POST   /api/v2/webhooks/discord/interaction       Discord interaction payload
```

### 4.4 request/response examples

**create change request (auto-triggered by middleware):**
```json
POST /api/v2/change-requests
{
  "action": "server.delete",
  "resource_id": "srv-prod-api-01",
  "resource_type": "server",
  "resource_tags": {
    "environment": "production",
    "team": "platform"
  },
  "requested_by": "u_bob",
  "policy_id": "pol_block_prod_server_delete",
  "justification": "Decommissioning old API server after migration to v2"
}

Response 201:
{
  "id": "cr_a1b2c3",
  "status": "pending",
  "policy_name": "block-prod-server-delete",
  "approvers": ["u_alice", "u_carol"],
  "created_at": "2026-05-27T12:00:00Z",
  "notification_sent": true,
  "channels": ["slack", "discord"]
}
```

**slack interactive payload (incoming webhook):**
```json
POST /api/v2/webhooks/slack/interactive
{
  "type": "block_actions",
  "team": { "id": "T12345" },
  "user": { "id": "U67890", "name": "alice" },
  "actions": [
    {
      "action_id": "approve_cr_a1b2c3",
      "block_id": "cr_a1b2c3",
      "value": "approve"
    }
  ]
}
```

**approve request:**
```json
POST /api/v2/change-requests/cr_a1b2c3/approve
{
  "approved_by": "u_alice",
  "comment": "Migration confirmed complete, proceed with decommission"
}

Response 200:
{
  "id": "cr_a1b2c3",
  "status": "approved",
  "approved_by": "u_alice",
  "approved_at": "2026-05-27T12:05:00Z"
}
```

**break-glass:**
```json
POST /api/v2/change-requests/cr_a1b2c3/break-glass
{
  "bypassed_by": "u_bob",
  "incident_id": "inc_20260527_001",
  "justification": "Production outage - need immediate server recycle",
  "acknowledged_risk": true
}

Response 200:
{
  "id": "cr_a1b2c3",
  "status": "break_glass_bypassed",
  "bypassed_at": "2026-05-27T12:10:00Z",
  "audit_recorded": true
}
```

## 5. data model

### 5.1 `approval_policies`

| column | type | description |
|--------|------|-------------|
| id | varchar(64) (pk) | human-readable slug |
| name | varchar(128) | policy display name |
| enabled | boolean | whether policy is active |
| match_conditions | jsonb | action + resource attribute matchers |
| requires_approval | boolean | whether approval is required |
| approver_roles | text[] | roles eligible to approve |
| notification_channels | text[] | `slack`, `discord`, `in_app` |
| cooldown_seconds | int | re-approval window |
| created_by | uuid (fk to users) | policy creator |
| created_at | timestamptz | creation timestamp |
| updated_at | timestamptz | last modification |

### 5.2 `change_requests`

| column | type | description |
|--------|------|-------------|
| id | varchar(64) (pk) | e.g., `cr_a1b2c3` |
| policy_id | varchar(64) (fk) | matched policy |
| action | varchar(64) | e.g., `server.delete` |
| resource_id | varchar(128) | target resource |
| resource_type | varchar(64) | e.g., `server` |
| resource_tags | jsonb | tags at time of request |
| requested_by | uuid (fk to users) | requester |
| justification | text | why the action is needed |
| status | enum | `pending`, `approved`, `rejected`, `cancelled`, `break_glass_bypassed`, `expired` |
| approved_by | uuid (fk to users, nullable) | approver |
| approved_at | timestamptz | approval timestamp |
| rejected_by | uuid (fk to users, nullable) | rejector |
| rejected_at | timestamptz | rejection timestamp |
| rejected_reason | text | reason for rejection |
| break_glass_by | uuid (fk to users, nullable) | who bypassed |
| break_glass_at | timestamptz | when bypassed |
| break_glass_reason | text | justification for bypass |
| incident_id | varchar(64) | associated incident (break-glass) |
| notification_sent | boolean | whether slack/discord was notified |
| created_at | timestamptz | creation |
| updated_at | timestamptz | last update |
| expires_at | timestamptz | auto-expiry (default: 1 hour) |

### 5.3 `approval_audit_log`

| column | type | description |
|--------|------|-------------|
| id | bigserial (pk) | auto-increment |
| change_request_id | varchar(64) (fk) | related cr |
| action | varchar(32) | `created`, `approved`, `rejected`, `cancelled`, `break_glass` |
| actor_id | uuid (fk to users) | who performed the action |
| detail | jsonb | additional context |
| ip_address | inet | originating ip |
| created_at | timestamptz | immutable timestamp |

## 6. service assignments

| service | responsibilities |
|---------|-----------------|
| **management panel** (primary) | policy engine, change request lifecycle, approval interceptor middleware, break-glass controller, audit recorder |
| **auth service** | role resolution for approver matching |
| **notification service** | slack/discord message delivery |
| **slack bot** | interactive button handling, webhook endpoint |
| **discord bot** | interaction handling, webhook endpoint |
| **database** | policy storage, change requests, audit log |

## 7. approval flow (detailed)

```
1. User initiates destructive action in Management Panel
2. Middleware intercepts action before execution
3. Policy engine evaluates action + resource attributes
   ├── No matching policy → action proceeds normally
   └── Policy matched → approval required
        ├── Check cooldown: if < cooldown_seconds since last approval for same resource → skip
        └── Create change request (status: pending)
             ├── Determine eligible approvers (role-based)
             ├── Send notification to Slack/Discord with interactive buttons
             └── Return 202 Accepted with change request ID to requester

4. Approver clicks "Approve" in Slack/Discord
   └── Webhook received → validate user is eligible approver
        ├── Yes → update status to "approved", execute original action
        └── No → return error notification

5. If no response within expiry (default 1 hour):
   └── Status → "expired", requester notified to resubmit

6. Emergency:
   └── Break-glass bypass → records justification, updates status, executes action
       └── Alert all admins: break-glass was used
```

## 8. effort estimate

| phase | person-days |
|-------|-------------|
| phase 1: policy engine & change request crud | 1.5-2 pt |
| phase 2: slack/discord integration | 1.5-2 pt |
| phase 3: audit, break-glass & ui | 1-2 pt |
| **total** | **4-6 pt** |

## 9. future enhancements

- multi-step approval chains (n of m approvers)
- time-based policies (require approval only during off-hours)
- integration with pagerduty on-call for approver routing
- webhook notifications for external change management tools
- scheduled change requests with automatic execution window
