# CLI Reference

## Usage

```bash
ipilot [global-flags] <command> [subcommand] [flags]
```

Global flags: `--output`/`-o` (json, table, yaml, plain), `--profile`/`-p`, `--no-color`

## Core Commands

| Command | Description |
| --------- | ------------- |
| `login <api_key>` | Authenticate |
| `logout` | Clear auth token |
| `version` | Show version |
| `interactive` | REPL mode |
| `completion [shell] [--install]` | Shell completion |
| `doctor doctor [--fix] [--verbose]` | System health |

## Server Management

| Command | Description |
| --------- | ------------- |
| `server list` | List servers |
| `server create <name> --image <image> [--memory MB]` | Create server (`--type` is a deprecated alias for `--image`) |
| `server delete <id>` | Delete server |
| `server status <id>` | Server status |
| `server start <id>` | Start container |
| `server stop <id>` | Stop container |
| `server restart <id>` | Restart container |

## Backup & Snapshots

| Command | Description |
| --------- | ------------- |
| `backup list [server]` | List backups |
| `backup create <server> [--s3 bucket:path]` | Create backup |
| `backup schedule <server> [--interval] [--retention] [--s3]` | Schedule backups |
| `backup snapshots <server> [--create] [--restore]` | Snapshot management |
| `backup restore <id> [--target]` | Restore backup |
| `backup config [--s3-bucket] [--s3-key] [--s3-secret] [--s3-endpoint]` | S3 config |

## Deployment

| Command | Description |
| --------- | ------------- |
| `deploy deploy <server> <branch> [--repo-url] [--template]` | Deploy branch |
| `deploy list [--server]` | List deployments |
| `deploy status <id>` | Deployment status |
| `deploy rollback <id>` | Rollback deployment |

## Logs

| Command | Description |
| --------- | ------------- |
| `logs fetch <server> [--lines] [--follow]` | Fetch server logs |

## GitOps (Infrastructure as Code)

| Command | Description |
| --------- | ------------- |
| `gitops export [-o file.yaml] [-s server]` | Export current infra as YAML |
| `gitops plan [-f file.yaml]` | Show diff between current state and YAML |
| `gitops apply [-f file.yaml] [--dry-run] [-y]` | Apply YAML config to infra |
| `gitops drift [--scan]` | Detect configuration drift |
| `gitops import-config <file>` | Import from YAML file |

## SSH Session Management

| Command | Description |
| --------- | ------------- |
| `ssh list [--status active\|closed]` | List SSH sessions |
| `ssh connect <server> [-u user] [-j jump] [-p port]` | Connect via SSH |
| `ssh jump_hosts [--create --host --user]` | Manage jump hosts |
| `ssh keys [--add --name] [--delete]` | Manage SSH keys |
| `ssh record <session-id>` | View session recording |
| `ssh saved [--add host@host:port] [--delete]` | Manage saved hosts |

## Server Inventory

| Command | Description |
| --------- | ------------- |
| `inventory list [--tag] [--environment] [--region] [--owner] [--provider]` | List with filters |
| `inventory show <server>` | Show server metadata |
| `inventory update <server> [--owner] [--environment] [--region] [--provider] [--os] [--cost] [--tags]` | Update metadata |
| `inventory tags [--list] [--server] [--add server:tag] [--remove server:tag]` | Tag management |

## Secret Management

| Command | Description |
| --------- | ------------- |
| `secrets list [--path]` | List secrets |
| `secrets get <key> [--version]` | Get secret value |
| `secrets set <key> <value> [--rotate] [--rotation-days]` | Store a secret |
| `secrets delete <key>` | Delete a secret |
| `secrets versions <key>` | List version history |
| `secrets rotate [--key] [--all]` | Rotate secrets |
| `secrets roles <key> [--grant role] [--revoke role]` | RBAC for secrets |

## Deployment Templates

| Command | Description |
| --------- | ------------- |
| `templates list [--type node\|python\|docker-compose\|nginx\|postgres\|redis\|traefik]` | List templates |
| `templates show <template>` | Show template details |
| `templates deploy <template> <name> [--server] [--vars] [--dry-run]` | Deploy from template |
| `templates init <template> <name> [--output]` | Initialize local project |

## Plugin System

| Command | Description |
| --------- | ------------- |
| `plugins list [--installed]` | List available plugins |
| `plugins install <name> [--source] [--version]` | Install a plugin |
| `plugins uninstall <name>` | Uninstall a plugin |
| `plugins update [--name] [--all]` | Update plugins |
| `plugins info <name>` | Plugin details |

Built-in: kubernetes, docker, aws, hetzner, cloudflare, proxmox, ansible, nomad, azure

## Webhooks

