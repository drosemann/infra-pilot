# feature 48: container image scanner

- feature id: 48
- status: planned
- priority: high
- primary service: orchestrator agent
- supporting services: integration service, api gateway, notification service
- effort: medium (4-6 pt)
- dependencies: registry integration (docker hub, ecr, gcr, harbor), vulnerability database access

## overview

integrate container image scanning (trivy, snyk, grype) into the image pull / deployment pipeline. each image is scanned for cves before deployment. results include severity scoring, fix versions, and auto-remediation via pull request. policy enforcement blocks deployments containing critical cves.

## architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Registry (Docker Hub / ECR / GCR / Harbor)                             │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Image: myapp:v1.2.3                                            │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Image pull / push
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     Orchestrator Agent                                   │
│                                                                          │
│  ┌─────────────────┐   ┌─────────────────┐   ┌──────────────────────┐   │
│  │ Image Puller     │   │ Scanner Engine   │   │ Policy Enforcer      │   │
│  │ • Pull manifest  │──▶│ • Trivy          │──▶│ • Severity rules     │   │
│  │ • Resolve digest │   │ • Grype          │   │ • Block critical CVEs│   │
│  │ • Cache layer    │   │ • Snyk (API)     │   │ • Allowlist mgmt     │   │
│  └─────────────────┘   └────────┬─────────┘   └──────────────────────┘   │
└─────────────────────────────────┼────────────────────────────────────────┘
                                  │
                    ┌─────────────┼──────────────┐
                    │             │              │
                    ▼             ▼              ▼
┌─────────────────┐  ┌─────────────────┐  ┌──────────────────────────┐
│ CVE Database     │  │ Report Store     │  │ Remediation Engine       │
│ • Local cache    │  │ • Scan results   │  │ • Auto-create PR         │
│ • Daily updates  │  │ • Historical     │  │ • Suggest fix version    │
│ • NVD / GHSA     │  │ • Trend analysis │  │ • Update Dockerfile      │
└─────────────────┘  └─────────────────┘  └──────────────────────────┘
```

**data flow:**

• trigger — scanning is triggered on image push to registry, pre-deployment, or on a schedule (re-scan).
• pull & digest — the orchestrator agent pulls the image manifest and resolves the digest for cache-busting.
• scan — the scanner engine runs trivy (and optionally grype/snyk) against the image. results are normalized into a standard cve format.
• policy evaluation — the policy enforcer checks each finding against severity rules. critical cves without an exception cause the deployment to be blocked.
• reporting — results are stored in the report store. notifications are sent via slack/email/webhook.
• remediation — for fixable cves, the remediation engine can create a pr that updates base images or applies patches.

## implementation plan

### phase 1 — scanning foundation (2 pt)
| step | description |
|------|-------------|
| 1.1  | integrate trivy as the primary scanner (go library / cli) |
| 1.2  | normalize scan results into a unified cve schema |
| 1.3  | implement cve database cache with daily sync from nvd/ghsa |
| 1.4  | add scan trigger on image push (registry webhook) |

### phase 2 — policy engine (1.5 pt)
| step | description |
|------|-------------|
| 2.1  | policy engine with yaml-based severity rules |
| 2.2  | enforce "block on critical cve" by default |
| 2.3  | allowlist management (waived cves with expiry) |
| 2.4  | integration with deployment pipeline (fail on policy violation) |

### phase 3 — reporting & remediation (1.5 pt)
| step | description |
|------|-------------|
| 3.1  | scan report storage (postgres / s3) with historical tracking |
| 3.2  | notification integration (slack, email, webhook) |
| 3.3  | remediation engine — pr creation with fix version suggestions |
| 3.4  | trend dashboard api (cve counts over time, fix rate) |

### phase 4 — advanced scanning (1 pt)
| step | description |
|------|-------------|
| 4.1  | add grype as secondary scanner for cross-validation |
| 4.2  | add snyk api integration (license compliance, sast) |
| 4.3  | multi-architecture image scanning (arm64, amd64) |
| 4.4  | sbom generation (cyclonedx / spdx) |

## api design

### scans

```
POST   /api/v1/scans                          → Trigger a scan
  Body: { image: "myapp:v1.2.3", registry: "dockerhub" }

GET    /api/v1/scans                          → List scan results
GET    /api/v1/scans/{id}                     → Scan detail + CVE list
GET    /api/v1/scans/{id}/summary             → Summary counts by severity
```

### policies

```
GET    /api/v1/policies                       → List scan policies
POST   /api/v1/policies                       → Create / update policy
DELETE /api/v1/policies/{id}                  → Remove policy
GET    /api/v1/policies/{id}/evaluate?image=  → Dry-run evaluation
```

### allowlist

```
GET    /api/v1/allowlist                      → List waived CVEs
POST   /api/v1/allowlist                      → Add CVE waiver
  Body: { cve_id, reason, expires_at }

DELETE /api/v1/allowlist/{id}
```

### remediation

```
POST   /api/v1/remediations                   → Auto-create remediation PR
  Body: { scan_id, cve_ids: ["CVE-2026-1234"] }

