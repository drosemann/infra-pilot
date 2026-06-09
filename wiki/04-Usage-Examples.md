# 04 – Usage Examples: 5 Use-Cases

## 1. Server deployen und Logs live verfolgen

```bash
ipilot server create --name web-prod --type web --memory 4096
ipilot logs srv_abc123 --lines 50 --follow
```

Drücke `Ctrl+C` um das Log-Tailing zu beenden.

## 2. Backup erstellen und wiederherstellen

```bash
# Backup anlegen
ipilot backup create srv_abc123

# Alle Backups anzeigen
ipilot backup list srv_abc123
```

## 3. DNS-Zone verwalten

```bash
# Zone erstellen
ipilot dns create-zone --domain example.com --ttl 3600

# A-Record hinzufügen
ipilot dns add-record --zone-id zone_123 --name www --type A --value 192.168.1.1 --ttl 300

# Records anzeigen
ipilot dns records zone_123
```

## 4. Energieverbrauch tracken (Green Computing)

```bash
# Aktuellen Energieverbrauch abrufen
ipilot energy current

# CO₂-Fußabdruck anzeigen
ipilot carbon current

# Nachhaltige Provider ranken
ipilot provider rank
```

## 5. FinOps – Kosten optimieren

```bash
# Ungenutzte Ressourcen erkennen
ipilot reclaim scan

# Auto-Shutdown-Richtlinie erstellen (Ressourcen nach 20 Uhr stoppen)
ipilot shutdown create --name "night-shutdown" --tags "env:staging" --shutdown-hours "20:00-08:00"

# Savings Report
ipilot reclaim report
```

## Weitere Beispiele

| Thema | Befehl |
|-------|--------|
| VPN-Konfiguration | `ipilot vpn create --name office --server de-01 --port 51820 --protocol wireguard` |
| Reverse Proxy | `ipilot proxy create --domain app.example.com --target http://localhost:3000 --tls` |
| Backup-SLA | `ipilot backup-sla create --name "daily-3-2-1" --rpo 24 --rto 4` |
| Compliance-Scan | `ipilot compliance scan --benchmark cis-aws-1.4` |
| Chaos-Experiment | `ipilot chaos create --name "network-latency" --fault latency --duration 300` |

---

*Stand: Mai 2026 · [CLI-Referenz](05-CLI-Reference)*
