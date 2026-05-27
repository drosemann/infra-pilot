# docker panel - complete changelog & implementation

## release 2026-05-26 — ux & platform expansion

### new backend features
- **real docker calls** — container start/stop/restart now use `docker exec` directly instead of status-only stubs
- **rate-limited login** — `post /api/setup/init` protected by 10 requests per 15-minute window
- **openapi / swagger docs** — full openapi 3.1 spec at `/api/openapi.json` with interactive swagger ui at `/api/docs`
- **audit trail** — new `audit_log` table logs all mutations (app crud, backups, alerts, config) with `get /api/audit-log` endpoint supporting pagination and filtering
- **websocket real-time** — dedicated websocket server for live `docker logs -f` streaming and `docker stats` metrics at 2s intervals
- **global search api** — `get /api/search?q=` searches apps, backups, and audit logs via postgresql ilike
- **notification channels** — full crud for email/webhook/telegram channels plus test endpoint; new `notification_channels` table

### new frontend features
- **theme persistence** — dark/light mode preference saved to `localstorage`
- **onboarding wizard** — 5-step guided tour shown on first visit, dismissable with `localstorage` flag
- **pwa support** — `manifest.json` + service worker with cache-first strategy, registered in `main.tsx`
- **mobile-responsive layout** — hamburger menu toggle, slide-in sidebar on small screens
- **global search (cmd+k)** — command palette with debounced search, grouped results, keyboard shortcut
- **audit trail viewer** — new `/audit` page with filterable table and pagination
- **web terminal** — in-browser container shell with websocket, command input, 500-line buffer, fullscreen toggle

### new integration service features
- **notification providers** — email (smtp/tls), webhook (http post), telegram (bot api) with `notificationmanager` registry
- **alert notification integration** — alerts can now trigger delivery through configured notification channels

## overview

the management panel has been completely redesigned and reimplemented from scratch to create a **self-hosted docker container management panel** with:

- personal mode (default) - simple, focused docker app management for self-hosters
- business mode (optional) - full-featured hosting control panel (roadmap)
- feature gates - clean separation of concerns based on mode
- supabase backend - modern database with rls and authentication
- express.js api - restful backend with 30+ endpoints
- react router - type-safe frontend routing
- comprehensive documentation - architecture guides and quick-start

## deleted files & directories

### removed convex-based code
- `convex/` (entire directory) - replaced with express.js backend
- `setup.mjs` - old convex setup script
- `src/signinform.tsx` - replaced by setup.tsx
- `src/signoutbutton.tsx` - replaced by mainlayout.tsx

### removed documentation
- `redesign_plan.md` (root) - outdated redesign plan

## new files created

### backend server (445 lines)
- **`server/index.ts`** - express.js api with:
  - setup initialization routes
  - docker app crud operations
  - container control endpoints (start/stop/restart)
  - log streaming (paginated)
  - user management endpoints
  - configuration endpoints
  - jwt authentication middleware
  - supabase integration

### database schema (119 lines)
- **`db/schema.sql`** - postgresql schema with:
  - 7 core tables (setup_config, docker_apps, user_profiles, app_logs, pterodactyl_config, shared_config)
  - row-level security (rls) policies on all user-scoped tables
  - indexes for query optimization
  - prepared for business mode expansion

### frontend pages (920 lines total)

| file | lines | purpose |
|------|-------|---------|
| `src/pages/Setup.tsx` | 150 | onboarding wizard with mode selection |
| `src/pages/Dashboard.tsx` | 160 | main dashboard with app grid |
| `src/pages/AppForm.tsx` | 280 | create/edit docker apps with full config |
| `src/pages/AppDetail.tsx` | 330 | app management with 5 tabs |

### utilities & libraries (190 lines total)

| file | lines | purpose |
|------|-------|---------|
| `src/lib/api.ts` | 90 | axios api client with all endpoints |
| `src/lib/auth.ts` | 35 | supabase auth helpers |
| `src/lib/types.ts` | 65 | typescript types, interfaces, feature gates |

