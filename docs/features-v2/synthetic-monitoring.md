# feature 37: synthetic monitoring

- feature id: 37
- category: advanced observability
- primary service: orchestrator agent
- effort: medium (4-6 pt)
- dependencies: feature 13 (webhook event bus), feature 36 (slo tracking)

## overview

deploy a global network of synthetic monitoring probes that simulate real user traffic to verify service availability, performance, and correctness. run http/s checks, tcp port checks, minecraft server pings, ssl certificate expiry monitoring, and dns resolution tests from multiple geographic locations. alert immediately when degradation is detected and track response time trends over time.

### supported check types

| check type | description | metrics collected |
|---|---|---|
| http/https | full request/response validation | status code, response time, body match, redirect chain |
| tcp port | tcp connect check | connection time, port open/closed |
| icmp ping | network layer reachability | packet loss %, round-trip time |
| ssl/tls | certificate validity check | days to expiry, issuer, sans, chain validity |
| dns resolution | record lookup verification | resolution time, record match, nxdomain detection |
| minecraft ping | minecraft server query | online status, player count, motd, version, latency |

## architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                        Management Panel                             │
│  Check Configuration  │  Probe Map  │  Results Dashboard  │  Alerts │
└─────────────────────────────────┬──────────────────────────────────┘
                                  │
┌─────────────────────────────────▼──────────────────────────────────┐
│                      Orchestrator Agent                            │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                   Synthetic Monitor Core                      │  │
│  │  ┌─────────────┐ ┌──────────────┐ ┌──────────────────────┐  │  │
│  │  │  Check       │ │  Schedule    │ │  Result Aggregator   │  │  │
│  │  │  Definition  │ │  Engine      │ │  (multi-probe merge) │  │  │
│  │  └─────────────┘ └──────────────┘ └──────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                  │                                  │
│  ┌───────────────────────────────▼──────────────────────────────┐  │
│  │                    Probe Dispatcher                            │  │
│  │  Routes checks to nearest/available probe locations           │  │
│  └───────────────────────────────┬──────────────────────────────┘  │
└──────────────────────────────────┬─────────────────────────────────┘
                                   │
┌──────────────────────────────────▼─────────────────────────────────┐
│                      Global Probe Network                            │
│                                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │ Probe    │  │ Probe    │  │ Probe    │  │ Probe    │   ... (N)  │
│  │ us-east  │  │ eu-west  │  │ ap-south │  │ sa-east  │           │
│  │          │  │          │  │          │  │          │           │
│  │ HTTP TCP │  │ HTTP TCP │  │ HTTP TCP │  │ HTTP TCP │           │
│  │ Ping SSL │  │ Ping SSL │  │ Ping SSL │  │ Ping SSL │           │
│  │ DNS MC   │  │ DNS MC   │  │ DNS MC   │  │ DNS MC   │           │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘           │
└────────────────────────────────────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼─────────────────────────────────┐
│                      Data & Notification Sinks                       │
│  ┌──────────────┐  ┌────────────────┐  ┌────────────────────────┐  │
│  │ Prometheus   │  │ Alert Manager  │  │ Integration Service    │  │
│  │ (metrics)    │  │ (notifications) │  │ (SLO engine, webhooks) │  │
│  └──────────────┘  └────────────────┘  └────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
```

### probe location architecture

each probe is a lightweight docker container running a python agent that:

• connects to the orchestrator agent via grpc for configuration and heartbeat
• pulls its assigned check schedule every 60s
• executes checks and reports results asynchronously
• stores a local buffer (last 1000 results) for offline resilience
• reports its own health (cpu, memory, connectivity) to the orchestrator

### planned probe locations (initial)

| location | region | provider |
|---|---|---|
| us-east-1 | n. virginia | aws |
| us-west-1 | n. california | aws |
| eu-west-1 | ireland | aws |
| eu-central-1 | frankfurt | aws |
| ap-southeast-1 | singapore | aws |
| sa-east-1 | sao paulo | aws |
| eu-west-2 | london | hetzner |

## data model

### check definition

```yaml
synthetic_check:
  id: "check-http-web-prod"
  name: "Web Production Health Check"
  type: "http"                      # http | tcp | ping | ssl | dns | minecraft
  enabled: true
  interval_seconds: 300
  timeout_ms: 10000
  retry_count: 2
  probe_locations:
    - "us-east-1"
    - "eu-west-1"
    - "ap-southeast-1"
  targets:
    http:
      url: "https://app.example.com/health"
      method: "GET"
      expected_status: 200
      expected_body_regex: "\"status\":\"ok\""
      follow_redirects: true
      headers:
        User-Agent: "InfraPilot-Synthetic/1.0"
    tcp:
      host: "db.internal"
      port: 5432
    ssl:
      host: "app.example.com"
      port: 443
      warn_days_before_expiry: 30
      crit_days_before_expiry: 14
    dns:
      hostname: "app.example.com"
      record_type: "A"
      expected_values:
        - "203.0.113.42"
    minecraft:
      host: "mc.example.com"
      port: 25565
      expected_online: true
      min_player_threshold: 0
  alerts:
    enabled: true
    cooldown_minutes: 15
    channels:
      - "discord"
      - "email"
  labels:
    team: "platform"
    environment: "production"
