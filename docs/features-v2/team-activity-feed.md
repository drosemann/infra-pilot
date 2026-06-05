# Feature 33: Team Activity Feed

- **Feature ID:** 33
- **Status:** Planned
- **Priority:** Medium
- **Primary Service:** Management Panel
- **Effort:** Small (1–3 PT)

---

## 1. Overview

The Team Activity Feed provides a unified, chronological stream of all actions performed by team members across infra-pilot services. Every mutation — server creation, runbook execution, dashboard edit, alert acknowledgement — is recorded as an event and surfaced in a filterable, searchable, real-time feed. Users can export the feed (CSV / JSON) for auditing and compliance.

---

## 2. Architecture

```
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│ Orchestrator     │    │ Management       │    │ Integration      │
│ Agent            │    │ Panel            │    │ Service          │
│                  │    │                  │    │                  │
│ runbook_executed │    │ dashboard_edited │    │ alert_acknowledged
│ server_created   │    │ kb_article_written    │ webhook_sent     │
└────────┬─────────┘    └────────┬─────────┘    └────────┬─────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │     Event Bus          │
                    │  (NATS / Redis PubSub) │
                    └────────────┬───────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │  Activity Feed Service │
                    │                        │
                    │  ┌──────────────────┐  │
                    │  │ Event Ingest     │  │
                    │  │ (subscribe →     │  │
                    │  │  normalize →     │  │
                    │  │  enrich → store) │  │
                    │  └──────────────────┘  │
                    │  ┌──────────────────┐  │
                    │  │ Event Store      │  │
                    │  │ (TimescaleDB /   │  │
                    │  │  PostgreSQL)     │  │
                    │  └──────────────────┘  │
                    │  ┌──────────────────┐  │
                    │  │ Real-Time Hub    │  │
                    │  │ (WebSocket       │  │
                    │  │  fan-out)        │  │
                    │  └──────────────────┘  │
                    │  ┌──────────────────┐  │
                    │  │ Export Engine    │  │
                    │  │ (CSV, JSON)      │  │
                    │  └──────────────────┘  │
                    └────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
                    ▼                         ▼
           ┌─────────────────┐     ┌─────────────────┐
           │ Management Panel│     │ External Audit  │
           │ (Web UI)        │     │ (SIEM, Log      │
           │ + WebSocket     │     │  Archive)        │
           └─────────────────┘     └─────────────────┘
```

---

## 3. Event Model

Every event follows a normalized schema:

```json
{
  "id": "evt_01J2ABC…",
  "timestamp": "2026-05-27T14:30:00Z",
  "service": "orchestrator",
  "actor": {
    "user_id": "usr_abc123",
    "username": "alice",
    "source": "ui"           // "ui" | "api" | "system" | "webhook"
  },
  "action": "runbook.executed",
  "resource": {
    "type": "runbook",
    "id": "rb_xyz456",
    "name": "Restart Postgres Primary"
  },
  "details": {
    "execution_id": "exec_789",
    "status": "succeeded",
    "duration_ms": 45200
  },
  "metadata": {
    "ip_address": "10.0.1.42",
    "user_agent": "Mozilla/5.0 …",
    "correlation_id": "corr_111"
  }
}
```

**Event taxonomy (action field):**

| Category | Events |
|---|---|
| `server.*` | `server.created`, `server.updated`, `server.deleted`, `server.config_changed` |
| `runbook.*` | `runbook.executed`, `runbook.gate_approved`, `runbook.gate_rejected`, `runbook.cancelled` |
| `dashboard.*` | `dashboard.created`, `dashboard.updated`, `dashboard.deleted`, `dashboard.shared` |
| `kb.*` | `kb.article.created`, `kb.article.updated`, `kb.article.deleted`, `kb.article.restored` |
| `alert.*` | `alert.acknowledged`, `alert.resolved`, `alert.silenced` |
| `auth.*` | `auth.login`, `auth.logout`, `auth.permission_changed` |
| `system.*` | `system.config_updated`, `system.backup_completed`, `system.health_check_failed` |

---