| Command | Description |
| --------- | ------------- |
| `webhooks list` | List webhooks |
| `webhooks create <name> <url> [--events] [--secret]` | Create webhook |
| `webhooks delete <id>` | Delete webhook |
| `webhooks test [--id] [--event]` | Test delivery |
| `webhooks logs [--id]` | Delivery logs |

## API Keys

Scoped keys (panel key model v2). New keys are prefixed `ip_live_`
(production) or `ip_test_` (clearly-marked test keys); legacy `ip_<hex>`
keys still work but carry full wildcard access and are flagged
`needs_rotation: true`.

| Command | Description |
| --------- | ------------- |
| `apikeys list` | List API keys (scopes, class, rotation state) |
| `apikeys create <name> [--scopes s] [--type live\|test] [--app app-id] [--expire days] [--role r]` | Create a scoped key |
| `apikeys rotate <key-id> [--overlap hours]` | Rotate a key with an overlap window |
| `apikeys revoke <id>` | Revoke API key |

Create options:

- `--scopes`/`-s` — comma-separated scopes, e.g.
  `--scopes apps:read,metrics:*`. Scope syntax is `<family>:<action>`
  (`apps:read`), `<family>:*` (`metrics:*`), or the wildcard `*`.
  Omitting it creates a wildcard key; the CLI notes when it does.
- `--type`/`-t` — key class, `live` (production prefix) or `test`.
- `--app`/`-a` — bind the key to one app; a bound key only works on that
  app's routes (`403 app_binding` otherwise).
- `--expire`/`-e` — expiration in days (max 730).

Rotation (`apikeys rotate <key-id> --overlap hours`): a replacement is issued
immediately and the old key keeps working until the overlap deadline
(default 24 h, max 168). The replacement key is printed once — save it.
Note: with TOTP enabled, the panel requires a fresh two-factor code
(`X-2FA-Token`) for key create/rotate/revoke; the CLI shows the panel's
challenge message if one is needed for the caller's account.

`login <api_key>` records the key's scopes in the profile — server-provided
scopes win so the profile matches the key; `--scopes apps:read,metrics:*`
records a hint only. Logging in with a legacy `ip_<hex>` full-access key
prints a rotation warning pointing at `apikeys list` / `apikeys rotate`.

Scope denials: the panel answers `403` with
`{ code: 'scope_denied', required: '<scope>' }`; the CLI surfaces it as
"This API key lacks permission for \<path\>: missing scope '\<required\>'"
plus advice (create a key with the needed scope via
`ipilot apikeys create ... --scopes` or use a wildcard key).

```bash
ipilot apikeys create ci-deployer --scopes apps:read,apps:write,metrics:* --type live --app app-1
ipilot apikeys rotate <key-id> --overlap 48
ipilot login ip_live_... --scopes apps:read,metrics:*
```

## Undo / Rollback

| Command | Description |
| --------- | ------------- |
| `rollback list [--resource] [--limit]` | Recent changes |
| `rollback undo <change-id> [--dry-run]` | Undo a change |
| `rollback rollback <resource-type> <resource-id> [--version]` | Rollback resource |
| `rollback history [--resource] [--id]` | Change history |

## Metrics

Real-time, historical, and aggregated resource metrics. Relative windows
(`1h`, `6h`, `24h`, `7d`) pass through to the panel; ISO-8601 ranges are
mapped to the smallest supported period that covers them. Intervals are
`1m`, `5m`, or `1h`.

| Command | Description |
| --------- | ------------- |
| `metrics realtime [--app id]` | Real-time CPU/memory/disk/network snapshot |
| `metrics history [--app id] [--since 1h\|6h\|24h\|7d\|ISO] [--until ISO] [--interval 1m\|5m\|1h]` | Historical metric time series |
| `metrics aggregated` | Fleet-wide totals across all apps |
| `metrics grafana-url` | Configured Grafana embed URL, if any |

```bash
ipilot metrics realtime --app app-1
ipilot metrics history --since 24h --interval 1h
ipilot metrics history --since 2026-01-01T00:00:00Z --until 2026-01-01T06:00:00Z
ipilot --output json metrics aggregated
```

## Alerts

Alert rules (configs) watch a metric with a comparison operator and
threshold; alert history holds triggered incidents. Operators are `gt`,
`lt`, `gte`, `lte`, `eq`. Incident commands take the alert-history entry ID.

| Command | Description |
| --------- | ------------- |
| `alerts list [--rules] [--limit n]` | List incidents (default) or rules with `--rules` |
| `alerts show <id>` | Show one incident from history |
| `alerts acknowledge <id>` | Acknowledge a triggered alert |
| `alerts resolve <id>` | Resolve a triggered alert |
| `alerts create-rule --metric m --operator op --threshold n [--disabled] [--notify-email]` | Create an alert rule |
| `alerts update-rule <id> [--metric] [--operator] [--threshold] [--enable\|--disable] [--notify-email]` | Update an alert rule |
| `alerts delete-rule <id>` | Delete an alert rule |

