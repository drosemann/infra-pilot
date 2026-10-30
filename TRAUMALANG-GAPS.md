# TraumaLang-Port — Lücken, offene Arbeiten, Anleitung

Stand: 179 `.tl`-Dateien (Backend-Batches 1-22). Sprache: [TraumaLang v2.2](https://github.com/drosemann/TraumaLang)
(Compiler `traumalang`, `.tl` → C via GCC; Referenz: `docs/LANGUAGE.md`, `docs/GRAMMAR.md`,
`docs/KEYWORDS.md`, `docs/REWRITER.md` im verlinkten Repo).
Übersichts-Doku: [docs/TRAUMALANG.md](./docs/TRAUMALANG.md).

Diese Datei listet **alles, was noch fehlt**, damit ein anderer Agent die Portierung
anders/fortführend implementieren kann: offene Quelldateien, nur angerissene Module,
nicht unterstützte Konstrukte, sämtliche Zeilen-Warnungen und eine Arbeitsanleitung.

Grundsätze (aus dem Ursprungsauftrag, bitte einhalten):

- Nur lesen und schreiben. Keine Befehle ausführen, nichts bauen/installieren/testen.
  Build/Test-Status aller `.tl`-Dateien: **nicht ausgeführt** (gilt fort, bis jemand
  mit Compiler-Zugriff `traumalang build/run` tatsächlich laufen lässt).
- Jedes Programm beginnt mit `IT'S SHOWTIME`, endet mit `YOU HAVE BEEN TERMINATED`.
- Ausgaben via `TALK TO THE HAND "…"` (direkte String-Literale erlaubt).
- Quellkommentare/Docstrings → `PUT IT IN JIRA <name>`.
- Nicht übersetzbare Konstrukte **niemals** als semantisch gleichwertig ausgeben, sondern
  Warnung im Format `Zeile N: Konstrukt nicht vollständig unterstützt`.
- Der offizielle Weg wäre `traumalang rewrite --from <lang> -i <datei> -o <datei.tl>`
  (optional `--roast`); bisher wurde er **nicht ausgeführt**, alles ist manuell nach
  dem Rewriter-Mapping (`docs/REWRITER.md`) nachgebildet. `--roast` wurde nirgends verwendet.

## Arbeitsanleitung für den nächsten Agenten

1. Nächste offene Datei aus Abschnitt 2/3 wählen (kleine zuerst).
2. Quelle mit Lesezugriff lesen (bei großen Dateien in Fenstern, gelesenen Bereich im
   Abschlussbericht vermerken).
3. `.tl`-Datei daneben schreiben (gleicher Name, Endung `.tl`), Rahmen + Keyword-Mappings
   aus [docs/TRAUMALANG.md](./docs/TRAUMALANG.md) nutzen.
4. Pro nicht abbildbarem Konstrukt eine `Zeile N`-Warnung in den Abschlussbericht aufnehmen.
5. Diese Datei (`TRAUMALANG-GAPS.md`) und [docs/TRAUMALANG.md](./docs/TRAUMALANG.md)
   aktualisieren: Datei aus „offen" streichen, Dateiliste + Warnungen ergänzen.
6. Tokens sparen: keine Subagenten, keine parallelen Erkundungen, keine Rewrites
   bereits fertiger `.tl`-Dateien ohne Anlass.

## 1. Übersetzte Dateien — was jeweils noch fehlt

Jede `.tl`-Datei ist eine **Satire-Skizze, kein lauffähiges Äquivalent**.
Was pro Datei konkret fehlt bzw. nur angerissen ist:

- `tests/conftest.tl` ← `tests/conftest.py`: Hook-Logik (`inspect.iscoroutinefunction`,
  Fixture-Dict, `asyncio.run`) nur als Strings. Fehlt: alles jenseits der gelesenen 35 Zeilen
  gibt es nicht (Datei ist vollständig gelesen, aber semantisch nur Hülle).
- `tests/scripts/test_update_flow.tl` ← nur Zeilen 1–50 gelesen. Rest der Datei
  (Stub-Bodies für docker/git/compose, eigentliche Testfunktionen, Assertions) **nicht gelesen,
  nicht portiert**.
- `cli/__init__.tl`, `cli/ipilot/__init__.tl`: reine Docstring-/Versionsdateien, vollständig.
  Keine Lücke.
- `cli/ipilot/config.tl` ← `config.py` voll gelesen (186 Zeilen). Semantik (JSON laden/speichern,
  Profile, `os.environ`-Final-Word, F-String-Pfade) nur als Strings. Fehlt: echte
  `load`/`save`-Abläufe, `get` ist Hülle ohne Rückgabe.
- `cli/ipilot/main.tl` ← nur Zeilen 1–120 gelesen. Rest ab Zeile 120
  (`benchmark`-Command und alles danach) **nicht gelesen, nicht portiert**.
- `cli/ipilot/client.tl` ← nur Zeilen 1–50 gelesen. Rest (`_headers`-Rest, alle
  `cmd_*`/Endpoint-Methoden, Fehlerbehandlung) **nicht gelesen, nicht portiert**.
- `cli/ipilot/core/exceptions.tl`: 7 Klassen nur als `PUT IT IN JIRA` + Sammel-`TALK TO THE HAND`.
  Fehlt: Vererbungshierarchie, Raise-/Catch-Semantik (in TraumaLang nicht ausdrückbar).
- `cli/ipilot/core/__init__.tl` ← nur Zeilen 1–30 gelesen. `__all__`-Rest ab Zeile 30
  **nicht gelesen, nicht portiert**.
- `cli/ipilot/core/command_registry.tl` ← voll gelesen (89 Zeilen). Echte Registry-Logik
  (Dict mit Tupeln, `walk_packages`, `add_typer`) nur als Strings.
- `cli/ipilot/core/cli.tl` ← nur Zeilen 1–60 gelesen. `get_client`-Rest ab Zeile 58
  **nicht gelesen, nicht portiert**.
- `cli/ipilot/output/__init__.tl` ← nur Zeilen 1–30 gelesen. `__all__`-Rest
  **nicht gelesen, nicht portiert**.
- `cli/ipilot/output/formatters.tl` ← nur Zeilen 1–140 gelesen. Rest ab Zeile 140
  (`_dict_table`, `_key_value_table`, `print_output`) **nun voll gelesen (218 Zeilen)**; alle Funktionen als Huellen + `TALK TO THE HAND`.
- `cli/ipilot/output/styling.tl` ← nur Zeilen 1–60 gelesen. Rest ab Zeile 60
  (`print_error/info/json/success`, `spinner`) **nun voll gelesen (124 Zeilen)**; alle Funktionen als Huellen + `TALK TO THE HAND`.
- `cli/ipilot/commands/__init__.tl` ← nur Zeilen 1–50 gelesen. `__all__`-Rest
  **nicht gelesen, nicht portiert**.
- `cli/ipilot/commands/pet.tl` ← nur Zeilen 1–60 gelesen. `rename`-Rest ab Zeile 60
  **nicht gelesen, nicht portiert**.
- `services/orchestrator-agent/rate_limiter.tl` ← nun voll gelesen (482 Zeilen). Kernlogik
  (Ringpuffer, Token-Bucket/Sliding-Window-Entscheidung, Zeitgrenzen) **nun als Huellen portiert**.
  nicht portiert**.
- `services/orchestrator-agent/config.tl` ← nun voll gelesen (325 Zeilen). `checks`-Liste,
  Produktions-Branch (`raise` vs. Warnung + Rückgabe) **nun als Huellen portiert**.
- `services/discord-service/index.tl` ← nun voll gelesen (362 Zeilen). Bot-Login,
  Event-Handler, Command-Dispatch (Rest der Datei) **nun als Huellen portiert**.
- `scripts/generate-env.tl` ← voll gelesen. `gen_secret`-/`fill`-Logik (openssl, grep, awk,
  mv) nur als Strings; kein ausführbarer Ersatz.
- `scripts/update.tl` ← voll gelesen (177 Zeilen). 4-Schritte-Ablauf (Preflight, Backup,
  `git pull --ff-only`, `compose up -d --build`, Healthcheck + Volume-Verify) nur als
  `TALK TO THE HAND`-Kette; Flags/Guards nur als Strings.

- `cli/ipilot/commands/doctor.tl` (neu): `doctor/__init__.py` voll gelesen (334 Zeilen). Funktionen (`_get_client`, `_memory_usage`, `_disk_usage`, `_load_average`, `doctor`, `benchmark`, `diagnose`) als Huellen + `TALK TO THE HAND`. Fehlt: echte Checks, /proc/meminfo-Parsing, ctypes-Branch, shutil.which-Kette, API-Healthcheck.
- `scripts/healthcheck.tl` (neu): `healthcheck.sh` voll gelesen (113 Zeilen). Funktionen (`success`/`warn`/`error`/`info`/`usage`/`check_file`/`check_docker_service`) + Datei-/Docker-Checks nur als `TALK TO THE HAND`-Kette; Flags/Guards nur als Strings.

- `scripts/db-backup.tl` (neu): `db-backup.sh` voll gelesen (330 Zeilen). Funktionen (`success`/`warn`/`error`/`info`/`usage`/`write_checksum`/`maybe_encrypt_and_upload`/`prune`) + Postgres-/Redis-/Grafana-/Borg-Ablauf nur als `TALK TO THE HAND`-Kette; Flags/Guards nur als Strings.

- `scripts/db-restore.tl` (neu): `db-restore.sh` voll gelesen (158 Zeilen). Funktionen (`info`/`success`/`error`/`usage`) + GPG-Decrypt-, Header-/Dry-run-Checks, Confirm-Prompt, pg_restore-/Redis-/Grafana-Ablauf nur als `TALK TO THE HAND`-Kette; Flags/Guards nur als Strings.

- `scripts/install-deps.tl` (neu): `install-deps.sh` voll gelesen (96 Zeilen). Funktionen (`info`/`success`/`warn`/`error`/`usage`) + npm-/pip-Installationsablauf nur als `TALK TO THE HAND`-Kette; Flags/Guards nur als Strings.

- `scripts/prerequisites-check.tl` (neu): `prerequisites-check.sh` voll gelesen (67 Zeilen). Funktionen (`info`/`success`/`warn`/`error`/`usage`/`check_command`) + Docker-/Node-/Python-/Git-/Compose-Pruefung nur als `TALK TO THE HAND`-Kette; Flags/Guards nur als Strings.

- `scripts/verify.tl` (neu): `verify.sh` voll gelesen (115 Zeilen). Funktionen (`info`/`success`/`warn`/`error`/`usage`/`run_stage`) + Health-/Setup-/Test-/Lint-/Integration-Stufen nur als `TALK TO THE HAND`-Kette; Flags/JSON-Aufbau nur als Strings.

- `scripts/setup.tl` (neu): `setup.sh` voll gelesen (120 Zeilen). Funktionen (`info`/`success`/`warn`/`error`/`usage`/`check_command`) + Prereq-/Infra-/Service-Checks und .env-Anlage nur als `TALK TO THE HAND`-Kette; Flags/Guards nur als Strings.

- `scripts/release.tl` (neu): `release.sh` voll gelesen (101 Zeilen). Funktionen (`info`/`success`/`warn`/`error`/`usage`) + Tag-/Changelog-/Push-Ablauf nur als `TALK TO THE HAND`-Kette; Flags/Guards nur als Strings.

- `scripts/docker-build.tl` (neu): `docker-build.sh` voll gelesen (119 Zeilen). Funktionen (`info`/`success`/`warn`/`error`/`usage`) + Versions-/Build-/Push-Ablauf nur als `TALK TO THE HAND`-Kette; Flags/Guards nur als Strings.

- `scripts/test.tl` (neu): `test.sh` voll gelesen (176 Zeilen). Funktionen (`info`/`success`/`warn`/`error`/`section`/`usage`/`run_pytest_suite`) + Python-/Node-Suitenablauf mit Coverage-, Offline- und JSON-Zweig nur als `TALK TO THE HAND`-Kette; Flags/Zaehler nur als Strings.

- `tests/scripts/test_pr_voting.tl` (neu): `test_pr_voting.py` voll gelesen (325 Zeilen). FakeGh-, Helper- und Testgruppen (`count_votes`, `select_winner`, `is_ci_green`, `main`, failure propagation) als Huellen + `TALK TO THE HAND`. Fehlt: echte Assert-/Fixture-Semantik (in TraumaLang nicht ausdrueckbar).

- `tests/scripts/test_backup_scripts.tl` (neu): `test_backup_scripts.py` voll gelesen (387 Zeilen). Helper-, Fixture- und Testklassen (`run`, `stub`, `backup_tools`, `selfhosted_tools`, Backup-/Restore-Help, Upload-, Grafana-, Borg-, Sha256-, Prune-Tests) als Huellen + `TALK TO THE HAND`. Fehlt: echte Assert-/Fixture-/Parametrize-Semantik (in TraumaLang nicht ausdrueckbar).

- `scripts/update_readme_coverage.tl` (neu): `update_readme_coverage.sh` voll gelesen (60 Zeilen). Funktionen (`info`/`success`/`warn`/`error`/`usage`) + Badge-Updater-Call und Badge-Commit-Push nur als `TALK TO THE HAND`-Kette; Guards nur als Strings.

- `scripts/coverage_badge_updater.tl` (neu): `coverage_badge_updater.py` voll gelesen (78 Zeilen). Funktionen (`read_coverage_percent`, `update_readme`, `main`) als Huellen + `TALK TO THE HAND`. Fehlt: echte Regex-/Datei-Semantik (in TraumaLang nur als Strings).

- `scripts/coverage_lib.tl` (neu): `coverage_lib.py` voll gelesen (33 Zeilen). Funktion (`read_line_rate`) als Huelle + `TALK TO THE HAND`. Fehlt: echte XML-/Optional-Semantik (in TraumaLang nur als Strings).

- `scripts/coverage_report.tl` (neu): `coverage_report.py` voll gelesen (26 Zeilen). Funktion (`main`) als Huelle + `TALK TO THE HAND`. Fehlt: echte JSON-/Exit-Semantik (in TraumaLang nur als Strings).

- Backend-Batch (36 Dateien, alle voll gelesen, nur Huellen + `TALK TO THE HAND`): Orchestrator (`compute/__init__`, `manifest/__init__`, `rbac/__init__`, `main`, `discord_auth`, `compute/registry`, `rbac/models`, `compute/base`, `fleet_collect`, `integration`, `db`), Discord (`validation`, `pterodactyl`, `db`, `backupScheduler`, `docker`, `petCommands`, `serverLimits`, `cli-bridge`, `integration`, `serverStatus`, `ticketCommands`), CLI (`infrastructure/logs`, `apikeys`, `rollback`, `webhooks`, `plugins`, `templates`, `tui`, `secrets`, `inventory`, `ssh`, `gitops`, `infrastructure/server`, `infrastructure/deployment`, `infrastructure/__init__`). Durchgehend nicht abbildbar: Typer-Apps/`@app.command`, `async`/`await`, Klassen/`@dataclass`/`Enum`, `try/except`, Datei-/Env-/Subprozess-Zugriffe, Asserts.

- Backend-Batch 2 (5 Dateien, alle voll gelesen, nur Huellen + `TALK TO THE HAND`): `rbac_store` (Upserts/Deletes/Batch-Load, best-effort mit Fail-Counter), `vps_manager` (Kompatibilitaets-Einstieg mit 4 Mixins), `compute/docker_provider` (Interface auf VPSManager, Lazy-Import, Status-Mapping), `rbac/engine` (CRUD + Checks + Restore, 308 Zeilen), `resource_monitor` (Legacy Docker/MySQL-Loop). Nicht abbildbar: `async`, Klassen, `try/except`, SQL, Mixins.

- Backend-Batch 3 (2 Dateien, alle voll gelesen, nur Huellen + `TALK TO THE HAND`): `vps_docker_support` (Allow-Listen, Validierungen, Storage-Opt-Fallback, VPSConfig), `secrets_manager` (Vault-/AWS-/Azure-Backends, Token-/Policy-/Transit-Ops, Facade; keine Literal-Secrets, nur Env-Namen). Nicht abbildbar: `re`-Patterns, `dataclass`, Klassen, `try/except`, SDK-Calls.

- Backend-Batch 4 (3 Dateien, alle voll gelesen, nur Huellen + `TALK TO THE HAND`): `webhook_server` (948 Zeilen: RBAC-Routen, Deploy-Reconcile, HMAC-Webhooks, Federation-Auth, Health/Metrics/Ready, Fleet-Routen), `living_fleet` (Mood-Engine, JSON-Store, Fleet-Handler), `vps_backup_snapshots` (Backup/Snapshot-Mixin mit Retention und Restore). Nicht abbildbar: `aiohttp`-Routen/Middlewares, `async`, Klassen, `try/except`, HMAC, SQL.

- Backend-Batch 5 (3 Dateien, alle voll gelesen, nur Huellen + `TALK TO THE HAND`): `vps_container_lifecycle` (Create/Delete/Start/Stop/Restart, Stats, User-Instanzen, Config-Update mit Rollback), `vps_health_monitoring` (Clone/Migrate, Ping-/Port-/Process-/API-Checks mit Allow-Listen, Benchmarks, History/Netz-Stats), `vps_instance_persistence` (Postgres-primaer/JSON-Fallback mit Lock, DB-CRUD, SSH-Command). Nicht abbildbar: `async`, Klassen/Mixins, `try/except`, Docker-SDK, SQL.

- Backend-Batch 6 (2 Dateien, alle voll gelesen, nur Huellen + `TALK TO THE HAND`): `manifest/engine` (390 Zeilen: Drift-Erkennung, Reconcile mit Dry-Run, Netz-/Volume-Anlage), `manifest/schema` (407 Zeilen: InfraFile-Modelle, from_dict, validate/to_dict, Teil-Validatoren). Nicht abbildbar: `dataclass`/`Enum`, `async`, Docker-SDK, `ipaddress`-Pruefung, `raise ValueError`.

- Backend-Batch 7 (4 Dateien, alle voll gelesen, nur Huellen + `TALK TO THE HAND`): `discord/index` (362 Zeilen: Registrierungs-State-Machine, Slash-Dispatch, Reactions, Webhook-Health, Login-Gate), `maintenance` (Cleanup-Dry-Run/Run, Update-Check/Apply), `taskScheduler` (Cron-CRUD mit Admin-/Ownership-Checks, Single-Flight-Reload), `alertManager` (Schwellwert-Loop, DM-Embeds, Alert-CRUD). Nicht abbildbar: `async`, Event-Handler, cron, SQL, `require`-Zyklen.

- Backend-Batch 8 (3 Dateien, alle voll gelesen, nur Huellen + `TALK TO THE HAND`): `ticketSystem` (Panel/Channel/Welcome/Close/Transcript/Staff), `statsCommands` (Pool, Slash-Defs, Stats-/Leaderboard-Handler, Format-Helper), `roleManager` (Menu/Reaction/DM, Custom-Create/Edit, Info, Hierarchie, Bulk). Nicht abbildbar: Klassen, `async`, SQL-`$1`-Platzhalter, Embeds.

- Backend-Batch 9 (3 Dateien, alle voll gelesen, nur Huellen + `TALK TO THE HAND`): `vpsCommands` (11 Slash-Specs, Create/List/Lifecycle/Stats/Backup/Restore/Update mit Ownership und Delete-Confirm), `monitoring` (Minuten-Collect, Peak-DB, Cooldown-Alerts, QuickChart-Graphen, Admin-Schwellen), `healthChecks` (Ping/Port/Process/API mit Allow-Listen, Loop mit Reentrancy-Guard, DM bei Fehlern, Health-CRUD). Nicht abbildbar: `async`, Event-Handler, cron, SQL, `Buffer`/Embeds.

- Backend-Batch 10 (3 Dateien, alle voll gelesen, nur Huellen + `TALK TO THE HAND`): `templateManager` (Versioned-Create mit Retry, Apply-latest, Dedup-Liste), `resourcePools` (Optimistic-Concurrency-Member-Mutation, CRUD mit Ownership), `dbManager` (MySQL-Container pro User, Wait-Ready, DM-Creds; Passwoerter nur zur Laufzeit generiert). Nicht abbildbar: `async`, SQL-`$1`-Platzhalter, JSONB, Embeds.

- Backend-Batch 11 (4 Dateien, alle voll gelesen, nur Huellen + `TALK TO THE HAND`): `legacyCommands` (Credits-Tabelle, Spawn-Capture, Tmate-Deploy, Cuttly-Earn mit Cooldowns, Renew, Serveo-Forwards; Secrets nur als Env-Namen), `alembic/script` (Mako-Template), `alembic/env` (DB-URL aus Env, Offline-/Online-Modus), `0001_initial_schema` (617 Zeilen: alle Baseline-Tabellen, destruktiver Downgrade). Nicht abbildbar: `async`, SQL, Mako-Syntax, Downgrade-Semantik.

- Backend-Batch 12 (2 Dateien, jetzt voll gelesen, nur Huellen + `TALK TO THE HAND`): `config` (325 Zeilen: Platzhalter-Defaults nie als Literale, Secret-Validierung fail-fast, alle Gruppen), `rate_limiter` (482 Zeilen: TokenBucket/SlidingWindow asserts, Limiter-Checks, 429-Middleware, Regel-Registry mit Default-Regeln). Nicht abbildbar: `dataclass`, `assert`, `async`, `re`, LRU-`OrderedDict`.

- Backend-Batch 13 (3 Dateien, alle voll gelesen, nur Huellen + `TALK TO THE HAND`): `client` (725 Zeilen: alle Endpoint-Gruppen Auth/Server/SSH/Inventory/Secrets/Webhooks/Keys/Plugins/Templates/Doctor/Rollback/Fleet), `main` (213 Zeilen: Login/Logout/Assets/Benchmark/Diagnose/Docs/REPL), `core/cli` (77 Zeilen: App-Registrierung, Client-Factory). Nicht abbildbar: `requests`-Session, `typer`-Apps, `CliRunner`-Aliase.

- Backend-Batch 14 (5 Dateien, alle voll gelesen, nur Huellen + `TALK TO THE HAND`): `infrastructure/backup` (391 Zeilen: Local-/API-Modus, Dry-Run, Verify mit Header-Check), `core/__init__`, `output/__init__`, `core/exceptions`, `commands/__init__` (Registrierungen, Fehlerklassen). Nicht abbildbar: `typer`-Apps, `subprocess`, Datei-Checks, Lazy-Import-`__getattr__`.

- Backend-Batch 15 (4 Dateien, alle voll gelesen, nur Huellen + `TALK TO THE HAND`): `coverage_report.sh` (Pytest-Coverage-Lauf + Summary + HTML-Hinweis), `coverage_summary` (Prozent + JSON; Quelle enthaelt latenten Bug: `sys.stderr` ohne `sys`-Import in einer Branch), `pr_voting` (321 Zeilen: gh-CLI-Vote/Merge/Comment-Pipeline), `capture-screenshots` (156 Zeilen: Playwright, 6 Routen, hermetische Kontexte, Demo-Fixtures; Platzhalter-Tokens nie als Literale). Nicht abbildbar: `subprocess`, `argparse`, Playwright-`async`, `dataclass`.

- Backend-Batch 16 (9 Dateien, alle voll gelesen, nur Huellen + `TALK TO THE HAND`): alle 9 `.ps1`-Zwillinge (`prerequisites-check`, `docker-build`, `verify`, `healthcheck`, `release`, `install-deps`, `generate-env`, `test`, `setup`) als `-ps.tl`-Port. Nicht abbildbar: `Get-Command`, `Write-Host`-Farben, `Join-Path`/`Test-Path`, `ConvertTo-Json`, RNGCrypto, Call-Operator `&`.

- Backend-Batch 17 (5 Dateien, alle voll gelesen, nur Huellen + `TALK TO THE HAND`): `test_command_registry`, `test_main_extra`, `test_inventory_commands`, `test_styling`, `test_core_cli` (Fixtures, Runner-Invokes, Mock-Clients, Asserts als Strings). Nicht abbildbar: `pytest`-Fixtures, `CliRunner`, `MagicMock`, `capsys`/`caplog`.

- Backend-Batch 18 (4 Dateien, alle voll gelesen, nur Huellen + `TALK TO THE HAND`): `test_config`, `test_gitops_commands`, `test_config_profiles`, `test_output` (Env-Fixtures, Runner-Invokes, Mock-Clients, exakte String-Asserts). Nicht abbildbar: `pytest`-Fixtures, `patch.dict`, `CliRunner`, Mock-`assert_called`.

- Backend-Batch 19 (2 Dateien, alle voll gelesen, nur Huellen + `TALK TO THE HAND`): `test_main` (Boot-Smoke, Version/Login/Logout/Batch/Docs/Doctor-Alias-Gruppen), `test_doctor_tui` (Doctor/Benchmark/Diagnose/Memory/Load/Disk/TUI/Textual-Stub-Gruppen, 484 Zeilen). Nicht abbildbar: `pytest`-Fixtures, `CliRunner`, `MagicMock`, `ctypes`-Stubs, `sys.modules`-Patches.

- Backend-Batch 20 (3 Dateien, alle voll gelesen, nur Huellen + `TALK TO THE HAND`): `test_client` (Health/Auth/Server/SSH/Keys/Doctor/Webhooks-Gruppen, 479 Zeilen), `test_secrets_ssh_plugins_webhooks_apikeys` (alle 5 Gruppen, 430 Zeilen; Fixture-Key nur generisch), `test_templates_rollback_infra_gitops` (Templates/Rollback/Server/Deploy/Logs/Backup/Inventory/Gitops-Extras, 635 Zeilen). Nicht abbildbar: `pytest`-Fixtures, `CliRunner`, `MagicMock`, exakte String-Asserts.

- Backend-Batch 21 (11 Dateien, alle voll gelesen, nur Huellen + `TALK TO THE HAND`): `test_update_flow`-Rest (Stub-Tools, Help/CheckOnly/FullFlow/Volumes/SkipBackup/NoDocker, 212 Zeilen), `test_report_bot` (Mocha Constructor/Command/Button/Cron, 46 Zeilen), `test_naming_resolver` (Yaml/Base/Overrides/Merge/Map/Resolve/Env, 186 Zeilen), `resolver` (Yaml-Map Merge Env Override, 81 Zeilen), k6 `smoke`/`soak`/`spike`/`common` (Szenarien, Thresholds, Manifest-Builder, 37/44/46/195 Zeilen; Token nur als Env-Namen), 4 leere `__init__`-Markierungen. Nicht abbildbar: `pytest`/`mocha`-Fixtures, `subprocess`-Stubs, k6-`http`/`check`/`crypto`, `yaml.safe_load`.

- Backend-Batch 22 (35 Dateien, alle voll gelesen, nur Huellen + `TALK TO THE HAND`): 11 `commands/*/__init__`-Marker (Inhalt steckt in den flachen `<name>.tl`-Ports), `vpsManager` (Tabellen, Lifecycle, Stats, Backups, Retention, Restore, Exec, 371 Zeilen), discord-`smoke` (Modul-Load, Validation, RoleManager, 47 Zeilen), `install` (Tool-Checks, Setup-Key, Clone, Token, Build, Run; Key nur als Name), orchestrator-`conftest` (No-DB-Stub, Mock-Docker, 153 Zeilen), `test_imports` (Modul-Importe, 36 Zeilen), 19 Unit-Tests (DB-Migration, Cogs, OpenAPI-Contract, Secrets, Auth-Observability, LivingFleet, Config-Validation, Federation, Compute, RBAC-API/Store/Engine, Manifest-Schema/Engine, RateLimiter, Hardening, Webhook-Auth, VPS-Manager, Deploy-API; Fixture-Tokens nur generisch). Nicht abbildbar: `pytest`/`unittest`-Fixtures, `aiohttp`-TestClient, `docker-py`-Mocks, SQL-Strings, HMAC-Logik, exakte Status-Asserts.

- `cli/ipilot/commands/gitops/blame.tl` / `tests/cli/test_gitops_blame.tl` (neu): blame-aware GitOps (`run_git_blame`, `parse_blame_porcelain`, `resource_spans`, `annotate` mit uncommitted/stale/many-hands/unknown-Risiken, `blame`-Command, `plan --blame`). Fehlt: echte git-Subprocess-Semantik (nur Huellen + `TALK TO THE HAND`). Panel-Dateien (`server/git-blame.ts`, `src/pages/GitBlame.tsx`, Tests) haben keine `.tl`-Zwillinge (`services/management-panel/` komplett offen, siehe 2f).

## 2. Noch gar nicht übersetzte Quelldateien

### 2a. `cli/ipilot/commands/`-Submodule (alle erledigt, siehe Abschnitt 1 und Batches)

- (infrastructure/backup.py erledigt, siehe Abschnitt 1 und Batch 14),
  (alle CLI-Module erledigt),


  (bereinigt),
  (bereinigt),
  (bereinigt),
  (bereinigt),
  (bereinigt)
- Hinweis: Registrierungsnamen stehen in `commands/__init__.tl`
  (server, backup, deploy, logs, gitops, ssh, inventory, secrets, plugins, doctor,
  webhooks, apikeys, templates, tui, rollback, pet; alle Module existieren als `.tl`-Skizzen).

### 2b. `cli/ipilot/`-Reste

- (client.py, main.py, core/cli.py erledigt, siehe Abschnitt 1 und Batch 13)





- `output/formatters.py`-Rest und `output/styling.py`-Rest: erledigt (voll gelesen, siehe Abschnitt 1)


- `commands/__init__.py` ab Zeile 51 (`__all__`-Rest)
- `commands/pet.py` ab Zeile 61 (`rename`-Rest)

### 2c. `scripts/`-Reste (alle offen außer `generate-env.sh`, `update.sh`, `healthcheck.sh`, `db-backup.sh`, `db-restore.sh`, `install-deps.sh`, `prerequisites-check.sh`, `verify.sh`, `setup.sh`, `release.sh`, `test.sh`, `update_readme_coverage.sh`, `coverage_badge_updater.py`, `coverage_lib.py`, `coverage_report.py`, `coverage_report.sh`, `coverage_summary.py`, `pr_voting.py`, `capture-screenshots.mjs`)

- (scripts-Reste erledigt: capture-screenshots, coverage_report.sh, coverage_summary.py, pr_voting.py),


  (alle .ps1-Zwillinge erledigt, siehe Abschnitt 1 und Batch 16),

- (alle 9 `.ps1`-Zwillinge erledigt: docker-build, generate-env,
  `healthcheck`, `install-deps`, `prerequisites-check`, `release`, `setup`, `test`, `verify`)
- (docker-build.sh erledigt, siehe Abschnitt 1)

### 2d. `services/orchestrator-agent/`-Reste (alle erledigt, siehe Abschnitt 1 und Batches)

- (config.py und rate_limiter.py erledigt, siehe Abschnitt 1; Rest unten),
  (Rest: vps lifecycles unten),
  `vps_container_lifecycle.py`,
  `vps_container_lifecycle.py`,
  `vps_health_monitoring.py`, `vps_instance_persistence.py`
- Hersteller-Logik (DB, RBAC, Secrets, Webhooks) enthält Security-Sensibles:
  Secrets **niemals** als Literale in `.tl` übernehmen (vgl. Warnung zu `config.py` Zeile 29
  und `orchestrator-agent/config.py`-Platzhaltern).

### 2e. `services/discord-service/`-Reste (alle erledigt, siehe Abschnitt 1 und Batches)

- Discord-Module: alle erledigt (index, alle 21 Module, cli-bridge, integration)




- JS ist Rewriter-Sprache (`--from javascript`); `async function` mappt zusätzlich auf
  `I WAS DOUBLE-BOOKED ON 2 OFFSITES` — bisher ungenutzt, steht für den nächsten Agenten bereit.

### 2f. `services/management-panel/` (komplett offen)

- TypeScript/React/Express-App (`server/index.ts`, `src/`, `src/components/`,
  `src/pages/`). Rewriter-Sprache wäre `--from typescript`. Bisher keine einzige
  `.tl`-Datei; wegen Größe dateiweise vorgehen, mit kleinen Modulen beginnen.
- OpenAPI-Vertrag (`/api/openapi.json`) und `api_docs/openapi.yaml` des Orchestrators
  sind als Kontraktquellen zu lesen, aber keine `.tl`-Ziele.

### 2g. `tests/`-Reste (alle offen außer `conftest.py`, `test_update_flow.py`-Kopf)

- `tests/cli/` (11 erledigt, siehe Batches 17-19): `test_client.py`,



  `test_secrets_ssh_plugins_webhooks_apikeys.py`,
  `test_templates_rollback_infra_gitops.py`
- `tests/scripts/` (backup- und voting-Tests erledigt, siehe Abschnitt 1):
  `test_update_flow.py` (ab Zeile 51)
- `tests/infrastructure/`, `tests/discord/`, `tests/load/`, `tests/orchestrator/`,
  `tests/fixtures/` (noch nicht inventarisiert — erst per Dateisuche listen, dann übersetzen)
- Tests enthalten fast nur Asserts/Subprozess-Stubs: in TraumaLang nur als
  Funktionshüllen + `TALK TO THE HAND` abbildbar (kein Assert-Keyword in v2.2).

## 3. Nicht unterstützte Konstrukte (Katalog)

Alle folgenden Konstrukte haben **kein** TraumaLang-v2.2-Äquivalent und wurden in den
`.tl`-Dateien nur als `PUT IT IN JIRA`-Kommentar oder `TALK TO THE HAND`-String
abgebildet — niemals als gleichwertige Semantik:

- Imports/Re-Exports aller Art (`import`, `from … import`, `require()`, relative Imports,
  `importlib.import_module`, `pkgutil.walk_packages`, `__future__`-Imports)
- `sys.path`-Manipulation, Modul-`__getattr__`-Lazy-Loading, `getattr`
- `asyncio` (`iscoroutinefunction`, `asyncio.run`, `**kwargs`-Calls)
- Klassen, Vererbung (`class X(Y)`), `self`, `Enum`, `@dataclass` (+ `__post_init__`-Asserts),
  Closures/Dekorator-Fabriken (`register(…)(app)`, `@app.command`, `@app.callback`)
- Typer-App-Modell: `typer.Typer(…)`, `Context`, `typer.Option`/`typer.Argument`,
  `typer.echo`, `get_completion_script`, `add_typer`, `ctx.ensure_object`
- `requests`-Sessions/Header-Dicts, `process.env`/`os.environ`, `parseInt`-Fallbacks
- Datei-I/O (`open`, `json.load`/`json.dump`, `os.path.*`, `os.listdir`, `os.remove`,
  `symlink_to`, `chmod`, `write_text`), `yaml.safe_load`, `dotenv.config()`
- String-Operationen jenseits von Literalen: F-Strings, `.strip().lower()`, Slicing
  (`fname[7:-5]`), `join`/Generator-`join`, `.items()`-Schleifen
- Datenstrukturen mit Verhalten: typisierte Dicts/Tupel, `OrderedDict`, `frozenset`,
  Dispatch-Dicts mit Funktionsreferenzen, Dict-/List-Comprehensions
- Kontrollfluss ohne Keyword: `for` über Module/Registry/Items, `while` über `$#` mit
  `shift`, `case`-Muster, Rekursion (`_to_yaml` mit Akkumulator), `walk_packages`-Schleifen
- Fehlerbehandlung: `try/except`, `raise`, `logger.warning/error/exception`, Exit-Codes
- Shell: Subshells/Pipes (`openssl | tr`, `grep`, `awk`, `sed`, `mv`), `BASH_SOURCE`-Pfade,
  `read -p`-Prompts, `command -v`, `docker compose`, `git pull --ff-only`, `bash`-Subskripte
- Serialisierung/Prüfung: `isinstance`-/`is None`-/`bool`-Dispatch, `json.dumps`,
  Rich-Rendering (`Console`, `RichTable`, `Panel`, `spinner`), Test-Harness
  (`subprocess.run`, Stub-Bodies, `shutil.which`), Asserts generell

## 4. Warnungsindex (alle `Zeile N`-Warnungen der 179 `.tl`-Dateien)

- `tests/conftest.tl` — Zeile 1 (`import sys/inspect/asyncio/pathlib`); Zeile 14
  (`for mod in list(sys.modules)` mit `del`); Zeile 27 (`inspect.iscoroutinefunction`);
  Zeile 30 (Dict-Comprehension); Zeile 34 (`asyncio.run` mit `**kwargs`)
- `tests/scripts/test_update_flow.tl` — Zeilen 8/12
  (`import shutil/subprocess/pathlib/pytest`); Zeile 14
  (`Path(__file__).resolve().parents[2]`); Zeile 17 (`shutil.which("bash")`); Zeile 20
  (Variadic-Helper mit `CompletedProcess`-Rückgabe); Zeilen 32/42 (innere `stub`-Funktion
  mit Closure, `symlink_to`, `chmod`, F-String-Stub-Bodies)
- `cli/ipilot/config.tl` — Zeile 3 (`import json/logging/os/typing`); Zeile 43
  (`dict()`-Kopie mit Typannotation); Zeilen 46/58 (`os.path.exists`, `open`, `json.load`
  mit `try/except`); Zeilen 67/69/71 (`os.environ`-Zugriff); Zeile 84 (`dict.pop` mit
  Default); Zeile 142 (`os.listdir`-Schleife mit String-Slicing); Zeilen 158/159
  (`os.path.exists`, `os.remove` mit `try/except`); Zeile 174 (F-String-Pfad)
- `cli/ipilot/main.tl` — Zeile 7 (`import typer/yaml`, relative Imports);
  Zeilen 22/46/57 (`@app.command`-Dekoratoren); Zeilen 26/73/99
  (`typer.Argument/Option`-Parameter); Zeilen 62/83/85/106 (`typer.echo`,
  `get_completion_script`); Zeile 104 (`yaml.safe_load` mit `try/except`); Zeile 113
  (`for op in …`)
- `cli/ipilot/client.tl` — Zeile 10 (`import requests`); Zeile 21 (`class ApiClient`
  mit `self`); Zeilen 32/44 (`__init__`, `requests.Session`, Header-Dict); Zeile 29
  (Token-Parameter als Secret erkannt, nicht als Literal übernommen)
- `cli/ipilot/core/exceptions.tl` — Zeilen 9/13/17/21/25/29/33
  (`class …(Exception)`-Vererbung, 7 Klassen)
- `cli/ipilot/core/__init__.tl` — Zeilen 5/6 (relative Re-Export-Imports); Zeile 17
  (Modul-`__getattr__`-Lazy-Import mit `getattr`)
- `cli/ipilot/core/command_registry.tl` — Zeilen 3/8 (`import importlib/pkgutil/typer`);
  Zeile 12 (typisiertes Registry-Dict mit Tupel); Zeilen 27/34 (Dekorator-Fabrik mit
  Closure); Zeilen 44/55 (`importlib.import_module`, `pkgutil.walk_packages`);
  Zeilen 52/71/81 (`for`-Schleifen, Dict-Comprehension); Zeile 72 (`app.add_typer`)
- `cli/ipilot/core/cli.tl` — Zeilen 3/6/8 (`import logging/typer`, relative Imports);
  Zeilen 21/28 (`typer.Typer(…)`-Konstruktion, `@app.callback`-Dekorator);
  Zeilen 31/37/43 (`typer.Option`-Parameter); Zeilen 49/50 (`ctx.ensure_object`,
  `load_config`-Kontextbefüllung)
- `cli/ipilot/output/__init__.tl` — Zeilen 3/11 (relative Re-Export-Imports)
- `cli/ipilot/output/formatters.tl` — Zeile 3 (`import json/logging/sys/typing`);
  Zeilen 27/33 (Formatter-Dispatch-Dict mit Funktionsreferenzen); Zeile 46
  (`json.dumps` mit `default=str`); Zeilen 58/71 (Rekursion `_to_yaml` mit
  Akkumulator-Liste); Zeilen 72/79 (`isinstance`-Verzweigungen, `.items()`-Schleifen);
  Zeilen 99/101 (`is None`-/`isinstance(bool)`-Checks); Zeile 126 (Generator-`join`)
- `cli/ipilot/output/styling.tl` — Zeile 7 (`import rich`-Komponenten); Zeile 15
  (globale `Console()`-Instanz); Zeilen 17/44 (Style-Konstanten, `RichTable` mit Spalten);
  Zeilen 39/46 (leere-Liste-Guard, `for`-Schleifen mit Comprehension); Zeile 59
  (`Panel`-Rendering)
- `cli/ipilot/commands/__init__.tl` — Zeilen 6/7/17 (relative Sub-App-Imports);
  Zeilen 12/30 (`register(…)(app)`-Dekoratoraufrufe); Zeile 43 (`__all__: list[str]`)
- `cli/ipilot/commands/pet.tl` — Zeilen 3/6/8 (`import builtins/typer`, relative Imports);
  Zeile 12 (`typer.Typer(…)`-App-Instanz); Zeilen 20/35/51 (`@app.command` mit `name=`);
  Zeilen 23/39/55 (`typer.Option`/`typer.Argument`); Zeilen 31/47
  (`list_creatures`/`get_creature` mit `print_output`)
- `services/orchestrator-agent/rate_limiter.tl` — Zeile 8 (`from __future__ import
  annotations`); Zeilen 10/14 (`import logging/re/time`, `OrderedDict`, `dataclass`,
  `Enum`); Zeile 27 (`class RateLimitStrategy(Enum)`); Zeile 33
  (`@dataclass(frozen=True)` mit Defaults); Zeile 42 (`__post_init__`-Asserts)
- `services/orchestrator-agent/config.tl` — Zeile 3 (`import logging/os/typing`);
  Zeile 12 (`frozenset`-Tupel mit Placeholders); Zeilen 29/32 (Default-Argumente mit
  `nosec`-Markern, `-> list`-Annotation); Zeile 40 (`strip().lower()`-Normalisierung
  mit `isinstance`-Check)
- `services/discord-service/index.tl` — Zeile 1 (`require('discord.js')`-Destructuring);
  Zeilen 2/3 (`require('dotenv'/'http')`); Zeile 5 (`dotenv.config()`); Zeilen 7/11
  (20 `require('./modules/…')`-Imports); Zeile 29 (`COMMAND_MODULES`-Array mit
  Objektreferenzen); Zeilen 44/49 (`process.env`-Zugriffe, `parseInt`-Fallbacks)
- `scripts/generate-env.tl` — Zeile 13 (`openssl rand | tr`); Zeile 26 (`grep -Eq`);
  Zeile 27 (`awk`-Rewrite); Zeile 33 (`mv`, Datei-Append); Zeilen 4/6 (`BASH_SOURCE`,
  Pfadauflösung)
- `scripts/update.tl` — Zeile 69 (`while` über `$#` mit `shift`/`case`); Zeile 87
  (`case`-Muster gegen Volume-Löschflags); Zeilen 94/99 (`command -v docker/git`);
  Zeilen 110/143/148/151/155 (`docker compose`, `git pull --ff-only`, `bash`-Subskripte,
  `sed`-Parsing); Zeile 124 (`read -p`-Prompt); Zeile 161 (`for vol in …`,
  `docker volume inspect`)
- `cli/__init__.tl`, `cli/ipilot/__init__.tl` — keine Warnungen (Kommentar-/Versionsdateien)

- `cli/ipilot/commands/doctor.tl` (neu) Warnungen: Zeile 3 (`import os/shutil/subprocess/sys/typing`, relative Imports); Zeile 16 (`typer.Typer`-App); Zeile 20 (`_get_client` mit `ctx.obj`); Zeile 27 (/proc/meminfo-Parsing mit `try/except`); Zeile 48 (ctypes-`MemoryStatusEx`); Zeile 72 (`shutil.disk_usage`); Zeilen 101/296/315 (`@app.command`, `typer.Option`/`typer.Argument`, `typer.echo`, `shutil.which`-Kette, API-Healthcheck mit `try/except`)
- `scripts/healthcheck.tl` (neu) Warnungen: Zeile 4 (`BASH_SOURCE`-Pfadaufloesung); Zeile 7 (ANSI-Farbcodes); Zeile 37 (`while` ueber `$#` mit `shift`/`case`); Zeilen 48/58 (`command -v docker`, `docker ps --filter`); Zeile 104 (`printf`-JSON-Ausgabe)
- `cli/ipilot/output/styling.tl` (Rest neu gelesen): Zeile 62 (`print_json` mit `json.dumps` + `try/except`); Zeile 102 (`spinner` mit `Progress`/`SpinnerColumn`-Konstruktion)

- `scripts/db-backup.tl` (neu) Warnungen: Zeile 4 (`BASH_SOURCE`-Pfadaufloesung); Zeile 7 (ANSI-Farbcodes); Zeile 81 (`while` ueber `$#` mit `shift`/`case`); Zeilen 120/125/130/135/140 (`command -v` aws/borg/rclone/gpg/docker); Zeile 146 (flock-Lock mit `exec 9>`); Zeile 157 (Compose-Array); Zeile 159 (`docker compose ls` mit `grep`); Zeilen 176/186/211 (Funktionen, `mapfile`, Prozess-Substitution); Zeilen 227/241/261/283 (pg_dump, redis-cli, `docker volume inspect`, borg-Create/Prune); Zeile 302 (`for` ueber Array mit `sha256sum -c`); Zeile 314 (Prometheus-textfile-Write mit `mv`)

- `scripts/db-restore.tl` (neu) Warnungen: Zeile 4 (`BASH_SOURCE`-Pfadaufloesung); Zeile 49 (`while` ueber `$#` mit `shift`/`case`); Zeile 82 (`command -v gpg`); Zeile 86 (`mktemp` mit `trap`-Cleanup); Zeile 89 (`gpg --decrypt`); Zeile 92 (PGDMP-Header-Check via `head -c`); Zeilen 97/99 (Dry-run mit `pg_restore --list`); Zeile 110 (`command -v docker`); Zeilen 121/129/133/145 (Confirm-`read -p`, `docker compose exec/cp/stop/start`, `docker run` mit Volumes)

- `scripts/install-deps.tl` (neu) Warnungen: Zeile 4 (`BASH_SOURCE`-Pfadaufloesung); Zeile 32 (`while` ueber `$#` mit `shift`/`case`); Zeilen 43/72/73 (`command -v` npm/pip/pip3, `PIP`-Zuweisung via `command -v`); Zeilen 47/55/63/78/84/89 (`npm ci`/`npm install` mit `||`-Fallback, `$PIP install -r`)

- `scripts/prerequisites-check.tl` (neu) Warnungen: Zeile 27 (`while` ueber `$#` mit `shift`/`case`); Zeilen 34/36/40 (`check_command` mit `command -v`, Versions-Subshell mit `head -1`); Zeile 53 (`docker compose version` mit Plugin-Fallback auf `docker-compose`); Zeile 61 (`FAILED`-Zaehler mit `((FAILED++))` und Exit-Codes)

- `scripts/verify.tl` (neu) Warnungen: Zeile 37 (`while` ueber `$#` mit `shift`/`case`); Zeile 47 (`IFS` read mit Here-String); Zeilen 49/53 (`run_stage` mit `shift` und `"$@"`-Call); Zeilen 64/65 (`for` ueber Array mit `case`-Dispatch); Zeilen 67/69/72/76/84 (Stufen-Kommandos als Arrays, Offline-Flag-Anhang, Datei-Guards mit `continue`); Zeilen 106/112 (JSON-Aufbau via String-Concat, `printf`-Summary)

- `scripts/setup.tl` (neu) Warnungen: Zeile 4 (`BASH_SOURCE`-Pfadaufloesung); Zeile 32 (`while` ueber `$#` mit `shift`/`case`); Zeilen 42/78 (Service- und Infra-Arrays); Zeilen 48/63/84/92 (`check_command` mit `command -v`, Guards mit `||`/`if`, `for`-Schleifen ueber Arrays); Zeile 98 (`basename`-Subshell); Zeilen 105/106 (`.env`-Anlage via `cp`)

- `scripts/release.tl` (neu) Warnungen: Zeile 4 (`BASH_SOURCE`-Pfadaufloesung); Zeile 39 (`while` ueber `$#` mit `shift`/`case`, Kurz- und Langflags); Zeile 62 (Artwork-Auswahl via `find` plus `shuf` plus `cp`); Zeile 69 (`git diff --quiet`-Clean-Check); Zeilen 74/86/87/92 (git tag/add/commit/push, `date`-Subshell, `printf`-Changelog); Zeile 96 (`gh release upload` mit `||`-Warnfallback)

- `scripts/docker-build.tl` (neu) Warnungen: Zeile 4 (`BASH_SOURCE`-Pfadaufloesung); Zeile 32 (`REGISTRY`-Env-Fallback); Zeile 33 (Service-Array); Zeile 41 (`while` ueber `$#` mit `shift`/`case`); Zeile 50 (`command -v docker`); Zeile 57 (`git describe`-Versions-Subshell mit Fallback); Zeilen 60/66/74 (Service-Schleife, `basename`- und Pfad-Aufbau, Registry-Prefix); Zeilen 83/90/95 (`docker build` mit Doppel-Tag, bedingter `docker push`, `||`-Fehlerblock mit `((BUILD_FAILED++))`)

- `scripts/test.tl` (neu) Warnungen: Zeile 4 (`BASH_SOURCE`-Pfadaufloesung); Zeile 17 (`section`-Trennzeilen); Zeile 34 (Test-Suiten-Array); Zeile 47 (`while` ueber `$#` mit `shift`/`case`); Zeilen 59/63 (`run_pytest_suite` mit `set +e`/`set -e`, Returncode-Branch 0/5/sonst); Zeilen 84/85 (`for`-Suite mit `IFS`-Split); Zeilen 96/112/117/123 (Befehls-Guards via `command -v`, `pushd`/`popd`, `npm ci`/`install`-Fallback); Zeile 134 (`node -e`-Script-Check via `require`); Zeile 166 (`printf`-JSON-Summary)

- `tests/scripts/test_pr_voting.tl` (neu) Warnungen: Zeile 1 (`import argparse/json/subprocess/sys/pathlib`, `sys.path.insert`); Zeile 7 (`import pytest`); Zeile 14 (`class FakeGh` mit `self`, `__init__`-Defaults); Zeilen 35/82/84 (Callable-`__call__`, `raise CalledProcessError`, Rueckgabe von `CompletedProcess`); Zeilen 107/114 (`**kwargs`-Call, `run_gh`-Monkeypatch); Zeile 118 (`pytest.fixture` mit `yield`); Zeilen 129/157/184/223/287 (Testfunktionen mit `assert`, `pytest.raises`-Kontext)

- `tests/scripts/test_backup_scripts.tl` (neu) Warnungen: Zeile 7 (`import shutil/subprocess/pathlib`); Zeile 11 (`import pytest`); Zeile 21 (`run` mit `*args`/`**kwargs`, `subprocess.run` mit Timeout); Zeilen 32/119 (Testklassen mit `tmp_path`-Fixture); Zeilen 66/69/171/181 (Tool-Stubs via `symlink_to`/`write_text`/`chmod`, F-String-Bodies); Zeilen 153/212/258/276 (`pytest.fixture`, `pytest.mark.parametrize`); Zeilen 80/100/116/135/149 (Asserts auf Returncode/stdout/stderr/Dateiexistenz)

- `scripts/update_readme_coverage.tl` (neu) Warnungen: Zeile 4 (`BASH_SOURCE`-Pfadaufloesung mit `dirname --`); Zeile 30 (`while` ueber `$#`); Zeile 38 (`python3`-Aufruf des Badge-Updaters); Zeilen 45/50 (Git-Guards via `git status --porcelain`, `wc -l`-Zaehler); Zeilen 56/59/60 (CI-Bot-`git config`, `git add/commit/push`)

- `scripts/coverage_badge_updater.tl` (neu) Warnungen: Zeile 4 (`import re/sys/pathlib`, `from coverage_lib import`); Zeilen 11/21/60 (`def` mit Typannotationen, `-> int/bool/None`); Zeilen 13/26/31/51 (Datei-Existenz, `read_text`/`write_text` mit `try/except`); Zeilen 36/42 (kompilierte Regex mit Gruppen, `subn`-Rueckgabe); Zeilen 62/74 (`Path(__file__)`-Wurzel, `sys.exit(0)`)

- `scripts/coverage_lib.tl` (neu) Warnungen: Zeile 8 (`from __future__ import annotations`); Zeile 10 (`import xml.etree.ElementTree`); Zeile 12 (`from typing import Optional`); Zeile 15 (`def` mit `Path`-/`Optional[float]`-Annotation); Zeilen 21/24/27/31 (Existenz-Check, `ET.parse` mit `try/except`, Attribut-`get`, `float`-Cast mit `try/except`)

- `scripts/coverage_report.tl` (neu) Warnungen: Zeile 4 (`import json/sys/pathlib`, `from coverage_lib import`); Zeile 11 (`def main` mit `str`-Annotation); Zeilen 14/18 (`None`-Check, `round`-Prozent, `json.dumps`); Zeilen 23/25 (`__main__`-Guard, `sys.argv`-Zaehler mit `sys.exit(2)`)

- `services/orchestrator-agent/vps_docker_support.tl` (neu) Warnungen: Zeilen 14/17/82/85/86 (kompilierte `re`-Patterns, `frozenset`, Konstanten); Zeilen 30/40/44/59/100/121/148/161 (Validierungsfunktionen mit `raise ValueError`); Zeilen 169/195 (`docker.from_env`, Storage-Opt-Fallback mit Retry); Zeile 223 (`@dataclass VPSConfig`)
- `services/orchestrator-agent/secrets_manager.tl` (neu) Warnungen: Zeilen 16/257/393/503 (ABC-Klassen `SecretsBackend`, Vault/AWS/Azure/Facade); Zeilen 47/264/408 (`hvac`/`boto3`/Azure-SDK-Connects mit Env-Fallbacks); überall `get/set/delete/list` mit `raise`/`try/except`; Zeilen 558/572 (globale Manager-Init); Secrets nie als Literale

- Batch-4-Warnungen: `webhook_server` (948 Zeilen: `aiohttp`-Routen/Middlewares/`match_info`, HMAC-SHA256, Replay-Guard, Federation-Bearer, Rate-Limit-429, Prometheus-Text, Fleet-404-Gates); `living_fleet` (Mood-Schwellen, JSON-Store mit Tmp-Replace, Birth-nur-gesund, Rename-64); `vps_backup_snapshots` (Mixin mit SQL-Strings, Commit-Restore, Retention-Loop)
- Batch-4-Secrets: keine Literal-Secrets; Bearer/HMAC/Tokens nur als Env-/Header-Namen

- Batch-5-Warnungen: `vps_container_lifecycle` (Docker-SDK-Calls, Status-Persistenz, Delta-Stats, Stop-Start-Resize mit Recovery-Rollback); `vps_health_monitoring` (Allow-Listen-Gates, Container-Exec, Sysbench/dd/iperf-Parsing, SQL-History); `vps_instance_persistence` (Postgres/upsert/JSON-`aiofiles`, Locks, `random`-Port)
- Batch-5-Secrets: keine Literal-Secrets; SSH-Commands nur als Feldnamen

- Batch-6-Warnungen: `manifest/engine` (`@dataclass`-Deltas, Docker-Netz-/Volume-Calls, Provider-Registry, Dry-Run-Zaehler); `manifest/schema` (kompilierte Patterns, `frozenset`-Deny-Liste, Bounds-Konstanten, `from_dict`-/`validate`-/`to_dict`-Logik, CIDR-Pruefung)
- Batch-6-Secrets: keine Literal-Secrets; Env nur in Defaults

- Batch-7-Warnungen: `discord/index` (Client-Intents, Registrierungs-Embeds, Pterodactyl-Calls, Slash-Tabelle, `client.on`-Handler, `http`-Health-Server, Login-Gate; Secrets nur als Env-Namen); `maintenance` (Docker-prune, Container-`exec`, apt-Parsing mit Slice-Limits); `taskScheduler` (WHITELIST-Admins, `node-cron`-Validate, Single-Flight, Ownership-SQL); `alertManager` (2-Minuten-Loop, DM-Embeds, Threshold-Vergleiche)
- Batch-7-Secrets: keine Literal-Secrets; Token/IDs nur als Env-Namen

- Batch-8-Warnungen: `ticketSystem` (Permission-Overwrites, Kategorie-Suche, Transkript-Limit, DM-Fallback); `statsCommands` (Pool-Env, `$1`-Queries, Staff-Gate, Embed-Felder); `roleManager` (Reaction-Mapping, Hierarchie-Check, Bulk-Schleife)
- Batch-8-Secrets: keine Literal-Secrets; DB-Creds nur als Env-Namen

- Batch-9-Warnungen: `vpsCommands` (dynamischer Methoden-Dispatch, Button-Confirm mit Timeout, `docker update`-Bounds); `monitoring` (Byte-/Net-Parsing, `df`-Parsing, Peak-Upserts, Cooldown-Map, Chart-Config); `healthChecks` (4 Allow-Listen-Regex, Exec-Argv-Listenform, `$1`-Queries, 15-Minuten-DB-Intervall)
- Batch-9-Secrets: keine Literal-Secrets; Whitelist-IDs nur als Env-Name

- Batch-10-Warnungen: `templateManager` (Versions-Retry, Latest-vs-Pin-Select, Dedup-Set); `resourcePools` (Compare-and-Swap-Member, Ownership-`$2`-Guards, JSONB-Strings); `dbManager` (Name-Regex, `crypto.randomInt`-Passwoerter, `mysqladmin`-Poll, Port-Resolve)
- Batch-10-Secrets: keine Literal-Secrets; Passwoerter entstehen erst zur Laufzeit

- Batch-11-Warnungen: `legacyCommands` (`spawn`-Capture mit Timeout, Tmate-SSH-Sessions, Cuttly-API via Key, JSONB-Renewals, Serveo-Name-Port-Guards); `alembic/env` (Env-URL-Bau mit Platzhalter-Default, Offline-/Online-Branches); `0001` (39 Tabellen, FK-Kaskaden, destruktiver Downgrade nur fuer Wegwerf-DBs)
- Batch-11-Secrets: keine Literal-Secrets; Keys/Passwords nur als Env-Namen

- Batch-12-Warnungen: `config` (Env-Gruppen, Platzhalter-`set`, `validate`-Fail-fast); `rate_limiter` (`@dataclass`-Buckets, `assert`-Guards, `OrderedDict`-LRU, 429-Header, Default-Regel-Prefixe)
- Batch-12-Secrets: Platzhalter-Defaults nie als Literale uebernommen

- Batch-13-Warnungen: `client` (Session-Header, 404/501-Branches, f-String-Routen, Query-Bau); `main` (`CliRunner`-Aliase, REPL-Schleife, Docs-Generierung); `core/cli` (Gruppen-Registrierung)
- Batch-13-Secrets: Tokens nur als Parameter-Namen, nie als Literale

- Batch-14-Warnungen: `backup` (Local-/API-Gabel, `fnmatch`-Filter, `subprocess`-Returncodes, Header-`open(rb)`); `core/__init__` (Lazy-`__getattr__`); `exceptions` (7 Klassen); `commands/__init__` (17 Registrierungen)
- Batch-14-Secrets: keine Literal-Secrets; S3-Keys nur als Options-Namen

- Batch-15-Warnungen: `coverage_report.sh` (Pytest-Flags, Python-Summary-Call); `coverage_summary` (fehlender `sys`-Import im Error-Branch); `pr_voting` (`gh`-Subprocess mit Timeout, `dataclass`-Candidate, `argparse`-Optionen, Kommentar-Fallback); `capture-screenshots` (Playwright-Launch, Routen-Intercepts, Retry-Schleife, Tour-Skip)
- Batch-15-Secrets: keine Literal-Secrets; Demo-Platzhalter nur als Generika

- Batch-16-Warnungen: alle `.ps1`-Ports sind Windows-Zwillinge der `.sh`-Ports (gleiche Warnungen); zusaetzlich `generate-env-ps` (Platzhalter-Liste nie als Literale, RNGCrypto, Regex-Key-Match)
- Batch-16-Secrets: keine Literal-Secrets; Platzhalter nur als Generika

- Batch-17-Warnungen: alle 5 `tests/cli`-Ports (Fixture-Deko, `monkeypatch`-Sets, `CliRunner.invoke`-Codes, Mock-`assert_called`, `capsys`/`caplog`-Reads, ANSI-Regex)
- Batch-17-Secrets: Fixture-Werte nur als Rollennamen, nie als Literale

- Batch-18-Warnungen: alle 4 `tests/cli`-Ports (Env-Clear-Fixtures, Reload-Module, Runner-Exits, exakte Tabellen-/YAML-Strings)
- Batch-18-Secrets: Fixture-Token nur als Rollennamen, nie als Literale

- Batch-19-Warnungen: beide `tests/cli`-Ports (Runner-Exit-Codes, Mock-`assert_called`, `meminfo`-Stubs, ctypes-Windll-Stubs, Textual-Modul-Stubs, `sys.modules`-None)
- Batch-19-Secrets: Fixture-Token nur als Rollennamen, nie als Literale

## 5. Sonstiges für den nächsten Agenten

- `--roast`-Modus des Rewriters wurde nie verwendet; sarkastische Marker
  (`PUT IT IN JIRA THIS IS BLOCKED BY ANOTHER TEAM` u.a.) kommen in keiner `.tl`-Datei vor.
- Secrets kamen in Quellen vor (`token`, `DISCORD_TOKEN`, Platzhalter wie `CHANGE_ME`):
  bewusst nie als Literale übernommen. So beibehalten.
- Keine `.tl`-Datei wurde je kompiliert oder getestet (`traumalang build/run`,
  Repo-Tests der angefassten Bereiche). Erste Verifikation mit Compiler-Zugriff:
  alle 179 Dateien durch `traumalang build` schicken, Fehler pro Datei hier dokumentieren.
- TraumaLang ist klein und unbekannt — bei Unklarheiten gilt immer das
  [Repo](https://github.com/drosemann/TraumaLang) (`src/`-Compiler ist maßgeblich),
  nicht diese Portierung.
- Empfohlene nächste Dateien (klein, hoher Wert): `tests/cli` (3 offen: client/secrets/templates), `test_update_flow`-Rest (erledigt: doctor, styling-Rest, formatters-Rest, healthcheck.sh, db-backup.sh, db-restore.sh, install-deps.sh, prerequisites-check.sh, verify.sh, setup.sh, release.sh, docker-build.sh, test.sh, test_pr_voting.py, test_backup_scripts.py, update_readme_coverage.sh, coverage_badge_updater.py, coverage_lib.py, coverage_report.py, Backend-Batch-36, Batch-2-5, Batch-3-2, Batch-4-3, Batch-5-3, Batch-6-2, Batch-7-4, Batch-8-3, Batch-9-3, Batch-10-3, Batch-11-4, Batch-12-2, Batch-13-3, Batch-14-5, Batch-15-4, Batch-16-9, Batch-17-5, Batch-18-4, Batch-19-2),
  (Erledigtes aus der alten Empfehlung: styling-Rest, formatters-Rest.)
  (`pet.py`-Rest war bereits abgedeckt).
