# feature 46: compliance framework reports

- feature id: 46
- status: planned
- priority: high
- primary service: integration service
- supporting services: orchestrator agent, api gateway, auth service
- effort: large (7-10 pt)
- dependencies: feature 47 (secrets management), feature 48 (container image scanner)

## overview

generate auditor-ready compliance reports for soc 2, hipaa, and pci-dss frameworks. the system continuously collects evidence from infrastructure, maps controls to framework requirements, and produces exportable reports (pdf, html, json) suitable for external auditors.

## architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        API Gateway                               │
│  POST /api/v1/compliance/reports  GET /api/v1/compliance/...     │
└──────────┬───────────────────────────────────────────────────────┘
           │
┌──────────▼───────────────────────────────────────────────────────┐
│                    Integration Service                            │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐  │
│  │ Framework Engine  │  │ Evidence Manager  │  │ Report Builder  │  │
│  │  • SOC 2          │  │  • Collectors     │  │  • Templates    │  │
│  │  • HIPAA          │  │  • Timestamps     │  │  • PDF/HTML     │  │
│  │  • PCI-DSS        │  │  • Integrity hash │  │  • JSON export  │  │
│  └────────┬─────────┘  └────────┬──────────┘  └────────┬───────┘  │
└──────────┬──────────────────────┬──────────────────────┬──────────┘
           │                      │                      │
           ▼                      ▼                      ▼
┌───────────────────┐  ┌───────────────────┐  ┌────────────────────┐
│  Control Mapper    │  │  Evidence Store   │  │  Report Store      │
│  • Control→Evidence│  │  • Immutable log  │  │  • Generated docs  │
│  • Gap detection   │  │  • Retention 7yr  │  │  • Signed PDFs     │
│  • Remediation     │  │  • Encrypted at   │  │  • Auditor portal  │
│    tracking        │  │    rest           │  │    (future)        │
└───────────────────┘  └───────────────────┘  └────────────────────┘
```

**data flow:**

• evidence collection — collectors run on a schedule (cron / event-driven) and gather evidence from cloud apis, kubernetes audit logs, container scan results, iam policies, network configurations, and backup logs.
• control mapping — the control mapper matches collected evidence against framework control requirements. each control is linked to one or more evidence items.
• gap analysis — unmapped or failing controls are flagged. remediation tickets can be auto-created.
• report generation — templates are hydrated with evidence and control status. reports are timestamped, hashed, and signed.
• export — reports are made available for download in pdf, html, and json formats.

## implementation plan

### phase 1 — foundation (3 pt)
| step | description |
|------|-------------|
| 1.1  | define framework data models (controls, evidence items, mappings) |
| 1.2  | implement evidence store with append-only log semantics |
| 1.3  | implement control mapper with pluggable framework definitions |
| 1.4  | add evidence collection framework with cron trigger support |

### phase 2 — framework coverage (2 pt)
| step | description |
|------|-------------|
| 2.1  | soc 2 control definitions (security, availability, confidentiality) |
| 2.2  | hipaa control definitions (administrative, physical, technical safeguards) |
| 2.3  | pci-dss control definitions (12 requirements mapped to evidence) |

### phase 3 — reporting & export (2 pt)
| step | description |
|------|-------------|
| 3.1  | report builder with templating engine (handlebars/liquid) |
| 3.2  | pdf generation (wkhtmltopdf / puppeteer) |
| 3.3  | json export for siem integration |
| 3.4  | report digital signing and integrity verification |

### phase 4 — continuous monitoring (2 pt)
| step | description |
|------|-------------|
| 4.1  | real-time evidence stream (kafka / nats) |
| 4.2  | automated gap detection alerts |
| 4.3  | compliance dashboard api |
| 4.4  | remediation workflow integration |

## api design

### frameworks

```
GET    /api/v1/compliance/frameworks              → List all frameworks
GET    /api/v1/compliance/frameworks/{id}         → Framework details + controls
POST   /api/v1/compliance/frameworks              → Register custom framework
```

### evidence

```
GET    /api/v1/compliance/evidence                → List evidence items
GET    /api/v1/compliance/evidence/{id}           → Evidence detail + integrity hash
POST   /api/v1/compliance/evidence                → Submit evidence (from collectors)
DELETE /api/v1/compliance/evidence/{id}           → Soft-delete (admin only)
```

### reports

```
POST   /api/v1/compliance/reports                 → Generate report
  Body: { framework_id, start_date, end_date, format: "pdf"|"html"|"json" }

