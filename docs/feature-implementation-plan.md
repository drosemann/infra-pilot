# Feature Implementation Plan — Infra Pilot

## Übersicht

Dieser Plan deckt **50 Features** in **5 Kategorien** ab.  
Jedes Feature wird einem Service zugeordnet, der Status des bereits Vorhandenen bewertet und der Implementierungsaufwand geschätzt.

### Bewertungsschlüssel

| Symbol | Bedeutung |
|--------|-----------|
| ✅ | Vollständig implementiert |
| 🟡 | Teilweise vorhanden, Erweiterung nötig |
| 🔴 | Neu zu entwickeln |
| ⚪ | Nicht zutreffend / entfällt |

---

## 1. 🎮 Gaming & Bot-Spezifische Features

| # | Feature | Management Panel | Orchestrator Agent | Discord Service | Integration Service | Service Core | Status | Aufwand |
|---|---------|:---:|:---:|:---:|:---:|:---:|--------|--------|
| 1 | **Modpack-Installer mit 1-Klick** | UI + API | Neues Cog | – | CurseForge/Modrinth API | Startup-Integration | 🔴 Neu | 5 PT |
| 2 | **Sub-Server-Netzwerke (BungeeCord/Velocity)** | UI für Netzwerk-Config | Neues Cog (BungeeCord-Setup) | – | – | BungeeCord-Konfiguration | 🔴 Neu | 6 PT |
| 3 | **Discord-Bot Token-Validierung** | Backend-Endpoint | – | Validierungs-Utility | Validation API | – | 🟡 Teilw. | 2 PT |
| 4 | **Bot-Uptime-Keeper** | – | Neues Cog (Ping-Service) | Health-Check-Erweiterung | Monitoring-Aggregation | – | 🔴 Neu | 4 PT |
| 5 | **RCON-Web-Konsole** | WebSocket-RCON-Component | – | – | RCON-Proxy-API | RCON-Server-Interface | 🔴 Neu | 5 PT |
| 6 | **Spieler-Statistiken-Dashboard** | Live-Statistik-UI | – | – | Metrics-Aggregation | PlayerStatistics existiert | 🟡 Teilw. | 4 PT |
| 7 | **Auto-Plugin-Updater** | – | update_manager erweitern | – | – | Plugin-Update-Mechanismus | 🟡 Teilw. | 4 PT |
| 8 | **Config-Editor mit Syntax-Highlighting** | Monaco/CodeMirror-Editor | – | – | Config-Read/Write-API | Config-Dateien | 🔴 Neu | 4 PT |
| 9 | **MySQL-Datenbank per Klick** | UI für DB-Erstellung | Neues Cog (MySQL-Container) | – | DB-Provisioning-API | DB-Konfiguration | 🟡 Teilw. | 3 PT |
| 10 | **Custom Java-Version-Selector** | UI für Java-Version | Docker-Image-Selektion | – | – | Java-Compat-Check | 🔴 Neu | 3 PT |

### Details zu Gaming-Features

**1. Modpack-Installer** — 5 PT (Orchestrator + Panel + Integration)
- Orchestrator: Neues Cog `modpack_installer.py` — CurseForge API (`api.curseforge.com`) und Modrinth API (`api.modrinth.com`) abfragen, Modpack-Metadaten laden, Docker-Image mit Modpack bauen
- Management Panel: Neue Seite "Modpacks" mit Suchleiste, Kategorieselect, Installationsbutton
- Integration Service: API-Endpunkt `/api/modpacks/search`, `/api/modpacks/install` als Proxy
- Service Core: Startup-Flag für Modpack-Pfad

**2. Sub-Server-Netzwerke** — 6 PT (Orchestrator + Panel + Core)
- Orchestrator: Neues Cog `network_manager.py` — BungeeCord/Velocity-Konfiguration automatisch generieren, Server registrieren, Waterfall/Velocity-Docker-Image starten
- Management Panel: Netzwerk-Config-UI (Server hinzufügen/entfernen, Prioritäten, Motd)
- Service Core: `config.yml` um Network-Sektion erweitern, PluginMessageListener für BungeeCord-Kommunikation

