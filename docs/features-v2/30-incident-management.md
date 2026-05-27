# feature 30: incident management

| metadata | value |
|----------|-------|
| feature id | 30 |
| feature name | incident management |
| primary service | integration service |
| effort estimate | large (7-10 pt) |
| dependencies | auth service, notification service, pagerduty/opsgenie api |
| priority | high |

## 1. overview

the incident management feature provides a complete lifecycle for operational incidents: detection, alerting, on-call scheduling, escalation, timeline tracking, post-mortem documentation, and optional public status page. it integrates with pagerduty and opsgenie for alert routing and on-call synchronization.

### 1.1 goals

- define on-call schedules with rotation support
- configure escalation policies with time-based and approval-based rules
- track incidents from detection through resolution
- provide post-mortem templates for blameless retrospectives
- sync on-call rotations with pagerduty and opsgenie
- optional public status page for external stakeholders

### 1.2 non-goals

- replace full-featured monitoring (prometheus, grafana, datadog)
- incident response runbook automation (future scope)
- sla/slo tracking and reporting
- root cause analysis automation

## 2. architecture

### 2.1 high-level diagram

```
┌──────────────────────────────────────────────────────────────────────────┐
│                              Integration Service                          │
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ On-Call       │  │ Escalation   │  │ Incident     │  │ Post-Mortem  │ │
│  │ Scheduler     │  │ Engine       │  │ Lifecycle    │  │ Templates    │ │
│  │ - Rotations   │  │ - Policies   │  │ - Create     │  │ - CRUD       │ │
│  │ - Coverage    │  │ - Time-based │  │ - Update     │  │ - Render     │ │
│  │ - Overrides   │  │ - Routing    │  │ - Resolve    │  │ - Export     │ │
│  └──────┬────────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │
│         │                  │                  │                  │        │
│         ▼                  ▼                  ▼                  ▼        │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │  Integration Adapter Layer                                      │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌────────────────────────┐  │    │
│  │  │ PagerDuty   │  │ Opsgenie    │  │ Status Page Renderer   │  │    │
│  │  │ Sync        │  │ Sync        │  │ (public HTML/JSON)     │  │    │
│  │  └─────────────┘  └─────────────┘  └────────────────────────┘  │    │
│  └──────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────────┘
         │                  │                  │
         ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────────┐  ┌──────────────────────┐
│  Database    │  │  PagerDuty API   │  │  Public Status Page  │
│  - Schedules │  │  (external)      │  │  (optional hosting)  │
│  - Incidents │  │                  │  │                      │
│  - Post-     │  │  Opsgenie API    │  │                      │
│    mortems   │  │  (external)      │  │                      │
└──────────────┘  └──────────────────┘  └──────────────────────┘
```

### 2.2 component descriptions

| component | role | technology |
|-----------|------|------------|
| on-call scheduler | manages rotation schedules, user assignments, overrides | go / node.js |
| escalation engine | evaluates escalation policies, routes to next responder | integration service |
| incident lifecycle | state machine for incident tracking (detecting to acknowledged to resolving to resolved) | integration service |
| post-mortem templates | crud for markdown-based post-mortem documents | integration service |
| pagerduty sync | bidirectional sync of on-call schedules and alerts | rest api + webhooks |
| opsgenie sync | bidirectional sync of on-call schedules and alerts | rest api + webhooks |
| status page renderer | generates public html/json status page | static site generation |

### 2.3 incident state machine

```

                  ┌──────────────┐
                  │  Detecting   │
                  └──────┬───────┘
                         │
                         ▼
                  ┌──────────────┐
          ┌──────►│ Acknowledged │◄───────┐
          │       └──────┬───────┘        │
          │              │                │
          │         Auto-│escalate        │ Re-escalate
          │              ▼                │
          │       ┌──────────────┐        │
          │       │ Investigating│────────┘
          │       └──────┬───────┘
          │              │
          │         Resolving
          │              │
          │              ▼
          │       ┌──────────────┐
          └───────│   Resolved   │
                  └──────────────┘

```

## 3. implementation plan

### phase 1: on-call scheduling (pt 2-3)

| task | description |
|------|-------------|
| 1.1 | define data models: schedules, rotations, shifts, overrides |
| 1.2 | implement schedule crud with recurrence rules (rrule / icalendar) |
| 1.3 | implement rotation assignment (primary, secondary, tertiary) |
| 1.4 | coverage gap detection and alerting |
| 1.5 | manual override support (swap shifts, temporary reassignment) |

### phase 2: incident lifecycle (pt 2-3)