GET    /api/v1/compliance/reports                 → List generated reports
GET    /api/v1/compliance/reports/{id}            → Report metadata + download URL
GET    /api/v1/compliance/reports/{id}/download   → Download report file
DELETE /api/v1/compliance/reports/{id}            → Archive report
```

### dashboard / monitoring

```
GET    /api/v1/compliance/dashboard               → Compliance scores per framework
GET    /api/v1/compliance/gaps                    → Current control gaps
```

### example: generate report

```json
POST /api/v1/compliance/reports
{
  "framework_id": "soc2_type2",
  "start_date": "2026-01-01T00:00:00Z",
  "end_date": "2026-06-30T23:59:59Z",
  "format": "pdf",
  "include_evidence": true,
  "sign": true
}

Response 201:
{
  "report_id": "rpt_a1b2c3d4",
  "framework": "soc2_type2",
  "status": "generating",
  "download_url": "/api/v1/compliance/reports/rpt_a1b2c3d4/download",
  "expires_at": "2026-07-31T23:59:59Z"
}
```

## data model

### framework

```yaml
Framework:
  id: string (uuid)
  name: string                          # "SOC 2 Type II"
  slug: string                          # "soc2_type2"
  version: string                       # "2025"
  controls: list<Control>
  created_at: timestamp
  updated_at: timestamp
```

### control

```yaml
Control:
  id: string (uuid)
  framework_id: string
  control_id: string                    # "CC6.1", "HIPAA.164.312(a)(1)"
  title: string
  description: string
  category: string                      # "Security" | "Availability" | "Confidentiality" | ...
  risk_level: string                    # "critical" | "high" | "medium" | "low"
  evidence_requirements: list<string>   # Evidence types that satisfy this control
```

### evidence

```yaml
Evidence:
  id: string (uuid)
  type: string                          # "audit_log" | "scan_result" | "iam_policy" | ...
  source: string                        # "kubernetes" | "aws_cloudtrail" | "vault" | ...
  collected_at: timestamp
  content_hash: string                  # SHA-256 of raw content
  raw_content: object                   # JSON blob
  retained_until: timestamp             # 7-year retention for PCI-DSS
```

### report

```yaml
Report:
  id: string (uuid)
  framework_id: string
  period_start: timestamp
  period_end: timestamp
  format: string                        # "pdf" | "html" | "json"
  status: string                        # "generating" | "ready" | "expired"
  evidence_count: integer
  control_summary:
    passed: integer
    failed: integer
    not_audited: integer
  download_url: string
  signed_by: string                     # Certificate fingerprint
  signed_at: timestamp
  created_at: timestamp
  expires_at: timestamp
```

## service assignments

| service | responsibility |
|---------|---------------|
| **integration service** | framework engine, evidence collection orchestration, control mapper, report builder |
| **orchestrator agent** | collect infrastructure-level evidence (k8s audit logs, container scan results, network policies) |
| **api gateway** | route /api/v1/compliance/*, enforce auth, rate-limit report generation |
| **auth service** | validate access tokens, enforce rbac (compliance_viewer, compliance_admin roles) |
| **secrets (feature 47)** | store evidence collector api keys, signing certificates |

## effort estimate

| phase | pt | dependencies |
|-------|----|--------------|
| foundation | 3 | data models, evidence store, collector framework |
| framework coverage | 2 | soc 2, hipaa, pci-dss control definitions |
| reporting & export | 2 | pdf/html/json generation, digital signing |
| continuous monitoring | 2 | real-time streams, gap alerts, dashboard api |
| **total** | **9** | ranges 7-10 depending on framework depth |

## open questions

• should evidence be stored in immutable object storage (s3/gcs) or a database?
• what is the retention policy for intermediate evidence vs. final reports?
• do we need support for custom (user-defined) frameworks beyond soc 2 / hipaa / pci-dss?
• should report signing use an internal ca or integrate with external kms?
• what is the acceptable latency for report generation (synchronous vs. async)?
