# ai code review bot

| field | value |
|-------|-------|
| id | f-007 |
| name | ai code review bot |
| category | ai & intelligence |
| primary service | discord service |
| effort | medium (4-6 pt) |
| dependencies | feature 13 (webhook event bus), github app registration |
| phase | phase 1 |

## overview

the ai code review bot listens for github pull request webhook events, performs automated static analysis, security scanning, and configuration validation across the changed files, then posts a structured review summary directly to the configured discord channel. it also updates the pr status with check results and inline comments.

### goals

- reduce code review cycle time by 40% through automated first-pass analysis
- catch security issues, config mistakes, and api misuse before human review
- deliver clear, actionable review summaries in discord with severity breakdown
- provide pr status checks that block merges on critical findings

### non-goals

- not a replacement for human code review (ai findings are advisory)
- does not auto-merge or auto-approve prs
- not a ci/cd pipeline -- analysis runs parallel to existing ci
- does not store full source code permanently (processes in memory, retains only metadata)

## architecture

```
┌─────────────────┐     ┌─────────────────────────────────────────────────┐
│   GitHub         │     │                  Discord Service                │
│   (Webhook)      │     │                                                 │
│                  │     │  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  PR opened       │────▶│  │ Webhook  │  │ Analyzer │  │ Discord Bot  │  │
│  PR synchronized │     │  │ Receiver │──▶│ Pipeline │──▶│ Publisher    │  │
│  PR reopened     │     │  └──────────┘  └────┬─────┘  └──────┬───────┘  │
│  PR review       │     │                      │               │          │
└─────────────────┘     │                      ▼               │          │
                        │  ┌─────────────────────────────────┐  │          │
                        │  │        Analyzer Pipeline         │  │          │
                        │  │  ┌──────────┐  ┌──────────────┐ │  │          │
                        │  │  │ Security │  │ Config Check │ │  │          │
                        │  │  │ Scanner  │  │              │ │  │          │
                        │  │  ├──────────┤  ├──────────────┤ │  │          │
                        │  │  │ - secrets │  │ - YAML valid │ │  │          │
                        │  │  │ - vulns   │  │ - Dockerfile │ │  │          │
                        │  │  │ - deps    │  │ - CI config  │ │  │          │
                        │  │  │ - SAST    │  │ - API misuse │ │  │          │
                        │  │  └──────────┘  └──────────────┘ │  │          │
                        │  │  ┌──────────┐  ┌──────────────┐ │  │          │
                        │  │  │ Lint     │  │ AI Review    │ │  │          │
                        │  │  │ Checker  │  │ Engine       │ │  │          │
                        │  │  ├──────────┤  ├──────────────┤ │  │          │
                        │  │  │ - ESLint │  │ - diff       │ │  │          │
                        │  │  │ - Ruff   │  │   analysis   │ │  │          │
                        │  │  │ - style  │  │ - pattern    │ │  │          │
                        │  │  │   checks │  │   detection  │ │  │          │
                        │  │  └──────────┘  └──────────────┘ │  │          │
                        │  └─────────────────────────────────┘  │          │
                        │                                       │          │
                        │  ┌─────────────────────────────────┐  │          │
                        │  │         PR Status Manager       │  │          │
                        │  │  ┌──────────┐  ┌──────────────┐ │  │          │
                        │  │  │ Check    │  │ Inline       │ │  │          │
                        │  │  │ Runner   │  │ Commenter    │ │  │          │
                        │  │  └──────────┘  └──────────────┘ │  │          │
                        │  └─────────────────────────────────┘  │          │
                        └──────────────────────────────────────┘          │
                                     │                                    │
                                     ▼                                    │
                        ┌─────────────────────┐                          │
                        │     Discord          │                          │
                        │  #code-reviews       │◀─────────────────────────┘
                        │  ┌────────────────┐  │
                        │  │ PR Review      │  │
                        │  │ #42: Fix       │  │
                        │  │ database pool  │  │
                        │  │ 3 warnings     │  │
                        │  │ 2 critical     │  │
                        │  └────────────────┘  │
                        └─────────────────────┘
```

### event flow

```
GitHub PR Event ──► Webhook Receiver
                       │
                       ├──► Validate signature (HMAC-SHA256)
                       ├──► Filter: only opened/synchronized/reopened
                       ├──► Fetch PR diff (GitHub API)
                       │
                       ▼
                Analyzer Pipeline (parallel)
                       │
                       ├──► Security Scanner
                       │     ├── Secret detection (gitleaks-style patterns)
                       │     ├── Dependency vulns (OSV API)
                       │     ├── SAST (semgrep rules)
                       │     └── Dockerfile scan (hadolint)
                       │
                       ├──► Config Checker
                       │     ├── YAML/JSON validation
                       │     ├── CI config linting
                       │     └── API usage pattern check
                       │
                       ├──► Lint Checker
                       │     ├── Language-specific linters
                       │     └── Style consistency
                       │
                       └──► AI Review Engine
                             ├── Diff understand (LLM)
                             ├── Logic error detection
                             └── Best practice suggestions
                       │
                       ▼
                Results Aggregator
                       │
                       ├──► Post Discord embed summary
                       ├──► Set GitHub commit status (pass/fail/pending)
                       └──► Add inline review comments (optional)
```

