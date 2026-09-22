# Configuration

## Environment file

Copy `.env.example` to `.env` and keep `.env` out of version control. The root
example is the authoritative list of values used by the default Compose stack.

| Group | Important variables | Purpose |
|---|---|---|
| PostgreSQL | `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_PORT` | Database service and service connection strings. |
| Panel | `MANAGEMENT_FRONTEND_PORT`, `MANAGEMENT_BACKEND_PORT`, `VITE_API_URL`, `CORS_ORIGINS` | Browser/UI and Express API exposure. |
| Orchestrator | `ORCHESTRATOR_WEBHOOK_PORT`, `GITHUB_WEBHOOK_SECRET`, `GITOPS_WEBHOOK_TOKEN`, `FEDERATION_API_TOKEN` | Webhook/API listener and request authentication. |
| Monitoring/load test | `PROMETHEUS_PORT`, `GRAFANA_PORT`, `K6_*` | Optional monitoring and k6 profiles. |
| Discord | `DISCORD_TOKEN`, `PTERODACTYL_API_URL`, `PTERODACTYL_API_KEY` | Optional `discord` profile. |

Run `bash scripts/generate-env.sh` after copying the example to generate blank
secret values. In production, provide secrets through your deployment platform
rather than committing an `.env` file.

## CLI configuration and precedence

The CLI stores its default configuration in `~/.ipilot/config.json` and named profiles in `~/.ipilot/config-<profile>.json`. It uses `http://localhost:3001` when no API URL is configured.

```bash
# Authenticate; the returned token is stored in the selected profile/default config
ipilot login <api-key>

# One-command overrides
IPILOT_API_URL=https://panel.example.test ipilot server list
IPILOT_TOKEN=<token> ipilot server list
IPILOT_OUTPUT=json ipilot server list
```

Configuration is resolved in this order: built-in defaults, default config
file, selected profile file, then `IPILOT_API_URL`, `IPILOT_TOKEN`, and
`IPILOT_OUTPUT` environment variables. Use `ipilot --help` to see how to
select a profile and output format in the current CLI build.

## Network and authentication boundaries

- The panel's setup and selected health/documentation routes are public;
  operational `/api/*` routes use the panel's authentication middleware.
- The orchestrator exposes `/health` and `/metrics` for probes and Prometheus.
  Webhook/API authentication is documented in [Auth Matrix](11-Auth-Matrix.md).
- `FEDERATION_API_TOKEN` protects the orchestrator `/api/` route group when configured. Do not expose it to browsers.
- The Discord service has access to `/var/run/docker.sock` in Compose; restrict it to trusted hosts and administrators.

See [`.env.example`](../.env.example) and the service-level `.env.example` files for exact defaults.
