# ai log anomaly detector

feature id: 1
category: ai & intelligence
primary service: integration service
effort estimate: large (7-10 pt)
status: planned

## overview

train an unsupervised ml model on historical server logs to detect anomalous patterns in real time. the detector identifies crash loops, intrusion attempts, silent failures, and other irregular log sequences that would otherwise go unnoticed until a customer reports an issue.

alerts are pushed to the management panel via websocket and optionally forwarded to discord, slack, or email.

### goals

- reduce mean time to detection (mttd) for silent failures from hours to seconds
- automatically surface crash loops and repeated error patterns before they cascade
- distinguish genuine anomalies from expected noise (deployments, scheduled restarts)
- provide a feedback loop for operators to mark false positives, improving model accuracy over time

## architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Log Sources                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │  Docker  │  │ Systemd  │  │  Nginx   │  │ App    │ │
│  │  daemon  │  │  journal │  │  access  │  │ logs   │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └───┬────┘ │
└───────┼──────────────┼────────────┼─────────────┼───────┘
        │              │            │             │
        ▼              ▼            ▼             ▼
┌─────────────────────────────────────────────────────────┐
│              Integration Service                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │           Log Collection Pipeline                 │   │
│  │  ┌─────────┐  ┌──────────┐  ┌─────────────────┐ │   │
│  │  │  Agent  │──│ Buffer & │──│ Feature          │ │   │
│  │  │  Sidecar│  │ Batch    │  │ Extraction       │ │   │
│  │  └─────────┘  └──────────┘  └────────┬─────────┘ │   │
│  └──────────────────────────────────────────────────┘   │
│                        │                                 │
│                        ▼                                 │
│  ┌──────────────────────────────────────────────────┐   │
│  │           Anomaly Detection Engine                │   │
│  │  ┌──────────────────┐  ┌──────────────────────┐ │   │
│  │  │ Isolation Forest │  │ LSTM Sequence        │ │   │
│  │  │ (pattern scoring)│  │ (temporal analysis)  │ │   │
│  │  └────────┬─────────┘  └──────────┬───────────┘ │   │
│  │           │                       │              │   │
│  │           ▼                       ▼              │   │
│  │  ┌──────────────────────────────────────────┐    │   │
│  │  │         Ensemble Scorer                   │    │   │
│  │  │  Combines model outputs → anomaly_score   │    │   │
│  │  └──────────────────┬───────────────────────┘    │   │
│  └─────────────────────┼────────────────────────────┘   │
│                        │                                 │
│                        ▼                                 │
│  ┌──────────────────────────────────────────────────┐   │
│  │           Alert Manager                           │   │
│  │  ┌──────────┐  ┌──────────┐  ┌────────────────┐ │   │
│  │  │ Dedup &  │──│ Severity │──│ Notify (WS,    │ │   │
│  │  │ Throttle │  │ Routing  │  │ Discord, Slack)│ │   │
│  │  └──────────┘  └──────────┘  └────────────────┘ │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│              Management Panel                            │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Realtime Alert Feed (WebSocket)                  │   │
│  │  Anomaly Detail View                             │   │
│  │  Feedback Buttons: ✓ True Anomaly / ✗ False Pos  │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## implementation plan

### phase 1: log collection pipeline (2-3 pt)

| step | description | artifacts |
|------|-------------|-----------|
| 1.1 | deploy log-agent sidecar to all managed nodes | log shipper (fluentd vector), config per node type |
| 1.2 | central log buffer with kafka or redis streams | buffered log topics, retention policy (7d raw, 90d aggregated) |
| 1.3 | log parsing & normalization | structured schema: `{timestamp, source, level, message, service, host, container_id}` |
| 1.4 | feature extraction service | extracted features written to time-series store |

**feature extraction logic:**

