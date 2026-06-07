# docker panel

self-hosted docker container management panel with personal mode for individual users and optional hosting business mode.

[![mit license](https://img.shields.io/badge/license-MIT-blue.svg)](../../LICENSE)
[![typescript](https://img.shields.io/badge/TypeScript-5.0%2B-blue?logo=typescript)](https://www.typescriptlang.org/)
[![react 19](https://img.shields.io/badge/React-19-61dafb?logo=react)](https://react.dev)
[![node.js 18+](https://img.shields.io/badge/Node.js-18%2B-brightgreen?logo=node.js)](https://nodejs.org/)

## overview

docker panel is a pterodactyl-inspired web panel for managing docker containers locally. perfect for self-hosters, hobby projects, and home labs.

### personal mode (default)
- docker app management - create, deploy, and manage containerized applications
- container controls - start/stop/restart via real docker api calls
- dashboard - real-time status and metrics with live websocket updates
- logs & monitoring - stream application logs via websocket in real-time
- configuration - port mapping, environment variables, volume mounts
- simple auth - single admin account with rate-limited login
- audit trail - append-only log of all mutations with timeline viewer
- global search - cmd+k palette to search apps, backups, and audit logs
- web terminal - in-browser container shell via websocket + docker exec
- notification channels - email, webhook, and telegram alert delivery
- pwa support - installable as desktop app with offline caching
- onboarding wizard - guided 5-step tour after first-time setup

### business mode (optional)
- all personal mode features +
- customer account management
- plans and pricing tiers
- white-label branding
- team and staff management
- audit logging (business mode extension)

## quick start (3 commands)

```bash
# 1. Get the code
cd services/management-panel

# 2. Setup environment
cp .env.local.example .env.local

# 3. Install and run
npm install && npm run dev
```

### demo feature flag (per-env)

- gate the seed demo ui behind a per-environment feature flag to avoid accidental usage in prod-like environments.
- env var: `vite_demo_feature_enabled`
- default: false (flag is off unless explicitly enabled)
- how to enable/disable:
  - local development: set in your .env.local
    - add: `vite_demo_feature_enabled=true`
  - staging/qa: set to `true` to enable demo flows for testers, or `false` to hide in testing
  - production: keep it `false` to avoid accidental seeds
- verification:
  - start frontend and check that the seed demo button appears only when the flag is enabled.
  - click seed demo to see the confirmation modal before seeding.
- notes:
- this flag gates only the ui; the backend seed endpoints remain available to programmatic use when needed and are still protected by business mode.

### qa checklist (gating demo per-env)
- development (`vite_demo_feature_enabled=true`)
  - seed demo button is visible on the customers page in business mode.
  - click seed demo to open the confirmation modal; confirm to seed.
  - verify the ui shows a success toast with seeded counts and the customers list refreshes.
  - verify the seed demo action is not shown when the flag is off.
- staging/qa (`vite_demo_feature_enabled=true` or false)
  - if true, perform the same checks as development.
  - if false, seed demo button should be hidden; confirm gating works in this environment.
- production (`vite_demo_feature_enabled` not set or false)
  - seed demo button must be hidden; ui should reflect no demo button.
  - optional: try calling the api directly with a valid token and confirm backend blocks based on business mode as designed.
- validation steps (end-to-end)
  - start both frontend and backend, login as a business mode admin, navigate to customers, ensure gating behavior matches env flag.
  - seed demo idempotence: verify re-clicking seed demo (when enabled) does not crash and either updates or leaves data idempotently.
- troubleshooting
  - if seed demo button is missing, verify `vite_demo_feature_enabled` is set to true and the frontend is restarted to pick up the env var.
  - if seed demo still seeds in prod-like env, rebuild the frontend to ensure the flag is re-evaluated.

then open: http://localhost:5173

first-time setup will guide you through:
• choose personal mode or business mode
• create admin account
• start managing docker apps

## native desktop shell (zero-native)

the panel can also run as a zero-native desktop app. the react/vite ui is loaded into a native webview, while the express api remains the local backend on `http://127.0.0.1:3001`.

```bash
# Terminal 1: API
npm run dev:backend

# Terminal 2: native shell + Vite managed by zero-native
npm run desktop:dev -- -Dzero-native-path=/absolute/path/to/zero-native
```

useful scripts:

- `npm run desktop:validate` validates `app.zon`.
- `npm run desktop:doctor` checks the host zero-native environment.
- `npm run desktop:package -- -Dzero-native-path=/absolute/path/to/zero-native` packages the built `dist/` assets.

see the repository guide at [`../../docs/desktop/zero-native-management-panel.md`](../../docs/desktop/zero-native-management-panel.md).

## documentation

| document | topic |
|----------|-------|
| [docker panel quick start](README-DOCKER-PANEL.md) | getting started guide |
| [personal mode architecture](docs/PERSONAL_MODE.md) | mode design & feature gates |
| [database setup guide](docs/DATABASE_SETUP.md) | supabase configuration |
| [system architecture](docs/ARCHITECTURE.md) | technical diagrams & flows |
| [implementation summary](IMPLEMENTATION_SUMMARY.md) | complete overview |

## features at a glance

### personal mode
- docker app crud (create, read, update, delete)
- container start/stop/restart controls
- real-time logs and status monitoring
- environment variable configuration
- port mapping (host ↔ container)
- volume/mount management
- memory and cpu limits
- simple dashboard with app grid
- server performance monitoring with real-time metrics (tps, cpu, memory, player count)
- health check dashboard with uptime tracking and incident timeline
- backup job automation and scheduling with retention policies
- access log viewer for authentication and console events
- reports generation with csv/pdf export
- alert configuration (metric thresholds) and alert history
- maintenance window scheduling
- config version control with snapshot and rollback
- config editor — in-browser yaml/json config editor with syntax highlighting
- java version selector — switch between java 8/11/17/21 per server
- mysql database per click — instant mysql container provisioning
- git deployment webhook — auto-deploy on github push
- cronjob scheduler — scheduled tasks via cron expressions
- real-time resource graphs — live cpu/memory/disk gauges with sparklines
- log search — full-text log search with filters and pagination
- prepaid billing — pay-as-you-go balance system with transaction history
- modpack-installer — one-click modpack install from curseforge/modrinth
- 2fa (totp) — two-factor authentication via totp
- discord token validation — validate bot token before container start

### business mode (roadmap)
- customer accounts and management
- plans and pricing configuration
- billing integration hooks
- white-label branding
- team/staff rbac
- audit logging
- advanced analytics

## tech stack

| layer | technology | why |
|-------|-----------|-----|
| frontend | react 19 + typescript | modern, type-safe |
| styling | tailwind css | utility-first, dark mode |
| routing | react router v6 | industry standard |
| backend | express.js | lightweight, async |
| database | postgresql + supabase | structured, rls security |
| auth | supabase auth | built-in, scalable |

## canvas visualizations

5 seiten nutzen die raw **Canvas 2D API** für interaktive infrastructure-visualisierungen:

| Page | File | Purpose |
|------|------|---------|
| Topology3D | `src/pages/Topology3D.tsx` | 3d infrastructure topology graph (nodes, edges, forces) |
| DependencyGraphViewer | `src/pages/DependencyGraphViewer.tsx` | Service dependency graph with zoom/pan |
| GeolocationHeatmap | `src/pages/GeolocationHeatmap.tsx` | World-map heatmap + timelapse overlay |
| BIDashboard | `src/pages/BIDashboard.tsx` | Bar charts, pie charts, metric cards |
| CostAnalytics | `src/pages/CostAnalytics.tsx` | Cost trends, mini bar charts, sparklines |

### HTML-in-Canvas rendering

Alle text-labels in diesen canvas-zeichnungen werden via der experimentellen **HTML-in-Canvas** API gerendert — dem [WICG `layoutsubtree` + `drawElementImage`](https://github.com/WICG/canvas-draw-element) vorschlag.

**Funktionsweise:**
- In `useEffect` werden `document.createElement('span')` elemente erstellt und per `canvas.appendChild(el)` direkt in den canvas-dom eingehängt (erforderlich für `drawElementImage`)
- Ein `paint`-event-listener auf dem canvas führt `ctx.drawElementImage(el, x, y)` aus, sobald der browser das layout des elements berechnet hat
- Der zurückgegebene `DOMMatrix` wird auf `el.style.transform` gesetzt, damit canvas-hit-testing (z. B. klick-erkennung) mit den gerenderten positionen synchron bleibt
- Geometrie (kreise, edgelines, balken) wird weiterhin mit `ctx.arc / fillRect / moveTo` gezeichnet — nur text-label werden als DOM-Elemente gehandhabt

**Progressive enhancement / fallback:**
```typescript
const hasDrawElement = typeof (ctx as any).drawElementImage === 'function';
if (hasDrawElement) {
  /* HTML-in-Canvas via drawElementImage */
} else {
  ctx.fillText(label, x, y); /* fallback */
}
```

**Vorteile:**
- Kein manuelles text-trunkieren, text-wrapping oder `measureText` notwendig
- Volle CSS-styling-fähigkeit (font-family, font-size, color, text-shadow, white-space)
- Automatische i18n / RTL-unterstützung
- Accessibility (screenreader können den DOM-text erfassen)
- Vorbereitet für zukünftige browser-standards

> **Hinweis:** Die HTML-in-Canvas API ist aktuell (2026) experimentell und hinter `chrome://flags/#canvas-draw-element` verfügbar. In browsern ohne support wird automatisch auf `fillText` zurückgefallen.

## project structure

```
services/management-panel/
├── src/
│   ├── pages/           # Setup, Dashboard, AppForm, AppDetail, Monitoring, AccessLogs, Backups, Reports, Settings, AuditLog, Billing
│   ├── components/      # MainLayout, Sidebar, NavBar, OnboardingWizard, GlobalSearch, WebTerminal, ConfigEditor, CronJobManager, DatabaseManager, GitDeployManager, RealtimeMetrics, MetricsConfig, BillingDashboard, ModpackBrowser, TwoFactorSetup, shared/monitoring/backup/alert components
│   ├── lib/             # API client, auth, types, feature gates
│   ├── App.tsx          # Main router and mode provider
│   ├── main.tsx         # React entry point (includes PWA service worker registration)
│   └── ThemeToggle.tsx  # Dark/light mode with localStorage persistence
├── server/
│   ├── index.ts         # Express API (WebSocket server, 70+ routes)
│   ├── presets.ts       # Server preset definitions
│   └── openapi.ts       # OpenAPI 3.1 specification
├── public/
│   ├── manifest.json    # PWA manifest
│   └── sw.js            # Service worker (cache-first strategy)
├── db/
│   └── schema.sql       # PostgreSQL schema with RLS (16+ tables including audit_log, notification_channels)
├── docs/
│   ├── PERSONAL_MODE.md # Mode architecture
│   ├── DATABASE_SETUP.md # Setup guide
│   └── ARCHITECTURE.md   # Technical architecture
├── tests/
│   ├── helpers/          # Shared test mocks (supabase-mock, http-client)
│   ├── unit/             # Unit tests (auth-storage)
│   ├── integration/      # API integration tests (api, rate-limit)
│   └── playwright/       # Playwright E2E browser tests
├── package.json         # Dependencies (includes ws dependency)
├── vite.config.ts       # Frontend build config
└── tsconfig.json        # TypeScript config
```

## api reference

### interactive docs
```
GET    /api/docs                          Swagger UI (browser)
GET    /api/openapi.json                  OpenAPI 3.1 spec (JSON)
```

### setup
```
GET    /api/setup/status                  Check if initialized
POST   /api/setup/init                    Initialize with admin + mode (rate-limited: 10 req/15min)
```

### docker apps
```
GET    /api/apps                          List user's apps
POST   /api/apps                          Create new app
GET    /api/apps/:appId                   Get app details
PATCH  /api/apps/:appId                   Update app settings
DELETE /api/apps/:appId                   Delete app
```

### container control (real docker exec)
```
POST   /api/apps/:appId/start             Start container via `docker start`
POST   /api/apps/:appId/stop              Stop container via `docker stop`
POST   /api/apps/:appId/restart           Restart container via `docker restart`
GET    /api/apps/:appId/logs              Get logs (paginated)
```

### websocket real-time
```
ws://host:3001?appId=<id>                 WebSocket connection for live logs & metrics
  → {"type":"subscribe","appId":"<id>"}         Starts docker logs -f streaming
  → {"type":"subscribe:metrics","appId":"<id>"} Starts docker stats every 2s
```

### user & config
```
GET    /api/user                          Current user profile
GET    /api/config/mode                   Get mode (personal/business)
GET    /health                            API health check
```

### monitoring & metrics
```
GET    /api/apps/:appId/metrics            Server metrics (TPS, CPU, memory, players) with time range
GET    /api/metrics/aggregated             Aggregated metrics across all apps
```

### audit trail
```
GET    /api/audit-log                     Paginated audit log (?user_id=&entity_type=&action=&start_date=&end_date=)
```

### global search
```
GET    /api/search?q=<query>              Search apps, backups, and audit logs (min 2 chars)
```

### notification channels
```
GET    /api/notification-channels          List notification channels
POST   /api/notification-channels          Create channel (type: email|webhook|telegram, config: JSON)
PATCH  /api/notification-channels/:id      Update channel
DELETE /api/notification-channels/:id      Delete channel
POST   /api/notification-channels/:id/test Send test notification
```

### access logs & config versions
```
GET    /api/logs/access                    Access logs (paginated)
GET    /api/apps/:appId/config-versions    Config version history
POST   /api/apps/:appId/config-versions    Create config snapshot
POST   /api/apps/:appId/config-versions/:version/rollback  Rollback to version

### config editor
```
GET    /api/apps/:appId/config              Get app config (YAML/JSON)
POST   /api/apps/:appId/config              Update app config
GET    /config/read                         Read config file from disk
POST   /config/write                        Write config file to disk
POST   /config/validate                     Validate YAML/JSON syntax
```

### databases
```
GET    /api/databases                       List MySQL databases
POST   /api/databases                       Provision a new MySQL container
DELETE /api/databases/:id                   Remove a MySQL database
```

### billing
```
GET    /api/billing/balance                 Get current credit balance
POST   /api/billing/topup                   Add credits to balance
GET    /api/billing/transactions            Transaction history
GET    /api/billing/cost-estimate           Estimate cost for a configuration
GET    /api/billing/rates                   Current billing rates
```

### modpack installer
```
GET    /api/modpacks/search                 Search modpacks (?query=&platform=)
POST   /api/apps/:appId/modpacks/install    Install modpack on server
```

### validation
```
POST   /api/validate/discord-token          Validate Discord bot token
```

### deployments
```
GET    /api/deployments                     List deployments
POST   /api/deployments                     Create deployment
DELETE /api/deployments/:id                 Delete deployment
PATCH  /api/deployments/:id/toggle          Toggle deployment active/inactive
```

### real-time metrics
```
GET    /api/metrics/realtime                Live CPU/memory/disk metrics
GET    /api/metrics/history                 Historical metric data
GET    /api/metrics/stream/config           Configure streaming metrics
GET    /api/metrics/grafana-url             Get Grafana dashboard URL
```

### scheduled tasks
```
GET    /api/scheduled-tasks                 List scheduled tasks
POST   /api/scheduled-tasks                 Create scheduled task
PATCH  /api/scheduled-tasks/:id             Update scheduled task
DELETE /api/scheduled-tasks/:id             Delete scheduled task
```

### maintenance windows
```
GET    /api/maintenance-windows            List maintenance windows
POST   /api/maintenance-windows            Create maintenance window
PATCH  /api/maintenance-windows/:id        Update window
```

### backups
```
GET    /api/backup-jobs                    List backup jobs
POST   /api/backup-jobs                    Create backup job
PATCH  /api/backup-jobs/:id                Update job
DELETE /api/backup-jobs/:id                Delete job
GET    /api/backup-jobs/:jobId/status      Backup execution history
```

### alerting
```
GET    /api/alert-configs                  List alert configurations
POST   /api/alert-configs                  Create alert config
PATCH  /api/alert-configs/:id              Update alert config
DELETE /api/alert-configs/:id              Delete alert config
GET    /api/alert-history                  Alert trigger history
POST   /api/alert-history/:id/acknowledge  Acknowledge alert
```

### health checks
```
GET    /api/health-checks                  Health check results (optional ?app_id= filter)
```

### reports
```
GET    /api/reports                        Generate report (optional start_date, end_date)
GET    /api/reports/export                 Export report (?format=csv|pdf)
```

### customers (business mode)
```
GET    /api/customers                      List customers
POST   /api/customers                      Create customer
PATCH  /api/customers/:customerId          Update customer
DELETE /api/customers/:customerId          Delete customer
POST   /api/seed-demo                      Seed demo data (Business Mode only)
```

## configuration

### environment variables

create `.env.local` (see `.env.local.example`):

```bash
# Supabase (localhost dev)
VITE_SUPABASE_URL=http://localhost:54321
VITE_SUPABASE_ANON_KEY=<your-anon-key>

# API Backend
VITE_API_URL=http://localhost:3001

# Docker
DOCKER_HOST=unix:///var/run/docker.sock
```

### production setup

see [database setup guide](docs/DATABASE_SETUP.md#production-deployment) for:
- managed supabase configuration
- production environment variables
- deployment recommendations

## development

### install
```bash
npm install
```

### start dev servers
```bash
# Both frontend (5173) and backend (3001)
npm run dev
```

### build for production
```bash
npm run build
```

### lint & type check
```bash
npm run lint
```

### preview production build
```bash
npm run preview
```

## security

- **authentication**: supabase auth (email + password)
- **authorization**: jwt tokens in `authorization` header
- **database security**: row-level security (rls) policies
- **user isolation**: users only access their own resources
- **feature gates**: mode-based access control

## docker integration

the panel manages docker containers via direct `docker` cli calls (start/stop/restart through `child_process.exec`). container configurations are stored in postgresql via supabase with full rls enforcement.

real-time monitoring is handled via:
- **websocket live streaming** - `docker logs -f` and `docker stats --no-stream` pushed to browser in real-time
- **web terminal** - in-browser shell via websocket + `docker exec`
- **server metrics** - tps, cpu, memory, player count, lag spike detection
- **health checks** - http ping, port checks with uptime/degraded/down status
- **backup system** - scheduled backup jobs with retention and status tracking
- **access logging** - authentication and console access event recording

## use cases

### personal mode
- home lab automation
- self-hosted hobby projects
- learning docker
- running small production services
- testing and development

### business mode (coming soon)
- managed hosting platform
- vps reselling
- container-as-a-service
- multi-tenant environments

## roadmap

### phase 1 complete
- [x] supabase migration from convex
- [x] setup wizard with mode selection
- [x] docker app crud (full backend + frontend)
- [x] dashboard and app detail pages
- [x] feature gates framework
- [x] comprehensive documentation

### phase 2 monitoring & operations
- [x] server metrics collection (tps, cpu, memory, players)
- [x] health check dashboard with uptime tracking
- [x] backup job automation and scheduling
- [x] access log viewer
- [x] alert configuration and history
- [x] maintenance window scheduling
- [x] config version control with rollback
- [x] reports generation with csv/pdf export
- [x] real docker calls (docker exec for start/stop/restart)
- [x] real-time websocket for live logs & metrics
- [x] rate-limited login (10 req/15min)

### phase 3 ux & platform
- [x] theme persistence (localstorage dark/light mode)
- [x] onboarding wizard (5-step tour)
- [x] pwa support (manifest + service worker)
- [x] mobile-responsive layout (hamburger menu)
- [x] global search (cmd+k palette)
- [x] audit trail with timeline viewer
- [x] web terminal (in-browser container shell)
- [x] notification channels (email, webhook, telegram)
- [x] openapi/swagger docs at /api/docs

### phase 4 business mode
- [ ] customer management
- [ ] plans/pricing ui
- [ ] billing integration hooks
- [ ] team management
- [ ] multi-tenant rbac

### phase 5 advanced
- [ ] white-label system
- [ ] multi-region support
- [ ] advanced analytics dashboard
- [ ] kubernetes mode

### phase 6 new features
- [x] config editor (in-browser yaml/json with syntax highlighting)
- [x] java version selector (8/11/17/21 per server)
- [x] mysql database per click (instant container provisioning)
- [x] git deployment webhook (auto-deploy on github push)
- [x] cronjob scheduler (cron-based scheduled tasks)
- [x] real-time resource graphs (live gauges + sparklines)
- [x] log search (full-text search with filters & pagination)
- [x] prepaid billing (pay-as-you-go balance system)
- [x] modpack-installer (one-click curseforge/modrinth install)
- [x] 2fa (totp) (two-factor authentication)
- [x] user avatar (identicon) — automatisch generierte profilbilder via jdenticon (kein upload nötig)
- [x] discord token validation (validate bot token before start)

## learn more

- **mode architecture**: read [docs/personal_mode.md](docs/PERSONAL_MODE.md)
- **system design**: see [docs/architecture.md](docs/ARCHITECTURE.md)
- **database setup**: follow [docs/database_setup.md](docs/DATABASE_SETUP.md)
- **full details**: check [implementation_summary.md](IMPLEMENTATION_SUMMARY.md)

## troubleshooting

### "failed to check setup status"
- ensure backend api is running on `http://localhost:3001`
- check `vite_api_url` in `.env.local`

### "connection refused" to supabase
- verify supabase is running (`docker ps`)
- check `vite_supabase_url` points to correct instance
- see [database setup guide](docs/DATABASE_SETUP.md)

### "not authenticated" after setup
- check localstorage has `sb_access_token`
- reload page to refresh token
- verify backend validates token correctly

## dependencies

### core
- **react** - ui framework
- **react-router-dom** - client-side routing
- **@supabase/supabase-js** - database & auth
- **axios** - http client
- **sonner** - toast notifications

### development
- **typescript** - type safety
- **tailwindcss** - styling
- **vite** - build tool
- **eslint** - linting

for full list, see [package.json](package.json).

## contributing

see [contributing](../../CONTRIBUTING.md) in repository root.

## license

mit - see [license](../../LICENSE)

## getting started

• **read**: [readme-docker-panel.md](README-DOCKER-PANEL.md) (getting started guide)
• **setup**: follow [docs/database_setup.md](docs/DATABASE_SETUP.md)
• **run**: `npm run dev`
• **visit**: http://localhost:5173
• **explore**: create your first docker app!

## support

- [full documentation](docs/)
- [github issues](https://github.com/DaaanielTV/infra-pilot/issues)
- [discussions](https://github.com/DaaanielTV/infra-pilot/discussions)

built for self-hosters and developers