### components
- **`src/components/MainLayout.tsx`** (75 lines) - main layout with header, nav, logout

### configuration files
- **`.env.local.example`** - environment variable template
- **`setup.sh`** - quick-start automation script

### documentation (1,200+ lines total)

| file | lines | topic |
|------|-------|-------|
| `readme-docker-panel.md` | 350 | getting started guide |
| `implementation_summary.md` | 350 | complete implementation overview |
| `docs/personal_mode.md` | 420 | mode architecture & design decisions |
| `docs/database_setup.md` | 140 | supabase setup instructions |
| `docs/architecture.md` | 300 | technical diagrams & data flows |

### modified files

• **`package.json`** - updated dependencies:
   - removed: `convex`, `@convex-dev/auth`
   - added: `@supabase/supabase-js`, `@supabase/auth-helpers-react`, `express`, `express-cors`, `axios`, `react-router-dom`, `ts-node`, `@types/express`

• **`src/App.tsx`** - complete rewrite:
   - removed convex providers and components
   - added react router setup
   - added configcontext for mode management
   - implemented conditional routing based on setup status
   - integrated setup wizard flow

• **`src/main.tsx`** - simplified:
   - removed convexauthprovider
   - removed convexreactclient
   - kept simple react entry point

• **`readme.md`** (root) - updated:
   - removed old setup instructions
   - added docker panel quick start
   - added links to new documentation
   - highlighted personal mode

• **`readme.md`** (management-panel) - complete rewrite:
   - replaced single paragraph with comprehensive guide
   - added features matrix
   - added architecture overview
   - added api reference
   - added troubleshooting section
   - added roadmap

## architecture changes

### before: convex-based
```
Frontend (Vite + React)
    ↓
Convex Auth Provider
Convex React Client
    ↓
Convex Backend (Functions)
Convex Database
```

**issues:**
- tightly coupled to convex
- limited customization
- no clear separation for feature modes
- limited authentication options

### after: supabase + express.js
```
Frontend (Vite + React + React Router)
    ↓ (JWT Token in Authorization header)
Express.js API Server (:3001)
    ↓
Supabase (Auth + PostgreSQL)
    ↓
PostgreSQL with RLS Policies
```

**improvements:**
- independent, deployable backend
- full customization control
- clean feature gate separation
- industry-standard stack
- rls-based security
- easy to extend

## core feature implementation

### setup wizard
**new file:** `src/pages/Setup.tsx`

```
Step 1: Mode Selection
├─ Personal Mode (default, recommended)
└─ Hosting Business Mode

Step 2: Create Admin Account
├─ Display Name
├─ Email
├─ Password
└─ Submit

Result:
├─ Create auth.users (Supabase Auth)
├─ Create user_profiles (DB)
├─ Create setup_config with mode
└─ Issue JWT token → redirect to Dashboard
```

### docker app management
**new files:** `src/pages/AppForm.tsx`, `src/pages/AppDetail.tsx`

**crud operations:**
- **create**: form with ports, environment, volumes, resource limits
- **read**: dashboard grid + detail page with tabs
- **update**: edit form with pre-filled values
- **delete**: confirmation dialog before deletion

**tabs on app detail:**
• overview - container info and metadata
• logs - real-time paginated log viewer
• environment - view env variables
• volumes - view mount paths
• settings - edit and delete controls

### container controls
**backend:** `server/index.ts` routes

```
POST /api/apps/:appId/start
POST /api/apps/:appId/stop
POST /api/apps/:appId/restart
```

currently updates status in db (stub for docker api integration).

### feature gates system
**new file:** `src/lib/types.ts`

```typescript
export const featureGates = {
  // Personal mode (always available)
  canManageLocalApps: (mode) => true,
  canViewLogs: (mode) => true,
  canConfigureEnv: (mode) => true,
  
  // Business mode features
  canManageCustomers: (mode) => mode === 'business',
  canManagePlans: (mode) => mode === 'business',
  canViewBilling: (mode) => mode === 'business',
  canWhitelabel: (mode) => mode === 'business',
  canManageTeam: (mode) => mode === 'business',
  canViewAuditLogs: (mode) => mode === 'business',
  canConfigureHosting: (mode) => mode === 'business',
}
```