```python
# pseudocode: log_feature_extractor.py
def extract_features(log_batch: list[dict]) -> dict:
    features = {
        "error_rate": count_errors(log_batch) / len(log_batch),
        "unique_error_types": count_unique(match_pattern(log_batch, ERROR_PATTERNS)),
        "log_volume_delta": len(log_batch) - rolling_avg("log_volume", window=300),
        "temporal_entropy": shannon_entropy([l["level"] for l in log_batch]),
        "keyword_scores": {
            kw: score_keyword_occurrence(log_batch, kw)
            for kw in ["timeout", "exception", "failed", "denied", "crash"]
        },
        "burst_score": detect_burst_pattern(log_batch, interval_ms=1000),
    }
    return features
```

### phase 2: model training pipeline (3-4 pt)

| step | description | artifacts |
|------|-------------|-----------|
| 2.1 | historical log export & labeling | labeled dataset (anomaly / normal) from past incidents |
| 2.2 | train isolation forest model | `model/isolation_forest.pkl` |
| 2.3 | train lstm sequence model | `model/lstm_anomaly.h5` with sequence length=100 |
| 2.4 | ensemble calibrator | weight optimizer for combining model outputs |
| 2.5 | model versioning & a/b deployment | mlflow registry, canary deployment strategy |

**model config:**

```yaml
# config/anomaly_detector.yaml
model:
  ensemble:
    isolation_forest:
      enabled: true
      n_estimators: 200
      contamination: 0.01
      max_samples: 256
    lstm:
      enabled: true
      sequence_length: 100
      epochs: 50
      batch_size: 32
      lstm_units: [64, 32]
  scoring:
    threshold_mode: "dynamic" # dynamic | static
    static_threshold: 0.85
    dynamic_percentile: 95
    dynamic_window: 3600 # seconds

pipeline:
  batch_size: 5000
  flush_interval_ms: 5000
  feature_window_s: 300

feedback:
  store_false_positives: true
  retrain_interval_hours: 168 # weekly
  min_feedback_samples: 100
```

### phase 3: alerting & feedback loop (2-3 pt)

| step | description | artifacts |
|------|-------------|-----------|
| 3.1 | alert deduplication engine | hash-based dedup, suppression per source + pattern |
| 3.2 | severity classification | critical / warning / info based on anomaly score + source |
| 3.3 | websocket push to panel | real-time alert feed |
| 3.4 | notification integrations | discord embed, slack message, email |
| 3.5 | feedback ingestion api | `POST /api/v1/anomalies/{id}/feedback` |
| 3.6 | scheduled retraining pipeline | cron trigger, dataset refresh, model promotion |

## api design

### anomaly events (websocket)

**topic:** `ws://<host>/ws/v1/events`
**event type:** `anomaly.detected`

```json
{
  "event": "anomaly.detected",
  "data": {
    "id": "anom-20260527-abc123",
    "timestamp": "2026-05-27T14:23:11Z",
    "severity": "warning",
    "score": 0.91,
    "source": "docker:web-01",
    "service": "nginx",
    "pattern": "connection_timeout_burst",
    "summary": "5x timeout spike in 60s window on web-01",
    "affected_logs": [
      {"line": 1452, "message": "2026-05-27T14:22:50Z [error] upstream timed out (110)"},
      {"line": 1453, "message": "2026-05-27T14:22:51Z [error] upstream timed out (110)"}
    ],
    "features_snapshot": {
      "error_rate": 0.18,
      "log_volume_delta": 340,
      "keyword_timeout": 0.92
    }
  }
}
```

### rest api

#### list anomalies

```
GET /api/v1/anomalies
  ?severity=critical,warning
  &source=web-01
  &from=2026-05-01T00:00:00Z
  &to=2026-05-27T23:59:59Z
  &status=open,acknowledged,resolved
  &limit=50
  &offset=0
```

