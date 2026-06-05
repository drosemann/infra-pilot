# feature 26: service mesh integration

| metadata | value |
|----------|-------|
| feature id | 26 |
| feature name | service mesh integration |
| primary service | integration service |
| effort estimate | large (7-10 pt) |
| status | planned |

## 1. overview

deep integration with **istio** and **linkerd** service meshes, providing zero-trust mtls between all services, fine-grained traffic splitting for canary deployments, and comprehensive observability dashboards -- all managed from the panel with a simplified ux that abstracts mesh complexity.

### goals

- enable mtls with one click -- no manual certificate management
- simplify canary deployments via traffic weight / header / mirror rules
- provide unified telemetry (golden signals: latency, traffic, errors, saturation)
- support multi-cluster mesh federation (future)
- reduce operational overhead with pre-built mesh profiles (dev, staging, prod)

## 2. architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                            Panel (UI)                                   │
│  ┌────────────────┐  ┌─────────────────┐  ┌──────────────────────────┐ │
│  │ Mesh Dashboard  │  │ Traffic Manager  │  │ Observability Explorer  │ │
│  │ (overview,     │  │ (routing rules,  │  │ (Jaeger, Grafana, Kiali)│ │
│  │  status)       │  │  canary config)  │  │                          │ │
│  └───────┬────────┘  └────────┬────────┘  └────────────┬─────────────┘ │
└──────────┼────────────────────┼────────────────────────┼───────────────┘
           │                    │                        │
           ▼                    ▼                        ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        Integration Service                              │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    Mesh Abstraction Layer                         │   │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐  │   │
│  │  │   Istio Adapter   │  │   Linkerd Adapter│  │  (Future:    │  │   │
│  │  │   (istio.io/v1)   │  │   (linkerd.io)   │  │  Consul,     │  │   │
│  │  │                   │  │                  │  │  Kuma...)    │  │   │
│  │  └────────┬─────────┘  └────────┬─────────┘  └───────┬───────┘  │   │
│  └───────────┼─────────────────────┼────────────────────┼───────────┘   │
│              │                     │                    │               │
│  ┌───────────┴─────────────────────┴────────────────────┴───────────┐   │
│  │                    Mesh Operator                                   │   │
│  │  ┌──────────────┐ ┌────────────────┐ ┌────────────────────────┐   │   │
│  │  │ Sidecar      │ │ mTLS / Security│ │ Traffic Management    │   │   │
│  │  │ Injector     │ │ Manager        │ │ (VS, DR, GW CRDs)     │   │   │
│  │  └──────────────┘ └────────────────┘ └────────────────────────┘   │   │
│  │  ┌──────────────┐ ┌────────────────┐ ┌────────────────────────┐   │   │
│  │  │ Telemetry    │ │ Canary         │ │ Dashboard / Export    │   │   │
│  │  │ Collector    │ │ Controller     │ │ (Prometheus, Grafana) │   │   │
│  │  └──────────────┘ └────────────────┘ └────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────┘
           │                    │                        │
           ▼                    ▼                        ▼
