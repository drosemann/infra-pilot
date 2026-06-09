# 05 – CLI Reference

## Global Usage

```bash
ipilot [global-flags] <command> [subcommand] [flags]
```

### Global Flags

| Flag | Kurzform | Beschreibung |
|------|----------|-------------|
| `--version` | | Version anzeigen |
| `--output` | `-o` | Format: `json`, `table`, `yaml`, `plain` (default: `table`) |

---

## Core Commands

| Command | Beschreibung |
|---------|-------------|
| `login <api_key>` | Authentifizieren |
| `logout` | Token löschen |
| `health` | System-Health-Check |
| `config get [key]` | CLI-Konfiguration anzeigen |
| `config set <key> <value>` | CLI-Konfiguration setzen |

## Server Management

| Command | Flags |
|---------|-------|
| `server list` | |
| `server create` | `--name`, `--type`, `--memory` |
| `server delete <id>` | |
| `server status <id>` | |
| `logs <server>` | `--lines`, `--follow` |
| `backup list <server>` | |
| `backup create <server>` | |
| `deploy <server> <branch>` | |

## Networking

| Command | Flags |
|---------|-------|
| `dns zones` | |
| `dns create-zone` | `--domain`, `--ttl` |
| `dns records <zone>` | |
| `dns add-record` | `--zone-id`, `--name`, `--type`, `--value`, `--ttl` |
| `vpn create` | `--name`, `--server`, `--port`, `--protocol` |
| `proxy create` | `--domain`, `--target`, `--tls` |
| `bgp create` | `--name`, `--peer-as`, `--peer-ip` |
| `segment create` | `--name`, `--cidr`, `--env` |

## Edge & IoT

| Command | Flags |
|---------|-------|
| `edge list` | `--device-type`, `--status` |
| `edge register` | `--name`, `--device-type`, `--hardware-id` |
| `fn deploy` | `--name`, `--runtime`, `--device-id`, `--source`, `--handler` |
| `iot codes` | `--count`, `--ttl` |
| `mesh create` | `--name`, `--mesh-type`, `--subnet` |

## Green Computing

| Command | Flags |
|---------|-------|
| `energy current` | |
| `energy history` | `--server-id`, `--hours` |
| `carbon current` | |
| `carbon history` | |
| `green schedule` | `--name`, `--command`, `--urgency` |
| `offset quote` | `--project-type` |
| `provider rank` | |
| `reclaim scan` | |

## FinOps & Cost Management

| Command | Flags |
|---------|-------|
| `finops commitment` | |
| `finops spot` | |
| `finops anomaly` | |
| `finops rightsizing` | |
| `finops waste` | |
| `finops budget` | |

## Security & Compliance

| Command | Flags |
|---------|-------|
| `vuln cves` | |
| `vuln scan` | |
| `cspm scan` | |
| `compliance scan` | `--benchmark` |
| `secrets findings` | |
| `soar playbooks` | |

## Resilience & DR

| Command | Flags |
|---------|-------|
| `dr create` | `--name`, `--region` |
| `dr failover` | |
| `chaos create` | `--name`, `--fault`, `--duration` |
| `heal status` | |

## Platform Engineering

| Command | Flags |
|---------|-------|
| `environments create` | `--ttl`, `--branch` |
| `scaffold generate` | `--params` |
| `scorecards create` | `--dora` |
| `techdebt list` | `--severity` |

> **Hinweis:** Dies ist eine Übersicht der wichtigsten Commands. Das vollständige CLI umfasst 200+ Befehle. Nutze `ipilot <command> --help` für Details zu jedem Befehl.

---

*Stand: Mai 2026 · [Quellcode: cli/ipilot/cli.py](https://github.com/daaanieltv/infra-pilot/blob/main/cli/ipilot/cli.py)*
