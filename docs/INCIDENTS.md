# Incidents & On-Call

Duty-routed incident workflow with escalation chain and blameless
postmortem drafts. Implements the Ideen-Buendel #69 (Incident-Workflow),
#17 (Dienst-Zustaendigkeit statt Sternzeichen), #75 (Eskalationskette)
und #81 (sachlicher Postmortem-Entwurf) aus
[IDEEN-UND-TO-DOS.md](../IDEEN-UND-TO-DOS.md).

## Konzept in einem Satz

Ein Incident bekommt automatisch den diensthabenden Owner aus dem
Bereitschaftsplan, jede Aenderung landet in einer auditierbaren Timeline,
ueberfaellige Uebergaben werden eskaliert — und der Abschlussbericht
bleibt ausdruecklich ein Entwurf, bis ein Mensch ihn freigibt.

## Konfiguration (Orchestrator)

| Variable | Beispiel | Wirkung |
| --- | --- | --- |
| `INCIDENTS_STORE` | `./incidents.json` | JSON-Ablage (atomar ersetzt, wie Living Fleet). |
| `INCIDENTS_ESCALATION` | `alice\|bob;carol` | Stufen mit `;` trennen, Mitglieder mit `\|`. Stufe 0 liefert den Duty-Owner. |
| `INCIDENTS_ESCALATE_AFTER_S` | `1800` | Frist, nach der `escalation_due` true wird. Minimum 60. |
| `INCIDENTS_QUIET_HOURS` | `22:00-06:00` | Ruhezeit; Eskalation wird dann nur protokolliert (`deferred`), ausser mit `force`. |

Ohne `INCIDENTS_ESCALATION` gibt es keinen Duty-Owner und keine
Eskalationsstufen — Incidents funktionieren trotzdem (Timeline, Status,
Postmortem), nur ohne automatische Uebergabe.

## Ablauf

1. `POST /api/v1/incidents` — anlegen (`service`, `severity`,
   `title`, optional `runbook`, `reporter`). Status `open`, Owner = Stufe 0.
2. `POST .../notes` — Status-Updates in die Timeline schreiben.
3. `POST .../status` — `acknowledged` (Mensch kuemmert sich) oder
   `resolved` (braucht eine Abschlussnotiz, sonst 400).
4. `POST .../escalate` — naechste Stufe uebernimmt. In Ruhezeiten nur
   `deferred`, ausser `force: true`. Auf hoechster Stufe No-Op.
5. `GET .../postmortem` — Entwurf aus Timeline-Fakten erzeugen,
   reviewen, freigeben. Niemals automatisch final.

`GET /api/v1/incidents` listet kompakt (neueste zuerst, `escalation_due`
markiert ueberfaellige), mit `?status=`- und `?service=`-Filtern.
`GET /api/v1/incidents/{id}` liefert den vollen Incident mit Timeline.
`POST .../assign` weist manuell zu (wird auditiert).

Alle Routen hängen hinter dem Federation-Token-Middleware wie alle
`/api/`-Routen des Orchestrators; Vertrag in
`services/orchestrator-agent/api_docs/openapi.yaml`.
Der OpenAPI-Contract-Test prueft Routen und Spec in beide Richtungen.

## CLI

```bash
ipilot incident create payments "checkout 500s" --severity critical
ipilot incident list --status open
ipilot incident show inc-abc123
ipilot incident note inc-abc123 "rollback vorbereitet" --actor alice
ipilot incident ack inc-abc123 --actor alice
ipilot incident escalate inc-abc123 --actor alice
ipilot incident resolve inc-abc123 --note "hotfix deployed, error rate normal" --actor alice
ipilot incident postmortem inc-abc123
```

Die Incident-Befehle sprechen dieselben `/v1/`-Pfade wie `ipilot pet`
(Living Fleet) ueber den konfigurierten API-Endpunkt.

## Grenzen (ehrlich)

- Kein ChatOps-Versand: Es gibt keine Discord-/Pager-Anbindung;
  Eskalation heisst Besitzerwechsel plus Timeline-Eintrag, kein Page.
- Kein SLO-Engine: `escalation_due` nutzt nur die Aktualitaetsfrist,
  keine Error-Budget-Berechnung (Ideen #22/#99 bleiben offen).
- Datei-Store, kein Multi-Reader-Lock: ausreichend fuer den
  Orchestrator-Betrieb, kein Ersatz fuer eine Incident-Datenbank.
