# Feature 34: Distributed Tracing

- **Feature ID:** 34
- **Status:** Planned
- **Priority:** Medium
- **Primary Service:** Integration Service
- **Effort:** Medium (4–6 PT)

---

## 1. Overview

Distributed Tracing adds end-to-end visibility into requests that cross service boundaries within infra-pilot (e.g. a Discord slash command → Integration Service → Orchestrator Agent → Docker API). By adopting OpenTelemetry and exporting traces in Jaeger / Zipkin-compatible format, operators gain latency breakdowns per span, dependency graphs between services, and the ability to pinpoint bottlenecks in complex multi-hop workflows.

---

## 2. Architecture

```
                         ┌──────────────────────┐
                         │   Discord / Slack     │
                         │   (User Request)      │
                         └──────────┬───────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────┐
│                     Integration Service                          │
│                                                                  │
│  ┌───────────────┐   ┌───────────────┐   ┌──────────────────┐   │
│  │ HTTP Router   │──▶│ Handler       │──▶│ OpenTelemetry    │   │
│  │ /api/command  │   │ (business     │   │ SDK (Tracer      │   │
│  │               │   │  logic)       │   │  Provider)       │   │
│  └───────────────┘   └───────┬───────┘   └────────┬─────────┘   │
│                              │                    │             │
│                         ┌────▼────┐               │             │
│                         │ gRPC    │               │             │
│                         │ Client  │               │             │
│                         └────┬────┘               │             │
│                              │ inject context     │             │
│                              ▼                    │             │
└──────────────────────────────┼────────────────────┘             │
                               │                                   │
                               ▼                                   │
┌──────────────────────────────────────────────────┐               │
│                Orchestrator Agent                 │              │
│                                                   │             │
│  ┌──────────────┐  ┌──────────────┐               │             │
│  │ gRPC Server  │─▶│ Runbook      │               │             │
│  │ (extract ctx)│  │ Engine       │               │             │
│  └──────┬───────┘  └──────┬───────┘               │             │
│         │                 │                       │             │
│         │           ┌─────▼──────┐                │             │
│         │           │ Docker     │                │             │
│         │           │ Client     │                │             │
│         │           └─────┬──────┘                │             │
│         │                 │                       │             │
│         │            ┌────▼────┐                  │             │
│         │            │ Span    │                  │             │
│         │            │ Exporter│                  │             │
│         │            └─────────┘                  │             │
│         └─────────────────────────────────────────┘             │
│                                                                  │
│              ┌─────────────────────────────┐                     │
│              │   OTel Collector (Sidecar)  │                     │
│              │   │ batch │ enrich │ export  │                     │
│              └─────────────┬───────────────┘                     │
└────────────────────────────┼─────────────────────────────────────┘
                             │
                             ▼
                ┌─────────────────────────┐
                │    Backend Storage       │
                │                          │
                │  ┌─────────┐ ┌────────┐  │
                │  │ Jaeger  │ │ Zipkin │  │
                │  │ (gRPC)  │ │ (HTTP) │  │
                │  └─────────┘ └────────┘  │
                │  ┌─────────────────────┐  │
                │  │ Elasticsearch /     │  │
                │  │ S3 (long-term)      │  │
                │  └─────────────────────┘  │
                └─────────────────────────┘
```

**Trace flow (example: Discord restart command):**

```
Discord Slash Command: /restart postgres-primary
    ↓
Integration Service ························· span: "handle_command"
    ├─ parse & validate ···················· span: "validate_input"
    ├─ call Orchestrator gRPC ·············· span: "orchestrator.execute_runbook"
    │   └─ Orchestrator Agent
    │       ├─ resolve runbook ············· span: "resolve_runbook"
    │       ├─ exec step: drain-connections  span: "step.drain-connections"
    │       ├─ exec step: manual-approve ··· span: "step.manual-approve"
    │       │   └─ (waiting…)
    │       └─ exec step: restart-service ·· span: "step.restart-service"
    │           └─ docker restart ·········· span: "docker.api.restart"
    └─ respond to Discord ·················· span: "format_response"
```

