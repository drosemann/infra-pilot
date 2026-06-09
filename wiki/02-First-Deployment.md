# 02 – First Deployment: Server erstellen in 3 Minuten

Dieses Beispiel zeigt, wie du über die CLI einen Server deployst.

## Voraussetzungen

- Infra-Pilot läuft (siehe [Installation](01-Installation))
- Du hast einen API-Key (im Management Panel unter Settings)

## 1. CLI konfigurieren

```bash
# API-URL setzen (lokal = http://localhost:3001)
ipilot config set api_url http://localhost:3001

# Mit API-Key authentifizieren
ipilot login dein-api-key
```

**Expected Output:**
```
┌──────────────────────────┐
│ status                   │
├──────────────────────────┤
│ Logged in successfully   │
└──────────────────────────┘
```

## 2. Verfügbare Server anzeigen

```bash
ipilot server list
```

**Expected Output:**
```
┌──────┬──────┬──────┬────────┐
│ id   │ name │ type │ status │
├──────┼──────┼──────┼────────┤
└──────┴──────┴──────┴────────┘
(no servers)
```

## 3. Server erstellen

```bash
ipilot server create --name mein-erster-server --type web --memory 2048
```

**Expected Output:**
```
┌────────────┬──────────────────────────────────────┐
│ field      │ value                                │
├────────────┼──────────────────────────────────────┤
│ id         │ srv_abc123                           │
│ name       │ mein-erster-server                   │
│ type       │ web                                  │
│ memory     │ 2048 MB                              │
│ status     │ creating                             │
│ created_at │ 2026-06-09T19:00:00Z                 │
└────────────┴──────────────────────────────────────┘
```

## 4. Status prüfen

```bash
ipilot server status srv_abc123
```

Sobald der Status `running` anzeigt, ist dein Server bereit.

## 5. Server wieder löschen (Cleanup)

```bash
ipilot server delete srv_abc123
```

**Expected Output:**
```
┌──────────┬──────────────────────────────────────┐
│ status   │ Server srv_abc123 deleted             │
└──────────┴──────────────────────────────────────┘
```

## Alternativ: Über das Management Panel

Öffne http://localhost:5173, klicke auf **"Server erstellen"** und folge dem Wizard – kein CLI nötig.

## Fehlerbehebung

| Problem | Lösung |
|---------|--------|
| `Connection failed` | Prüfe ob `docker compose ps` alle Services zeigt |
| `Unauthorized` | `ipilot login` erneut ausführen |
| Server bleibt `creating` | Prüfe die Logs: `docker compose logs orchestrator-agent` |

---

*Stand: Mai 2026 · [CLI-Referenz](05-CLI-Reference)*