response:
```json
{
  "anomalies": [
    {
      "id": "anom-20260527-abc123",
      "severity": "warning",
      "score": 0.91,
      "source": "docker:web-01",
      "pattern": "connection_timeout_burst",
      "summary": "5x timeout spike in 60s window on web-01",
      "status": "open",
      "detected_at": "2026-05-27T14:23:11Z",
      "acknowledged_by": null,
      "resolved_at": null
    }
  ],
  "total": 47,
  "limit": 50,
  "offset": 0
}
```

#### submit feedback

```
POST /api/v1/anomalies/{id}/feedback
```

request:
```json
{
  "is_true_positive": false,
  "correct_label": "deployment_artifact",
  "comment": "This was during rolling deploy, expected pattern",
  "submitted_by": "ops-admin"
}
```

#### get anomaly details

```
GET /api/v1/anomalies/{id}
```

#### acknowledge / resolve

```
PATCH /api/v1/anomalies/{id}
```

request:
```json
{
  "status": "acknowledged",
  "assigned_to": "sre-team"
}
```

## data model

```python
# models/anomaly.py
@dataclass
class LogEvent:
    timestamp: datetime
    source: str          # e.g. "docker:web-01"
    service: str         # e.g. "nginx", "postgres"
    level: str           # DEBUG, INFO, WARN, ERROR, FATAL
    message: str
    host: str
    container_id: str | None
    raw: str

@dataclass
class LogFeatureVector:
    window_start: datetime
    window_end: datetime
    source: str
    error_rate: float
    unique_error_types: int
    log_volume_delta: float
    temporal_entropy: float
    keyword_scores: dict[str, float]
    burst_score: float
    embedding: list[float] | None  # LSTM encoder output

@dataclass
class AnomalyEvent:
    id: str
    timestamp: datetime
    severity: str          # critical / warning / info
    score: float           # 0.0 - 1.0
    source: str
    service: str
    pattern: str           # ML-classified pattern label
    summary: str
    affected_logs: list[dict]
    features_snapshot: dict
    status: str            # open / acknowledged / resolved / dismissed
    acknowledged_by: str | None
    resolved_at: datetime | None
    feedback: list[Feedback] | None

@dataclass
class Feedback:
    anomaly_id: str
    is_true_positive: bool
    correct_label: str | None
    comment: str | None
    submitted_by: str
    submitted_at: datetime
```

**database schema (postgresql + timescaledb):**

```sql
-- Log events (raw, short retention)
CREATE TABLE log_events (
    id          BIGSERIAL,
    timestamp   TIMESTAMPTZ NOT NULL,
    source      TEXT NOT NULL,
    service     TEXT,
    level       TEXT NOT NULL,
    message     TEXT NOT NULL,
    host        TEXT,
    container_id TEXT,
    raw         TEXT
) PARTITION BY RANGE (timestamp);

-- Features (aggregated, medium retention)
CREATE TABLE log_features (
    window_start    TIMESTAMPTZ NOT NULL,
    window_end      TIMESTAMPTZ NOT NULL,
    source          TEXT NOT NULL,
    error_rate      DOUBLE PRECISION,
    unique_errors   INTEGER,
    log_volume_delta DOUBLE PRECISION,
    temporal_entropy DOUBLE PRECISION,
    keyword_scores  JSONB,
    burst_score     DOUBLE PRECISION,
    embedding       VECTOR(128),
    PRIMARY KEY (window_start, source)
);

-- Anomaly events (long retention)
CREATE TABLE anomaly_events (
    id              TEXT PRIMARY KEY,
    detected_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    severity        TEXT NOT NULL,
    score           DOUBLE PRECISION NOT NULL,
    source          TEXT NOT NULL,
    service         TEXT,
    pattern         TEXT,
    summary         TEXT,
    features_snapshot JSONB,
    status          TEXT NOT NULL DEFAULT 'open',
    acknowledged_by TEXT,
    resolved_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Feedback
CREATE TABLE anomaly_feedback (
    id              SERIAL PRIMARY KEY,
    anomaly_id      TEXT REFERENCES anomaly_events(id),
    is_true_positive BOOLEAN NOT NULL,
    correct_label   TEXT,
    comment         TEXT,
    submitted_by    TEXT NOT NULL,
    submitted_at    TIMESTAMPTZ DEFAULT NOW()
);
```

