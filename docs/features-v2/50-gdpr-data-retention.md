# gdpr & data retention

- feature id: 50
- category: security & compliance
- primary service: integration service
- effort estimate: medium (4-6 pt)
- status: planned

## overview

implement a comprehensive data lifecycle management system that ensures compliance with the general data protection regulation (gdpr) and similar privacy frameworks. the system manages automated data retention policies, right-to-erasure (article 17) workflows, data inventory exports (article 30), and consent management across all infra pilot services.

all personally identifiable information (pii) stored within the platform — including user profiles, audit logs, billing records, and support tickets — is classified, tagged, and subject to configurable lifecycle policies.

### goals

• auto-purge logs and records older than configurable retention periods
• provide a fully auditable right-to-erasure workflow (forget me)
• generate gdpr article 30 data inventory exports in machine-readable format
• classify all stored data by pii sensitivity level
• manage user consent records for data processing activities
• generate data processing agreement (dpa) documents on demand
• maintain a tamper-proof audit trail for all data lifecycle operations

## architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                        Infra Pilot Platform                           │
│                                                                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────┐  │
│  │  User     │  │  Audit   │  │  Billing  │  │  Support  │  │ Tele- │  │
│  │  Profiles │  │  Logs    │  │  Records  │  │  Tickets  │  │ metry │  │
│  └─────┬────┘  └─────┬────┘  └─────┬────┘  └─────┬────┘  └───┬───┘  │
│        │              │              │              │            │     │
│        ▼              ▼              ▼              ▼            ▼     │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │                  Integration Service                           │    │
│  │                                                               │    │
│  │  ┌────────────────────────────────────────────────────────┐  │    │
│  │  │              Data Lifecycle Engine                      │  │    │
│  │  │                                                         │  │    │
│  │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │  │    │
│  │  │  │ Data         │  │ Retention    │  │ Purge        │ │  │    │
│  │  │  │ Classifier   │──│ Policy Engine│──│ Executor     │ │  │    │
│  │  │  └──────────────┘  └──────────────┘  └──────┬───────┘ │  │    │
│  │  │                                              │         │  │    │
│  │  │  ┌──────────────┐  ┌──────────────┐  ┌──────┴───────┐ │  │    │
│  │  │  │ Right-to-    │  │ Consent      │  │ Data         │ │  │    │
│  │  │  │ Erasure      │──│ Manager      │  │ Inventory    │ │  │    │
│  │  │  │ Workflow     │  │              │  │ Export       │ │  │    │
│  │  │  └──────────────┘  └──────────────┘  └──────────────┘ │  │    │
│  │  └────────────────────────────────────────────────────────┘  │    │
│  │                               │                               │    │
│  │                               ▼                               │    │
│  │  ┌────────────────────────────────────────────────────────┐  │    │
│  │  │               DPA Generator                             │  │    │
│  │  │  Template engine → GDPR-compliant PDF + Markdown       │  │    │
│  │  └────────────────────────────────────────────────────────┘  │    │
│  │                                                               │    │
│  │  ┌────────────────────────────────────────────────────────┐  │    │
│  │  │               Audit Trail                               │  │    │
│  │  │  Immutable log of all purge / erasure / consent events │  │    │
│  │  └────────────────────────────────────────────────────────┘  │    │
│  └──────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────┘
```

## implementation plan

### phase 1: data classification & policy engine (2 pt)

| step | description | artifacts |
|------|-------------|-----------|
| 1.1 | pii classification schema across all services | `internal/gdpr/classifier.go` — scan database schemas, tag columns by pii category |
| 1.2 | retention policy definition & storage | `internal/gdpr/policy.go` — yaml-driven retention rules per data category |
| 1.3 | policy engine (evaluate + schedule) | `internal/gdpr/engine.go` — cron-driven evaluation, schedules purge jobs |
| 1.4 | metadata registry for tracked data locations | `internal/gdpr/registry.go` — tracks database tables, columns, object storage paths |

**pii classification levels:**

| level | label | examples | retention default |
|-------|-------|----------|------------------|
| l0 | none | system metrics, anonymised aggregates | indefinite |
| l1 | internal | email addresses, usernames | 3 years |
| l2 | sensitive | ip addresses, user-agent strings | 1 year |
| l3 | critical | payment tokens, passwords (hashed), government ids | 90 days (or legal minimum) |

**retention policy definition:**

```yaml
# config/data_retention.yaml
retention_policies:
  - category: "user.profile"
    pii_level: L1
    default_days: 1095        # 3 years
    legal_hold: true           # preserve if legal hold active
    purge_action: "anonymize"  # anonymize | delete | archive
    services:
      - integration
      - panel

  - category: "audit.logs"
    pii_level: L2
    default_days: 365
    legal_hold: true
    purge_action: "delete"
    services:
      - integration
      - orchestrator

  - category: "billing.invoices"
    pii_level: L1
    default_days: 2555        # 7 years (tax requirement)
    legal_hold: true
    purge_action: "archive"
    services:
      - billing

  - category: "support.tickets"
    pii_level: L2
    default_days: 730         # 2 years
    legal_hold: true
    purge_action: "anonymize"
    services:
      - support

  - category: "telemetry.session"
    pii_level: L3
    default_days: 90
    legal_hold: false
    purge_action: "delete"
    services:
      - integration

  - category: "consent.records"
    pii_level: L1
    default_days: -1          # -1 = permanent (legal requirement)
    legal_hold: true
    purge_action: "none"
    services:
      - integration
