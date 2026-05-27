# feature 17: opentelemetry export

- feature #: 17
- category: developer ecosystem & api
- primary service: integration service
- supporting services: orchestrator agent, management panel, discord service, service core
- effort: medium (4-6 pt)
- dependencies: feature #14 (api gateway & rate limiting)

## 1. overview

opentelemetry export enables infra pilot to emit traces, metrics, and logs via the opentelemetry protocol (otlp) to any otel-compatible backend (grafana tempo, jaeger, signoz, datadog, new relic, honeycomb, etc.). distributed trace context propagates across all services (panel → integration service → orchestrator agent → service core), enabling end-to-end request visibility.

### goals

- export traces, metrics, and logs via otlp (grpc and http/protobuf)
- distributed trace propagation across all microservices
- automatic instrumentation of http handlers, database queries, and message queues
- configurable sampling (rate-based, head-based, tail-based)
- correlation between traces, metrics, and logs via consistent span/trace ids
- minimal performance overhead (~1-3% latency increase at 100% sampling)

### non-goals

- running an otel collector as part of infra pilot (users bring their own backend/collector)
- replacing existing prometheus metrics endpoint (otel supplements, does not replace)
- custom otel instrumentation sdk development — use standard sdks

## 2. architecture

### high-level component diagram

```
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│ Management Panel │    │ Integration      │    │ Orchestrator     │
│ (JS/React)       │    │ Service (Node)   │    │ Agent (Python)   │
│                  │    │                  │    │                  │
│ OTel JS SDK      │    │ OTel Node SDK    │    │ OTel Python SDK  │
│ Web OTEL         │    │ Auto-            │    │ Auto-            │
│ Exporter         │    │ Instrumentation  │    │ Instrumentation  │
└────────┬─────────┘    └────────┬─────────┘    └────────┬─────────┘
         │                      │                       │
         │                      │                       │
         └──────────────────────┼───────────────────────┘
                                │
                                ▼
                  ┌─────────────────────────────┐
                  │  OTLP Exporter (gRPC / HTTP) │
                  │  ─────────────────────────── │
                  │  endpoint: ${OTEL_EXPORTER_  │
                  │    OTLP_ENDPOINT}:4317       │
                  └────────────┬────────────────┘
                               │
                               ▼
                  ┌─────────────────────────────┐
                  │  User's OTel Backend         │
                  │  (Collector, Grafana Tempo,  │
                  │   Jaeger, SigNoz, Datadog)   │
                  └─────────────────────────────┘
```

### trace propagation flow

```
Browser / External Request
       │
       │ Traceparent: 00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01
       ▼
┌──────────────────┐
│ Management Panel │──► Create/Inject span context
│ (React)          │
└──────┬───────────┘
       │ HTTP header propagation
       ▼
┌──────────────────┐
│ Integration      │──► Extract context → Create child span
│ Service (Node)   │──► Auto-instrument HTTP, DB, Queue
└──────┬───────────┘
       │ gRPC metadata / HTTP headers
       ▼
┌──────────────────┐
│ Orchestrator     │──► Extract context → Create child span
│ Agent (Python)   │──► Auto-instrument aiohttp, psycopg2, redis
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Service Core     │──► Extract context → Create child span
│ (Java)           │──► Auto-instrument JAX-RS, JDBC, RabbitMQ
└──────────────────┘
```

### span attributes (enrichment)

every span carries standardized attributes for correlation:

```json
{
  "span_id": "b7ad6b7169203331",
  "trace_id": "0af7651916cd43dd8448eb211c80319c",
  "resource": {
    "service.name": "orchestrator-agent",
    "service.version": "2.5.0",
    "deployment.environment": "production",
    "host.name": "ip-orch-pod-7f8b9c",
    "telemetry.sdk.name": "opentelemetry",
    "telemetry.sdk.language": "python",
    "telemetry.sdk.version": "1.28.0"
  },
  "scope": {
    "name": "infrapilot.orchestrator.provisioning"
  },
  "attributes": {
    "infrapilot.tenant_id": "tnt_001",
    "infrapilot.server_id": "srv_web_01",
    "infrapilot.server_name": "web-01",
    "infrapilot.action": "server.create",
    "infrapilot.user_id": "usr_abc",
    "http.method": "POST",
    "http.route": "/api/v2/servers",
    "http.status_code": 201,
    "db.system": "postgresql",
    "db.name": "infrapilot"
  }
}
```

