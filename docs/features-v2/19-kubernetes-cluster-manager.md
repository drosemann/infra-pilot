# feature 19: kubernetes cluster manager

- plan id: #19
- category: advanced infrastructure
- primary service: orchestrator agent
- effort: extra large (11+ pt)
- dependencies: feature 16 (gitops sync), feature 26 (service mesh)

## overview

deploy and manage k3s/k8s clusters through infra pilot. users provision single-node or multi-node kubernetes clusters, manage node pools, deploy workloads via helm, access clusters through a panel-based kubectl proxy, and configure pod auto-scaling. supports both lightweight k3s for edge/small deployments and full k8s for production-grade clusters.

### key capabilities

| capability | description |
|---|---|
| cluster provisioning | one-click k3s/k8s cluster creation with configurable version, cni, and storage backend |
| node pool management | dynamic add/remove of worker nodes with taints, labels, and instance sizing |
| kubectl proxy | browser-based kubectl terminal via the panel with rbac scoping |
| helm chart repository | built-in chart repository with versioning, one-click installs, and rollback |
| pod auto-scaling | hpa/vpa configuration through panel ui, custom metrics support |
| cluster monitoring | prometheus/grafana stack auto-deployment, node/pod metrics, alerting |
| backup & restore | velero-based cluster backup to s3-compatible storage |

## architecture

### system context

```
┌─────────────────────────────────────────────────────────────┐
│                    Infra Pilot Platform                       │
│                                                               │
│  ┌──────────┐   ┌──────────────┐   ┌────────────────────┐    │
│  │  Panel   │──▶│ Orchestrator │──▶│  K8s Cluster(s)     │    │
│  │ (React)  │   │ Agent        │   │                     │    │
│  └──────────┘   │              │   │  ┌───────────────┐  │    │
│       │         │  ┌─────────┐ │   │  │ K3s / K8s API │  │    │
│       │         │  │ Cluster │ │   │  └───────┬───────┘  │    │
│       │         │  │ Manager │─┼──│──────────▶│           │    │
│       │         │  └─────────┘ │   │          ▼           │    │
│       │         │  ┌─────────┐ │   │  ┌───────────────┐  │    │
│       └─────────┼──│ Helm    │ │   │  │ Node Pool(s)  │  │    │
│                 │  │ Proxy   │ │   │  └───────────────┘  │    │
│                 │  └─────────┘ │   │  ┌───────────────┐  │    │
│                 │  ┌─────────┐ │   │  │ Workloads     │  │    │
│                 │  │ Metrics │ │   │  └───────────────┘  │    │
│                 │  │ Bridge  │─┼──│──▶ Prometheus        │    │
│                 │  └─────────┘ │   └────────────────────┘    │
│                 └──────────────┘                             │
└─────────────────────────────────────────────────────────────┘
```

### component architecture

```
┌──────────────────────────────────────────────────┐
│              Cluster Manager Module                │
│                   (Orchestrator Agent)             │
├──────────────────────────────────────────────────┤
│                                                    │
│  ┌─────────────────┐  ┌────────────────────────┐ │
│  │ Provisioning     │  │ Node Pool Controller   │ │
│  │ Engine           │  │                        │ │
│  │ - K3s installer  │  │ - Auto-scaling group   │ │
│  │ - K8s (kubeadm)  │  │ - Taint/label mgmt     │ │
│  │ - Multi-master   │  │ - Drain & cordon       │ │
│  └────────┬─────────┘  └───────────┬────────────┘ │
│           │                        │              │
│  ┌────────▼────────────────────────▼────────────┐ │
│  │            Cluster State Store               │ │
│  │  (PostgreSQL — cluster specs, node status)   │ │
│  └────────────────────┬─────────────────────────┘ │
│           │            │            │              │
│  ┌────────▼──┐ ┌──────▼──────┐ ┌──▼───────────┐ │
│  │ Helm      │ │ kubectl     │ │ Metrics       │ │
│  │ Proxy     │ │ Proxy       │ │ Collector     │ │
│  │           │ │ (WebSocket) │ │ (Prometheus)  │ │
│  └───────────┘ └─────────────┘ └──────────────┘ │
└──────────────────────────────────────────────────┘
```

