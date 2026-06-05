# feature 41: desktop app

- feature id: 41
- primary service: management panel (tauri)
- effort: large (7-10 pt)
- phase: phase 5 (ux, mobile & compliance)
- dependencies: management panel v1 (react/vite), convex backend, zero-native shell (existing)

## overview

native desktop application built with tauri that wraps the existing management panel (react/vite) into a fully native experience. goes beyond the current zero-native webview shell by adding offline-first local state, system tray integration, native os notifications, an auto-updater, and deep link protocol handling.

the desktop app targets power users and server administrators who prefer a dedicated native window with system-level integration — taskbar/dock presence, global hotkeys, background running in system tray, and native file dialogs.

### key capabilities

- native window — frameless or standard window with custom titlebar, draggable regions
- system tray — minimize to tray, context menu with quick actions (quick restart, status overview)
- native notifications — os-native toast/banner notifications, notification center integration
- offline-first — local state persistence via sqlite, offline action queuing, sync on reconnect
- auto-updater — silent background updates, differential downloads, rollback capability
- deep links — `infrapilot://` protocol handler for server access, action triggers
- global hotkeys — custom keyboard shortcuts for quick actions (ctrl+shift+s for server search)
- touch bar / widgets — macos touch bar integration, desktop widgets (future)

## architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Tauri Desktop App                        │
│                                                          │
│  ┌────────────────────┐  ┌──────────────────────────┐    │
│  │  Rust Core          │  │  WebView Frontend        │    │
│  │                     │  │                          │    │
│  │  ┌───────────────┐  │  │  React / Vite (Panel)   │    │
│  │  │ Tauri Commands │◄─┼──┤                          │    │
│  │  │ (IPC Bridge)   │  │  │  @tauri-apps/api calls  │    │
│  │  └───────┬───────┘  │  └──────────┬───────────────┘    │
│  │          │          │             │                     │
│  │  ┌───────┴───────┐  │             │                     │
│  │  │ Plugin Layer   │  │             │                     │
│  │  │ ┌───────────┐ │  │             │                     │
│  │  │ │System Tray│ │  │             │                     │
│  │  │ │Notifc     │ │  │             │                     │
│  │  │ │Updater    │ │  │             │                     │
│  │  │ │Deep Links │ │  │             │                     │
│  │  │ │Hotkeys    │ │  │             │                     │
│  │  │ └───────────┘ │  │             │                     │
│  │  └───────┬───────┘  │             │                     │
│  │          │          │  ┌──────────▼──────────┐          │
│  │  ┌───────┴───────┐  │  │  Local State (IPC)  │          │
│  │  │ SQLite DB      │◄─┼──┤  IndexedDB / SQLite │          │
│  │  │ (Local cache)  │  │  └─────────────────────┘          │
│  │  └───────────────┘  │                                    │
│  └────────────────────┘                                     │
│                                                          │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  WebSocket Client (keepalive, real-time updates)    │  │
│  └──────────────────────┬──────────────────────────────┘  │
└─────────────────────────┼─────────────────────────────────┘
                          │ WSS
