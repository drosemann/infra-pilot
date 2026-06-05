# plugin marketplace

- feature #: 15
- category: developer ecosystem & api
- primary service: management panel
- supporting services: integration service, orchestrator agent, discord service, service core
- effort: extra large (11+ pt)
- dependencies: feature #14 (api gateway & rate limiting), feature #13 (webhook event bus)

## 1. overview

the plugin marketplace enables a community-driven plugin ecosystem for infra pilot. developers can upload, publish, version, and distribute plugins that extend the management panel ui, discord bot commands, and orchestrator agent behavior. end-users discover, install, and manage plugins through a one-click interface with automatic dependency resolution.

### goals

- allow third-party developers to extend every major surface of infra pilot
- provide secure sandboxed execution for plugins
- automate dependency resolution and version management
- deliver a marketplace experience (search, ratings, compatibility badges)
- support semantic versioning with upgrade/downgrade paths

### non-goals

- full-blown ide or plugin sdk debugger (v1 ships with cli scaffolding only)
- multi-tenant plugin hosting (each instance runs its own registry)
- paid plugin distribution (no billing integration in this iteration)

## 2. architecture

### high-level component diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    Management Panel (React)                       │
│  ┌────────────┐  ┌──────────────┐  ┌─────────────────────────┐  │
│  │ Marketplace│  │ Plugin       │  │ Plugin Host (Sandbox)   │  │
│  │ Browser    │  │ Manager UI  │  │ iframe / Web Component  │  │
│  └─────┬──────┘  └──────┬───────┘  └───────────┬─────────────┘  │
└────────┼─────────────────┼──────────────────────┼────────────────┘
         │                 │                      │
         ▼                 ▼                      ▼
┌──────────────────────────────────────────────────────────────────┐
│              Integration Service (API Gateway)                     │
│  ┌────────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Plugin Registry│  │ Download     │  │ Marketplace Auth     │  │
│  │ CRUD API       │  │ Proxy/Cache  │  │ (API Key Scoping)    │  │
│  └───────┬────────┘  └──────┬───────┘  └──────────┬───────────┘  │
└──────────┼───────────────────┼─────────────────────┼──────────────┘
           │                   │                     │
           ▼                   ▼                     ▼
┌──────────────────────────────────────────────────────────────────┐
│              Orchestrator Agent (Plugin Runtime)                   │
│  ┌──────────────┐  ┌───────────────┐  ┌────────────────────────┐ │
│  │ Plugin Loader│  │ Dependency    │  │ Sandbox (gVisor /      │ │
│  │ (Hot-reload) │  │ Resolver     │  │  Deno / WASM)         │ │
│  └──────────────┘  └───────────────┘  └────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│              Discord Service (Plugin Commands)                     │
│  ┌──────────────────┐  ┌──────────────────┐                      │
│  │ Command Registrar│  │ Plugin Slash     │                      │
│  │ Dynamic          │  │ Command Router   │                      │
│  └──────────────────┘  └──────────────────┘                      │
└──────────────────────────────────────────────────────────────────┘
```

### plugin types

| Type | Extension Point | Sandbox |
|------|----------------|---------|
| `panel-ui` | React components (tabs, widgets, pages) | iframe + postMessage API |
| `panel-api` | Custom API routes served by Panel backend | Node.js VM2 sandbox |
| `discord-command` | Slash commands and context menus | Deno subprocess |
| `orchestrator-hook` | Event hooks (server.start, backup.complete) | WASM / gVisor |
| `service-core` | Java-based game server lifecycle extensions | ClassLoader isolation |

### plugin lifecycle

```
Publisher Upload
     │
     ▼
Registry Validation (signature, schema, malware scan)
     │
     ▼
Published (draft -> review -> public)
     │
     ▼
User Discover (search, browse categories)
     │
     ▼
One-Click Install
     │
     ├── Dependency Resolution (tree computed)
     ├── Version Pin (semver range satisfied)
     └── Sandbox Allocation
          │
          ▼
Activated (hot-reload or restart)
     │
     ▼