### interaction flow

```
Panel User                    Orchestrator Agent              Target Node(s)
    │                              │                              │
    │  POST /k8s/cluster/create    │                              │
    │─────────────────────────────▶│                              │
    │                              │  Generate join token/config  │
    │                              │  ssh user@node -- script.sh  │
    │                              │─────────────────────────────▶│
    │                              │  Install containerd + K3s    │
    │                              │◀─────────────────────────────│
    │                              │  Health check (kubectl get   │
    │                              │  nodes --wait-ready)         │
    │                              │◀─────────────────────────────│
    │  {"cluster_id": "kc-a1b2",   │                              │
    │   "status": "running",       │                              │
    │   "kubeconfig": "...",       │                              │
    │   "api_endpoint": "..."}     │                              │
    │◀─────────────────────────────│                              │
    │                              │                              │
    │  Panel opens kubectl proxy   │                              │
    │  WebSocket tunnel            │                              │
    │══════════════════════════════╪═══════════════▶│          │
    │  kubectl get pods -A        │                              │
    │◀═════════════════════════════╪════════════════│          │
```

## implementation plan

### phase 1: core cluster provisioning (4 pt)

| task | description |
|---|---|
| 1.1 | implement k3s installation driver (ssh-based, cloud-init, ansible) |
| 1.2 | implement k8s installation driver (kubeadm wrapper) |
| 1.3 | cluster creation api endpoint with async workflow |
| 1.4 | cluster state machine (provisioning → running → error → deleting) |
| 1.5 | tls certificate management for cluster api access |

### phase 2: node pool management (2 pt)

| task | description |
|---|---|
| 2.1 | node pool crud operations (add/drain/remove worker nodes) |
| 2.2 | auto-scaling group integration (cloud provider asgs) |
| 2.3 | taint, label, and toleration management ui |
| 2.4 | node health monitoring and auto-replacement |

### phase 3: kubectl proxy & panel integration (2 pt)

| task | description |
|---|---|
| 3.1 | websocket-based kubectl proxy in orchestrator agent |
| 3.2 | browser-based terminal component in panel (xterm.js) |
| 3.3 | rbac scoping (kubeconfig generation with limited permissions) |
| 3.4 | audit logging of all kubectl commands executed via proxy |

### phase 4: helm integration (2 pt)

| task | description |
|---|---|
| 4.1 | helm sdk integration in orchestrator agent |
| 4.2 | built-in chart repository (oci-compatible, s3-backed) |
| 4.3 | one-click chart install/upgrade/rollback from panel |
| 4.4 | chart versioning and dependency resolution |

### phase 5: auto-scaling & monitoring (2 pt)

| task | description |
|---|---|
| 5.1 | hpa/vpa configuration api and panel form |
| 5.2 | custom metrics adapter for hpa |
| 5.3 | auto-deploy prometheus + grafana stack per cluster |
| 5.4 | cluster-level dashboards and alert rules |

### phase 6: backup & security (1 pt)

| task | description |
|---|---|
| 6.1 | velero integration for cluster backup/restore |
| 6.2 | scheduled backups with retention policy |
| 6.3 | cluster upgrade workflow (k8s/k3s version bump) |
| 6.4 | security scanning (cis benchmark, trivy on node images) |

## api design

### endpoints

all endpoints are prefixed with `/api/v2/k8s`.

#### clusters

```
GET    /api/v2/k8s/clusters                          — List clusters
POST   /api/v2/k8s/clusters                          — Create cluster
GET    /api/v2/k8s/clusters/{cluster_id}              — Get cluster details
PATCH  /api/v2/k8s/clusters/{cluster_id}              — Update cluster (scale, upgrade)
DELETE /api/v2/k8s/clusters/{cluster_id}              — Delete cluster
POST   /api/v2/k8s/clusters/{cluster_id}/kubeconfig   — Generate kubeconfig
POST   /api/v2/k8s/clusters/{cluster_id}/upgrade      — Trigger cluster upgrade
POST   /api/v2/k8s/clusters/{cluster_id}/backup       — Trigger manual backup
```