```

### check result

```yaml
check_result:
  id: "res-wXk3m9qR"
  check_id: "check-http-web-prod"
  probe_location: "us-east-1"
  executed_at: 1745712345
  duration_ms: 342
  status: "pass"                    # pass | fail | error
  type: "http"
  data:
    http:
      status_code: 200
      response_time_ms: 312
      body_length: 4523
      tls_version: "TLSv1.3"
      redirect_chain: []
    tcp:
      connection_time_ms: 45
      port_open: true
    ssl:
      days_remaining: 187
      issuer: "Let's Encrypt Authority X3"
      subject_cn: "app.example.com"
      valid: true
      chain_valid: true
    dns:
      resolution_time_ms: 23
      resolved_ips: ["203.0.113.42"]
      records_match: true
    minecraft:
      online: true
      players_online: 42
      max_players: 100
      motd: "§aWelcome to Example MC"
      version: "1.20.4"
      latency_ms: 78
  error: null                       # Error message on failure
  raw_output: null                  # Stored for debugging (truncated)
```

### probe agent

```yaml
probe_agent:
  id: "probe-us-east-1"
  location: "us-east-1"
  status: "online"
  version: "1.2.0"
  last_heartbeat: 1745712345
  checks_assigned: 47
  checks_completed_total: 142305
  checks_failed_total: 312
  avg_execution_time_ms: 284
  resources:
    cpu_usage_percent: 23.4
    memory_usage_mb: 128
    network_rx_bytes: 1048576
    network_tx_bytes: 524288
```

## api design

### check management

#### list checks

```
GET /api/v2/synthetic/checks
  ?type=http
  &status=active
  &page=1
  &per_page=50
```

#### create check

```
POST /api/v2/synthetic/checks
```

```json
{
  "name": "Web Production Health Check",
  "type": "http",
  "interval_seconds": 300,
  "timeout_ms": 10000,
  "retry_count": 2,
  "probe_locations": ["us-east-1", "eu-west-1"],
  "targets": {
    "http": {
      "url": "https://app.example.com/health",
      "method": "GET",
      "expected_status": 200,
      "expected_body_regex": "\"status\":\"ok\""
    }
  },
  "alerts": {
    "enabled": true,
    "cooldown_minutes": 15
  },
  "labels": {
    "team": "platform"
  }
}
```

response `201`:
```json
{
  "id": "check-http-web-prod",
  "status": "active",
  "created_at": "2026-05-01T00:00:00Z"
}
```

#### get check details

```
GET /api/v2/synthetic/checks/{check_id}
```

#### update check

```
PATCH /api/v2/synthetic/checks/{check_id}
```

#### delete check

```
DELETE /api/v2/synthetic/checks/{check_id}
```

#### trigger immediate check

```
POST /api/v2/synthetic/checks/{check_id}/run
```

```json
{
  "probe_locations": ["us-east-1", "eu-west-1"]
}
```

### results

#### get latest results

```
GET /api/v2/synthetic/checks/{check_id}/results/latest
```

#### query results history

```
GET /api/v2/synthetic/checks/{check_id}/results
  ?start=2026-05-01T00:00:00Z
  &end=2026-05-31T23:59:59Z
  &probe_location=us-east-1
  &status=fail
  &page=1
  &per_page=100