┌─────────────────────────┼─────────────────────────────────┐
│          Backend        │                                 │
│  ┌──────────────────────▼──────────────────────────────┐  │
│  │           Integration Service                        │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────────────┐    │  │
│  │  │ REST API │ │ WebSocket│ │ Update Server    │    │  │
│  │  │ Gateway  │ │ Hub      │ │ (releases.json)  │    │  │
│  │  └──────────┘ └──────────┘ └──────────────────┘    │  │
│  └─────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────┘
```

### technology stack

| layer | technology | rationale |
|---|---|---|
| desktop shell | tauri 2.x (rust) | smaller binary than electron (5 mb vs 150+), lower memory, rust safety |
| frontend | react 18 + vite + tailwind css | reuse existing management panel, zero migration needed |
| local database | sqlite via tauri-plugin-sql | offline state, server cache, action queue |
| ipc bridge | @tauri-apps/api + tauri commands | typescript ↔ rust bidirectional communication |
| system tray | tauri-plugin-tray (custom) | cross-platform tray with dynamic context menu |
| notifications | tauri-plugin-notification | native notification center integration |
| auto-updater | tauri-plugin-updater | differential updates, checksum verification |
| deep links | tauri-plugin-deep-link | os-level protocol handler registration |
| global hotkeys | tauri-plugin-global-shortcut | system-wide keyboard shortcuts |
| state sync | crdt / last-write-wins merge | conflict resolution for offline edits |

## implementation plan

### phase 1: tauri shell & migration (2 pt)

| step | description | deliverables |
|---|---|---|
| 1.1 | tauri project scaffolding | `src-tauri/` directory, cargo.toml, tauri.conf.json |
| 1.2 | webview integration | load existing vite dev/build into webview, verify asset paths |
| 1.3 | ipc bridge setup | tauri commands for core operations, typescript bindings |
| 1.4 | window customization | frameless window, custom titlebar, draggable regions, min-size |
| 1.5 | dev workflow | `npm run tauri dev`, hot-reload across rust + react |

**tauri.conf.json:**

```json
{
  "productName": "Infra Pilot",
  "version": "1.0.0",
  "identifier": "com.infrapilot.desktop",
  "build": {
    "frontendDist": "../dist",
    "devUrl": "http://localhost:5173",
    "beforeDevCommand": "npm run dev",
    "beforeBuildCommand": "npm run build"
  },
  "app": {
    "windows": [
      {
        "label": "main",
        "title": "Infra Pilot",
        "width": 1280,
        "height": 800,
        "minWidth": 900,
        "minHeight": 600,
        "decorations": false,
        "center": true
      }
    ],
    "security": {
      "csp": "default-src 'self'; connect-src 'self' https://api.infrapilot.io wss://api.infrapilot.io; style-src 'self' 'unsafe-inline'"
    }
  },
  "plugins": {
    "updater": {
      "active": true,
      "endpoints": ["https://releases.infrapilot.io/desktop/{{target}}/{{current_version}}"],
      "dialog": true,
      "pubkey": "YOUR_UPDATER_PUBLIC_KEY"
    },
    "deep-link": {
      "desktop": {
        "schemes": ["infrapilot"]
      }
    }
  }
}
```

**folder structure:**

```
services/management-panel/
├── src-tauri/
│   ├── src/
│   │   ├── main.rs              # Entry point
│   │   ├── lib.rs                # Tauri builder setup
│   │   ├── commands/             # IPC command handlers
│   │   │   ├── mod.rs
│   │   │   ├── system.rs         # System info, app state
│   │   │   ├── notifications.rs  # Native notification dispatch
│   │   │   ├── tray.rs           # System tray management
│   │   │   ├── updater.rs        # Update checks & apply
│   │   │   └── deeplink.rs       # Deep link handler
│   │   ├── db/                   # SQLite operations
│   │   │   ├── mod.rs
│   │   │   ├── schema.rs
│   │   │   └── migrations.rs
│   │   └── state.rs              # AppState (DB pool, config)
│   ├── Cargo.toml
│   ├── tauri.conf.json
│   ├── capabilities/
│   ├── icons/
│   └── build.rs
├── src/                          # Existing React frontend
├── public/
├── package.json
└── vite.config.ts
```

### phase 2: system tray & native notifications (2 pt)

| step | description | deliverables |
|---|---|---|
| 2.1 | system tray menu | tray icon, context menu (open, quick restart, status dashboard, quit) |
| 2.2 | dynamic tray updates | server status badge counter, connection indicator |
| 2.3 | minimize-to-tray | close button minimizes, ctrl+q to quit, double-click to restore |
| 2.4 | native notification dispatch | forward panel alerts to os notification center |
| 2.5 | notification click handling | click notification → open window → navigate to relevant view |

**system tray diagram:**

```
System Tray Icon (dynamic badge):
  ● Green  = All servers online
  ● Yellow = Some servers degraded
  ● Red    = Critical alerts active

Context Menu:
  ┌──────────────────────┐
  │  Open Infra Pilot    │
  │  ─────────────────── │
  │  Server Status        │
  │  ├─ web-01  ● Online │
  │  ├─ db-01   ● Online │
  │  └─ game-01 ● Online │
  │  ─────────────────── │
  │  Quick Actions        │
  │  ├─ Restart web-01  ▶│
  │  └─ Backup all      ▶│
  │  ─────────────────── │
  │  Settings             │
  │  Quit                 │
  └──────────────────────┘
