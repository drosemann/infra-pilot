# docker panel architecture

## system diagram

```text
┌─────────────────────────────────────────────────────────────────┐
│                       User Browser                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         React Frontend (http://localhost:5173)          │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │  ┌─────────────────────────────────────────────────┐    │  │
│  │  │  App Router (React Router v6)                 │    │  │
│  │  │  ├─ /setup → Setup Wizard                     │    │  │
│  │  │  ├─ /dashboard → Dashboard                    │    │  │
│  │  │  ├─ /apps/new → AppForm (Create)             │    │  │
│  │  │  ├─ /apps/:id → AppDetail                    │    │  │
│  │  │  ├─ /apps/:id/edit → AppForm (Edit)          │    │  │
│  │  │  ├─ /monitoring → Monitoring                 │    │  │
│  │  │  ├─ /backups → Backups                       │    │  │
│  │  │  ├─ /reports → Reports                       │    │  │
│  │  │  ├─ /settings → Settings                     │    │  │
│  │  │  ├─ /audit → AuditLog                        │    │  │
│  │  │  ├─ /logs/access → AccessLogs                │    │  │
│  │  │  └─ /customers → Customers (Business Mode)   │    │  │
│  │  └─────────────────────────────────────────────────┘    │  │
│  │                                                          │  │
│  │  ┌─────────────────────────────────────────────────┐    │  │
│  │  │  Global State                                  │    │  │
│  │  │  ├─ ConfigContext (mode: personal|business)   │    │  │
│  │  │  ├─ localStorage (JWT token)                  │    │  │
│  │  │  └─ localStorage (theme: dark|light)          │    │  │
│  │  └─────────────────────────────────────────────────┘    │  │
│  │                                                          │  │
│  │  ┌─────────────────────────────────────────────────┐    │  │
│  │  │  Global Components                             │    │  │
│  │  │  ├─ OnboardingWizard (5-step tour, 1st visit)  │    │  │
│  │  │  ├─ GlobalSearch (Cmd+K, debounced search)    │    │  │
│  │  │  └─ WebTerminal (in-browser container shell)   │    │  │
│  │  └─────────────────────────────────────────────────┘    │  │
│  │                                                          │  │
│  │  ┌─────────────────────────────────────────────────┐    │  │
│  │  │  Feature Gates                                 │    │  │
│  │  │  └─ featureGates.canXXX(mode: SetupMode)      │    │  │
│  │  └─────────────────────────────────────────────────┘    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
│              HTTP Client (Axios + JWT Token)                     │
│                                                                   │
└──────────────┬──────────────────────────────────────────────────┘
               │ HTTPS/HTTP
               ▼
        ┌──────────────────┐
        │  Firewall/Proxy  │
        └─────────┬────────┘
                  │
        ┌─────────▼─────────────────────────────────────────┐
        │   Backend API Server (Express.js localhost:3001)  │
        ├───────────────────────────────────────────────────┤
        │                                                   │
        │  ┌─────────────────────────────────────────────┐ │
        │  │  Express Routes                            │ │
        │  │  ├─ /api/setup/* - Setup endpoints         │ │
        │  │  ├─ /api/apps/* - CRUD operations          │ │
        │  │  ├─ /api/apps/:id/[start|stop|restart]    │ │
        │  │  ├─ /api/apps/:id/logs - Log streaming     │ │
        │  │  ├─ /api/user - User profile              │ │
        │  │  ├─ /api/config/* - Configuration         │ │
        │  │  ├─ /api/audit-log - Audit trail           │ │
        │  │  ├─ /api/search - Global search            │ │
        │  │  ├─ /api/notification-channels/* - Notifs  │ │
        │  │  ├─ /api/openapi.json - OpenAPI spec       │ │
        │  │  ├─ /api/docs - Swagger UI                 │ │
        │  │  └─ /health - Health check                │ │
        │  └─────────────────────────────────────────────┘ │
        │                                                   │
        │  ┌─────────────────────────────────────────────┐ │
        │  │  WebSocket Server (ws://)                   │ │
        │  │  ├─ subscribe → docker logs -f streaming   │ │
        │  │  └─ subscribe:metrics → docker stats 2s    │ │
        │  └─────────────────────────────────────────────┘ │
        │                                                   │
        │  ┌─────────────────────────────────────────────┐ │
        │  │  Middleware                                │ │
        │  │  ├─ CORS                                   │ │
        │  │  ├─ JSON Parser                            │ │
        │  │  ├─ Rate Limiter (login: 10 req/15min)    │ │
        │  │  ├─ Auth (verifyAuth middleware)           │ │
        │  │  ├─ Audit Logger (logAudit on mutations)  │ │
        │  │  └─ Error Handling                         │ │
        │  └─────────────────────────────────────────────┘ │
        │                                                   │
        └────────────┬──────────────────┬──────────────────┘
                     │                  │
                     │ JWT Validation   │ HTTPS/TCP
                     ▼                  ▼
        ┌─────────────────────────────────────────┐
        │    Supabase Auth                        │
        │  (Handles user creation, JWT signing)   │
        └─────────────┬───────────────────────────┘
                      │
                      │ PostgreSQL Protocol
                      ▼
        ┌──────────────────────────────────────────────────┐
        │  PostgreSQL Database (Supabase)                  │
        │  localhost:5432 (dev) or managed (prod)          │
        ├──────────────────────────────────────────────────┤
        │                                                   │
        │  ┌─────────────────────────────────────────────┐ │
        │  │  Tables                                     │ │
        │  │  ├─ auth.users (Supabase managed)          │ │
        │  │  ├─ user_profiles (with RLS)               │ │
        │  │  ├─ setup_config (mode, initialized)        │ │
        │  │  ├─ docker_apps (container configs)        │ │
        │  │  ├─ app_logs (application logs)            │ │
        │  │  ├─ audit_log (append-only mutations)      │ │
        │  │  ├─ notification_channels (email/webhook/telegram) │ │
        │  │  ├─ backup_jobs with backup_status        │ │
        │  │  ├─ alert_configs with alert_history       │ │
        │  │  ├─ maintenance_windows                    │ │
        │  │  ├─ config_versions                        │ │
        │  │  ├─ health_checks                          │ │
        │  │  ├─ server_metrics                         │ │
        │  │  ├─ access_logs                            │ │
        │  │  ├─ pterodactyl_config (optional)          │ │
        │  │  └─ shared_config (key-value store)         │ │
        │  └─────────────────────────────────────────────┘ │
        │                                                   │
        │  ┌─────────────────────────────────────────────┐ │
        │  │  Security (RLS Policies)                    │ │
        │  │  ├─ Users see only their own apps          │ │
        │  │  ├─ Admins can manage setup config         │ │
        │  │  └─ Auto-enforced by PostgreSQL            │ │
        │  └─────────────────────────────────────────────┘ │
        │                                                   │
        └──────────────────────────────────────────────────┘
```

