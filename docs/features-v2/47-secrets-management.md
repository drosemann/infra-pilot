# feature 47: secrets management

- feature id: 47
- status: planned
- priority: critical
- primary service: integration service
- supporting services: orchestrator agent, api gateway, auth service
- effort: medium (4-6 pt)
- dependencies: auth service (rbac), orchestrator agent (container injection)

## overview

integrate hashicorp vault as the central secrets backend. provide dynamic secrets (short-lived credentials), automated database credential rotation, and encrypted environment variable injection into containers at deployment time. all secret access is audited.

## architecture

```
                               ┌──────────────────────┐
                               │   HashiCorp Vault     │
                               │  ┌──────────────────┐ │
                               │  │ Transit Engine    │ │
                               │  │ KV Engine         │ │
                               │  │ Database Engine   │ │
                               │  │ PKI Engine        │ │
                               │  └──────────────────┘ │
                               └──────────┬───────────┘
                                          │
┌─────────────────────────────────────────┼──────────────────────────┐
│            Integration Service          │                           │
│  ┌──────────────────────┐  ┌───────────▼──────────┐              │
│  │  Vault Client SDK    │  │  Rotation Manager     │              │
│  │  • Token/Auth        │  │  • Schedule & detect   │              │
│  │  • Lease management  │  │  • Force rotation      │              │
│  │  • Dynamic secrets   │  │  • Notify consumers    │              │
│  └──────────────────────┘  └───────────────────────┘              │
│  ┌──────────────────────┐  ┌───────────────────────┐              │
│  │  Env Injection API   │  │  Audit Logger          │              │
│  │  • Encrypt env vars  │  │  • All access logged   │              │
│  │  • Container attach  │  │  • Immutable audit     │              │
│  │  • Sidecar inject    │  │  • SIEM export         │              │
│  └──────────────────────┘  └───────────────────────┘              │
└────────────────────────────────────────────────────────────────────┘
           │                              │
           ▼                              ▼
┌──────────────────────┐    ┌────────────────────────────┐
│  Orchestrator Agent   │    │     External Systems        │
│  • Inject secrets     │    │  • Databases (Postgres,    │
│  • Sidecar container  │    │    MySQL, MongoDB)          │
│  • Rotate on deploy   │    │  • Cloud APIs (AWS, GCP)   │
│  • Cleanup leases     │    │  • SMTP / LDAP             │
└──────────────────────┘    └────────────────────────────┘
```

**data flow:**

• authentication — integration service authenticates to vault using kubernetes service account jwt (or approle). a short-lived vault token is issued.
• dynamic secret request — when a deployment is created, the integration service requests dynamic credentials from vault (e.g., database user with a 24h ttl).
• rotation — the rotation manager monitors credential ttl. when a secret is 25% from expiry, a rotation is triggered: new credentials are issued, the old ones are revoked after a cooldown window.
• injection — secrets are encrypted with the vault transit engine and injected into the deployment manifest as environment variables or volume mounts via a sidecar.
• audit — every secret access is logged to the audit store. logs include requester identity, secret path, operation type, and timestamp.

## implementation plan

### phase 1 — vault integration (2 pt)
| step | description |
|------|-------------|
| 1.1  | deploy vault cluster (ha mode with raft backend) |
| 1.2  | implement vault client sdk wrapper (auth, crud, lease mgmt) |
| 1.3  | set up kubernetes auth method for pod-level authentication |
| 1.4  | create kv engine for static secrets migration |

### phase 2 — dynamic secrets (1.5 pt)
| step | description |
|------|-------------|
| 2.1  | configure vault database engine for postgres & mysql |
| 2.2  | implement dynamic secret request api |
| 2.3  | add lease lifecycle management (renew, revoke) |

### phase 3 — rotation (1 pt)
| step | description |
|------|-------------|
| 3.1  | rotation manager — schedule-based and event-based triggers |
| 3.2  | database credential rotation with connection draining |
| 3.3  | rotation notification webhook |

### phase 4 — injection & audit (1.5 pt)
| step | description |
|------|-------------|
| 4.1  | encrypted env injection via kubernetes mutation webhook |
| 4.2  | vault agent sidecar injector |
| 4.3  | audit log pipeline (vault audit → kafka → s3 / siem) |
| 4.4  | access control policies (path-based rbac) |

## api design

### secret operations