```

### phase 3: offline-first local state (2 pt)

| step | description | deliverables |
|---|---|---|
| 3.1 | sqlite schema | local cache tables (servers, events, settings, action_queue) |
| 3.2 | sync engine | background sync on connectivity change, delta updates |
| 3.3 | offline action queue | queue mutations, replay on reconnect, conflict detection |
| 3.4 | connectivity indicator | global offline banner, stale data badges |

**local state data flow:**

```
┌──────────┐    Online?    ┌──────────┐
│  React    │─────────────▶│  API     │
│  Frontend │◀─────────────│  Client  │
└─────┬────┘               └──────────┘
      │ IPC                          ▲
      ▼                              │
┌──────────┐               ┌─────────┴────┐
│ Tauri    │               │ Sync Engine  │
│ Commands │◀──────────────│ (background) │
│          │               └──────────────┘
│  SQLite  │◀──────────────┘
│  (local) │
└──────────┘
```

**sqlite schema:**

```sql
-- Local server cache
CREATE TABLE cached_servers (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  status TEXT NOT NULL,
  ip_address TEXT,
  cpu_usage REAL,
  ram_usage REAL,
  ram_total INTEGER,
  disk_usage REAL,
  last_seen TEXT,
  cached_at TEXT NOT NULL DEFAULT (datetime('now')),
  dirty INTEGER DEFAULT 0     -- Flag for unsynced local changes
);

-- Action queue for offline operations
CREATE TABLE action_queue (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  server_id TEXT NOT NULL,
  action TEXT NOT NULL CHECK(action IN ('start', 'stop', 'restart')),
  status TEXT NOT NULL DEFAULT 'pending'
    CHECK(status IN ('pending', 'syncing', 'completed', 'failed')),
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  synced_at TEXT,
  error_message TEXT,
  retry_count INTEGER DEFAULT 0
);

-- Local settings (synced to cloud when online)
CREATE TABLE local_settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Notification log (local only)
CREATE TABLE notification_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  notification_id TEXT UNIQUE,
  title TEXT NOT NULL,
  body TEXT,
  server_id TEXT,
  severity TEXT,
  read INTEGER DEFAULT 0,
  received_at TEXT NOT NULL
);
```

### phase 4: auto-updater (1 pt)

| step | description | deliverables |
|---|---|---|
| 4.1 | update server setup | static json manifest on cdn, signed release artifacts |
| 4.2 | update check interval | check on launch + every 6 hours, user-initiated check |
| 4.3 | download & install | background download, progress bar, prompt on ready |
| 4.4 | rollback mechanism | backup previous version, restore on crash loop detection |

**update manifest format (`releases.json`):**

```json
{
  "version": "1.2.0",
  "pub_date": "2026-06-15T10:00:00Z",
  "platforms": {
    "windows-x86_64": {
      "signature": "dW50cnVzdGVkIGNvbW1lbnQ...",
      "url": "https://releases.infrapilot.io/desktop/1.2.0/InfraPilot_1.2.0_x64.msi.zip"
    },
    "darwin-x86_64": {
      "signature": "dW50cnVzdGVkIGNvbW1lbnQ...",
      "url": "https://releases.infrapilot.io/desktop/1.2.0/InfraPilot_1.2.0_x64.dmg.zip"
    },
    "darwin-aarch64": {
      "signature": "dW50cnVzdGVkIGNvbW1lbnQ...",
      "url": "https://releases.infrapilot.io/desktop/1.2.0/InfraPilot_1.2.0_aarch64.dmg.zip"
    },
    "linux-x86_64": {
      "signature": "dW50cnVzdGVkIGNvbW1lbnQ...",
      "url": "https://releases.infrapilot.io/desktop/1.2.0/InfraPilot_1.2.0_amd64.AppImage.tar.gz"
    }
  }
}
```

### phase 5: deep links & global hotkeys (1 pt)

| step | description | deliverables |
|---|---|---|
| 5.1 | protocol registration | `infrapilot://` scheme on all platforms |
| 5.2 | route resolver | parse deep link → react router navigation |
| 5.3 | global hotkeys | configurable shortcuts via settings ui |
| 5.4 | hotkey presets | default profiles (administrator, developer, game host) |