## native desktop entry (zero-native)

the management panel has an optional zero-native shell alongside the browser-hosted vite app:

```text
┌───────────────────────────┐
│ zero-native Zig shell     │
│ native/src/main.zig       │
└────────────┬──────────────┘
             │ system WebView / zero://app
             ▼
┌───────────────────────────┐
│ React/Vite management UI  │
│ src/ + dist/              │
└────────────┬──────────────┘
             │ HTTP API
             ▼
┌───────────────────────────┐
│ Express API               │
│ server/index.ts           │
└───────────────────────────┘
```

the shell is configured by `app.zon`, loads `dist/index.html` for packaged builds, and uses the vite dev
server when launched through `zero-native dev`. the backend stays as an express service so docker control,
supabase/postgresql access, and integration tests keep the same boundaries as the web deployment.

## data flow: setup & authentication

```text
┌─────────┐
│ Browser │
└────┬────┘
     │ GET /
     ▼
┌───────────────────────┐
│ Check setup status    │
│ GET /api/setup/status │
└───────────┬───────────┘
            │
       ┌────┴─────────────────────┐
       │                          │
   NOT initialized           Already initialized
       │                          │
       ▼                          ▼
┌─────────────────┐   ┌──────────────────────┐
│ Show Setup      │   │ Check localStorage   │
│ Wizard          │   │ for JWT token        │
└────┬────────────┘   └──┬───────────────────┘
     │                   │
     │ User selects      ├─ Token exists → Set ConfigContext
     │ mode (personal/   │
     │ business)         └─ No token → Redirect to /setup
     │
     │ User creates admin account
     │
     ▼
┌────────────────────────────┐
│ POST /api/setup/init       │
│ {email, password, mode}    │
└────────┬───────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ Supabase Auth                   │
│ signUp({email, password})       │
└────────┬────────────────────────┘
         │
         ├─ Create auth.users row
         │
         ▼
┌──────────────────────────────────┐
│ Create user_profiles row         │
│ {id, display_name, role: admin}  │
└────────┬─────────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│ Create setup_config row        │
│ {mode, initialized: true}      │
└────────┬───────────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│ Return JWT token                 │
│ {access_token, refresh_token}    │
└────────┬─────────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│ Store token in localStorage    │
│ sb_access_token = JWT...       │
└────────┬───────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│ Set ConfigContext              │
│ {mode, loading: false}         │
└────────┬───────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│ Render Dashboard @/dashboard   │
└────────────────────────────────┘
```

## data flow: docker app crud

