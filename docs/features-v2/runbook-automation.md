# Feature 31: Runbook Automation

- **Feature ID:** 31
- **Status:** Planned
- **Priority:** High
- **Primary Service:** Orchestrator Agent
- **Effort:** Medium (4–6 PT)

---

## 1. Overview

Runbook Automation enables operators to define, version, and execute structured runbooks directly from the Orchestrator Agent. Runbooks are YAML-based procedural documents that codify incident response, maintenance procedures, and recovery workflows. They support automated steps (commands, API calls), manual gates (approval checkpoints), conditional branching, rollback on failure, and multiple trigger sources (alerts, button clicks, cron schedules).

The goal is to eliminate tribal knowledge, reduce mean-time-to-recovery (MTTR), and provide a repeatable, auditable execution trail for every operational procedure.

---

## 2. Architecture

```
┌──────────────────┐     Trigger Sources     ┌──────────────────────┐
│  Alert Manager   │ ── on_firing ────────▶  │                      │
├──────────────────┤                         │   Orchestrator      │
│  Web UI Button   │ ── manual_trigger ────▶  │   Agent             │
├──────────────────┤                         │                      │
│  Cron Scheduler  │ ── scheduled ─────────▶  │  ┌──────────────┐   │
└──────────────────┘                         │  │ Runbook      │   │
                                             │  │ Engine       │   │
┌──────────────────┐                         │  │              │   │
│  Runbook Store   │ ◀── fetch YAML ──────── │  │ • Step Exec  │   │
│  (Git repo / DB) │                         │  │ • Gate Check │   │
└──────────────────┘                         │  │ • Rollback   │   │
                                             │  │ • History    │   │
┌──────────────────┐                         │  └──────┬───────┘   │
│  Execution Logs  │ ◀── append ──────────── │         │           │
│  (Event Store)   │                         │         ▼           │
└──────────────────┘                         │  ┌──────────────┐   │
                                             │  │ Target Infra │   │
                                             │  │ (Docker, API)│   │
                                             │  └──────────────┘   │
                                             └──────────────────────┘
```

**Components:**

| Component | Role |
|---|---|
| Runbook Store | Persistent storage for runbook YAML definitions (Git-based for versioning) |
| Runbook Engine | Core execution loop inside Orchestrator Agent; parses YAML, executes steps, evaluates gates |
| Step Executor | Dispatches individual steps (shell commands, HTTP calls, manual tasks) |
| Rollback Manager | Tracks state before each mutation; reverses changes on failure or interrupt |
| Event Recorder | Writes execution lifecycle events into the Event Store for audit and replay |

---

## 3. Runbook YAML Format

Each runbook is a single YAML file with the following top-level structure:

```yaml
apiVersion: infra-pilot/v1
kind: Runbook
metadata:
  name: restart-postgres-primary
  description: "Restart the PostgreSQL primary node with a rolling drain."
  tags:
    - database
    - postgres
    - recovery
  owner: "team-platform"

spec:
  # ----- Trigger Configuration -----
  triggers:
    - type: alert
      source: prometheus
      condition: alertname == "PostgresPrimaryDown"
    - type: schedule
      cron: "0 3 * * 0"   # every Sunday at 03:00 UTC
    - type: manual
      label: "Restart Postgres Primary"

  # ----- Default Behaviour -----
  timeout: 300             # max execution seconds
  rollbackOnFailure: true
  concurrency: forbid      # forbid | allow | queue

  # ----- Environment Variables -----
  env:
    PGHOST: "{{ .target.host }}"
    PGUSER: "{{ .secrets.pg_user }}"

  # ----- Steps -----
  steps:
    - id: drain-connections
      name: "Drain active connections"
      type: command
      shell: psql
      args:
        - "-c"
        - "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'appdb';"
      timeout: 30
      onFailure: abort     # abort | skip | next

    - id: notify-slack
      name: "Notify Slack channel"
      type: api_call
      method: POST
      url: "{{ .secrets.slack_webhook }}"
      body:
        text: "Restarting Postgres primary ({{ .runbook.metadata.name }})…"
      headers:
        Content-Type: application/json
      onFailure: skip

    - id: manual-approve
      name: "Approve restart window"
      type: manual_gate
      message: |
        Confirm that the secondary is caught up and you are ready to proceed.
        Run: `SHOW pg_stat_replication` on the standby before approving.
      approvers:
        - team: platform
        - user: "oncall-admin"
      timeout: 300           # must approve within 5 minutes

    - id: restart-service
      name: "Restart postgres container"
      type: command
      shell: docker
      args:
        - restart
        - "{{ .target.container_id }}"
      timeout: 60

    - id: verify-health
      name: "Verify primary is healthy"
      type: api_call
      method: GET
      url: "http://{{ .target.host }}:8008/health"
      expected:
        statusCode: 200
        jsonPath: "$.status"
        equals: "running"
      timeout: 30

  # ----- Rollback Steps (reverse order of execution) -----
  rollback:
    - id: rollback-restart
      name: "Restart previous primary if health check fails"
      type: command
      shell: docker
      args:
        - restart
        - "{{ .target.previous_primary }}"
```