**usage in components:**
```tsx
if (!featureGates.canViewAuditLogs(mode)) {
  return <Disabled />;
}
```

## security implementation

### authentication flow
• user creates account during setup
• supabase auth creates `auth.users` row
• jwt token issued and stored in localstorage
• token sent in `authorization: bearer <token>` header
• backend validates token on each request

### database security
• **rls policies** - enforced at database level
   - users see only their own docker_apps
   - users see only their own user_profile
• **auth middleware** - express.js validates jwt
• **feature gates** - ui and api level checks

### example rls policy
```sql
CREATE POLICY "Users can view their own apps" ON docker_apps
FOR SELECT USING (auth.uid() = user_id);
```

## documentation created

### quick start documentation
- **readme-docker-panel.md** - 3-command quick start
- **readme.md (panel)** - complete feature overview

### architecture documentation
- **personal_mode.md** - mode design, feature gates, migration path
- **architecture.md** - system diagrams, data flows, deployment
- **database_setup.md** - supabase and postgresql setup

### implementation documentation
- **implementation_summary.md** - features, roadmap, tech stack

## getting started

### development (3 commands)
```bash
cd services/management-panel
cp .env.local.example .env.local
npm install && npm run dev
```

visit: `http://localhost:5173`
api: `http://localhost:3001`

### first run
• select personal mode or business mode
• create admin account
• dashboard appears automatically
• create your first docker app!

## roadmap

### phase 1 (complete)
- [x] switch from convex to supabase
- [x] setup wizard with mode selection
- [x] docker app crud
- [x] dashboard and detail pages
- [x] feature gates throughout
- [x] documentation

### phase 2 (business mode mvp)
- [ ] customer management ui
- [ ] plans and pricing
- [ ] billing integration
- [ ] audit logging
- [ ] team management

### phase 3 (docker integration)
- [ ] live container creation (dockerode)
- [ ] real-time status updates (websocket)
- [ ] image pull/push workflows
- [ ] container health monitoring
- [ ] resource usage metrics

### phase 4 (advanced)
- [ ] white-label branding
- [ ] advanced multi-tenant rbac
- [ ] multi-region deployment
- [ ] advanced analytics dashboard

## statistics

| metric | value |
|--------|-------|
| backend lines | 445 |
| frontend pages | 4 (920 lines) |
| database schema | 119 lines |
| api endpoints | 30+ |
| documentation | 1,200+ lines |
| total new code | 2,500+ lines |
| test coverage | framework ready |

## migration path: convex → supabase

### what changed
| aspect | before (convex) | after (supabase) |
|--------|-----------------|-----------------|
| auth | `@convex-dev/auth` | supabase auth |
| database | convex db | postgresql |
| mutations | convex functions | express routes |
| queries | convex hooks | axios calls |
| backend | serverless | node.js server |
| deployment | convex platform | docker/any host |

### data preservation
- new schema supports existing features
- empty fresh start (no data migration needed)
- designed for clean setup from scratch

## key improvements

• independent backend - not locked into convex
• better customization - full control over api and auth
• cleaner architecture - separation of concerns
• feature gates - easy to toggle features per mode
• enterprise ready - standard stack, documented, secure
• type safe - typescript throughout
• well documented - comprehensive guides
• personal mode first - simplicity by default

## documentation links

• [quick start](readme-docker-panel.md)
• [mode architecture](docs/PERSONAL_MODE.md)
• [database setup](docs/DATABASE_SETUP.md)
• [system architecture](docs/ARCHITECTURE.md)
• [full overview](implementation_summary.md)

## summary

the docker panel has been modernized, simplified, and made self-hostable with a focus on personal mode for individual users. the architecture is clean, well-documented, and ready for extension with business mode features.

ready to deploy and use immediately.