```text
User clicks "New App"
        │
        ▼
┌──────────────────────┐
│ Navigate to /apps/new│
└────────┬─────────────┘
         │
         ▼
┌────────────────────────────────────┐
│ <AppForm /> (create mode)          │
│ Show form with fields:             │
│  - name, image                     │
│  - ports (add/remove)              │
│  - environment_vars (add/remove)   │
│  - volumes (add/remove)            │
│  - memory_limit                    │
└────────┬───────────────────────────┘
         │
         │ User fills in form
         │ (e.g., name="web", image="nginx:latest")
         │
         ▼
┌─────────────────────────────────────┐
│ Form submission validation          │
│ if (!name || !image) error "Required"
└────┬────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────────────┐
│ POST /api/apps                                 │
│ Authorization: Bearer <JWT>                    │
│ {name, image, ports, env, volumes, ...}       │
└────────┬─────────────────────────────────────┘
         │
         ▼
┌────────────────────────────┐
│ Backend: verifyAuth        │
│ Validate JWT signature     │
└────────┬───────────────────┘
         │
         ├─ Invalid? → 401 Unauthorized
         │
         ▼
┌─────────────────────────────┐
│ Insert docker_apps row      │
│ {user_id, name, image, ...} │
└────────┬────────────────────┘
         │
         ├─ RLS checks: user_id == auth.uid()
         │
         ▼
┌─────────────────────────────┐
│ Return 201 Created          │
│ {id, name, image, status}   │
└────────┬────────────────────┘
         │
         ▼
┌──────────────────────────┐
│ Frontend receives app    │
│ Show success toast       │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│ Navigate to /apps/{id}   │
│ App detail page loads    │
└──────────────────────────┘
```

## feature gate checking

```text
Component wants to render business feature
        │
        ▼
┌────────────────────────────────────┐
│ const { mode } = useConfig()       │
│ Returns: 'personal' or 'business'  │
└────────┬───────────────────────────┘
         │
         ▼
┌────────────────────────────────────┐
│ Check feature gate:                │
│ if (!featureGates.canXXX(mode)) {  │
│   return <Disabled />              │
│ }                                  │
└────────┬───────────────────────────┘
         │
      ┌──┴──────────────────────────────┐
      │                                    │
    mode == 'personal'              mode == 'business'
      │                                    │
      ▼                                    ▼
┌──────────────────────┐      ┌──────────────────────┐
│ Feature hidden       │      │ Feature visible      │
│ Show helpful message │      │ Full functionality   │
│ "Not available in    │      │ available            │
│  Personal Mode"      │      │                      │
└──────────────────────┘      └──────────────────────┘
```

## mode decision tree

```text
Setup Wizard
    │
    ├─ Select Personal Mode
    │   │
    │   ├─ Features Enabled:
    │   │   ├─ Docker app CRUD ✅
    │   │   ├─ Container controls ✅
    │   │   ├─ Logs & monitoring ✅
    │   │   └─ Single admin ✅
    │   │
    │   └─ Features Disabled:
    │       ├─ Customer management ❌
    │       ├─ Plans/billing ❌
    │       ├─ White-label ❌
    │       └─ Team management ❌
    │
    └─ Select Business Mode
        │
        ├─ Features Enabled:
        │   ├─ All Personal Mode features ✅
        │   ├─ Customer management ✅
        │   ├─ Plans/billing ✅
        │   ├─ White-label ✅
        │   └─ Team management ✅
        │
        └─ Additional Considerations:
            ├─ More database tables
            ├─ Advanced RBAC
            └─ Billing hooks
```

## deployment architecture (production)

```text
┌──────────────────────────────────────────────────────────┐
│  User's Internet                                         │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
           ┌─────────────────────┐
           │  CDN / Load Balancer│
           │  (Optional: Vercel) │
           └──────────┬──────────┘
                      │
        ┌─────────────┴─────────────┐
        │                           │
        ▼                           ▼
   ┌─────────────┐      ┌──────────────────────┐
   │ Frontend    │      │ Backend API          │
   │ (Nginx,     │      │ (Node.js + Express)  │
   │  Vercel, or │      │ (Docker container)   │
   │  your host) │      └──────────┬───────────┘
   └─────────────┘                 │
                                   ▼
                          ┌─────────────────────┐
                          │  Supabase Project   │
                          │  (Managed or        │
                          │   Self-hosted)      │
                          ├─────────────────────┤
                          │ PostgreSQL          │
                          │ Auth                │
                          │ RLS/Security        │
                          └─────────────────────┘
                                   │
                                   ▼
                          ┌─────────────────────┐
                          │  Docker Daemon      │
                          │  (Local or remote)  │
                          │  /var/run/docker.sock
                          │  OR tcp://docker:2375
                          └─────────────────────┘
```

## summary

- **frontend**: react spa with client-side routing and jwt auth
- **backend**: express.js rest api with route-level auth & rls
- **database**: postgresql with row-level security
- **auth**: supabase auth (jwt tokens)
- **feature gates**: configured at setup, checked everywhere
- **scaling**: easy to add business mode tables/routes later

the architecture is **modular, secure, and extensible**.
