# Infra Pilot CLI (`ipilot`)

Python/Typer command-line client for the management-panel API. It defaults to `http://localhost:3001` and supports table or JSON-oriented output.

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
|---|---|
| `server`, `backup`, `deploy`, `logs` | Core infrastructure lifecycle, backups, deployments, and logs. |
| `gitops`, `ssh`, `inventory`, `secrets` | Declarative operations, remote-access records, metadata, and secret workflows. |
| `plugins`, `templates`, `webhooks`, `apikeys` | Extensibility and automation configuration. |
| `doctor`, `tui`, `rollback` | Diagnostics, terminal UI, and change recovery. |
| `login`, `logout`, `completion`, `interactive`, `batch`, `docs` | Global authentication, shell, interactive, batch, and documentation helpers. |

The installed CLI is the source of truth for flags and availability:

```bash
ipilot --help
ipilot server --help
ipilot docs --output docs/cli-reference.md
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