┌──────────────┐    ┌──────────────────┐    ┌───────────────────────┐
│ Kubernetes   │    │ Istio / Linkerd  │    │ Prometheus / Jaeger   │
│ API Server   │    │ Control Plane    │    │ / Grafana / Kiali     │
│ (CRDs)       │    │ (istiod /       │    │                       │
│              │    │  linkerd-cp)    │    │                       │
└──────────────┘    └──────────────────┘    └───────────────────────┘
```

### component responsibilities

| component | role |
|-----------|------|
| panel | mesh dashboard, traffic manager ui, canary wizard, observability explorer |
| integration service | provider abstraction, crd generation, telemetry aggregation |
| istio / linkerd adapter | translates panel config into provider-specific crds (virtualservice, destinationrule, serviceentry, etc.) |
| sidecar injector | manages automatic sidecar injection via namespace labels and annotations |
| mtls manager | configures peer authentication, destination rules, and certificate rotation |
| traffic manager | creates and updates virtualservice / destinationrule / serviceentry resources |
| canary controller | manages progressive traffic shifting with automated rollback gates |
| telemetry collector | aggregates prometheus metrics and jaeger traces for the dashboard |

## 3. data model

### `mesh_profiles`

| field | type | description |
|-------|------|-------------|
| id | uuid | primary key |
| environment_id | uuid | fk to environments.id |
| name | varchar | e.g. "production-mesh" |
| provider | enum | "istio", "linkerd" |
| version | varchar | e.g. "1.20.2" |
| status | enum | installing, active, degraded, removed |
| mtls | enum | "disabled", "permissive", "strict" |
| config | jsonb | provider-specific mesh config |
| telemetry_enabled | boolean | |
| tracing_enabled | boolean | |
| created_at | timestamptz | |
| updated_at | timestamptz | |

### `mesh_namespaces`

| field | type | description |
|-------|------|-------------|
| id | uuid | primary key |
| profile_id | uuid | fk to mesh_profiles.id |
| namespace | varchar | kubernetes namespace |
| sidecar_injection | enum | "enabled", "disabled", "inherit" |
| mtls_mode | enum | "inherit", "strict", "permissive" |
| created_at | timestamptz | |

### `mesh_traffic_rules`

| field | type | description |
|-------|------|-------------|
| id | uuid | primary key |
| profile_id | uuid | fk to mesh_profiles.id |
| name | varchar | rule name |
| rule_type | enum | "routing", "canary", "mirroring", "timeout", "retry", "fault_injection" |
| source_service | varchar | |
| destination_service | varchar | |
| config | jsonb | type-specific configuration |
| enabled | boolean | |
| priority | int | |
| created_at | timestamptz | |
| updated_at | timestamptz | |

### `mesh_canary_releases`

| field | type | description |
|-------|------|-------------|
| id | uuid | primary key |
| profile_id | uuid | fk to mesh_profiles.id |
| name | varchar | e.g. "api-v2-canary" |
| target_service | varchar | |
| target_namespace | varchar | |
| baseline_version | varchar | |
| canary_version | varchar | |
| strategy | enum | "weighted", "header_based", "mirror_based" |
| steps | jsonb | traffic weight progression e.g. `[{"weight":5, "duration":"10m"}, {"weight":25, ...}]` |
| metrics_gates | jsonb | success rate, latency, error budget thresholds |
| current_step | int | |
| status | enum | running, promoted, rolled_back, failed, completed |
| started_at | timestamptz | |
| promoted_at | timestamptz | |

### `mesh_telemetry`

| field | type | description |
|-------|------|-------------|
| id | uuid | primary key |
| profile_id | uuid | fk to mesh_profiles.id |
| source_service | varchar | |
| destination_service | varchar | |
| metric | varchar | "request_count", "error_rate", "p50_latency", "p99_latency" |
| value | float | |
| timestamp | timestamptz | |

## 4. api design

### mesh profiles

```
POST   /api/v2/mesh/profiles                   — Install / create mesh profile
GET    /api/v2/mesh/profiles                    — List mesh profiles
GET    /api/v2/mesh/profiles/:id                — Get profile details
PUT    /api/v2/mesh/profiles/:id                — Update mesh configuration
DELETE /api/v2/mesh/profiles/:id                — Uninstall mesh
GET    /api/v2/mesh/profiles/:id/status         — Detailed health status
```

### namespace management

```
GET    /api/v2/mesh/profiles/:id/namespaces     — List mesh-enabled namespaces
POST   /api/v2/mesh/profiles/:id/namespaces     — Enable mesh for a namespace
PUT    /api/v2/mesh/profiles/:id/namespaces/:nid — Update namespace config
DELETE /api/v2/mesh/profiles/:id/namespaces/:nid — Disable mesh for namespace
```

### traffic rules

```
GET    /api/v2/mesh/profiles/:id/rules          — List traffic rules
POST   /api/v2/mesh/profiles/:id/rules          — Create traffic rule
PUT    /api/v2/mesh/profiles/:id/rules/:rid     — Update traffic rule
DELETE /api/v2/mesh/profiles/:id/rules/:rid     — Delete traffic rule
POST   /api/v2/mesh/profiles/:id/rules/simulate — Simulate rule before applying
```

### canary releases

```
GET    /api/v2/mesh/profiles/:id/canaries       — List canary releases
POST   /api/v2/mesh/profiles/:id/canaries       — Start canary release
GET    /api/v2/mesh/profiles/:id/canaries/:cid   — Get canary details
POST   /api/v2/mesh/profiles/:id/canaries/:cid/promote  — Promote canary to 100%
POST   /api/v2/mesh/profiles/:id/canaries/:cid/rollback — Rollback canary
```

### mtls & security

```
GET    /api/v2/mesh/profiles/:id/mtls           — Get mTLS status
PUT    /api/v2/mesh/profiles/:id/mtls           — Update mTLS mode (strict/permissive/disabled)
POST   /api/v2/mesh/profiles/:id/mtls/rotate    — Rotate mTLS certificates
```

### telemetry

```
GET    /api/v2/mesh/profiles/:id/telemetry      — Service graph + golden signals
GET    /api/v2/mesh/profiles/:id/telemetry/services/:svc — Per-service metrics
GET    /api/v2/mesh/profiles/:id/telemetry/topology     — Service dependency graph
GET    /api/v2/mesh/profiles/:id/telemetry/traces      — Recent traces (Jaeger-backed)
```

## 5. implementation plan

### phase 1 -- mesh provider abstraction & profile management (2 pt)

• define `meshadapter` interface:
   - `installmesh(config)` to provisions mesh control plane via helm
   - `uninstallmesh(profileid)` to removes mesh
   - `enablesidecarinjection(namespace)`, `disablesidecarinjection(namespace)`
   - `createvirtualservice(rule)`, `createdestinationrule(rule)`
   - `getmeshstatus()` to health + version
• implement istio adapter (generates `virtualservice`, `destinationrule`, `peerauthentication`, `serviceentry` crds)
• implement linkerd adapter (generates `httproute`, `serviceprofile`, `trafficsplit` crds)
• build `mesh_profiles` crud + helm-based install/uninstall workflow

### phase 2 -- sidecar injection & mtls (1.5 pt)

• namespace-level sidecar injection management (enable/disable via labels)
• mtls mode configuration (`strict` / `permissive` / `disable`)
• certificate rotation endpoint
• mtls status dashboard (percentage of traffic encrypted)

### phase 3 -- traffic management (2 pt)

• routing rules crud (virtualservice / serviceprofile generation)
• fault injection rules (delay, abort)
• timeout and retry rule configuration
• mirroring (shadow traffic to a new version)
• rule validation + dry-run simulation

### phase 4 -- canary releases (2 pt)

• canary release controller -- step-based traffic shifting
• metrics gates: success rate, latency, error budget
• auto-promote / auto-rollback based on gate thresholds
• canary overview dashboard (current step, metrics, decision)

### phase 5 -- observability (1 pt)

• prometheus metric scraping configuration for mesh telemetry
• jaeger tracing integration
• kiali-like service graph embedded in panel
• golden signals dashboard (red method: rate, errors, duration)

### phase 6 -- ui & polish (0.5-1 pt)

• mesh overview dashboard (status, version, service count, mtls %, traffic rates)
• traffic rule editor with yaml preview
• canary wizard with visual step configuration
• service topology graph (interactive d3/vis.js)
• export metrics to grafana datasource

## 6. configuration examples

### mesh profile creation (post /api/v2/mesh/profiles)

```json
{
  "name": "production-mesh",
  "environment_id": "env-prod-001",
  "provider": "istio",
  "version": "1.20.2",
  "config": {
    "control_plane": {
      "replicas": 3,
      "cpu": "500m",
      "memory": "1Gi"
    },
    "proxy": {
      "cpu": "100m",
      "memory": "256Mi",
      "log_level": "warning"
    },
    "mesh_config": {
      "enable_auto_mtls": true,
      "access_log_format": "JSON",
      "outbound_traffic_policy": "ALLOW_ANY"
    }
  },
  "mtls": "strict",
  "telemetry_enabled": true,
  "tracing_enabled": true,
  "namespaces": ["default", "api", "frontend", "backend"]
}
```

### canary release (post /api/v2/mesh/profiles/:id/canaries)

```json
{
  "name": "api-v2-2026-05",
  "target_service": "api-gateway",
  "target_namespace": "api",
  "baseline_version": "v1.3.0",
  "canary_version": "v2.0.0-beta.1",
  "strategy": "weighted",
  "steps": [
    {"weight": 5, "duration": "10m"},
    {"weight": 25, "duration": "20m"},
    {"weight": 50, "duration": "30m"},
    {"weight": 75, "duration": "20m"},
    {"weight": 100, "duration": "0m"}
  ],
  "metrics_gates": {
    "error_rate": {"threshold": 0.01, "window": "5m"},
    "p99_latency_ms": {"threshold": 500, "window": "5m"},
    "success_rate": {"threshold": 0.995, "window": "5m"}
  }
}
```

### traffic splitting rule (post /api/v2/mesh/profiles/:id/rules)

```json
{
  "name": "canary-api-split",
  "rule_type": "canary",
  "source_service": "ingress-gateway",
  "destination_service": "api-gateway",
  "config": {
    "hosts": ["api.example.com"],
    "subsets": [
      {
        "name": "stable",
        "labels": {"version": "v1.3.0"},
        "weight": 75
      },
      {
        "name": "canary",
        "labels": {"version": "v2.0.0-beta.1"},
        "weight": 25,
        "headers": {
          "request": {
            "set": {
              "X-Canary": "true"
            }
          }
        }
      }
    ],
    "mirror": {
      "percentage": 10,
      "host": "api-gateway-shadow",
      "subset": "canary"
    },
    "retries": {
      "attempts": 3,
      "per_try_timeout": "2s"
    },
    "fault_injection": null,
    "timeout": "10s"
  },
  "enabled": true,
  "priority": 100
}
```

### istio crds generated by adapter

```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: api-gateway-canary
  namespace: api