| task | description |
|------|-------------|
| 2.1 | define incident data model + state machine |
| 2.2 | incident crud endpoints |
| 2.3 | escalation policy engine (time-based delays, routing rules) |
| 2.4 | escalation timer service (check for unacknowledged, escalate) |
| 2.5 | incident timeline tracking (auto-log state transitions + manual entries) |
| 2.6 | notification dispatch on state changes (slack, email, sms) |

### phase 3: integrations & status page (pt 3-4)

| task | description |
|------|-------------|
| 3.1 | pagerduty rest api integration: pull on-call schedules, push alerts |
| 3.2 | opsgenie rest api integration: pull on-call schedules, push alerts |
| 3.3 | inbound webhook handlers for pagerduty/opsgenie alerts to auto-create incidents |
| 3.4 | post-mortem template crud + markdown rendering |
| 3.5 | post-mortem export (pdf, markdown) |
| 3.6 | public status page generator (components, incidents, uptime timeline) |
| 3.7 | status page api for external consumers (json feed) |

## 4. api design

### 4.1 on-call schedule endpoints

```
POST   /api/v2/oncall/schedules                    Create schedule
GET    /api/v2/oncall/schedules                     List schedules
GET    /api/v2/oncall/schedules/:id                 Get schedule details
PUT    /api/v2/oncall/schedules/:id                 Update schedule
DELETE /api/v2/oncall/schedules/:id                 Delete schedule

POST   /api/v2/oncall/schedules/:id/overrides       Add override
DELETE /api/v2/oncall/schedules/:id/overrides/:ovId  Remove override

GET    /api/v2/oncall/who-is-oncall                 Current on-call for all schedules
GET    /api/v2/oncall/who-is-oncall?schedule_id=:id  Current on-call for specific schedule
```

### 4.2 escalation policy endpoints

```
POST   /api/v2/escalation-policies                  Create policy
GET    /api/v2/escalation-policies                   List policies
GET    /api/v2/escalation-policies/:id               Get policy details
PUT    /api/v2/escalation-policies/:id               Update policy
DELETE /api/v2/escalation-policies/:id               Delete policy
```

### 4.3 incident endpoints

```
POST   /api/v2/incidents                            Create incident
GET    /api/v2/incidents                             List incidents (filterable)
GET    /api/v2/incidents/:id                         Get incident details
PUT    /api/v2/incidents/:id                         Update incident
POST   /api/v2/incidents/:id/acknowledge             Acknowledge
POST   /api/v2/incidents/:id/resolve                 Resolve
POST   /api/v2/incidents/:id/escalate               Manually escalate
POST   /api/v2/incidents/:id/timeline               Add timeline entry
```

### 4.4 post-mortem endpoints

```
POST   /api/v2/post-mortems                         Create post-mortem
GET    /api/v2/post-mortems                          List post-mortems
GET    /api/v2/post-mortems/:id                      Get post-mortem details
PUT    /api/v2/post-mortems/:id                      Update post-mortem
POST   /api/v2/post-mortems/:id/export              Export (markdown, PDF)
```

### 4.5 status page endpoints

```
POST   /api/v2/status-pages                         Create status page config
GET    /api/v2/status-pages                          List status pages
GET    /api/v2/status-pages/:id                      Get page details + current status
PUT    /api/v2/status-pages/:id                      Update page

GET    /api/v2/status-pages/:id/public               Public status JSON (no auth)
```

### 4.6 request/response examples

**create schedule:**
```json
POST /api/v2/oncall/schedules
{
  "name": "primary-sre-rotation",
  "description": "Primary SRE on-call rotation",
  "timezone": "UTC",
  "rotation_type": "weekly",
  "shift_start": "09:00",
  "shift_duration_hours": 168,
  "members": [
    { "user_id": "u_alice", "rank": 1 },
    { "user_id": "u_bob", "rank": 2 },
    { "user_id": "u_carol", "rank": 3 }
  ],
  "handoff_day": "monday",
  "handoff_time": "09:00:00"
}

Response 201:
{
  "id": "sched_sre_primary",
  "name": "primary-sre-rotation",
  "rotation_type": "weekly",
  "current_on_call": { "user_id": "u_alice", "started_at": "2026-05-25T09:00:00Z" },
  "created_at": "2026-05-27T12:00:00Z"
}
```

