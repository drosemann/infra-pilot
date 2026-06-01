# documentation index

willkommen in der infra-pilot-dokumentation. dieser index listet bewusst nur dokumente, die aktuell im repository vorhanden sind.

## schnellstart

- [quickstart](quickstart.md)
- [local development setup](setup/local-development.md)
- [management panel readme](../services/management-panel/README.md)
- [docker panel quick start](../services/management-panel/README-DOCKER-PANEL.md)
- [zero-native management panel shell](desktop/zero-native-management-panel.md)

## architektur

- [system overview](architecture/overview.md)
- [orchestrator agent](architecture/orchestrator-agent.md)
- [implementation plan](implementation-plan.md)
- [feature implementation plan v2](feature-implementation-plan-v2.md) (50 neue features: ai, developer ecosystem, advanced infra, collaboration, observability, ux, compliance)
- [feature implementation plan v3](feature-implementation-plan-v3.md) (100 neue features: edge/iot, green computing, networking, marketplace, storage, gaming, identity, automation, visualization/bi, integration ecosystem)

## development & ci

- [development workflow](development/development-workflow.md)
- [code standards](development/code-standards.md)
- [ci architecture](development/ci-architecture.md)
- [ai assistant playbook](development/ai-assistant-playbook.md)
- [contributing](../CONTRIBUTING.md)
- [docs contributing](CONTRIBUTING.md)

## testing

- [testing overview](TESTING.md)
- [testing guidelines](testing-guidelines.md)
- [running tests](testing/running_tests.md)
- [automated test suite](testing/automated-test-suite.md)
- [test plan](testing/test_plan.md)
- [provider neutral mapping](testing/provider_neutral_mapping.md)
- [ci demo gate](CI_DEMO_GATE.md)

## operations

- [deployment guide](operations/deployment-guide.md)
- [workflow optimization audit](operations/workflow-optimization-audit.md)

hinweis: `docker-compose.yml` ist der reference path für kleine deployments. der stack enthält alle services; prometheus und grafana laufen optional über das `monitoring` profile.

## branding & design

- [branding](branding.md)
- [branding guidelines](branding-guidelines.md)
- [design system](design-system.md)
- [design tokens](design-tokens.md)
- [repository branding](../branding/branding.md)

## service-dokumentation

- [management panel](../services/management-panel/README.md)
- [management panel architecture](../services/management-panel/docs/ARCHITECTURE.md)
- [management panel database setup](../services/management-panel/docs/DATABASE_SETUP.md)
- [management panel personal mode](../services/management-panel/docs/PERSONAL_MODE.md)
- [discord service](../services/discord-service/README.md)
- [orchestrator agent](../services/orchestrator-agent/README.md)
- [integration service](../services/integration-service/README.md)
- [service core](../services/service-core/README.md) (minecraft-plugin mit feature-modulen: economy, worlds, statistics, gameplay, items, server, community)
- [implementation plan](implementation-plan.md) (phasenplan für ~120 features)

## feature plan v3 — 100 neue features (edge, green, networking, marketplace, storage, gaming, identity, automation, visualization, integration)

alle 100 features sind implementiert (224.553+ zeilen, 1.106+ dateien).

vollständiger plan: [feature-implementation-plan-v3.md](feature-implementation-plan-v3.md)

feature-spezifikationen in `features-v3/`:

### edge & iot computing (features 1-10)
- [01 — edge device manager](features-v3/edge-iot/01-edge-device-manager.md)
- [02 — iot data pipeline](features-v3/edge-iot/02-iot-data-pipeline.md)
- [03 — edge function runtime](features-v3/edge-iot/03-edge-function-runtime.md)
- [04 — mesh network manager](features-v3/edge-iot/04-mesh-network-manager.md)
- [05 — edge ml inference](features-v3/edge-iot/05-edge-ml-inference.md)
- [06 — iot device provisioning](features-v3/edge-iot/06-iot-device-provisioning.md)
- [07 — lorawan gateway](features-v3/edge-iot/07-lorawan-gateway.md)
- [08 — edge cdn](features-v3/edge-iot/08-edge-cdn.md)
- [09 — digital twin viewer](features-v3/edge-iot/09-digital-twin-viewer.md)
- [10 — edge backup & restore](features-v3/edge-iot/10-edge-backup-restore.md)

