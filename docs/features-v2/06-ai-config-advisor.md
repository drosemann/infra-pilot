# ai config advisor

| field | value |
|-------|-------|
| id | f-006 |
| name | ai config advisor |
| category | ai & intelligence |
| primary service | management panel |
| effort | medium (4-6 pt) |
| dependencies | feature 13 (webhook event bus), feature 14 (api gateway) |
| phase | phase 1 |

## overview

the ai config advisor analyzes server configuration files (jvm flags, yaml, properties, toml, json) against a comprehensive database of best practices. it identifies suboptimal settings, security risks, and performance bottlenecks, then presents clear recommendations with a one-click apply mechanism including diff preview.

### goals

- reduce server misconfiguration incidents by 60%
- surface 10+ actionable recommendations per average server scan
- enable one-click safe application of config changes
- provide clear before/after diff for every suggested change

### non-goals

- not a configuration management system (no continuous sync)
- does not modify configs without explicit user approval
- not responsible for runtime config reload -- applies changes to files only

## architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Management Panel (Frontend)                   │
│  ┌──────────┐  ┌──────────────┐  ┌──────────┐  ┌────────────┐ │
│  │ Config   │  │ Scan Results │  │ Diff     │  │ One-Click │ │
│  │ Explorer │  │ Dashboard    │  │ Viewer   │  │ Apply      │ │
│  └────┬─────┘  └──────┬───────┘  └────┬─────┘  └─────┬──────┘ │
└───────┼───────────────┼───────────────┼───────────────┼────────┘
        │               │               │               │
┌───────▼───────────────▼───────────────▼───────────────▼────────┐
│                    Management Panel (API / Backend)              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐ │
│  │ Config Fetcher   │  │ Rule Engine      │  │ Apply Engine   │ │
│  │ ┌──────────────┐ │  │ ┌──────────────┐ │  │ ┌────────────┐ │ │
│  │ │SSH Connector │ │  │ │Pattern Match │ │  │ │Backup      │ │ │
│  │ │API Connector │ │  │ │Value Check   │ │  │ │File Patch  │ │ │
│  │ │File Upload   │ │  │ │Cross-ref     │ │  │ │Rollback    │ │ │
│  │ └──────────────┘ │  │ └──────────────┘ │  │ └────────────┘ │ │
│  └──────────────────┘  └────────┬─────────┘  └────────────────┘ │
└─────────────────────────────────┼───────────────────────────────┘
                                  │
┌─────────────────────────────────▼───────────────────────────────┐
│                       Rule Engine Backend                        │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐ │
│  │ JVM Rule   │  │ YAML Rule  │  │ Security   │  │ Performance│ │
│  │ Set        │  │ Set        │  │ Rule Set   │  │ Rule Set   │ │
│  ├────────────┤  ├────────────┤  ├────────────┤  ├────────────┤ │
│  │-Xmx sizing │  │indent      │  │open ports  │  │pool sizes  │ │
│  │GC tuning   │  │anchor dup  │  │credentials │  │timeout     │ │
│  │heap ratio  │  │schema valid│  │tls version │  │buffer sizes│ │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘ │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │               Best Practice Database                        │ │
│  │  (versioned, curated, community-contributable rules)        │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### data flow

```
User clicks "Scan" ──► Config Fetcher retrieves files
                           │
                           ▼
                    Rule Engine matches rules
                           │
                           ▼
                    Results ranked by severity/impact
                           │
                           ▼
                    User reviews in Diff Viewer
                           │
                    ┌──────┴──────┐
                    ▼              ▼
              Apply All     Select Individual
                    │              │
                    ▼              ▼
              Backup original ──► Patch file
                           │
                           ▼
                    Apply result notification
```

## implementation plan

### phase 1: core engine (week 1-2, 2 pt)

1. **config parser library** -- build parsers for:
   - jvm flags (`-x`, `-xx:` notation)
   - yaml/toml/json (using existing libraries)
   - java `.properties` files
   - `.env` files
   - generic key=value formats
   - xml (server.xml, web.xml)

2. **config fetcher module**
   - ssh-based file retrieval (agentless)
   - api-based fetch for agent-managed servers
   - direct file upload from panel
   - git repository source support

3. **data model** -- implement `configurationfile`, `configentry`, `rule`, `routeresult` models (see below)

### phase 2: rule engine & database (week 2-3, 1.5 pt)

1. **rule engine** -- build with:
   - pattern matching (regex, jsonpath, jmespath, xpath)
   - value comparison (range, set membership, semantic version)
   - cross-file reference checks
   - context-aware rules (e.g., "if x is set, y should also be set")

2. **best practice database**
   - 50+ curated v1 rules
   - versioned rule schema with semantic versioning
   - community contribution pipeline
   - auto-update mechanism

3. **rule categories**