```

### phase 2: purge executor & right-to-erasure (1.5 pt)

| step | description | artifacts |
|------|-------------|-----------|
| 2.1 | purge executor service | `internal/gdpr/purge.go` — executes delete/anonymize/archive across all services |
| 2.2 | anonymization engine | `internal/gdpr/anonymize.go` — field-level masking, hashing, aggregation |
| 2.3 | archive storage backend | cold storage (s3/blob) with encryption-at-rest |
| 2.4 | right-to-erasure workflow | `internal/gdpr/erasure.go` — multi-step verification + execution |
| 2.5 | erasure request api | `post /api/v1/gdpr/erasure` — submit + track erasure requests |

**anonymization strategies:**

```python
# pseudocode: anonymize.py
def anonymize_field(value: str, strategy: str) -> str:
    strategies = {
        "mask": value[0] + "*" * (len(value) - 2) + value[-1] if len(value) > 2 else "***",
        "hash": hashlib.sha256(value.encode()).hexdigest(),
        "truncate": value[:4] + "…",
        "redact": "[REDACTED]",
        "aggregate": bucket_into_range(value),  # e.g. age → 25-30
        "tokenize": vault_tokenize(value),       # vault-backed tokenization
    }
    return strategies.get(strategy, "[REDACTED]")
```

**right-to-erasure flow:**

```
User Request          Verification          Execution              Confirmation
─────────────         ─────────────         ─────────               ───────────
                                                    ┌──────────┐
User submits             Verify identity           │  Search   │
erasure request  ───►  (email link / 2FA)  ───►  │  all PII  │───► Summary shown to user
via Panel / API                                    │  stores   │
                                                    └──────────┘
                                                         │
                                                    ┌──────────┐
                    User confirms                   │ Execute  │
                    intention         ◄──────────  │ purge &  │
                    (72h cool-down)                │ anonymize│
                                                    └──────────┘
                                                         │
                                                    ┌──────────┐
                     Erasure complete               │ Audit log│
                     Email confirmation  ◄────────  │ notify   │
                                                    │ user     │
                                                    └──────────┘
