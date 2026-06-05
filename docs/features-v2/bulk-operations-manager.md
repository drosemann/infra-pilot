# feature 45: bulk operations manager

- feature id: 45
- status: planned
- priority: high
- primary service: management panel
- effort estimate: medium (4-6 pt)
- dependencies: feature 43 (keyboard navigation for multi-select)

## overview

provide a guided workflow that lets operators select multiple servers (or other resources) and apply a batch action — start, stop, reboot, backup, tag, change plan, or decommission. the feature includes a persistent progress tracker, per-item status reporting, undo/rollback capability, and a full audit trail.

### goals

• support batch actions on up to 500 servers in a single operation.
• real-time progress (server-sent events or websocket push).
• rollback of failed/cancelled operations where the target action supports it.
• full action history visible in the management panel.

## architecture & component map

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Management Panel (Frontend)                     │
│                                                                     │
│  ┌──────────────────────┐   ┌──────────────────────────────────┐   │
│  │  ServerTable          │   │  BulkActionBar                   │   │
│  │  (multi-select rows)  │   │  [Start] [Stop] [Backup] [...]  │   │
│  │  checkbox per row     │   │  Shows "N selected"              │   │
│  └──────────┬───────────┘   └────────────┬─────────────────────┘   │
│             │                            │                          │
│  ┌──────────▼────────────────────────────▼──────────────────────┐  │
│  │  ConfirmationDialog                                           │  │
│  │  • summary of what will happen                                │  │
│  │  • "Apply to N servers — proceed?"                            │  │
│  │  • optional dry-run preview                                   │  │
│  └──────────────────────────┬────────────────────────────────────┘  │
│                             │                                        │
│  ┌──────────────────────────▼────────────────────────────────────┐  │
│  │  ProgressPanel (persistent drawer / page)                     │  │
│  │  • SSE / WS connection → live per-server status               │  │
│  │  • progress bar (completed / failed / total)                  │  │
│  │  • expandable row list: ✓ serverA, ✗ serverB (error), ...    │  │
│  │  • "Rollback" button for reversible actions                   │  │
│  └──────────────────────────┬────────────────────────────────────┘  │
│                             │                                        │
│  ┌──────────────────────────▼────────────────────────────────────┐  │
│  │  ActionHistory (tab in settings)                              │  │
│  │  • table of past bulk operations                              │  │
│  │  • filter by action, date, status                             │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  Backend (API Gateway + Worker)                                     │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  POST /api/v2/bulk/actions  →  returns bulkOperationId        │ │
│  │  GET  /api/v2/bulk/actions/:id  →  status + per-item results  │ │
│  │  POST /api/v2/bulk/actions/:id/rollback                       │ │
│  │  GET  /api/v2/bulk/actions/history  →  paginated history      │ │
│  │  WS   /api/v2/bulk/actions/:id/stream  →  live events         │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

## implementation plan

### phase 1 — backend api & worker (2 pt)

• bulk operation model & table (see §5).
• `POST /api/v2/bulk/actions`
  - accepts `{ action, resourceType, resourceIds, params }`.
  - validates that all resources exist and are in a valid state for the action (e.g., cannot "start" an already-running server).
  - creates a `bulk_operations` row with status `pending`.
  - enqueues an async job (redis queue / in-process goroutine).
• worker
  - pulls job, iterates over `resourceIds`.
  - for each item: calls the relevant service (e.g., `compute.start(serverId)`, `backup.create(serverId, params)`) and records result.
  - updates progress counters in db every n items.
  - on failure: continues remaining items (no fail-fast unless `failFast: true` flag is set).
  - on completion: sets `completed_at` and final status.
• get endpoint returns current progress, per-item results array.
• websocket endpoint pushes `BulkProgressEvent` to connected clients.

### phase 2 — multi-select ui & action bar (1-1.5 pt)

• extend `ServerTable` with per-row `<input type="checkbox">`.
• add a "select all" checkbox in the header (toggles current page; option "select all n items across all pages").
• `BulkActionBar` — a sticky bar that appears when ≥ 1 item is selected.
  - shows count ("3 servers selected").
  - dropdown of applicable actions (filtered by resource state).
  - "select all matching" button for cross-page selection.
• `ConfirmationDialog` — shows summary of the action; allows optional parameters (e.g., backup retention days). provides a "dry-run" toggle that lists items that would fail validation.

### phase 3 — progress & rollback (1 pt)

• `ProgressPanel` — a right-side drawer (or full-page route) opened automatically after confirmation.
  - overall progress bar: `(completed + failed) / total`.
  - per-item table: server name, status (pending / running / success / failed), error message.
  - status colours with aria labels (f43 compliance).