#### node pools

```
GET    /api/v2/k8s/clusters/{cluster_id}/nodepools           — List node pools
POST   /api/v2/k8s/clusters/{cluster_id}/nodepools           — Create node pool
GET    /api/v2/k8s/clusters/{cluster_id}/nodepools/{pool_id} — Get node pool
PATCH  /api/v2/k8s/clusters/{cluster_id}/nodepools/{pool_id} — Update node pool
DELETE /api/v2/k8s/clusters/{cluster_id}/nodepools/{pool_id} — Delete node pool
```

#### helm charts

```
GET    /api/v2/k8s/helm/repos                  — List chart repos
POST   /api/v2/k8s/helm/repos                  — Add chart repo
DELETE /api/v2/k8s/helm/repos/{repo_id}        — Remove repo
GET    /api/v2/k8s/helm/charts                 — Search available charts
POST   /api/v2/k8s/clusters/{cluster_id}/helm/install  — Install chart
POST   /api/v2/k8s/clusters/{cluster_id}/helm/upgrade   — Upgrade release
POST   /api/v2/k8s/clusters/{cluster_id}/helm/rollback  — Rollback release
```

#### proxy

```
WS     /api/v2/k8s/clusters/{cluster_id}/proxy/ws   — WebSocket kubectl proxy
```

#### auto-scaling

```
GET    /api/v2/k8s/clusters/{cluster_id}/hpa                  — List HPA rules
POST   /api/v2/k8s/clusters/{cluster_id}/hpa                  — Create HPA rule
PATCH  /api/v2/k8s/clusters/{cluster_id}/hpa/{hpa_id}         — Update HPA rule
DELETE /api/v2/k8s/clusters/{cluster_id}/hpa/{hpa_id}         — Delete HPA rule
```

### request/response examples

#### create cluster

```json
POST /api/v2/k8s/clusters

{
  "name": "production-eu-1",
  "type": "k3s",
  "version": "v1.30.0+k3s1",
  "region": "eu-west-1",
  "high_availability": true,
  "control_plane": {
    "count": 3,
    "instance_type": "c6i.xlarge"
  },
  "node_pools": [
    {
      "name": "workers",
      "instance_type": "c6i.2xlarge",
      "min_size": 3,
      "max_size": 10,
      "desired_size": 3,
      "taints": [],
      "labels": {
        "workload": "general"
      }
    }
  ],
  "networking": {
    "cni": "cilium",
    "pod_cidr": "10.42.0.0/16",
    "service_cidr": "10.43.0.0/16"
  },
  "storage": {
    "backend": "longhorn",
    "replica_count": 3
  }
}
```

response:

```json
{
  "cluster_id": "kc-euprod-7f2a",
  "status": "provisioning",
  "api_endpoint": "https://api.kc-euprod-7f2a.infra-pilot.io:6443",
  "created_at": "2026-05-27T10:30:00Z",
  "estimated_ready": "2026-05-27T10:35:00Z"
}
```

#### install helm chart

```json
POST /api/v2/k8s/clusters/kc-euprod-7f2a/helm/install

{
  "chart": "nginx-ingress/ingress-nginx",
  "version": "4.10.0",
  "release_name": "ingress",
  "namespace": "ingress-nginx",
  "values": {
    "controller": {
      "replicaCount": 2,
      "service": {
        "type": "LoadBalancer"
      }
    }
  }
}
```

response:

```json
{
  "release_name": "ingress",
  "namespace": "ingress-nginx",
  "status": "deployed",
  "chart": "nginx-ingress/ingress-nginx",
  "version": "4.10.0",
  "updated_at": "2026-05-27T10:35:00Z"
}
```