| Category | Example Rules | Source |
|----------|--------------|--------|
| JVM Memory | `-Xmx` should not exceed 80% of available RAM | Oracle docs |
| JVM GC | Use G1GC for heaps >4 GB, ZGC for >32 GB | OpenJDK |
| YAML Style | 2-space indentation, no tab characters | YAML spec |
| Security | No hardcoded passwords, TLS 1.2+ only | OWASP |
| Performance | Connection pool size ≤ (core_count * 2) + 1 | HikariCP |
| Minecraft | `view-distance` ≤ 10 for <4 GB RAM, simulation-distance ≤ view-distance | PaperMC |

### phase 3: apply engine & ui (week 3-4, 2.5 pt)

1. **apply engine**
   - automatic file backup before any modification
   - atomic file patching with verification
   - rollback mechanism (undo last apply)
   - dry-run mode (no changes, just report what would change)

2. **diff viewer** -- side-by-side diff with:
   - syntax-highlighted before/after
   - line-level change highlighting
   - accept/reject per change
   - comment annotation

3. **dashboard integration**
   - scan history with trend tracking
   - configuration health score (0-100)
   - exportable reports (pdf, html)
   - scheduled recurring scans

## api design

### endpoints

all endpoints are prefixed with `/api/v2/config-advisor`.

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/scan` | Trigger a new config scan for a server |
| `GET`  | `/scan/{scanId}` | Get scan results |
| `GET`  | `/scan/{scanId}/diff/{recommendationId}` | Get diff for a specific recommendation |
| `POST` | `/scan/{scanId}/apply` | Apply selected or all recommendations |
| `POST` | `/scan/{scanId}/apply/{recommendationId}` | Apply a single recommendation |
| `POST` | `/scan/{scanId}/rollback` | Rollback last apply operation |
| `GET`  | `/rules` | List available rules |
| `POST` | `/rules` | Add a custom rule |
| `GET`  | `/history` | Get scan history for a server |
| `GET`  | `/health-score` | Get configuration health score |

### request/response examples

**POST /api/v2/config-advisor/scan**

```json
{
  "server_id": "srv-a1b2c3d4",
  "source": "ssh",
  "ssh_config": {
    "host": "192.168.1.100",
    "port": 22,
    "username": "root",
    "auth_method": "key",
    "key_id": "key-xyz789"
  },
  "include_patterns": [
    "*.yml", "*.yaml", "*.properties",
    "*.json", "*.toml", "*.env",
    "*.sh", "*.bat"
  ],
  "exclude_patterns": [
    "*/logs/*", "*/cache/*", "*/plugins/*"
  ],
  "options": {
    "dry_run": false,
    "severity_threshold": "info",
    "max_recommendations": 50
  }
}
```

**response**

```json
{
  "scan_id": "scan-20260527-abc123",
  "status": "completed",
  "server_id": "srv-a1b2c3d4",
  "scanned_at": "2026-05-27T14:30:00Z",
  "files_scanned": 24,
  "total_entries": 847,
  "recommendations": [
    {
      "id": "rec-001",
      "rule_id": "jvm-xmx-ratio",
      "category": "JVM Memory",
      "severity": "warning",
      "title": "JVM max heap too large for available memory",
      "description": "-Xmx is set to 12 GB but available RAM is 8 GB",
      "file": "/etc/infrapilot/server.conf",
      "line": 12,
      "current_value": "-Xmx12g",
      "suggested_value": "-Xmx6g",
      "impact": "risk",
      "effort": "low"
    },
    {
      "id": "rec-002",
      "rule_id": "yaml-indent",
      "category": "YAML Style",
      "severity": "info",
      "title": "Inconsistent indentation",
      "description": "Mixing 2-space and 4-space indentation in server.yml",
      "file": "/opt/minecraft/server.yml",
      "line": 47,
      "current_value": "    view-distance: 12",
      "suggested_value": "  view-distance: 12",
      "impact": "style",
      "effort": "low"
    }
  ],
  "health_score": {
    "overall": 62,
    "categories": {
      "JVM Memory": 45,
      "YAML Style": 80,
      "Security": 55,
      "Performance": 70
    }
  },
  "summary": {
    "critical": 0,
    "warning": 1,
    "info": 3,
    "style": 2
  }
}
```

## data model

### core entities

```yaml
ConfigurationFile:
  id: string (UUID)
  server_id: string
  path: string
  format: "yaml" | "json" | "toml" | "properties" | "jvm_flags" | "env" | "xml"
  content_hash: string (SHA-256)
  size_bytes: integer
  last_modified: datetime
  entries: ConfigEntry[]

ConfigEntry:
  id: string (UUID)
  file_id: string
  key: string
  value: string
  line_number: integer
  line_content: string
  context_before: string[]
  context_after: string[]

