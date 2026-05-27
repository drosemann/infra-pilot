# contest for the new owner of infra-pilot: the first person which contributes 250.000 lines worth of ai generated code, gets the ownership of this repository.

# infra pilot

infrastructure-orchestration und docker-management für self-hosting, demo-umgebungen und provider-neutrale provisioning-flows.

infra pilot bündelt mehrere services und hilfsbibliotheken, um container-/game-server-verwaltung, discord-gesteuerte provisionierung, provider-neutrale testdaten und ein modernes management-panel in einem repository zu entwickeln.

orchestrate. automate. scale.

## inhaltsverzeichnis

• [aktueller projektstatus](#aktueller-projektstatus)
• [quick start](#quick-start)
• [repository-struktur](#repository-struktur)
• [services](#services)
• [konfiguration](#konfiguration)
• [development & testing](#development--testing)
• [docker & deployment](#docker--deployment)
• [dokumentation](#dokumentation)
• [security](#security)
• [contributing](#contributing)
• [license & warranty](#license--warranty)

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
• mobile app — react native/expo app with server mgmt, push notifications (new `mobile/` directory)
• desktop app — tauri native shell with system tray, offline mode, auto-updater (new `src-tauri/`)
• i18n / l10n — 11 locales, rtl support, crowdin integration (management panel)
• wcag 2.1 aa compliance — aria, keyboard nav, screen reader support (management panel)
• theme studio — visual theme builder with live preview + gallery (management panel)
• bulk operations manager — multi-select batch actions with rollback (management panel)
• compliance framework reports — soc 2, hipaa, pci-dss report generation (integration service)
• secrets management — hashicorp vault + fernet encryption + rotation (integration service)
• container image scanner — trivy/grype cve scanning with policy enforcement (orchestrator cog)
• siem export — audit log streaming to splunk/elk/datadog/syslog (integration service)
• gdpr & data retention — data lifecycle, right-to-erasure, consent management (integration service)
• docker compose: `docker-compose.yml` ist als stack-scaffold vorhanden. aktuell besitzt nur `services/orchestrator-agent/` ein dockerfile; die compose-definitionen für management panel, discord service, service core und monitoring benötigen vor einem vollständigen stack-start noch dockerfiles bzw. infrastrukturdateien.

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

### option 3: discord service prüfen

```bash
git clone https://github.com/DaaanielTV/infra-pilot.git
cd infra-pilot/services/discord-service
npm install
cp .env.example .env
# .env mit discord- und pterodactyl-werten befüllen
node --check index.js
```

weitere details: [discord service readme](services/discord-service/README.md).

## voraussetzungen

| bereich | voraussetzung |
| --- | --- |
| allgemein | git, bash-kompatible shell |
| management panel | node.js 18+, npm |
| orchestrator agent | python 3.9+, pip, optional pytest |
| discord service | node.js 18+, npm, discord-bot, pterodactyl-api-zugang |
| service core | java/maven, sofern `services/service-core` genutzt oder erweitert wird |
| optional | docker, docker compose, zig 0.16.0+ und zero-native cli für die native desktop-shell |

## repository-struktur

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

## services

### management panel (`services/management-panel/`)

modernes docker-management-panel für self-hoster und hosting-workflows.

• stack: react 19, typescript, vite, tailwind css, express.js, supabase/postgresql, websocket (ws).
• modi: personal mode als standard, business mode für kunden-, plan- und demo-datenflüsse.
• features: app-/container-crud, logs, ressourcenlimits, setup-flow, seed demo feature gate, optionale zero-native desktop-shell.
• dashboards/seiten: dashboard, appdetail, appform, monitoring, accesslogs, backups, reports, settings, auditlog, customers, billing, configeditor, cronjobmanager, databasemanager, gitdeploymanager, realtimemetrics, modpackbrowser, twofactorsetup, marketplace, dashboardbuilder, knowledgebase, themestudio, collaborativeterminal.
• real-time: websocket-server für live-container-logs (`docker logs -f`) und metrik-streaming (`docker stats`, 2s-intervall). live-cpu/memory/disk-gauges mit sparklines und netdata/grafana-integration.
• globale suche: cmd+k-palette mit echtzeit-suche über apps, backups und audit-logs.
• audit trail: append-only-log aller mutationen mit timeline-viewer und filterung.
• benachrichtigungen: verwaltung von email-/webhook-/telegram-kanälen mit testversand.
• web terminal: in-browser-container-shell via websocket + docker exec.
• pwa: installierbare app mit service worker und offline-caching.
• onboarding: geführte 5-schritt-tour nach ersteinrichtung.
• theme persistenz: dark/light-mode wird in localstorage gespeichert.
• mobile-responsive: hamburger-menü und slide-in-sidebar.
• config editor: yaml/json-editor mit syntax-highlighting im browser (codemirror-basiert).
• java version selector: auswahl zwischen java 8/11/17/21 pro server über ui-formular.
• mysql database per click: ein-klick-provisionsierung von mysql-containern über ui + api.
• git deployment webhook: auto-deploy bei github-push mit webhook-server und discord-benachrichtigung.
• cronjob scheduler: geplante tasks (restart/command/backup) über cron-ausdrücke.
• real-time resource graphs: live-cpu/memory/disk-gauges mit sparklines, netdata/grafana-integration.
• log search: volltext-logsuche mit filtern, paginierung und highlighting.
• prepaid billing: pay-as-you-go-guthabensystem mit aufladungen, kostenrechner und transaktionshistorie.
• discord token validation: bot-token-validierung vor container-start.
• modpack-installer: ein-klick-modpack-installation von curseforge/modrinth.
• 2fa (totp): zwei-faktor-authentifizierung über totp mit setup-ui und backup-codes.
• ai config advisor: server-konfigurationsanalyse mit 50+ best-practice-regeln und ein-klick-fix.
• plugin marketplace: community-plugin-ökosystem mit suchen, installieren und veröffentlichen.
• collaborative terminal: multi-user-terminal-sessions via websocket mit chat und cursor-sharing.
• change approval workflow: genehmigungspflicht für destruktive aktionen mit break-glass-notfallmodus.
• knowledge base: markdown-basiertes wiki mit ressourcenverknüpften artikeln und volltextsuche.
• activity feed: chronologischer, filterbarer event-stream aller team-aktionen.
• dashboard builder: drag-and-drop-grafana-ähnlicher dashboard-editor mit multiplen panel-typen.
• i18n / l10n: vollständige internationalisierung mit 11 sprachen, rtl-support und crowdin-integration.
• wcag 2.1 aa: screenreader-support, tastaturnavigation, focus-management und aria-labels.
• theme studio: visueller theme-builder mit live-vorschau, export/import und community-galerie.
• bulk operations manager: batch-aktionen mit mehrfachauswahl, fortschrittsanzeige und rollback.
• desktop app: tauri-basierte native desktop-app mit system tray, offline-modus und auto-updater.
• wichtige skripte:
  • `npm run dev` startet frontend und backend parallel.
  • `npm run dev:frontend` startet nur vite.
  • `npm run dev:backend` startet nur die express-api.
  • `npm run test`, `npm run test:unit`, `npm run test:api` führen node-test-suites aus.
  • `npm run lint` führt den typescript-check aus.

### orchestrator agent (`services/orchestrator-agent/`)

python-basierte provisioning- und orchestrierungslogik.

• stack: python 3.9+, discord.py/aiohttp-umfeld laut requirements.
• features: vps-management, billing-/pricing-cogs, ressourcenmonitoring, integration hooks, ai/ml-optimierung, gitops, container-scanning, synthetisches monitoring.
• cogs (47): ai_capacity_forecaster, ai_resource_optimizer, ai_threat_detection, alert_manager, auto_scaling, backup_manager, benchmark, bot_commands, cleanup, clone_system, container_scanner, cost_optimizer, cost_prediction, cron_scheduler, database_manager, disaster_recovery, dns_manager, edge_compute, faas_manager, git_deploy, gitops_sync, health_checks, kubernetes_manager, load_balancer, modpack_installer, monitoring, multi_cloud_cost, network_monitor, performance_optimizer, prepaid_billing, quota_manager, recovery, resource_manager, runbook_automation, security_audit, server_migration, snapshot_system, ssl_manager, synthetic_monitoring, template_manager, traffic_analysis, troubleshoot, update_manager, vps_billing, vps_commands, vps_pricing.
• einstiegspunkt: `main.py` lädt alle 47 cogs. `bot.py` und `b2.py` sind legacy-dateien (deprecated), die nur noch als referenz dienen.
• docker: enthält aktuell ein dockerfile und ist damit der einzige service, der im repository direkt als image gebaut werden kann.

### discord service (`services/discord-service/`)

discord.js-service für pterodactyl-nahe server-erstellungsflüsse.

• stack: node.js 18+, commonjs, discord.js/axios/dotenv (package.json jetzt vorhanden).
• features: `/server create`-flow, pterodactyl-user-/server-erstellung, rollen-/limit-konfiguration.
• module (29, alle verdrahtet): activitytracker, advancedticketsystem, categorymanager, channelcleanup, codereviewbot, customcommands, dashboard, economycommands, eventscheduler, messagearchive, messagefilter, messagelogger, messagescheduler, pollcreator, prefixsettings, rolehierarchy, rolemanager, serverstatus, statscommands, statsgraphs, tempvoicechannels, ticketcommands, ticketsystem, topicrotation, verificationlevels, verificationsystem, voicemanager, warningsystem, welcomemessages.
• token validation: bot-token-validierungs-utility prüft `discord_token` vor service-start.
• git deployment notification: empfängt und leitet git-deployment-benachrichtigungen vom orchestrator weiter.
• konfiguration: siehe `services/discord-service/.env.example`.

### integration service (`services/integration-service/`)

python-basierter cross-plattform-hub für serviceübergreifende kommunikation.

• stack: python 3.9+, aiohttp.
• module (36): alerts, alert_fatigue, announcements, api, api_gateway, auth, auth_2fa, backup, backup_validator, cdn_waf, commands, compliance_reports, cost_allocation, distributed_tracing, events, gdpr_manager, graphql_api, incident_manager, integration, log_analyzer, logging, messaging, multi_region, opentelemetry_exporter, permissions, resource_tracker, secrets_manager, service_mesh, siem_exporter, slo_tracker, ticket_triage, webhook_bus, workspaces
• 2fa/totp: vollständiger totp-authentifizierungs-flow (setup, verify, disable, backup-codes).
• modpack search: curseforge/modrinth-suche und -details über einheitliche api.
• log search: erweiterte volltext-logsuche mit paginierung und filterung.
• notification providers: email (smtp mit tls), webhook (http post mit konfigurierbaren headern), telegram (bot api) – alle über einen zentralen `notificationmanager` orchestriert.
• aufgabe: zentraler nerv des gesamtsystems – verbindet discord-bot, minecraft-plugin, orchestrator und management panel über eine einheitliche api.

### service core (`services/service-core/`)

java/maven-minecraft-plugin mit vollständigem feature-set.

• stack: java, maven, paper/bukkit-api, playerserverplugin als entry point.
• feature-module: economy (currencyexchangemanager, marketmanager, shoptaxmanager), statistics (achievementsmanager, playerstatistics, statisticscommand), worlds (bordermanager, resourceworldmanager, worldcommands), gameplay (deathpenaltymanager, playertimeweathermanager, playtimerewardsmanager, resourcemultipliermanager), items (customcraftingmanager, customitemmanager), server (anticheatmanager, commandcooldownmanager, maintenancemanager, permissionmanager, resourcelimitsmanager, vipperksmanager), community (referralmanager, voterewardsmanager), plus inactivityshutdowntask und pluginmessagelistener.

## provider-neutrales token-system

provider-spezifische identitäten werden über neutrale tokens abstrahiert. das erleichtert tests, demos und providerwechsel.

```yaml
# infra/naming/provider_map.yaml
PROVIDER_MOCK: mock-provider
AWS_EC2: aws
GCP_COMPUTE: gcp
REGION_MOCK_US_EAST: mock-us-east
SKU_MOCK_SMALL: mock-small
```

beispiel in python:

```python
from infra.naming.resolver import resolve_token

provider = resolve_token("PROVIDER_MOCK")  # "mock-provider"
```

weitere informationen: [provider neutral mapping](docs/testing/provider_neutral_mapping.md).

## konfiguration

### root-konfiguration

• `.env.example` enthält eine repo-weite vorlage für datenbank-, redis-, discord-, orchestrator- und frontend-variablen.
• für lokale secrets immer `.env` oder service-spezifische `.env.local`-dateien nutzen und niemals echte zugangsdaten committen.

### management panel

minimalwerte für lokale entwicklung:

```env
VITE_API_URL=http://localhost:3001
VITE_SUPABASE_URL=http://localhost:54321
VITE_SUPABASE_ANON_KEY=test-anon-key
VITE_DEMO_FEATURE_ENABLED=false
```

`VITE_DEMO_FEATURE_ENABLED=true` zeigt demo-seeding-funktionen in der ui an. für produktionsähnliche umgebungen sollte der wert `false` bleiben.

### discord service

die benötigten variablen sind in [services/discord-service/.env.example](services/discord-service/.env.example) dokumentiert, insbesondere:

• `discord_token`
• `pterodactyl_api_url`
• `pterodactyl_api_key`
• channel-, rollen-, egg- und location-ids

## development & testing

### häufige befehle

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

### testdokumentation

• [testing overview](docs/TESTING.md)
• [running tests](docs/testing/running_tests.md)
• [automated test suite](docs/testing/automated-test-suite.md)
• [test plan](docs/testing/test_plan.md)
• [ci demo gate](docs/CI_DEMO_GATE.md)

### code- und workflow-dokumentation

• [development workflow](docs/development/development-workflow.md)
• [code standards](docs/development/code-standards.md)
• [ci architecture](docs/development/ci-architecture.md)
• [ai assistant playbook](docs/development/ai-assistant-playbook.md)

## docker & deployment

### aktueller stand

• `scripts/docker-build.sh` überspringt services ohne dockerfile automatisch.
• aktuell besitzt `services/orchestrator-agent/` ein dockerfile.
• `docker-compose.yml` beschreibt den ziel-stack mit postgresql, redis, service core, orchestrator, discord service, management panel und optionalem monitoring, ist aber ohne zusätzliche dockerfiles/monitoring-konfiguration noch nicht als vollständiger ein-befehl-stack nutzbar.

### aktuell sinnvoller docker-befehl

```bash
./scripts/docker-build.sh
```

der befehl baut vorhandene service-images und meldet fehlende dockerfiles als warnung.

### deployment-dokumentation

• [deployment guide](docs/operations/deployment-guide.md)
• [workflow optimization audit](docs/operations/workflow-optimization-audit.md)
• [local development setup](docs/setup/local-development.md)
• [zero-native management panel](docs/desktop/zero-native-management-panel.md)

## dokumentation

der zentrale dokumentationsindex liegt unter [docs/README.md](docs/README.md).

### wichtige einstiege

• [quickstart](docs/quickstart.md)
• [architecture overview](docs/architecture/overview.md)
• [orchestrator agent architecture](docs/architecture/orchestrator-agent.md)
• [management panel readme](services/management-panel/README.md)
• [discord service readme](services/discord-service/README.md)
• [integration service readme](services/integration-service/README.md)
• [branding guidelines](docs/branding-guidelines.md)
• [design system](docs/design-system.md)
• [design tokens](docs/design-tokens.md)
• [feature implementation plan v2](docs/feature-implementation-plan-v2.md) (50 neue features: ai, developer ecosystem, advanced infra, collaboration, observability, ux, compliance)
• [cli readme](cli/README.md) (infra pilot cli - `ipilot`)
• [terraform provider docs](infra/terraform/docs/index.md) (terraform provider for infra pilot)
• [mobile app](mobile/app.json) (react native/expo mobile app)

## security

• sicherheitsmeldungen bitte gemäß [security.md](SECURITY.md) einreichen.
• produktive umgebungen sollten echte secrets ausschließlich über geeignete secret stores oder deployment-variablen bereitstellen.
• demo-seeding (`VITE_DEMO_FEATURE_ENABLED`) in produktionsähnlichen umgebungen deaktiviert lassen.
• vor produktiver nutzung dockerfiles, compose-/monitoring-dateien, authentifizierung, tls, backups und berechtigungen gezielt härten.

## contributing

beiträge sind willkommen. bitte vorab lesen:

• [contributing.md](CONTRIBUTING.md)
• [docs/contributing.md](docs/CONTRIBUTING.md)
• [code standards](docs/development/code-standards.md)
• [code of conduct](CODE_OF_CONDUCT.md)

kurzablauf:

```bash
git checkout -b feature/my-feature
# Änderungen vornehmen und testen
git commit -m "feat: describe change"
git push origin feature/my-feature
```

## license & warranty

### license

dieses projekt ist unter der mit license lizenziert. details stehen in [license](LICENSE).

### warranty & liability

diese software wird ohne gewährleistung bereitgestellt.

• die mit license enthält den vollständigen haftungsausschluss.
• testen sie änderungen gründlich, bevor sie infra pilot in produktionsnahen umgebungen einsetzen.
• betreiber sind selbst dafür verantwortlich, secrets, provider-zugänge, discord-bots, datenbanken und deployments sicher zu konfigurieren.

[zurück nach oben](#infra-pilot)