```

### phase 3: data inventory, consent & dpa (0.5-1 pt)

| step | description | artifacts |
|------|-------------|-----------|
| 3.1 | data inventory scanner | `internal/gdpr/inventory.go` — scans all connected data stores |
| 3.2 | gdpr article 30 export | `internal/gdpr/report.go` — generates csv/json/pdf inventory report |
| 3.3 | consent management crud | `internal/gdpr/consent.go` — record + version user consent for processing purposes |
| 3.4 | dpa template & generator | `internal/gdpr/dpa.go` — fills organisation details into gdpr-compliant dpa template |
| 3.5 | expiry notification service | automated alerts to admins before retention periods elapse |

## api design

### data retention rules

#### list retention policies

```
GET /api/v1/gdpr/retention-policies
```

response:
```json
{
  "policies": [
    {
      "category": "user.profile",
      "pii_level": "L1",
      "default_days": 1095,
      "purge_action": "anonymize",
      "legal_hold_enabled": true,
      "affected_services": ["integration", "panel"],
      "estimated_next_purge": "2026-08-15T02:00:00Z",
      "total_records_marked": 14253
    }
  ]
}
```

#### update retention policy

```
PATCH /api/v1/gdpr/retention-policies/{category}
```

request:
```json
{
  "default_days": 730,
  "purge_action": "delete",
  "legal_hold_enabled": false
}
```

#### trigger manual purge

```
POST /api/v1/gdpr/retention-policies/{category}/purge
```

response:
```json
{
  "job_id": "purge-20260527-a1b2c3",
  "category": "audit.logs",
  "records_affected": 45200,
  "estimated_duration_seconds": 120,
  "status": "running"
}
```

### right-to-erasure

#### submit erasure request

```
POST /api/v1/gdpr/erasure
```

request:
```json
{
  "user_id": "user-789",
  "verification_method": "email_link",
  "reason": "Data no longer necessary for processing purposes",
  "requested_by": "user-789"
}
```

response: `201 Created`
```json
{
  "request_id": "erasure-20260527-xyz789",
  "status": "pending_verification",
  "verification_url": "https://panel.example.com/gdpr/erasure/verify/xyz789",
  "cool_down_expires": "2026-05-30T14:30:00Z",
  "created_at": "2026-05-27T14:30:00Z"
}
```

#### verify erasure request

```
POST /api/v1/gdpr/erasure/{request_id}/verify
```

request:
```json
{
  "verification_token": "abc123def456"
}
```

response:
```json
{
  "request_id": "erasure-20260527-xyz789",
  "status": "pending_confirmation",
  "summary": {
    "total_records_found": 342,
    "categories": [
      {"category": "user.profile", "records": 1, "action": "anonymize"},
      {"category": "audit.logs", "records": 280, "action": "delete"},
      {"category": "billing.invoices", "records": 12, "action": "anonymize"},
      {"category": "support.tickets", "records": 49, "action": "anonymize"}
    ]
  }
}
```

#### confirm erasure

```
POST /api/v1/gdpr/erasure/{request_id}/confirm
```

response:
```json
{
  "request_id": "erasure-20260527-xyz789",
  "status": "executing",
  "job_id": "purge-erasure-xyz789",
  "estimated_completion": "2026-05-27T14:35:00Z"
}
```

#### get erasure status

```
GET /api/v1/gdpr/erasure/{request_id}
```

#### list erasure requests (admin)

```
GET /api/v1/gdpr/erasure?status=completed&from=2026-01-01&limit=50
```

### data inventory

#### generate inventory report

```
POST /api/v1/gdpr/inventory/export
```

request:
```json
{
  "format": "csv",
  "include_sample_data": false,
  "sections": ["databases", "object_storage", "backups", "third_party"]
}
```

response: `200 OK` (file download)

**sample csv output:**

```csv
category,service,table,column,pii_level,purge_action,retention_days,record_count
user.profile,panel,users,email,L1,anonymize,1095,12500
user.profile,panel,users,full_name,L1,anonymize,1095,12500
audit.logs,integration,log_events,ip_address,L2,delete,365,2840000
audit.logs,integration,log_events,user_agent,L2,delete,365,2840000
billing.invoices,billing,invoices,card_last_four,L3,archive,2555,48000
support.tickets,support,tickets,message_body,L2,anonymize,730,89000
consent.records,integration,consents,all,L1,none,-1,12500
```

### consent management

#### record consent

```
POST /api/v1/gdpr/consent
```

request:
```json
{
  "user_id": "user-789",
  "purposes": [
    {
      "purpose": "service_operations",
      "granted": true,
      "version": "2.1"
    },
    {
      "purpose": "marketing_communications",
      "granted": false,
      "version": "1.0"
    },
    {
      "purpose": "third_party_sharing",
      "granted": false,
      "version": "1.0"
    }
  ],
  "ip_address": "203.0.113.42",
  "user_agent": "Mozilla/5.0 ..."
}
```

#### get consent record

```
GET /api/v1/gdpr/consent/{user_id}
```

#### get consent history

```
GET /api/v1/gdpr/consent/{user_id}/history
```

### dpa generation

#### generate dpa

```
POST /api/v1/gdpr/dpa/generate
```

request:
```json
{
  "organisation_name": "ACME Corp GmbH",
  "organisation_address": "Musterstr. 42, 60329 Frankfurt, Germany",
  "representative_name": "Jane Doe",
  "representative_email": "jane.doe@acme.com",
  "data_categories": [
    "identity_data",
    "contact_data",
    "usage_data",
    "billing_data"
  ],
  "processing_purposes": [
    "service_provision",
    "billing",
    "support",
    "security_monitoring"
  ],
  "subprocessors": [
    {"name": "AWS EMEA", "address": "Berlin, Germany", "purpose": "cloud_infrastructure"},
    {"name": "Stripe Payments", "address": "Dublin, Ireland", "purpose": "payment_processing"}
  ],
  "security_measures": [
    "encryption_at_rest_AES256",
    "encryption_in_transit_TLSv1.3",
    "access_control_RBAC",
    "audit_logging",
    "soc2_type2"
  ],
  "format": "pdf"
}
```

response: `200 OK` (dpa document download)

## data model

```python
# models/gdpr.py
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