```bash
ipilot alerts list
ipilot alerts list --rules
ipilot alerts create-rule --metric cpu --operator gt --threshold 90
ipilot alerts update-rule c1 --threshold 85 --enable
ipilot alerts acknowledge 42
```

## Audit Log

Filtered audit browsing and export. Filters map to the panel's
`user_id`/`action`/`entity_type`/`start_date`/`end_date` query params.
`--limit` is the page size (max 200) for `list`; for `export` it caps the
total number of entries fetched across pages.

| Command | Description |
| --------- | ------------- |
| `audit list [--actor id] [--action a] [--resource r] [--since ISO] [--until ISO] [--limit n] [--page n]` | List audit entries (paginated) |
| `audit export [--format csv\|jsonl] [--file path] [same filters as list] [--limit n]` | Export entries as CSV or JSON Lines |
| `audit watch [--interval n] [--limit n] [--duration n] [same filters as list]` | Follow the log, printing new entries as they arrive |

```bash
ipilot audit list --limit 20
ipilot audit list --action alert:create --resource alert_config
ipilot audit list --since 2026-01-01 --until 2026-02-01 --page 2
ipilot audit export --format csv --file audit.csv
ipilot audit export --format jsonl > audit.jsonl
ipilot audit watch --interval 5 --action database:create
```

## Runbooks

Operational runbooks merge built-in procedures (deploy-production,
rollback-deployment, backup-verify, system-update) with user-defined ones.
Definitions are YAML or JSON mappings with a non-empty `name` and a
`steps` list. `--wait` polls the execution until a terminal status or
`--timeout` seconds elapse; `--dry-run` previews steps without executing.

| Command | Description |
| --------- | ------------- |
| `runbooks list` | List built-in and user-defined runbooks |
| `runbooks show <id\|name>` | Show a runbook's definition and steps |
| `runbooks create --file def.yaml` | Create a runbook from a YAML/JSON file |
| `runbooks edit <id> [--file def.yaml] [--name n] [--description d]` | Edit an existing runbook |
| `runbooks delete <id>` | Delete a runbook |
| `runbooks execute <id> [--wait] [--timeout n] [--dry-run]` | Execute a runbook |
| `runbooks history [--runbook id]` | List execution history |
| `runbooks execution <execution-id>` | Status of a single execution |
| `runbooks steps <id\|name>` | List a runbook's steps |
| `runbooks validate --file def.yaml` | Validate a definition file locally (no API call) |
| `runbooks export <id\|name> [--format yaml\|json] [--file path]` | Export a runbook definition for reuse |

```bash
ipilot runbooks list
ipilot runbooks show builtin-deploy-prod
ipilot runbooks create --file runbook.yaml
ipilot runbooks execute r1 --wait --timeout 120
ipilot runbooks execute r1 --dry-run
ipilot runbooks validate --file runbook.yaml
ipilot runbooks export builtin-deploy-prod --format yaml --file deploy.yaml
```

## Maintenance Windows

Scheduled maintenance windows. `--starts`/`--ends` are ISO-8601
timestamps; `--app` scopes a window to one app. Statuses are `scheduled`,
`active`, `completed`, `cancelled`. `enable`/`disable` are shorthands for
setting the status to `scheduled`/`cancelled`.

| Command | Description |
| --------- | ------------- |
| `maintenance list` | List maintenance windows |
| `maintenance create --title t --starts ISO --ends ISO [--description d] [--app id]` | Create a window |
| `maintenance update <id> [--title] [--description] [--starts] [--ends] [--app] [--status]` | Update a window |
| `maintenance delete <id>` | Delete a window |
| `maintenance enable <id>` | Re-enable (status -> scheduled) |
| `maintenance disable <id>` | Disable (status -> cancelled) |

```bash
ipilot maintenance create --title "db upgrade" \
  --starts 2026-02-01T00:00:00Z --ends 2026-02-01T02:00:00Z
ipilot maintenance update m1 --status active
ipilot maintenance disable m1
```

## Notifications

Notification channels are delivery targets (`email`, `webhook`,
`telegram`); alert rules decide when they fire (see Alerts). `--config`
is a JSON object with channel-specific settings, replaced wholesale on
update.

| Command | Description |
| --------- | ------------- |
| `notifications list` | List channels |
| `notifications create <name> --type email\|webhook\|telegram --config json` | Create a channel |
| `notifications update <id> [--name] [--config json] [--enable\|--disable]` | Update a channel |
| `notifications delete <id>` | Delete a channel |
| `notifications test <id>` | Send a test notification |