## 4. API Design

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/feed` | Query the activity feed (paginated) |
| `GET` | `/api/v1/feed/stream` | WebSocket upgrade for real-time events |
| `GET` | `/api/v1/feed/export` | Export filtered feed as CSV or JSON |
| `GET` | `/api/v1/feed/actions` | List all known action types (taxonomy) |

### Query Parameters (`GET /api/v1/feed`)

| Param | Type | Example | Description |
|---|---|---|---|
| `limit` | int | `50` | Page size (max 200) |
| `offset` | int | `0` | Pagination offset |
| `since` | RFC3339 | `2026-05-01T00:00:00Z` | Include events after this time |
| `until` | RFC3339 | `2026-05-27T23:59:59Z` | Include events before this time |
| `service` | string | `orchestrator` | Filter by source service |
| `action` | string | `runbook.*` | Glob pattern over action field |
| `actor` | string | `alice` | Filter by username |
| `resource_type` | string | `server` | Filter by resource type |
| `resource_id` | string | `srv_abc123` | Filter by specific resource |
| `search` | string | `postgres restart` | Full-text search over details |
| `sort` | string | `-timestamp` | `timestamp` asc or `-timestamp` desc |

### WebSocket (`/api/v1/feed/stream`)

```javascript
// Client connects:
const ws = new WebSocket("wss://infra-pilot.example.com/api/v1/feed/stream");

// Sends subscription filter (optional):
ws.send(JSON.stringify({
  "filter": { "actions": ["runbook.*", "alert.*"] }
}));

// Receives events in real-time:
ws.onmessage = (msg) => {
  const event = JSON.parse(msg.data);
  console.log(`${event.actor.username} ${event.action}`);
};
```

### Export

| Method | `GET /api/v1/feed/export` |
|---|---|
| Query params | Same as feed query + `format=csv` or `format=json` |
| Response | `Content-Disposition: attachment; filename="activity-feed-2026-05-27.csv"` |

---

## 5. Data Model

```sql
CREATE TABLE activity_events (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    service        VARCHAR(50)  NOT NULL,
    actor_user_id  VARCHAR(255),
    actor_username VARCHAR(255),
    actor_source   VARCHAR(20)  NOT NULL DEFAULT 'ui',
    action         VARCHAR(100) NOT NULL,
    resource_type  VARCHAR(50),
    resource_id    VARCHAR(255),
    resource_name  VARCHAR(500),
    details        JSONB,
    metadata       JSONB,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Partition by month for performance
CREATE INDEX idx_events_timestamp    ON activity_events(timestamp DESC);
CREATE INDEX idx_events_action       ON activity_events(action);
CREATE INDEX idx_events_actor        ON activity_events(actor_username);
CREATE INDEX idx_events_resource     ON activity_events(resource_type, resource_id);
CREATE INDEX idx_events_details_gin  ON activity_events USING GIN (details jsonb_path_ops);
```

---

## 6. Service Assignments

| Service | Responsibilities |
|---|---|
| **Management Panel** | Activity feed UI, infinite-scroll list, filter controls, search bar, real-time WebSocket subscription, export button |
| **Activity Feed Service** | Event ingestion (subscribe to Event Bus), normalization, enrichment (resolve actor display name, resource name), persistence, WebSocket fan-out, export generation |
| **Event Bus** | Central pub/sub channel; all services publish mutations as events |
| **All Services** | Publish events to the Event Bus on every user-initiated mutation |

---

## 7. Effort Estimate

| Phase | Tasks | PT |
|---|---|---|
| Design | Event taxonomy, API contracts, data model | 0.5 |
| Event Ingest | Subscribe to Event Bus, normalise and store incoming events | 0.5 |
| Feed API | List with filters, pagination, search, export endpoint | 0.5 |
| WebSocket Hub | Real-time fan-out per client subscription filter | 0.5 |
| Management UI | Feed component, filter bar, search, export button, live updates | 0.5 |
| Service integration | Instrument remaining services to publish events | 0.5 |
| **Total** | | **1–3** |

---

## 8. Future Considerations

- **Webhook output**: Push critical events to external SIEM via webhook
- **Retention policies**: Configurable TTL per action type (e.g. keep auth.* for 1 year, system.* for 30 days)
- **Personal feed**: Each user sees only events scoped to their team/projects
- **Reactions**: Comment or react to events for team collaboration
