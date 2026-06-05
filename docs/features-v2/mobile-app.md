# feature 40: mobile app

- feature id: 40
- primary service: new `mobile/` directory
- effort: extra large (11+ pt)
- phase: phase 5 (ux, mobile & compliance)
- dependencies: stable rest api (phase 1-2), webhook event bus (#13), push notification infrastructure

## overview

native mobile application (ios & android) for on-the-go server management. provides real-time server monitoring, push notifications for alerts, quick-action toggles (restart, stop, start), a mobile-optimized terminal emulator, and biometric authentication.

the mobile app targets server administrators and game server owners who need immediate visibility and control from their phone without launching a desktop browser.

### key capabilities

- dashboard — server list with health status, cpu/ram/disk gauges
- push notifications — alert on server down, backup complete, high resource usage
- quick actions — start/stop/restart servers, one-tap ssh keys
- mobile terminal — optimized terminal emulator with touch-friendly keyboard
- biometric auth — face id / touch id / fingerprint for app unlock
- offline support — cached server list, queued actions, offline-first data model
- deep links — `infrapilot://server/{id}` to open specific server views

## architecture

```
┌─────────────────────────────────────────────────┐
│              Mobile App (iOS/Android)            │
│                                                   │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────┐  │
│  │  UI Layer    │  │  State       │  │  Local   │  │
│  │ (Screens,    │──│  Management  │──│  DB      │  │
│  │  Widgets)    │  │  (Riverpod)  │  │  (SQLite)│  │
│  └─────────────┘  └──────┬───────┘  └─────────┘  │
│                          │                        │
│  ┌───────────────────────┴──────────────────────┐ │
│  │            Service Layer                      │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────────┐  │ │
│  │  │ API      │ │ WebSocket│ │ Push          │  │ │
│  │  │ Client   │ │ Client   │ │ Registration  │  │ │
│  │  └──────────┘ └──────────┘ └──────────────┘  │ │
│  └───────────────────────┬──────────────────────┘ │
└──────────────────────────┼────────────────────────┘
                           │ HTTPS / WSS
┌──────────────────────────┼────────────────────────┐
│            Backend       │                        │
│  ┌───────────────────────┴──────────────────────┐ │
│  │           Integration Service                 │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────────┐  │ │
│  │  │ REST API │ │ WebSocket│ │ FCM/APNs     │  │ │
│  │  │ Gateway  │ │ Hub      │ │ Proxy         │  │ │
│  │  └──────────┘ └──────────┘ └──────────────┘  │ │
│  └──────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────┘
```

### technology stack

| layer | technology | rationale |
|---|---|---|
| framework | flutter 3.x | single codebase, strong mobile terminal ecosystem, excellent perf |
| state management | riverpod + flutter_bloc | testable, reactive, scalable |
| local db | drift (sqlite) | offline-first, type-safe queries, migrations |
| http client | dio | interceptors, retry, ssl pinning |
| websocket | web_socket_channel | native websocket support |
| push notifications | firebase_messaging + local_notifications | fcm for android, apns via fcm proxy |
| terminal emulator | flutter_xterm / terminal_xterm | full vt100/xterm emulation |
| biometrics | local_auth | platform biometric api |
| secure storage | flutter_secure_storage | keychain/keystore for tokens |
| deep linking | app_links + uni_links | universal links / app links |
| ci/cd | codemagic / github actions | ios + android builds in parallel |

## implementation plan

### phase 1: foundation (3 pt)

| step | description | deliverables |
|---|---|---|
| 1.1 | project scaffolding | flutter project, folder structure, ci/cd pipeline |
| 1.2 | api client layer | dio-based rest client with auth token refresh, error handling |
| 1.3 | state management setup | riverpod providers, app state models, repository pattern |
| 1.4 | local database | drift schema for cached servers, users, settings |
| 1.5 | navigation shell | bottom tab navigation (dashboard, servers, terminal, settings) |

**folder structure:**

```
mobile/
├── lib/
│   ├── app/                  # App entry, router, theme
│   │   ├── router/
│   │   ├── theme/
│   │   └── app.dart
│   ├── core/                 # Shared utilities
│   │   ├── api/              # Dio client, interceptors
│   │   ├── storage/          # Secure storage, prefs
│   │   ├── websocket/        # WS connection manager
│   │   └── constants/
│   ├── features/             # Feature modules
│   │   ├── auth/
│   │   ├── dashboard/
│   │   ├── servers/
│   │   ├── terminal/
│   │   ├── notifications/
│   │   └── settings/
│   ├── models/               # Data models (freezed)
│   ├── repositories/         # Data access layer
│   └── providers/            # Riverpod providers
├── test/
├── ios/
├── android/
├── pubspec.yaml
└── README.md
```

### phase 2: authentication & server management (3 pt)

| step | description | deliverables |
|---|---|---|
| 2.1 | login flow | api token auth, oauth2 pkce flow, session persistence |
| 2.2 | biometric unlock | local_auth integration, app lock screen |
| 2.3 | server list | paginated list with search, sort, status indicators |
| 2.4 | server detail view | metrics gauges, recent events, quick actions |
| 2.5 | server control | start/stop/restart with confirmation, action history |

**api endpoints consumed:**

```yaml
# Core mobile API endpoints
endpoints:
  auth:
    login:
      method: POST
      path: /api/v2/auth/login
      body: { email, password, device_name }
      response: { access_token, refresh_token, user }

    refresh:
      method: POST
      path: /api/v2/auth/refresh
      body: { refresh_token }
      response: { access_token, refresh_token }

  servers:
    list:
      method: GET
      path: /api/v2/servers
      params: { page, per_page, search, sort, status }
      response: { data: [Server], meta: { page, total } }

    detail:
      method: GET
      path: /api/v2/servers/{id}
      response: { data: Server, metrics: Metrics }

    action:
      method: POST
      path: /api/v2/servers/{id}/action
      body: { action: "start" | "stop" | "restart" | "kill" }
      response: { status: "accepted", job_id }

  metrics:
    realtime:
      method: GET (WebSocket Upgrade)
      path: /api/v2/ws/servers/{id}/metrics
      frames: [ { cpu, ram, disk, net_rx, net_tx, timestamp } ]
```

### phase 3: push notifications (2 pt)

| step | description | deliverables |
|---|---|---|
| 3.1 | fcm registration | token registration on login, refresh on token change |
| 3.2 | notification handlers | foreground (in-app banner), background (system tray), data-only (silent sync) |
| 3.3 | notification preferences | per-category toggle (alerts, backups, deployments), quiet hours |
| 3.4 | deep link routing | parse notification payload → navigate to relevant screen |

**notification payload format:**

```json
{
  "notification": {
    "title": "Server Alert",
    "body": "web-01 is down — automatic restart initiated"
  },
  "data": {
    "type": "server.alert",
    "server_id": "srv_abc123",
    "severity": "critical",
    "action_url": "infrapilot://server/srv_abc123",
    "silent": false,
    "category": "alerts"
  }
}
```

### phase 4: mobile terminal (2 pt)

| step | description | deliverables |
|---|---|---|
| 4.1 | terminal widget | xterm.js-based flutter terminal emulator widget |
| 4.2 | ssh/websocket relay | connect via rest api websocket proxy, not direct ssh |
| 4.3 | touch keyboard | custom toolbar: tab, ctrl, esc, arrow keys, function keys |
| 4.4 | session persistence | restore terminal session, scrollback buffer caching |

**terminal architecture:**

```
┌─────────────────────────────────────────────┐
│          Mobile App                         │
│  ┌─────────────────────────────────────┐    │
│  │  Terminal Widget (flutter_xterm)    │    │
│  │  ┌───────────────────────────────┐  │    │
│  │  │  Terminal Buffer             │  │    │
│  │  │  (scrollback, selection)     │  │    │
│  │  └───────────────────────────────┘  │    │
│  └──────────────────┬──────────────────┘    │
│                     │ WebSocket (WSS)       │
│  ┌──────────────────▼──────────────────┐    │
│  │  Terminal Proxy Service (Backend)   │    │
│  │  ┌──────────────┐ ┌──────────────┐  │    │
│  │  │ WS Server    │→│ SSH Client   │  │    │
│  │  │ (auth, audit)│ │ (session mgr)│  │    │
│  │  └──────────────┘ └──────────────┘  │    │
│  └─────────────────────────────────────┘    │
└─────────────────────────────────────────────┘
```

### phase 5: offline support & polish (1 pt)

| step | description | deliverables |
|---|---|---|
| 5.1 | offline-first data model | read from local db, sync in background on connectivity |
| 5.2 | action queue | queue server actions when offline, execute on reconnect |
| 5.3 | connectivity awareness | banner when offline, graceful degradation |
| 5.4 | error states | empty states, retry widgets, timeout handling |

## data model

```yaml
# Core mobile-local data models (drift/SQLite)
MobileServer:
  table: servers
  columns:
    id: TEXT PRIMARY KEY           # Server UUID
    name: TEXT NOT NULL
    status: TEXT NOT NULL           # online | offline | starting | stopping | error
    ip_address: TEXT
    region: TEXT
    cpu_usage: REAL                # 0.0 - 100.0
    ram_usage: REAL
    ram_total: INTEGER             # MB
    disk_usage: REAL
    disk_total: INTEGER            # GB
    last_seen: TEXT                # ISO 8601
    cached_at: TEXT                # Local cache timestamp
    favorite: INTEGER DEFAULT 0    # Boolean (0/1)

MobileNotification:
  table: notifications
  columns:
    id: TEXT PRIMARY KEY
    type: TEXT NOT NULL            # server.alert | backup.done | deploy.complete
    title: TEXT NOT NULL
    body: TEXT
    server_id: TEXT                # FK to servers.id
    severity: TEXT                 # info | warning | critical
    read: INTEGER DEFAULT 0
    action_url: TEXT               # Deep link
    received_at: TEXT NOT NULL

ActionQueue:
  table: action_queue
  columns:
    id: INTEGER PRIMARY KEY AUTOINCREMENT
    server_id: TEXT NOT NULL
    action: TEXT NOT NULL          # start | stop | restart
    status: TEXT DEFAULT "pending" # pending | syncing | completed | failed
    created_at: TEXT NOT NULL
    synced_at: TEXT
    error_message: TEXT
```

## api design (backend additions)

the mobile app consumes the existing rest api but requires several new/adapted endpoints:

### new endpoints

```yaml
# Push notification registration
POST /api/v2/devices/register
  Body:   { device_token, platform: "ios"|"android", app_version }
  Response: { device_id, registered_at }

POST /api/v2/devices/unregister
  Body:   { device_token }
  Response: { success: true }

# Notification preferences
GET /api/v2/notifications/preferences
  Response: { categories: [{ type, enabled, push, email }] }

PUT /api/v2/notifications/preferences
  Body:   { categories: [{ type, enabled: bool }] }
  Response: { success: true }

# Terminal WebSocket proxy
GET /api/v2/ws/servers/{id}/terminal
  Upgrade: WebSocket
  Query:   { cols, rows, font_size }
  Frames:  [ stdin: text, stdout: text, resize: { cols, rows } ]

# Biometric auth token
POST /api/v2/auth/biometric-token
  Body:   { password }
  Response: { biometric_token, expires_at }

POST /api/v2/auth/biometric-login
  Body:   { biometric_token }
  Response: { access_token, refresh_token }
```

## service assignments

| service | role | ownership |
|---|---|---|
| new: `mobile/` | flutter app codebase, builds, app store deployment | mobile team (2-3 devs) |
| integration service | push notification fcm/apns proxy, terminal ws relay, device registration api | backend team |
| management panel | shared api client types & openapi spec; no mobile ui changes | shared |
| service core | no direct changes; mobile relies on existing core api | — |

## push notification architecture

```
┌──────────┐    FCM/APNs    ┌────────────┐   HTTPS   ┌──────────────────┐
│  Mobile   │◄──────────────│ Firebase    │◄─────────│ Integration      │
│  Device   │                │ Cloud       │          │ Service          │
│           │                │ Messaging   │          │                  │
└──────────┘                └────────────┘          │  ┌────────────┐   │
       ▲                                             │  │ Event      │   │
       │ WebSocket (app open)                        │  │ Router     │   │
       └─────────────────────────────────────────────│  │ (webhook)  │   │
                                                      │  └────────────┘   │
                                                      │         ▲         │
                                                      │    ┌───────────┐  │
                                                      │    │ Event Bus │  │
                                                      │    │ (#13)     │  │
                                                      │    └───────────┘  │
                                                      └──────────────────┘
```

## offline-first strategy

| scenario | behavior |
|---|---|
| no connectivity at launch | show cached server list with "offline" badge, stale data indicator |
| action while offline | queue action in local db, show "pending" indicator, execute on reconnect |
| connectivity restored | sync pending actions, refresh server data, clear stale indicators |
| partial connectivity | retry with exponential backoff, show per-item error states |
| token expired offline | store refresh token securely, re-auth on reconnect transparently |

## mobile terminal ux

the mobile terminal requires careful ux decisions:

- gesture handling — pinch-to-zoom font size, swipe to scroll buffer, long-press for paste
- touch keyboard toolbar — persistent bottom bar with: ctrl, tab, esc, arrow keys, function keys (f1-f12), clipboard paste
- color scheme — match desktop terminal theme, optionally customisable
- session timeout — auto-disconnect after 15 min inactivity, reconnect prompt
- buffer limit — 10,000 line scrollback, overflow truncation with "buffer full" indicator

## security considerations

| concern | mitigation |
|---|---|
| token theft | device-bound biometric token + short-lived access tokens |
| man-in-the-middle | certificate pinning (dio ssl pinning), wss required |
| local data exposure | all cached data encrypted with flutter_secure_storage |
| push notification spoofing | verify fcm/apns signature server-side |
| terminal session hijack | one-time terminal token, scoped to server, expires on disconnect |

## effort estimate: extra large (11+ pt)

| phase | pt | dependencies |
|---|---|---|
| phase 1: foundation | 3 | — |
| phase 2: auth & server management | 3 | phase 1, stable rest api |
| phase 3: push notifications | 2 | phase 2, webhook event bus (#13) |
| phase 4: mobile terminal | 2 | phase 2, terminal proxy service |
| phase 5: offline & polish | 1 | phase 2-4 |
| app store submission & ci/cd | 1 | all phases |
| total | **12** | |

### staffing recommendation

- 2 senior flutter developers — full-time, phases 1-5
- 1 backend developer — 50% time, push notification & terminal proxy endpoints
- 1 qa engineer — 50% time, device matrix testing, e2e test automation