**deep link url scheme:**

```
infrapilot://servers                              → Open server list
infrapilot://server/{id}                          → Open server detail
infrapilot://server/{id}/terminal                 → Open terminal
infrapilot://alerts                               → Open alert center
infrapilot://settings                             → Open settings
infrapilot://action/restart?server={id}           → Confirm restart dialog
infrapilot://search?q={query}                     → Open search with query
```

## api design (backend additions)

the desktop app uses the existing api but requires new endpoints for updater and state sync:

```yaml
# Update check endpoint (called by Tauri plugin)
GET https://releases.infrapilot.io/desktop/{target}/{current_version}
  Response:
    version: "1.2.0"
    pub_date: "2026-06-15T10:00:00Z"
    url: "https://..."
    signature: "dW50cnVzdGVk..."
    notes: "Bug fixes and performance improvements"

# State sync endpoint
POST /api/v2/desktop/sync
  Headers:  Authorization: Bearer <token>
  Body:
    last_sync_at: "2026-05-27T12:00:00Z"
    actions: [                           # Queued offline actions
      { id: "local_1", server_id: "srv_1", action: "restart", timestamp: "..." },
      { id: "local_2", server_id: "srv_2", action: "start", timestamp: "..." }
    ]
    settings: { theme: "dark", terminal_font_size: 14 }
  Response:
    sync_at: "2026-05-27T12:05:00Z"
    action_results: [
      { local_id: "local_1", status: "accepted", job_id: "job_abc" },
      { local_id: "local_2", status: "accepted", job_id: "job_def" }
    ]
    updated_servers: [ { id: "srv_1", status: "online", ... } ]
    conflicts: []                     # Server-side wins for conflicting edits
```

## service assignments

| service | role | ownership |
|---|---|---|
| management panel | tauri shell, rust plugins, frontend integration | desktop team (2 devs) |
| integration service | state sync endpoint, notification proxy | backend team |
| infrastructure | update cdn, release ci/cd pipeline signing | devops team |

## offline-first conflict resolution

| scenario | resolution strategy |
|---|---|
| server status changed while offline | server wins — discard local stale status on sync |
| user queued action while online elsewhere | server deduplicates by action + timestamp |
| settings changed on two devices | last-write-wins with server timestamp |
| action failed on server (e.g., server already stopped) | action marked `failed` with error message, notify user |

## security considerations

| concern | mitigation |
|---|---|
| update tampering | ed25519 signature verification via tauri-plugin-updater |
| deep link injection | url scheme validated in rust before passing to frontend |
| local data exposure | sqlite encryption via tauri-plugin-sql with os keychain |
| backend token storage | encrypted in os keychain (windows credential manager, macos keychain, linux secret-service) |

## effort estimate: large (7-10 pt)

| phase | pt | dependencies |
|---|---|---|
| phase 1: tauri shell & migration | 2 | management panel v1 (existing) |
| phase 2: system tray & notifications | 2 | phase 1 |
| phase 3: offline-first local state | 2 | phase 1 |
| phase 4: auto-updater | 1 | phase 1, update cdn |
| phase 5: deep links & hotkeys | 1 | phase 1-2 |
| packaging, signing & ci/cd | 1 | all phases |
| total | **9** | |

### staffing recommendation

- 1 senior rust developer — tauri core, plugins, ipc commands, auto-updater
- 1 full-stack developer — react integration, offline state sync, frontend ipc bindings
- 1 devops engineer — 25% time, release pipeline, code signing, update cdn

## comparison: zero-native shell vs. tauri

| aspect | current zero-native shell | proposed tauri app |
|---|---|---|
| binary size | ~5 mb (zig + system webview) | ~5-8 mb |
| system tray | manual implementation | plugin ecosystem |
| offline state | none — requires network | sqlite local cache |
| auto-updater | manual | built-in plugin |
| deep links | not supported | plugin-supported |
| global hotkeys | not possible | plugin-supported |
| native file dialogs | via webview only | tauri plugin |
| development maturity | experimental | battle-tested (v2 stable) |
| effort to add features | high (custom zig) | low (plugin ecosystem) |