### green computing (features 11-20)
- [11 — energy consumption tracker](features-v3/green-computing/11-energy-consumption-tracker.md)
- [12 — carbon footprint dashboard](features-v3/green-computing/12-carbon-footprint-dashboard.md)
- [13 — green scheduling](features-v3/green-computing/13-green-scheduling.md)
- [14 — idle resource reclamation](features-v3/green-computing/14-idle-resource-reclamation.md)
- [15 — efficiency scorecards](features-v3/green-computing/15-efficiency-scorecards.md)
- [16 — auto-shutdown policies](features-v3/green-computing/16-auto-shutdown-policies.md)
- [17 — hardware lifecycle tracker](features-v3/green-computing/17-hardware-lifecycle-tracker.md)
- [18 — pue/dcim integration](features-v3/green-computing/18-pue-dcim-integration.md)
- [19 — sustainable provider ranking](features-v3/green-computing/19-sustainable-provider-ranking.md)
- [20 — co2 offset integration](features-v3/green-computing/20-co2-offset-integration.md)

### networking (features 21-30)
- [21 — sd-wan controller](features-v3/networking/21-sd-wan-controller.md)
- [22 — vpn as a service](features-v3/networking/22-vpn-as-a-service.md)
- [23 — dns management console](features-v3/networking/23-dns-management-console.md)
- [24 — bgp route manager](features-v3/networking/24-bgp-route-manager.md)
- [25 — reverse proxy catalog](features-v3/networking/25-reverse-proxy-catalog.md)
- [26 — network segmentation designer](features-v3/networking/26-network-segmentation-designer.md)
- [27 — packet capture studio](features-v3/networking/27-packet-capture-studio.md)
- [28 — dns filtering / dhcp server](features-v3/networking/28-dns-filtering-dhcp-server.md)
- [29 — network cost analyzer](features-v3/networking/29-network-cost-analyzer.md)
- [30 — 5g/lte integration](features-v3/networking/30-5g-lte-integration.md)

### marketplace (features 31-40)
- [31 — resource trading platform](features-v3/marketplace/31-resource-trading-platform.md)
- [32 — one-click app marketplace](features-v3/marketplace/32-one-click-app-marketplace.md)
- [33 — pay-per-use billing](features-v3/marketplace/33-pay-per-use-billing.md)
- [34 — reseller / white-label](features-v3/marketplace/34-reseller-white-label.md)
- [35 — sla management & credits](features-v3/marketplace/35-sla-management-credits.md)
- [36 — crypto payment gateway](features-v3/marketplace/36-crypto-payment-gateway.md)
- [37 — subscription plan builder](features-v3/marketplace/37-subscription-plan-builder.md)
- [38 — usage-based recommendations](features-v3/marketplace/38-usage-based-recommendations.md)
- [39 — invoice & tax automation](features-v3/marketplace/39-invoice-tax-automation.md)
- [40 — loyalty & reward system](features-v3/marketplace/40-loyalty-reward-system.md)

### advanced storage (features 41-50)
- [41 — distributed storage cluster](features-v3/advanced-storage/41-distributed-storage-cluster.md)
- [42 — object storage gateway](features-v3/advanced-storage/42-object-storage-gateway.md)
- [43 — backup chain visualizer](features-v3/advanced-storage/43-backup-chain-visualizer.md)
- [44 — storage tiering policies](features-v3/advanced-storage/44-storage-tiering-policies.md)
- [45 — file sharing & sync](features-v3/advanced-storage/45-file-sharing-sync.md)
- [46 — database replication manager](features-v3/advanced-storage/46-database-replication-manager.md)
- [47 — data migration wizard](features-v3/advanced-storage/47-data-migration-wizard.md)
- [48 — dedup & compression](features-v3/advanced-storage/48-dedup-compression.md)
- [49 — immutable backup vault](features-v3/advanced-storage/49-immutable-backup-vault.md)
- [50 — data catalog & lineage](features-v3/advanced-storage/50-data-catalog-lineage.md)

