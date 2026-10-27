# TraumaLang-Port — Lücken, offene Arbeiten, Anleitung

Stand: 21 `.tl`-Dateien. Sprache: [TraumaLang v2.2](https://github.com/drosemann/TraumaLang)
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
  (`_dict_table`, `_key_value_table`, `print_output` u.a.) **nicht gelesen, nicht portiert**.
- `cli/ipilot/output/styling.tl` ← nur Zeilen 1–60 gelesen. Rest ab Zeile 60
  (`print_error/info/json/success`, `spinner` u.a.) **nicht gelesen, nicht portiert**.
- `cli/ipilot/commands/__init__.tl` ← nur Zeilen 1–50 gelesen. `__all__`-Rest
  **nicht gelesen, nicht portiert**.
- `cli/ipilot/commands/pet.tl` ← nur Zeilen 1–60 gelesen. `rename`-Rest ab Zeile 60
  **nicht gelesen, nicht portiert**.
- `services/orchestrator-agent/rate_limiter.tl` ← nur Zeilen 1–50 gelesen. Kernlogik
  (Ringpuffer, Token-Bucket/Sliding-Window-Entscheidung, Zeitgrenzen) **nicht gelesen,
  nicht portiert**.
- `services/orchestrator-agent/config.tl` ← nur Zeilen 1–50 gelesen. `checks`-Liste,
  Produktions-Branch (`raise` vs. Warnung + Rückgabe) **nicht gelesen, nicht portiert**.
- `services/discord-service/index.tl` ← nur Zeilen 1–50 gelesen. Bot-Login,
  Event-Handler, Command-Dispatch (Rest der Datei) **nicht gelesen, nicht portiert**.
- `scripts/generate-env.tl` ← voll gelesen. `gen_secret`-/`fill`-Logik (openssl, grep, awk,
  mv) nur als Strings; kein ausführbarer Ersatz.
- `scripts/update.tl` ← voll gelesen (177 Zeilen). 4-Schritte-Ablauf (Preflight, Backup,
  `git pull --ff-only`, `compose up -d --build`, Healthcheck + Volume-Verify) nur als
  `TALK TO THE HAND`-Kette; Flags/Guards nur als Strings.

## 2. Noch gar nicht übersetzte Quelldateien

### 2a. `cli/ipilot/commands/`-Submodule (alle offen außer `pet.py`-Kopf)

- `commands/infrastructure/__init__.py`, `commands/infrastructure/server.py`,
  `commands/infrastructure/backup.py`, `commands/infrastructure/deployment.py`,
  `commands/infrastructure/logs.py`
- `commands/apikeys/__init__.py`, `commands/doctor/__init__.py`,
  `commands/gitops/__init__.py`, `commands/inventory/__init__.py`,
  `commands/plugins/__init__.py`, `commands/rollback/__init__.py`,
  `commands/secrets/__init__.py`, `commands/ssh/__init__.py`,
  `commands/templates/__init__.py`, `commands/tui/__init__.py`,
  `commands/webhooks/__init__.py`
- Hinweis: Registrierungsnamen stehen in `commands/__init__.tl`
  (server, backup, deploy, logs, gitops, ssh, inventory, secrets, plugins, doctor,
  webhooks, apikeys, templates, tui, rollback, pet) — die Module dahinter fehlen alle.

### 2b. `cli/ipilot/`-Reste

- `client.py` ab Zeile 51 (alle Endpoint-Methoden, Fehlerklassen `APIError`,
  `AuthenticationError`, `ConnectionError` aus `core/exceptions.py`)
- `main.py` ab Zeile 121 (`benchmark`-Command und alles danach)
- `core/cli.py` ab Zeile 61 (`get_client`-Rest)
- `core/__init__.py` ab Zeile 31 (`__all__`-Rest)
- `output/__init__.py` ab Zeile 31 (`__all__`-Rest)
- `output/formatters.py` ab Zeile 141 (`_dict_table`, `_key_value_table`, `print_output`)
- `output/styling.py` ab Zeile 61 (`print_error`, `print_info`, `print_json`,
  `print_success`, `spinner`)
- `commands/__init__.py` ab Zeile 51 (`__all__`-Rest)
- `commands/pet.py` ab Zeile 61 (`rename`-Rest)

### 2c. `scripts/`-Reste (alle offen außer `generate-env.sh`, `update.sh`)

- `db-backup.sh`, `db-restore.sh`, `healthcheck.sh`, `install-deps.sh`,
  `prerequisites-check.sh`, `release.sh`, `setup.sh`, `test.sh` (Kopf Zeilen 1–40 gelesen,
  Rest ungelesen), `verify.sh`, `update_readme_coverage.sh`, `capture-screenshots.mjs`,
  `coverage_badge_updater.py`, `coverage_lib.py`, `coverage_report.py`, `coverage_report.sh`,
  `coverage_summary.py`, `pr_voting.py`
- jeweils auch die `.ps1`-Zwillinge, wo vorhanden (`docker-build`, `generate-env`,
  `healthcheck`, `install-deps`, `prerequisites-check`, `release`, `setup`, `test`, `verify`)
- `docker-build.sh` (kein `.tl`-Zwilling)

### 2d. `services/orchestrator-agent/`-Reste (alle offen außer Köpfen von `config.py`, `rate_limiter.py`)

- `main.py`, `webhook_server.py`, `db.py`, `config.py` (ab Zeile 51), `rate_limiter.py`
  (ab Zeile 51), `rbac_store.py`, `secrets_manager.py`, `integration.py`, `discord_auth.py`,
  `fleet_collect.py`, `living_fleet.py`, `resource_monitor.py`, `vps_manager.py`,
  `vps_backup_snapshots.py`, `vps_container_lifecycle.py`, `vps_docker_support.py`,
  `vps_health_monitoring.py`, `vps_instance_persistence.py`
- Hersteller-Logik (DB, RBAC, Secrets, Webhooks) enthält Security-Sensibles:
  Secrets **niemals** als Literale in `.tl` übernehmen (vgl. Warnung zu `config.py` Zeile 29
  und `orchestrator-agent/config.py`-Platzhaltern).

### 2e. `services/discord-service/`-Reste (alle offen außer `index.js`-Kopf)

- `index.js` ab Zeile 51, `cli-bridge.js`, `integration.js`, alle Dateien unter `modules/`
  (`pterodactyl`, `validation`, `serverLimits`, `serverStatus`, `ticketSystem`,
  `ticketCommands`, `statsCommands`, `roleManager`, `vpsCommands`, `monitoring`,
  `healthChecks`, `backupScheduler`, `alertManager`, `taskScheduler`, `maintenance`,
  `templateManager`, `resourcePools`, `dbManager`, `legacyCommands`, `petCommands`)
- JS ist Rewriter-Sprache (`--from javascript`); `async function` mappt zusätzlich auf
  `I WAS DOUBLE-BOOKED ON 2 OFFSITES` — bisher ungenutzt, steht für den nächsten Agenten bereit.

### 2f. `services/management-panel/` (komplett offen)

- TypeScript/React/Express-App (`server/index.ts`, `src/`, `src/components/`,
  `src/pages/`). Rewriter-Sprache wäre `--from typescript`. Bisher keine einzige
  `.tl`-Datei; wegen Größe dateiweise vorgehen, mit kleinen Modulen beginnen.
- OpenAPI-Vertrag (`/api/openapi.json`) und `api_docs/openapi.yaml` des Orchestrators
  sind als Kontraktquellen zu lesen, aber keine `.tl`-Ziele.

### 2g. `tests/`-Reste (alle offen außer `conftest.py`, `test_update_flow.py`-Kopf)

- `tests/cli/`: `test_client.py`, `test_command_registry.py`, `test_config.py`,
  `test_config_profiles.py`, `test_core_cli.py`, `test_doctor_tui.py`,
  `test_gitops_commands.py`, `test_inventory_commands.py`, `test_main.py`,
  `test_main_extra.py`, `test_output.py`,
  `test_secrets_ssh_plugins_webhooks_apikeys.py`, `test_styling.py`,
  `test_templates_rollback_infra_gitops.py`
- `tests/scripts/`: `test_backup_scripts.py`, `test_pr_voting.py`,
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

## 4. Warnungsindex (alle `Zeile N`-Warnungen der 21 `.tl`-Dateien)

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

## 5. Sonstiges für den nächsten Agenten

- `--roast`-Modus des Rewriters wurde nie verwendet; sarkastische Marker
  (`PUT IT IN JIRA THIS IS BLOCKED BY ANOTHER TEAM` u.a.) kommen in keiner `.tl`-Datei vor.
- Secrets kamen in Quellen vor (`token`, `DISCORD_TOKEN`, Platzhalter wie `CHANGE_ME`):
  bewusst nie als Literale übernommen. So beibehalten.
- Keine `.tl`-Datei wurde je kompiliert oder getestet (`traumalang build/run`,
  Repo-Tests der angefassten Bereiche). Erste Verifikation mit Compiler-Zugriff:
  alle 21 Dateien durch `traumalang build` schicken, Fehler pro Datei hier dokumentieren.
- TraumaLang ist klein und unbekannt — bei Unklarheiten gilt immer das
  [Repo](https://github.com/drosemann/TraumaLang) (`src/`-Compiler ist maßgeblich),
  nicht diese Portierung.
- Empfohlene nächste Dateien (klein, hoher Wert): `commands/doctor/__init__.py`,
  `output/styling.py`-Rest (ab Zeile 61), `output/formatters.py`-Rest (ab Zeile 141),
  `commands/pet.py`-Rest (ab Zeile 61), `test_pr_voting.py`, `healthcheck.sh`.