**3. Discord-Bot Token-Validierung** — 2 PT (Discord Service + Panel)
- Discord Service: `validateBotToken(token)` — mittels Discord.js REST (`discord.js/rest`) prüfen, ob Token gültig ist
- Management Panel: Backend-Endpoint `POST /api/validate/discord-token` ruft Discord API auf, gibt Guild-Name und Bot-Name zurück

**4. Bot-Uptime-Keeper** — 4 PT (Orchestrator + Integration)
- Orchestrator: Neues Cog `uptime_keeper.py` — periodischer Ping auf Bot-Websocket-Endpoint, bei fehlender Response: Container-Neustart via Docker SDK, Health-Check-Event an Integration Service
- Integration Service: Uptime-Statistiken sammeln, Ausfall-Historie, Alert bei häufigem Neustart

**5. RCON-Web-Konsole** — 5 PT (Panel + Integration + Core)
- Management Panel: Neue WebSocket-basierte RCON-Konsole mit xterm.js oder eigener Terminal-Darstellung, farbige Ausgabe
- Integration Service: `/api/rcon/connect` — RCON-Proxy, der WebSocket-Verbindungen zu Minecraft-RCON-Ports hält
- Service Core: `rcon.properties` generieren, RCON-Port konfigurierbar

**6. Spieler-Statistiken-Dashboard** — 4 PT (Panel + Integration + Core)
- Management Panel: Bestehenden `PlayerCountChart` erweitern um: Spielerliste, Ping-Anzeige, aktivste Nutzer (nach Spielzeit), Tages-/Wochenstatistik
- Integration Service: `UnifiedMetrics` um Spieler-Metriken erweitern
- Service Core: `PlayerStatistics` mit Ping-Tracking ergänzen

**7. Auto-Plugin-Updater** — 4 PT (Orchestrator + Core)
- Orchestrator: Cog `update_manager.py` erweitern — SpigotMC API (`api.spigotmc.org`) und PaperMC API nach Updates durchsuchen, Download bei neuer Version, Plugin-JAR im Container austauschen, Cron-Job für nächtliche Updates
- Service Core: Konfiguration für erlaubte/nicht erlaubte Auto-Updates

**8. Config-Editor** — 4 PT (Panel + Integration)
- Management Panel: Neue Component mit Monaco Editor (@monaco-editor/react) oder CodeMirror, YAML/JSON-Validierung (js-yaml), Fehlermarkierung, Speichern-Button
- Integration Service: API-Endpunkte `/api/config/:appId/read`, `/api/config/:appId/write` — Config-Dateien aus Container lesen/schreiben

**9. MySQL-Datenbank per Klick** — 3 PT (Orchestrator + Integration)
- Orchestrator: Cog `database_manager.py` — MySQL-Container via Docker SDK starten, DB-User und -Passwort generieren, Verbindungsdaten zurückgeben
- Integration Service: Endpunkt `/api/databases/create` in Resource Tracker

**10. Custom Java-Version-Selector** — 3 PT (Panel + Orchestrator + Core)
- Management Panel: Dropdown für Java 8, 11, 17, 21 in AppForm
- Orchestrator: Docker-Image-Name je nach Java-Version auswählen (z. B. `eclipse-temurin:17-jdk` vs `eclipse-temurin:21-jdk`)
- Service Core: `config.yml` um `java_version` erweitern

---

## 2. 🛡️ Sicherheit & Zugriffskontrolle