### gaming & esports (features 51-60)
- [51 — anti-cheat integration](features-v3/gaming-esports/51-anti-cheat-integration.md)
- [52 — tournament manager](features-v3/gaming-esports/52-tournament-manager.md)
- [53 — matchmaking service](features-v3/gaming-esports/53-matchmaking-service.md)
- [54 — voice server provisioning](features-v3/gaming-esports/54-voice-server-provisioning.md)
- [55 — live spectate / obs](features-v3/gaming-esports/55-live-spectate-obs.md)
- [56 — game analytics dashboard](features-v3/gaming-esports/56-game-analytics-dashboard.md)
- [57 — mod/modpack publishing](features-v3/gaming-esports/57-mod-modpack-publishing.md)
- [58 — server rental marketplace](features-v3/gaming-esports/58-server-rental-marketplace.md)
- [59 — cross-play proxy](features-v3/gaming-esports/59-cross-play-proxy.md)
- [60 — game server dashboard](features-v3/gaming-esports/60-game-server-dashboard.md)

### identity, auth & compliance (features 61-70)
- [61 — sso/oidc provider](features-v3/61-sso-oidc-provider.md)
- [62 — passkey/webauthn](features-v3/62-passkey-webauthn.md)
- [63 — session manager](features-v3/63-session-manager.md)
- [64 — privileged access management](features-v3/64-privileged-access-management.md)
- [65 — policy as code](features-v3/65-policy-as-code.md)
- [66 — compliance scanner](features-v3/66-compliance-scanner.md)
- [67 — audit trail analytics](features-v3/67-audit-trail-analytics.md)
- [68 — data classification engine](features-v3/68-data-classification-engine.md)
- [69 — vendor risk assessment](features-v3/69-vendor-risk-assessment.md)
- [70 — breach notification](features-v3/70-breach-notification.md)

### automation & orchestration (features 71-80)
- [71 — workflow studio](features-v3/71-workflow-studio.md)
- [72 — ansible/salt integration](features-v3/72-ansible-salt-integration.md)
- [73 — infrastructure pipelines](features-v3/73-infrastructure-pipelines.md)
- [74 — config drift detector](features-v3/74-configuration-drift-detector.md)
- [75 — resource quota management](features-v3/75-resource-quota-management.md)
- [76 — event-driven auto-remediation](features-v3/76-event-driven-auto-remediation.md)
- [77 — maintenance planner](features-v3/77-scheduled-maintenance-planner.md)
- [78 — runbook template library](features-v3/78-runbook-templates-library.md)
- [79 — chaos engineering toolkit](features-v3/79-chaos-engineering-toolkit.md)
- [80 — self-healing infrastructure](features-v3/80-self-healing-infrastructure.md)

### visualization, reporting & bi (features 81-90)
- [81 — 3d infrastructure topology](features-v3/81-3d-topology.md)
- [82 — custom report builder](features-v3/82-custom-report-builder.md)
- [83 — bi dashboard](features-v3/83-bi-dashboard.md)
- [84 — anomaly detection](features-v3/84-anomaly-detection.md)
- [85 — resource forecasting](features-v3/85-resource-forecasting.md)
- [86 — dependency graph](features-v3/86-dependency-graph.md)
- [87 — cost analytics](features-v3/87-cost-analytics.md)
- [88 — executive summary](features-v3/88-executive-summary.md)
- [89 — geolocation heatmap](features-v3/89-geolocation-heatmap.md)
- [90 — report bot](features-v3/90-report-bot.md)

### integration ecosystem (features 91-100)
- [91 — pub/sub event bus](features-v3/91-pubsub-event-bus.md)
- [92 — integration marketplace](features-v3/92-integration-marketplace.md)
- [93 — low-code connectors](features-v3/93-low-code-connectors.md)
- [94 — email infrastructure](features-v3/94-email-infrastructure.md)
- [95 — sms/voice notification](features-v3/95-sms-voice.md)
- [96 — calendar sync](features-v3/96-calendar-sync.md)
- [97 — vcs integration](features-v3/97-vcs-integration.md)
- [98 — jira/linear sync](features-v3/98-jira-linear-sync.md)
- [99 — identity federation](features-v3/99-identity-federation.md)
- [100 — ipaas integration](features-v3/100-ipaas-integration.md)

## feature plans v2

50 features in 7 kategorien — vollständig dokumentiert in `features-v2/`:

