# Documentation maintenance guide

This guide defines the repository's documentation contract. It is
intentionally close to the code so that a feature can be documented
in the same pull request that introduces it.

## Source of truth

| Area | Primary implementation | Documentation to update when it changes |
|---|---|---|
| Local stack, ports, profiles, required secrets | `docker-compose.yml`, `.env.example` | `README.md`, `wiki/01-Installation.md`, `wiki/03-Configuration.md` |
| CLI commands, global options, profiles | `cli/ipilot/main.py`, `cli/ipilot/commands/`, `cli/ipilot/config.py` | `cli/README.md`, `wiki/05-CLI-Reference.md` |
| Panel routes and user-facing features | `services/management-panel/server/index.ts`, `src/` | `services/management-panel/README.md`, OpenAPI at `/api/openapi.json` |
| Orchestrator routes, manifests, providers, RBAC | `services/orchestrator-agent/webhook_server.py`, `manifest/`, `compute/`, `rbac/` | `services/orchestrator-agent/README.md`, `wiki/06-Architecture.md`, `wiki/11-Auth-Matrix.md` |
| Discord integration | `services/discord-service/index.js`, `modules/`, `.env.example` | `services/discord-service/README.md` |
| Backup and recovery scripts | `scripts/db-backup.sh`, `scripts/db-restore.sh` | `wiki/12-Backup-Restore.md` |
| Panel screenshots and visual docs | `services/management-panel/src/pages/`, `src/components/` | `docs/screenshots/`, root `README.md` |
| Architecture invariants | `docker-compose.yml`, service routers, `helm/` | `docs/ARCHITECTURE.md`, `wiki/06-Architecture.md` |

Generated interfaces take precedence over prose: use `ipilot --help`
for the installed CLI, `/api/openapi.json` for panel requests, and the
orchestrator's `api_docs/openapi.yaml` for its contract.

## The 25-line rule

Every approximately 25 lines of new or materially changed
**behavioral code** must have a nearby documentation unit. A documentation
unit is one of the following:

1. A docstring/JSDoc/TSDoc that explains the public contract, inputs, outputs, side effects, and failure behaviour.
2. A short heading and explanatory paragraph in the closest README or
   design document for a cohesive implementation block.
3. A contract artifact such as OpenAPI, a schema, or a tested example, linked from the relevant README.

Do not add filler comments merely to meet a line count. Group tightly
related code under one useful section; split long, independent flows into
separately headed sections. Update examples whenever flags, environment
variables, paths, default ports, authentication, or destructive effects
change.

## Pull-request checklist

- [ ] Compare changed behaviour with the source-of-truth table above.
- [ ] Add or revise one documentation unit for each roughly 25-line behavioural block.
- [ ] Mark optional services and required secrets accurately; never place real tokens in examples.
- [ ] Verify commands and URLs against the current implementation.
- [ ] Run the relevant help, schema, test, or lint command and record it in the PR.

## Review cadence

Review this guide, the root README, and the wiki
installation/configuration/architecture pages whenever Compose, public
routes, or CLI registration changes. Review service READMEs whenever their
package scripts, Dockerfiles, or environment examples change.