## data model

### cluster

```sql
CREATE TABLE k8s_clusters (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(128) NOT NULL UNIQUE,
    type            VARCHAR(10) NOT NULL CHECK (type IN ('k3s', 'k8s')),
    version         VARCHAR(32) NOT NULL,
    region          VARCHAR(64) NOT NULL,
    high_availability BOOLEAN DEFAULT FALSE,
    status          VARCHAR(20) NOT NULL DEFAULT 'provisioning'
                    CHECK (status IN ('provisioning','running','upgrading',
                                      'degraded','error','deleting')),
    api_endpoint    VARCHAR(512),
    kubeconfig_encrypted TEXT,
    cluster_ca_cert TEXT,
    config          JSONB NOT NULL DEFAULT '{}',
    created_by      UUID NOT NULL REFERENCES users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE k8s_node_pools (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cluster_id      UUID NOT NULL REFERENCES k8s_clusters(id) ON DELETE CASCADE,
    name            VARCHAR(128) NOT NULL,
    instance_type   VARCHAR(64) NOT NULL,
    min_size        INTEGER NOT NULL DEFAULT 1,
    max_size        INTEGER NOT NULL DEFAULT 10,
    desired_size    INTEGER NOT NULL,
    current_size    INTEGER NOT NULL DEFAULT 0,
    taints          JSONB DEFAULT '[]',
    labels          JSONB DEFAULT '{}',
    status          VARCHAR(20) NOT NULL DEFAULT 'creating',
    provider_data   JSONB DEFAULT '{}',  -- cloud ASG / instance IDs
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (cluster_id, name)
);

CREATE TABLE k8s_helm_releases (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cluster_id      UUID NOT NULL REFERENCES k8s_clusters(id) ON DELETE CASCADE,
    release_name    VARCHAR(128) NOT NULL,
    namespace       VARCHAR(128) NOT NULL DEFAULT 'default',
    chart_name      VARCHAR(256) NOT NULL,
    chart_version   VARCHAR(64) NOT NULL,
    values_encrypted TEXT,
    status          VARCHAR(20) NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending','deployed','failed',
                                      'superseded','uninstalled')),
    revision        INTEGER NOT NULL DEFAULT 1,
    installed_by    UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (cluster_id, release_name, namespace)
);

CREATE TABLE k8s_hpa_rules (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cluster_id      UUID NOT NULL REFERENCES k8s_clusters(id) ON DELETE CASCADE,
    name            VARCHAR(128) NOT NULL,
    target_kind     VARCHAR(32) NOT NULL DEFAULT 'Deployment',
    target_name     VARCHAR(256) NOT NULL,
    namespace       VARCHAR(128) NOT NULL DEFAULT 'default',
    min_replicas    INTEGER NOT NULL DEFAULT 1,
    max_replicas    INTEGER NOT NULL,
    metrics         JSONB NOT NULL,  -- [{type, resource/target}]
    status          VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE k8s_backups (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cluster_id      UUID NOT NULL REFERENCES k8s_clusters(id) ON DELETE CASCADE,
    type            VARCHAR(10) NOT NULL CHECK (type IN ('manual', 'scheduled')),
    status          VARCHAR(20) NOT NULL DEFAULT 'running',
    storage_path    VARCHAR(1024),
    size_bytes      BIGINT,
    includes_resources TEXT[],
    excludes_resources TEXT[],
    started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMPTZ,
    triggered_by    UUID REFERENCES users(id)
);
```

### state machine