• rollback
  - post to `/rollback` triggers a new bulk operation that reverses the original actions (e.g., stop → start, tag-add → tag-remove).
  - rollback operation is linked to the original via `rolled_back_from`.
  - only available for actions that define a `revert` handler.

### phase 4 — action history (0.5 pt)

• history page/panel — paginated table of past bulk operations.
• columns: date, action name, resource count, status (success / partial / failed), duration, rollback link.
• allows re-execution of the same action on the same resource set.

## api design

### endpoints

| method | path | description |
|---|---|---|
| `POST` | `/api/v2/bulk/actions` | start a new bulk operation |
| `GET` | `/api/v2/bulk/actions/:id` | get operation status + results |
| `POST` | `/api/v2/bulk/actions/:id/cancel` | cancel a running operation |
| `POST` | `/api/v2/bulk/actions/:id/rollback` | rollback a completed/failed op |
| `GET` | `/api/v2/bulk/actions/history` | list past operations (paginated) |
| `WS` | `/api/v2/bulk/actions/:id/stream` | live progress events |

### start operation — request

```json
POST /api/v2/bulk/actions
{
  "action": "start",
  "resourceType": "server",
  "resourceIds": ["srv-001", "srv-002", "srv-003"],
  "params": {},
  "failFast": false
}
```

### start operation — response

```json
HTTP 202
{
  "id": "bulk-a1b2c3d4",
  "status": "pending",
  "total": 3,
  "completed": 0,
  "failed": 0,
  "createdAt": "2026-05-27T10:00:00Z"
}
```

### progress stream (websocket event)

```json
{
  "type": "BulkProgressEvent",
  "operationId": "bulk-a1b2c3d4",
  "itemId": "srv-002",
  "status": "success",
  "completed": 2,
  "failed": 0,
  "total": 3,
  "timestamp": "2026-05-27T10:00:05Z"
}
```

## data model

### postgresql

```sql
CREATE TYPE bulk_action AS ENUM (
  'start', 'stop', 'reboot', 'backup',
  'tag', 'change_plan', 'decommission'
);

CREATE TYPE bulk_status AS ENUM (
  'pending', 'running', 'completed',
  'partial', 'failed', 'cancelled'
);

CREATE TABLE bulk_operations (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  action        bulk_action NOT NULL,
  resource_type VARCHAR(64) NOT NULL,
  resource_ids  UUID[] NOT NULL,
  params        JSONB NOT NULL DEFAULT '{}',
  status        bulk_status NOT NULL DEFAULT 'pending',
  progress      JSONB NOT NULL DEFAULT '{}',
  -- progress example: { "completed": 5, "failed": 1, "total": 50, "items": [{ "id": "srv-001", "status": "success" }, ...] }
  fail_fast     BOOLEAN NOT NULL DEFAULT false,
  rolled_back_from UUID REFERENCES bulk_operations(id),
  created_by    UUID NOT NULL REFERENCES users(id),
  started_at    TIMESTAMPTZ,
  completed_at  TIMESTAMPTZ,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_bulk_ops_created_by ON bulk_operations (created_by, created_at DESC);
```

### per-item result (embedded in `progress.items`)

```typescript
interface BulkItemResult {
  resourceId: string;
  status: 'pending' | 'running' | 'success' | 'failed';
  error?: string;
  startedAt?: string;     // ISO
  completedAt?: string;   // ISO
  result?: unknown;       // action-specific payload
}
```

## service assignments

| service | role |
|---|---|
| management panel | multi-select ui, confirmation dialog, progress panel, history |
| api gateway | bulk action crud endpoints, websocket upgrade |
| worker (async) | processes bulk operations sequentially per item |
| database | `bulk_operations` table |
| compute / backup | target services that execute individual actions (called by worker) |

## effort estimate

| phase | person-days |
|---|---|
| backend api & worker | 2 |
| multi-select ui & action bar | 1-1.5 |
| progress panel & rollback | 1 |
| action history | 0.5 |
| total | **4-6** |

## acceptance criteria

• user can select multiple servers via checkboxes (including "select all across pages").
• bulk action bar appears when ≥ 1 item is selected with valid actions.
• confirmation dialog shows action summary and accepts/rejects.
• progress panel updates in real-time via websocket.
• per-item success/failure is displayed.
• rollback is available for supported actions and creates a linked inverse operation.
• action history page lists all past operations with filtering.
• bulk operations can be cancelled while running.
• maximum tested scale: 500 servers per operation.
