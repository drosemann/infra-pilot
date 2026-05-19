# 10 Good First Issues für `infra-pilot`

Diese Vorschläge sind so formuliert, dass du sie direkt als GitHub Issues copy-pasten kannst.

---

## 1) README um „Quickstart in 5 Minuten“ erweitern

**Titel:** docs: add 5-minute quickstart section to README

**Beschreibung:**
Aktuell fehlt ein ultra-kurzer Einstieg für neue Contributor. Ergänze im `README.md` einen Abschnitt „Quickstart in 5 Minuten“ mit den minimalen Schritten zum lokalen Start.

**Aufgaben:**
- Voraussetzungen auflisten (z. B. Docker/Node/Python je nach Projekt)
- Installations- und Start-Befehle ergänzen
- Kurzen „Was sollte ich jetzt sehen?“-Check hinzufügen

**Akzeptanzkriterien:**
- README enthält den neuen Abschnitt
- Schritte sind auf einem frischen Setup nachvollziehbar
- Ein neuer Nutzer kann das Projekt ohne Rückfragen starten

---

## 2) CONTRIBUTING.md erstellen

**Titel:** docs: add CONTRIBUTING guide for first-time contributors

**Beschreibung:**
Es fehlt ein klarer Leitfaden für Pull Requests. Erstelle eine `CONTRIBUTING.md` mit Branch-Namenskonventionen, Commit-Style, Test-Anforderungen und PR-Checklist.

**Aufgaben:**
- Datei `CONTRIBUTING.md` anlegen
- Standard-Workflow dokumentieren (Fork/Branch/PR)
- PR-Checklist hinzufügen

**Akzeptanzkriterien:**
- `CONTRIBUTING.md` ist im Repo vorhanden
- README verlinkt auf `CONTRIBUTING.md`
- Mindestens 1 Beispiel für guten PR-Titel enthalten

---

## 3) EditorConfig hinzufügen

**Titel:** chore: add .editorconfig for consistent formatting

**Beschreibung:**
Um unnötige Format-Diffs zu vermeiden, soll eine `.editorconfig` mit Basisregeln ergänzt werden.

**Aufgaben:**
- `.editorconfig` im Repo-Root erstellen
- Regeln für Einrückung, Zeilenenden, Final Newline definieren
- Falls sinnvoll, Overrides für relevante Dateitypen ergänzen

**Akzeptanzkriterien:**
- `.editorconfig` vorhanden
- Regeln sind dokumentiert (kurzer Kommentar oder Doku-Hinweis)
- Keine bestehenden Dateien werden funktional verändert

---

## 4) GitHub Issue Templates anlegen

**Titel:** meta: add issue templates for bug report and feature request

**Beschreibung:**
Für bessere Struktur bei neuen Issues sollen Standard-Templates ergänzt werden.

**Aufgaben:**
- `.github/ISSUE_TEMPLATE/bug_report.md` erstellen
- `.github/ISSUE_TEMPLATE/feature_request.md` erstellen
- Pflichtfelder für Repro/Expected/Actual bzw. Use Case/Proposal ergänzen

**Akzeptanzkriterien:**
- Beide Templates sind auswählbar beim Erstellen eines Issues
- Felder sind klar und kurz gehalten
- Templates enthalten aussagekräftige Beispieltexte

---

## 5) Pull Request Template hinzufügen

**Titel:** meta: add pull request template

**Beschreibung:**
Ein PR-Template soll sicherstellen, dass Kontext, Tests und Risiken immer dokumentiert sind.

**Aufgaben:**
- `.github/pull_request_template.md` erstellen
- Sektionen für „Was wurde geändert?“, „Wie getestet?“, „Risiken/Rollback“ hinzufügen
- Checkboxen für Selbstreview ergänzen

**Akzeptanzkriterien:**
- PR-Template wird bei neuen PRs automatisch vorgeschlagen
- Enthält mindestens 1 Checkliste für Tests
- Ist kurz genug für den Alltag (max. ~40 Zeilen)