## 3. data model

### configuration

```json
{
  "otel": {
    "enabled": true,
    "exporter": {
      "protocol": "grpc",
      "endpoint": "http://otel-collector:4317",
      "headers": {
        "x-api-key": "${OTEL_API_KEY}"
      },
      "compression": "gzip",
      "timeout_ms": 10000
    },
    "traces": {
      "enabled": true,
      "sampler": {
        "type": "parentbased_traceidratio",
        "ratio": 0.1,
        "rate_limit_per_second": 100
      },
      "max_export_batch_size": 512,
      "export_interval_ms": 5000
    },
    "metrics": {
      "enabled": true,
      "export_interval_ms": 30000,
      "temporality": "delta",
      "exemplars_enabled": true
    },
    "logs": {
      "enabled": true,
      "severity_threshold": "INFO",
      "include_console": true
    },
    "propagation": {
      "format": ["traceparent", "baggage"],
      "headers": ["traceparent", "tracestate", "baggage"]
    },
    "resource": {
      "service.name": "infrapilot",
      "deployment.environment": "production"
    }
  }
}
```

### metrics exported

| metric name | type | description | unit |
|---|---|---|---|
| `infrapilot.server.provisioning.duration` | histogram | time to provision a server | ms |
| `infrapilot.server.backup.duration` | histogram | time to complete backup | ms |
| `infrapilot.server.backup.size` | histogram | backup size | bytes |
| `infrapilot.api.request.duration` | histogram | api request latency | ms |
| `infrapilot.api.request.count` | counter | total api requests | count |
| `infrapilot.api.request.errors` | counter | api request errors | count |
| `infrapilot.discord.command.count` | counter | discord command invocations | count |
| `infrapilot.db.connection.pool.size` | gauge | active db connections | count |
| `infrapilot.db.query.duration` | histogram | database query latency | ms |
| `infrapilot.queue.depth` | gauge | message queue depth | count |

### log correlation

structured logs include trace context for correlation:

```json
{
  "timestamp": "2026-05-20T12:00:00.123Z",
  "level": "INFO",
  "message": "Server provisioned successfully",
  "service": "orchestrator-agent",
  "trace_id": "0af7651916cd43dd8448eb211c80319c",
  "span_id": "b7ad6b7169203331",
  "trace_flags": "01",
  "resource": {
    "server_id": "srv_web_01",
    "tenant_id": "tnt_001",
    "provider": "hetzner"
  }
}
```

## 4. implementation plan

### phase 1: sdk integration & auto-instrumentation (weeks 1-2, 2.5 pt)

| task | service | description |
|---|---|---|
| 1.1 | integration service | add otel node.js sdk + auto-instrumentation packages |
| 1.2 | orchestrator agent | add otel python sdk + auto-instrumentation packages |
| 1.3 | discord service | add otel node.js sdk + auto-instrumentation |
| 1.4 | service core | add otel java sdk + auto-instrumentation (openliberty/quarkus) |
| 1.5 | management panel | add otel web sdk (web vitals, fetch instrumentation) |
| 1.6 | all | configure otlp exporter, batching, compression, tls |

deliverables: all services instrumented and exporting traces to configurable otlp endpoint.

### phase 2: trace propagation (week 2-3, 1 pt)

| task | service | description |
|---|---|---|
| 2.1 | all | ensure w3c tracecontext (traceparent/tracestate) propagation |
| 2.2 | integration service | add propagation through grpc metadata |
| 2.3 | orchestrator agent | add propagation through aiohttp client requests |
| 2.4 | management panel | add propagation through fetch/axios interceptors |
| 2.5 | all | add baggage propagation for tenant/user context |

