# siem export

- feature id: 49
- category: security & compliance
- primary service: integration service
- effort estimate: small (1-3 pt)
- status: planned

## overview

stream audit logs from the infra pilot platform to external siem (security information and event management) systems including splunk, elk stack (elasticsearch/logstash/kibana), datadog, and any rfc 5424 syslog-compatible endpoint. all exports use structured json formatting with mandatory tls transport.

this feature enables security teams to centralise log monitoring, run correlation rules, and maintain a single pane of glass across their infrastructure estate.

### goals

• deliver real-time and batch audit log export to major siem platforms
• enforce tls/mtls for all outbound log transmissions
• provide filterable export rules (by severity, source, service, label)
• implement exponential-backoff retry for transient delivery failures
• support both push (http/syslog) and pull (siem-initiated scrape) models
• maintain delivery guarantees with at-least-once semantics

## architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                     Infra Pilot Platform                          │
│                                                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │  Audit    │  │  Access  │  │  Billing  │  │  Resource        │ │
│  │  Logs     │  │  Logs    │  │  Logs     │  │  Change Logs     │ │
│  └─────┬────┘  └─────┬────┘  └─────┬────┘  └────────┬─────────┘ │
│        │              │              │                │           │
│        ▼              ▼              ▼                ▼           │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │                 Integration Service                        │    │
│  │  ┌────────────────────────────────────────────────────┐  │    │
│  │  │              SIEM Export Pipeline                   │  │    │
│  │  │                                                     │  │    │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │  │    │
│  │  │  │ Log      │──│ Filter & │──│ Transformer      │  │  │    │
│  │  │  │ Buffer   │  │ Classify │  │ → JSON Schema    │  │  │    │
│  │  │  └──────────┘  └──────────┘  └────────┬─────────┘  │  │    │
│  │  │                                        │            │  │    │
│  │  │                                        ▼            │  │    │
│  │  │  ┌──────────────────────────────────────────────┐  │  │    │
│  │  │  │         Output Router                         │  │  │    │
│  │  │  │  ┌─────────┐ ┌──────────┐ ┌──────────────┐  │  │  │    │
│  │  │  │  │ Syslog  │ │  HTTPS   │ │  Pull API    │  │  │  │    │
│  │  │  │  │ (RFC5424)│ │  Push    │ │  (Scrape)    │  │  │  │    │
│  │  │  │  └────┬────┘ └────┬─────┘ └──────┬───────┘  │  │  │    │
│  │  │  └───────┼───────────┼──────────────┼──────────┘  │  │    │
│  │  │          │           │              │             │  │    │
│  │  │          ▼           ▼              ▼             │  │    │
│  │  │  ┌────────────────────────────────────────────┐  │  │    │
│  │  │  │         TLS/mTLS Termination Layer          │  │  │    │
│  │  │  │  ┌──────────┐ ┌──────────┐ ┌────────────┐ │  │  │    │
│  │  │  │  │  CA      │ │  Cert    │ │  Mutual    │ │  │  │    │
│  │  │  │  │  Pool    │ │  Pinning │ │  Auth (mTLS)│ │  │  │    │
│  │  │  │  └──────────┘ └──────────┘ └────────────┘ │  │  │    │
│  │  │  └────────────────────────────────────────────┘  │  │    │
│  │  │                                                  │  │    │
│  │  │  ┌────────────────────────────────────────────┐  │  │    │
│  │  │  │         Retry & Backoff Engine              │  │  │    │
│  │  │  │  Exponential backoff (max 5 retries)       │  │  │    │
│  │  │  │  Dead-letter queue for permanent failures   │  │  │    │
│  │  │  └────────────────────────────────────────────┘  │  │    │
│  │  └────────────────────────────────────────────────────┘  │    │
│  └──────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
                           │
           ┌────────────────┼────────────────┬────────────────┐
           ▼                ▼                ▼                ▼
