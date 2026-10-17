# Infra Pilot CLI (`ipilot`)

Python/Typer command-line client for the management-panel API. It defaults to `http://localhost:3001` and
supports table or JSON-oriented output.

## Installation and login

```bash
pip install ./cli
ipilot --help
ipilot login <api-key>
```

For editable development installation, run `pip install -e ./cli`.
Set `IPILOT_API_URL` to target a non-default panel API; `IPILOT_TOKEN` and
`IPILOT_OUTPUT` override the stored token and output format for a single
command.

## Command groups

| Command | Responsibility |
| --- | --- |
| `server`, `backup`, `deploy`, `logs` | Core infrastructure lifecycle, backups, deployments, and logs. |
| `gitops`, `ssh`, `inventory`, `secrets` | Declarative operations, remote-access records, metadata, and secret workflows. |
| `plugins`, `templates`, `webhooks`, `apikeys` | Extensibility and automation configuration. |
| `metrics`, `alerts`, `audit` | Resource metrics, alert rules/incidents, and the audit log. |
| `runbooks`, `maintenance`, `notifications` | Operational runbooks, maintenance windows, and notification channels. |
| `orgs`, `databases`, `reports` | Organizations and memberships, managed databases, and usage reports. |
| `two-factor`, `search` | Panel-account 2FA management and global search. |
| `doctor`, `tui`, `rollback` | Diagnostics, terminal UI, and change recovery. |
| `login`, `logout`, `completion`, `interactive`, `batch`, `docs` | Global authentication, shell, interactive, batch, and documentation helpers. |

The installed CLI is the source of truth for flags and availability:

```bash
ipilot --help
ipilot server --help
ipilot metrics --help
ipilot docs --output docs/cli-reference.md
```

### Observability and operations

```bash
ipilot metrics realtime --app app-1
ipilot metrics history --since 24h --interval 1h
ipilot alerts list --rules
ipilot alerts create-rule --metric cpu --operator gt --threshold 90
ipilot alerts acknowledge 42
ipilot audit list --action alert:create --limit 20
ipilot audit export --format csv --file audit.csv
ipilot audit watch --interval 5
```

### Runbooks, maintenance, and notifications

```bash
ipilot runbooks list
ipilot runbooks create --file runbook.yaml
ipilot runbooks execute r1 --wait --timeout 120
ipilot maintenance create --title "db upgrade" \
  --starts 2026-02-01T00:00:00Z --ends 2026-02-01T02:00:00Z
ipilot notifications create ops-hook --type webhook \
  --config '{"url": "https://example.com/h"}'
ipilot notifications test n1
ipilot runbooks validate --file runbook.yaml
```

### Organizations, databases, reports, 2FA, and search

```bash
ipilot orgs create acme --slug acme-inc
ipilot orgs invite o1 ops@example.com --role admin
ipilot databases create appdb --app web
ipilot reports download --format csv --file report.csv
ipilot two-factor setup
ipilot two-factor verify 123456
ipilot search web --types app,server
```

`ipilot docs` produces a help-based reference for the current executable.
The curated examples are in [wiki/04-Usage-Examples.md](../wiki/04-Usage-Examples.md);
configuration precedence is in [wiki/03-Configuration.md](../wiki/03-Configuration.md).

## Configuration files

The default profile is `~/.ipilot/config.json`; named profiles are stored as
`~/.ipilot/config-<profile>.json`. Environment overrides take precedence over
persisted values. Do not put credentials in shell history or commit profile
files.

## Development checks

```bash
pytest tests/cli/ -v
```