```

#### get response time series

```
GET /api/v2/synthetic/checks/{check_id}/timeseries
  ?window=24h
  &granularity=5m
  &aggregate=avg
```

### probes

#### list probes

```
GET /api/v2/synthetic/probes
```

#### get probe details

```
GET /api/v2/synthetic/probes/{probe_id}
```

#### get probe heartbeat log

```
GET /api/v2/synthetic/probes/{probe_id}/heartbeats
  ?window=24h
```

## implementation plan

### phase 1: probe runner & check execution (pt 1-2)

| step | description | artifacts |
|---|---|---|
| 1.1 | define check configuration schema and db models | `models/synthetic.py` |
| 1.2 | implement check executors: http, tcp, ping | `executors/http.py`, `executors/tcp.py`, `executors/ping.py` |
| 1.3 | implement check executors: ssl, dns, minecraft | `executors/ssl.py`, `executors/dns.py`, `executors/minecraft.py` |
| 1.4 | build probe agent bootstrap script + dockerfile | `infra/probe-agent/Dockerfile`, `probe_agent.py` |

### phase 2: orchestration & scheduling (pt 3-4)

| step | description | artifacts |
|---|---|---|
| 2.1 | probe dispatcher: assign checks to probes, load balancing | `services/probe_dispatcher.py` |
| 2.2 | schedule engine: cron-like intervals with jitter | `services/schedule_engine.py` |
| 2.3 | result aggregator: merge multi-probe results, deduplicate | `services/result_aggregator.py` |
| 2.4 | probe agent heartbeats and health monitoring | `services/probe_health.py` |

### phase 3: alerting & dashboard (pt 5-6)

| step | description | artifacts |
|---|---|---|
| 3.1 | alert evaluation: degradation detection, multi-probe consensus | `services/alert_evaluator.py` |
| 3.2 | rest api endpoints for checks, results, probes | `routes/synthetic.py` |
| 3.3 | panel ui: check list, create/edit form, probe map | panel components |
| 3.4 | panel ui: results dashboard, response time charts, alert history | panel components |

## service assignments

| service | responsibility |
|---|---|
| orchestrator agent (primary) | check definition management, probe dispatch, schedule engine, result aggregation, alert evaluation, rest api |
| probe agent (new sub-component) | lightweight python agent deployed at each location, executes checks, reports results |
| management panel | check configuration ui, results dashboard, probe map visualization, alert configuration |
| integration service | receives check results for slo integration, webhook dispatch on alert |
| discord service | alert notifications with check status, response time graphs |

## effort estimate: medium (4-6 pt)

| area | pt estimate |
|---|---|
| check executors (http, tcp, ping, ssl, dns, minecraft) | 1.5 |
| probe agent + docker image | 1.0 |
| probe dispatcher + schedule engine | 1.0 |
| result aggregation + alert evaluation | 1.0 |
| rest api endpoints | 0.5 |
| panel ui (check config, results dashboard, probe map) | 1.5 |
| integration + e2e tests | 0.5 |
| documentation | 0.5 |
| total | **7.5 pt (rounded to 6 with framework reuse)** |

### risk factors

- minecraft protocol parsing may need library adaptation (use `mcstatus` python library)
- probe network deployment requires at least 3 cloud regions for meaningful multi-region coverage
- ssl check accuracy depends on proper sni support and certificate chain validation
- dns check reliability may vary by probe location's upstream resolver behavior

## key metrics

| metric | target |
|---|---|
| check execution frequency | every 60s minimum, configurable per check |
| end-to-end result latency | < 5s from execution to api |
| probe locations at launch | 7 (aws regions + hetzner) |
| maximum checks per probe | 500 |
| probe agent resource usage | < 256 mb ram, < 0.5 cpu core |
| api throughput | 200 req/s for results ingestion |