**create escalation policy:**
```json
POST /api/v2/escalation-policies
{
  "name": "sre-escalation",
  "description": "SRE escalation: every 15 min, escalate to next tier",
  "rules": [
    {
      "escalation_delay_minutes": 15,
      "targets": [
        { "type": "schedule", "id": "sched_sre_primary" },
        { "type": "user", "id": "u_alice" }
      ]
    },
    {
      "escalation_delay_minutes": 30,
      "targets": [
        { "type": "schedule", "id": "sched_sre_secondary" }
      ]
    },
    {
      "escalation_delay_minutes": 60,
      "targets": [
        { "type": "user", "id": "u_manager" },
        { "type": "webhook", "url": "https://hooks.slack.com/services/xxx" }
      ]
    }
  ]
}
```

**create incident:**
```json
POST /api/v2/incidents
{
  "title": "High latency on api.example.com",
  "severity": "critical",
  "source": "prometheus",
  "source_id": "alert-abc-123",
  "description": "P99 latency > 5s for 10 minutes on api-prod-01",
  "affected_components": ["api-gateway", "user-service"],
  "escalation_policy_id": "pol_sre_escalation"
}

Response 201:
{
  "id": "inc_20260527_001",
  "status": "detecting",
  "acknowledged_by": null,
  "on_call_paged": true,
  "created_at": "2026-05-27T12:05:00Z",
  "timeline": [
    { "ts": "2026-05-27T12:05:00Z", "type": "created", "detail": "Incident created from Prometheus alert" }
  ]
}
```

**resolve incident:**
```json
POST /api/v2/incidents/inc_20260527_001/resolve
{
  "resolved_by": "u_alice",
  "resolution_notes": "Scaled up API replicas from 3 to 6, latency returned to normal",
  "root_cause": "CPU saturation due to traffic spike after product launch"
}

Response 200:
{
  "id": "inc_20260527_001",
  "status": "resolved",
  "resolved_by": "u_alice",
  "resolved_at": "2026-05-27T12:45:00Z",
  "duration_minutes": 40
}
```

**status page (public json):**
```json
GET /api/v2/status-pages/sp_infrapilot/public

Response 200:
{
  "page_name": "Infra Pilot Status",
  "overall_status": "degraded_performance",
  "components": [
    { "name": "API Gateway", "status": "operational" },
    { "name": "Dashboard", "status": "operational" },
    { "name": "User Service", "status": "degraded_performance" }
  ],
  "active_incidents": [
    {
      "id": "inc_20260527_001",
      "title": "High latency on api.example.com",
      "status": "resolved",
      "created_at": "2026-05-27T12:05:00Z",
      "resolved_at": "2026-05-27T12:45:00Z"
    }
  ],
  "updated_at": "2026-05-27T12:46:00Z"
}
```

## 5. data model

### 5.1 `oncall_schedules`

| column | type | description |
|--------|------|-------------|
| id | varchar(64) (pk) | human-readable slug |
| name | varchar(128) | display name |
| description | text | optional description |
| timezone | varchar(64) | iana timezone |
| rotation_type | enum | `weekly`, `daily`, `custom` |
| shift_start | time | when shift begins |
| shift_duration_hours | int | length of each shift |
| handoff_day | varchar(16) | day of week for handoff |
| handoff_time | time | time of handoff |
| created_by | uuid (fk to users) | creator |
| created_at | timestamptz | creation |
| updated_at | timestamptz | last update |

### 5.2 `oncall_members`

| column | type | description |
|--------|------|-------------|
| id | uuid (pk) | auto-generated |
| schedule_id | varchar(64) (fk) | parent schedule |
| user_id | uuid (fk to users) | team member |
| rank | int | 1 = primary, 2 = secondary, etc. |
| is_active | boolean | whether currently participating |

### 5.3 `oncall_overrides`

| column | type | description |
|--------|------|-------------|
| id | uuid (pk) | auto-generated |
| schedule_id | varchar(64) (fk) | parent schedule |
| original_user_id | uuid (fk to users) | who is being replaced |
| replacement_user_id | uuid (fk to users) | replacement |
| starts_at | timestamptz | override start |
| ends_at | timestamptz | override end |
| reason | text | justification |
| created_by | uuid (fk to users) | who created override |

### 5.4 `escalation_policies`

| column | type | description |
|--------|------|-------------|
| id | varchar(64) (pk) | human-readable slug |
| name | varchar(128) | display name |
| rules | jsonb | array of escalation rules with targets and delays |
| created_by | uuid (fk to users) | creator |
| created_at | timestamptz | creation |
| updated_at | timestamptz | last update |

### 5.5 `incidents`