┌──────────────────┐ ┌──────────────┐ ┌────────────┐ ┌──────────┐
│     Splunk       │ │   ELK Stack  │ │  Datadog   │ │ RFC 5424 │
│  HEC / TCP Input │ │  Logstash    │ │  HTTP API  │ │  Syslog  │
└──────────────────┘ └──────────────┘ └────────────┘ └──────────┘
```

## implementation plan

### phase 1: core pipeline (1-2 pt)

| step | description | artifacts |
|------|-------------|-----------|
| 1.1 | log buffer & classification service | `internal/siem/buffer.go` — in-memory ring buffer with configurable capacity |
| 1.2 | structured json transformer | `internal/siem/transformer.go` — normalise to canonical siem schema |
| 1.3 | output router (syslog / https / pull) | `internal/siem/router.go` — route per destination config |
| 1.4 | tls termination layer | `internal/siem/tls.go` — cert loading, mtls handshake, ca pinning |

**canonical json schema:**

```json
{
  "version": "1.0",
  "timestamp": "2026-05-27T14:30:00.123Z",
  "event_id": "evt-abc123def",
  "event_type": "audit.resource.create",
  "severity": "notice",
  "source": {
    "service": "orchestrator",
    "host": "ctrl-01.infra.example.com",
    "ip": "10.0.1.42"
  },
  "actor": {
    "id": "user-789",
    "type": "user",
    "email": "ops@example.com"
  },
  "resource": {
    "type": "server",
    "id": "srv-web-42",
    "action": "create"
  },
  "context": {
    "request_id": "req-xyz-987",
    "user_agent": "InfraPilot CLI v2.1.0",
    "geo": {
      "city": "Frankfurt",
      "country": "DE"
    }
  },
  "payload": {
    "changes": {
      "cpu_cores": 4,
      "memory_gb": 16
    }
  },
  "labels": {
    "env": "production",
    "team": "platform"
  }
}
```

### phase 2: destinations & retry (0.5-1 pt)

| step | description | artifacts |
|------|-------------|-----------|
| 2.1 | splunk hec integration | `internal/siem/dest/splunk.go` — http event collector client |
| 2.2 | elk logstash integration | `internal/siem/dest/elastic.go` — logstash tcp/http input client |
| 2.3 | datadog integration | `internal/siem/dest/datadog.go` — datadog http logs api client |
| 2.4 | generic syslog (rfc 5424) | `internal/siem/dest/syslog.go` — tcp/tls syslog sender |
| 2.5 | retry engine with backoff | `internal/siem/retry.go` — exponential backoff, jitter, dead-letter queue |

**retry configuration:**

```yaml
# config/siem_export.yaml
export:
  retry:
    max_attempts: 5
    initial_backoff_ms: 1000
    max_backoff_ms: 60000
    multiplier: 2.0
    jitter: 0.1          # +/- 10% jitter
    dead_letter_ttl_hours: 72
  batch:
    max_size_bytes: 1048576   # 1 MB
    max_events: 500
    flush_interval_ms: 5000
```

### phase 3: filtering & monitoring (0.5 pt)

| step | description | artifacts |
|------|-------------|-----------|
| 3.1 | filter rules engine | `internal/siem/filter.go` — include/exclude rules based on severity, source, labels, event_type |
| 3.2 | rate limiter per destination | `internal/siem/ratelimit.go` — token-bucket per output sink |
| 3.3 | health check & metrics | prometheus metrics: `siem_exported_total`, `siem_errors_total`, `siem_queue_depth` |
| 3.4 | status dashboard panel | panel widget showing per-destination health, throughput, error rate |

## api design

### siem export configuration crud

#### list export targets

```
GET /api/v1/integrations/siem
```

response:
```json
{
  "targets": [
    {
      "id": "siem-splunk-prod",
      "name": "Splunk Production",
      "type": "splunk_hec",
      "endpoint": "https://splunk.example.com:8088/services/collector",
      "enabled": true,
      "tls": {
        "verify": true,
        "mtls_enabled": false
      },
      "filter": {
        "min_severity": "notice",
        "include_labels": {"env": "production"},
        "exclude_event_types": ["heartbeat"]
      },
      "status": "connected",
      "exported_count": 1425300,
      "error_count": 12,
      "last_error_at": "2026-05-27T12:01:00Z",
      "created_at": "2026-05-01T00:00:00Z"
    }
  ]
}
```

#### create export target

```
POST /api/v1/integrations/siem
```

request:
```json
{
  "name": "Splunk Production",
  "type": "splunk_hec",
  "endpoint": "https://splunk.example.com:8088/services/collector",
  "auth": {
    "token": "{{ secrets.SPLUNK_HEC_TOKEN }}",
    "mtls_cert_pem": null,
    "mtls_key_pem": null
  },
  "tls": {
    "verify": true,
    "ca_cert_pem": null
  },
  "filter": {
    "min_severity": "notice",
    "include_labels": {"env": "production"},
    "exclude_event_types": ["heartbeat"]
  },
  "batch": {
    "max_size_bytes": 1048576,
    "max_events": 500,
    "flush_interval_ms": 5000
  },
  "retry": {
    "max_attempts": 5,
    "initial_backoff_ms": 1000,
    "max_backoff_ms": 60000
  }
}
```

response: `201 Created`

#### update export target

```
PATCH /api/v1/integrations/siem/{id}
```

#### delete export target

```
DELETE /api/v1/integrations/siem/{id}
```

#### test connection

```
POST /api/v1/integrations/siem/{id}/test
```

response:
```json
{
  "success": true,
  "latency_ms": 145,
  "tls_version": "TLSv1.3",
  "server_info": "Splunk HEC v8.2"
}
```

#### list available event types

```
GET /api/v1/integrations/siem/event-types
```

response:
```json
{
  "event_types": [
    {"type": "audit.resource.create", "description": "Resource created"},
    {"type": "audit.resource.delete", "description": "Resource deleted"},
    {"type": "audit.resource.modify", "description": "Resource modified"},
    {"type": "audit.access.granted", "description": "Access granted"},
    {"type": "audit.access.denied", "description": "Access denied"},
    {"type": "audit.login.success", "description": "Successful login"},
    {"type": "audit.login.failure", "description": "Failed login attempt"},
    {"type": "billing.invoice.created", "description": "Invoice generated"},
    {"type": "system.heartbeat", "description": "Service health check"}
  ]
}
```

## data model

```python
# models/siem_export.py
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