| # | Feature | Management Panel | Orchestrator Agent | Discord Service | Integration Service | Service Core | Status | Aufwand |
|---|---------|:---:|:---:|:---:|:---:|:---:|--------|--------|
| 11 | **2FA (TOTP)** | TOTP-Setup/Verify-UI | – | – | Auth-Erweiterung | – | 🔴 Neu | 5 PT |
| 12 | **Sub-User-Management** | RBAC-UI (bereits Customers) | – | – | permissions.py erweitern | – | 🟡 Teilw. | 4 PT |
| 13 | **SSH-Key-Manager** | UI für SSH-Keys | Neues Cog | – | Key-Storage-API | – | 🔴 Neu | 4 PT |
| 14 | **Automatisierte Firewall (UFW/Iptables GUI)** | Firewall-Regel-UI | security_audit erweitern | – | Firewall-API | – | 🔴 Neu | 4 PT |
| 15 | **DDoS-Traffic-Analyse** | Live-Traffic-Charts | traffic_analysis.py erweitern | – | Traffic-Metrics-Aggregation | – | 🟡 Teilw. | 4 PT |
| 16 | **Aktivitäts-Logbuch (Audit-Log)** | ✅ AuditLog-Seite existiert | – | – | ✅ AuditLogger existiert | – | ✅ Fertig | – |
| 17 | **Automatisches IP-Whitelisting** | IP-Whitelist-UI | Firewall-Integration | – | Whitelist-API | – | 🔴 Neu | 3 PT |
| 18 | **SSL-Zertifikate per Klick** | SSL-Status-UI | ✅ ssl_manager.py existiert | – | Cert-Status-API | – | 🟡 Teilw. | 2 PT |
| 19 | **Malware- & Schadcode-Scanner** | Upload-Scan-UI | Neues Security-Cog | – | Scan-Orchestrierung | – | 🔴 Neu | 5 PT |
| 20 | **Isolierte Umgebungen (Docker/Podman)** | ✅ Docker-Integration | ✅ vps_manager.py (Docker SDK) | – | – | – | ✅ Fertig | – |

### Details zu Sicherheits-Features

**11. 2FA (TOTP)** — 5 PT (Panel + Integration + Discord)
- Management Panel: QR-Code-Setup (Speichebene via `otpauth://` URI), Verify-Seite, Backup-Codes, „Remember this device"-Cookie
- Integration Service: `speakeasy` (Node) oder `pyotp` (Python) TOTP-Validierung in `/api/auth/2fa/setup`, `/api/auth/2fa/verify`
- Discord Service: `verificationSystem.js` um 2FA-Integration erweitern

**12. Sub-User-Management** — 4 PT (Panel + Integration)
- Management Panel: Bestehende `Customers`-Seite um RBAC erweitern — Rollen (Admin/Editor/Viewer/Support), Berechtigungsmatrix („Darf Server neustarten", „Darf Dateien löschen"), Einladungs-Link
- Integration Service: `permissions.py` um Sub-User-Rollen, Permission-Inheritance, Team-Bereiche erweitern

**13. SSH-Key-Manager** — 4 PT (Orchestrator + Panel + Integration)
- Orchestrator: Neues Cog `ssh_key_manager.py` — SSH-Keys in Containern deployen (`~/.ssh/authorized_keys`), Public-Key-Validierung, Key-Rotation
- Management Panel: UI zum Hochladen/Verwalten von Public-Keys
- Integration Service: Key-Storage-API (verschlüsselt), `/api/ssh-keys/crud`

**14. Automatisierte Firewall** — 4 PT (Orchestrator + Panel + Integration)
- Orchestrator: `security_audit.py` erweitern um UFW/Iptables-Regeln via `docker exec` — Port-Block/Allow, Regel-Liste, Regel-Priorität
- Management Panel: Firewall-Regel-Editor (Port, Protokoll, Source-IP, Aktion)
- Integration Service: Firewall-State-Persistierung, Audit-Trail

**15. DDoS-Traffic-Analyse** — 4 PT (Orchestrator + Panel)
- Orchestrator: `traffic_analysis.py` erweitern — Bandbreiten-Monitoring pro Container, Traffic-Spitzen erkennen (≥3σ-Abweichung), Heatmap-Diagramme
- Management Panel: Live-Traffic-Charts (Realtime via WebSocket), Tages-/Wochenansicht, Alarm bei Anomalie

