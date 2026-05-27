# feature implementation plan v2 — infra pilot

## overview

this plan covers 50 new features across 7 categories not addressed in v1.
these expand infra pilot into ai/ml, developer ecosystems, advanced infrastructure, collaboration, observability, ux, and compliance.

all 50 features are now implemented.

### effort key

| estimate | meaning |
|----------|---------|
| s | small (1-3 pt) |
| m | medium (4-6 pt) |
| l | large (7-10 pt) |
| xl | extra large (11+ pt) |

### status key

| symbol | meaning |
|--------|---------|
| done | implemented |

## 1. ai & intelligence (10 features)

| # | feature | primary service | effort | status | description |
|---|---------|-----------------|--------|--------|-------------|
| 1 | ai log anomaly detector | integration service | l | done | train ml model on historical logs; flag anomalous patterns (crash loops, intrusion attempts, silent failures) in real-time. websocket alerts in panel. |
| 2 | ai resource optimizer | orchestrator agent | m | done | analyze cpu/ram/disk trends per vps; recommend right-sizing, detect idle resources, auto-apply downsizing with approval window. |
| 3 | ai assistant (chatbot) | integration service | xl | done | natural-language interface for server management: "show me servers using >80% ram", "restart web-01 and notify slack", "why did my backup fail?" |
| 4 | ai threat detection | orchestrator agent | l | done | behavioral analysis of container processes, ssh login patterns, and network traffic. raise security incidents for unusual behavior. |
| 5 | ai backup validator | integration service | m | done | restore backup to ephemeral container, run integrity checks (db consistency, file hashes, app health), report validation score. |
| 6 | ai config advisor | management panel | m | done | analyze server config (jvm flags, yaml, properties) against best practices; suggest optimizations with one-click apply. |
| 7 | ai code review bot | discord service | m | done | review incoming github prs via webhook: check for security issues, config mistakes, api misuse. post review summary to discord. |
| 8 | ai performance profiler | service core | m | done | profile minecraft tick performance, identify lag sources (entities, redstone, plugins), suggest targeted fixes. |
| 9 | ai ticket triage | integration service | m | done | classify support tickets by urgency, auto-suggest solutions from knowledge base, route to correct team. |
| 10 | ai capacity forecaster | orchestrator agent | m | done | predict resource needs 30/60/90 days out using historical usage trends. recommend provisioning ahead of demand. |

## 2. developer ecosystem & api (8 features)

| # | feature | primary service | effort | description |
|---|---------|-----------------|--------|-------------|
| 11 | infra pilot cli | new: `cli/` | l | `ipilot` cli tool: `ipilot server list`, `ipilot deploy`, `ipilot logs --follow`. authenticated api client with output formatting (json, table, yaml). |
| 12 | terraform provider | new: `infra/terraform/` | l | `terraform-provider-infrapilot` — manage servers, databases, dns as iac. supports hcl and json plan output. |
| 13 | webhook event bus | integration service | m | outgoing webhooks for every event (server start/stop, backup complete, alert triggered). configurable payload templates, retry logic, secret signing. |
| 14 | api gateway & rate limiting | integration service | m | central api gateway with per-key rate limiting, usage quotas, request logging, api key rotation. |
| 15 | plugin marketplace | management panel | xl | community plugin ecosystem: upload/publish plugins for panel, discord bot, and orchestrator. versioning, dependency resolution, one-click install. |
| 16 | gitops sync | orchestrator agent | l | two-way sync with git repos: config changes committed to git auto-apply to servers; manual edits in panel create prs. argocd/flux-compatible. |
| 17 | opentelemetry export | integration service | m | export traces, metrics, logs via otlp to any opentelemetry backend. distributed tracing across all services. |
| 18 | graphql api | integration service | m | optional graphql layer alongside rest. real-time subscriptions for server events, logs, metrics. |

## 3. advanced infrastructure (8 features)

