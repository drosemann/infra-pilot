# 08 – Security

## Welche Daten gehen an LLM-APIs?

Infra-Pilot bietet verschiedene AI/ML-Features (AI Assistant, Log Anomaly Detection, Capacity Forecasting, etc.). Wenn aktiviert, werden folgende Daten an den konfigurierten LLM-Provider gesendet:

| Feature | Daten | LLM-Kontakt |
|---------|-------|-------------|
| **AI Assistant** | Server-Status, Konfiguration, deine Chat-Nachrichten | Ja |
| **Log Anomaly Detection** | Container-Logs (Auszüge) | Ja (konfigurierbar) |
| **AI Capacity Forecaster** | Metriken, Zeitreihen, Auslastungsdaten | Ja |
| **AI Config Advisor** | Infrastruktur-Konfiguration | Ja |
| **AI Code Review Bot** | PR-Diffs aus GitHub | Ja |

**Standard-Provider:** OpenAI (GPT-4) – konfigurierbar via `AI_API_ENDPOINT` und `AI_API_KEY` in der `.env`.

### Lokaler Modus (keine Datenverlassen die Maschine)

Setze in der `.env`:
```env
AI_API_ENDPOINT=http://localhost:1234/v1
AI_API_KEY=not-needed
AI_MODEL=llama3-8b
```

Kompatibel mit Ollama, LM Studio, llama.cpp und jedem OpenAI-kompatiblen lokalen Endpunkt.

## Telemetry

Infra-Pilot erhebt **keine** Telemetrie. Es gibt kein Tracking, keine Analytics-Dienste und kein Phone-Home. Du musst nichts deaktivieren – es ist standardmäßig aus.

Sollte sich das in Zukunft ändern, wird dies explizit in den Release-Notes kommuniziert und es gibt einen Opt-out per `.env`-Variable.

## Umgang mit Secrets

### `.env` / `.tfvars`

- `.env` ist in `.gitignore` – wird nie committed
- Secrets gehören **nicht** in Versionskontrolle
- Nutze Umgebungsvariablen oder einen Secrets-Manager (HashiCorp Vault wird unterstützt)

### Verschlüsselung

- **Transport:** TLS/SSL für alle externen API-Endpunkte
- **Speicher:** Secrets können via `SECRETS_ENCRYPTION_KEY` (Fernet-Verschlüsselung) gespeichert werden
- **JWT-Tokens:** Secure Token Handling im CLI – Token wird lokal in `~/.ipilot/config.json` gespeichert

### Empfohlene Secrets-Strategie

```
1. KEINE Secrets in Code oder Config committed
2. .env.example ohne echte Werte
3. In Produktion: Vault / Secret-Store verwenden
4. Rotation: 'ipilot secrets rotate' für regelmäßige Rotation
```

## Security-Scans (CI/CD)

| Tool | Scannt | Ausführung |
|------|--------|-----------|
| `bandit` | Python-Code auf Sicherheitslücken | GitHub Actions |
| `safety` | Python-Dependencies auf CVEs | GitHub Actions |
| `npm audit` | JS-Dependencies auf CVEs | GitHub Actions |
| `trivy` | Docker-Images | GitHub Actions |

## Sicherheits-Features im Überblick

- **JWT-Authentifizierung** mit Token-basierten Sessions
- **RBAC** (Role-Based Access Control) für alle Operationen
- **2FA/TOTP** und **WebAuthn/Passkey** für Admin-Accounts
- **PAM** (Privileged Access Management) mit Just-in-Time-Freigaben
- **Audit-Trail** – Append-only Log für alle Mutationen
- **Breach Notification** – GDPR-konformes 72h-Benachrichtigungs-Tracking

## Security-Vorfälle melden

**Öffne keine öffentlichen Issues für Sicherheitslücken!**

Melde Vorfälle per E-Mail an die Maintainer (siehe [`SECURITY.md`](https://github.com/daaanieltv/infra-pilot/blob/main/SECURITY.md)). Wir bestätigen den Eingang innerhalb von 48h und arbeiten an einem Fix.

---

*Stand: Mai 2026 · [SECURITY.md](https://github.com/daaanieltv/infra-pilot/blob/main/SECURITY.md)*