**17. Automatisches IP-Whitelisting** — 3 PT (Orchestrator + Integration)
- Orchestrator: IP-Whitelist-Regeln via Iptables/UFW setzen, nur vordefinierte IPs dürfen auf bestimmte Ports
- Integration Service: `/api/security/whitelist` — CRUD für IP-Whitelist-Einträge

**19. Malware-Scanner** — 5 PT (Orchestrator + Integration + Panel)
- Orchestrator: Neues Cog `malware_scanner.py` — ClamAV via Docker (`mkodockx/docker-clamav`) oder YARA-Regeln auf .jar/.py-Dateien, Scan-Ergebnis auswerten
- Management Panel: Upload-Fenster mit Fortschrittsbalken, Ergebnis-Anzeige
- Integration Service: Scan-Orchestrierung, Quarantäne-Management

---

## 3. ⚙️ Automatisierung & DevOps

| # | Feature | Management Panel | Orchestrator Agent | Discord Service | Integration Service | Service Core | Status | Aufwand |
|---|---------|:---:|:---:|:---:|:---:|:---:|--------|--------|
| 21 | **Geplante Aufgaben (Cronjobs)** | MaintenanceScheduler existiert | Background-Tasks erweitern | node-cron existiert | announcement_scheduler.py | – | 🟡 Teilw. | 3 PT |
| 22 | **Git-Deployment (Webhook)** | Webhook-Config-UI | Neues Cog (Git-Pull) | GitHub-Webhook-Handler | Webhook-API | – | 🔴 Neu | 4 PT |
| 23 | **Automatisches Backup-System** | ✅ BackupManager existiert | ✅ backup_manager.py | – | ✅ BackupManager existiert | – | 🟡 Teilw. | 3 PT |
| 24 | **Auto-Scaling bei Last** | – | ✅ auto_scaling.py existiert | – | ResourceTracker erweitern | – | 🟡 Teilw. | 2 PT |
| 25 | **Template-System** | UI für Templates | ✅ template_manager.py | – | Template-API | – | 🟡 Teilw. | 2 PT |
| 26 | **API-Zugriff (REST API)** | ✅ 70+ Endpoints + OpenAPI | – | – | ✅ 80+ Endpoints | – | ✅ Fertig | – |
| 27 | **Auto-Heal** | – | health_checks.py + recovery.py | – | Health-Monitoring | – | 🟡 Teilw. | 3 PT |
| 28 | **Start-Argumente-Optimierer** | JVM-Flag-UI | performance_optimizer.py erweitern | – | – | JVM-Config | 🔴 Neu | 3 PT |
| 29 | **Ressourcen-Limits (Cgroups)** | Resource-UI in AppForm | ✅ vps_manager.py (Docker) | – | – | – | ✅ Fertig | – |
| 30 | **Ein-Klick-OS-Reinstall** | – | clone_system.py erweitern | – | Reinstall-API | – | 🟡 Teilw. | 4 PT |

### Details zu DevOps-Features

**21. Geplante Aufgaben (Cronjobs)** — 3 PT (Panel + Orchestrator + Discord)
- Management Panel: Bestehenden `MaintenanceScheduler` erweitern auf beliebige Cron-Jobs (Server-Restart, Befehl, Backup)
- Orchestrator: Background-Task-Scheduler (Cron-ähnlich) in `main.py` — Tasks aus DB lesen, zu festgelegten Zeiten ausführen
- Discord Service: `node-cron` in `index.js` für Discord-interne Aufgaben (Cleanup, Status-Update)

**22. Git-Deployment (Webhook)** — 4 PT (Orchestrator + Discord + Panel)
- Orchestrator: Neues Cog `git_deployer.py` — Webhook empfangen (`/webhook/github`), Git-Pull im Container, `npm install`/`pip install`, Container-Restart, Rollback bei Fehler
- Discord Service: GitHub-Webhook-Event-Handler (push, pull_request)
- Management Panel: UI zur Konfiguration (Repository, Branch, Deploy-Command)