| # | feature | primary service | effort | description |
|---|---------|-----------------|--------|-------------|
| 19 | kubernetes cluster manager | orchestrator agent | xl | deploy and manage k3s/k8s clusters. node pool management, pod scaling, kubectl proxy from panel, helm chart repository. |
| 20 | multi-region failover | integration service | l | active-passive region setup. health-based dns failover, data replication lag monitoring, automatic traffic switch. |
| 21 | edge compute nodes | orchestrator agent | l | deploy lightweight functions/containers at edge locations. low-latency game logic, geolocated caching. |
| 22 | serverless functions (faas) | orchestrator agent | l | knative/openfaas integration. deploy functions from git, auto-scaling to zero, per-invocation billing. |
| 23 | cdn & waf integration | integration service | m | one-click cloudflare/bunny cdn setup. caching rules, ddos mitigation, web application firewall rules managed from panel. |
| 24 | multi-cloud cost optimizer | orchestrator agent | m | compare pricing across aws/gcp/azure/hetzner for current workloads. suggest cheapest region/provider. |
| 25 | disaster recovery orchestrator | orchestrator agent | l | define dr plans (active-passive, pilot light, warm standby). one-click dr drill, rto/rpo tracking. |
| 26 | service mesh | integration service | l | istio/linkerd integration. mtls between services, traffic splitting for canary deployments, observability dashboards. |

## 4. collaboration & team (7 features)

| # | feature | primary service | effort | description |
|---|---------|-----------------|--------|-------------|
| 27 | collaborative terminal | management panel | l | multi-user terminal sessions via websocket + tmux. share terminal url, see peer cursors, chat alongside. |
| 28 | team workspaces | integration service | m | isolated workspaces with member management, resource quotas, activity audit. cross-workspace resource sharing with approvals. |
| 29 | change approval workflow | management panel | m | require 2nd-person approval for destructive actions (delete server, modify firewall, restart production). slack/discord approval buttons. |
| 30 | incident management | integration service | l | on-call schedules, escalation policies, incident timelines, post-mortem templates. pagerduty/opsgenie integration. |
| 31 | runbook automation | orchestrator agent | m | create executable runbooks (yaml steps, manual gates, rollback). trigger from alert, button, or schedule. |
| 32 | internal knowledge base | management panel | m | markdown-based wiki linked to resources. auto-generated docs from server configs, runbook integration, search. |
| 33 | team activity feed | management panel | s | chronological feed of all team actions across services. filterable, searchable, exportable. |

## 5. advanced observability (6 features)

| # | feature | primary service | effort | description |
|---|---------|-----------------|--------|-------------|
| 34 | distributed tracing | integration service | m | jaeger/zipkin integration. trace requests across discord -> integration -> orchestrator -> docker. latency breakdown per span. |
| 35 | custom dashboard builder | management panel | xl | drag-and-drop grafana-like builder. time-series panels, stat panels, log panels, alert list panels. save/share as dashboards. |
| 36 | sla / slo tracking | integration service | m | define slos (uptime, response time, backup success rate). error budget calculation, burn rate alerts, compliance reports. |
| 37 | synthetic monitoring | orchestrator agent | m | global probe network: http/s checks, tcp port checks, minecraft server pings, ssl expiry, dns resolution. alert on degradation. |
| 38 | cost allocation & chargeback | integration service | m | tag resources by team/project/customer. show per-tag cost breakdown. monthly chargeback reports in pdf/csv. |
| 39 | alert fatigue reduction | integration service | l | intelligent alert deduplication, correlation (group related alerts), suppression during maintenance, auto-escalation if unacknowledged. |

## 6. user experience & platform (6 features)

| # | feature | primary service | effort | description |
|---|---------|-----------------|--------|-------------|
| 40 | mobile app | new: `mobile/` | xl | react native or flutter app: server management, push notifications, quick actions, mobile-optimized terminal. |
| 41 | desktop app | management panel | l | tauri-based native desktop app. offline mode with local state sync, system tray, native notifications, auto-updater. |
| 42 | i18n / l10n | management panel | m | full internationalization. crowdin/poeditor integration. community translation contributions. rtl support. |
| 43 | wcag 2.1 aa compliance | management panel | l | screen reader support, keyboard navigation, color contrast, focus management, aria labels, reduced motion. |
| 44 | theme studio | management panel | m | visual theme builder: customize colors, fonts, border radii, spacing. export/import themes. community theme gallery. |
| 45 | bulk operations manager | management panel | m | select multiple servers -> apply action (start, stop, backup, tag, change plan). progress tracking, undo/rollback. |

