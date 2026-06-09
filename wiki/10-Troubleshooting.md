# 10 – Troubleshooting

## CLI & Connection

| Fehler | Ursache | Lösung |
|--------|---------|--------|
| `Connection failed: [Errno 111] Connection refused` | Management API läuft nicht | `docker compose ps` prüfen; API-URL mit `ipilot config set api_url ...` korrigieren |
| `Connection failed: [Errno -2] Name or service not known` | Falsche API-URL | `ipilot config get` zeigt aktuelle URL; auf `http://localhost:3001` setzen |
| `Unauthorized` | Token abgelaufen oder fehlt | `ipilot login <api-key>` erneut ausführen |
| `404 Not Found` | Falscher API-Pfad | Prüfe ob du die aktuellste Version nutzt (`ipilot --version`) |

## Docker Stack

| Fehler | Ursache | Lösung |
|--------|---------|--------|
| Container restartet ständig | Fehlende `.env`-Variablen | `.env.example` kopieren und alle Pflichtfelder setzen |
| `port is already allocated` | Port-Konflikt | Andere Docker-Container stoppen oder Ports in `docker-compose.override.yml` ändern |
| PostgreSQL nicht erreichbar | Wartezeit zu kurz | `docker compose logs postgres` prüfen; `depends_on` mit `condition: service_healthy` greift automatisch |
| `no matching manifest for windows/amd64` | Image nicht für Windows | Docker Desktop mit Linux-Containern nutzen |

## Management Panel

| Problem | Lösung |
|---------|--------|
| Leere Seite / weißer Bildschirm | Browser-Konsole (F12) auf Fehler prüfen; `VITE_API_URL` in `.env` korrekt setzen |
| CORS-Fehler | `CORS_ORIGIN=http://localhost:5173` in `.env` setzen |
| API-Aufrufe schlagen fehl | Prüfe ob `MANAGEMENT_BACKEND_PORT` und `PORT` in `.env` korrekt sind |
| Supabase-Fehler | `VITE_SUPABASE_URL` und `VITE_SUPABASE_ANON_KEY` prüfen (optional für Demo-Modus) |

## Discord Bot

| Fehler | Ursache | Lösung |
|--------|---------|--------|
| Bot antwortet nicht | Token fehlt oder falsch | `DISCORD_TOKEN` in `.env` prüfen |
| `Privileged Gateway Intents` | Fehlende Intents | Im Discord Developer Portal unter Bot → Gateway Intents alle drei aktivieren |
| Bot sieht keine Nachrichten | Falsche Channel-ID | `SERVER_CREATION_CHANNEL_ID` in `.env` prüfen |
| `Missing Access` | Bot hat keine Berechtigungen | Bot-Rolle im Server nach oben ziehen |

## LLM / AI Features

| Problem | Lösung |
|---------|--------|
| AI Assistant antwortet nicht | `AI_API_ENDPOINT` und `AI_API_KEY` in `.env` prüfen |
| Lokales LLM langsam | Kleinere Modelle nutzen (z. B. `llama3-8b` statt `70b`); GPU-Beschleunigung prüfen |
| "Model not found" | `AI_MODEL` auf ein verfügbares Modell setzen |

## Cloud Provider

| Provider | Häufiger Fehler | Lösung |
|----------|----------------|--------|
| AWS | `InvalidAccessKeyId` | AWS Creds in Umgebungsvariablen oder `~/.aws/credentials` prüfen |
| Azure | `AuthenticationFailed` | `az login` ausführen oder Service Principal korrekt setzen |
| Hetzner | `unauthorized` | Hetzner API-Token in `.env` prüfen |

## Logs anzeigen

```bash
# Alle Services
docker compose logs --tail=100 -f

# Einzelner Service
docker compose logs orchestrator-agent --tail=50 -f
docker compose logs management-panel --tail=50 -f

# CLI-Debug
ipilot -o json health
```

## Support

- **Issues:** [github.com/daaanieltv/infra-pilot/issues](https://github.com/daaanieltv/infra-pilot/issues)
- **Discussions:** [github.com/daaanieltv/infra-pilot/discussions](https://github.com/daaanieltv/infra-pilot/discussions)
- **Security-Vorfälle:** Bitte *kein* öffentliches Issue – siehe [SECURITY.md](https://github.com/daaanieltv/infra-pilot/blob/main/SECURITY.md)

---

*Stand: Mai 2026*
