# 09 – FAQ

## Allgemein

**Was genau ist Infra-Pilot?**

Ein modulares Orchestrierungs-Framework für Infrastructure-as-Code, Container-Management und Multi-Cloud-Provisionierung – gesteuert über CLI, Web-Dashboard oder Discord.

**Warum nicht einfach Terraform/Pulumi/Ansible nutzen?**

Infra-Pilot setzt *darauf* auf. Es bietet eine einheitliche API/CLI über mehrere Provider hinweg, ergänzt um AI-Features, Discord-Steuerung, Green-Computing-Tracking und ein modernes Dashboard. Du kannst weiterhin Terraform darunter nutzen.

## Installation & Setup

**Ich bekomme "Connection failed" bei `ipilot health`**

Prüfe, ob der Stack läuft: `docker compose ps`. Standard-API-URL ist `http://localhost:8080` – wenn dein Panel auf `:3001` läuft, setze `ipilot config set api_url http://localhost:3001`.

**Kann ich nur einzelne Services starten?**

Ja. `docker compose up -d postgres redis` startet nur die Datenbanken. Starte Services gezielt: `docker compose up -d management-panel`.

**Unter Windows geht Docker Compose nicht?**

Nutze Docker Desktop mit WSL2-Backend. Alternativ die Services nativ installieren (siehe [Installation](01-Installation)).

## CLI

**Wie ändere ich das Ausgabeformat?**

```bash
ipilot config set output_format json
ipilot server list   # → JSON-Ausgabe
```

Formate: `table` (default), `json`, `yaml`, `plain`.

**Es gibt 200+ Commands – wie behalte ich den Überblick?**

`ipilot --help` zeigt alle Top-Level-Commands. Für Subcommands: `ipilot server --help`, `ipilot dns --help`, etc.

## AI / LLM

**Welches LLM wird standardmäßig genutzt?**

OpenAI GPT-4 (konfigurierbar via `AI_MODEL`). Du kannst auf jedes OpenAI-kompatible Modell wechseln.

**Kann ich offline arbeiten?**

Ja. Setze einen lokalen LLM-Endpunkt (Ollama, LM Studio, llama.cpp) in der `.env`. Alle AI-Features laufen dann lokal – kein Internet nötig.

**Welche Daten werden an OpenAI gesendet?**

Siehe [Security-Seite](08-Security#welche-daten-gehen-an-llm-apis) für eine detaillierte Aufstellung.

## Troubleshooting

**Server bleibt ewig im Status "creating"**

Prüfe die Logs des Orchestrator Agents: `docker compose logs orchestrator-agent`. Häufige Ursache: fehlende Cloud-Provider-Credentials.

**Discord-Bot reagiert nicht**

- Ist `DISCORD_TOKEN` in der `.env` gesetzt?
- Läuft der Discord Service? `docker compose logs discord-service`
- Hat der Bot die nötigen Intents im Discord Developer Portal?

**Management Panel zeigt leere Seite**

Prüfe die Browser-Console (F12) auf CORS-Fehler. Setze `CORS_ORIGIN` in der `.env` auf die korrekte Frontend-URL.

---

*Stand: Mai 2026 · [Alle Issues](https://github.com/daaanieltv/infra-pilot/issues) · [Discussions](https://github.com/daaanieltv/infra-pilot/discussions)*
