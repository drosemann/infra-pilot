# infra-passenger CLI (`infra-passenger`)

Python/Typer command-line client for the management-panel API. It defaults to `http://localhost:3001` and supports table or JSON-oriented output.

## Installation and login

```bash
pip install ./cli
infra-passenger --help
infra-passenger login <api-key>
```

For editable development installation, run `pip install -e ./cli`.
Set `INFRA_PASSENGER_API_URL` to target a non-default panel API; `INFRA_PASSENGER_TOKEN` and
`INFRA_PASSENGER_OUTPUT` override the stored token and output format for a single
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
infra-passenger --help
infra-passenger server --help
infra-passenger docs --output docs/cli-reference.md
```

`infra-passenger docs` produces a help-based reference for the current executable.
The curated examples are in [wiki/04-Usage-Examples.md](../wiki/04-Usage-Examples.md);
configuration precedence is in [wiki/03-Configuration.md](../wiki/03-Configuration.md).

## Configuration files

The default profile is `~/.infra-passenger/config.json`; named profiles are stored as
`~/.infra-passenger/config-<profile>.json`. Environment overrides take precedence over
persisted values. Do not put credentials in shell history or commit profile
files.

## Development checks

```bash
pytest tests/cli/ -v
```