| column | type | description |
|--------|------|-------------|
| id | varchar(64) (pk) | e.g., `inc_20260527_001` |
| title | text | short description |
| severity | enum | `critical`, `major`, `minor`, `warning` |
| status | enum | `detecting`, `acknowledged`, `investigating`, `resolving`, `resolved` |
| source | varchar(64) | detection source (prometheus, pagerduty, manual) |
| source_id | varchar(128) | external alert id |
| description | text | full description |
| affected_components | text[] | list of affected services |
| escalation_policy_id | varchar(64) (fk) | active escalation policy |
| acknowledged_by | uuid (fk to users, nullable) | who acknowledged |
| acknowledged_at | timestamptz | when acknowledged |
| resolved_by | uuid (fk to users, nullable) | who resolved |
| resolved_at | timestamptz | when resolved |
| resolution_notes | text | how it was resolved |
| root_cause | text | identified rca |
| created_at | timestamptz | creation |
| updated_at | timestamptz | last update |

### 5.6 `incident_timeline`

| column | type | description |
|--------|------|-------------|
| id | bigserial (pk) | auto-increment |
| incident_id | varchar(64) (fk) | parent incident |
| entry_type | enum | `created`, `acknowledged`, `note`, `escalated`, `resolved`, `reopened` |
| detail | text | free-text entry |
| actor_id | uuid (fk to users, nullable) | who created entry |
| created_at | timestamptz | immutable timestamp |

### 5.7 `post_mortems`

| column | type | description |
|--------|------|-------------|
| id | uuid (pk) | auto-generated |
| incident_id | varchar(64) (fk, nullable) | related incident |
| title | varchar(256) | post-mortem title |
| template_id | uuid (fk to templates) | template used |
| content | jsonb | structured fields based on template |
| document | text | rendered markdown |
| created_by | uuid (fk to users) | author |
| created_at | timestamptz | creation |
| updated_at | timestamptz | last update |

### 5.8 `post_mortem_templates`

| column | type | description |
|--------|------|-------------|
| id | uuid (pk) | auto-generated |
| name | varchar(128) | template name |
| schema | jsonb | field definitions (title, summary, timeline, rca, action-items) |
| markdown_template | text | go template / handlebars template for rendering |
| created_by | uuid (fk to users) | creator |

### 5.9 `status_pages`

| column | type | description |
|--------|------|-------------|
| id | uuid (pk) | auto-generated |
| name | varchar(128) | status page title |
| subdomain | varchar(64) | e.g., `status.example.com` |
| is_public | boolean | whether publicly accessible |
| components | jsonb | list of service components and their status |
| custom_css | text | optional custom styling |
| created_by | uuid (fk to users) | creator |
| created_at | timestamptz | creation |
| updated_at | timestamptz | last update |

## 6. service assignments

| service | responsibilities |
|---------|-----------------|
| **integration service** (primary) | on-call scheduling engine, escalation engine, incident lifecycle, post-mortem crud, status page generator |
| **notification service** | slack alerts, email notifications, sms (via twilio) for incident state changes |
| **pagerduty (external)** | on-call schedule sync source-of-truth, alert routing |
| **opsgenie (external)** | on-call schedule sync source-of-truth, alert routing |
| **database** | all schedule, incident, post-mortem, and status page data |

## 7. integration patterns

### 7.1 pagerduty sync

```yaml
# Configuration
pagerduty:
  api_token: ${PAGERDUTY_API_TOKEN}
  sync_interval_seconds: 300
  webhook_secret: ${PAGERDUTY_WEBHOOK_SECRET}

# Sync flow:
# 1. Every 5 min, pull on-call schedules from PagerDuty API
# 2. Map PD schedules to local oncall_schedules by external_id
# 3. Update local oncall_members with current on-call users
# 4. When an alert fires in PD → webhook → creates incident
# 5. When incident is resolved in Infra Pilot → push to PD
```

### 7.2 escalation timer flow

```
1. Incident created → status = "detecting"
2. Escalation timer starts (based on escalation_policy first rule delay)
3. If not acknowledged within delay → execute escalation rule targets
   ├── Page on-call schedule (via PagerDuty/Opsgenie/notification)
   └── Move to next escalation rule, restart timer with that delay
4. If acknowledged → status = "acknowledged", timer cancelled
5. If acknowledged but not resolved within policy threshold → re-escalate
```

## 8. effort estimate

| phase | person-days |
|-------|-------------|
| phase 1: on-call scheduling | 2-3 pt |
| phase 2: incident lifecycle | 2-3 pt |
| phase 3: integrations & status page | 3-4 pt |
| **total** | **7-10 pt** |

## 9. future enhancements

- runbook automation (attach automated remediation to incident types)
- sla breach prediction and alerting
- incident metrics dashboard (mttd, mttr, etc.)
- ai-powered root cause suggestion
- video/voice conference bridge auto-creation on incident open
- multi-region status page aggregation