**23. Automatisches Backup-System** — 3 PT (alle Services)
- Bestehende Backups (Panel, Orchestrator, Integration) um externe Speicherung erweitern:
  - AWS S3 (boto3/botocore) oder S3-kompatibel (MinIO)
  - SFTP (paramiko)
  - Automatische Retention (7 täglich, 4 wöchentlich, 3 monatlich)
- Management Panel: Backup-Ziel-Konfiguration, manueller Trigger

**24. Auto-Scaling bei Last** — 2 PT (Orchestrator + Integration)
- Orchestrator: Vorhandenes `auto_scaling.py` mit Metrics-Integration abschließen — CPU/RAM-Schwellenwerte aus config.py verwenden, Docker-Update-API für neue Limits
- Integration Service: `UnifiedResourceTracker` mit Scaling-Events koppeln

**27. Auto-Heal** — 3 PT (Orchestrator + Integration)
- Orchestrator: `health_checks.py` + `recovery.py` zu Auto-Heal-Pipeline verbinden:
  1. Health-Check schlägt fehl → Playbook ausführen
  2. Playbook-Stufen: Container-Neustart → Host-Reboot → Admin-Benachrichtigung
- Integration Service: Health-Status-Dashboard, Incident-Timeline

**28. Start-Argumente-Optimierer** — 3 PT (Panel + Orchestrator)
- Management Panel: RAM-Schieberegler (z. B. 1GB–32GB) → automatisch passende JVM-Flags generieren
  - Aikar's Flags für Minecraft (`-XX:+UseG1GC`, `-XX:G1HeapRegionSize=4M`, etc.)
- Orchestrator: `performance_optimizer.py` erweitern um JVM-Flag-Berechnung

**30. Ein-Klick-OS-Reinstall** — 4 PT (Orchestrator + Integration)
- Orchestrator: `clone_system.py` erweitern — Container löschen, neues Image deployen, SSH-Keys wiederherstellen, Backup einspielen
- Integration Service: OS-Image-Liste, Reinstall-Audit-Trail

---

## 4. 📊 Monitoring & Analytics

| # | Feature | Management Panel | Orchestrator Agent | Discord Service | Integration Service | Service Core | Status | Aufwand |
|---|---------|:---:|:---:|:---:|:---:|:---:|--------|--------|
| 31 | **Echtzeit-Ressourcen-Graphen** | ResourceChart etc. existieren | monitoring.py existiert | – | Netdata/Grafana-Bridge | – | 🟡 Teilw. | 3 PT |
| 32 | **Discord/Telegram-Benachrichtigungen** | – | – | – | ✅ notification_providers.py | – | ✅ Fertig | – |
| 33 | **Log-Dateien-Suchfunktion** | LiveLogs erweitern | – | – | UnifiedLogger erweitern | – | 🟡 Teilw. | 3 PT |
| 34 | **Speicherplatz-Warnung** | – | Alert Thresholds existieren | – | Alert-System erweitern | – | 🟡 Teilw. | 2 PT |
| 35 | **Ping- & Latenz-Tracker** | – | ✅ network_monitor.py | – | – | – | ✅ Fertig | – |
| 36 | **Kosten-Live-Kalkulator** | – | ✅ cost_optimizer.py | – | – | – | 🟡 Teilw. | 2 PT |
| 37 | **Prozess-Manager (HTOP-Klon)** | ✅ WebTerminal existiert | Docker-Exec-Prozessliste | – | – | – | 🟡 Teilw. | 2 PT |
| 38 | **Uptime-Statusseite** | Neue Public-Status-Seite | Health-Endpoints | – | Status-API | – | 🔴 Neu | 4 PT |
| 39 | **Inaktivitäts-Erkennung** | – | – | – | – | ✅ InactivityShutdownTask | ✅ Fertig | – |
| 40 | **Historischer Daten-Export** | ✅ Reports (CSV/PDF) | – | – | – | – | ✅ Fertig | – |

### Details zu Monitoring-Features