GET    /api/v1/remediations                   → List PRs created
```

### example: trigger scan

```json
POST /api/v1/scans
{
  "image": "ghcr.io/myorg/api-gateway:v2.5.1",
  "registry_credentials": {
    "type": "ghcr",
    "token_name": "SCAN_TOKEN"
  },
  "scanners": ["trivy", "grype"]
}

Response 201:
{
  "scan_id": "scan_abc123",
  "image": "ghcr.io/myorg/api-gateway:v2.5.1",
  "digest": "sha256:a1b2c3d4...",
  "status": "scanning",
  "created_at": "2026-05-27T10:30:00Z"
}
```

### example: policy evaluation result

```json
{
  "scan_id": "scan_abc123",
  "image": "ghcr.io/myorg/api-gateway:v2.5.1",
  "policy": "default-strict",
  "evaluated_at": "2026-05-27T10:31:00Z",
  "action": "block",
  "summary": {
    "total": 12,
    "critical": 2,
    "high": 4,
    "medium": 4,
    "low": 2
  },
  "blocking_cves": [
    {
      "cve_id": "CVE-2026-1234",
      "severity": "critical",
      "package": "libssl3",
      "installed_version": "3.0.12",
      "fixed_version": "3.0.14",
      "description": "Buffer overflow in TLS handshake"
    }
  ],
  "remediation_suggestions": [
    {
      "type": "base_image_update",
      "current": "ubuntu:22.04",
      "suggested": "ubuntu:22.04-20260526"
    }
  ]
}
```

## data model

### scan

```yaml
Scan:
  id: string (uuid)
  image: string                             # "myapp:v1.2.3"
  digest: string                            # sha256:...
  registry: string                          # "dockerhub" | "ecr" | "ghcr"
  scanners: list<string>                    # ["trivy", "grype"]
  status: string                            # "pending" | "scanning" | "completed" | "failed"
  summary:
    critical: integer
    high: integer
    medium: integer
    low: integer
    unknown: integer
  created_at: timestamp
  completed_at: timestamp
```

### vulnerability

```yaml
Vulnerability:
  id: string (uuid)
  scan_id: string
  cve_id: string                            # "CVE-2026-1234"
  severity: string                          # "CRITICAL" | "HIGH" | "MEDIUM" | "LOW"
  score: float                              # CVSS v3 score 0.0-10.0
  package_name: string
  installed_version: string
  fixed_version: string                     # null if no fix available
  status: string                            # "fixed" | "will_not_fix" | "unknown"
  description: string
  cvss_vector: string                       # "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"
  cwe_ids: list<string>
  exploit_available: boolean
  references: list<string>
```

### policy

```yaml
Policy:
  id: string (uuid)
  name: string                              # "default-strict"
  rules:
    - severity: "CRITICAL"
      action: "block"
      exceptions:
        - package: "openssl"
          max_score: 9.0
    - severity: "HIGH"
      action: "warn"
    - severity: "MEDIUM"
      action: "allow"
    - severity: "LOW"
      action: "allow"
  default_action: "allow"
  created_at: timestamp
  updated_at: timestamp
```

### allowlist entry (waiver)

```yaml
AllowlistEntry:
  id: string (uuid)
  cve_id: string
  reason: string
  waived_by: string
  expires_at: timestamp
  created_at: timestamp
```

### remediation pr

```yaml
RemediationPR:
  id: string (uuid)
  scan_id: string
  cve_ids: list<string>
  pr_url: string                            # GitHub/GitLab PR link
  pr_status: string                         # "open" | "merged" | "closed"
  base_image_update: object
  package_updates: list<object>
  created_at: timestamp
```

## service assignments

| service | responsibility |
|---------|---------------|
| **orchestrator agent** | primary service — image pulling, scanner engine, policy enforcer, remediation pr creation |
| **integration service** | cve database sync (nvd/ghsa), notification dispatch, trend analytics api |
| **api gateway** | route /api/v1/scans/* and /api/v1/policies/*, authenticate developers |
| **notification service** | slack / email / webhook delivery on policy violations |
| **compliance (feature 46)** | consume scan results as evidence for soc 2 cc6.1 (patching) and cc7.1 (vulnerability management) |

## effort estimate

| phase | pt | dependencies |
|-------|----|--------------|
| scanning foundation | 2 | trivy integration, cve database, push-trigger |
| policy engine | 1.5 | severity rules, deployment blocking, allowlist |
| reporting & remediation | 1.5 | reports, notifications, auto-pr creation |
| advanced scanning | 1 | grype/snyk, multi-arch, sbom |
| **total** | **6** | ranges 4-6 depending on number of scanners integrated |

## open questions

• should we support on-premise registries (harbor, nexus) with air-gapped cve databases?
• what is the sla for cve database freshness (4h / 12h / 24h)?
• how do we handle images with no known cve database (distroless, scratch)?
• should the auto-remediation pr be auto-merged on low-severity findings?
• do we need integration with external ticketing systems (jira, linear) for critical cves?
• what is the strategy for handling false positives (noise reduction)?