---

## 3. Trace Context Propagation

Services propagate a W3C `traceparent` header through every protocol boundary:

| Protocol | Propagation Mechanism |
|---|---|
| HTTP (REST APIs) | `traceparent` / `tracestate` HTTP headers |
| gRPC | `grpc-trace-bin` metadata key (via OTel gRPC interceptor) |
| Message Queue (NATS) | Inject context into message headers |
| WebSocket | `traceparent` query parameter on upgrade; context attached to each frame |

**Example HTTP headers:**

```
traceparent: 00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01
tracestate: rojo=00f067aa0ba902b7,congo=t61rcWkgMzE
```

---

## 4. Span Layout

Each trace is composed of spans. Every span has:

| Field | Description |
|---|---|
| `trace_id` | 16-byte hex — shared by all spans in the trace |
| `span_id` | 8-byte hex — unique to this span |
| `parent_span_id` | 8-byte hex — links to the caller span |
| `name` | Short human-readable label (e.g. "docker.api.restart") |
| `kind` | `CLIENT`, `SERVER`, `INTERNAL`, `PRODUCER`, `CONSUMER` |
| `start_time` | Unix nano timestamp |
| `end_time` | Unix nano timestamp |
| `status` | `Unset`, `Ok`, `Error` (with optional description) |
| `attributes` | key-value pairs (service, resource ID, step ID, etc.) |
| `events` | Timestamped log-like annotations within the span |

### Standard Attributes per infra-pilot Span

```go
// All spans
span.SetAttributes(
    attribute.String("service.name", "orchestrator"),
    attribute.String("service.version", "1.2.0"),
    attribute.String("environment", "prod"),
)

// Runbook-related
span.SetAttributes(
    attribute.String("runbook.id", "rb_xyz456"),
    attribute.String("runbook.name", "restart-postgres-primary"),
    attribute.String("execution.id", "exec_789"),
    attribute.String("step.id", "restart-service"),
)

// API calls
span.SetAttributes(
    attribute.String("http.method", "POST"),
    attribute.String("http.url", "https://docker.sock/v1.41/containers/abc/restart"),
    attribute.Int("http.status_code", 204),
)

// Errors
span.SetAttributes(
    attribute.String("error.type", "timeout"),
    attribute.String("error.message", "container restart exceeded 30s timeout"),
)
```

---

## 5. Integration with Jaeger / Zipkin

The OpenTelemetry Collector is deployed as a sidecar or daemonset and configured to export to both Jaeger and Zipkin:

```yaml
# otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    timeout: 1s
    send_batch_size: 1024
  attributes:
    actions:
      - key: infra-pilot.cluster
        value: "prod-us-east"
        action: upsert

exporters:
  jaeger:
    endpoint: jaeger:14250
    tls:
      insecure: true
  zipkin:
    endpoint: http://zipkin:9411/api/v2/spans
  logging:
    loglevel: debug

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch, attributes]
      exporters: [jaeger, zipkin, logging]
```

---

## 6. API Design

### 6.1 Query (proxy to Jaeger/Zipkin API)

The Integration Service exposes a lightweight query proxy:

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/tracing/traces/{trace_id}` | Get full trace by ID |
| `GET` | `/api/v1/tracing/search` | Search traces (service, operation, tags, time range) |
| `GET` | `/api/v1/tracing/services` | List known services |
| `GET` | `/api/v1/tracing/services/{service}/operations` | List operations per service |
| `GET` | `/api/v1/tracing/dependencies` | Get service dependency graph (edges + call count) |

### 6.2 Span Ingestion (internal)

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/tracing/spans` | Accept span batch (Zipkin JSON v2 format) — fallback for services that cannot use OTLP |

---

## 7. Data Model