deliverables: end-to-end distributed traces across all service boundaries.

### phase 3: metrics export (week 3, 1 pt)

| task | service | description |
|---|---|---|
| 3.1 | integration service | define & register otel metrics (histograms, counters, gauges) |
| 3.2 | orchestrator agent | define & register otel metrics for provisioning operations |
| 3.3 | service core | define & register otel metrics for game server lifecycle |
| 3.4 | integration service | add exemplar support (trace-to-metrics correlation) |
| 3.5 | all | configure delta vs cumulative temporality |

deliverables: custom metrics exported via otlp with exemplar support.

### phase 4: log correlation (week 4, 1 pt)

| task | service | description |
|---|---|---|
| 4.1 | all | inject trace_id/span_id into all structured log entries |
| 4.2 | all | configure otel log exporter (severity filtering, batching) |
| 4.3 | integration service | add log correlation dashboard config (optional grafana) |
| 4.4 | shared | document trace-to-log query patterns |

deliverables: all logs include trace context; logs exportable via otlp.

### phase 5: sampler configuration & performance (week 5, 0.5 pt)

| task | service | description |
|---|---|---|
| 5.1 | all | head-based sampling configuration (rate, trace id ratio) |
| 5.2 | integration service | tail-based sampler (sample only interesting spans: errors, slow) |
| 5.3 | all | load testing at 100% and 1% sampling; measure overhead |
| 5.4 | shared | document recommended sampling strategies per environment |

deliverables: configurable sampling strategies with validated performance characteristics.

## 5. api design

### configuration endpoint

```yaml
GET /api/v2/otel/status
```

```json
{
  "enabled": true,
  "exporter": {
    "endpoint": "http://otel-collector:4317",
    "protocol": "grpc",
    "connected": true,
    "last_export": "2026-05-20T12:00:05Z"
  },
  "traces": {
    "spans_exported": 15234,
    "spans_dropped": 12,
    "sampling_ratio": 0.1
  },
  "metrics": {
    "datapoints_exported": 89234,
    "datapoints_dropped": 0
  },
  "logs": {
    "records_exported": 452345,
    "records_dropped": 45
  }
}
```

### environment variables

| variable | default | description |
|---|---|---|
| `OTEL_SDK_DISABLED` | `false` | disable otel sdk entirely |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://localhost:4317` | otlp grpc endpoint |
| `OTEL_EXPORTER_OTLP_PROTOCOL` | `grpc` | otlp protocol (`grpc`/`http/protobuf`) |
| `OTEL_EXPORTER_OTLP_HEADERS` | — | custom headers (e.g., api key) |
| `OTEL_EXPORTER_OTLP_COMPRESSION` | `gzip` | compression (`gzip`/`none`) |
| `OTEL_TRACES_SAMPLER` | `parentbased_always_on` | sampler type |
| `OTEL_TRACES_SAMPLER_ARG` | `1.0` | sampler argument (ratio) |
| `OTEL_METRICS_EXPORTER` | `otlp` | metrics exporter |
| `OTEL_LOGS_EXPORTER` | `otlp` | logs exporter |
| `OTEL_SERVICE_NAME` | `infrapilot` | service name for resource |
| `OTEL_RESOURCE_ATTRIBUTES` | — | additional resource attributes |

### sampler configuration

```yaml
traces:
  sampler:
    # Parent-based trace ID ratio sampler
    type: parentbased_traceidratio
    ratio: 0.1  # 10% of traces

    # Or: rate-limiting sampler
    # type: rate_limiting
    # traces_per_second: 10

    # Or: always sample errors + slow spans
    # type: tail_based
    # rules:
    #   - sample_when: { http.status_code >= 500 }
    #   - sample_when: { duration_ms >= 5000 }
    #   - rate: 0.01  # background rate for normal spans
```

## 6. service assignments