```bash
ipilot notifications create ops-mail --type email \
  --config '{"to": "ops@example.com"}'
ipilot notifications create ops-hook --type webhook \
  --config '{"url": "https://example.com/h"}'
ipilot notifications update n1 --disable
ipilot notifications test n1
```

## Organizations

Multi-tenant organizations and memberships. Roles are `member` (default),
`admin`, `owner`. `create` makes the current user the owner; `--slug`
defaults to a hyphenated lowercase name.

| Command | Description |
| --------- | ------------- |
| `orgs list` | List organizations you own or belong to |
| `orgs create <name> [--slug slug]` | Create an organization |
| `orgs members <org-id>` | List members |
| `orgs invite <org-id> <email> [--role member\|admin\|owner]` | Invite a user by email |
| `orgs roles <org-id> <user-id> --set member\|admin\|owner` | Change a member's role |
| `orgs remove <org-id> <user-id>` | Remove a member |

```bash
ipilot orgs create acme --slug acme-inc
ipilot orgs members o1
ipilot orgs invite o1 ops@example.com --role admin
```

## Databases

Managed database instances scoped to the current user. Names must be
alphanumeric with underscores only; the CLI validates this against the
same rule the panel uses before sending the request. Passwords are
masked in all responses.

| Command | Description |
| --------- | ------------- |
| `databases list` | List managed databases |
| `databases show <id>` | Show connection details (password masked) |
| `databases create <name> [--app id]` | Create a database |
| `databases delete <id>` | Delete a database (destructive) |

```bash
ipilot databases create appdb --app web
ipilot databases show d1
```

## Reports

On-demand usage reports. The panel computes reports from live data; there
is no stored report list. Exports stream to stdout unless `--file` is
given. Formats are `csv`, `pdf`, `json`; schedule frequencies are `daily`
and `weekly`.

| Command | Description |
| --------- | ------------- |
| `reports generate [--start ISO] [--end ISO]` | Compute a usage report |
| `reports list [--start] [--end]` | Alias for generate |
| `reports download [--format csv\|pdf\|json] [--file path] [--start] [--end]` | Download a report |
| `reports schedule [--frequency daily\|weekly]` | Schedule a recurring report |

```bash
ipilot reports generate --start 2026-01-01 --end 2026-02-01
ipilot reports download --format csv --file report.csv
ipilot reports schedule --frequency weekly
```

## Two-Factor Authentication

TOTP second factor for panel accounts. CLI login uses API keys
(`ipilot login <api-key>`) and never challenges for a TOTP code; these
commands manage the server-side 2FA state that protects panel web
sign-ins. `backup-codes --regenerate` starts a fresh setup flow — confirm
with `verify` to activate the new secret and codes.

| Command | Description |
| --------- | ------------- |
| `two-factor status [--user id]` | Show 2FA status (probed via backup codes) |
| `two-factor setup [--user id]` | Begin setup; prints secret and authenticator URI |
| `two-factor verify <code> [--user id]` | Confirm setup with a TOTP code |
| `two-factor disable --password pw [--user id]` | Disable 2FA (requires password) |
| `two-factor backup-codes [--regenerate] [--user id]` | List or regenerate backup codes |

```bash
ipilot two-factor setup
ipilot two-factor verify 123456
ipilot two-factor backup-codes
ipilot two-factor backup-codes --regenerate
```

## Search

Global search across apps, servers, backups, runbooks, secrets, hosts,
and audit actions. Uses `/api/global-search`, falling back to the legacy
`/api/search` when the panel does not implement it. Results are
normalised to `{type, id, title, subtitle}` and deduplicated by
`(type, id)`. `--type` restricts to one kind; `--limit` caps the output.

| Command | Description |
| --------- | ------------- |
| `search <query> [--type t] [--types a,b] [--limit n]` | Search all resource types |

Known types: `app`, `server`, `backup`, `runbook`, `secret`, `host`,
`audit`. `--type` restricts to a single kind; `--types` accepts a
comma-separated list and is combined with `--type` when both are given.

```bash
ipilot search web
ipilot search backup --type backup
ipilot --output json search deploy --limit 10
ipilot search web --types app,server
```

## TUI (Terminal UI)

| Command | Description |
| --------- | ------------- |
| `tui dashboard` | Interactive dashboard |
| `tui monitor [server]` | Real-time monitoring |
| `tui logs [server]` | Log viewer |

## Developer Tools

| Command | Description |
| --------- | ------------- |
| `doctor doctor [--fix] [--verbose]` | System diagnostics |
| `benchmark [--server]` | Performance benchmarks (alias for `doctor benchmark`) |
| `diagnose [--server] [--issue connectivity\|performance\|disk]` | Issue diagnosis (alias for `doctor diagnose`) |

---

*Source: `ipilot <command> --help` for each command*