```
                ┌──────────────────────────────────────┐
                │                                      │
                ▼                                      │
        ┌──────────────┐                              │
        │ provisioning │                              │
        └──────┬───────┘                              │
               │                                      │
        ┌──────▼───────┐                              │
        │   running    │──────────────────────────┐   │
        └──────┬───────┘                         │   │
               │                                  │   │
     ┌─────────┼─────────┐                       │   │
     │         │         │                       │   │
     ▼         ▼         ▼                       │   │
┌────────┐ ┌────────┐ ┌────────┐                │   │
│upgrad- │ │degraded│ │scaling │                │   │
│ing     │ │        │ │        │                │   │
└───┬────┘ └───┬────┘ └───┬────┘                │   │
    │          │          │                     │   │
    └──────────┼──────────┘                     │   │
               │                                │   │
        ┌──────▼───────┐                        │   │
        │   running    │◀───────────────────────┘   │
        └──────┬───────┘                            │
               │                                    │
        ┌──────▼───────┐                            │
        │   deleting   │                            │
        └──────┬───────┘                            │
               │                                    │
               ▼                                    │
          [deleted]                                 │
               │                                    │
               └────────────────────────────────────┘
```

## service assignments

| component | service | responsibilities |
|---|---|---|
| cluster manager core | **orchestrator agent** | cluster lifecycle, node pool management, helm operations |
| kubectl proxy | **orchestrator agent** | websocket proxy, kubeconfig generation, audit logging |
| metrics bridge | **orchestrator agent** | prometheus auto-deploy, metric scraping, hpa config |
| cluster ui | **management panel** | cluster dashboard, kubectl terminal, chart browser |
| backup controller | **orchestrator agent** | velero integration, backup scheduling, restore workflows |
| notification events | **integration service** | cluster status alerts, backup completion, scaling events |
| gitops sync | **orchestrator agent** (+ feature 16) | config-as-code via git repositories |
| service mesh | **integration service** (+ feature 26) | mtls, traffic splitting for canary deployments |

## effort estimate

| phase | tasks | pt |
|---|---|---|
| phase 1: core provisioning | 1.1–1.5 | 4 |
| phase 2: node pool management | 2.1–2.4 | 2 |
| phase 3: kubectl proxy & panel | 3.1–3.4 | 2 |
| phase 4: helm integration | 4.1–4.4 | 2 |
| phase 5: auto-scaling & monitoring | 5.1–5.4 | 2 |
| phase 6: backup & security | 6.1–6.4 | 1 |
| **total** | **24 tasks** | **13 pt** |

### risk factors

| risk | mitigation |
|---|---|
| k8s version fragmentation across clusters | pin supported versions, automate ugprade testing |
| multi-cloud node provisioning complexity | abstract via cloud provider factory pattern |
| long-running cluster operations (upgrade, backup) | fully async workflows with status streaming |
| security -- kubectl proxy privilege escalation | rbac scoping per user, audit log all commands |
| helm chart compatibility issues | chart validation sandbox, pre-install dry-run |

## monitoring & observability

### prometheus metrics (cluster manager)

```python
# Cluster-level
k8s_clusters_total{status}         # Gauge — cluster count by status
k8s_cluster_provision_duration     # Histogram — time to provision
k8s_cluster_upgrade_duration       # Histogram — upgrade duration

# Node pools
k8s_node_pool_nodes{cluster,pool}  # Gauge — node count per pool
k8s_node_pool_capacity{resource}   # Gauge — allocatable CPU/memory

# Helm
k8s_helm_releases_total{status}    # Counter — releases by status
k8s_helm_install_duration          # Histogram — install time

# Proxy
k8s_proxy_commands_total{action}   # Counter — kubectl commands proxied
k8s_proxy_active_sessions          # Gauge — active proxy connections
```

### logging

```json
{
  "event": "cluster.created",
  "cluster_id": "kc-euprod-7f2a",
  "type": "k3s",
  "version": "v1.30.0+k3s1",
  "duration_ms": 185000,
  "created_by": "usr-abc123"
}
```

## related documents

- [architecture overview](../architecture/overview.md)
- [orchestrator agent architecture](../architecture/orchestrator-agent.md)
- [feature 16: gitops sync](16-gitops-sync.md)
- [feature 26: service mesh](26-service-mesh.md)
- [implementation plan v2](../feature-implementation-plan-v2.md)

**last updated:** may 2026