**31. Echtzeit-Ressourcen-Graphen** — 3 PT (Panel + Integration)
- Management Panel: Bestehende Charts (ResourceChart, PerformanceChart) um folgende Live-Daten erweitern:
  - Netdata-Integration (`http://netdata:19999/api/v1/chart`) oder Grafana-Embed
  - WebSocket-basierte Echtzeit-Updates (alle 2s via bestehender WS-Infrastruktur)
- Integration Service: Metrics-Bridge zu externen Tools (Netdata, Grafana, Prometheus)

**33. Log-Dateien-Suchfunktion** — 3 PT (Panel + Integration)
- Management Panel: LiveLogs um Suchleiste erweitern (Filter nach „Exception", „Error", Zeitraum, Log-Level)
- Integration Service: `UnifiedLogger.search()` — Volltextsuche in Log-Dateien, Regex-Unterstützung, Pagination

**34. Speicherplatz-Warnung** — 2 PT (Orchestrator + Integration)
- Orchestrator: Bestehende Disk-Alert-Config (90 %) mit Monitoring-Loop verbinden → Event an Integration Service
- Integration Service: Alert-Regel prüfen, Benachrichtigung via konfigurierte Kanäle (Email/Webhook/Telegram)

**36. Kosten-Live-Kalkulator** — 2 PT (Panel + Orchestrator)
- Management Panel: Kleine Anzeige im Dashboard „Aktuelle Kosten: €0.47/Stunde"
- Orchestrator: `cost_optimizer.py` + `cost_prediction.py` Daten an Panel-API übermitteln

**37. Prozess-Manager (HTOP-Klon)** — 2 PT (Panel + Orchestrator)
- Management Panel: Bestehende WebTerminal-Integration nutzen, zusätzlich `docker exec <container> ps aux` als Tabellenansicht
- Orchestrator: `vps_manager.py` um `exec_in_container()` für Prozess-Listing erweitern

**38. Uptime-Statusseite** — 4 PT (Panel + Integration)
- Management Panel: Neue Public-Seite (ohne Auth) als Subdomain oder `/status`-Route
  - Zeigt alle Server-Dienste mit Status (grün/gelb/rot)
  - Uptime-Prozente, letzte Incidents
  - Stil wie Cachet oder Uptime Kuma
- Integration Service: `/api/status` — aggregierte Health-Daten aller Services

---

## 5. 💳 Abrechnung & Kundenverwaltung

| # | Feature | Management Panel | Orchestrator Agent | Discord Service | Integration Service | Service Core | Status | Aufwand |
|---|---------|:---:|:---:|:---:|:---:|:---:|--------|--------|
| 41 | **Prepaid-Guthaben-System** | Kundenkonto-UI | player_economy + billing | – | Balance-API | EconomyManager existiert | 🟡 Teilw. | 4 PT |
| 42 | **Automatisches Mahnwesen** | UI für überfällige Zahlungen | vps_billing.py erweitern | – | – | – | 🟡 Teilw. | 3 PT |
| 43 | **Rabatt- und Gutscheincode-System** | Coupon-Admin-UI | vps_pricing.py erweitern | – | Coupon-API | – | 🔴 Neu | 4 PT |
| 44 | **Affiliate-Programm** | Affiliate-Dashboard | Neues Billing-Cog | – | Affiliate-API | – | 🔴 Neu | 5 PT |
| 45 | **Multi-Währungs-Support** | Währungs-Selector | Pricing-System erweitern | – | Umrechnungs-API | – | 🔴 Neu | 3 PT |
| 46 | **Ticket-Support-System** | – | – | ✅ ticketSystem.js | Ticket-API-Sync | – | ✅ Fertig | – |
| 47 | **Server-Sharing / Transfer** | Transfer-UI | server_migration.py erweitern | – | Transfer-API | – | 🟡 Teilw. | 4 PT |
| 48 | **Rechnungs-PDF-Generator** | Reports für Rechnungen | Billing-Log | – | PDF-Gen-API | – | 🔴 Neu | 4 PT |
| 49 | **Kostenlose Testphase (Trial)** | Trial-Anzeige | vps_billing.py erweitern | – | Trial-Management | – | 🔴 Neu | 3 PT |
| 50 | **Verbrauchshistorie** | Reports-Seite erweitern | vps_statistics existiert | – | – | – | 🟡 Teilw. | 2 PT |

