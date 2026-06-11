# infra-pilot

[![CI](https://github.com/d5niel-lgtm/infra-pilot/actions/workflows/ci.yml/badge.svg)](https://github.com/d5niel-lgtm/infra-pilot/actions/workflows/ci.yml)

Container management and server provisioning platform with a React dashboard, Python orchestrator, and Discord bot integration for self-hosted infrastructure.

## Quick start

```bash
git clone https://github.com/DaaanielTV/infra-pilot.git
cd infra-pilot
cp .env.example .env
docker compose up -d
```

**was sollte ich jetzt sehen?**

| service | url |
|---------|-----|
| management panel (frontend) | http://localhost:5173 |
| management panel (api) | http://localhost:3001 |
| integration service api | http://localhost:9000 |
| orchestrator health | http://localhost:8500/health |

### Default Ports

| Port | Service |
|------|---------|
| 5173 | Management Panel (Frontend) |
| 3001 | Management Panel (Backend) |
| 8500 | Orchestrator Agent |
| 9000 | Integration Service |
| 3002 | Discord Service |
| 5432 | PostgreSQL |
| 6379 | Redis |
| 9090 | Prometheus |
| 3000 | Grafana |

Check availability: `lsof -i :PORT` (macOS/Linux) or `netstat -an | findstr :PORT` (Windows)

## inhaltsverzeichnis

• [aktueller projektstatus](#aktueller-projektstatus)
• [quick start](#quick-start)
• [repository-struktur](#repository-struktur)
• [services](#services)
• [v3 feature overview — 100 neue features](#v3-feature-overview--100-neue-features)
• [v4 feature overview — 100 neue features](#v4-feature-overview--100-neue-features)
• [projektstatistiken](#projektstatistiken)
• [konfiguration](#konfiguration)
• [development & testing](#development--testing)
• [docker & deployment](#docker--deployment)
• [dokumentation](#dokumentation)
• [security](#security)
• [contributing](#contributing)
• [license & warranty](#license--warranty)

## v4 feature overview — 100 neue features

das v4-update erweitert infra pilot um **100 neue features** in **10 kategorien** (~150.000 zeilen code):

| Kategorie | Features | Status |
|-----------|----------|--------|
| 1. federated hybrid cloud management | 1-10 | ✅ ~15k loc |
| 2. platform engineering & inner source | 11-20 | ✅ ~15k loc |
| 3. finops & advanced cost management | 21-30 | ✅ ~15k loc |
| 4. resiliency engineering & disaster recovery | 31-40 | ✅ ~15k loc |
| 5. data platform & analytics | 41-50 | ✅ ~15k loc |
| 6. aiops & autonomous operations | 51-60 | ✅ ~15k loc |
| 7. compliance automation & audit 2.0 | 61-70 | ✅ ~15k loc |
| 8. customer experience & support platform | 71-80 | ✅ ~15k loc |
| 9. security operations center (soc) deep | 81-90 | ✅ ~15k loc |
| 10. emerging technologies & web3 | 91-100 | ✅ ~15k loc |

jede kategorie umfasst integration-service-module, orchestrator-cogs, management-panel-seiten, cli-befehle, mobile-screens, api-routen, tests und dokumentation.

detailplan: [docs/feature-implementation-plan-v4.md](docs/feature-implementation-plan-v4.md)

## aktueller projektstatus

• management panel: react/vite-frontend mit express-api, personal mode, optionalem business mode, supabase/postgresql-anbindung und seed-demo-feature-gate.
• orchestrator agent: python-service mit discord-/vps-provisioning-komponenten, provider-neutraler namensauflösung und eigenen tests.
• discord service: node.js/discord.js-integration für pterodactyl-/provisioning-flows. alle 28 module sind eingebunden und verdrahtet.
• provider-neutrales test-framework: token-mapping unter `infra/naming/` und tests unter `tests/`.
• real-time websocket: live container-logs und metrik-streaming via websocket-server im management panel.
• audit trail: append-only-audit-log für alle mutationen (apps, backups, alerts, config) mit timeline-viewer.
• globale suche: cmd+k-palette durchsucht apps, backups und audit-logs via postgresql ilike.
• notification channels: verwaltung mehrerer benachrichtigungskanäle (email, webhook, telegram) mit integrierten providern.
• pwa support: manifest + service worker für installierbare desktop-app und offline-caching.
• onboarding wizard: 5-schrittige geführte tour nach der ersteinrichtung.
• mobile-responsive layout: hamburger-menü, slide-in-sidebar für mobilgeräte.
• web terminal: in-browser-container-terminal via websocket + docker exec.
• modpack-installer — one-click modpack install from curseforge/modrinth (orchestrator cog, management panel ui, integration api)
• discord token validation — validate bot token before container start (management panel endpoint + ui, orchestrator python util)
• config editor — in-browser yaml/json config editor with syntax highlighting (management panel component, backend endpoints)
• mysql database per click — instant mysql container provisioning (orchestrator cog, management panel ui + api)
• java version selector — switch between java 8/11/17/21 per server (management panel form + presets)
• 2fa (totp) — two-factor authentication via totp (integration service auth, management panel setup ui, settings)
• git deployment webhook — auto-deploy on github push (orchestrator cog + webhook server, management panel ui, discord notification)
• cronjob scheduler — scheduled tasks (restart/command/backup) via cron expressions (orchestrator cog, management panel ui + api)
• real-time resource graphs — live cpu/memory/disk gauges + sparklines, netdata/grafana integration (management panel component + backend metrics)
• log search — full-text log search with filters, pagination, highlighting (management panel livelogs upgrade, integration service search api)
• prepaid billing — pay-as-you-go balance system with top-ups, cost calculator, transaction history (orchestrator cog, management panel page + api)
• ai log anomaly detector — ml-based anomaly detection on container logs (integration service module)
• ai resource optimizer — trend analysis, right-sizing recommendations, idle detection (orchestrator cog)
• ai assistant chatbot — natural-language server management interface (integration service)
• ai threat detection — behavioral analysis of processes, logins, network traffic (orchestrator cog)
• ai backup validator — ephemeral restore + integrity checks + validation scoring (integration service)
• ai config advisor — config analysis against 50+ best-practice rules (management panel component)
• ai code review bot — github pr review with security scanning, discord summary (discord service module)
• ai performance profiler — minecraft tick profiling, lag source identification (service core)
• ai ticket triage — ticket classification, urgency scoring, auto-routing (integration service)
• ai capacity forecaster — 30/60/90 day resource prediction (orchestrator cog)
• infra pilot cli — `ipilot` cli tool with server management, logs, deploy (new `cli/` directory)
• terraform provider — `terraform-provider-infrapilot` for iac (new `infra/terraform/` directory)
• webhook event bus — outgoing webhooks with retry, signing, templating (integration service)
• api gateway & rate limiting — central gateway with token bucket rate limiting (integration service)
• plugin marketplace — community plugin ecosystem with one-click install (management panel)
• gitops sync — two-way git config sync with drift detection (orchestrator cog)
• opentelemetry export — otlp trace/metric/log export (integration service)
• graphql api — graphql layer alongside rest with subscriptions (integration service)
• kubernetes cluster manager — k3s/k8s cluster deploy + helm management (orchestrator cog)
• multi-region failover — active-passive regions with dns failover (integration service)
• edge compute nodes — edge function/container deployment (orchestrator cog)
• serverless functions (faas) — knative/openfaas integration with auto-scaling (orchestrator cog)
• cdn & waf integration — one-click cloudflare/bunny cdn + waf rules (integration service)
• multi-cloud cost optimizer — cross-provider pricing comparison (orchestrator cog)
• disaster recovery orchestrator — dr plans, drills, rto/rpo tracking (orchestrator cog)
• service mesh integration — istio/linkerd mtls + canary deployments (integration service)
• collaborative terminal — multi-user terminal sessions via websocket (management panel)
• team workspaces — isolated workspaces with quotas + sharing (integration service)
• change approval workflow — 2nd-person approval for destructive actions (management panel)
• incident management — on-call schedules, escalation, post-mortems (integration service)
• runbook automation — yaml-based executable runbooks with rollback (orchestrator cog)
• internal knowledge base — markdown wiki linked to resources (management panel)
• team activity feed — unified chronological event stream (management panel)
• distributed tracing — jaeger/zipkin span collection + flamegraphs (integration service)
• custom dashboard builder — drag-and-drop grafana-like dashboards (management panel)
• sla / slo tracking — slo definitions, error budgets, burn rate alerts (integration service)
• synthetic monitoring — global probes: http, tcp, ping, ssl, dns (orchestrator cog)
• cost allocation & chargeback — resource tagging + per-team cost breakdown (integration service)
• alert fatigue reduction — dedup, correlation, suppression, digest mode (integration service)
• mobile app — react native/expo app with server mgmt, push notifications, edge/iot, green computing screens (new `mobile/` directory)
• desktop app — tauri native shell with system tray, offline mode, auto-updater (new `src-tauri/`)
• edge & iot — 10 features: edge device manager, iot data pipeline, edge function runtime, mesh network, ml inference, iot provisioning, lorawan gateway, edge cdn, digital twin, backup/restore (cogs in `services/orchestrator-agent/cogs/`, integration modules, CLI commands, management panel pages, mobile screens)
• green computing — 10 features: energy tracker, carbon dashboard, green scheduling, idle reclamation, efficiency scorecards, auto shutdown, hardware lifecycle, pue/dcim, provider ranking, co2 offset (cogs, integration modules, CLI commands, management panel pages, mobile screens)
• i18n / l10n — 11 locales, rtl support, crowdin integration (management panel)
• wcag 2.1 aa compliance — aria, keyboard nav, screen reader support (management panel)
• theme studio — visual theme builder with live preview + gallery (management panel)
• bulk operations manager — multi-select batch actions with rollback (management panel)
• compliance framework reports — soc 2, hipaa, pci-dss report generation (integration service)
• secrets management — hashicorp vault + fernet encryption + rotation (integration service)
• container image scanner — trivy/grype cve scanning with policy enforcement (orchestrator cog)
• siem export — audit log streaming to splunk/elk/datadog/syslog (integration service)
• gdpr & data retention — data lifecycle, right-to-erasure, consent management (integration service)
• v4 features — 100 neue features in 10 kategorien: hybrid cloud, platform engineering, finops, resiliency, data platform, aiops, compliance v4, customer experience, soc deep, emerging tech — implementiert über integration service, orchestrator cogs, management panel, CLI und mobile (54.592+ zeilen code)
• docker compose: `docker-compose.yml` startet den stack mit postgres, redis, orchestrator agent, integration service, discord service, management panel, service core (profil `minecraft`) und optionalem monitoring (profil `monitoring`) + CLI utility container (profil `cli`). alle services besitzen dockerfiles oder fertige upstream-images.

## quick start

### option 1: management panel lokal starten (empfohlen)

```bash
git clone https://github.com/DaaanielTV/infra-pilot.git
cd infra-pilot/services/management-panel
npm install
cat > .env.local <<'ENV'
VITE_API_URL=http://localhost:3001
VITE_SUPABASE_URL=http://localhost:54321
VITE_SUPABASE_ANON_KEY=test-anon-key
VITE_DEMO_FEATURE_ENABLED=false
ENV
npm run dev
```

danach öffnen:

• frontend: <http://localhost:5173>
• backend-api: <http://localhost:3001>
• health check: <http://localhost:3001/health>

weitere details: [management panel readme](services/management-panel/README.md) und [docker panel quick start](services/management-panel/README-DOCKER-PANEL.md).

### option 2: orchestrator agent lokal starten

```bash
git clone https://github.com/DaaanielTV/infra-pilot.git
cd infra-pilot/services/orchestrator-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python bot.py
```

weitere details: [orchestrator agent readme](services/orchestrator-agent/README.md).

### option 4: docker compose (vollständiger stack)

```bash
git clone https://github.com/DaaanielTV/infra-pilot.git
cd infra-pilot
cp .env.example .env  # oder nutze die bereits vorhandene .env
docker compose up -d --build
```

## Services

| Service | Stack | Purpose |
|---------|-------|---------|
| **management-panel** | React 19, Express, PostgreSQL | Web dashboard for container and server management |
| **orchestrator-agent** | Python (discord.py) | Server provisioning, health monitoring, automation |
| **discord-service** | Node.js (discord.js) | Discord bot for server creation and management |
| **integration-service** | Python (aiohttp) | Cross-service communication hub |
| **service-core** | Java (Paper/Bukkit) | Minecraft server plugin |

## Default ports

| Port | Service |
|------|---------|
| 5173 | Management Panel (Frontend) |
| 3001 | Management Panel (Backend) |
| 8500 | Orchestrator Agent |
| 9000 | Integration Service |
| 3002 | Discord Service |
| 5432 | PostgreSQL |
| 6379 | Redis |
| 9090 | Prometheus |
| 3000 | Grafana |

## Repository structure

```
.
├── services/
│   ├── management-panel/     # React + Express dashboard
│   ├── orchestrator-agent/   # Python provisioning agent
│   ├── discord-service/      # Discord bot
│   ├── integration-service/  # Cross-platform hub
│   └── service-core/         # Minecraft plugin (Java)
├── cli/                      # Python CLI tool (ipilot)
├── mobile/                   # React Native (Expo) mobile app
├── infra/                    # Provider-neutral naming, Terraform
├── infrastructure/           # Monitoring configs (Prometheus, Grafana)
├── tests/                    # Unit, integration, and smoke tests
├── docs/                     # Architecture and development docs
├── wiki/                     # User-facing documentation
└── scripts/                  # Build, test, and setup helpers
```

## Requirements

- Docker and Docker Compose (for stack deployment)
- Node.js 18+ (management panel, discord service)
- Python 3.9+ (orchestrator agent, integration service)
- Java/Maven (service core)

## License

MIT
