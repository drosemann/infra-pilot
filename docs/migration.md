# Migrating from infra-pilot to infra-passenger

This migration is a rename; behavior and control-plane logic remain the same.

1. Install the new CLI package and use `infra-passenger` (or its short alias,
   `ipas`) instead of the old command.
2. Move local CLI settings from `~/.ipilot/` to `~/.infra-passenger/` and rename
   `IPILOT_API_URL`, `IPILOT_TOKEN`, and `IPILOT_OUTPUT` to
   `INFRA_PASSENGER_API_URL`, `INFRA_PASSENGER_TOKEN`, and
   `INFRA_PASSENGER_OUTPUT`.
3. Rename GitOps configuration files to `infra-passenger.yaml`, and update
   manifest API groups to `infra-passenger.io/v1`.
4. Update Compose project names, Helm paths, image tags, labels, CI variables,
   and repository links to use `infra-passenger`.

No data schema or API behavior changes are required. Rebuild or redeploy the
same services after changing names so containers, labels, and generated output
are consistent.