```json
{
  "trace": {
    "trace_id": "0af7651916cd43dd8448eb211c80319c",
    "spans": [
      {
        "span_id": "b7ad6b7169203331",
        "parent_span_id": "",
        "trace_id": "0af7651916cd43dd8448eb211c80319c",
        "operation_name": "handle_command",
        "kind": "SERVER",
        "start_time": 1716805800000000000,
        "end_time": 1716805805000000000,
        "duration_ns": 5000000000,
        "status": {"code": "OK"},
        "attributes": {
          "service.name": "integration-service",
          "http.method": "POST",
          "http.route": "/api/v1/commands"
        },
        "events": [
          {
            "name": "runbook_execution_started",
            "timestamp": 1716805801000000000,
            "attributes": {"execution_id": "exec_789"}
          }
        ]
      }
    ]
  },

  "dependency_edge": {
    "parent": "integration-service",
    "child": "orchestrator",
    "call_count": 1523,
    "error_count": 12,
    "p99_latency_ms": 3400
  }
}
```

---

## 8. Latency Analysis

| Report | Computation |
|---|---|
| **Span duration** | `end_time − start_time` (nanoseconds → ms) |
| **Critical path** | Longest chain of dependent spans (top-level → leaf) |
| **Service p50/p95/p99** | Percentile aggregation grouped by `service.name` |
| **Error rate** | `count(status.code == ERROR) / count(*)` per operation |
| **SLA breach** | Tags spans where `duration > threshold` (configurable per operation) |

**Management Panel display (latency breakdown):**

```
Trace: handle_command (5.0s)
├─ validate_input ............. 50ms
├─ orchestrator.execute_runbook  
│  ├─ resolve_runbook ........ 10ms
│  ├─ step.drain-connections . 800ms  ◄── bottleneck
│  ├─ step.manual-approve .... 2.0s
│  └─ step.restart-service ... 1.5s
│     └─ docker.api.restart .. 1.2s  ◄── bottleneck
└─ format_response ........... 15ms
```

---

## 9. Management Panel Integration

The Management Panel includes a **Tracing View**:

- **Trace search**: Query by service, operation, tags, time range
- **Trace detail**: Waterfall span view with attribute inspection
- **Service graph**: Force-directed graph of service dependencies with edge latency/error annotations
- **Latency heatmap**: Distribution of span durations over time (p50/p95/p99 lines)

---

## 10. Service Assignments

| Service | Responsibilities |
|---|---|
| **Integration Service** | OTel SDK setup, context propagation middleware, trace query proxy, dependency graph calculation |
| **Orchestrator Agent** | OTel SDK, wrap runbook execution steps as child spans, inject context into Docker API calls |
| **Management Panel** | Trace search UI, waterfall view, service graph, latency analysis dashboards |
| **Event Store** | Persist trace IDs on execution records for cross-referencing |
| **DevOps** | Deploy OTel Collector, Jaeger, Zipkin; manage retention policies |

---

## 11. Effort Estimate

| Phase | Tasks | PT |
|---|---|---|
| Design | Span taxonomy, attribute dictionary, context propagation strategy | 0.5 |
| OTel SDK integration | Instrument Integration Service, Orchestrator, Management Panel | 1.5 |
| Context propagation | gRPC interceptors, HTTP middleware, message queue headers | 1 |
| Collector config | Sidecar deployment, batch processor, Jaeger/Zipkin exporters | 0.5 |
| Query proxy | Trace search, service/operation listing, dependency graph | 0.5 |
| Management UI | Trace waterfall, service graph, latency panels | 1.5 |
| Testing & validation | End-to-end trace verification, latency budget assertions | 0.5 |
| **Total** | | **4–6** |

---

## 12. Future Considerations

- **Sampling**: Head-based probabilistic sampling for high-throughput services (e.g. 1% at Discord gateway, 100% at runbook execution)
- **Tail-based sampling**: Keep traces that contain errors regardless of probability
- **SLO dashboards**: Red metrics (request rate, error rate, duration) per service + operation
- **Trace-to-log correlation**: Embed `trace_id` in structured log entries for log → trace jumping