### Details zu Billing-Features

**41. Prepaid-Guthaben-System** — 4 PT (Panel + Orchestrator + Integration)
- Management Panel: Kundenkonto-Seite mit Guthaben-Anzeige, Auflade-Button, Zahlungsmethoden (PayPal/Stripe)
- Orchestrator: `player_economy` und `vps_billing.py` verbinden — Guthaben wird stündlich abgebucht, bei 0-Guthaben → Suspend
- Integration Service: Balance-API `/api/billing/balance`, `/api/billing/topup`

**42. Automatisches Mahnwesen** — 3 PT (Orchestrator + Panel)
- Orchestrator: `vps_billing.py` erweitern:
  - Tag 0-3: Grace Period (Server läuft weiter)
  - Tag 3-7: Server gestoppt, Daten bleiben erhalten
  - Tag 7-14: Erste Mahnung (E-Mail + Discord DM)
  - Tag 14+: Server gelöscht, Backup in Cold Storage
- Management Panel: Liste überfälliger Zahlungen, manuelle Verlängerung

**43. Rabatt- und Gutscheincode-System** — 4 PT (Panel + Orchestrator + Integration)
- Orchestrator: `vps_pricing.py` erweitern um Coupon-Logik:
  - Typen: Prozent-Rabatt, Fixbetrag, kostenlose X Tage, kostenlose Ressourcenerweiterung
  - Einschränkungen: einmalig, zeitlich begrenzt, Mindestbestellwert
- Management Panel: Coupon-Admin-UI (Erstellen, Deaktivieren, Statistik)
- Integration Service: Coupon-Validierungs-API

**44. Affiliate-Programm** — 5 PT (Panel + Orchestrator + Integration)
- Orchestrator: Neues Cog `affiliate_manager.py` — Affiliate-Codes, Provision (z. B. 20 % des ersten Monats), Auszahlungsschwelle
- Management Panel: Affiliate-Dashboard (Codes, Klicks, Conversions, Guthaben)
- Integration Service: Affiliate-Tracking-API, Conversion-Tracking

**45. Multi-Währungs-Support** — 3 PT (Integration + Orchestrator + Panel)
- Integration Service: Währungsumrechnungs-API (fixe Wechselkurse oder via `exchangeratesapi.io`), EUR/USD/GBP als Basis
- Orchestrator: `config.py`-Pricing um Währungsfeld erweitern
- Management Panel: Währungs-Selector, Preise werden automatisch umgerechnet

**47. Server-Sharing / Transfer** — 4 PT (Orchestrator + Panel + Integration)
- Orchestrator: `server_migration.py` erweitern — Transfer zwischen User-Accounts: Container-Commit + Image-Export + Re-Import unter neuem Owner
- Management Panel: Transfer-UI (Ziel-User, Bestätigungsdialog)
- Integration Service: Transfer-API, Audit-Trail, Benachrichtigung beider Parteien

**48. Rechnungs-PDF-Generator** — 4 PT (Panel + Orchestrator + Integration)
- Management Panel: Bestehende `reports`-Export-Funktion nehmen, PDF-Vorlage für Rechnungen erstellen (umbuchbar, steuerkonform)
- Orchestrator: `vps_billing.py` um Rechnungsnummern, -daten und -historie erweitern
- Integration Service: PDF-Generierung (wkhtmltopdf oder weasyprint), E-Mail-Versand via SMTP

**49. Kostenlose Testphase (Trial)** — 3 PT (Orchestrator + Panel)
- Orchestrator: `vps_billing.py` erweitern:
  - Neuer User → 24h Trial-VPS (kleine Ressourcen)
  - Timer läuft, nach Ablauf → automatische Löschung oder Upgrade-Aufforderung