## service assignments

| service | responsibility |
|---------|---------------|
| integration service | log collection pipeline, feature extraction, model inference, alert manager, feedback api |
| orchestrator agent | deploy log-agent sidecar configuration, manage log buffer infrastructure (kafka/redis) |
| management panel | websocket alert feed, anomaly detail view, feedback ui, historical search |
| discord bot / notifications | forward critical anomalies to discord/slack channels |

## configuration reference

```yaml
# config/log_agent.yaml
agent:
  collection:
    sources:
      - type: tail
        path: /var/log/nginx/*.log
        parser: nginx
      - type: journald
        filter:
          - unit: docker.service
          - unit: sshd.service
    buffer_max_size: 10MB
    flush_interval_s: 5
  enrich:
    add_hostname: true
    add_container_labels: true
```

```json
// config/anomaly_alerts.json
{
  "channels": {
    "panel": { "enabled": true, "websocket_topic": "anomaly.detected" },
    "discord": { "enabled": true, "webhook_url": "{{ secrets.DISCORD_ALERT_WEBHOOK }}" },
    "slack": { "enabled": false, "webhook_url": "" },
    "email": { "enabled": true, "recipients": ["sre@example.com"], "throttle_minutes": 15 }
  },
  "severity_rules": {
    "critical": { "notify_all": true, "auto_create_incident": true },
    "warning": { "notify_discord": true, "auto_create_incident": false },
    "info": { "notify_panel_only": true }
  }
}
```

## effort breakdown

| phase | task | pt | dependencies |
|-------|------|----|-------------|
| 1.1 | log agent sidecar deployment | 1 | docker orchestration |
| 1.2 | central log buffer setup (kafka/redis) | 1 | infrastructure |
| 1.3 | log parsing & normalization | 0.5 | log schema definition |
| 1.4 | feature extraction service | 1 | parsing pipeline |
| 2.1 | historical dataset preparation | 1 | phase 1 completion |
| 2.2 | isolation forest training | 1 | labeled dataset |
| 2.3 | lstm training | 1.5 | gpu-available infra |
| 2.4 | ensemble calibrator | 0.5 | both models trained |
| 2.5 | model registry & deployment | 0.5 | mlflow setup |
| 3.1 | alert deduplication | 0.5 | anomaly event schema |
| 3.2 | severity classification | 0.5 | scoring pipeline |
| 3.3 | websocket push | 0.5 | panel websocket infra |
| 3.4 | notification integrations | 0.5 | discord/slack webhooks |
| 3.5 | feedback api | 0.5 | rest api framework |
| 3.6 | scheduled retraining | 0.5 | cron + mlflow |
| | total | 10.5 | |

## risks & mitigations

| risk | impact | mitigation |
|------|--------|------------|
| high false-positive rate | alert fatigue, ignored alerts | feedback loop, dynamic threshold tuning, ensemble scoring |
| log volume at scale | storage costs, latency | sampling for high-volume sources, tiered retention, kafka compression |
| model drift over time | degraded detection accuracy | weekly retraining, drift monitoring, automatic rollback to previous model |
| privacy / sensitive logs | compliance violation | pii redaction pipeline, configurable exclude patterns, audit trail |

## metrics & kpis

| metric | target | measurement |
|--------|--------|-------------|
| mttd (mean time to detect) | < 30s | time from error to anomaly event creation |
| precision (accuracy of alerts) | > 90% | true positives / (tp + fp) |
| recall (anomalies caught) | > 85% | tp / (tp + fn) from post-mortem review |
| feedback response rate | > 20% of alerts | feedback count / total anomaly events |
| model training time | < 4 hours | end-to-end pipeline duration |