class PIILevel(str, Enum):
    NONE = "L0"
    INTERNAL = "L1"
    SENSITIVE = "L2"
    CRITICAL = "L3"

class PurgeAction(str, Enum):
    DELETE = "delete"
    ANONYMIZE = "anonymize"
    ARCHIVE = "archive"
    NONE = "none"

class ErasureStatus(str, Enum):
    PENDING_VERIFICATION = "pending_verification"
    PENDING_CONFIRMATION = "pending_confirmation"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ConsentPurpose(str, Enum):
    SERVICE_OPERATIONS = "service_operations"
    MARKETING_COMM = "marketing_communications"
    THIRD_PARTY_SHARING = "third_party_sharing"
    ANALYTICS = "analytics"
    SUPPORT = "support"

@dataclass
class RetentionPolicy:
    category: str
    pii_level: PIILevel
    default_days: int               # -1 = permanent
    purge_action: PurgeAction
    legal_hold_enabled: bool
    services: list[str]

@dataclass
class DataLocation:
    service: str
    database: str
    table: str
    column: str
    pii_level: PIILevel
    purge_action: PurgeAction
    retention_days: int
    record_count: int
    sample_data: dict | None = None

@dataclass
class PurgeJob:
    id: str
    category: str
    policy: RetentionPolicy
    records_affected: int
    status: str                     # pending / running / completed / failed
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None

@dataclass
class ErasureRequest:
    id: str
    user_id: str
    status: ErasureStatus
    verification_method: str
    verification_token_hash: str
    verification_expires: datetime
    cool_down_expires: datetime
    confirmed_at: datetime | None
    summary: dict | None            # records found per category
    purge_job_id: str | None
    created_at: datetime
    updated_at: datetime

@dataclass
class ConsentRecord:
    id: str
    user_id: str
    purpose: ConsentPurpose
    granted: bool
    version: str
    ip_address: str
    user_agent: str
    granted_at: datetime
    revoked_at: datetime | None