## implementation plan

### phase 1: webhook & core infrastructure (week 1, 1.5 pt)

1. **github webhook receiver**
   - hmac-sha256 signature verification
   - event filtering (pull_request, pull_request_review)
   - rate limiting (github api best practices)
   - queue-based processing (async to avoid webhook timeout)
   - retry with exponential backoff

2. **github api client**
   - fetch pr diff and metadata
   - post commit status checks
   - create review comments (inline + summary)
   - authenticate via github app installation token

3. **discord bot publisher**
   - rich embed message builder
   - severity-colored embeds (green/yellow/red)
   - action buttons (view pr, approve, request changes placeholder)
   - thread creation for detailed discussion per review

### phase 2: analysis pipeline (week 2-3, 2.5 pt)

1. **security scanner**
   - secret/credential detection (regex + entropy analysis)
   - dependency vulnerability lookup (osv.dev api, github advisory db)
   - semgrep-based sast with community rules
   - dockerfile/hadolint integration
   - secrets detection for common patterns (aws keys, tokens, connection strings)

2. **config checker**
   - yaml/json syntax and schema validation
   - ci/cd config linting (github actions, docker compose)
   - api misuse detection (known anti-patterns)
   - infrastructure-as-code checks (terraform, helm, k8s manifests)

3. **lint checker**
   - language detection from file extensions
   - invoke language-specific linters (eslint, ruff, clippy, etc.)
   - aggregate and deduplicate results

4. **ai review engine**
   - llm-based diff analysis
   - context-aware code review (understand surrounding code)
   - bug pattern detection (null pointer, race condition, resource leak)
   - performance optimization suggestions
   - rate-limited to avoid excessive api costs

### phase 3: comments & status integration (week 3-4, 1.5 pt)

1. **pr status manager**
   - map severity levels to github check states:
     - critical -> failure (blocks merge)
     - warning -> neutral (advisory)
     - info -> success (informational)
   - update status on each analysis pass
   - handle re-analysis on new commits

2. **inline comment engine**
   - deduplicate comments across analysis runs
   - file+line anchored comments
   - suggestion blocks with code fence
   - batch create via github reviews api

3. **discord ux polish**
   - customizable channel subscriptions per repo
   - filter by minimum severity
   - per-repository configuration command
   - archive digests for large prs (summary-only mode)

## api design

### internal endpoints (discord service)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/webhooks/github` | GitHub webhook receiver |
| `GET`  | `/reviews/{reviewId}` | Get review details |
| `GET`  | `/reviews/{reviewId}/findings` | Get individual findings |
| `POST` | `/reviews/{reviewId}/reanalyze` | Trigger re-analysis |
| `GET`  | `/config/{guildId}/{repoId}` | Get review config for repo |
| `PATCH` | `/config/{guildId}/{repoId}` | Update review config |

### webhook payload (github -> infra pilot)

```json
{
  "event": "pull_request",
  "action": "opened",
  "signature": "sha256=abc123def456...",
  "payload": {
    "repository": {
      "full_name": "myorg/minecraft-server",
      "clone_url": "https://github.com/myorg/minecraft-server.git",
      "default_branch": "main"
    },
    "pull_request": {
      "number": 42,
      "title": "Fix database connection pool configuration",
      "head": {
        "sha": "abc123def456",
        "ref": "fix/db-pool",
        "repo": { "full_name": "myorg/minecraft-server" }
      },
      "base": {
        "sha": "789012abc345",
        "ref": "main",
        "repo": { "full_name": "myorg/minecraft-server" }
      },
      "user": { "login": "developer1" },
      "created_at": "2026-05-27T10:00:00Z",
      "changed_files": 12,
      "additions": 340,
      "deletions": 50
    }
  }
}
```

### discord embed output

```json
{
  "embeds": [{
    "title": "code review: pr #42 - fix database connection pool configuration",
    "url": "https://github.com/myorg/minecraft-server/pull/42",
    "color": 16776960,
    "fields": [
      {
        "name": "Repository",
        "value": "myorg/minecraft-server",
        "inline": true
      },
      {
        "name": "Author",
        "value": "developer1",
        "inline": true
      },
      {
        "name": "Branch",
        "value": "fix/db-pool -> main",
        "inline": true
      },
      {
        "name": "Changes",
        "value": "+340 / -50 in 12 files",
        "inline": true
      },
      {
        "name": "critical (2)",
        "value": "- hardcoded database password in `config.yml:24`\n- sql injection vulnerable query in `queries.java:88`",
        "inline": false
      },
      {
        "name": "warnings (3)",
        "value": "- connection pool timeout set to 30s (recommended <= 5s) in `config.yml:12`\n- unused import `java.util.date` in `server.java:3`\n- missing `@override` annotation in `service.java:45`",
        "inline": false
      },
      {
        "name": "info (4)",
        "value": "- consider using try-with-resources in `database.java:67`\n- method `getplayer()` could be static",
        "inline": false
      }
    ],
    "footer": {
      "text": "infra pilot ai code review - analysis took 12.4s"
    },
    "timestamp": "2026-05-27T10:05:00Z"
  }]
}
```