```
POST   /api/v1/secrets                   → Create / store a static secret
GET    /api/v1/secrets/{path}            → Read secret (audited)
PUT    /api/v1/secrets/{path}            → Update secret
DELETE /api/v1/secrets/{path}            → Delete / revoke secret
POST   /api/v1/secrets/{path}/rotate     → Force rotation
```

### dynamic secrets

```
POST   /api/v1/secrets/dynamic           → Request dynamic credentials
  Body: { engine: "database"|"aws"|"pki", ttl: "24h", role: "readonly" }

POST   /api/v1/secrets/dynamic/{id}/renew    → Renew lease
POST   /api/v1/secrets/dynamic/{id}/revoke   → Revoke immediately
```

### injection

```
POST   /api/v1/secrets/inject            → Inject secrets into deployment manifest
  Body: { deployment_id, secrets: [{ path, env_var }] }
```

### audit

```
GET    /api/v1/secrets/audit             → Query audit log
  Params: secret_path, user_id, start_date, end_date, page, limit
```

### example: request dynamic database credentials

```json
POST /api/v1/secrets/dynamic
{
  "engine": "database",
  "role": "app_readwrite",
  "ttl": "24h",
  "metadata": {
    "app_id": "user-service",
    "environment": "production"
  }
}

Response 201:
{
  "lease_id": "db/app_readwrite/a1b2c3d4",
  "credentials": {
    "username": "v-app-uuid-abc123",
    "password": "********",
    "host": "postgres-primary.internal:5432",
    "database": "app_production"
  },
  "lease_duration": "24h",
  "renewable": true,
  "expires_at": "2026-05-28T12:00:00Z"
}
```

## data model

### secret

```yaml
Secret:
  path: string                            # "kv/app/production/db-password"
  type: string                            # "static" | "dynamic" | "pki"
  engine: string                          # "kv-v2" | "database" | "transit" | "pki"
  metadata:
    created_by: string
    rotation_policy: string               # "never" | "30d" | "90d"
    last_rotated: timestamp
  version: integer
  created_at: timestamp
  updated_at: timestamp
```

### lease

```yaml
Lease:
  id: string                              # Vault lease ID
  secret_path: string
  type: string                            # "database" | "aws" | "pki"
  ttl: duration
  renewable: boolean
  issued_at: timestamp
  expires_at: timestamp
  last_renewed_at: timestamp
  status: string                          # "active" | "expiring" | "revoked"
```

### audit entry

```yaml
AuditEntry:
  id: string (uuid)
  timestamp: timestamp
  user_id: string
  service_account: string
  secret_path: string
  operation: string                       # "read" | "write" | "delete" | "rotate" | "renew"
  allowed: boolean
  client_ip: string
  request_id: string
  metadata: object
```

### rotation policy

```yaml
RotationPolicy:
  id: string (uuid)
  secret_path_pattern: string             # "db/*/production/*"
  schedule: string                        # "0 0 */30 * *" (cron) or "75%"
  max_ttl: duration
  cooldown: duration                       # Grace period before revoking old creds
  notify_on_rotation: list<string>        # Email/webhook targets
```

## service assignments

| service | responsibility |
|---------|---------------|
| **integration service** | vault client sdk, dynamic secret lifecycle, rotation manager, audit logging |
| **orchestrator agent** | vault sidecar injector, kubernetes mutatingwebhookconfiguration for env injection |
| **api gateway** | route /api/v1/secrets/*, enforce mtls between services and vault |
| **auth service** | vault kubernetes auth integration, path-based access policies |
| **compliance (feature 46)** | consume audit logs for soc 2 cc6.1 (logical and physical access control) evidence |

## effort estimate

| phase | pt | dependencies |
|-------|----|--------------|
| vault integration | 2 | cluster deployment, client sdk, auth methods |
| dynamic secrets | 1.5 | database engine, lease lifecycle |
| rotation | 1 | rotation manager, connection draining |
| injection & audit | 1.5 | webhook injector, audit pipeline |
| **total** | **6** | ranges 4-6 depending on vault ha complexity |

## open questions

• should we support cloud-native secret stores (aws secrets manager / gcp secret manager) as a fallback?
• what is the strategy for vault unsealing in production (auto-unseal with kms vs shamir)?
• how do we handle cross-cluster secret replication for dr?
• should the rotation manager force rotation on security incidents (e.g., credential leak)?
• what is the performance impact of the mutatingwebhook on deployment latency?
