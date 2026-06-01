# infra pilot

infrastructure-orchestration und docker-management für self-hosting, demo-umgebungen und provider-neutrale provisioning-flows.

infra pilot bündelt mehrere services und hilfsbibliotheken, um container-/game-server-verwaltung, discord-gesteuerte provisionierung, provider-neutrale testdaten und ein modernes management-panel in einem repository zu entwickeln.

orchestrate. automate. scale.

## inhaltsverzeichnis

• [aktueller projektstatus](#aktueller-projektstatus)
• [quick start](#quick-start)
• [repository-struktur](#repository-struktur)
• [services](#services)
• [v3 feature overview — 100 neue features](#v3-feature-overview--100-neue-features)
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
• docker compose: `docker-compose.yml` startet den stack mit postgres, redis, service core, orchestrator, integration service, discord service, management panel und optionalem monitoring.

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
├── docker-compose.yml                # Compose-Stack für alle lokalen/kleinen Deployments
├── infra/naming/                     # Provider-neutrale Token-Auflösung
├── docker-compose.yml                # Compose-Scaffold für den späteren Stack-Ausbau
├── cli/ipilot/                       # Python CLI Tool (server, deploy, logs, edge, green, networking +)
├── infra/                            # Provider-neutrale Token-Auflösung + Terraform Provider + Edge/Green Helpers
├── mobile/                           # React Native (Expo) App (server mgmt, push, edge/iot, green screens)
├── scripts/                          # Setup-, Test-, Coverage- und Build-Hilfen
├── services/
│   ├── management-panel/             # React/Vite + Express Docker Panel (100+ Pages, v3 Features)
│   ├── orchestrator-agent/           # Python Provisioning-/Discord-Agent (67+ Cogs)
│   ├── discord-service/              # Discord.js Bot Service (29+ Module, Report Bot)
│   ├── integration-service/          # Cross-Plattform-Hub (60+ Module: Auth, Edge, Green, Network, Market, Storage, Gaming, Identity, Automation, Viz, Integration)
│   └── service-core/                 # Java/Maven Minecraft-Plugin (economy, worlds, stats, items, gameplay, server, community)
├── tests/                            # Repo-weite Unit-/Integration-/Smoke-Tests (identity, automation, integration, orchestrator, discord, management-panel, mobile, cli)
└── docs/                             # Projekt-, Architektur-, Testing- und Operations-Doku (features-v3/ mit 100 feature-specs)
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
• docker: besitzt ein eigenes dockerfile und wird im compose-stack als orchestrator-service gebaut.
• cogs (67+): ai_capacity_forecaster, ai_resource_optimizer, ai_threat_detection, alert_manager, auto_scaling, backup_manager, benchmark, bot_commands, cleanup, clone_system, container_scanner, cost_optimizer, cost_prediction, cron_scheduler, database_manager, disaster_recovery, dns_manager, edge_compute, faas_manager, git_deploy, gitops_sync, health_checks, kubernetes_manager, load_balancer, modpack_installer, monitoring, multi_cloud_cost, network_monitor, performance_optimizer, prepaid_billing, quota_manager, recovery, resource_manager, runbook_automation, security_audit, server_migration, snapshot_system, ssl_manager, synthetic_monitoring, template_manager, traffic_analysis, troubleshoot, update_manager, vps_billing, vps_commands, vps_pricing
• **v3 edge/iot/green cogs**: edge_device_manager, edge_function_runtime, edge_ml_inference, iot_device_provisioning, edge_cdn, edge_backup_restore, green_scheduling, idle_resource_reclamation, auto_shutdown_policies
• **v3 networking/marketplace cogs**: sdwan_controller, vpn_service, dns_manager, bgp_manager, reverse_proxy, segmentation, packet_capture, dns_filtering, cost_analyzer, cellular_manager, resource_trading, app_marketplace, pay_per_use, reseller, sla_manager, crypto_gateway, plan_builder, recommendations, tax_automation, loyalty
• **v3 identity/automation cogs**: identity_provider, webauthn, session_manager, pam_manager, policy_engine, compliance_scanner, workflow_studio, ansible_salt_integration, infrastructure_pipelines, drift_detector, quota_manager, auto_remediation, maintenance_planner, runbook_library, chaos_engineering, self_healing
• einstiegspunkt: `main.py` lädt alle cogs. `bot.py` und `b2.py` sind legacy-dateien (deprecated).
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
• module (60+): alerts, alert_fatigue, announcements, api, api_gateway, auth, auth_2fa, backup, backup_validator, cdn_waf, commands, compliance_reports, cost_allocation, distributed_tracing, events, gdpr_manager, graphql_api, incident_manager, integration, log_analyzer, logging, messaging, multi_region, opentelemetry_exporter, permissions, resource_tracker, secrets_manager, service_mesh, siem_exporter, slo_tracker, ticket_triage, webhook_bus, workspaces
• **v3 edge/iot**: energy_consumption_tracker, hardware_lifecycle_tracker, pue_dcim_integration, co2_offset_integration, mesh_network_manager, lorawan_gateway_manager, iot_data_pipeline
• **v3 networking**: sdwan_controller, vpn_service, dns_manager, bgp_manager, reverse_proxy, segmentation, packet_capture, dns_filtering, cost_analyzer, cellular_manager
• **v3 marketplace**: resource_trading, app_marketplace, pay_per_use, reseller, sla_manager, crypto_gateway, plan_builder, recommendations, tax_automation, loyalty
• **v3 storage**: distributed_storage, object_storage_gateway, backup_chain_visualizer, storage_tiering, file_sharing, db_replication, data_migration, dedup_compression, immutable_backup, data_catalog
• **v3 gaming**: anti_cheat, tournament_manager, matchmaking, voice_provisioning, live_spectate, mod_publishing, server_rental, cross_play
• **v3 identity/automation**: identity_provider_ext, webauthn_ext, session_manager_ext, pam_manager_ext, policy_engine_ext, compliance_scanner_ext, workflow_studio_ext, ansible_salt_integration_ext, infrastructure_pipelines_ext, drift_detector_ext, quota_manager_ext, auto_remediation_ext, maintenance_planner_ext, runbook_library_ext, chaos_engineering_ext, self_healing_ext
• **v3 viz/integration**: anomaly_detection, resource_forecasting, executive_summary, pubsub_event_bus, integration_marketplace, low_code_connectors, email_infrastructure, sms_voice_notifications, calendar_sync, vcs_integration, jira_linear_sync, identity_federation, ipaas_integration
• 2fa/totp: vollständiger totp-authentifizierungs-flow (setup, verify, disable, backup-codes).
• modpack search: curseforge/modrinth-suche und -details über einheitliche api.
• log search: erweiterte volltext-logsuche mit paginierung und filterung.
• notification providers: email (smtp mit tls), webhook (http post mit konfigurierbaren headern), telegram (bot api) – alle über einen zentralen `notificationmanager` orchestriert.
• aufgabe: zentraler nerv des gesamtsystems – verbindet discord-bot, minecraft-plugin, orchestrator und management panel über eine einheitliche api.

### service core (`services/service-core/`)

java/maven-minecraft-plugin mit vollständigem feature-set.

• stack: java, maven, paper/bukkit-api, playerserverplugin als entry point.
• feature-module: economy (currencyexchangemanager, marketmanager, shoptaxmanager), statistics (achievementsmanager, playerstatistics, statisticscommand), worlds (bordermanager, resourceworldmanager, worldcommands), gameplay (deathpenaltymanager, playertimeweathermanager, playtimerewardsmanager, resourcemultipliermanager), items (customcraftingmanager, customitemmanager), server (anticheatmanager, commandcooldownmanager, maintenancemanager, permissionmanager, resourcelimitsmanager, vipperksmanager), community (referralmanager, voterewardsmanager), plus inactivityshutdowntask und pluginmessagelistener.

## v3 feature overview — 100 neue features

der [v3 feature plan](docs/feature-implementation-plan-v3.md) umfasst 100 neue features in 10 kategorien —
realisiert durch 5 parallele implementations-agenten (224.553+ zeilen code, 1.106+ dateien).

### 1. edge & iot computing (features 1-10)
- **1 — edge device manager**: raspberry pi/jetson nano/rockpi als edge-nodes registrieren, überwachen, fernsteuern. ota-firmware-updates, health-pings, geolocation-tagging. `edge_device_manager.py`
- **2 — iot data pipeline**: mqtt/coap/http-sensordaten erfassen, transformieren, filtern und routen. rule-engine für schwellwert-alarme. `iot_data_pipeline.py`
- **3 — edge function runtime**: lightweight wasm/lua/js-runtime für edge-nodes. offline-first mit lokaler queue. `edge_function_runtime.py`
- **4 — mesh network manager**: wireguard/tinc-mesh-vpn über edge-nodes. automatisches routing, peer-discovery, verschlüsselte tunnels. `mesh_network_manager.py`
- **5 — edge ml inference**: tflite/onnx-modelle auf edge-nodes deployen. kamerabild-analyse, vibrationsüberwachung, predictive maintenance. `edge_ml_inference.py`
- **6 — iot device provisioning**: zero-touch-geräte-onboarding. claim-codes, zertifikatsenrollment, device-shadow-state. `iot_device_provisioning.py`
- **7 — lorawan gateway management**: lorawan-gateways und -concentratoren verwalten. packet-forwarder-konfiguration, channel-planung. `lorawan_gateway_manager.py`
- **8 — edge cdn**: verteiltes content-caching an edge-nodes. pull-through-cache für container/images. `edge_cdn.py`
- **9 — digital twin viewer**: 3d-visualisierung von edge-geräten mit echtzeit-telemetrie (three.js). `DigitalTwinViewer.tsx`
- **10 — edge backup & restore**: periodisches backup des edge-device-zustands (config, daten, ml-modelle). full/incremental. `edge_backup_restore.py`

vollständige specs: [`docs/features-v3/edge-iot/`](docs/features-v3/edge-iot/)

### 2. sustainable & green computing (features 11-20)
- **11 — energy consumption tracker**: pro-container-energieverbrauch via rapl/intel-pcm oder schätzung aus cpu/ram/disk. `energy_consumption_tracker.py`
- **12 — carbon footprint dashboard**: co2-emissionsanzeige mit historischen trends, grid-carbon-intensity-api. `CarbonDashboard.tsx`
- **13 — green scheduling**: workloads (backups, batch-jobs) zeitlich so planen, dass sie bei niedrigster netz-co2-intensität laufen. `green_scheduling.py`
- **14 — idle resource reclamation**: zombie-container, ungenutzte volumes, orphaned networks erkennen und automatisch bereinigen. `idle_resource_reclamation.py`
- **15 — efficiency scorecards**: pro-server-effizienz-rating (auslastung vs. kapazität) gamifiziert als "green score". `EfficiencyScorecards.tsx`
- **16 — auto-shutdown policies**: auto-stop von dev/staging-umgebungen außerhalb der geschäftszeiten. `auto_shutdown_policies.py`
- **17 — hardware lifecycle tracker**: server-hardware-alter, garantie, e-waste-status verfolgen. alerts bei überfälligem austausch. `hardware_lifecycle_tracker.py`
- **18 — pue/dcim integration**: datacenter-infrastructure-management für power-usage-effectiveness. `pue_dcim_integration.py`
- **19 — sustainable provider ranking**: cloud-provider nach co2-intensität, wasserverbrauch, erneuerbaren prozenten ranken. `SustainableProviderRanking.tsx`
- **20 — co2 offset integration**: ein-klick-kauf von carbon-offsets via patch/climate-tech-api. `co2_offset_integration.py`

vollständige specs: [`docs/features-v3/green-computing/`](docs/features-v3/green-computing/)

### 3. advanced networking & connectivity (features 21-30)
- **21 — sd-wan controller**: mehrere uplinks managen, traffic-steering, failover-policies, pro-app-qos. `sdwan_controller.py`
- **22 — vpn as a service**: ein-klick-wireguard/openvpn-server-deployment, client-config, qr-code für mobil. `vpn_service.py`
- **23 — dns management console**: vollständiger dns-zonen-editor (a/aaaa/cname/mx/txt), dnssec, ddns. `dns_manager.py`
- **24 — bgp route manager**: bgp-sessions, prefix-announcements, as-path-prepend, community-tagging. `bgp_manager.py`
- **25 — reverse proxy catalog**: zentrales reverse-proxy-management (nginx/caddy/traefik). auto-ssl, upstream-health-checks. `reverse_proxy.py`
- **26 — network segmentation designer**: drag-and-drop-vlan/subnet-designer. firewall-regel-generierung aus topologie. `segmentation.py`
- **27 — packet capture studio**: web-basiertes tcpdump/wireshark: capture starten, live-streamen, display-filter. `packet_capture.py`
- **28 — dns filtering / dhcp server**: pi-hole/adguard-home-integration. dns-basiertes content-filtering, dhcp-server. `dns_filtering.py`
- **29 — network cost analyzer**: bandwidth-kosten pro provider/region/server tracken. egress-cost-alerts. `cost_analyzer.py`
- **30 — 5g/lte integration**: zellulare modems managen, apn-config, signal-monitoring, data-usage-caps. `cellular_manager.py`

vollständige specs: [`docs/features-v3/networking/`](docs/features-v3/networking/)

### 4. marketplace, commerce & monetization (features 31-40)
- **31 — resource trading platform**: p2p-marktplatz für ungenutzte cpu/ram/storage. smart-contract-escrow. `resource_trading.py`
- **32 — one-click app marketplace**: kuratierter marktplatz mit 100+ apps (wordpress, nextcloud, minecraft). `app_marketplace.py`
- **33 — pay-per-use billing**: sekundengenaue abrechnung. stripe/metronome-integration. `pay_per_use.py`
- **34 — reseller / white-label**: reseller-portal mit eigener domain, branded-panel, sub-admin-accounts. `reseller.py`
- **35 — sla management & credits**: sla-definitionen, uptime-tracking, automatische credit-berechnung. `sla_manager.py`
- **36 — crypto payment gateway**: bitcoin/ethereum/solana/usdc-zahlungen akzeptieren. `crypto_gateway.py`
- **37 — subscription plan builder**: admin-tool für eigene tarife: ressourcen-stufen, feature-flags, addons. `plan_builder.py`
- **38 — usage-based recommendations**: nutzungsmuster analysieren, optimalen tarif vorschlagen. `recommendations.py`
- **39 — invoice & tax automation**: automatisierte steuerberechnung (vat/gst/sales tax). xrechnung/zugferd. `tax_automation.py`
- **40 — loyalty & reward system**: punkte für referral, uptime, frühzeitige zahlung. badges, rewards. `loyalty.py`

vollständige specs: [`docs/features-v3/marketplace/`](docs/features-v3/marketplace/)

### 5. advanced storage & data management (features 41-50)
- **41 — distributed storage cluster**: minio/ceph/glusterfs-cluster deployen und managen. erasure-coding, s3-kompatible-api. `distributed_storage.py`
- **42 — object storage gateway**: s3-gateway mit bucket-policies, lifecycle-rules, versioning. `object_storage_gateway.py`
- **43 — backup chain visualizer**: visueller backup-chain-baum (full + incremental + differential). restore-point-auswahl. `backup_chain_visualizer.py`
- **44 — storage tiering policies**: auto-move zwischen hot/warm/cold-tiers basierend auf access-frequenz. `storage_tiering.py`
- **45 — file sharing & sync**: nextcloud/owncloud/seafile-integration. share-links mit ablauf, passwortschutz. `file_sharing.py`
- **46 — database replication manager**: ein-klick-master-slave/multi-master-replication für mysql/postgres. `db_replication.py`
- **47 — data migration wizard**: geführte migration zwischen storage-backends. rsync/rclone mit fortschritt. `data_migration.py`
- **48 — deduplication & compression**: inline-dedup (zstd/btrfs/zfs) für container-volumes. `dedup_compression.py`
- **49 — immutable backup vault**: worm-storage, object-lock, retention-policies, air-gapped-recovery. `immutable_backup.py`
- **50 — data catalog & lineage**: automatisiertes data-discovery, schema-detection, lineage-tracking. `data_catalog.py`

vollständige specs: [`docs/features-v3/advanced-storage/`](docs/features-v3/advanced-storage/)

### 6. gaming & esports platform (features 51-60)
- **51 — anti-cheat integration**: sentinel/eac-integration. cheat-detection-log-analyse, automatisierte bans. `anti_cheat.py`
- **52 — tournament manager**: bracket-generation (single/double/swiss/round-robin), match-scheduling, server-allokation. `tournament_manager.py`
- **53 — matchmaking service**: elo/mmr-matchmaking, party-system, region-preference, skill-based-balancing. `matchmaking.py`
- **54 — voice server provisioning**: ein-klick-teamspeak3/mumble/sonic-voice-server. slot-management. `voice_provisioning.py`
- **55 — live spectate / obs integration**: obs-studio-plugin für auto-scene-switching. spectator-slots. `live_spectate.py`
- **56 — game analytics dashboard**: spieler-metriken: aktive spieler, session-dauer, peak-concurrency, heatmaps. `GameAnalytics.tsx`
- **57 — mod/modpack publishing**: mods hochladen, versionieren, verteilen. abhängigkeitsgraph, curseforge-sync. `mod_publishing.py`
- **58 — server rental marketplace**: stündliche/tägliche game-server-miete für events. instant-provisioning. `server_rental.py`
- **59 — cross-play proxy**: geyser/bedrock-parity-proxy zwischen java/bedrock-editionen. player-sync. `cross_play.py`
- **60 — game server dashboard**: live-status aller game-server: spieler, tps, memory, uptime. `GameServerDashboard.tsx`

vollständige specs: [`docs/features-v3/gaming-esports/`](docs/features-v3/gaming-esports/)

### 7. identity, authentication & compliance (features 61-70)
- **61 — sso / oidc provider**: built-in-oidc/saml-identity-provider. azure-ad/okta/google-workspace-integration. `identity_provider_ext.py`
- **62 — passkey / webauthn auth**: passwortlose auth via fingerprint, face id, yubikey, windows hello. `webauthn_ext.py`
- **63 — session manager**: aktive sessions anzeigen/widerrufen. device-fingerprint, geolocation, risk-scoring. `session_manager_ext.py`
- **64 — privileged access management**: just-in-time-elevated-access. approval-workflows, session-recording, break-glass. `pam_manager_ext.py`
- **65 — policy as code**: opa/rego-inspirierte policy-engine mit 8 built-in policies. git-versioniert, dry-run. `policy_engine_ext.py`
- **66 — compliance scanner**: multi-benchmark-scanner (cis/nist/bsi/soc2). per-check-severity-scoring, remediation. `compliance_scanner_ext.py`
- **67 — audit trail analytics**: ml-anomalie-detektion auf audit-logs (z-score, iqr). trendanalyse, anomali-timeline.
- **68 — data classification engine**: pii/phi/pci-auto-klassifizierung via regex-muster. risk-scoring, data-inventory.
- **69 — vendor risk assessment**: vendor-registrierung mit sig/caiq-fragebögen. risk-scoring über 10 kategorien.
- **70 — breach notification workflow**: gdpr-breach-notification mit 72h-tracking, aufsichtsbehördlicher meldung.

vollständige specs: [`docs/features-v3/`](docs/features-v3/) (61–70)

### 8. automation & orchestration deep (features 71-80)
- **71 — workflow studio**: visueller drag-and-drop-workflow-builder mit 30+ knotentypen. dag-ausführung, cycle-detection. `workflow_studio_ext.py`
- **72 — ansible/salt integration**: ansible-playbooks/salt-states ausführen. inventory-management, rollback. `ansible_salt_integration_ext.py`
- **73 — infrastructure pipelines**: ci/cd-pipelines für infrastructure-as-code. lint → plan → apply → validate. `infrastructure_pipelines_ext.py`
- **74 — configuration drift detector**: soll/ist-konfigurationsvergleich. snapshot-basiert, package-drift, file-integrity. `drift_detector_ext.py`
- **75 — resource quota management**: mehrdimensionale quotas (cpu/ram/storage/network/gpu) pro org/team/projekt. `quota_manager_ext.py`
- **76 — event-driven auto-remediation**: regel-basierte auto-remediation. modi: automatic/semi/manual/advisory. `auto_remediation_ext.py`
- **77 — maintenance scheduler**: kalender-basierte maintenance-windows. konflikterkennung, genehmigungs-workflows. `maintenance_planner_ext.py`
- **78 — runbook template library**: ausführbare runbook-vorlagen. kategorien: incident/deployment/security/backup. `runbook_library_ext.py`
- **79 — chaos engineering framework**: fault-injection-experimente mit 15+ fault-typen. blast-radius-control. `chaos_engineering_ext.py`
- **80 — self-healing infrastructure**: ml-gestützte auto-remediation (prophet). health-monitoring, recovery-aktionen. `self_healing_ext.py`

vollständige specs: [`docs/features-v3/`](docs/features-v3/) (71–80)

### 9. visualization, reporting & bi (features 81-90)
- **81 — 3d infrastructure topology**: three.js-3d-karte aller infrastruktur. server, container, netzwerk-links, regionen. `Topology3D.tsx`
- **82 — custom report builder**: drag-and-drop-report-designer. widget-palette, scheduling, delivery (email/slack/webhook). `CustomReportBuilder.tsx`
- **83 — bi dashboard**: mrr/arr/ltv/cac/churn-kpi-cards, revenue-trends, cohort-retention, revenue-forecast. `BIDashboard.tsx`
- **84 — time-series anomaly detection**: automatisierte anomalie-detektion auf metrik-zeitreihen (z-score, mad, iqr, cusum). `anomaly_detection.py`
- **85 — resource forecasting engine**: prophet/arima-basierte kapazitätsprognose. what-if-szenarien. `resource_forecasting.py`
- **86 — dependency graph viewer**: force-directed-graph der service-abhängigkeiten. impact-analyse, png-export. `DependencyGraphViewer.tsx`
- **87 — cost & usage analytics**: pro-service-cost-breakdown, unit-economics, budget-gauge-rings, savings-empfehlungen. `CostAnalytics.tsx`
- **88 — executive summary generator**: auto-generierte weekly/monthly-summaries. markdown/html-output, scheduling. `executive_summary.py`
- **89 — geolocation heatmap**: canvas-weltkarte mit heatmap-overlay. city-drill-down, region/provider/date-filters. `GeolocationHeatmap.tsx`
- **90 — slack/discord report bot**: geplante report-delivery zu chat-kanälen. 6 report-typen, cron-scheduling. `reportBot.js`

vollständige specs: [`docs/features-v3/`](docs/features-v3/) (81–90)

### 10. integration ecosystem (features 91-100)
- **91 — pub/sub event bus**: multi-tenant-event-bus mit topics, subscriptions, replay. cloud-events-spec. `pubsub_event_bus.py`
- **92 — integration marketplace**: community-integrationen (github, jira, pagerduty, datadog, sentry). ein-klick-install. `integration_marketplace.py`
- **93 — low-code connector builder**: visueller api-connector-builder. http-request, transform, conditional, auth-nodes. `low_code_connectors.py`
- **94 — email as infrastructure**: smtp-relay, inbound-email-parsing (sendgrid/ses), template-rendering (jinja2). `email_infrastructure.py`
- **95 — sms/voice notification**: twilio/plivo-integration. sms + voice-calls, escalation-chains, cost-tracking. `sms_voice_notifications.py`
- **96 — calendar & scheduling sync**: ical/caldav-event-management. maintenance-windows, rrule-recurrence. `calendar_sync.py`
- **97 — github/gitlab app**: deployment-status-checks, commit-status, pr-comments, app-token-generation. `vcs_integration.py`
- **98 — jira/linear integration**: bidirektionaler ticket-sync mit status/field-mappings. webhook-handling. `jira_linear_sync.py`
- **99 — external identity federation**: ldap/ad/azure-ad/okta/saml/oidc/scim-provider. group-sync, role-mapping. `identity_federation.py`
- **100 — ipaas integration**: 14 trigger-typen, 12 action-typen, openapi-spec-generation, webhook-signing. `ipaas_integration.py`

vollständige specs: [`docs/features-v3/`](docs/features-v3/) (91–100)

### implementation summary

alle 100 features wurden durch 5 parallele implementations-agenten realisiert:

| agent | kategorie | features | ergebnis |
|-------|-----------|----------|----------|
| agent 1 | edge & iot + green computing | 1-20 | 71.147 zeilen, 406 dateien |
| agent 2 | networking + marketplace | 21-40 | vollständig mit cogs, routes, panel-pages |
| agent 3 | storage + gaming/esports | 41-60 | 57.973 zeilen, 244 dateien |
| agent 4 | identity/auth + automation | 61-80 | vollständig mit tests, docs, erweiterungen |
| agent 5 | visualization/bi + integration | 81-100 | vollständig mit panel, service, discord-modulen |

**gesamtergebnis**: 1.106+ dateien, 224.553+ zeilen code, 100 feature-specs in `docs/features-v3/`

jedes feature umfasst:
- **integration service module** — python-manager-klassen mit CRUD, JSON-persistenz, API-endpoints
- **orchestrator agent cog** — discord.py-slash-commands mit embeds, permissions
- **management panel page** — react/typescript-ui mit shadcn/ui, tailwind
- **cli commands** — argparse-befehle in `cli/ipilot/cli.py`
- **mobile endpoints** — expo-kompatible api-endpoints in `mobile/src/api/endpoints.ts`
- **tests** — pytest-unit/-integration-tests
- **dokumentation** — feature-specifikation in `docs/features-v3/`

der vollständige feature-plan inklusive aufwandsabschätzung und phasenplan: [`docs/feature-implementation-plan-v3.md`](docs/feature-implementation-plan-v3.md)

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

• `docker-compose.yml` beschreibt den stack mit postgresql, redis, service core, orchestrator, integration service, discord service, management panel und optionalem monitoring.
• alle compose-services besitzen dockerfiles oder fertige upstream images.
• prometheus und grafana laufen über das optionale `monitoring` profile.

### stack starten

```bash
docker compose up -d --build
```

mit monitoring:

```bash
docker compose --profile monitoring up -d --build
```

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

### edge & iot architecture

• [edge-iot architecture](docs/architecture/edge-iot-architecture.md) — edge device manager, iot data pipeline, edge function runtime, mesh network, ml inference, iot provisioning, lorawan gateway, edge cdn, digital twin, backup/restore
• [edge device manager cog](services/orchestrator-agent/cogs/edge_device_manager.py) (10 features: device mgmt, ota, config, monitoring, auth, commands, telemetry, policies, remote, analytics)
• [iot data pipeline](services/integration-service/src/iot_data_pipeline.py) (mqtt ingestion, protocol translation, stream routing)
• [edge function runtime](services/orchestrator-agent/cogs/edge_function_runtime.py) (wasm/lua/js runtime, deployment, scaling)
• [mesh network manager](services/integration-service/src/mesh_network_manager.py) (ospf/batman routing, topology)
• [edge ml inference](services/orchestrator-agent/cogs/edge_ml_inference.py) (tflite/onnx model deployment)
• [iot device provisioning](services/orchestrator-agent/cogs/iot_device_provisioning.py) (claim codes, certificates, shadows)
• [lorawan gateway](services/integration-service/src/lorawan_gateway_manager.py) (lorawan gateway/device mgmt)
• [edge cdn](services/orchestrator-agent/cogs/edge_cdn.py) (cache policies, origin shields, invalidation)
• [edge backup & restore](services/orchestrator-agent/cogs/edge_backup_restore.py) (full/incremental backup, restore, snapshots)
• [digital twin viewer](services/management-panel/src/pages/EdgeIoT/DigitalTwinViewer.tsx) (real-time device state visualization)

### green computing architecture

• [green computing architecture](docs/architecture/green-computing-architecture.md) — energy tracking, carbon dashboard, green scheduling, idle reclamation, efficiency scores, auto shutdown, hardware lifecycle, pue/dcim, provider ranking, co2 offset
• [energy consumption tracker](services/integration-service/src/energy_consumption_tracker.py) (real-time power monitoring)
• [carbon dashboard](services/management-panel/src/pages/GreenComputing/CarbonDashboard.tsx) (co2 visualization)
• [green scheduling](services/orchestrator-agent/cogs/green_scheduling.py) (carbon-aware job scheduling)
• [idle resource reclamation](services/orchestrator-agent/cogs/idle_resource_reclamation.py) (reclaim underutilized resources)
• [efficiency scorecards](services/management-panel/src/pages/GreenComputing/EfficiencyScorecards.tsx) (facility efficiency scoring)
• [auto shutdown policies](services/orchestrator-agent/cogs/auto_shutdown_policies.py) (time/idle-based auto shutdown)
• [hardware lifecycle tracker](services/integration-service/src/hardware_lifecycle_tracker.py) (asset lifecycle management)
• [pue/dcim integration](services/integration-service/src/pue_dcim_integration.py) (power usage effectiveness)
• [sustainable provider ranking](services/management-panel/src/pages/GreenComputing/SustainableProviderRanking.tsx) (provider sustainability scores)
• [co2 offset integration](services/integration-service/src/co2_offset_integration.py) (carbon offset purchasing)

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