@dataclass
class DPATemplate:
    organisation_name: str
    organisation_address: str
    representative_name: str
    representative_email: str
    data_categories: list[str]
    processing_purposes: list[str]
    subprocessors: list[dict]
    security_measures: list[str]
    generated_at: datetime
    valid_until: datetime
```

**database schema:**

```sql
-- Retention policies (configuration, cached from YAML)
CREATE TABLE retention_policies (
    category        TEXT PRIMARY KEY,
    pii_level       TEXT NOT NULL,
    default_days    INTEGER NOT NULL,
    purge_action    TEXT NOT NULL,
    legal_hold_enabled BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Data inventory (populated by scanner)
CREATE TABLE data_inventory (
    id              SERIAL PRIMARY KEY,
    service         TEXT NOT NULL,
    database_name   TEXT NOT NULL,
    table_name      TEXT NOT NULL,
    column_name     TEXT NOT NULL,
    pii_level       TEXT NOT NULL,
    purge_action    TEXT NOT NULL,
    retention_days  INTEGER NOT NULL,
    record_count    BIGINT DEFAULT 0,
    discovered_at   TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (service, database_name, table_name, column_name)
);

-- Purge jobs
CREATE TABLE purge_jobs (
    id              TEXT PRIMARY KEY,
    category        TEXT NOT NULL,
    policy_category TEXT REFERENCES retention_policies(category),
    records_affected BIGINT DEFAULT 0,
    status          TEXT NOT NULL DEFAULT 'pending',
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    error_message   TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Right-to-erasure requests
CREATE TABLE erasure_requests (
    id                  TEXT PRIMARY KEY,
    user_id             TEXT NOT NULL,
    status              TEXT NOT NULL DEFAULT 'pending_verification',
    verification_method TEXT NOT NULL,
    verification_token_hash TEXT NOT NULL,
    verification_expires TIMESTAMPTZ NOT NULL,
    cool_down_expires   TIMESTAMPTZ NOT NULL,
    confirmed_at        TIMESTAMPTZ,
    summary             JSONB,
    purge_job_id        TEXT REFERENCES purge_jobs(id),
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

-- Consent records
CREATE TABLE consent_records (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         TEXT NOT NULL,
    purpose         TEXT NOT NULL,
    granted         BOOLEAN NOT NULL,
    version         TEXT NOT NULL,
    ip_address      TEXT,
    user_agent      TEXT,
    granted_at      TIMESTAMPTZ DEFAULT NOW(),
    revoked_at      TIMESTAMPTZ,
    INDEX idx_consent_user (user_id)
);

-- DPA documents
CREATE TABLE dpa_documents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organisation_name TEXT NOT NULL,
    data             JSONB NOT NULL,
    format           TEXT NOT NULL DEFAULT 'pdf',
    file_path        TEXT,
    generated_at    TIMESTAMPTZ DEFAULT NOW(),
    valid_until     TIMESTAMPTZ
);

-- Data lifecycle audit trail (immutable)
CREATE TABLE lifecycle_audit_log (
    id              BIGSERIAL PRIMARY KEY,
    event_type      TEXT NOT NULL,    -- purge_executed / erasure_completed / consent_change / policy_updated
    category        TEXT,
    user_id         TEXT,
    details         JSONB NOT NULL,
    performed_by    TEXT NOT NULL,     -- system / admin user ID / erasure-request
    performed_at    TIMESTAMPTZ DEFAULT NOW()
);
```

## configuration reference

```yaml
# config/data_retention.yaml
retention:
  scheduler:
    cron_expression: "0 2 * * *"        # Daily at 02:00
    purge_batch_size: 10000
    purge_concurrency: 4
    dry_run: false                       # Safety: log without deleting

  anonymization:
    default_strategy: "mask"
    strategies:
      email: "mask"
      ip_address: "hash"
      full_name: "mask"
      phone: "truncate"
      credit_card: "tokenize"
      password_hash: "redact"           # should already be hashed
      message_body: "redact"
    vault_address: "http://vault:8200"  # for tokenization

  archive:
    storage_backend: "s3"
    s3_bucket: "infrapilot-gdpr-archive"
    s3_region: "eu-central-1"
    encryption_key_arn: "arn:aws:kms:eu-central-1:...:key/..."
    archive_format: "jsonl.gzip"

  legal_hold:
    enabled: true
    hold_api_endpoint: "http://legal-hold-service:8080"
    hold_check_timeout_ms: 5000

  erasure:
    cool_down_hours: 72
    verification_token_ttl_minutes: 60
    max_erasure_execution_minutes: 30
    notification:
      on_submit: true
      on_complete: true
      on_failure: true
    email_templates:
      verification: "templates/gdpr/erasure_verification.html"
      confirmation: "templates/gdpr/erasure_confirmation.html"
      complete: "templates/gdpr/erasure_complete.html"

  notifications:
    expiry_warning_days: [90, 30, 14, 7]
    notify_roles: ["admin", "compliance_officer"]
    notify_channels: ["email", "panel"]
```

## service assignments

| service | responsibility |
|---------|---------------|
| **integration service** | data lifecycle engine — classification, retention policy engine, purge executor, anonymization, right-to-erasure workflow, consent management, data inventory, dpa generator, audit trail |
| **management panel** | gdpr dashboard — retention policy management ui, erasure request submission & tracking, consent preference ui, data inventory viewer, dpa download, compliance reporting |
| **orchestrator agent** | coordinate cross-service purge execution; ensure all worker nodes respect data retention policies; deploy anonymization sidecars |
| **notification service** | send erasure verification emails, expiry warnings, compliance alerts to designated roles |

## effort breakdown

| phase | task | pt | dependencies |
|-------|------|----|-------------|
| 1.1 | pii classification schema & scanner | 1 | data schemas across all services |
| 1.2 | retention policy definition & yaml config | 0.5 | classification schema |
| 1.3 | policy engine (scheduler + evaluator) | 1 | policy definitions |
| 1.4 | metadata registry for tracked data | 0.5 | scanner |
| 2.1 | purge executor (delete/anonymize/archive) | 1 | policy engine |
| 2.2 | anonymization engine | 0.5 | purge executor |
| 2.3 | archive storage backend (s3/blob) | 0.5 | purge executor |
| 2.4 | right-to-erasure workflow | 1 | purge executor, anonymization |
| 2.5 | erasure request api | 0.5 | workflow |
| 3.1 | data inventory scanner | 0.5 | classification |
| 3.2 | gdpr article 30 export | 0.5 | inventory |
| 3.3 | consent management crud | 0.5 | database schema |
| 3.4 | dpa template & generator | 0.5 | consent management |
| 3.5 | expiry notification service | 0.25 | policy engine |
| 3.6 | lifecycle audit trail | 0.25 | all phases |
| | **total** | **8.75** | |

**note:** phases 1-3 overlap where possible. consolidated effort is **4-6 pt** as stated in the plan.

## risks & mitigations

| risk | impact | mitigation |
|------|--------|------------|
| accidental data deletion before retention expiry | permanent data loss, compliance violation | dry-run mode enforced on first execution; confirmation step for all purge jobs; soft-delete with 30-day recovery window |
| incomplete erasure (missed pii in backups/derived data) | gdpr non-compliance, fines | backup scanning integrated into inventory; `lifecycle_audit_log` tracks all copies; follow-up scan 24h post-erasure |
| legal hold conflict with retention purge | wrongful deletion of evidence | legal hold api check before every purge; hold flag overrides retention policy; all overrides logged |
| cross-service consistency during purge | partial purge, inconsistent state | distributed saga pattern with compensating actions; two-phase commit across services |
| consent version drift (user consented to old policy) | invalid consent basis | versioned consent records; prompt re-consent on policy changes; deny processing until re-consent |
| dpa template becomes outdated (law changes) | non-compliant dpa | versioned templates with expiry dates; automated notification when new template available |
