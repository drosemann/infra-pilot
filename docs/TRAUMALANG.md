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

## Übersetzte Dateien (21)

| Quelle | `.tl`-Datei | Abdeckung |
| --- | --- | --- |
| `tests/conftest.py` | `tests/conftest.tl` | vollständig gelesen |
| `tests/scripts/test_update_flow.py` | `tests/scripts/test_update_flow.tl` | Zeilen 1–50 gelesen |
| `cli/__init__.py` | `cli/__init__.tl` | vollständig |
| `cli/ipilot/__init__.py` | `cli/ipilot/__init__.tl` | vollständig |
| `cli/ipilot/config.py` (186 Zeilen) | `cli/ipilot/config.tl` | vollständig gelesen |
| `cli/ipilot/main.py` | `cli/ipilot/main.tl` | Zeilen 1–120 gelesen |
| `cli/ipilot/client.py` | `cli/ipilot/client.tl` | Zeilen 1–50 gelesen |
| `cli/ipilot/core/exceptions.py` (45 Zeilen) | `cli/ipilot/core/exceptions.tl` | vollständig gelesen |
| `cli/ipilot/core/__init__.py` | `cli/ipilot/core/__init__.tl` | Zeilen 1–30 gelesen |
| `cli/ipilot/core/command_registry.py` (89 Zeilen) | `cli/ipilot/core/command_registry.tl` | vollständig gelesen |
| `cli/ipilot/core/cli.py` | `cli/ipilot/core/cli.tl` | Zeilen 1–60 gelesen |
| `cli/ipilot/output/__init__.py` | `cli/ipilot/output/__init__.tl` | Zeilen 1–30 gelesen |
| `cli/ipilot/output/formatters.py` | `cli/ipilot/output/formatters.tl` | Zeilen 1–140 gelesen |
| `cli/ipilot/output/styling.py` | `cli/ipilot/output/styling.tl` | Zeilen 1–60 gelesen |
| `cli/ipilot/commands/__init__.py` | `cli/ipilot/commands/__init__.tl` | Zeilen 1–50 gelesen |
| `cli/ipilot/commands/pet.py` | `cli/ipilot/commands/pet.tl` | Zeilen 1–60 gelesen |
| `services/orchestrator-agent/rate_limiter.py` | `services/orchestrator-agent/rate_limiter.tl` | Zeilen 1–50 gelesen |
| `services/orchestrator-agent/config.py` | `services/orchestrator-agent/config.tl` | Zeilen 1–50 gelesen |
| `services/discord-service/index.js` | `services/discord-service/index.tl` | Zeilen 1–50 gelesen |
| `scripts/generate-env.sh` | `scripts/generate-env.tl` | vollständig gelesen |
| `scripts/update.sh` (177 Zeilen) | `scripts/update.tl` | vollständig gelesen |

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