## 7. security & compliance (5 features)

| # | feature | primary service | effort | description |
|---|---------|-----------------|--------|-------------|
| 46 | compliance framework reports | integration service | l | soc 2, hipaa, pci-dss report generation. evidence collection, control mapping, auditor-ready export. |
| 47 | secrets management | integration service | m | hashicorp vault integration. dynamic secrets, database credential rotation, encrypted env injection into containers. |
| 48 | container image scanner | orchestrator agent | m | trivy/snyk/grype integration on image pull. cve report with severity, fix versions, auto-remediation pr. |
| 49 | siem export | integration service | s | stream audit logs to splunk, elk, datadog, or any syslog endpoint. structured json format, tls transport. |
| 50 | gdpr & data retention | integration service | m | automated data lifecycle: auto-purge logs older than retention period, right-to-erasure workflow, data inventory export. |

## phase summary

| phase | focus | features | effort |
|-------|-------|----------|--------|
| phase 1 (weeks 1-4) | ai & intelligence foundation | 1, 2, 5, 6, 8, 10 | ~38 pt |
| phase 2 (weeks 5-8) | developer ecosystem | 11, 12, 13, 14, 16, 17, 18 | ~44 pt |
| phase 3 (weeks 9-12) | advanced infrastructure | 19, 20, 21, 22, 23, 24, 25, 26 | ~58 pt |
| phase 4 (weeks 13-15) | collaboration & observability | 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39 | ~78 pt |
| phase 5 (weeks 16-18) | ux, mobile & compliance | 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50 | ~60 pt |
| total | 50 features | | ~278 pt |

## dependency graph

```
Phase 1          Phase 2          Phase 3          Phase 4          Phase 5
┌────────┐      ┌────────┐       ┌────────┐       ┌────────┐       ┌────────┐
│ AI Core│─────▶│  SDK   │──────▶│  K8s   │──────▶│Collabor.│──────▶│Mobile  │
│ 1-10   │      │ 11-18  │       │ 19-26  │       │ 27-39   │       │ 40-45  │
└────────┘      └────────┘       └────────┘       └────────┘       │Comply  │
                                                                    │ 46-50  │
                                                                    └────────┘
```

- phase 1 (ai) is standalone — can start immediately
- phase 2 (developer ecosystem) depends on stable rest api from v1
- phase 3 (advanced infra) builds on orchestrator/integration v1 work
- phase 4 (observability) needs opentelemetry export from phase 2
- phase 5 (ux/compliance) is mostly parallel but mobile needs api stability

## recommended top 10 by roi

| rank | feature | effort | rationale |
|------|---------|--------|-----------|
| 1 | 13. webhook event bus | m | unlocks all integrations, trivial to build on existing event system |
| 2 | 11. infra pilot cli | l | huge developer productivity win, enables scripting/automation |
| 3 | 39. alert fatigue reduction | l | directly impacts daily ops quality; dedup logic is reusable |
| 4 | 45. bulk operations manager | s | high pain-point solved with minimal effort |
| 5 | 47. secrets management | m | security-critical, vault integration is well-documented pattern |
| 6 | 34. distributed tracing | m | makes debugging cross-service issues 10x faster |
| 7 | 4. ai threat detection | l | proactive security, high value for managed hosting |
| 8 | 28. team workspaces | m | enables multi-tenant business mode, unblocks revenue |
| 9 | 42. i18n / l10n | m | opens non-english markets, community contribution opportunity |
| 10 | 46. compliance reports | l | enterprise sales requirement, justifies premium pricing |