**Step Types:**

| Type | Description |
|---|---|
| `command` | Execute a shell command with args, capture stdout/stderr |
| `api_call` | HTTP request with method, URL, body, headers, and expected-response assertions |
| `manual_gate` | Pause execution until approved or rejected by specified users |
| `sub_runbook` | Invoke another runbook by name (nested composition) |
| `condition` | Evaluate a CEL expression and branch to different step IDs |
| `log` | Write an informational message to the execution log without an action |

---

## 4. Execution Lifecycle

```
  ┌─────────────┐
  │  Pending    │  ← Queued, waiting for concurrency slot
  └──────┬──────┘
         ▼
  ┌─────────────┐
  │  Running    │  ← Engine is iterating through steps
  └──────┬──────┘
         │
    ┌────┴────┐
    ▼         ▼
  ┌──────┐ ┌──────┐
  │ Step │ │ Gate │  ← Each step/gate evaluated sequentially
  │ OK   │ │ Wait │
  └──┬───┘ └──┬───┘
     │        │
     ▼        ▼
  ┌─────────────┐
  │  Waiting    │  ← Manual gate pending approval
  └──────┬──────┘
         ▼
  ┌─────────────┐
  │  Approved   │  ← Continue to next step
  └──────┬──────┘
         ▼
  ┌─────────────┐
  │  Succeeded  │  ← All steps completed
  ├─────────────┤     OR
  │  Failed     │  ← Step aborted, rollback executed
  ├─────────────┤     OR
  │  Rejected   │  ← Manual gate denied
  ├─────────────┤     OR
  │  Timed Out  │  ← Execution exceeded spec.timeout
  └─────────────┘
```

---

## 5. API Design (Orchestrator Agent — Internal gRPC / HTTP)

### 5.1 Runbook CRUD

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/runbooks` | Create / register a runbook definition |
| `GET` | `/api/v1/runbooks` | List all runbooks (filterable by tag, owner) |
| `GET` | `/api/v1/runbooks/{id}` | Get runbook definition + latest version |
| `PUT` | `/api/v1/runbooks/{id}` | Update runbook definition |
| `DELETE` | `/api/v1/runbooks/{id}` | Soft-delete a runbook |

### 5.2 Execution

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/runbooks/{id}/execute` | Trigger execution (supports override env vars) |
| `GET` | `/api/v1/executions/{exec_id}` | Get execution status, step results, logs |
| `POST` | `/api/v1/executions/{exec_id}/cancel` | Cancel a running execution |
| `POST` | `/api/v1/executions/{exec_id}/approve` | Approve a pending manual gate |
| `POST` | `/api/v1/executions/{exec_id}/reject` | Reject a pending manual gate |
| `GET` | `/api/v1/executions` | List execution history (paginated, filterable) |

### 5.3 gRPC Protobuf (core service contract)

