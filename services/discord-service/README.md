# Discord Service

Optional Node.js integration that handles Discord workflows and
Pterodactyl-backed server provisioning. In the root Compose file it is disabled
by default and is enabled with the `discord` profile.

## Start it

### With Docker Compose (recommended)

```bash
# From the repository root; configure Discord/Pterodactyl values in .env first.
docker compose --profile discord up -d discord-service
docker compose logs -f discord-service
```

The health endpoint is published on `http://localhost:3002/health` by default. The service mounts the host Docker socket in Compose; run it only on a trusted host.

### Standalone development

```bash
cd services/discord-service
npm install
cp .env.example .env
node index.js
```

## Configuration

| Variables | Purpose |
|---|---|
| `DISCORD_TOKEN` | Discord bot token. |
| `PTERODACTYL_API_URL`, `PTERODACTYL_API_KEY`, `LOCATION_ID` | Pterodactyl provisioning connection and location. |
| `SERVER_CREATION_CHANNEL_ID`, `SERVER_CREATOR_ROLE_ID` | Discord access points for provisioning. |
| `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` | PostgreSQL-backed modules. |
| `WHITELIST_IDS`, `SERVER_LIMIT`, `HEALTH_CHECK_INTERVAL_SECONDS` | Operational limits and monitoring. |
| `API_BASE_URL` | Management-panel API URL (Compose uses `http://management-panel:3001`). |

See `.env.example` for optional backup, database-management, code-review, and
notification values. Keep all tokens out of source control.

## Module map

The `modules/` directory groups independently loaded features such as
provisioning, ticketing, backups, monitoring/alerts, databases, resource
pools, templates, scheduling, role management, and Pterodactyl calls.
`index.js` wires Discord events and commands; `integration.js` and
`cli-bridge.js` connect to the surrounding Infra Pilot services.

## Checks

```bash
npm test
```
