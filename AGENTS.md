# infra-pilot — Agent Guide

## Arbeitsweise

- Arbeite pragmatisch, ehrlich und direkt. Prüfe bestehenden Code und den
  betroffenen Ablauf, bevor du Änderungen vornimmst.
- Setze klare, sichere Aufgaben direkt um. Frage nur nach, wenn fehlende
  Informationen die Lösung wesentlich beeinflussen.
- Bevorzuge kleine, verständliche und rückgängig zu machende Änderungen.
  Vermeide unnötige Abstraktionen und Abhängigkeiten.
- Weise knapp auf konkrete Risiken, widersprüchliche Anforderungen oder
  einfachere Alternativen hin. Implementiere keine zusätzliche Änderung ohne
  Bezug zur Anfrage.
- Ergänze oder ändere Tests und Dokumentation, wenn es die Änderung erfordert.

## Projektleitfaden

## Wie wir entwickeln

- Bevorzuge die kleinste produktionsreife Änderung, die das eigentliche
  Problem löst. Verstehe das bestehende Verhalten, bevor du Abstraktionen oder
  Konfigurationen hinzufügst.
- Setze den Ablauf für Nutzerinnen und Nutzer durchgängig um. CLI,
  Verwaltungsoberfläche, Agent, Discord-Bridge, Deployment-Dateien und
  Dokumentation können unterschiedliche Teile desselben Features sein.
- Bevorzuge funktionierende Implementierungen statt Platzhaltern, gefälschter
  Integrationen oder nicht eingebundenem Democode. Entferne veraltete Wege,
  wenn du sie ersetzt; baue kein neues Verhalten auf totem Code auf.
- Behandle den Produktivbetrieb, Sicherheitsgrenzen und vorhandene Nutzerdaten
  als zentrale Anforderungen. Upgrades, Migrationen, Backups und
  Wiederherstellungen müssen Daten bewahren oder einen sicheren
  Wiederherstellungsweg klar definieren.
- Ergänze gezielte Tests für geändertes Verhalten und Regressionen. Tests
  sollten aussagekräftige Ergebnisse prüfen und nicht lediglich die
  Implementierung nachbilden.
- Aktualisiere die Dokumentation für Nutzer, Betreiber, APIs oder Architektur,
  wenn sich durch die Änderung relevante Informationen für diese Zielgruppen
  ändern. Folge [docs/DOCUMENTATION.md](docs/DOCUMENTATION.md), statt
  Dokumentation zu duplizieren.

## Projektstruktur

- `cli/` — `ipilot`-Kommandozeilenclient
- `services/management-panel/` — React-Oberfläche, Express-API und WebSocket-Server
- `services/orchestrator-agent/` — Python-Agent, Manifeste, RBAC und Webhooks
- `services/discord-service/` — optionale Integration für Discord und Pterodactyl
- `helm/` und `infra/` — Kubernetes-Chart und Infrastruktur
- `scripts/` — Hilfsprogramme für Umgebungen, Backups, Healthchecks und Releases
- `tests/` — Python-Testsuiten und Lasttestszenarien
- `docs/` und `wiki/` — Entwicklerdokumentation sowie Anleitungen für Nutzer und Betreiber

Lies vor Änderungen an einem Service dessen README und vorhandene Tests.
Prüfe bei serviceübergreifendem Verhalten den Vertrag an jeder Schnittstelle,
statt anzunehmen, dass die Tests einer Komponente den gesamten Ablauf abdecken.

## Wie du entwicklen sollst

- keine sub agents nur ein single agent
- sei sparsam mit tokens
- wenn du etwas nicht weißt gib es zu und probiere nicht etliche male und verschwende tokens
- sei token effizient
- wenn ich bullshit sage sag es mir
- sei kreativ, mach ruhig wilde features die erstmal dumm wirken