### ai & intelligence
- [01 - ai log anomaly detector](features-v2/01-ai-log-anomaly-detector.md)
- [02 - ai resource optimizer](features-v2/02-ai-resource-optimizer.md)
- [03 - ai assistant chatbot](features-v2/03-ai-assistant-chatbot.md)
- [04 - ai threat detection](features-v2/04-ai-threat-detection.md)
- [05 - ai backup validator](features-v2/05-ai-backup-validator.md)
- [06 - ai config advisor](features-v2/06-ai-config-advisor.md)
- [07 - ai code review bot](features-v2/07-ai-code-review-bot.md)
- [08 - ai performance profiler](features-v2/08-ai-performance-profiler.md)
- [09 - ai ticket triage](features-v2/09-ai-ticket-triage.md)
- [10 - ai capacity forecaster](features-v2/10-ai-capacity-forecaster.md)

### developer ecosystem
- [11 - infra pilot cli](features-v2/11-infra-pilot-cli.md)
- [12 - terraform provider](features-v2/12-terraform-provider.md)
- [13 - webhook event bus](features-v2/13-webhook-event-bus.md)
- [14 - api gateway & rate limiting](features-v2/14-api-gateway-rate-limiting.md)
- [15 - plugin marketplace](features-v2/15-plugin-marketplace.md)
- [16 - gitops sync](features-v2/16-gitops-sync.md)
- [17 - opentelemetry export](features-v2/17-opentelemetry-export.md)
- [18 - graphql api](features-v2/18-graphql-api.md)

### advanced infrastructure
- [19 - kubernetes cluster manager](features-v2/19-kubernetes-cluster-manager.md)
- [20 - multi-region failover](features-v2/20-multi-region-failover.md)
- [21 - edge compute nodes](features-v2/21-edge-compute-nodes.md)
- [22 - serverless functions (faas)](features-v2/22-serverless-functions-faas.md)
- [23 - cdn & waf integration](features-v2/23-cdn-waf-integration.md)
- [24 - multi-cloud cost optimizer](features-v2/24-multi-cloud-cost-optimizer.md)
- [25 - disaster recovery orchestrator](features-v2/25-disaster-recovery-orchestrator.md)
- [26 - service mesh integration](features-v2/26-service-mesh-integration.md)

### collaboration & team
- [27 - collaborative terminal](features-v2/27-collaborative-terminal.md)
- [28 - team workspaces](features-v2/28-team-workspaces.md)
- [29 - change approval workflow](features-v2/29-change-approval-workflow.md)
- [30 - incident management](features-v2/30-incident-management.md)
- [31 - runbook automation](features-v2/31-runbook-automation.md)
- [32 - internal knowledge base](features-v2/32-internal-knowledge-base.md)
- [33 - team activity feed](features-v2/33-team-activity-feed.md)

### advanced observability
- [34 - distributed tracing](features-v2/34-distributed-tracing.md)
- [35 - custom dashboard builder](features-v2/35-custom-dashboard-builder.md)
- [36 - sla / slo tracking](features-v2/36-sla-slo-tracking.md)
- [37 - synthetic monitoring](features-v2/37-synthetic-monitoring.md)
- [38 - cost allocation & chargeback](features-v2/38-cost-allocation-chargeback.md)
- [39 - alert fatigue reduction](features-v2/39-alert-fatigue-reduction.md)

### user experience & platform
- [40 - mobile app](features-v2/40-mobile-app.md)
- [41 - desktop app](features-v2/41-desktop-app.md)
- [42 - i18n / l10n](features-v2/42-i18n-l10n.md)
- [43 - wcag 2.1 aa compliance](features-v2/43-wcag-21-aa-compliance.md)
- [44 - theme studio](features-v2/44-theme-studio.md)
- [45 - bulk operations manager](features-v2/45-bulk-operations-manager.md)

### security & compliance
- [46 - compliance framework reports](features-v2/46-compliance-framework-reports.md)
- [47 - secrets management](features-v2/47-secrets-management.md)
- [48 - container image scanner](features-v2/48-container-image-scanner.md)
- [49 - siem export](features-v2/49-siem-export.md)
- [50 - gdpr & data retention](features-v2/50-gdpr-data-retention.md)

## security & support

- [security policy](../SECURITY.md)
- [security review 2026-05-04](security/security-review-2026-05-04.md)
- [code of conduct](../CODE_OF_CONDUCT.md)
- [owners](../OWNERS.md)

## license

infra pilot ist unter der [mit license](../LICENSE) lizenziert.

last updated: may 2026 (v2 + v3 feature plans added)
