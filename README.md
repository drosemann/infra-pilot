# Contest for the new owner of infra-pilot: The first person which contributes 250.000 lines worth of ai generated code, gets the ownership of this repository.

# 🚀 Infra Pilot

**Infrastructure-Orchestration und Docker-Management für Self-Hosting, Demo-Umgebungen und Provider-neutrale Provisioning-Flows.**

Infra Pilot bündelt mehrere Services und Hilfsbibliotheken, um Container-/Game-Server-Verwaltung, Discord-gesteuerte Provisionierung, Provider-neutrale Testdaten und ein modernes Management-Panel in einem Repository zu entwickeln.

> **Orchestrate. Automate. Scale.**

## Inhaltsverzeichnis

- [Aktueller Projektstatus](#aktueller-projektstatus)
- [Quick Start](#quick-start)
- [Repository-Struktur](#repository-struktur)
- [Services](#services)
- [Konfiguration](#konfiguration)
- [Development & Testing](#development--testing)
- [Docker & Deployment](#docker--deployment)
- [Dokumentation](#dokumentation)
- [Security](#security)
- [Contributing](#contributing)
- [License & Warranty](#license--warranty)

## Aktueller Projektstatus

- ✅ **Management Panel:** React/Vite-Frontend mit Express-API, Personal Mode, optionalem Business Mode, Supabase/PostgreSQL-Anbindung und Seed-Demo-Feature-Gate.
- ✅ **Orchestrator Agent:** Python-Service mit Discord-/VPS-Provisioning-Komponenten, Provider-neutraler Namensauflösung und eigenen Tests.
- ✅ **Discord Service:** Node.js/Discord.js-Integration für Pterodactyl-/Provisioning-Flows. Alle 28 Module sind eingebunden und verdrahtet.
- ✅ **Provider-neutrales Test-Framework:** Token-Mapping unter `infra/naming/` und Tests unter `tests/`.
- ✅ **Real-Time WebSocket:** Live Container-Logs und Metrik-Streaming via WebSocket-Server im Management Panel.
- ✅ **Audit Trail:** Append-Only-Audit-Log für alle Mutationen (Apps, Backups, Alerts, Config) mit Timeline-Viewer.
- ✅ **Globale Suche:** Cmd+K-Palette durchsucht Apps, Backups und Audit-Logs via PostgreSQL ILIKE.
- ✅ **Notification Channels:** Verwaltung mehrerer Benachrichtigungskanäle (Email, Webhook, Telegram) mit integrierten Providern.
- ✅ **PWA Support:** Manifest + Service Worker für installierbare Desktop-App und Offline-Caching.
- ✅ **Onboarding Wizard:** 5-schrittige geführte Tour nach der Ersteinrichtung.
- ✅ **Mobile-Responsive Layout:** Hamburger-Menü, Slide-In-Sidebar für Mobilgeräte.
- ✅ **Web Terminal:** In-Browser-Container-Terminal via WebSocket + Docker exec.
- ✅ **Modpack-Installer** — One-click modpack install from CurseForge/Modrinth (Orchestrator cog, Management Panel UI, Integration API)
- ✅ **Discord Token Validation** — Validate bot token before container start (Management Panel endpoint + UI, Orchestrator Python util)
- ✅ **Config Editor** — In-browser YAML/JSON config editor with syntax highlighting (Management Panel component, backend endpoints)
- ✅ **MySQL Database per Click** — Instant MySQL container provisioning (Orchestrator cog, Management Panel UI + API)
- ✅ **Java Version Selector** — Switch between Java 8/11/17/21 per server (Management Panel form + presets)
- ✅ **2FA (TOTP)** — Two-factor authentication via TOTP (Integration Service auth, Management Panel setup UI, Settings)
- ✅ **Git Deployment Webhook** — Auto-deploy on GitHub push (Orchestrator cog + webhook server, Management Panel UI, Discord notification)
- ✅ **Cronjob Scheduler** — Scheduled tasks (restart/command/backup) via cron expressions (Orchestrator cog, Management Panel UI + API)
- ✅ **Real-time Resource Graphs** — Live CPU/memory/disk gauges + sparklines, Netdata/Grafana integration (Management Panel component + backend metrics)
- ✅ **Log Search** — Full-text log search with filters, pagination, highlighting (Management Panel LiveLogs upgrade, Integration Service search API)
- ✅ **Prepaid Billing** — Pay-as-you-go balance system with top-ups, cost calculator, transaction history (Orchestrator cog, Management Panel page + API)
- ✅ **AI Log Anomaly Detector** — ML-based anomaly detection on container logs (Integration Service module)
- ✅ **AI Resource Optimizer** — Trend analysis, right-sizing recommendations, idle detection (Orchestrator cog)
- ✅ **AI Assistant Chatbot** — Natural-language server management interface (Integration Service)
- ✅ **AI Threat Detection** — Behavioral analysis of processes, logins, network traffic (Orchestrator cog)
- ✅ **AI Backup Validator** — Ephemeral restore + integrity checks + validation scoring (Integration Service)
- ✅ **AI Config Advisor** — Config analysis against 50+ best-practice rules (Management Panel component)
- ✅ **AI Code Review Bot** — GitHub PR review with security scanning, Discord summary (Discord Service module)
- ✅ **AI Performance Profiler** — Minecraft tick profiling, lag source identification (Service Core)
- ✅ **AI Ticket Triage** — Ticket classification, urgency scoring, auto-routing (Integration Service)
- ✅ **AI Capacity Forecaster** — 30/60/90 day resource prediction (Orchestrator cog)
- ✅ **Infra Pilot CLI** — `ipilot` CLI tool with server management, logs, deploy (new `cli/` directory)
- ✅ **Terraform Provider** — `terraform-provider-infrapilot` for IaC (new `infra/terraform/` directory)
- ✅ **Webhook Event Bus** — Outgoing webhooks with retry, signing, templating (Integration Service)
- ✅ **API Gateway & Rate Limiting** — Central gateway with token bucket rate limiting (Integration Service)
- ✅ **Plugin Marketplace** — Community plugin ecosystem with one-click install (Management Panel)
- ✅ **GitOps Sync** — Two-way Git config sync with drift detection (Orchestrator cog)
- ✅ **OpenTelemetry Export** — OTLP trace/metric/log export (Integration Service)
- ✅ **GraphQL API** — GraphQL layer alongside REST with subscriptions (Integration Service)
- ✅ **Kubernetes Cluster Manager** — K3s/K8s cluster deploy + Helm management (Orchestrator cog)
- ✅ **Multi-Region Failover** — Active-passive regions with DNS failover (Integration Service)
- ✅ **Edge Compute Nodes** — Edge function/container deployment (Orchestrator cog)
- ✅ **Serverless Functions (FaaS)** — Knative/OpenFaaS integration with auto-scaling (Orchestrator cog)
- ✅ **CDN & WAF Integration** — One-click Cloudflare/Bunny CDN + WAF rules (Integration Service)
- ✅ **Multi-Cloud Cost Optimizer** — Cross-provider pricing comparison (Orchestrator cog)
- ✅ **Disaster Recovery Orchestrator** — DR plans, drills, RTO/RPO tracking (Orchestrator cog)
- ✅ **Service Mesh Integration** — Istio/Linkerd mTLS + canary deployments (Integration Service)
- ✅ **Collaborative Terminal** — Multi-user terminal sessions via WebSocket (Management Panel)
- ✅ **Team Workspaces** — Isolated workspaces with quotas + sharing (Integration Service)
- ✅ **Change Approval Workflow** — 2nd-person approval for destructive actions (Management Panel)
- ✅ **Incident Management** — On-call schedules, escalation, post-mortems (Integration Service)
- ✅ **Runbook Automation** — YAML-based executable runbooks with rollback (Orchestrator cog)
- ✅ **Internal Knowledge Base** — Markdown wiki linked to resources (Management Panel)
- ✅ **Team Activity Feed** — Unified chronological event stream (Management Panel)
- ✅ **Distributed Tracing** — Jaeger/Zipkin span collection + flamegraphs (Integration Service)
- ✅ **Custom Dashboard Builder** — Drag-and-drop Grafana-like dashboards (Management Panel)
- ✅ **SLA / SLO Tracking** — SLO definitions, error budgets, burn rate alerts (Integration Service)
- ✅ **Synthetic Monitoring** — Global probes: HTTP, TCP, ping, SSL, DNS (Orchestrator cog)
- ✅ **Cost Allocation & Chargeback** — Resource tagging + per-team cost breakdown (Integration Service)
- ✅ **Alert Fatigue Reduction** — Dedup, correlation, suppression, digest mode (Integration Service)
- ✅ **Mobile App** — React Native/Expo app with server mgmt, push notifications (new `mobile/` directory)
- ✅ **Desktop App** — Tauri native shell with system tray, offline mode, auto-updater (new `src-tauri/`)
- ✅ **i18n / l10n** — 11 locales, RTL support, Crowdin integration (Management Panel)
- ✅ **WCAG 2.1 AA Compliance** — ARIA, keyboard nav, screen reader support (Management Panel)
- ✅ **Theme Studio** — Visual theme builder with live preview + gallery (Management Panel)
- ✅ **Bulk Operations Manager** — Multi-select batch actions with rollback (Management Panel)
- ✅ **Compliance Framework Reports** — SOC 2, HIPAA, PCI-DSS report generation (Integration Service)
- ✅ **Secrets Management** — HashiCorp Vault + Fernet encryption + rotation (Integration Service)
- ✅ **Container Image Scanner** — Trivy/Grype CVE scanning with policy enforcement (Orchestrator cog)
- ✅ **SIEM Export** — Audit log streaming to Splunk/ELK/Datadog/syslog (Integration Service)
- ✅ **GDPR & Data Retention** — Data lifecycle, right-to-erasure, consent management (Integration Service)
- ⚠️ **Docker Compose:** `docker-compose.yml` ist als Stack-Scaffold vorhanden. Aktuell besitzt nur `services/orchestrator-agent/` ein Dockerfile; die Compose-Definitionen für Management Panel, Discord Service, Service Core und Monitoring benötigen vor einem vollständigen Stack-Start noch Dockerfiles bzw. Infrastrukturdateien.

## Quick Start

### Option 1: Management Panel lokal starten (empfohlen)

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

Danach öffnen:

- Frontend: <http://localhost:5173>
- Backend-API: <http://localhost:3001>
- Health Check: <http://localhost:3001/health>

Weitere Details: [Management Panel README](services/management-panel/README.md) und [Docker Panel Quick Start](services/management-panel/README-DOCKER-PANEL.md).

### Option 2: Orchestrator Agent lokal starten

```bash
git clone https://github.com/DaaanielTV/infra-pilot.git
cd infra-pilot/services/orchestrator-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python bot.py
```

Weitere Details: [Orchestrator Agent README](services/orchestrator-agent/README.md).

### Option 3: Discord Service prüfen

```bash
git clone https://github.com/DaaanielTV/infra-pilot.git
cd infra-pilot/services/discord-service
npm install
cp .env.example .env
# .env mit Discord- und Pterodactyl-Werten befüllen
node --check index.js
```

Weitere Details: [Discord Service README](services/discord-service/README.md).

## Voraussetzungen

| Bereich | Voraussetzung |
| --- | --- |
| Allgemein | Git, Bash-kompatible Shell |
| Management Panel | Node.js 18+, npm |
| Orchestrator Agent | Python 3.9+, pip, optional pytest |
| Discord Service | Node.js 18+, npm, Discord-Bot, Pterodactyl-API-Zugang |
| Service Core | Java/Maven, sofern `services/service-core` genutzt oder erweitert wird |
| Optional | Docker, Docker Compose, Zig 0.16.0+ und zero-native CLI für die native Desktop-Shell |

## Repository-Struktur

```text
.
├── README.md                         # Hauptdokumentation
├── LICENSE                           # MIT License
├── docker-compose.yml                # Compose-Scaffold für den späteren Stack-Ausbau
├── infra/naming/                     # Provider-neutrale Token-Auflösung
├── scripts/                          # Setup-, Test-, Coverage- und Build-Hilfen
├── services/
│   ├── management-panel/             # React/Vite + Express Docker Panel (Pages: Monitoring, Backups, Reports, Settings, AccessLogs, Billing, …)
│   ├── orchestrator-agent/           # Python Provisioning-/Discord-Agent (35 Cogs: scaling, backup, health, security, DNS, SSL, database, deploy, cron, modpack, billing, …)
│   ├── discord-service/              # Discord.js Bot Service (20+ Module: tickets, polling, logging, moderation, token validation, …)
│   ├── integration-service/          # Cross-Plattform-Hub (Auth, 2FA/TOTP, Events, Messaging, Permissions, Users, Modpacks, Log Search, …)
│   └── service-core/                 # Java/Maven Minecraft-Plugin (Features: economy, worlds, stats, items, gameplay, server, community)
├── tests/                            # Repo-weite Unit-/Integration-/Smoke-Tests
└── docs/                             # Projekt-, Architektur-, Testing- und Operations-Doku
```

## Services

### Management Panel (`services/management-panel/`)

Modernes Docker-Management-Panel für Self-Hoster und Hosting-Workflows.

- **Stack:** React 19, TypeScript, Vite, Tailwind CSS, Express.js, Supabase/PostgreSQL, WebSocket (ws).
- **Modi:** Personal Mode als Standard, Business Mode für Kunden-, Plan- und Demo-Datenflüsse.
- **Features:** App-/Container-CRUD, Logs, Ressourcenlimits, Setup-Flow, Seed Demo Feature Gate, optionale zero-native Desktop-Shell.
- **Dashboards/Seiten:** Dashboard, AppDetail, AppForm, Monitoring, AccessLogs, Backups, Reports, Settings, **AuditLog**, Customers, **Billing**, **ConfigEditor**, **CronJobManager**, **DatabaseManager**, **GitDeployManager**, **RealtimeMetrics**, **ModpackBrowser**, **TwoFactorSetup**, **Marketplace**, **DashboardBuilder**, **KnowledgeBase**, **ThemeStudio**, **CollaborativeTerminal**.
- **Real-Time:** WebSocket-Server für Live-Container-Logs (`docker logs -f`) und Metrik-Streaming (`docker stats`, 2s-Intervall). Live-CPU/Memory/Disk-Gauges mit Sparklines und Netdata/Grafana-Integration.
- **Globale Suche:** Cmd+K-Palette mit Echtzeit-Suche über Apps, Backups und Audit-Logs.
- **Audit Trail:** Append-Only-Log aller Mutationen mit Timeline-Viewer und Filterung.
- **Benachrichtigungen:** Verwaltung von Email-/Webhook-/Telegram-Kanälen mit Testversand.
- **Web Terminal:** In-Browser-Container-Shell via WebSocket + Docker exec.
- **PWA:** Installierbare App mit Service Worker und Offline-Caching.
- **Onboarding:** Geführte 5-Schritt-Tour nach Ersteinrichtung.
- **Theme Persistenz:** Dark/Light-Mode wird in localStorage gespeichert.
- **Mobile-Responsive:** Hamburger-Menü und Slide-In-Sidebar.
- **Config Editor:** YAML/JSON-Editor mit Syntax-Highlighting im Browser (CodeMirror-basiert).
- **Java Version Selector:** Auswahl zwischen Java 8/11/17/21 pro Server über UI-Formular.
- **MySQL Database per Click:** Ein-Klick-Provisionsierung von MySQL-Containern über UI + API.
- **Git Deployment Webhook:** Auto-Deploy bei GitHub-Push mit Webhook-Server und Discord-Benachrichtigung.
- **Cronjob Scheduler:** Geplante Tasks (Restart/Command/Backup) über Cron-Ausdrücke.
- **Real-time Resource Graphs:** Live-CPU/Memory/Disk-Gauges mit Sparklines, Netdata/Grafana-Integration.
- **Log Search:** Volltext-Logsuche mit Filtern, Paginierung und Highlighting.
- **Prepaid Billing:** Pay-as-you-go-Guthabensystem mit Aufladungen, Kostenrechner und Transaktionshistorie.
- **Discord Token Validation:** Bot-Token-Validierung vor Container-Start.
- **Modpack-Installer:** Ein-Klick-Modpack-Installation von CurseForge/Modrinth.
- **2FA (TOTP):** Zwei-Faktor-Authentifizierung über TOTP mit Setup-UI und Backup-Codes.
- **AI Config Advisor:** Server-Konfigurationsanalyse mit 50+ Best-Practice-Regeln und Ein-Klick-Fix.
- **Plugin Marketplace:** Community-Plugin-Ökosystem mit Suchen, Installieren und Veröffentlichen.
- **Collaborative Terminal:** Multi-User-Terminal-Sessions via WebSocket mit Chat und Cursor-Sharing.
- **Change Approval Workflow:** Genehmigungspflicht für destruktive Aktionen mit Break-Glass-Notfallmodus.
- **Knowledge Base:** Markdown-basiertes Wiki mit ressourcenverknüpften Artikeln und Volltextsuche.
- **Activity Feed:** Chronologischer, filterbarer Event-Stream aller Team-Aktionen.
- **Dashboard Builder:** Drag-and-Drop-Grafana-ähnlicher Dashboard-Editor mit multiplen Panel-Typen.
- **i18n / l10n:** Vollständige Internationalisierung mit 11 Sprachen, RTL-Support und Crowdin-Integration.
- **WCAG 2.1 AA:** Screenreader-Support, Tastaturnavigation, Focus-Management und ARIA-Labels.
- **Theme Studio:** Visueller Theme-Builder mit Live-Vorschau, Export/Import und Community-Galerie.
- **Bulk Operations Manager:** Batch-Aktionen mit Mehrfachauswahl, Fortschrittsanzeige und Rollback.
- **Desktop App:** Tauri-basierte native Desktop-App mit System Tray, Offline-Modus und Auto-Updater.
- **Wichtige Skripte:**
  - `npm run dev` startet Frontend und Backend parallel.
  - `npm run dev:frontend` startet nur Vite.
  - `npm run dev:backend` startet nur die Express-API.
  - `npm run test`, `npm run test:unit`, `npm run test:api` führen Node-Test-Suites aus.
  - `npm run lint` führt den TypeScript-Check aus.

### Orchestrator Agent (`services/orchestrator-agent/`)

Python-basierte Provisioning- und Orchestrierungslogik.

- **Stack:** Python 3.9+, Discord.py/aiohttp-Umfeld laut Requirements.
- **Features:** VPS-Management, Billing-/Pricing-Cogs, Ressourcenmonitoring, Integration Hooks, AI/ML-Optimierung, GitOps, Container-Scanning, Synthetisches Monitoring.
- **Cogs (47):** **ai_capacity_forecaster**, **ai_resource_optimizer**, **ai_threat_detection**, alert_manager, auto_scaling, backup_manager, benchmark, bot_commands, cleanup, clone_system, **container_scanner**, cost_optimizer, cost_prediction, **cron_scheduler**, **database_manager**, **disaster_recovery**, dns_manager, **edge_compute**, **faas_manager**, **git_deploy**, **gitops_sync**, health_checks, **kubernetes_manager**, load_balancer, **modpack_installer**, monitoring, **multi_cloud_cost**, network_monitor, performance_optimizer, **prepaid_billing**, quota_manager, recovery, resource_manager, **runbook_automation**, security_audit, server_migration, snapshot_system, ssl_manager, **synthetic_monitoring**, template_manager, traffic_analysis, troubleshoot, update_manager, vps_billing, vps_commands, vps_pricing.
- **Einstiegspunkt:** `main.py` lädt alle 47 Cogs. `bot.py` und `b2.py` sind Legacy-Dateien (deprecated), die nur noch als Referenz dienen.
- **Docker:** Enthält aktuell ein Dockerfile und ist damit der einzige Service, der im Repository direkt als Image gebaut werden kann.

### Discord Service (`services/discord-service/`)

Discord.js-Service für Pterodactyl-nahe Server-Erstellungsflüsse.

- **Stack:** Node.js 18+, CommonJS, Discord.js/Axios/Dotenv (package.json jetzt vorhanden).
- **Features:** `/server create`-Flow, Pterodactyl-User-/Server-Erstellung, Rollen-/Limit-Konfiguration.
- **Module (29, alle verdrahtet):** activityTracker, advancedTicketSystem, categoryManager, channelCleanup, **codeReviewBot**, customCommands, dashboard, economyCommands, eventScheduler, messageArchive, messageFilter, messageLogger, messageScheduler, pollCreator, prefixSettings, roleHierarchy, roleManager, serverStatus, statsCommands, statsGraphs, tempVoiceChannels, ticketCommands, ticketSystem, topicRotation, verificationLevels, verificationSystem, voiceManager, warningSystem, welcomeMessages.
- **Token Validation:** Bot-Token-Validierungs-Utility prüft `DISCORD_TOKEN` vor Service-Start.
- **Git Deployment Notification:** Empfängt und leitet Git-Deployment-Benachrichtigungen vom Orchestrator weiter.
- **Konfiguration:** siehe `services/discord-service/.env.example`.

### Integration Service (`services/integration-service/`)

Python-basierter Cross-Plattform-Hub für serviceübergreifende Kommunikation.

- **Stack:** Python 3.9+, aiohttp.
- **Module (36):** alerts, **alert_fatigue**, announcements, api, **api_gateway**, auth, **auth_2fa**, backup, **backup_validator**, **cdn_waf**, commands, **compliance_reports**, **cost_allocation**, **distributed_tracing**, events, **gdpr_manager**, **graphql_api**, **incident_manager**, integration, **log_analyzer**, logging, messaging, **multi_region**, **opentelemetry_exporter**, permissions, resource_tracker, **secrets_manager**, **service_mesh**, **siem_exporter**, **slo_tracker**, **ticket_triage**, **webhook_bus**, **workspaces**
- **2FA/TOTP:** Vollständiger TOTP-Authentifizierungs-Flow (Setup, Verify, Disable, Backup-Codes).
- **Modpack Search:** CurseForge/Modrinth-Suche und -Details über einheitliche API.
- **Log Search:** Erweiterte Volltext-Logsuche mit Paginierung und Filterung.
- **Notification Providers:** Email (SMTP mit TLS), Webhook (HTTP POST mit konfigurierbaren Headern), Telegram (Bot API) – alle über einen zentralen `NotificationManager` orchestriert.
- **Aufgabe:** Zentraler Nerv des Gesamtsystems – verbindet Discord-Bot, Minecraft-Plugin, Orchestrator und Management Panel über eine einheitliche API.

### Service Core (`services/service-core/`)

Java/Maven-Minecraft-Plugin mit vollständigem Feature-Set.

- **Stack:** Java, Maven, Paper/Bukkit-API, PlayerServerPlugin als Entry Point.
- **Feature-Module:** economy (CurrencyExchangeManager, MarketManager, ShopTaxManager), statistics (AchievementsManager, PlayerStatistics, StatisticsCommand), worlds (BorderManager, ResourceWorldManager, WorldCommands), gameplay (DeathPenaltyManager, PlayerTimeWeatherManager, PlaytimeRewardsManager, ResourceMultiplierManager), items (CustomCraftingManager, CustomItemManager), server (AntiCheatManager, CommandCooldownManager, MaintenanceManager, PermissionManager, ResourceLimitsManager, VIPPerksManager), community (ReferralManager, VoteRewardsManager), plus InactivityShutdownTask und PluginMessageListener.

## Provider-neutrales Token-System

Provider-spezifische Identitäten werden über neutrale Tokens abstrahiert. Das erleichtert Tests, Demos und Providerwechsel.

```yaml
# infra/naming/provider_map.yaml
PROVIDER_MOCK: mock-provider
AWS_EC2: aws
GCP_COMPUTE: gcp
REGION_MOCK_US_EAST: mock-us-east
SKU_MOCK_SMALL: mock-small
```

Beispiel in Python:

```python
from infra.naming.resolver import resolve_token

provider = resolve_token("PROVIDER_MOCK")  # "mock-provider"
```

Weitere Informationen: [Provider Neutral Mapping](docs/testing/provider_neutral_mapping.md).

## Konfiguration

### Root-Konfiguration

- `.env.example` enthält eine repo-weite Vorlage für Datenbank-, Redis-, Discord-, Orchestrator- und Frontend-Variablen.
- Für lokale Secrets immer `.env` oder service-spezifische `.env.local`-Dateien nutzen und niemals echte Zugangsdaten committen.

### Management Panel

Minimalwerte für lokale Entwicklung:

```env
VITE_API_URL=http://localhost:3001
VITE_SUPABASE_URL=http://localhost:54321
VITE_SUPABASE_ANON_KEY=test-anon-key
VITE_DEMO_FEATURE_ENABLED=false
```

`VITE_DEMO_FEATURE_ENABLED=true` zeigt Demo-Seeding-Funktionen in der UI an. Für produktionsähnliche Umgebungen sollte der Wert `false` bleiben.

### Discord Service

Die benötigten Variablen sind in [services/discord-service/.env.example](services/discord-service/.env.example) dokumentiert, insbesondere:

- `DISCORD_TOKEN`
- `PTERODACTYL_API_URL`
- `PTERODACTYL_API_KEY`
- Channel-, Rollen-, Egg- und Location-IDs

## Development & Testing

### Häufige Befehle

```bash
# Repo-weite Tests über Script
./scripts/test.sh

# Offline-Verifikation ohne Maven-Netzwerkannahmen
make verify-offline

# Python-Tests im Root-Kontext
pytest

# Management Panel
cd services/management-panel
npm run lint
npm run test

# Orchestrator Agent
cd services/orchestrator-agent
pytest tests/
```

### Testdokumentation

- [Testing Overview](docs/TESTING.md)
- [Running Tests](docs/testing/running_tests.md)
- [Automated Test Suite](docs/testing/automated-test-suite.md)
- [Test Plan](docs/testing/test_plan.md)
- [CI Demo Gate](docs/CI_DEMO_GATE.md)

### Code- und Workflow-Dokumentation

- [Development Workflow](docs/development/development-workflow.md)
- [Code Standards](docs/development/code-standards.md)
- [CI Architecture](docs/development/ci-architecture.md)
- [AI Assistant Playbook](docs/development/ai-assistant-playbook.md)

## Docker & Deployment

### Aktueller Stand

- `scripts/docker-build.sh` überspringt Services ohne Dockerfile automatisch.
- Aktuell besitzt `services/orchestrator-agent/` ein Dockerfile.
- `docker-compose.yml` beschreibt den Ziel-Stack mit PostgreSQL, Redis, Service Core, Orchestrator, Discord Service, Management Panel und optionalem Monitoring, ist aber ohne zusätzliche Dockerfiles/Monitoring-Konfiguration noch nicht als vollständiger Ein-Befehl-Stack nutzbar.

### Aktuell sinnvoller Docker-Befehl

```bash
./scripts/docker-build.sh
```

Der Befehl baut vorhandene Service-Images und meldet fehlende Dockerfiles als Warnung.

### Deployment-Dokumentation

- [Deployment Guide](docs/operations/deployment-guide.md)
- [Workflow Optimization Audit](docs/operations/workflow-optimization-audit.md)
- [Local Development Setup](docs/setup/local-development.md)
- [zero-native Management Panel](docs/desktop/zero-native-management-panel.md)

## Dokumentation

Der zentrale Dokumentationsindex liegt unter [docs/README.md](docs/README.md).

### Wichtige Einstiege

- [Quickstart](docs/quickstart.md)
- [Architecture Overview](docs/architecture/overview.md)
- [Orchestrator Agent Architecture](docs/architecture/orchestrator-agent.md)
- [Management Panel README](services/management-panel/README.md)
- [Discord Service README](services/discord-service/README.md)
- [Integration Service README](services/integration-service/README.md)
- [Branding Guidelines](docs/branding-guidelines.md)
- [Design System](docs/design-system.md)
- [Design Tokens](docs/design-tokens.md)
- [Feature Implementation Plan v2](docs/feature-implementation-plan-v2.md) (50 neue Features: AI, Developer Ecosystem, Advanced Infra, Collaboration, Observability, UX, Compliance)
- [CLI README](cli/README.md) (Infra Pilot CLI - `ipilot`)
- [Terraform Provider Docs](infra/terraform/docs/index.md) (Terraform Provider for Infra Pilot)
- [Mobile App](mobile/app.json) (React Native/Expo mobile app)

## Security

- Sicherheitsmeldungen bitte gemäß [SECURITY.md](SECURITY.md) einreichen.
- Produktive Umgebungen sollten echte Secrets ausschließlich über geeignete Secret Stores oder Deployment-Variablen bereitstellen.
- Demo-Seeding (`VITE_DEMO_FEATURE_ENABLED`) in produktionsähnlichen Umgebungen deaktiviert lassen.
- Vor produktiver Nutzung Dockerfiles, Compose-/Monitoring-Dateien, Authentifizierung, TLS, Backups und Berechtigungen gezielt härten.

## Contributing

Beiträge sind willkommen. Bitte vorab lesen:

- [CONTRIBUTING.md](CONTRIBUTING.md)
- [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)
- [Code Standards](docs/development/code-standards.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)

Kurzablauf:

```bash
git checkout -b feature/my-feature
# Änderungen vornehmen und testen
git commit -m "feat: describe change"
git push origin feature/my-feature
```

## License & Warranty

### License

Dieses Projekt ist unter der **MIT License** lizenziert. Details stehen in [LICENSE](LICENSE).

### Warranty & Liability

⚠️ Diese Software wird ohne Gewährleistung bereitgestellt.

- Die MIT License enthält den vollständigen Haftungsausschluss.
- Testen Sie Änderungen gründlich, bevor Sie Infra Pilot in produktionsnahen Umgebungen einsetzen.
- Betreiber sind selbst dafür verantwortlich, Secrets, Provider-Zugänge, Discord-Bots, Datenbanken und Deployments sicher zu konfigurieren.

---

**[⬆ Zurück nach oben](#-infra-pilot)**