## data model

```yaml
ReviewRequest:
  id: string (UUID)
  event: "pull_request" | "pull_request_review"
  action: string
  repository: Repository
  pull_request: PullRequest
  sender: User
  received_at: datetime
  status: "queued" | "processing" | "completed" | "failed"

Repository:
  full_name: string
  owner: string
  name: string
  clone_url: string
  default_branch: string
  installation_id: integer

PullRequest:
  number: integer
  title: string
  description: string
  head_sha: string
  head_ref: string
  base_sha: string
  base_ref: string
  author: string
  created_at: datetime
  changed_files: integer
  additions: integer
  deletions: integer

ReviewResult:
  id: string (UUID)
  review_request_id: string
  status: "in_progress" | "completed" | "failed"
  started_at: datetime
  completed_at: datetime
  duration_ms: integer
  findings: Finding[]
  summary:
    critical: integer
    warning: integer
    info: integer
    total: integer
  pr_status: "success" | "neutral" | "failure"

Finding:
  id: string (UUID)
  rule_id: string
  category: "security" | "config" | "lint" | "logic" | "performance" | "style"
  severity: "critical" | "warning" | "info"
  title: string
  description: string
  file: string
  line: integer
  column: integer
  snippet: string
  suggested_fix: string
  cve_id: string | null
  cwe_id: string | null
  source: "semgrep" | "gitleaks" | "osv" | "hadolint" | "eslint" | "llm" | "builtin"

ReviewConfig:
  id: string (UUID)
  guild_id: string
  channel_id: string
  repo_pattern: string
  min_severity: string
  inline_comments: boolean
  auto_approve: boolean
  blocked_severities: string[]
  enabled_checks: string[]
```

## service assignments

| Service | Responsibility |
|---------|---------------|
| discord service | primary: webhook receiver, analyzer pipeline, discord publisher, pr status manager |
| integration service | secondary: github api rate limiting coordination, webhook event bus routing |
| service core | none directly; authentication, user/repo permission checks |

## effort estimate

| Phase | Task | PT | Owner |
|-------|------|----|-------|
| P1 | GitHub webhook receiver + signature verification | 0.5 | Backend |
| P1 | GitHub API client (diff fetch, status, comments) | 0.5 | Backend |
| P1 | Discord embed publisher | 0.5 | Backend |
| P2 | Security scanner (secrets + vulns + SAST) | 1.0 | Backend/SecEng |
| P2 | Config checker + lint integrations | 0.5 | Backend |
| P2 | AI Review Engine (LLM integration) | 1.0 | ML/Backend |
| P3 | PR status manager + inline comments | 0.5 | Backend |
| P3 | Discord UX + per-repo config | 0.5 | Backend |
| P3 | Testing + edge case handling | 0.25 | QA |
| total | | 5.25 pt | |

## configuration

### discord bot commands

```
/review register repo:myorg/minecraft-server channel:#code-reviews
/review config repo:myorg/minecraft-server min-severity:warning
/review config repo:myorg/minecraft-server inline-comments:true
/review status repo:myorg/minecraft-server
/review ignore repo:myorg/minecraft-server file:"vendor/*"
```

### yaml configuration example

```yaml
# discord-service/config/code-review.yml
repositories:
  - pattern: "myorg/*"
    channel: "code-reviews"
    min_severity: "warning"
    inline_comments: true
    auto_approve: false
    blocked_severities:
      - "critical"
    enabled_checks:
      - security
      - config
      - lint
      - ai_review
    ignore_patterns:
      - "vendor/*"
      - "node_modules/*"
      - "*.generated.*"
      - "dist/*"
    custom_rules:
      - id: "no-hardcoded-aws-keys"
        pattern: "AKIA[0-9A-Z]{16}"
        severity: "critical"
        message: "AWS access key detected"
```

## risks & mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| GitHub API rate limiting | medium | use github app with higher limits; queue-based processing |
| llm api latency/cost | medium | parallel analysis; cache results for identical diffs; set max tokens per review |
| false positives cause noise | high | configurable severity thresholds; per-repo rule tuning; user feedback buttons |
| webhook timeout (10s github limit) | high | acknowledge immediately; process async with status polling |
| secret leak in transit/processing | critical | process in-memory only; no persistent storage of diffs; audit logging |

## future enhancements

- v2.0: auto-fix suggestions with github suggestions api
- v2.1: learning mode -- adapt to project-specific patterns
- v2.2: multi-repo dashboard in management panel
- v2.3: gitlab/bitbucket/gitea support
- v2.4: team performance analytics (review velocity, common issues)
- v2.5: custom rule authoring ui