Runtime (metrics, health checks, updates)
```

## 3. data model

### plugin package

```json
{
  "id": "pkg_abc123",
  "name": "uptime-monitor",
  "display_name": "Uptime Monitor",
  "description": "Real-time HTTP health checks with Slack alerts",
  "type": "orchestrator-hook",
  "icon_url": "https://cdn.infrapilot.io/plugins/uptime-icon.png",
  "publisher": {
    "id": "usr_xyz",
    "name": "Acme Devs",
    "verified": true
  },
  "categories": ["monitoring", "alerts"],
  "tags": ["health-check", "http", "slack"],
  "created_at": "2026-05-01T00:00:00Z",
  "updated_at": "2026-05-15T00:00:00Z"
}
```

### plugin version

```json
{
  "id": "ver_def456",
  "package_id": "pkg_abc123",
  "version": "1.2.0",
  "semver": {
    "major": 1,
    "minor": 2,
    "patch": 0,
    "pre_release": null,
    "build_metadata": null
  },
  "requires": {
    "infrapilot": "^2.5.0",
    "plugins": {
      "http-client": "^1.0.0"
    }
  },
  "provides": {
    "hooks": ["http.check", "alert.send"],
    "permissions": ["network:outbound", "storage:read"]
  },
  "artifacts": {
    "download_url": "https://cdn.infrapilot.io/plugins/pkg_abc123/1.2.0/pkg.zip",
    "checksum_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "signature": "MEUCIQD...",
    "size_bytes": 245760
  },
  "manifest": {
    "entry": "main.js",
    "sdk_version": "2.x",
    "lifecycle": {
      "on_install": "scripts/install.js",
      "on_uninstall": "scripts/uninstall.js",
      "on_activate": "scripts/activate.js",
      "on_deactivate": "scripts/deactivate.js"
    }
  },
  "changelog": "## 1.2.0\n\n- Add Slack alert integration\n- Fix memory leak in health check loop",
  "status": "published",
  "download_count": 1423,
  "rating_avg": 4.7,
  "rating_count": 89,
  "created_at": "2026-05-15T00:00:00Z"
}
```

### plugin installation (per-tenant)

```json
{
  "id": "inst_789ghi",
  "tenant_id": "tnt_001",
  "package_id": "pkg_abc123",
  "version_id": "ver_def456",
  "status": "active",
  "config": {
    "check_interval_secs": 60,
    "slack_webhook": "https://hooks.slack.com/..."
  },
  "resolved_dependencies": [
    {"package_id": "pkg_http", "version_id": "ver_789", "auto_installed": true}
  ],
  "installed_at": "2026-05-20T00:00:00Z",
  "updated_at": "2026-05-21T00:00:00Z",
  "last_health_check": "2026-05-21T12:00:00Z",
  "health_status": "ok"
}
```

### sql schema (primary tables)

```sql
-- Plugin registry (global, shared across tenants)
CREATE TABLE plugin_packages (
    id          TEXT PRIMARY KEY,
    name        TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT,
    type        TEXT NOT NULL CHECK(type IN ('panel-ui','panel-api','discord-command','orchestrator-hook','service-core')),
    publisher_id TEXT NOT NULL REFERENCES users(id),
    icon_url    TEXT,
    categories  TEXT[] NOT NULL DEFAULT '{}',
    status      TEXT NOT NULL DEFAULT 'draft' CHECK(status IN ('draft','review','public','rejected','archived')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE plugin_versions (
    id              TEXT PRIMARY KEY,
    package_id      TEXT NOT NULL REFERENCES plugin_packages(id) ON DELETE CASCADE,
    version         TEXT NOT NULL,
    requires_json   JSONB NOT NULL DEFAULT '{}',
    provides_json   JSONB NOT NULL DEFAULT '{}',
    artifact_url    TEXT NOT NULL,
    checksum_sha256 TEXT NOT NULL,
    signature       TEXT,
    size_bytes      BIGINT NOT NULL,
    manifest_json   JSONB NOT NULL,
    changelog       TEXT,
    status          TEXT NOT NULL DEFAULT 'published' CHECK(status IN ('published','deprecated','yanked')),
    download_count  INT NOT NULL DEFAULT 0,
    rating_avg      DECIMAL(3,2) DEFAULT 0,
    rating_count    INT DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(package_id, version)
);

CREATE TABLE plugin_installations (
    id          TEXT PRIMARY KEY,
    tenant_id   TEXT NOT NULL,
    package_id  TEXT NOT NULL REFERENCES plugin_packages(id),
    version_id  TEXT NOT NULL REFERENCES plugin_versions(id),
    status      TEXT NOT NULL DEFAULT 'installing' CHECK(status IN ('installing','active','inactive','error','uninstalling')),
    config_json JSONB NOT NULL DEFAULT '{}',
    installed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE plugin_dependency_resolutions (
    installation_id     TEXT NOT NULL REFERENCES plugin_installations(id) ON DELETE CASCADE,
    dependency_pkg_id   TEXT NOT NULL REFERENCES plugin_packages(id),
    dependency_ver_id   TEXT NOT NULL REFERENCES plugin_versions(id),
    auto_installed      BOOLEAN NOT NULL DEFAULT true,
    PRIMARY KEY (installation_id, dependency_pkg_id)
);
```

## 4. api design

### plugin registry api (integration service)

all endpoints prefixed with `/api/v2/plugins`.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | List published plugins (paginated, filterable) |
| `GET` | `/{package_id}` | Get plugin details with latest version |
| `GET` | `/{package_id}/versions` | List all versions for a plugin |
| `GET` | `/{package_id}/versions/{version}` | Get specific version manifest |
| `POST` | `/` | Create a new plugin package (publisher) |
| `PUT` | `/{package_id}` | Update plugin metadata |
| `POST` | `/{package_id}/versions` | Upload a new version |
| `DELETE` | `/{package_id}/versions/{version}` | Yank a version |
| `GET` | `/{package_id}/download` | Download latest compatible version |
| `GET` | `/{package_id}/download/{version}` | Download specific version |

### installation api

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/installations` | Install plugin (with auto-resolve deps) |
| `GET` | `/installations` | List installed plugins per tenant |
| `GET` | `/installations/{id}` | Get installation status |
| `PUT` | `/installations/{id}` | Update installation config |
| `DELETE` | `/installations/{id}` | Uninstall plugin |
| `POST` | `/installations/{id}/upgrade` | Upgrade to latest compatible version |
| `POST` | `/installations/{id}/downgrade` | Downgrade to specific version |

### marketplace query parameters

```
GET /api/v2/plugins?type=orchestrator-hook
                   &category=monitoring
                   &q=uptime
                   &sort=downloads
                   &order=desc
                   &page=1
                   &per_page=20
                   &compatible=2.5.0
```

response:

```json
{
  "data": [
    {
      "id": "pkg_abc123",
      "name": "uptime-monitor",
      "display_name": "Uptime Monitor",
      "type": "orchestrator-hook",
      "icon_url": "...",
      "publisher": {"name": "Acme Devs", "verified": true},
      "latest_version": "1.2.0",
      "compatible": true,
      "rating_avg": 4.7,
      "download_count": 1423,
      "installed": false
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 142,
    "total_pages": 8
  }
}
```

### installation request

```json
POST /api/v2/plugins/installations
{
  "package_id": "pkg_abc123",
  "version_spec": "^1.0.0",
  "config": {
    "check_interval_secs": 60
  }
}
```

response:

```json
{
  "id": "inst_789ghi",
  "status": "installing",
  "resolved_dependencies": [
    {"package_id": "pkg_http", "version": "2.1.0", "auto_installed": true}
  ],
  "estimated_completion_secs": 15
}
```

## 5. implementation plan

### phase 1: foundation (weeks 1-2, 4 pt)

| Task | Service | Description |
|------|---------|-------------|
| 1.1 | Integration Service | Plugin registry data model & migrations |
| 1.2 | Integration Service | CRUD API for packages & versions |
| 1.3 | Integration Service | File upload endpoint with virus scan hook |
| 1.4 | Integration Service | Marketplace search & pagination |
| 1.5 | Management Panel | Plugin Browser UI (list, search, detail view) |
| 1.6 | Shared | Plugin manifest schema & validation library |

**deliverables:** registry api operational, basic browse ui, schema validation.

### phase 2: installation engine (weeks 3-5, 4 pt)

| Task | Service | Description |
|------|---------|-------------|
| 2.1 | Orchestrator Agent | Plugin loader with hot-reload capability |
| 2.2 | Orchestrator Agent | Dependency resolver (semver DAG, conflict detection) |
| 2.3 | Orchestrator Agent | Download & checksum verification pipeline |
| 2.4 | Orchestrator Agent | Plugin installation lifecycle hooks |
| 2.5 | Integration Service | Installation CRUD API |
| 2.6 | Management Panel | One-click install / uninstall UI |

**deliverables:** plugins can be installed and activated on orchestrator agent.

### phase 3: sandboxing & security (weeks 5-7, 2 pt)

| Task | Service | Description |
|------|---------|-------------|
| 3.1 | Orchestrator Agent | gVisor/Deno sandbox for orchestrator-hook plugins |
| 3.2 | Management Panel | iframe sandbox + postMessage bridge for panel-ui plugins |
| 3.3 | Discord Service | Subprocess isolation for discord-command plugins |
| 3.4 | Integration Service | Malware scan integration (ClamAV / custom rules) |
| 3.5 | Shared | Permission manifest enforcement at runtime |

**deliverables:** all plugin types execute in isolated sandboxes with permission controls.

### phase 4: marketplace experience (weeks 7-9, 1.5 pt)

| Task | Service | Description |
|------|---------|-------------|
| 4.1 | Management Panel | Plugin detail page (screenshots, changelog, ratings) |
| 4.2 | Management Panel | Publisher dashboard (analytics, version management) |
| 4.3 | Management Panel | Rating & review system |
| 4.4 | Integration Service | Compatibility badge computation |
| 4.5 | Management Panel | Plugin update notifications (badge in header) |

**deliverables:** full marketplace ux with ratings, compatibility, and publisher tools.

### phase 5: discord bot plugins (week 10, 1 pt)

| Task | Service | Description |
|------|---------|-------------|
| 5.1 | Discord Service | Dynamic slash command registration from plugins |
| 5.2 | Discord Service | Plugin command routing & permission checking |
| 5.3 | Discord Service | Plugin hot-reload for command updates |

**deliverables:** discord command plugins operational.

### phase 6: polish & docs (week 11, 0.5 pt)

| Task | Description |
|------|-------------|
| 6.1 | Write plugin developer guide (SDK reference, examples) |
| 6.2 | Plugin scaffolding CLI (`ipilot plugin init`) |
| 6.3 | Performance & load testing (50+ concurrent installs) |
| 6.4 | Documentation for marketplace operators |

**deliverables:** developer docs, cli scaffolding tool, production readiness validation.

## 6. service assignments

| Service | Responsibilities |
|---------|-----------------|
| **Management Panel** | Marketplace browser, plugin manager UI, publisher dashboard, ratings, update notifications, panel-ui sandbox host |
| **Integration Service** | Plugin registry CRUD, download proxy/cache, search indexing, malware scan orchestration, marketplace auth scoping |
| **Orchestrator Agent** | Plugin loader (hot-reload), dependency resolver, sandbox execution (gVisor/Deno/WASM), lifecycle hooks, health monitoring |
| **Discord Service** | Dynamic command registration, plugin command routing, subprocess isolation |
| **Service Core** | ClassLoader isolation for Java plugins, lifecycle hooks for game server extensions |

## 7. configuration example

### plugin manifest (`plugin.yaml`)

```yaml
api_version: "2.0"
id: uptime-monitor
name: Uptime Monitor
type: orchestrator-hook
version: 1.2.0
sdk_version: "^2.5.0"

publisher:
  name: Acme Devs
  email: plugins@acme.dev

description: Real-time HTTP health checks with Slack alerts
icon: icon.png
categories:
  - monitoring
  - alerts

permissions:
  - network:outbound
  - storage:read

requires:
  infrapilot: "^2.5.0"
  plugins:
    http-client: "^1.0.0"

provides:
  hooks:
    - http.check
    - alert.send

lifecycle:
  on_install: scripts/install.js
  on_uninstall: scripts/uninstall.js
  on_activate: scripts/activate.js
  on_deactivate: scripts/deactivate.js

entry: main.js
```

### panel configuration (infrapilot.yaml)

```yaml
plugins:
  marketplace:
    enabled: true
    registry_url: "https://api.infrapilot.io/api/v2/plugins"
    allow_community: true
    allowed_types:
      - panel-ui
      - orchestrator-hook
      - discord-command
    sandbox:
      panel_ui: iframe
      orchestrator_hook: gvisor
      discord_command: deno
    malware_scan: true
    auto_updates: false
    allow_manual_uploads: true
```

## 8. effort estimate

| Phase | PT | Dependencies |
|-------|----|-------------|
| Phase 1: Foundation | 4.0 | Feature #14 (API Gateway) |
| Phase 2: Installation Engine | 4.0 | Phase 1 |
| Phase 3: Sandboxing & Security | 2.0 | Feature #14 (Rate Limiting) |
| Phase 4: Marketplace Experience | 1.5 | Phase 2 |
| Phase 5: Discord Bot Plugins | 1.0 | Phase 2 |
| Phase 6: Polish & Docs | 0.5 | Phases 1-5 |
| buffer (15%) | 1.9 | - |
| total | ~14.9 pt | - |

### risk factors

- **sandboxing complexity:** gvisor on non-linux systems requires workarounds (wsl2, docker vm)
- **dependency resolution:** dag cycles and diamond dependencies need careful handling
- **plugin api stability:** breaking sdk changes require migration path for published plugins
- **malware scanning:** false positives can erode publisher trust

## 9. security & compliance

- all plugin artifacts signed via ed25519 (publisher private key)
- checksum verification before every installation
- sandbox resource limits (cpu, memory, network, filesystem)
- permission manifest enforced at runtime -- no ambient authority
- rate-limited uploads and installations per publisher/tenant
- audit log for every plugin lifecycle event (upload, install, activate, deactivate)
- semver range constraints prevent incompatible upgrades