spec:
  hosts:
    - api.example.com
  gateways:
    - ingress-gateway
  http:
    - match:
        - headers:
            X-Canary:
              exact: "true"
      route:
        - destination:
            host: api-gateway
            subset: canary
          weight: 100
    - route:
        - destination:
            host: api-gateway
            subset: stable
          weight: 75
        - destination:
            host: api-gateway
            subset: canary
          weight: 25
      timeout: 10s
      retries:
        attempts: 3
        perTryTimeout: 2s
      mirror:
        host: api-gateway-shadow
        subset: canary
      mirrorPercentage:
        value: 10.0
---
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: api-gateway-subsets
  namespace: api
spec:
  host: api-gateway
  subsets:
    - name: stable
      labels:
        version: v1.3.0
    - name: canary
      labels:
        version: v2.0.0-beta.1
  trafficPolicy:
    tls:
      mode: ISTIO_MUTUAL
    connectionPool:
      tcp:
        maxConnections: 100
      http:
        http1MaxPendingRequests: 1024
        maxRequestsPerConnection: 10
    outlierDetection:
      consecutive5xxErrors: 5
      interval: 30s
      baseEjectionTime: 30s
```

## 7. service assignments

| service | responsibilities |
|---------|------------------|
| **integration service** | mesh adapter layer, crd generation, helm lifecycle, telemetry aggregation |
| **orchestrator agent** | canary release controller, progressive traffic shifting, gate evaluation |
| **panel** | mesh dashboard, traffic rule editor, canary wizard, service graph, observability explorer |
| **database** | `mesh_profiles`, `mesh_namespaces`, `mesh_traffic_rules`, `mesh_canary_releases`, `mesh_telemetry` |
| **scheduler** | canary step progression cron, telemetry aggregation intervals |
| **notification service** | canary promote/rollback alerts, mtls cert expiry warnings |

## 8. effort breakdown

| task | pt | dependencies |
|------|----|-------------|
| meshadapter interface + helm lifecycle | 1.0 | -- |
| istio adapter (virtualservice, destinationrule, peerauthentication) | 1.0 | meshadapter |
| linkerd adapter (httproute, trafficsplit, serviceprofile) | 1.0 | meshadapter |
| sidecar injection management | 0.5 | adapters |
| mtls configuration + certificate rotation | 1.0 | adapters |
| traffic rules crud + validation | 1.0 | adapters |
| fault injection / timeout / retry rules | 0.5 | traffic rules |
| canary controller + step progression | 1.5 | traffic rules |
| metrics gates (auto-promote / rollback) | 0.5 | canary controller |
| prometheus / jaeger telemetry collector | 1.0 | -- |
| service graph + golden signals dashboard | 1.0 | telemetry |
| ui screens (mesh overview, rules, canary wizard, topology) | 1.5 | all apis |
| documentation & tests | 0.5 | -- |

## 9. mesh provider comparison

| aspect | istio | linkerd |
|--------|-------|---------|
| **control plane** | istiod (single binary) | linkerd-controller, identity, tap, destination |
| **proxy** | envoy | linkerd2-proxy (rust) |
| **mtls** | built-in, spiffe certs | built-in, identity controller |
| **traffic splitting** | virtualservice + destinationrule | trafficsplit + serviceprofile |
| **canary support** | manual (vs weights) + flagger | manual (ts weights) + flagger |
| **telemetry** | prometheus + grafana + kiali | linkerd-viz + grafana |
| **tracing** | jaeger / zipkin | opencensus collector |
| **performance overhead** | ~5-15 ms per hop | ~1-5 ms per hop |
| **resource usage** | higher (envoy) | lower (rust proxy) |
| **k8s crds** | 50+ | 10+ |

## 10. risks & mitigations

| risk | impact | mitigation |
|------|--------|------------|
| envoy proxy memory leak in long-running canaries | pod oom, traffic disruption | set proxy resource limits; implement canary step timeout |
| mtls certificate rotation failure | mesh communication broken | monitor cert expiry; pre-rotate before expiry; fallback to permissive mode |
| traffic split misconfiguration | incorrect routing for real users | simulation endpoint that dry-runs virtualservice generation; integration tests for each rule type |
| istio crd version drift across upgrades | rule application failure | version-pin crds; automated upgrade tests in staging |
| high cardinality telemetry explodes prometheus | expensive queries, slow dashboard | aggregation rules (5m, 30m, 1h rollups); cardinality limits on request labels |
