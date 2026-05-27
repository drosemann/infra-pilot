# infra pilot cli

- feature id: 11
- category: developer ecosystem & api
- primary service: new `cli/` directory
- effort estimate: large (7-10 pt)
- dependencies: stable rest api (v1), authentication service
- phase: phase 2 (weeks 5-8)

## overview

the **infra pilot cli** (`ipilot`) is a command-line tool that provides authenticated access to the infra pilot api. it enables developers and operators to manage servers, deployments, databases, dns records, and other infrastructure resources directly from the terminal. the cli supports scripting, automation pipelines, and ci/cd integration.

### goals

- provide a fast, ergonomic cli for all infra panel rest api operations
- support multiple output formats (json, table, yaml) for both human and machine consumption
- enable scripting and automation with non-interactive mode and exit codes
- offer shell tab completion for bash, zsh, fish, and powershell
- securely manage api tokens and multi-account profiles

### non-goals

- replace the management panel ui for complex workflows
- provide real-time terminal emulation (handled by collaborative terminal, feature 27)
- serve as an api gateway or rate-limiting layer

## architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User Terminal                           │
│  ipilot server list --format json --region us-east          │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│  cli/                                                       │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Main Entry Point (cmd/root.go)                       │ │
│  │  - Cobra root command setup                           │ │
│  │  - Global flags (--format, --output, --profile)       │ │
│  │  - Config file loading (~/.ipilot/config.yaml)        │ │
│  └────────────────────────┬───────────────────────────────┘ │
│                           │                                  │
│  ┌────────────────────────▼───────────────────────────────┐ │
│  │  Command Groups                                        │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │ │
│  │  │ server   │ │ deploy   │ │ logs     │ │ db       │  │ │
│  │  │ dns      │ │ backup   │ │ config   │ │ profile  │  │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │ │
│  └────────────────────────┬───────────────────────────────┘ │
│                           │                                  │
│  ┌────────────────────────▼───────────────────────────────┐ │
│  │  API Client Layer (client/)                            │ │
│  │  - HTTP client with retry & timeout                    │ │
│  │  - Auth token injection                                │ │
│  │  - Request/response interceptors                       │ │
│  │  - Pagination helpers                                  │ │
│  └────────────────────────┬───────────────────────────────┘ │
│                           │                                  │
│  ┌────────────────────────▼───────────────────────────────┐ │
│  │  Output Formatters (output/)                           │ │
│  │  - JSON formatter     - Table formatter                │ │
│  │  - YAML formatter     - Raw (ID-only) formatter        │ │
│  └────────────────────────┬───────────────────────────────┘ │
│                           │                                  │
│  ┌────────────────────────▼───────────────────────────────┐ │
│  │  Auth Module (auth/)                                   │ │
│  │  - Token storage (keyring / encrypted file)            │ │
│  │  - Login / logout flow                                 │ │
│  │  - Token refresh                                       │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
              ┌───────────────────────┐
              │  Infra Pilot REST API │
              │  (Integration Service) │
              └───────────────────────┘
```

### directory structure

```
cli/
├── main.go                    # Entry point
├── cmd/
│   ├── root.go                # Root command & global flags
│   ├── server.go              # ipilot server * subcommands
│   ├── deploy.go              # ipilot deploy
│   ├── logs.go                # ipilot logs (including --follow)
│   ├── db.go                  # ipilot db * subcommands
│   ├── dns.go                 # ipilot dns * subcommands
│   ├── backup.go              # ipilot backup * subcommands
│   ├── config.go              # ipilot config * (manage profile)
│   └── completion.go          # ipilot completion [bash|zsh|fish|powershell]
├── client/
│   ├── client.go              # HTTP client wrapper
│   ├── requests.go            # Request builders
│   ├── responses.go           # Response parsing
│   ├── middleware.go           # Auth injection, logging, retry
│   └── pagination.go          # Cursor/offset pagination
├── output/
│   ├── formatter.go           # Formatter interface
│   ├── json.go                # JSON formatter
│   ├── table.go               # Table formatter
│   ├── yaml.go                # YAML formatter
│   └── raw.go                 # Raw (ID list) formatter
├── auth/
│   ├── auth.go                # Auth flow
│   ├── token.go               # Token storage
│   └── login.go               # Device/login flow
├── config/
│   ├── config.go              # Config file read/write
│   └── defaults.go            # Default values
└── go.mod / go.sum
```

## implementation plan

### phase a: scaffolding & auth (2-3 pt)

1. initialize go module and cobra cli structure
2. implement `cmd/root.go` with global flags (`--format`, `--profile`, `--quiet`, `--verbose`)
3. build `auth/` module with device-code oauth flow
4. implement token storage via os keyring (fallback to encrypted file)
5. add `ipilot login` and `ipilot logout` commands
6. write config file management (`~/.ipilot/config.yaml`)

### phase b: api client layer (2 pt)

1. build `client/client.go` with configurable base url, timeouts, retry
2. implement request signing and auth header injection
3. add response middleware for error handling and rate-limit awareness
4. implement pagination helpers (cursor-based and offset-based)
5. add request/response logging in verbose mode

### phase c: core commands (2-3 pt)

1. implement `ipilot server [list|show|create|delete|start|stop|restart]`
2. implement `ipilot deploy [create|status|rollback]`
3. implement `ipilot logs [service] --follow` with websocket streaming
4. implement `ipilot db [list|create|backup|restore]`
5. implement `ipilot dns [list|create|delete|update]`
6. implement `ipilot backup [list|create|restore]`

### phase d: output formatting & completion (1-2 pt)

1. build `output/` formatters with auto-detection based on `--format`
2. implement table formatter with column auto-width
3. add `--quiet` mode (single id output for scripting)
4. implement `ipilot completion [shell]` with all subcommands and flags
5. add `IPILOT_FORMAT` and `IPILOT_PROFILE` environment variable support

## api design

the cli wraps the existing infra panel rest api. key endpoints consumed:

### server operations

| Method | Endpoint | CLI Command |
|--------|----------|-------------|
| `GET` | `/api/v1/servers` | `ipilot server list` |
| `GET` | `/api/v1/servers/:id` | `ipilot server show <id>` |
| `POST` | `/api/v1/servers` | `ipilot server create [flags]` |
| `DELETE` | `/api/v1/servers/:id` | `ipilot server delete <id>` |
| `POST` | `/api/v1/servers/:id/start` | `ipilot server start <id>` |
| `POST` | `/api/v1/servers/:id/stop` | `ipilot server stop <id>` |
| `POST` | `/api/v1/servers/:id/restart` | `ipilot server restart <id>` |

### deploy operations

| Method | Endpoint | CLI Command |
|--------|----------|-------------|
| `POST` | `/api/v1/deployments` | `ipilot deploy create [flags]` |
| `GET` | `/api/v1/deployments/:id` | `ipilot deploy status <id>` |
| `POST` | `/api/v1/deployments/:id/rollback` | `ipilot deploy rollback <id>` |

### logs

| Method | Endpoint | CLI Command |
|--------|----------|-------------|
| `GET` | `/api/v1/servers/:id/logs` | `ipilot logs <id>` |
| `WS` | `/api/v1/servers/:id/logs/stream` | `ipilot logs <id> --follow` |

## data model

### cli config file (`~/.ipilot/config.yaml`)

```yaml
current_profile: production
profiles:
  production:
    api_url: https://api.infrapanel.io
    default_format: table
    timeout_seconds: 30
  staging:
    api_url: https://staging.api.infrapanel.io
    default_format: json
    timeout_seconds: 60
