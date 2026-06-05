# gitops sync

- feature #: 16
- category: developer ecosystem & api
- primary service: orchestrator agent
- supporting services: integration service, management panel
- effort: large (7-10 pt)
- dependencies: feature #13 (webhook event bus), feature #14 (api gateway & rate limiting)

## 1. overview

gitops sync establishes a two-way reconciliation loop between git repositories and infra pilot infrastructure state. configuration changes committed to a git repository are automatically applied to servers; manual edits made in the management panel create pull requests back to the repository. this enables git-as-source-of-truth workflows compatible with argocd and flux patterns.

### goals

- bi-directional sync: git -> infra (auto-apply) and infra -> git (pr creation)
- drift detection: periodic reconciliation with alerting on divergence
- commit signing and verification for supply-chain security
- branch/tag filters to scope sync to specific environments
- dry-run mode to preview changes before application
- compatible with github, gitlab, bitbucket, and self-hosted gitea

### non-goals

- full git ui (file browser, commit history viewer) -- delegate to git hosting platform
- multi-repo orchestration (dag of dependent repos) -- future feature
- terraform/crossplane state management -- separate iac tooling (feature #12)

## 2. architecture

### high-level component diagram

```
┌──────────────────┐       ┌───────────────────────────────────────┐
│   Git Provider   │       │           Orchestrator Agent          │
│   (GitHub/GitLab)│       │                                       │
│                  │       │  ┌─────────────────────────────────┐  │
│   ┌──────────┐   │       │  │      GitOps Sync Engine         │  │
│   │  Repo    │   │◄──────┼──┤                                 │  │
│   │  (YAML)  │   │       │  │  ┌──────────┐  ┌────────────┐  │  │
│   └────┬─────┘   │       │  │  │  Git     │  │  Drift     │  │  │
│        │         │       │  │  │  Watcher │  │  Detector  │  │  │
│        │ Push/   │       │  │  └────┬─────┘  └──────┬─────┘  │  │
│        │ Webhook │       │  │       │               │         │  │
│        ▼         │       │  │       ▼               ▼         │  │
│   ┌──────────┐   │       │  │  ┌──────────────────────────┐   │  │
│   │ Webhooks │   │───────┼──┼──►  Reconciliation Loop     │   │  │
│   └──────────┘   │       │  │  │  (diff -> apply -> report) │   │  │
└──────────────────┘       │  │  └────────────┬─────────────┘   │  │
                           │  └───────────────┼─────────────────┘  │
                           │                  │                    │
                           │                  ▼                    │
                           │  ┌─────────────────────────────────┐  │
                           │  │   Config Translator             │  │
                           │  │   (YAML/JSON -> API calls)       │  │
                           │  └────────────┬────────────────────┘  │
                           └───────────────┼───────────────────────┘
                                           │
                                           ▼
                           ┌───────────────────────────────────────┐
                           │        Infrastructure State           │
                           │  (Servers, Databases, DNS, Firewalls) │
                           └───────────────────────────────────────┘
                                           ▲
                                           │
┌──────────────────┐       ┌───────────────┼───────────────────────┐
│ Management Panel │       │  Integration Service                   │
│                  │       │                                       │
│  User edits      │──────►│  ┌─────────────────────────────────┐  │
│  server config   │       │  │  PR Creator                     │  │
│                  │       │  │  (branch -> commit -> push -> PR)│  │
└──────────────────┘       │  └─────────────────────────────────┘  │
                           └───────────────────────────────────────┘
```

### sync flow

```
Git Push (or poll interval)
       │
       ▼
Git Watcher detects change
       │
       ▼
Clone/Fetch repo at target ref
       │
       ▼
Config Translator parses YAML/JSON
       │
       ▼
Diff against current infrastructure state
       │
       ├── No diff -> Report "in sync"
       │
       └── Diff found -> Generate plan
              │
              ▼
         Auto-apply enabled?
              │
       ┌──────┴──────┐
       ▼              ▼
      Yes            No
       │              │
       ▼              ▼
  Apply changes   Create PR
  (dry-run first)  (user reviews)
       │              │
       ▼              ▼
  Report result   Update status
```

### panel edit -> pr flow

```
User edits server config in Panel UI
       │
       ▼
Integration Service creates branch (gitops/srv-abc-20260520)
       │
       ▼
Commit config change with signed commit
       │
       ▼
Push branch to remote
       │
       ▼
Create pull request with description
       │
       ▼
Update Panel UI with PR link
       │
       ▼
User merges PR -> Git watcher picks up -> auto-applies
```

## 3. data model

### gitops sync configuration (per-tenant)

```json
{
  "id": "gitops_abc123",
  "tenant_id": "tnt_001",
  "name": "production-cluster",
  "repository": {
    "url": "https://github.com/myorg/infrapilot-config.git",
    "branch": "main",
    "path": "clusters/prod/",
    "auth_method": "deploy_key",
    "deploy_key_id": "key_001",
    "commit_signing_key_id": "gpg_001"
  },
  "sync": {
    "direction": "bidirectional",
    "auto_apply": true,
    "create_pr_on_panel_edit": true,
    "pr_base_branch": "main",
    "pr_label": "infrapilot-sync"
  },
  "schedule": {
    "poll_interval_secs": 300,
    "webhook_enabled": true,
    "webhook_secret_id": "secret_002"
  },
  "filters": {
    "include_paths": ["clusters/prod/**/*.yaml"],
    "exclude_paths": ["clusters/prod/secrets/**"],
    "resource_types": ["server", "database", "dns_record", "firewall_rule"]
  },
  "drift_detection": {
    "enabled": true,
    "alert_on_drift": true,
    "auto_remediate": false,
    "alert_severity": "warning"
  },
  "status": {
    "last_sync": "2026-05-20T12:00:00Z",
    "last_sync_commit": "a1b2c3d4",
    "last_sync_result": "success",
    "current_drift_count": 0,
    "in_sync": true
  }
}
```

### drift record

```json
{
  "id": "drift_001",
  "gitops_config_id": "gitops_abc123",
  "resource_type": "server",
  "resource_id": "srv_prod_web_01",
  "diff": {
    "expected": {
      "cpu_cores": 4,
      "memory_mb": 8192,
      "disk_gb": 100
    },
    "actual": {
      "cpu_cores": 4,
      "memory_mb": 4096,
      "disk_gb": 100
    }
  },
  "severity": "high",
  "status": "unresolved",
  "detected_at": "2026-05-20T12:05:00Z",
  "remediated_at": null
}
```

### git snapshot (cached state for diffing)

```json
{
  "id": "snap_001",
  "gitops_config_id": "gitops_abc123",
  "commit_sha": "a1b2c3d4e5f6...",
  "commit_message": "feat: scale web-01 to 8GB RAM",
  "committer": "Infra Pilot Bot",
  "timestamp": "2026-05-20T12:00:00Z",
  "resources": {
    "server": [
      {
        "id": "srv_prod_web_01",
        "name": "web-01",
        "spec": {
          "cpu_cores": 4,
          "memory_mb": 8192,
          "disk_gb": 100
        }
      }
    ],
    "dns_record": [...],
    "firewall_rule": [...]
  }
}
```

### sql schema

```sql
CREATE TABLE gitops_configs (
    id              TEXT PRIMARY KEY,
    tenant_id       TEXT NOT NULL,
    name            TEXT NOT NULL,
    repo_url        TEXT NOT NULL,
    repo_branch     TEXT NOT NULL DEFAULT 'main',
    repo_path       TEXT NOT NULL DEFAULT '/',
    auth_method     TEXT NOT NULL CHECK(auth_method IN ('deploy_key','personal_token','app_installation')),
    auth_credential_id TEXT,
    commit_signing_key_id TEXT,
    direction       TEXT NOT NULL DEFAULT 'bidirectional' CHECK(direction IN ('git_to_infra','bidirectional')),
    auto_apply      BOOLEAN NOT NULL DEFAULT false,
    create_pr_on_panel_edit BOOLEAN NOT NULL DEFAULT true,
    poll_interval_secs INT NOT NULL DEFAULT 300,
    webhook_secret  TEXT,
    filters_json    JSONB NOT NULL DEFAULT '{}',
    drift_config_json JSONB NOT NULL DEFAULT '{}',
    enabled         BOOLEAN NOT NULL DEFAULT true,
    last_sync_at    TIMESTAMPTZ,
    last_sync_commit TEXT,
    last_sync_result TEXT,
    in_sync         BOOLEAN NOT NULL DEFAULT true,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE drift_records (
    id              TEXT PRIMARY KEY,
    gitops_config_id TEXT NOT NULL REFERENCES gitops_configs(id) ON DELETE CASCADE,
    resource_type   TEXT NOT NULL,
    resource_id     TEXT NOT NULL,
    diff_json       JSONB NOT NULL,
    severity        TEXT NOT NULL CHECK(severity IN ('low','medium','high','critical')),
    status          TEXT NOT NULL DEFAULT 'unresolved' CHECK(status IN ('unresolved','acknowledged','remediated','ignored')),
    detected_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    remediated_at   TIMESTAMPTZ,
    acknowledged_by TEXT REFERENCES users(id)
);

CREATE TABLE git_snapshots (
    id              TEXT PRIMARY KEY,
    gitops_config_id TEXT NOT NULL REFERENCES gitops_configs(id) ON DELETE CASCADE,
    commit_sha      TEXT NOT NULL,
    commit_message  TEXT,
    committer       TEXT,
    resources_json  JSONB NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

## 4. api design

### gitops configuration api (orchestrator agent)

all endpoints prefixed with `/api/v2/gitops`.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/configs` | List GitOps sync configs |
| `POST` | `/configs` | Create new GitOps sync config |
| `GET` | `/configs/{id}` | Get sync config details |
| `PUT` | `/configs/{id}` | Update sync config |
| `DELETE` | `/configs/{id}` | Remove sync config |
| `POST` | `/configs/{id}/sync` | Trigger immediate sync |
| `POST` | `/configs/{id}/dry-run` | Preview changes without applying |
| `GET` | `/configs/{id}/drifts` | List drift records |
| `POST` | `/configs/{id}/drifts/{drift_id}/acknowledge` | Acknowledge drift |

### panel edit -> pr api (integration service)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v2/gitops/pr` | Create PR from Panel edit |
| `GET` | `/api/v2/gitops/pr/{pr_id}` | Get PR status / link |

### webhook receiver (orchestrator agent)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v2/gitops/webhook` | Receive push event from Git provider |

### config translation format

example git repository structure:

```
clusters/
├── prod/
│   ├── servers.yaml
│   ├── databases.yaml
│   ├── dns.yaml
│   └── firewall.yaml
└── staging/
    ├── servers.yaml
    └── databases.yaml
```

example `servers.yaml`:

```yaml
apiVersion: infrapilot.io/v1
kind: Server
metadata:
  name: web-01
spec:
  provider: hetzner
  region: fsn1
  plan: CX42
  cpu_cores: 4
  memory_mb: 8192
  disk_gb: 100
  image: ubuntu-24.04
  tags:
    - production
    - web
  firewall:
    - name: web-traffic
      rules:
        - protocol: tcp
          port: 443
          source: "0.0.0.0/0"
        - protocol: tcp
          port: 80
          source: "0.0.0.0/0"
---
apiVersion: infrapilot.io/v1
kind: Server
metadata:
  name: db-01
spec:
  provider: hetzner
  region: fsn1
  plan: CX62
  cpu_cores: 8
  memory_mb: 16384
  disk_gb: 200
  image: ubuntu-24.04
  tags:
    - production
    - database
```

### webhook payload (github example)

```json
{
  "ref": "refs/heads/main",
  "commits": [
    {
      "id": "a1b2c3d4e5f6...",
      "message": "feat: scale web-01 to 8GB RAM",
      "timestamp": "2026-05-20T12:00:00Z",
      "added": ["clusters/prod/servers.yaml"],
      "modified": [],
      "removed": []
    }
  ],
  "repository": {
    "clone_url": "https://github.com/myorg/infrapilot-config.git",
    "default_branch": "main"
  }
}
```

## 5. implementation plan

### phase 1: git watcher & sync engine (weeks 1-3, 4 pt)

| Task | Service | Description |
|------|---------|-------------|
| 1.1 | Orchestrator Agent | Git client abstraction layer (go-git / libgit2 bindings) |
| 1.2 | Orchestrator Agent | Poll-based watcher with configurable interval |
| 1.3 | Orchestrator Agent | Webhook receiver (GitHub/GitLab/Bitbucket) |
| 1.4 | Orchestrator Agent | Config translator -- parse YAML -> internal resource model |
| 1.5 | Orchestrator Agent | Diff engine -- compare desired vs actual state |
| 1.6 | Orchestrator Agent | Reconciliation loop -- apply diff in correct order |
| 1.7 | Orchestrator Agent | Dry-run mode -- plan output without mutation |

**deliverables:** single-direction git-to-infra sync operational with webhook and poll modes.

### phase 2: drift detection & alerting (weeks 3-4, 2 pt)

| Task | Service | Description |
|------|---------|-------------|
| 2.1 | Orchestrator Agent | Periodic state snapshots and comparison |
| 2.2 | Orchestrator Agent | Drift severity classification (low/medium/high/critical) |
| 2.3 | Orchestrator Agent | Alert integration via Webhook Event Bus (Feature #13) |
| 2.4 | Management Panel | Drift dashboard -- list, filter, acknowledge drifts |
| 2.5 | Orchestrator Agent | Auto-remediation for low-severity drifts |

**deliverables:** drift detection operational with alerting and dashboard.

### phase 3: panel-to-git pr flow (weeks 4-6, 2 pt)

| Task | Service | Description |
|------|---------|-------------|
| 3.1 | Integration Service | Git provider API client (create branch, commit, push, PR) |
| 3.2 | Management Panel | Config editor integration -- auto-generate PR on save |
| 3.3 | Integration Service | Commit signing via GPG/key management |
| 3.4 | Integration Service | PR status tracking (open, merged, closed) |
| 3.5 | Management Panel | PR link display in notification toast |

**deliverables:** panel edits create signed commits and pull requests.

### phase 4: config management & filters (weeks 6-7, 1 pt)

| Task | Service | Description |
|------|---------|-------------|
| 4.1 | Orchestrator Agent | Path-based include/exclude filters |
| 4.2 | Orchestrator Agent | Resource-type filters |
| 4.3 | Management Panel | GitOps config CRUD UI |
| 4.4 | Management Panel | Sync status dashboard (commit SHA, last sync time, drift count) |

**deliverables:** full configuration ui and filtering capabilities.

### phase 5: security & hardening (week 7, 1 pt)

| Task | Service | Description |
|------|---------|-------------|
| 5.1 | Orchestrator Agent | Deploy key management (generate, rotate, revoke) |
| 5.2 | Orchestrator Agent | Commit signature verification on sync |
| 5.3 | Integration Service | Encryption for stored tokens/keys |
| 5.4 | Shared | Audit logging for all sync operations |
| 5.5 | Shared | Rate limiting for webhook and sync triggers |

**deliverables:** production-ready security controls.

## 6. service assignments

| Service | Responsibilities |
|---------|-----------------|
| **Orchestrator Agent** | Git watcher (poll + webhook), config translator, diff engine, reconciliation loop, drift detector, deploy key management, commit verification |
| **Integration Service** | Git provider API client (branch/commit/push/PR), commit signing, PR status tracking, token encryption |
| **Management Panel** | GitOps config CRUD UI, drift dashboard, sync status display, config editor PR integration |

## 7. configuration example

**infrapilot.yaml** (global gitops configuration):

```yaml
gitops:
  enabled: true
  default_poll_interval: 300
  max_concurrent_syncs: 5
  commit_signing:
    enabled: true
    key_type: gpg
    key_storage: vault
  drift:
    enabled: true
    check_interval: 600
    auto_remediate: false
    default_severity: medium
  providers:
    github:
      app_id: 12345
      private_key_path: /etc/infrapilot/github-app-key.pem
    gitlab:
      url: https://gitlab.com
      token_env_var: GITLAB_TOKEN
```

**per-sync config example** (via api or panel ui):

```yaml
name: production-cluster
repository:
  url: https://github.com/myorg/infrapilot-config.git
  branch: main
  path: clusters/prod/
  auth_method: deploy_key
sync:
  direction: bidirectional
  auto_apply: true
  create_pr_on_panel_edit: true
schedule:
  poll_interval_secs: 300
  webhook_enabled: true
filters:
  resource_types:
    - server
    - database
  include_paths:
    - clusters/prod/**/*.yaml
```

## 8. effort estimate

| Phase | PT | Dependencies |
|-------|----|-------------|
| Phase 1: Git Watcher & Sync Engine | 4.0 | Feature #14 (API Gateway) |
| Phase 2: Drift Detection & Alerting | 2.0 | Feature #13 (Webhook Event Bus) |
| Phase 3: Panel-to-Git PR Flow | 2.0 | Phase 1 |
| Phase 4: Config Management & Filters | 1.0 | Phase 1 |
| Phase 5: Security & Hardening | 1.0 | Phase 1 |
| buffer (15%) | 1.5 | - |
| total | ~11.5 pt | - |

### risk factors

- **git client performance:** large monorepos with deep history require shallow clone optimizations
- **conflict resolution:** concurrent panel edits and git pushes can cause merge conflicts -- need rebase strategy
- **provider api differences:** github vs gitlab vs bitbucket webhook payloads and pr apis vary significantly
- **commit signing key management:** gpg key rotation and hsm integration adds operational complexity

## 9. security & compliance

- all stored tokens encrypted at rest (aes-256-gcm)
- deploy keys scoped to single repository (principle of least privilege)
- webhook payloads validated via hmac signatures
- commit signing enforced for all bot-generated commits
- audit log records: sync triggered, plan generated, changes applied, drift detected
- rbac: separate permissions for viewing gitops configs vs triggering syncs vs creating prs