Rule:
  id: string (UUID)
  name: string
  rule_id: string
  version: string
  category: string
  severity: "critical" | "warning" | "info" | "style"
  scope: "single_file" | "cross_file" | "cross_server"
  conditions: Condition[]
  remediation: Remediation
  metadata:
    author: string
    source: string
    tags: string[]
    created: datetime
    updated: datetime

Condition:
  type: "pattern" | "value_range" | "value_set" | "exists" | "not_exists" | "cross_reference"
  target: string
  operator: string
  value: any

Remediation:
  suggested_value: string | null
  template: string
  warning: string
  restart_required: boolean

RuleResult:
  id: string (UUID)
  scan_id: string
  rule_id: string
  file_id: string
  status: "pass" | "fail" | "skip" | "error"
  severity: string
  title: string
  description: string
  current_value: string
  suggested_value: string
  diff: Diff
  applied: boolean
  applied_at: datetime | null
  rollback_available: boolean

Diff:
  hunks: DiffHunk[]

DiffHunk:
  file_path: string
  old_start: integer
  old_lines: string[]
  new_start: integer
  new_lines: string[]

Scan:
  id: string (UUID)
  server_id: string
  status: "pending" | "running" | "completed" | "failed"
  source: "ssh" | "api" | "upload" | "git"
  triggered_by: string
  started_at: datetime
  completed_at: datetime
  results: RuleResult[]
  health_score: integer
```

## rule examples

### jvm memory rule (yaml definition)

```yaml
rule_id: jvm-xmx-ratio
version: "1.0.0"
category: JVM Memory
severity: warning
scope: single_file
conditions:
  - type: pattern
    target: "lines"
    operator: "matches"
    value: "-Xmx\\d+[gGmM]"
  - type: value_range
    target: "parsed.xmx_bytes"
    operator: "gt"
    value: "{{ server.ram_bytes * 0.8 }}"
remediation:
  suggested_value: "-Xmx{{ (server.ram_bytes * 0.6) | filesizeformat }}"
  warning: "Reducing heap may require GC tuning adjustment"
  restart_required: true
metadata:
  author: "Infra Pilot Team"
  source: "https://docs.oracle.com/javase/8/docs/technotes/guides/vm/gctuning/"
  tags: ["jvm", "memory", "heap"]
```

### security: hardcoded credential detection

```yaml
rule_id: sec-hardcoded-credential
version: "1.1.0"
category: Security
severity: critical
scope: single_file
conditions:
  - type: pattern
    target: "entries"
    operator: "matches"
    value: "(password|secret|token|apikey|api_key)\\s*[=:]\\s*['\"]?[^'\"\\s]{8,}"
remediation:
  suggested_value: null
  warning: "Replace with environment variable or secret manager reference. Do NOT auto-apply."
  restart_required: false
metadata:
  author: "Infra Pilot Team"
  source: "https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html"
  tags: ["security", "credentials", "secrets"]
```

## service assignments

| Service | Responsibility |
|---------|---------------|
| management panel | primary: config fetch orchestration, rule engine, apply engine, ui, diff viewer, scan history |
| integration service | secondary: webhook notifications on scan complete, export report delivery |
| orchestrator agent | secondary: agent-based config collection for managed servers |
| service core | none directly; authentication/authorization shared |

## effort estimate

| Phase | Task | PT | Owner |
|-------|------|----|-------|
| P1 | Config parser library | 1.0 | Backend |
| P1 | Config fetcher module | 0.5 | Backend |
| P1 | Core data model | 0.5 | Backend |
| P2 | Rule engine | 1.0 | Backend |
| P2 | Best practice DB (50 rules) | 0.5 | Backend/DevOps |
| P3 | Apply engine + backup/rollback | 0.75 | Backend |
| P3 | Diff viewer UI | 0.75 | Frontend |
| P3 | Dashboard integration | 0.5 | Frontend |
| P3 | Scheduled scans | 0.25 | Backend |
| P3 | Export reports | 0.25 | Backend/Frontend |
| total | | 6.0 pt | |

## risks & mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| SSH connection failures for config fetch | medium | fallback to manual upload; retry with backoff |
| false positives from rule engine | high | allow per-rule silencing; user feedback loop to improve rules |
| destructive apply on critical config | high | mandatory backup before apply; preview diff; rollback always available |
| rule database becomes stale | medium | auto-update mechanism; deprecate outdated rules; community contributions |
| cross-file rules are complex | medium | ship v1 with single-file rules only; cross-file in v2 |

## future enhancements

- v2.0: cross-file and cross-server rule analysis
- v2.1: ml-driven custom rule suggestions based on past changes
- v2.2: config drift detection (config vs. runtime state)
- v2.3: team-shared rule sets and compliance baselines
- v2.4: ansible/puppet/chef manifest analysis
- v2.5: auto-remediation workflows with approval gates