```protobuf
service RunbookService {
  rpc CreateRunbook (CreateRunbookRequest) returns (Runbook);
  rpc GetRunbook (GetRunbookRequest) returns (Runbook);
  rpc ListRunbooks (ListRunbooksRequest) returns (ListRunbooksResponse);
  rpc UpdateRunbook (UpdateRunbookRequest) returns (Runbook);
  rpc DeleteRunbook (DeleteRunbookRequest) returns (Empty);

  rpc ExecuteRunbook (ExecuteRunbookRequest) returns (Execution);
  rpc GetExecution (GetExecutionRequest) returns (Execution);
  rpc CancelExecution (CancelExecutionRequest) returns (Execution);
  rpc ApproveGate (ApproveGateRequest) returns (Execution);
  rpc RejectGate (RejectGateRequest) returns (Execution);
  rpc ListExecutions (ListExecutionsRequest) returns (ListExecutionsResponse);
}
```

---

## 6. Data Model

```json
{
  "runbook": {
    "id": "uuid",
    "name": "string",
    "description": "string",
    "api_version": "infra-pilot/v1",
    "spec": {
      "triggers": [{"type": "string", "source": "string", "condition": "string"}],
      "timeout": 300,
      "rollback_on_failure": true,
      "concurrency": "forbid",
      "env": {"key": "value"},
      "steps": [
        {
          "id": "string",
          "name": "string",
          "type": "command|api_call|manual_gate|sub_runbook|condition|log",
          "shell": "string",
          "args": ["string"],
          "timeout": 30,
          "on_failure": "abort|skip|next",
          "approvers": [{"team": "string", "user": "string"}]
        }
      ],
      "rollback": [{"same structure as steps"}]
    },
    "created_at": "rfc3339",
    "updated_at": "rfc3339",
    "version": 42
  },

  "execution": {
    "id": "uuid",
    "runbook_id": "uuid",
    "status": "pending|running|waiting|succeeded|failed|rejected|timed_out",
    "trigger": {"type": "string", "source": "string"},
    "env_overrides": {},
    "current_step_id": "string",
    "steps": [
      {
        "id": "string",
        "status": "pending|running|succeeded|failed|skipped",
        "started_at": "rfc3339",
        "finished_at": "rfc3339",
        "output": "string",
        "error": "string"
      }
    ],
    "rollback_executed": false,
    "created_at": "rfc3339",
    "finished_at": "rfc3339"
  }
}
```

---

## 7. Service Assignments

| Service | Responsibilities |
|---|---|
| **Orchestrator Agent** | Runbook Engine execution, step dispatch, gate evaluation, rollback, concurrency |
| **Management Panel** | Runbook editor UI, manual trigger buttons, approval UI, execution history viewer |
| **Integration Service** | Route alert-triggered executions from Alert Manager to Orchestrator |
| **Event Store** | Persist execution logs and lifecycle events for audit trail |
| **Identity & Access** | Authorize who can create, execute, approve runbooks (RBAC) |

---

## 8. Effort Estimate

| Phase | Tasks | PT |
|---|---|---|
| Design | YAML schema spec, protobuf contracts, state machine design | 1 |
| Core Engine | Runbook parser, step executor, gate evaluator, rollback manager | 1.5 |
| Triggers | Alert webhook listener, cron scheduler integration, manual trigger | 0.5 |
| API & Persistence | CRUD endpoints, execution endpoints, runbook/execution stores | 1 |
| Management UI | Runbook editor, execution viewer, approval dialogs | 1 |
| Testing & Docs | Integration tests, runbook examples, operator guide | 0.5 |
| **Total** | | **4–6** |

---

## 9. Dependencies

- Orchestrator Agent must be deployed and reachable
- Git repository or database for runbook storage (recommend Git for versioning)
- Credential/secret store for environment variable injection (Vault / K8s Secrets)
- RBAC service for manual gate approval authorization

---

## 10. Future Considerations

- **Parallel steps**: Allow steps to execute in a DAG rather than strict linear order
- **Runbook templates**: Parameterized runbooks with user-supplied input forms
- **Automated rollback tests**: Dry-run mode that validates rollback paths without mutating infra
- **Metrics**: Track runbook duration, failure rate, gate approval latency as Prometheus metrics