- Management Panel: Trial-Banner mit verbleibender Zeit, Upgrade-Button

**50. Verbrauchshistorie** — 2 PT (Panel + Orchestrator)
- Management Panel: Reports-Seite um Ressourcenverlauf-Diagramme erweitern (gebuchte vs. genutzte Ressourcen pro Monat)
- Orchestrator: `vps_statistics`-Daten über API bereitstellen

---

## Phasen-Zusammenfassung

| Phase | Fokus | Features | Aufwand (PT) |
|-------|-------|----------|-------------|
| Phase A (Woche 1-2) | Bestehendes verdrahten & Lücken schließen | 16, 20, 23, 24, 25, 26, 29, 32, 35, 39, 40, 46 | – (Bereits erledigt) |
| Phase B (Woche 3-5) | Gaming-Features & Config | 1, 2, 3, 6, 7, 8, 9, 10 | 31 PT |
| Phase C (Woche 6-8) | Sicherheit & Automatisierung | 11, 12, 13, 14, 17, 18, 21, 22, 27, 28, 30 | 37 PT |
| Phase D (Woche 9-11) | Monitoring & Billing (Basis) | 31, 33, 34, 36, 37, 38, 41, 42, 50 | 22 PT |
| Phase E (Woche 12-15) | Billing (Erweitert) & DDoS | 15, 19, 43, 44, 45, 47, 48, 49 | 32 PT |
| **Gesamt** | **50 Features** | | **~122 PT** |

### Abhängigkeiten zwischen Features

```
Phase B         Phase C          Phase D          Phase E
┌─────────┐    ┌─────────┐     ┌─────────┐     ┌─────────┐
│  1, 2   │───▶│ 11, 12  │────▶│ 31, 33  │────▶│ 43, 44  │
│  3, 6   │    │ 13, 14  │     │ 34, 36  │     │ 45, 47  │
│  7, 8   │    │ 17, 18  │     │ 37, 38  │     │ 48, 49  │
│  9, 10  │    │ 21, 22  │     │ 41, 42  │     │ 15, 19  │
└─────────┘    │ 27, 28  │     │ 50      │     └─────────┘
               │ 30      │     └─────────┘
               └─────────┘
```

- **Phase B** ist Grundvoraussetzung für C (da Config-Editor & Sub-Server-Netzwerke die Basis für Sicherheit und Automatisierung bilden)
- **Phase D** (Monitoring) kann parallel zu C starten, da unabhängige Services
- **Phase E** baut auf D auf (Billing-Basis → Erweiterte Billing-Features)
- **DDoS (15) und Malware-Scanner (19)** brauchen die Firewall (14) und Traffic-Analyse (15) aus Phase C

---

## Empfohlene Start-Reihenfolge (Top 10 nach ROI)

| Rang | Feature | Aufwand | Begründung |
|------|---------|---------|------------|
| 1 | **8. Config-Editor** | 4 PT | Ermöglicht Changes direkt im Panel statt SSH |
| 2 | **3. Discord-Token-Validierung** | 2 PT | Verhindert fehlerhafte Bot-Starts, einfache Implementierung |
| 3 | **9. MySQL per Klick** | 3 PT | Wichtig für Plugins, niedrige Komplexität |
| 4 | **10. Java-Version-Selector** | 3 PT | Häufigster Fehler beim Server-Setup |
| 5 | **11. 2FA (TOTP)** | 5 PT | Höchste Sicherheitswirkung |
| 6 | **33. Log-Suche** | 3 PT | Tägliches Debugging-Tool |
| 7 | **21. Cronjobs** | 3 PT | Ermöglicht Automatisierung aller weiteren Features |
| 8 | **22. Git-Deployment** | 4 PT | Entwickler-Workflow-Verbesserung |
| 9 | **31. Echtzeit-Ressourcen-Graphen** | 3 PT | Hoher Sichtbarkeitswert, baut auf Bestehendem auf |
| 10 | **41. Prepaid-Guthaben** | 4 PT | Geschäftsmodell-Grundlage |
