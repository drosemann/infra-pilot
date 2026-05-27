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
- ⚠️ **Docker Compose:** `docker-compose.yml` ist als Stack-Scaffold vorhanden. Aktuell besitzt nur `services/orchestrator-agent/` ein Dockerfile; die Compose-Definitionen für Management Panel, Discord Service, Service Core und Monitoring benötigen vor einem vollständigen Stack-Start noch Dockerfiles bzw. Infrastrukturdateien.
- ⚠️ **Kubernetes/Terraform:** Die README verweist nicht mehr auf produktionsfertige K8s-/Terraform-Manifeste, weil entsprechende `infrastructure/`-Dateien derzeit nicht im Repository enthalten sind.

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
- **Dashboards/Seiten:** Dashboard, AppDetail, AppForm, Monitoring, AccessLogs, Backups, Reports, Settings, **AuditLog**, Customers, **Billing**, **ConfigEditor**, **CronJobManager**, **DatabaseManager**, **GitDeployManager**, **RealtimeMetrics**, **ModpackBrowser**, **TwoFactorSetup**.
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
- **Wichtige Skripte:**
  - `npm run dev` startet Frontend und Backend parallel.
  - `npm run dev:frontend` startet nur Vite.
  - `npm run dev:backend` startet nur die Express-API.
  - `npm run test`, `npm run test:unit`, `npm run test:api` führen Node-Test-Suites aus.
  - `npm run lint` führt den TypeScript-Check aus.

### Orchestrator Agent (`services/orchestrator-agent/`)

Python-basierte Provisioning- und Orchestrierungslogik.

- **Stack:** Python 3.9+, Discord.py/aiohttp-Umfeld laut Requirements.
- **Features:** VPS-Management, Billing-/Pricing-Cogs, Ressourcenmonitoring, Integration Hooks.
- **Cogs (35):** alert_manager, auto_scaling, backup_manager, benchmark, bot_commands, cleanup, clone_system, cost_optimizer, cost_prediction, **cron_scheduler**, **database_manager**, dns_manager, **git_deploy**, health_checks, load_balancer, **modpack_installer**, monitoring, network_monitor, performance_optimizer, **prepaid_billing**, quota_manager, recovery, resource_manager, security_audit, server_migration, snapshot_system, ssl_manager, template_manager, traffic_analysis, troubleshoot, update_manager, vps_billing, vps_commands, vps_pricing.
- **Einstiegspunkt:** `main.py` lädt alle 35 Cogs. `bot.py` und `b2.py` sind Legacy-Dateien (deprecated), die nur noch als Referenz dienen.
- **Docker:** Enthält aktuell ein Dockerfile und ist damit der einzige Service, der im Repository direkt als Image gebaut werden kann.

### Discord Service (`services/discord-service/`)

Discord.js-Service für Pterodactyl-nahe Server-Erstellungsflüsse.

- **Stack:** Node.js 18+, CommonJS, Discord.js/Axios/Dotenv (package.json jetzt vorhanden).
- **Features:** `/server create`-Flow, Pterodactyl-User-/Server-Erstellung, Rollen-/Limit-Konfiguration.
- **Module (28, alle verdrahtet):** activityTracker, advancedTicketSystem, categoryManager, channelCleanup, customCommands, dashboard, economyCommands, eventScheduler, messageArchive, messageFilter, messageLogger, messageScheduler, pollCreator, prefixSettings, roleHierarchy, roleManager, serverStatus, statsCommands, statsGraphs, tempVoiceChannels, ticketCommands, ticketSystem, topicRotation, verificationLevels, verificationSystem, voiceManager, warningSystem, welcomeMessages.
- **Token Validation:** Bot-Token-Validierungs-Utility prüft `DISCORD_TOKEN` vor Service-Start.
- **Git Deployment Notification:** Empfängt und leitet Git-Deployment-Benachrichtigungen vom Orchestrator weiter.
- **Konfiguration:** siehe `services/discord-service/.env.example`.

### Integration Service (`services/integration-service/`)

Python-basierter Cross-Plattform-Hub für serviceübergreifende Kommunikation.

- **Stack:** Python 3.9+, aiohttp.
- **Module:** alerts, announcements, api, auth, **auth_2fa**, backup, commands, events, integration, logging, messaging, **modpacks**, **notification_providers**, permissions, resource_tracker, users.
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