---

## 6) CI Badge im README ergänzen

**Titel:** docs: add CI status badge to README

**Beschreibung:**
Der Build-Status soll direkt im README sichtbar sein.

**Aufgaben:**
- Richtigen Badge-Link für den Haupt-Workflow ermitteln
- Badge im oberen README-Bereich ergänzen
- Verifizieren, dass der Link korrekt zur Workflow-Seite führt

**Akzeptanzkriterien:**
- Badge wird im README korrekt angezeigt
- Klick auf Badge führt zum passenden GitHub Actions Workflow
- Keine toten Links im README

---

## 7) „Good First Issue“-Labeling dokumentieren

**Titel:** docs: define triage rules for good-first-issue labels

**Beschreibung:**
Damit neue Mitwirkende passende Aufgaben finden, sollen klare Kriterien für `good first issue` dokumentiert werden.

**Aufgaben:**
- Kriterien in `CONTRIBUTING.md` oder `docs/triage.md` ergänzen
- Beispiele für geeignete/nicht geeignete Issues angeben
- Optional: Vorschlag für weitere Labels (`help wanted`, `needs repro`)

**Akzeptanzkriterien:**
- Dokumentierte, nachvollziehbare Label-Regeln vorhanden
- Mindestens 3 konkrete Kriterien definiert
- Maintainer können Regeln direkt anwenden

---

## 8) Healthcheck-Skript für lokale Umgebung

**Titel:** tooling: add local environment healthcheck script

**Beschreibung:**
Ein kleines Skript soll prüfen, ob notwendige Tools lokal installiert sind und die wichtigsten Befehle funktionieren.

**Aufgaben:**
- Skript in `scripts/healthcheck.(sh|py)` anlegen
- Checks für Kern-Dependencies und Versionen einbauen
- Kurze Ausgabe mit ✅/❌ erzeugen

**Akzeptanzkriterien:**
- Skript läuft lokal ohne zusätzliche Abhängigkeiten
- Liefert bei fehlenden Tools verständliche Hinweise
- README enthält Aufrufbeispiel

---

## 9) Beispiel-Konfigurationsdatei ergänzen

**Titel:** docs: add/update .env.example with required variables

**Beschreibung:**
Neue Entwickler wissen oft nicht, welche Umgebungsvariablen nötig sind. Ergänze eine vollständige `.env.example`.

**Aufgaben:**
- Alle benötigten Variablen sammeln
- Platzhalterwerte und kurze Kommentare hinzufügen
- Sicherstellen, dass keine Secrets enthalten sind

**Akzeptanzkriterien:**
- `.env.example` enthält alle Pflichtvariablen
- Keine echten Zugangsdaten im Repo
- Setup klappt mit `.env.example` + lokaler Anpassung

---

## 10) Kleine Refactor-Aufgabe mit Tests

**Titel:** refactor: extract helper function and add unit tests

**Beschreibung:**
Wähle eine klar abgegrenzte, kleine Code-Stelle mit doppelter Logik und extrahiere sie in eine Helper-Funktion. Ergänze passende Unit-Tests.

**Aufgaben:**
- Duplizierte Logik identifizieren
- Helper-Funktion einführen
- Vorhandene Aufrufe umstellen
- Unit-Tests für Standard- und Edge-Cases ergänzen

**Akzeptanzkriterien:**
- Verhalten bleibt unverändert
- Neue Tests decken Hauptfälle + mindestens 1 Edge Case ab
- Linter/Tests laufen erfolgreich

---

## Optionaler Hinweis für jede Issue-Beschreibung

Du kannst am Ende jeder Issue diesen Block ergänzen:

- **Difficulty:** beginner
- **Estimated effort:** 1–3 hours
- **Mentor:** @maintainer-handle
- **Label:** `good first issue`