class SIEMDestinationType(str, Enum):
    SPLUNK_HEC = "splunk_hec"
    ELK_LOGSTASH = "elk_logstash"
    DATADOG_HTTP = "datadog_http"
    SYSLOG_RFC5424 = "syslog_rfc5424"

class ExportStatus(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    PAUSED = "paused"

@dataclass
class TLSConfig:
    verify: bool = True
    ca_cert_pem: str | None = None
    mtls_enabled: bool = False
    mtls_cert_pem: str | None = None
    mtls_key_pem: str | None = None

@dataclass
class ExportFilter:
    min_severity: str = "info"          # emerg, alert, crit, error, warning, notice, info
    include_labels: dict[str, str] = field(default_factory=dict)
    exclude_labels: dict[str, str] = field(default_factory=dict)
    include_event_types: list[str] = field(default_factory=list)
    exclude_event_types: list[str] = field(default_factory=list)
    include_sources: list[str] = field(default_factory=list)
    exclude_sources: list[str] = field(default_factory=list)

@dataclass
class BatchConfig:
    max_size_bytes: int = 1048576
    max_events: int = 500
    flush_interval_ms: int = 5000

@dataclass
class RetryConfig:
    max_attempts: int = 5
    initial_backoff_ms: int = 1000
    max_backoff_ms: int = 60000
    multiplier: float = 2.0
    jitter: float = 0.1
    dead_letter_ttl_hours: int = 72

@dataclass
class SIEMExportTarget:
    id: str
    name: str
    type: SIEMDestinationType
    endpoint: str
    enabled: bool
    tls: TLSConfig
    filter: ExportFilter
    batch: BatchConfig
    retry: RetryConfig
    status: ExportStatus
    exported_count: int
    error_count: int
    last_error_at: datetime | None
    created_at: datetime
    updated_at: datetime

@dataclass
class SIEMEvent:
    version: str = "1.0"
    timestamp: datetime
    event_id: str
    event_type: str
    severity: str
    source: dict       # {service, host, ip}
    actor: dict | None # {id, type, email}
    resource: dict     # {type, id, action}
    context: dict      # {request_id, user_agent, geo}
    payload: dict      # free-form event data
    labels: dict       # key-value metadata tags
```

**database schema:**

```sql
-- SIEM export targets
CREATE TABLE siem_export_targets (
    id              TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    type            TEXT NOT NULL,            -- splunk_hec, elk_logstash, datadog_http, syslog_rfc5424
    endpoint        TEXT NOT NULL,
    enabled         BOOLEAN DEFAULT true,
    tls_config      JSONB NOT NULL DEFAULT '{}',
    filter_config   JSONB NOT NULL DEFAULT '{}',
    batch_config    JSONB NOT NULL DEFAULT '{}',
    retry_config    JSONB NOT NULL DEFAULT '{}',
    status          TEXT NOT NULL DEFAULT 'disconnected',
    exported_count  BIGINT DEFAULT 0,
    error_count     BIGINT DEFAULT 0,
    last_error_at   TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Dead-letter queue for permanently failed events
CREATE TABLE siem_dead_letters (
    id              BIGSERIAL PRIMARY KEY,
    target_id       TEXT REFERENCES siem_export_targets(id),
    event           JSONB NOT NULL,
    error_reason    TEXT NOT NULL,
    attempt_count   INTEGER NOT NULL,
    failed_at       TIMESTAMPTZ DEFAULT NOW(),
    expires_at      TIMESTAMPTZ NOT NULL
);

-- Export audit trail
CREATE TABLE siem_export_log (
    id              BIGSERIAL PRIMARY KEY,
    target_id       TEXT NOT NULL,
    event_count     INTEGER NOT NULL,
    bytes_sent      BIGINT NOT NULL,
    success         BOOLEAN NOT NULL,
    error_message   TEXT,
    duration_ms     INTEGER,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

## configuration reference

```yaml
# config/siem_export.yaml
export:
  defaults:
    tls:
      verify: true
      min_version: "TLSv1.2"
    batch:
      max_size_bytes: 1048576
      max_events: 500
      flush_interval_ms: 5000
    retry:
      max_attempts: 5
      initial_backoff_ms: 1000
      max_backoff_ms: 60000
      multiplier: 2.0
      jitter: 0.1
      dead_letter_ttl_hours: 72

  targets:
    - name: "Splunk Production"
      type: splunk_hec
      endpoint: "https://splunk.example.com:8088/services/collector"
      auth:
        token: "${SPLUNK_HEC_TOKEN}"
      tls:
        verify: true
      filter:
        min_severity: notice
        include_labels:
          env: production
        exclude_event_types:
          - system.heartbeat
      enabled: true

    - name: "ELK Staging"
      type: elk_logstash
      endpoint: "tcp://logstash.staging.example.com:6514"
      tls:
        verify: true
        mtls_enabled: true
        mtls_cert_pem: "/etc/infrapilot/certs/siem-client.crt"
        mtls_key_pem: "/etc/infrapilot/certs/siem-client.key"
      filter:
        min_severity: info
      enabled: true

    - name: "Datadog EU"
      type: datadog_http
      endpoint: "https://http-intake.logs.datadoghq.eu/api/v2/logs"
      auth:
        token: "${DATADOG_API_KEY}"
      filter:
        min_severity: warning
        include_labels:
          env: production
      enabled: true

    - name: "Corporate Syslog"
      type: syslog_rfc5424
      endpoint: "tcp://syslog.corp.example.com:514"
      tls:
        verify: false
      filter:
        include_event_types:
          - audit.access.denied
          - audit.login.failure
      enabled: false
```

## service assignments

| service | responsibility |
|---------|---------------|
| **integration service** | siem export pipeline — buffer, transform, route, retry, dead-letter queue; rest api for target crud; tls/mtls termination |
| **management panel** | configuration ui for siem targets; per-destination health dashboard; dead-letter queue viewer and replay |
| **orchestrator agent** | deploy siem exporter sidecar configuration; manage secrets injection for auth tokens and tls material |

## effort breakdown

| phase | task | pt | dependencies |
|-------|------|----|-------------|
| 1.1 | log buffer & classification service | 0.5 | audit log schema |
| 1.2 | json transformer (canonical schema) | 0.5 | schema definition |
| 1.3 | output router (syslog / https / pull) | 0.5 | transformer |
| 1.4 | tls termination layer | 0.5 | router |
| 2.1 | splunk hec integration | 0.25 | output router |
| 2.2 | elk logstash integration | 0.25 | output router |
| 2.3 | datadog http integration | 0.25 | output router |
| 2.4 | generic syslog rfc 5424 | 0.25 | output router |
| 2.5 | retry engine with backoff | 0.5 | phase 1 |
| 3.1 | filter rules engine | 0.25 | transformer |
| 3.2 | rate limiter per destination | 0.25 | router |
| 3.3 | prometheus metrics & health | 0.25 | phase 2 |
| 3.4 | management panel ui | 0.5 | rest api |
| | **total** | **4.5** | |

**note:** parallelisation of destination integrations (2.1-2.4) reduces wall-clock time. actual effort is **1-3 pt** as stated in the plan.

## risks & mitigations

| risk | impact | mitigation |
|------|--------|------------|
| certificate expiry for mtls | export outage | automated cert expiry monitoring, pre-expiry alerts (30/14/7 days), cert rotation api |
| siem endpoint rate limiting | event loss | token-bucket rate limiter per target, backpressure signalling, dead-letter queue |
| sensitive data in audit logs | compliance violation | configurable field redaction, `exclude_fields` filter, regex-based pii scrubber |
| high log volume overwhelms network | latency spikes, dropped events | configurable batch sizing, compression (gzip), circuit breaker pattern |
| siem destination unreachable | log backlog | ring buffer with configurable capacity, backpressure to source, dead-letter after max retries |