```

### token storage

tokens are stored in the os keyring when available, falling back to an encrypted file at `~/.ipilot/tokens.json`:

```json
{
  "profiles": {
    "production": {
      "access_token": "ip_eyJhbGciOi...",
      "refresh_token": "ip_rf_abc123...",
      "expires_at": "2026-06-15T12:00:00Z",
      "token_type": "bearer"
    }
  }
}
```

## service assignments

| Component | Owner | Notes |
|-----------|-------|-------|
| CLI scaffolding & Cobra setup | Platform Team | Core CLI structure |
| Auth module | Security Team | OAuth flow, token storage |
| API client | Platform Team | HTTP client, retry, error handling |
| Server commands | Core Services Team | `ipilot server *` |
| Deploy commands | Orchestrator Team | `ipilot deploy *` |
| Logs streaming | Core Services Team | WebSocket `--follow` |
| Output formatters | Platform Team | JSON, table, YAML, raw |
| Tab completion | Platform Team | All shell variants |
| Documentation | Developer Experience | User guide, examples |
| E2E tests | QA | Integration test suite |

## effort estimate breakdown

| Task | PT | Dependencies |
|------|----|-------------|
| CLI scaffolding & config | 1.5 | None |
| Auth module (login/logout/token) | 1.5 | Auth Service API |
| API client with retry | 1.5 | REST API spec |
| Server commands (CRUD + actions) | 1.0 | Server API |
| Deploy commands | 1.0 | Deploy API |
| Logs with --follow | 1.0 | Logs API, WebSocket |
| Output formatters | 1.0 | None |
| Tab completion | 0.5 | All commands defined |
| Documentation | 0.5 | All features implemented |
| E2E tests | 1.0 | CLI stable |
| total | 10.0 | |

## usage examples

### basic usage

```bash
# List servers with table output
ipilot server list

# List servers with JSON output
ipilot server list --format json

# Create a server
ipilot server create --name web-01 --region us-east --plan standard-2

# View server details
ipilot server show srv_abc123 --format yaml

# Tail logs
ipilot logs srv_abc123 --follow

# Deploy an application
ipilot deploy create --service web --image nginx:1.25 --replicas 3

# Switch profile
ipilot config set-profile staging
```

### scripting

```bash
#!/bin/bash
# Automate server creation with JSON output parsing
SERVER_ID=$(ipilot server create \
  --name "ci-runner-${BUILD_NUMBER}" \
  --region us-east \
  --plan standard-4 \
  --format json \
  --quiet)

echo "Created server: $SERVER_ID"
```

### tab completion

```bash
# Install completion for current shell
eval "$(ipilot completion zsh)"

# Or generate and source the script
ipilot completion bash > ~/.ipilot/completion.bash
source ~/.ipilot/completion.bash
```

## risks & mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| API version drift | CLI breaks on API update | Use API version negotiation (`Accept: application/vnd.infrapanel.v1+json`) |
| Token exposure on shared machines | Credential leak | OS keyring integration, token encryption at rest |
| Large output sets | Memory pressure | Streaming pagination, `--limit` flag, cursor-based iteration |
| WebSocket reconnection | Log stream interruption | Automatic reconnect with backoff, buffer management |

## acceptance criteria

- [ ] `ipilot login` completes device-code oauth flow and stores token
- [ ] all server crud commands function correctly with json and table output
- [ ] `ipilot logs --follow` streams logs with < 2s latency and reconnects on disconnect
- [ ] `ipilot deploy create` accepts all required flags and returns deployment id
- [ ] `--format json`, `--format yaml`, `--format table` produce correct output for every command
- [ ] tab completion generates valid scripts for bash, zsh, fish, and powershell
- [ ] exit codes: 0 for success, 1 for user error, 2 for api/server error
- [ ] tests pass: unit (80%+ coverage), integration (all commands), e2e (happy path)
