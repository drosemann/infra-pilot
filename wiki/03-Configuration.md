# 03 – Configuration

Infra-Pilot verwendet zwei Konfigurationsebenen: **Umgebungsvariablen** (`.env`) für Services und eine **CLI-Konfiguration** (`~/.ipilot/config.json`).

## 1. CLI-Konfiguration (`~/.ipilot/config.json`)

Die CLI speichert ihre Einstellungen automatisch in `~/.ipilot/config.json`:

```json
{
  "api_url": "http://localhost:3001",
  "api_key": null,
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "output_format": "table"
}
```

| Feld | Beschreibung | Default |
|------|-------------|---------|
| `api_url` | Basis-URL der Management API | `http://localhost:8080` (überschreibbar via `IPILOT_API_URL`) |
| `api_key` | API-Key für die Authentifizierung | `null` |
| `token` | JWT-Token (wird beim Login gesetzt) | `null` |
| `output_format` | Ausgabeformat: `table`, `json`, `yaml`, `plain` | `table` |

CLI-Konfiguration bearbeiten:
```bash
ipilot config get              # Alle Werte anzeigen
ipilot config set api_url http://localhost:3001
ipilot config set output_format json
```

## 2. Umgebungskonfiguration (`.env`)

Kopiere `.env.example` nach `.env` und passe die Werte an:

```bash
cp .env.example .env
```

### Wichtige Gruppen

| Bereich | Wichtigste Variablen |
|---------|---------------------|
| **Discord** | `DISCORD_TOKEN`, `DISCORD_BOT_TOKEN`, Channel/Role-IDs |
| **Datenbank** | `DATABASE_URL`, `POSTGRES_USER`, `POSTGRES_PASSWORD` |
| **AI/LLM** | `AI_API_ENDPOINT`, `AI_API_KEY`, `AI_MODEL` (default: `gpt-4`) |
| **Security** | `JWT_SECRET`, `CORS_ORIGIN`, `SECRETS_ENCRYPTION_KEY` |
| **Monitoring** | `OTEL_EXPORTER_OTLP_ENDPOINT`, `SENTRY_DSN`, `LOKI_URL` |

Die vollständige Referenz findest du in der [`.env.example`](https://github.com/daaanieltv/infra-pilot/blob/main/.env.example).

## 3. Multi-Provider Konfiguration

Das provider-neutrale Mapping liegt in `infra/naming/provider_map.yaml`:

```yaml
PROVIDER_MOCK: mock-provider
REGION_MOCK_US_EAST: mock-region-us-east
```

Dieses Mapping erlaubt es, Infrastruktur-Ressourcen provider-neutral zu definieren und später auf echte Provider (AWS, Azure, Hetzner, ...) abzubilden.

## 4. Docker Compose Overrides

Für abweichende Ports oder Umgebungen kannst du eine `docker-compose.override.yml` nutzen:

```yaml
services:
  management-panel:
    ports:
      - "8080:5173"
```

---

*Stand: Mai 2026 · [Referenz: .env.example](https://github.com/daaanieltv/infra-pilot/blob/main/.env.example)*
