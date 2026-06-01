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

## feature plans v2

50 neue features in 7 kategorien — vollständig dokumentiert in `features-v2/`:

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

last updated: may 2026 (v2 feature plans added)