| service | responsibilities |
|---|---|
| integration service | otel node.js sdk + auto-instrumentation, grpc/http propagation, metric registration, tail-based sampling logic, status api |
| orchestrator agent | otel python sdk + auto-instrumentation (aiohttp, psycopg2, redis), trace propagation, provisioning metrics |
| management panel | otel web sdk (web vitals, fetch instrumentation), traceparent propagation via http headers |
| discord service | otel node.js sdk + auto-instrumentation, discord.js hook instrumentation, command metrics |
| service core | otel java sdk + auto-instrumentation (jax-rs, jdbc, rabbitmq), jvm metrics, game server lifecycle spans |

## 7. example: distributed trace output

### single request trace (panel → integration → orchestrator → db)

```
Trace: 0af7651916cd43dd8448eb211c80319c
├── Span: panel.dashboard.render          (2ms)    [Management Panel]
│   └── Span: panel.api.fetch.servers     (5ms)    [Management Panel]
│       └── Span: integration.http.POST   (3ms)    [Integration Service]
│           └── Span: orchestrator.provision.server  (850ms) [Orchestrator Agent]
│               ├── Span: cloud.hetzner.create_server (600ms) [Orchestrator Agent]
│               ├── Span: db.query.insert_server      (12ms)  [Orchestrator Agent]
│               └── Span: cache.set.server_state       (2ms)  [Orchestrator Agent]
│                   └── Span: redis.command.set        (1ms)  [Orchestrator Agent]
```

### span with error

```json
{
  "name": "cloud.hetzner.create_server",
  "trace_id": "0af7651916cd43dd8448eb211c80319c",
  "span_id": "b7ad6b7169203331",
  "parent_span_id": "9c8d7e6f5a4b3c2d",
  "start_time": "2026-05-20T12:00:00.000Z",
  "end_time": "2026-05-20T12:00:00.600Z",
  "status": {
    "code": "ERROR",
    "message": "Insufficient resources in fsn1 region"
  },
  "attributes": {
    "infrapilot.server_id": "srv_web_01",
    "infrapilot.provider": "hetzner",
    "infrapilot.region": "fsn1",
    "http.status_code": 507,
    "error.type": "INSUFFICIENT_CAPACITY",
    "error.message": "No available servers in fsn1 region"
  },
  "events": [
    {
      "name": "exception",
      "timestamp": "2026-05-20T12:00:00.600Z",
      "attributes": {
        "exception.type": "HetznerApiException",
        "exception.message": "HTTP 507: Insufficient resources",
        "exception.stacktrace": "HetznerApiException: ..."
      }
    }
  ]
}
```

## 8. effort estimate

| phase | pt | dependencies |
|---|---|---|
| phase 1: sdk integration & auto-instrumentation | 2.5 | feature #14 (api gateway) — for rate limiting on export |
| phase 2: trace propagation | 1.0 | phase 1 |
| phase 3: metrics export | 1.0 | phase 1 |
| phase 4: log correlation | 1.0 | phase 1 |
| phase 5: sampler configuration & performance | 0.5 | phase 1 |
| buffer (15%) | 0.9 | — |
| total | ~6.9 pt | — |

### risk factors

- sdk version compatibility: opentelemetry sdks across languages must agree on otlp version (v0/v1)
- auto-instrumentation blind spots: not all libraries are covered — manual instrumentation needed for custom middleware
- performance at scale: high-throughput services may need judicious sampling to avoid overwhelming the exporter
- java agent compatibility: service core runs java 8+; otel java agent requires java 8 minimum (ok) but may conflict with existing agents (jmx, etc.)

## 9. security & compliance

- otlp connection uses tls by default; mtls supported for mutual authentication
- api keys can be passed via otlp headers for collector authentication
- sampling must never drop error spans with security relevance (auth failures, permission errors)
- span attributes must not include secrets, passwords, or pii; attribute filtering middleware strips sensitive fields
- otel export is outbound-only — no inbound listener required
- all otel configuration is tenant-isolated where applicable (multi-tenant deployments)
