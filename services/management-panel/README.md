# 🐳 Docker Panel

**Self-hosted Docker container management panel** with Personal Mode for individual users and optional Hosting Business Mode.

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](../../LICENSE)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0%2B-blue?logo=typescript)](https://www.typescriptlang.org/)
[![React 19](https://img.shields.io/badge/React-19-61dafb?logo=react)](https://react.dev)
[![Node.js 18+](https://img.shields.io/badge/Node.js-18%2B-brightgreen?logo=node.js)](https://nodejs.org/)

## 🎯 Overview

**Docker Panel** is a Pterodactyl-inspired web panel for managing Docker containers locally. Perfect for self-hosters, hobby projects, and home labs.

### ✨ Personal Mode (Default)
- 🐳 **Docker App Management** - Create, deploy, and manage containerized applications
- 🎛️ **Container Controls** - Start/stop/restart with one click
- 📊 **Dashboard** - Real-time status and metrics
- 🔍 **Logs & Monitoring** - Stream application logs and view status
- ⚙️ **Configuration** - Port mapping, environment variables, volume mounts
- 🔐 **Simple Auth** - Single admin account

### 🚀 Business Mode (Optional)
- ✅ All Personal Mode features +
- 👥 Customer account management
- 💰 Plans and pricing tiers
- 🏷️ White-label branding
- 👔 Team and staff management
- 📋 Audit logging

---

## 🚀 Quick Start (3 Commands)

```bash
# 1. Get the code
cd services/management-panel

# 2. Setup environment
cp .env.local.example .env.local

# 3. Install and run
npm install && npm run dev
```

### Demo Feature Flag (per-env)

- Gate the Seed Demo UI behind a per-environment feature flag to avoid accidental usage in prod-like environments.
- Env var: `VITE_DEMO_FEATURE_ENABLED`
- Default: false (flag is off unless explicitly enabled)
- How to enable/disable:
  - Local development: set in your .env.local
    - Add: `VITE_DEMO_FEATURE_ENABLED=true`
  - Staging/QA: set to `true` to enable demo flows for testers, or `false` to hide in testing
  - Production: keep it `false` to avoid accidental seeds
- Verification:
  - Start frontend and check that the Seed Demo button appears only when the flag is enabled.
  - Click Seed Demo to see the confirmation modal before seeding.
- Notes:
- This flag gates only the UI; the backend seed endpoints remain available to programmatic use when needed and are still protected by Business Mode.

### QA Checklist (Gating Demo Per-Env)
- Development (VITE_DEMO_FEATURE_ENABLED=true)
  - Seed Demo button is visible on the Customers page in Business Mode.
  - Click Seed Demo to open the confirmation modal; confirm to seed.
  - Verify the UI shows a success toast with seeded counts and the Customers list refreshes.
  - Verify the Seed Demo action is not shown when the flag is off.
- Staging/QA (VITE_DEMO_FEATURE_ENABLED=true or false)
  - If true, perform the same checks as Development.
  - If false, Seed Demo button should be hidden; confirm gating works in this environment.
- Production (VITE_DEMO_FEATURE_ENABLED not set or false)
  - Seed Demo button must be hidden; UI should reflect no demo button.
  - Optional: try calling the API directly with a valid token and confirm backend blocks based on Business Mode as designed.
- Validation steps (end-to-end)
  - Start both frontend and backend, login as a Business Mode admin, navigate to Customers, ensure gating behavior matches env flag.
  - Seed Demo idempotence: verify re-clicking Seed Demo (when enabled) does not crash and either updates or leaves data idempotently.
- Troubleshooting
  - If Seed Demo button is missing, verify VITE_DEMO_FEATURE_ENABLED is set to true and the frontend is restarted to pick up the env var.
  - If Seed Demo still seeds in prod-like env, rebuild the frontend to ensure the flag is re-evaluated.

**Then open:** http://localhost:5173

**First-time setup will guide you through:**
1. Choose Personal Mode or Business Mode
2. Create admin account
3. Start managing Docker apps

---


## 🖥️ Native Desktop Shell (zero-native)

The panel can also run as a zero-native desktop app. The React/Vite UI is loaded into a native WebView, while the Express API remains the local backend on `http://127.0.0.1:3001`.

```bash
# Terminal 1: API
npm run dev:backend

# Terminal 2: native shell + Vite managed by zero-native
npm run desktop:dev -- -Dzero-native-path=/absolute/path/to/zero-native
```

Useful scripts:

- `npm run desktop:validate` validates `app.zon`.
- `npm run desktop:doctor` checks the host zero-native environment.
- `npm run desktop:package -- -Dzero-native-path=/absolute/path/to/zero-native` packages the built `dist/` assets.

See the repository guide at [`../../docs/desktop/zero-native-management-panel.md`](../../docs/desktop/zero-native-management-panel.md).

## 📚 Documentation

| Document | Topic |
|----------|-------|
| [Docker Panel Quick Start](README-DOCKER-PANEL.md) | Getting started guide |
| [Personal Mode Architecture](docs/PERSONAL_MODE.md) | Mode design & feature gates |
| [Database Setup Guide](docs/DATABASE_SETUP.md) | Supabase configuration |
| [System Architecture](docs/ARCHITECTURE.md) | Technical diagrams & flows |
| [Implementation Summary](IMPLEMENTATION_SUMMARY.md) | Complete overview |

---

## ⚡ Features at a Glance

### Personal Mode ✅
- Docker app CRUD (create, read, update, delete)
- Container start/stop/restart controls
- Real-time logs and status monitoring
- Environment variable configuration
- Port mapping (host ↔ container)
- Volume/mount management
- Memory and CPU limits
- Simple dashboard with app grid
- Server performance monitoring with real-time metrics (TPS, CPU, memory, player count)
- Health check dashboard with uptime tracking and incident timeline
- Backup job automation and scheduling with retention policies
- Access log viewer for authentication and console events
- Reports generation with CSV/PDF export
- Alert configuration (metric thresholds) and alert history
- Maintenance window scheduling
- Config version control with snapshot and rollback

### Business Mode (Roadmap) 🔜
- Customer accounts and management
- Plans and pricing configuration
- Billing integration hooks
- White-label branding
- Team/staff RBAC
- Audit logging
- Advanced analytics

---

## 🏗️ Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Frontend | React 19 + TypeScript | Modern, type-safe |
| Styling | Tailwind CSS | Utility-first, dark mode |
| Routing | React Router v6 | Industry standard |
| Backend | Express.js | Lightweight, async |
| Database | PostgreSQL + Supabase | Structured, RLS security |
| Auth | Supabase Auth | Built-in, scalable |

---

## 📂 Project Structure

```
services/management-panel/
├── src/
│   ├── pages/           # Setup, Dashboard, AppForm, AppDetail, Monitoring, AccessLogs, Backups, Reports, Settings
│   ├── components/      # MainLayout, shared components, monitoring/backup/alert components
│   ├── lib/             # API client, auth, types, feature gates
│   ├── App.tsx          # Main router and mode provider
│   └── main.tsx         # React entry point
├── server/
│   ├── index.ts         # Express API (1142 lines, 60+ routes)
│   └── presets.ts       # Server preset definitions
├── db/
│   └── schema.sql       # PostgreSQL schema with RLS (server_metrics, access_logs, config_versions, maintenance_windows, backup_jobs, backup_status, alert_configs, alert_history, health_checks)
├── docs/
│   ├── PERSONAL_MODE.md # Mode architecture
│   ├── DATABASE_SETUP.md # Setup guide
│   └── ARCHITECTURE.md   # Technical architecture
├── tests/
│   ├── helpers/          # Shared test mocks (supabase-mock, http-client)
│   ├── unit/             # Unit tests (auth-storage)
│   ├── integration/      # API integration tests (api, rate-limit)
│   └── playwright/       # Playwright E2E browser tests
├── package.json         # Dependencies
├── vite.config.ts       # Frontend build config
└── tsconfig.json        # TypeScript config
```

---

## 🔌 API Reference

### Setup
```
GET  /api/setup/status              Check if initialized
POST /api/setup/init                Initialize with admin + mode
```

### Docker Apps
```
GET    /api/apps                    List user's apps
POST   /api/apps                    Create new app
GET    /api/apps/:appId             Get app details
PATCH  /api/apps/:appId             Update app settings
DELETE /api/apps/:appId             Delete app
```

### Container Control
```
POST   /api/apps/:appId/start       Start container
POST   /api/apps/:appId/stop        Stop container
POST   /api/apps/:appId/restart     Restart container
GET    /api/apps/:appId/logs        Get logs (paginated)
```

### User & Config
```
GET    /api/user                    Current user profile
GET    /api/config/mode             Get mode (personal/business)
GET    /health                      API health check
```

### Monitoring & Metrics
```
GET    /api/apps/:appId/metrics            Server metrics (TPS, CPU, memory, players) with time range
GET    /api/metrics/aggregated             Aggregated metrics across all apps
```

### Access Logs & Config Versions
```
GET    /api/logs/access                    Access logs (paginated)
GET    /api/apps/:appId/config-versions    Config version history
POST   /api/apps/:appId/config-versions    Create config snapshot
POST   /api/apps/:appId/config-versions/:version/rollback  Rollback to version
```

### Maintenance Windows
```
GET    /api/maintenance-windows            List maintenance windows
POST   /api/maintenance-windows            Create maintenance window
PATCH  /api/maintenance-windows/:id        Update window
```

### Backups
```
GET    /api/backup-jobs                    List backup jobs
POST   /api/backup-jobs                    Create backup job
PATCH  /api/backup-jobs/:id                Update job
DELETE /api/backup-jobs/:id                Delete job
GET    /api/backup-jobs/:jobId/status      Backup execution history
```

### Alerting
```
GET    /api/alert-configs                  List alert configurations
POST   /api/alert-configs                  Create alert config
PATCH  /api/alert-configs/:id              Update alert config
DELETE /api/alert-configs/:id              Delete alert config
GET    /api/alert-history                  Alert trigger history
POST   /api/alert-history/:id/acknowledge  Acknowledge alert
```

### Health Checks
```
GET    /api/health-checks                  Health check results (optional ?app_id= filter)
```

### Reports
```
GET    /api/reports                        Generate report (optional start_date, end_date)
GET    /api/reports/export                 Export report (?format=csv|pdf)
```

---

## ⚙️ Configuration

### Environment Variables

Create `.env.local` (see `.env.local.example`):

```bash
# Supabase (localhost dev)
VITE_SUPABASE_URL=http://localhost:54321
VITE_SUPABASE_ANON_KEY=<your-anon-key>

# API Backend
VITE_API_URL=http://localhost:3001

# Docker
DOCKER_HOST=unix:///var/run/docker.sock
```

### Production Setup

See [Database Setup Guide](docs/DATABASE_SETUP.md#production-deployment) for:
- Managed Supabase configuration
- Production environment variables
- Deployment recommendations

---

## 🚦 Development

### Install
```bash
npm install
```

### Start Dev Servers
```bash
# Both frontend (5173) and backend (3001)
npm run dev
```

### Build for Production
```bash
npm run build
```

### Lint & Type Check
```bash
npm run lint
```

### Preview Production Build
```bash
npm run preview
```

---

## 🔒 Security

- **Authentication**: Supabase Auth (email + password)
- **Authorization**: JWT tokens in `Authorization` header
- **Database Security**: Row-level security (RLS) policies
- **User Isolation**: Users only access their own resources
- **Feature Gates**: Mode-based access control

---

## 🐳 Docker Integration

The panel stores app configurations and manages container state via Supabase. Docker API integration for live container operations (start/stop/restart) is wired through the backend with Dockerode available for socket-level control.

Real-time monitoring is handled via:
- **Server metrics** - TPS, CPU, memory, player count, lag spike detection
- **Health checks** - HTTP ping, port checks with uptime/degraded/down status
- **Backup system** - Scheduled backup jobs with retention and status tracking
- **Access logging** - Authentication and console access event recording

---

## 🎯 Use Cases

### Personal Mode
✅ Home lab automation  
✅ Self-hosted hobby projects  
✅ Learning Docker  
✅ Running small production services  
✅ Testing and development  

### Business Mode (Coming Soon)
✅ Managed hosting platform  
✅ VPS reselling  
✅ Container-as-a-Service  
✅ Multi-tenant environments  

---

## 🛣️ Roadmap

### Phase 1 ✅ Complete
- [x] Supabase migration from Convex
- [x] Setup wizard with mode selection
- [x] Docker app CRUD (full backend + frontend)
- [x] Dashboard and app detail pages
- [x] Feature gates framework
- [x] Comprehensive documentation

### Phase 2 ⏳ Business Mode
- [ ] Customer management
- [ ] Plans/pricing UI
- [ ] Billing integration hooks
- [ ] Audit logging
- [ ] Team management

### Phase 3 ✅ Monitoring & Operations
- [x] Server metrics collection (TPS, CPU, memory, players)
- [x] Health check dashboard with uptime tracking
- [x] Backup job automation and scheduling
- [x] Access log viewer
- [x] Alert configuration and history
- [x] Maintenance window scheduling
- [x] Config version control with rollback
- [x] Reports generation with CSV/PDF export
- [ ] Live container creation (Dockerode integration)
- [ ] Real-time status (WebSocket)
- [ ] Image pull workflows

### Phase 4 ⏳ Advanced
- [ ] White-label system
- [ ] Multi-tenant RBAC
- [ ] Multi-region support
- [ ] Advanced analytics dashboard

---

## 📖 Learn More

- **Mode Architecture**: Read [docs/PERSONAL_MODE.md](docs/PERSONAL_MODE.md)
- **System Design**: See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Database Setup**: Follow [docs/DATABASE_SETUP.md](docs/DATABASE_SETUP.md)
- **Full Details**: Check [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)

---

## 🐛 Troubleshooting

### "Failed to check setup status"
- Ensure backend API is running on `http://localhost:3001`
- Check `VITE_API_URL` in `.env.local`

### "Connection refused" to Supabase
- Verify Supabase is running (`docker ps`)
- Check `VITE_SUPABASE_URL` points to correct instance
- See [Database Setup Guide](docs/DATABASE_SETUP.md)

### "Not authenticated" after setup
- Check localStorage has `sb_access_token`
- Reload page to refresh token
- Verify backend validates token correctly

---

## 📦 Dependencies

### Core
- **react** - UI framework
- **react-router-dom** - Client-side routing
- **@supabase/supabase-js** - Database & auth
- **axios** - HTTP client
- **sonner** - Toast notifications

### Development
- **typescript** - Type safety
- **tailwindcss** - Styling
- **vite** - Build tool
- **eslint** - Linting

For full list, see [package.json](package.json).

---

## 🤝 Contributing

See [CONTRIBUTING.md](../../CONTRIBUTING.md) in repository root.

---

## 📄 License

MIT - See [LICENSE](../../LICENSE)

---

## 🎉 Getting Started

1. **Read**: [README-DOCKER-PANEL.md](README-DOCKER-PANEL.md) (Getting Started Guide)
2. **Setup**: Follow [docs/DATABASE_SETUP.md](docs/DATABASE_SETUP.md)
3. **Run**: `npm run dev`
4. **Visit**: http://localhost:5173
5. **Explore**: Create your first Docker app!

---

## 📞 Support

- 📖 [Full Documentation](docs/)
- 🐛 [GitHub Issues](https://github.com/DaaanielTV/infra-pilot/issues)
- 💬 [Discussions](https://github.com/DaaanielTV/infra-pilot/discussions)

---

**Built with ❤️ for self-hosters and developers**
