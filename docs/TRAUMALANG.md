# TraumaLang-Port (v2.2)

Teile von Infra Pilot liegen zusätzlich als [TraumaLang](https://github.com/drosemann/TraumaLang)-Programme (`.tl`, v2.2) vor.
TraumaLang ist eine satirische Sprache („Jira-Ticket trifft Cloud-Postmortem trifft Change-Advisory-Board"), deren Compiler
(`traumalang`, in C geschrieben) `.tl`-Dateien nach C (GCC) übersetzt.
Sprachreferenz und Keyword-Tabelle stehen im [TraumaLang-Repo](https://github.com/drosemann/TraumaLang) unter
`docs/LANGUAGE.md`, `docs/GRAMMAR.md`, `docs/KEYWORDS.md`; die Rewrite-Engine ist in `docs/REWRITER.md` beschrieben.

## Regeln dieser Portierung

- Jedes `.tl`-Programm beginnt mit `IT'S SHOWTIME` und endet mit `YOU HAVE BEEN TERMINATED`.
- Ausgaben nutzen `TALK TO THE HAND "…"` (direkte String-Literale sind erlaubt).
- Quellkommentare/Docstrings werden zu `PUT IT IN JIRA …`.
- Nicht übersetzbare Konstrukte werden **niemals** stillschweigend als gleichwertig ausgegeben:
  sie erzeugen Warnungen im Format `Zeile N: Konstrukt nicht vollständig unterstützt`.
- `traumalang rewrite --from <lang> -i <datei> -o <datei.tl>` (optional `--roast`) wurde
  **nicht ausgeführt**, sondern manuell nach dem Rewriter-Mapping nachgebildet.
  Build/Test-Status aller `.tl`-Dateien: **nicht ausgeführt**.

## Übersetzte Dateien (179)

| Quelle | `.tl`-Datei | Abdeckung |
| --- | --- | --- |
| `tests/conftest.py` | `tests/conftest.tl` | vollständig gelesen |
| `tests/scripts/test_update_flow.py` (212 Zeilen) | `tests/scripts/test_update_flow.tl` | vollständig gelesen |
| `tests/discord/test_report_bot.js` (46 Zeilen) | `tests/discord/test_report_bot.tl` | vollständig gelesen |
| `tests/infrastructure/test_naming_resolver.py` (186 Zeilen) | `tests/infrastructure/test_naming_resolver.tl` | vollständig gelesen |
| `tests/infrastructure/__init__.py` (0 Zeilen) | `tests/infrastructure/__init__.tl` | Markierung |
| `tests/orchestrator/__init__.py` (0 Zeilen) | `tests/orchestrator/__init__.tl` | Markierung |
| `tests/load/k6/smoke.js` (37 Zeilen) | `tests/load/k6/smoke.tl` | vollständig gelesen |
| `tests/load/k6/soak.js` (44 Zeilen) | `tests/load/k6/soak.tl` | vollständig gelesen |
| `tests/load/k6/spike.js` (46 Zeilen) | `tests/load/k6/spike.tl` | vollständig gelesen |
| `tests/load/k6/common.js` (195 Zeilen) | `tests/load/k6/common.tl` | vollständig gelesen |
| `infra/naming/resolver.py` (81 Zeilen) | `infra/naming/resolver.tl` | vollständig gelesen |
| `infra/__init__.py` | `infra/__init__.tl` | Markierung |
| `infra/naming/__init__.py` | `infra/naming/__init__.tl` | Markierung |
| `cli/__init__.py` | `cli/__init__.tl` | vollständig |
| `cli/ipilot/__init__.py` | `cli/ipilot/__init__.tl` | vollständig |
| `cli/ipilot/config.py` (186 Zeilen) | `cli/ipilot/config.tl` | vollständig gelesen |


| `cli/ipilot/core/exceptions.py` (45 Zeilen) | `cli/ipilot/core/exceptions.tl` | vollständig gelesen |

| `cli/ipilot/core/command_registry.py` (89 Zeilen) | `cli/ipilot/core/command_registry.tl` | vollständig gelesen |


| `cli/ipilot/output/formatters.py` | `cli/ipilot/output/formatters.tl` | vollständig gelesen |
| `cli/ipilot/output/styling.py` | `cli/ipilot/output/styling.tl` | vollständig gelesen |

| `cli/ipilot/commands/pet.py` | `cli/ipilot/commands/pet.tl` | Zeilen 1–60 gelesen |
| `services/orchestrator-agent/rate_limiter.py` (482 Zeilen) | `services/orchestrator-agent/rate_limiter.tl` | vollständig gelesen |
| `services/orchestrator-agent/config.py` (325 Zeilen) | `services/orchestrator-agent/config.tl` | vollständig gelesen |
| `cli/ipilot/client.py` (725 Zeilen) | `cli/ipilot/client.tl` | vollständig gelesen |
| `cli/ipilot/main.py` (213 Zeilen) | `cli/ipilot/main.tl` | vollständig gelesen |
| `cli/ipilot/core/cli.py` (77 Zeilen) | `cli/ipilot/core/cli.tl` | vollständig gelesen |
| `cli/ipilot/commands/infrastructure/backup.py` (391 Zeilen) | `cli/ipilot/commands/infrastructure/backup.tl` | vollständig gelesen |
| `cli/ipilot/core/__init__.py` (39 Zeilen) | `cli/ipilot/core/__init__.tl` | vollständig gelesen |
| `cli/ipilot/output/__init__.py` (37 Zeilen) | `cli/ipilot/output/__init__.tl` | vollständig gelesen |
| `cli/ipilot/commands/__init__.py` (60 Zeilen) | `cli/ipilot/commands/__init__.tl` | vollständig gelesen |
| `cli/ipilot/commands/apikeys/__init__.py` | `cli/ipilot/commands/apikeys/__init__.tl` | Markierung (Inhalt in `commands/apikeys.tl`) |
| `cli/ipilot/commands/doctor/__init__.py` | `cli/ipilot/commands/doctor/__init__.tl` | Markierung (Inhalt in `commands/doctor.tl`) |
| `cli/ipilot/commands/gitops/__init__.py` | `cli/ipilot/commands/gitops/__init__.tl` | Markierung (Inhalt in `commands/gitops.tl`) |
| `cli/ipilot/commands/inventory/__init__.py` | `cli/ipilot/commands/inventory/__init__.tl` | Markierung (Inhalt in `commands/inventory.tl`) |
| `cli/ipilot/commands/plugins/__init__.py` | `cli/ipilot/commands/plugins/__init__.tl` | Markierung (Inhalt in `commands/plugins.tl`) |
| `cli/ipilot/commands/rollback/__init__.py` | `cli/ipilot/commands/rollback/__init__.tl` | Markierung (Inhalt in `commands/rollback.tl`) |
| `cli/ipilot/commands/secrets/__init__.py` | `cli/ipilot/commands/secrets/__init__.tl` | Markierung (Inhalt in `commands/secrets.tl`) |
| `cli/ipilot/commands/ssh/__init__.py` | `cli/ipilot/commands/ssh/__init__.tl` | Markierung (Inhalt in `commands/ssh.tl`) |
| `cli/ipilot/commands/templates/__init__.py` | `cli/ipilot/commands/templates/__init__.tl` | Markierung (Inhalt in `commands/templates.tl`) |
| `cli/ipilot/commands/tui/__init__.py` | `cli/ipilot/commands/tui/__init__.tl` | Markierung (Inhalt in `commands/tui.tl`) |
| `cli/ipilot/commands/webhooks/__init__.py` | `cli/ipilot/commands/webhooks/__init__.tl` | Markierung (Inhalt in `commands/webhooks.tl`) |

| `services/discord-service/index.js` (362 Zeilen) | `services/discord-service/index.tl` | vollständig gelesen |
| `services/discord-service/modules/maintenance.js` (150 Zeilen) | `services/discord-service/modules/maintenance.tl` | vollständig gelesen |
| `services/discord-service/modules/taskScheduler.js` (220 Zeilen) | `services/discord-service/modules/taskScheduler.tl` | vollständig gelesen |
| `services/discord-service/modules/alertManager.js` (156 Zeilen) | `services/discord-service/modules/alertManager.tl` | vollständig gelesen |
| `services/discord-service/modules/ticketSystem.js` (329 Zeilen) | `services/discord-service/modules/ticketSystem.tl` | vollständig gelesen |
| `services/discord-service/modules/statsCommands.js` (253 Zeilen) | `services/discord-service/modules/statsCommands.tl` | vollständig gelesen |
| `services/discord-service/modules/roleManager.js` (258 Zeilen) | `services/discord-service/modules/roleManager.tl` | vollständig gelesen |
| `services/discord-service/modules/vpsCommands.js` (262 Zeilen) | `services/discord-service/modules/vpsCommands.tl` | vollständig gelesen |
| `services/discord-service/modules/monitoring.js` (283 Zeilen) | `services/discord-service/modules/monitoring.tl` | vollständig gelesen |
| `services/discord-service/modules/healthChecks.js` (314 Zeilen) | `services/discord-service/modules/healthChecks.tl` | vollständig gelesen |
| `services/discord-service/modules/templateManager.js` (133 Zeilen) | `services/discord-service/modules/templateManager.tl` | vollständig gelesen |
| `services/discord-service/modules/resourcePools.js` (176 Zeilen) | `services/discord-service/modules/resourcePools.tl` | vollständig gelesen |
| `services/discord-service/modules/dbManager.js` (238 Zeilen) | `services/discord-service/modules/dbManager.tl` | vollständig gelesen |
| `services/discord-service/modules/legacyCommands.js` (293 Zeilen) | `services/discord-service/modules/legacyCommands.tl` | vollständig gelesen |
| `services/discord-service/modules/vpsManager.js` (371 Zeilen) | `services/discord-service/modules/vpsManager.tl` | vollständig gelesen |
| `services/discord-service/tests/smoke.test.js` (47 Zeilen) | `services/discord-service/tests/smoke.test.tl` | vollständig gelesen |
| `services/orchestrator-agent/alembic/script.py.mako` (23 Zeilen) | `services/orchestrator-agent/alembic/script.tl` | vollständig gelesen |
| `services/orchestrator-agent/alembic/env.py` (68 Zeilen) | `services/orchestrator-agent/alembic/env.tl` | vollständig gelesen |
| `services/orchestrator-agent/alembic/versions/0001_initial_schema.py` (617 Zeilen) | `services/orchestrator-agent/alembic/versions/0001_initial_schema.tl` | vollständig gelesen |
| `scripts/generate-env.sh` | `scripts/generate-env.tl` | vollständig gelesen |
| `scripts/update.sh` (177 Zeilen) | `scripts/update.tl` | vollständig gelesen |
| `cli/ipilot/commands/doctor/__init__.py` (334 Zeilen) | `cli/ipilot/commands/doctor.tl` | vollständig gelesen |
| `scripts/healthcheck.sh` (113 Zeilen) | `scripts/healthcheck.tl` | vollständig gelesen |
| `scripts/db-backup.sh` (330 Zeilen) | `scripts/db-backup.tl` | vollständig gelesen |
| `scripts/db-restore.sh` (158 Zeilen) | `scripts/db-restore.tl` | vollständig gelesen |
| `scripts/install-deps.sh` (96 Zeilen) | `scripts/install-deps.tl` | vollständig gelesen |
| `scripts/prerequisites-check.sh` (67 Zeilen) | `scripts/prerequisites-check.tl` | vollständig gelesen |
| `scripts/verify.sh` (115 Zeilen) | `scripts/verify.tl` | vollständig gelesen |
| `scripts/setup.sh` (120 Zeilen) | `scripts/setup.tl` | vollständig gelesen |
| `scripts/release.sh` (101 Zeilen) | `scripts/release.tl` | vollständig gelesen |
| `scripts/docker-build.sh` (119 Zeilen) | `scripts/docker-build.tl` | vollständig gelesen |
| `scripts/test.sh` (176 Zeilen) | `scripts/test.tl` | vollständig gelesen |
| `tests/scripts/test_pr_voting.py` (325 Zeilen) | `tests/scripts/test_pr_voting.tl` | vollständig gelesen |
| `tests/scripts/test_backup_scripts.py` (387 Zeilen) | `tests/scripts/test_backup_scripts.tl` | vollständig gelesen |
| `scripts/update_readme_coverage.sh` (60 Zeilen) | `scripts/update_readme_coverage.tl` | vollständig gelesen |
| `scripts/coverage_badge_updater.py` (78 Zeilen) | `scripts/coverage_badge_updater.tl` | vollständig gelesen |
| `scripts/coverage_lib.py` (33 Zeilen) | `scripts/coverage_lib.tl` | vollständig gelesen |
| `scripts/coverage_report.py` (26 Zeilen) | `scripts/coverage_report.tl` | vollständig gelesen |
| `scripts/coverage_report.sh` (47 Zeilen) | `scripts/coverage_report_sh.tl` | vollständig gelesen |
| `scripts/coverage_summary.py` (39 Zeilen) | `scripts/coverage_summary.tl` | vollständig gelesen |
| `scripts/pr_voting.py` (321 Zeilen) | `scripts/pr_voting.tl` | vollständig gelesen |
| `scripts/capture-screenshots.mjs` (156 Zeilen) | `scripts/capture-screenshots.tl` | vollständig gelesen |
| `scripts/prerequisites-check.ps1` (34 Zeilen) | `scripts/prerequisites-check-ps.tl` | vollständig gelesen |
| `scripts/docker-build.ps1` (58 Zeilen) | `scripts/docker-build-ps.tl` | vollständig gelesen |
| `scripts/verify.ps1` (54 Zeilen) | `scripts/verify-ps.tl` | vollständig gelesen |
| `scripts/healthcheck.ps1` (66 Zeilen) | `scripts/healthcheck-ps.tl` | vollständig gelesen |
| `scripts/release.ps1` (66 Zeilen) | `scripts/release-ps.tl` | vollständig gelesen |
| `scripts/install-deps.ps1` (65 Zeilen) | `scripts/install-deps-ps.tl` | vollständig gelesen |
| `scripts/generate-env.ps1` (70 Zeilen) | `scripts/generate-env-ps.tl` | vollständig gelesen |
| `scripts/test.ps1` (78 Zeilen) | `scripts/test-ps.tl` | vollständig gelesen |
| `scripts/setup.ps1` (82 Zeilen) | `scripts/setup-ps.tl` | vollständig gelesen |
| `tests/cli/test_command_registry.py` (94 Zeilen) | `tests/cli/test_command_registry.tl` | vollständig gelesen |
| `tests/cli/test_main_extra.py` (99 Zeilen) | `tests/cli/test_main_extra.tl` | vollständig gelesen |
| `tests/cli/test_inventory_commands.py` (103 Zeilen) | `tests/cli/test_inventory_commands.tl` | vollständig gelesen |
| `tests/cli/test_styling.py` (127 Zeilen) | `tests/cli/test_styling.tl` | vollständig gelesen |
| `tests/cli/test_core_cli.py` (143 Zeilen) | `tests/cli/test_core_cli.tl` | vollständig gelesen |
| `tests/cli/test_config.py` (147 Zeilen) | `tests/cli/test_config.tl` | vollständig gelesen |
| `tests/cli/test_gitops_commands.py` (141 Zeilen) | `tests/cli/test_gitops_commands.tl` | vollständig gelesen |
| `tests/cli/test_config_profiles.py` (218 Zeilen) | `tests/cli/test_config_profiles.tl` | vollständig gelesen |
| `tests/cli/test_output.py` (196 Zeilen) | `tests/cli/test_output.tl` | vollständig gelesen |
| `tests/cli/test_main.py` (212 Zeilen) | `tests/cli/test_main.tl` | vollständig gelesen |
| `tests/cli/test_doctor_tui.py` (484 Zeilen) | `tests/cli/test_doctor_tui.tl` | vollständig gelesen |
| `tests/cli/test_client.py` (479 Zeilen) | `tests/cli/test_client.tl` | vollständig gelesen |
| `tests/cli/test_secrets_ssh_plugins_webhooks_apikeys.py` (430 Zeilen) | `tests/cli/test_secrets_ssh_plugins_webhooks_apikeys.tl` | vollständig gelesen |
| `tests/cli/test_templates_rollback_infra_gitops.py` (635 Zeilen) | `tests/cli/test_templates_rollback_infra_gitops.tl` | vollständig gelesen |
| `services/orchestrator-agent/compute/__init__.py` (14 Zeilen) | `services/orchestrator-agent/compute/__init__.tl` | vollständig gelesen |
| `services/orchestrator-agent/manifest/__init__.py` (19 Zeilen) | `services/orchestrator-agent/manifest/__init__.tl` | vollständig gelesen |
| `services/orchestrator-agent/rbac/__init__.py` (29 Zeilen) | `services/orchestrator-agent/rbac/__init__.tl` | vollständig gelesen |
| `services/orchestrator-agent/main.py` (39 Zeilen) | `services/orchestrator-agent/main.tl` | vollständig gelesen |
| `services/orchestrator-agent/discord_auth.py` (45 Zeilen) | `services/orchestrator-agent/discord_auth.tl` | vollständig gelesen |
| `services/orchestrator-agent/compute/registry.py` (73 Zeilen) | `services/orchestrator-agent/compute/registry.tl` | vollständig gelesen |
| `services/orchestrator-agent/rbac/models.py` (189 Zeilen) | `services/orchestrator-agent/rbac/models.tl` | vollständig gelesen |
| `services/orchestrator-agent/compute/base.py` (189 Zeilen) | `services/orchestrator-agent/compute/base.tl` | vollständig gelesen |
| `services/orchestrator-agent/fleet_collect.py` (178 Zeilen) | `services/orchestrator-agent/fleet_collect.tl` | vollständig gelesen |
| `services/orchestrator-agent/integration.py` (207 Zeilen) | `services/orchestrator-agent/integration.tl` | vollständig gelesen |
| `services/orchestrator-agent/db.py` (147 Zeilen) | `services/orchestrator-agent/db.tl` | vollständig gelesen |
| `services/discord-service/modules/validation.js` (18 Zeilen) | `services/discord-service/modules/validation.tl` | vollständig gelesen |
| `services/discord-service/modules/pterodactyl.js` (28 Zeilen) | `services/discord-service/modules/pterodactyl.tl` | vollständig gelesen |
| `services/discord-service/modules/db.js` (28 Zeilen) | `services/discord-service/modules/db.tl` | vollständig gelesen |
| `services/discord-service/modules/backupScheduler.js` (49 Zeilen) | `services/discord-service/modules/backupScheduler.tl` | vollständig gelesen |
| `services/discord-service/modules/docker.js` (64 Zeilen) | `services/discord-service/modules/docker.tl` | vollständig gelesen |
| `services/discord-service/modules/petCommands.js` (85 Zeilen) | `services/discord-service/modules/petCommands.tl` | vollständig gelesen |
| `services/discord-service/modules/serverLimits.js` (92 Zeilen) | `services/discord-service/modules/serverLimits.tl` | vollständig gelesen |
| `services/discord-service/cli-bridge.js` (97 Zeilen) | `services/discord-service/cli-bridge.tl` | vollständig gelesen |
| `services/discord-service/integration.js` (192 Zeilen) | `services/discord-service/integration.tl` | vollständig gelesen |
| `services/discord-service/modules/serverStatus.js` (208 Zeilen) | `services/discord-service/modules/serverStatus.tl` | vollständig gelesen |
| `services/discord-service/modules/ticketCommands.js` (204 Zeilen) | `services/discord-service/modules/ticketCommands.tl` | vollständig gelesen |
| `cli/ipilot/commands/infrastructure/logs.py` (33 Zeilen) | `cli/ipilot/commands/infrastructure/logs.tl` | vollständig gelesen |
| `cli/ipilot/commands/apikeys/__init__.py` (63 Zeilen) | `cli/ipilot/commands/apikeys.tl` | vollständig gelesen |
| `cli/ipilot/commands/rollback/__init__.py` (85 Zeilen) | `cli/ipilot/commands/rollback.tl` | vollständig gelesen |
| `cli/ipilot/commands/webhooks/__init__.py` (92 Zeilen) | `cli/ipilot/commands/webhooks.tl` | vollständig gelesen |
| `cli/ipilot/commands/plugins/__init__.py` (95 Zeilen) | `cli/ipilot/commands/plugins.tl` | vollständig gelesen |
| `cli/ipilot/commands/templates/__init__.py` (103 Zeilen) | `cli/ipilot/commands/templates.tl` | vollständig gelesen |
| `cli/ipilot/commands/tui/__init__.py` (112 Zeilen) | `cli/ipilot/commands/tui.tl` | vollständig gelesen |
| `cli/ipilot/commands/secrets/__init__.py` (140 Zeilen) | `cli/ipilot/commands/secrets.tl` | vollständig gelesen |
| `cli/ipilot/commands/inventory/__init__.py` (149 Zeilen) | `cli/ipilot/commands/inventory.tl` | vollständig gelesen |
| `cli/ipilot/commands/ssh/__init__.py` (145 Zeilen) | `cli/ipilot/commands/ssh.tl` | vollständig gelesen |
| `cli/ipilot/commands/gitops/__init__.py` (251 Zeilen) | `cli/ipilot/commands/gitops.tl` | vollständig gelesen |
| `cli/ipilot/commands/infrastructure/server.py` (155 Zeilen) | `cli/ipilot/commands/infrastructure/server.tl` | vollständig gelesen |
| `cli/ipilot/commands/infrastructure/deployment.py` (83 Zeilen) | `cli/ipilot/commands/infrastructure/deployment.tl` | vollständig gelesen |
| `cli/ipilot/commands/infrastructure/__init__.py` (8 Zeilen) | `cli/ipilot/commands/infrastructure/__init__.tl` | vollständig gelesen |
| `services/orchestrator-agent/rbac_store.py` (243 Zeilen) | `services/orchestrator-agent/rbac_store.tl` | vollständig gelesen |
| `services/orchestrator-agent/vps_manager.py` (94 Zeilen) | `services/orchestrator-agent/vps_manager.tl` | vollständig gelesen |
| `services/orchestrator-agent/compute/docker_provider.py` (216 Zeilen) | `services/orchestrator-agent/compute/docker_provider.tl` | vollständig gelesen |
| `services/orchestrator-agent/rbac/engine.py` (308 Zeilen) | `services/orchestrator-agent/rbac/engine.tl` | vollständig gelesen |
| `services/orchestrator-agent/resource_monitor.py` (232 Zeilen) | `services/orchestrator-agent/resource_monitor.tl` | vollständig gelesen |
| `services/orchestrator-agent/vps_docker_support.py` (232 Zeilen) | `services/orchestrator-agent/vps_docker_support.tl` | vollständig gelesen |
| `services/orchestrator-agent/secrets_manager.py` (577 Zeilen) | `services/orchestrator-agent/secrets_manager.tl` | vollständig gelesen |
| `services/orchestrator-agent/webhook_server.py` (948 Zeilen) | `services/orchestrator-agent/webhook_server.tl` | vollständig gelesen |
| `services/orchestrator-agent/living_fleet.py` (341 Zeilen) | `services/orchestrator-agent/living_fleet.tl` | vollständig gelesen |
| `services/orchestrator-agent/vps_backup_snapshots.py` (280 Zeilen) | `services/orchestrator-agent/vps_backup_snapshots.tl` | vollständig gelesen |
| `services/orchestrator-agent/vps_container_lifecycle.py` (296 Zeilen) | `services/orchestrator-agent/vps_container_lifecycle.tl` | vollständig gelesen |
| `services/orchestrator-agent/vps_health_monitoring.py` (396 Zeilen) | `services/orchestrator-agent/vps_health_monitoring.tl` | vollständig gelesen |
| `services/orchestrator-agent/vps_instance_persistence.py` (254 Zeilen) | `services/orchestrator-agent/vps_instance_persistence.tl` | vollständig gelesen |
| `services/orchestrator-agent/manifest/engine.py` (390 Zeilen) | `services/orchestrator-agent/manifest/engine.tl` | vollständig gelesen |
| `services/orchestrator-agent/manifest/schema.py` (407 Zeilen) | `services/orchestrator-agent/manifest/schema.tl` | vollständig gelesen |
| `services/orchestrator-agent/install.sh` (65 Zeilen) | `services/orchestrator-agent/install.tl` | vollständig gelesen |
| `services/orchestrator-agent/tests/conftest.py` (153 Zeilen) | `services/orchestrator-agent/tests/conftest.tl` | vollständig gelesen |
| `services/orchestrator-agent/tests/smoke/test_imports.py` (36 Zeilen) | `services/orchestrator-agent/tests/smoke/test_imports.tl` | vollständig gelesen |
| `services/orchestrator-agent/tests/unit/test_db_migrations.py` (55 Zeilen) | `services/orchestrator-agent/tests/unit/test_db_migrations.tl` | vollständig gelesen |
| `services/orchestrator-agent/tests/unit/test_orchestration_cogs.py` (63 Zeilen) | `services/orchestrator-agent/tests/unit/test_orchestration_cogs.tl` | vollständig gelesen |
| `services/orchestrator-agent/tests/unit/test_openapi_contract.py` (89 Zeilen) | `services/orchestrator-agent/tests/unit/test_openapi_contract.tl` | vollständig gelesen |
| `services/orchestrator-agent/tests/unit/test_secrets_manager.py` (87 Zeilen) | `services/orchestrator-agent/tests/unit/test_secrets_manager.tl` | vollständig gelesen |
| `services/orchestrator-agent/tests/unit/test_auth_observability.py` (86 Zeilen) | `services/orchestrator-agent/tests/unit/test_auth_observability.tl` | vollständig gelesen |
| `services/orchestrator-agent/tests/unit/test_living_fleet.py` (96 Zeilen) | `services/orchestrator-agent/tests/unit/test_living_fleet.tl` | vollständig gelesen |
| `services/orchestrator-agent/tests/unit/test_config_validation.py` (99 Zeilen) | `services/orchestrator-agent/tests/unit/test_config_validation.tl` | vollständig gelesen |
| `services/orchestrator-agent/tests/unit/test_federation_auth.py` (126 Zeilen) | `services/orchestrator-agent/tests/unit/test_federation_auth.tl` | vollständig gelesen |
| `services/orchestrator-agent/tests/unit/test_compute_providers.py` (137 Zeilen) | `services/orchestrator-agent/tests/unit/test_compute_providers.tl` | vollständig gelesen |
| `services/orchestrator-agent/tests/unit/test_rbac_api.py` (137 Zeilen) | `services/orchestrator-agent/tests/unit/test_rbac_api.tl` | vollständig gelesen |
| `services/orchestrator-agent/tests/unit/test_manifest_schema.py` (139 Zeilen) | `services/orchestrator-agent/tests/unit/test_manifest_schema.tl` | vollständig gelesen |
| `services/orchestrator-agent/tests/unit/test_rate_limiter.py` (214 Zeilen) | `services/orchestrator-agent/tests/unit/test_rate_limiter.tl` | vollständig gelesen |
| `services/orchestrator-agent/tests/unit/test_manifest_engine.py` (226 Zeilen) | `services/orchestrator-agent/tests/unit/test_manifest_engine.tl` | vollständig gelesen |
| `services/orchestrator-agent/tests/unit/test_rbac_store.py` (229 Zeilen) | `services/orchestrator-agent/tests/unit/test_rbac_store.tl` | vollständig gelesen |
| `services/orchestrator-agent/tests/unit/test_rbac_engine.py` (259 Zeilen) | `services/orchestrator-agent/tests/unit/test_rbac_engine.tl` | vollständig gelesen |
| `services/orchestrator-agent/tests/unit/test_hardening_p0.py` (273 Zeilen) | `services/orchestrator-agent/tests/unit/test_hardening_p0.tl` | vollständig gelesen |
| `services/orchestrator-agent/tests/unit/test_webhook_auth.py` (318 Zeilen) | `services/orchestrator-agent/tests/unit/test_webhook_auth.tl` | vollständig gelesen |
| `services/orchestrator-agent/tests/unit/test_vps_manager.py` (361 Zeilen) | `services/orchestrator-agent/tests/unit/test_vps_manager.tl` | vollständig gelesen |
| `services/orchestrator-agent/tests/unit/test_deploy_api.py` (330 Zeilen) | `services/orchestrator-agent/tests/unit/test_deploy_api.tl` | vollständig gelesen |

## Keyword-Mappings

- Programmrahmen: `IT'S SHOWTIME` / `YOU HAVE BEEN TERMINATED`
- `def` / Bash-Funktion / JS-Modulsetup / Test-Helper / Klasse: `WE NEED TO TAKE THIS OFFLINE <name>` / `THIS COULD HAVE BEEN AN EMAIL`
- Command-Funktionen: je eigene Funktion + `TALK TO THE HAND`-Beschreibung
- App-Erzeugung (`typer.Typer(…)`), Command-Registrierung (`register(…)(app)`), Registry-Dict: Funktionshüllen + `TALK TO THE HAND`
- Variablendeklaration: `WE HAVE 240 EMPLOYEES AND 340 ACTIVE ACCOUNTS <var>`
- Zuweisung: `I NEED YOUR CLOTHES YOUR BOOTS AND YOUR MOTORCYCLE <var> <wert>`
- Null (`None`): `I LIKE TO SET VERY VAGUE GOALS`
- Bedingung: `DO IT FOR THE METRICS` / `BLUE IS BROKEN GREEN IS WORSE` / `YOU HAVE BEEN TERMINATED`
- Ausgabe: `TALK TO THE HAND "…"`; Kommentare: `PUT IT IN JIRA …`

## Was noch fehlt

Die vollständige, pro Datei aufgeschlüsselte Liste steht in [TRAUMALANG-GAPS](../TRAUMALANG-GAPS.md):
offene Quelldateien, nur angerissene Module, nicht unterstützte Konstrukte und
eine Arbeitsanleitung für den nächsten Portierungs-Agenten.
