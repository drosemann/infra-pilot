# feature implementation plan — infra pilot

## übersicht

dieser plan deckt 50 features in 5 kategorien ab.
jedes feature wird einem service zugeordnet, der status des bereits vorhandenen bewertet und der implementierungsaufwand geschätzt.

### bewertungsschlüssel

| symbol | bedeutung |
|--------|-----------|
| done | vollständig implementiert |
| partial | teilweise vorhanden, erweiterung nötig |
| new | neu zu entwickeln |
| n/a | nicht zutreffend / entfällt |

## 1. gaming & bot-spezifische features

| # | feature | management panel | orchestrator agent | discord service | integration service | service core | status | aufwand |
|---|---------|:---:|:---:|:---:|:---:|:---:|--------|--------|
| 1 | modpack-installer mit 1-klick | ui + api | neues cog | – | curseforge/modrinth api | startup-integration | new | 5 pt |
| 2 | sub-server-netzwerke (bungeecord/velocity) | ui für netzwerk-config | neues cog (bungeecord-setup) | – | – | bungeecord-konfiguration | new | 6 pt |
| 3 | discord-bot token-validierung | backend-endpoint | – | validierungs-utility | validation api | – | partial | 2 pt |
| 4 | bot-uptime-keeper | – | neues cog (ping-service) | health-check-erweiterung | monitoring-aggregation | – | new | 4 pt |
| 5 | rcon-web-konsole | websocket-rcon-component | – | – | rcon-proxy-api | rcon-server-interface | new | 5 pt |
| 6 | spieler-statistiken-dashboard | live-statistik-ui | – | – | metrics-aggregation | playerstatistics existiert | partial | 4 pt |
| 7 | auto-plugin-updater | – | update_manager erweitern | – | – | plugin-update-mechanismus | partial | 4 pt |
| 8 | config-editor mit syntax-highlighting | monaco/codemirror-editor | – | – | config-read/write-api | config-dateien | new | 4 pt |
| 9 | mysql-datenbank per klick | ui für db-erstellung | neues cog (mysql-container) | – | db-provisioning-api | db-konfiguration | partial | 3 pt |
| 10 | custom java-version-selector | ui für java-version | docker-image-selektion | – | – | java-compat-check | new | 3 pt |

### details zu gaming-features

**1. modpack-installer** — 5 pt (orchestrator + panel + integration)
- orchestrator: neues cog `modpack_installer.py` — curseforge api (`api.curseforge.com`) und modrinth api (`api.modrinth.com`) abfragen, modpack-metadaten laden, docker-image mit modpack bauen
- management panel: neue seite "modpacks" mit suchleiste, kategorieselect, installationsbutton
- integration service: api-endpunkt `/api/modpacks/search`, `/api/modpacks/install` als proxy
- service core: startup-flag für modpack-pfad

**2. sub-server-netzwerke** — 6 pt (orchestrator + panel + core)
- orchestrator: neues cog `network_manager.py` — bungeecord/velocity-konfiguration automatisch generieren, server registrieren, waterfall/velocity-docker-image starten
- management panel: netzwerk-config-ui (server hinzufügen/entfernen, prioritäten, motd)
- service core: `config.yml` um network-sektion erweitern, pluginmessagelistener für bungeecord-kommunikation

**3. discord-bot token-validierung** — 2 pt (discord service + panel)
- discord service: `validatebottoken(token)` — mittels discord.js rest (`discord.js/rest`) prüfen, ob token gültig ist
- management panel: backend-endpoint `POST /api/validate/discord-token` ruft discord api auf, gibt guild-name und bot-name zurück

**4. bot-uptime-keeper** — 4 pt (orchestrator + integration)
- orchestrator: neues cog `uptime_keeper.py` — periodischer ping auf bot-websocket-endpoint, bei fehlender response: container-neustart via docker sdk, health-check-event an integration service
- integration service: uptime-statistiken sammeln, ausfall-historie, alert bei häufigem neustart

**5. rcon-web-konsole** — 5 pt (panel + integration + core)
- management panel: neue websocket-basierte rcon-konsole mit xterm.js oder eigener terminal-darstellung, farbige ausgabe
- integration service: `/api/rcon/connect` — rcon-proxy, der websocket-verbindungen zu minecraft-rcon-ports hält
- service core: `rcon.properties` generieren, rcon-port konfigurierbar

**6. spieler-statistiken-dashboard** — 4 pt (panel + integration + core)
- management panel: bestehenden `playercountchart` erweitern um: spielerliste, ping-anzeige, aktivste nutzer (nach spielzeit), tages-/wochenstatistik
- integration service: `unifiedmetrics` um spieler-metriken erweitern
- service core: `playerstatistics` mit ping-tracking ergänzen

**7. auto-plugin-updater** — 4 pt (orchestrator + core)
- orchestrator: cog `update_manager.py` erweitern — spigotmc api (`api.spigotmc.org`) und papermc api nach updates durchsuchen, download bei neuer version, plugin-jar im container austauschen, cron-job für nächtliche updates
- service core: konfiguration für erlaubte/nicht erlaubte auto-updates

**8. config-editor** — 4 pt (panel + integration)
- management panel: neue component mit monaco editor (`@monaco-editor/react`) oder codemirror, yaml/json-validierung (js-yaml), fehlermarkierung, speichern-button
- integration service: api-endpunkte `/api/config/:appId/read`, `/api/config/:appId/write` — config-dateien aus container lesen/schreiben

**9. mysql-datenbank per klick** — 3 pt (orchestrator + integration)
- orchestrator: cog `database_manager.py` — mysql-container via docker sdk starten, db-user und -passwort generieren, verbindungsdaten zurückgeben
- integration service: endpunkt `/api/databases/create` in resource tracker

**10. custom java-version-selector** — 3 pt (panel + orchestrator + core)
- management panel: dropdown für java 8, 11, 17, 21 in appform
- orchestrator: docker-image-name je nach java-version auswählen (z. b. `eclipse-temurin:17-jdk` vs `eclipse-temurin:21-jdk`)
- service core: `config.yml` um `java_version` erweitern

## 2. sicherheit & zugriffskontrolle

| # | feature | management panel | orchestrator agent | discord service | integration service | service core | status | aufwand |
|---|---------|:---:|:---:|:---:|:---:|:---:|--------|--------|
| 11 | 2fa (totp) | totp-setup/verify-ui | – | – | auth-erweiterung | – | new | 5 pt |
| 12 | sub-user-management | rbac-ui (bereits customers) | – | – | permissions.py erweitern | – | partial | 4 pt |
| 13 | ssh-key-manager | ui für ssh-keys | neues cog | – | key-storage-api | – | new | 4 pt |
| 14 | automatisierte firewall (ufw/iptables gui) | firewall-regel-ui | security_audit erweitern | – | firewall-api | – | new | 4 pt |
| 15 | ddos-traffic-analyse | live-traffic-charts | traffic_analysis.py erweitern | – | traffic-metrics-aggregation | – | partial | 4 pt |
| 16 | aktivitäts-logbuch (audit-log) | auditlog-seite existiert | – | – | auditlogger existiert | – | done | – |
| 17 | automatisches ip-whitelisting | ip-whitelist-ui | firewall-integration | – | whitelist-api | – | new | 3 pt |
| 18 | ssl-zertifikate per klick | ssl-status-ui | ssl_manager.py existiert | – | cert-status-api | – | partial | 2 pt |
| 19 | malware- & schadcode-scanner | upload-scan-ui | neues security-cog | – | scan-orchestrierung | – | new | 5 pt |
| 20 | isolierte umgebungen (docker/podman) | docker-integration | vps_manager.py (docker sdk) | – | – | – | done | – |

### details zu sicherheits-features

**11. 2fa (totp)** — 5 pt (panel + integration + discord)
- management panel: qr-code-setup (speichebene via `otpauth://` uri), verify-seite, backup-codes, "remember this device"-cookie
- integration service: `speakeasy` (node) oder `pyotp` (python) totp-validierung in `/api/auth/2fa/setup`, `/api/auth/2fa/verify`
- discord service: `verificationsystem.js` um 2fa-integration erweitern

**12. sub-user-management** — 4 pt (panel + integration)
- management panel: bestehende `customers`-seite um rbac erweitern — rollen (admin/editor/viewer/support), berechtigungsmatrix ("darf server neustarten", "darf dateien löschen"), einladungs-link
- integration service: `permissions.py` um sub-user-rollen, permission-inheritance, team-bereiche erweitern

**13. ssh-key-manager** — 4 pt (orchestrator + panel + integration)
- orchestrator: neues cog `ssh_key_manager.py` — ssh-keys in containern deployen (`~/.ssh/authorized_keys`), public-key-validierung, key-rotation
- management panel: ui zum hochladen/verwalten von public-keys
- integration service: key-storage-api (verschlüsselt), `/api/ssh-keys/crud`

**14. automatisierte firewall** — 4 pt (orchestrator + panel + integration)
- orchestrator: `security_audit.py` erweitern um ufw/iptables-regeln via `docker exec` — port-block/allow, regel-liste, regel-priorität
- management panel: firewall-regel-editor (port, protokoll, source-ip, aktion)
- integration service: firewall-state-persistierung, audit-trail

**15. ddos-traffic-analyse** — 4 pt (orchestrator + panel)
- orchestrator: `traffic_analysis.py` erweitern — bandbreiten-monitoring pro container, traffic-spitzen erkennen (≥3σ-abweichung), heatmap-diagramme
- management panel: live-traffic-charts (realtime via websocket), tages-/wochenansicht, alarm bei anomalie

**17. automatisches ip-whitelisting** — 3 pt (orchestrator + integration)
- orchestrator: ip-whitelist-regeln via iptables/ufw setzen, nur vordefinierte ips dürfen auf bestimmte ports
- integration service: `/api/security/whitelist` — crud für ip-whitelist-einträge

**19. malware-scanner** — 5 pt (orchestrator + integration + panel)
- orchestrator: neues cog `malware_scanner.py` — clamav via docker (`mkodockx/docker-clamav`) oder yara-regeln auf .jar/.py-dateien, scan-ergebnis auswerten
- management panel: upload-fenster mit fortschrittsbalken, ergebnis-anzeige
- integration service: scan-orchestrierung, quarantäne-management

## 3. automatisierung & devops

| # | feature | management panel | orchestrator agent | discord service | integration service | service core | status | aufwand |
|---|---------|:---:|:---:|:---:|:---:|:---:|--------|--------|
| 21 | geplante aufgaben (cronjobs) | maintenancescheduler existiert | background-tasks erweitern | node-cron existiert | announcement_scheduler.py | – | partial | 3 pt |
| 22 | git-deployment (webhook) | webhook-config-ui | neues cog (git-pull) | github-webhook-handler | webhook-api | – | new | 4 pt |
| 23 | automatisches backup-system | backupmanager existiert | backup_manager.py | – | backupmanager existiert | – | partial | 3 pt |
| 24 | auto-scaling bei last | – | auto_scaling.py existiert | – | resourcetracker erweitern | – | partial | 2 pt |
| 25 | template-system | ui für templates | template_manager.py | – | template-api | – | partial | 2 pt |
| 26 | api-zugriff (rest api) | 70+ endpoints + openapi | – | – | 80+ endpoints | – | done | – |
| 27 | auto-heal | – | health_checks.py + recovery.py | – | health-monitoring | – | partial | 3 pt |
| 28 | start-argumente-optimierer | jvm-flag-ui | performance_optimizer.py erweitern | – | – | jvm-config | new | 3 pt |
| 29 | ressourcen-limits (cgroups) | resource-ui in appform | vps_manager.py (docker) | – | – | – | done | – |
| 30 | ein-klick-os-reinstall | – | clone_system.py erweitern | – | reinstall-api | – | partial | 4 pt |

### details zu devops-features

**21. geplante aufgaben (cronjobs)** — 3 pt (panel + orchestrator + discord)
- management panel: bestehenden `maintenancescheduler` erweitern auf beliebige cron-jobs (server-restart, befehl, backup)
- orchestrator: background-task-scheduler (cron-ähnlich) in `main.py` — tasks aus db lesen, zu festgelegten zeiten ausführen
- discord service: `node-cron` in `index.js` für discord-interne aufgaben (cleanup, status-update)

**22. git-deployment (webhook)** — 4 pt (orchestrator + discord + panel)
- orchestrator: neues cog `git_deployer.py` — webhook empfangen (`/webhook/github`), git-pull im container, `npm install`/`pip install`, container-restart, rollback bei fehler
- discord service: github-webhook-event-handler (push, pull_request)
- management panel: ui zur konfiguration (repository, branch, deploy-command)

**23. automatisches backup-system** — 3 pt (alle services)
- bestehende backups (panel, orchestrator, integration) um externe speicherung erweitern:
  - aws s3 (boto3/botocore) oder s3-kompatibel (minio)
  - sftp (paramiko)
  - automatische retention (7 täglich, 4 wöchentlich, 3 monatlich)
- management panel: backup-ziel-konfiguration, manueller trigger

**24. auto-scaling bei last** — 2 pt (orchestrator + integration)
- orchestrator: vorhandenes `auto_scaling.py` mit metrics-integration abschließen — cpu/ram-schwellenwerte aus config.py verwenden, docker-update-api für neue limits
- integration service: `unifiedresourcetracker` mit scaling-events koppeln

**27. auto-heal** — 3 pt (orchestrator + integration)
- orchestrator: `health_checks.py` + `recovery.py` zu auto-heal-pipeline verbinden:
  1. health-check schlägt fehl → playbook ausführen
  2. playbook-stufen: container-neustart → host-reboot → admin-benachrichtigung
- integration service: health-status-dashboard, incident-timeline

**28. start-argumente-optimierer** — 3 pt (panel + orchestrator)
- management panel: ram-schieberegler (z. b. 1gb–32gb) → automatisch passende jvm-flags generieren
  - aikar's flags für minecraft (`-xx:+useg1gc`, `-xx:g1heapregionsize=4m`, etc.)
- orchestrator: `performance_optimizer.py` erweitern um jvm-flag-berechnung

**30. ein-klick-os-reinstall** — 4 pt (orchestrator + integration)
- orchestrator: `clone_system.py` erweitern — container löschen, neues image deployen, ssh-keys wiederherstellen, backup einspielen
- integration service: os-image-liste, reinstall-audit-trail

## 4. monitoring & analytics

| # | feature | management panel | orchestrator agent | discord service | integration service | service core | status | aufwand |
|---|---------|:---:|:---:|:---:|:---:|:---:|--------|--------|
| 31 | echtzeit-ressourcen-graphen | resourcechart etc. existieren | monitoring.py existiert | – | netdata/grafana-bridge | – | partial | 3 pt |
| 32 | discord/telegram-benachrichtigungen | – | – | – | notification_providers.py | – | done | – |
| 33 | log-dateien-suchfunktion | livelogs erweitern | – | – | unifiedlogger erweitern | – | partial | 3 pt |
| 34 | speicherplatz-warnung | – | alert thresholds existieren | – | alert-system erweitern | – | partial | 2 pt |
| 35 | ping- & latenz-tracker | – | network_monitor.py | – | – | – | done | – |
| 36 | kosten-live-kalkulator | – | cost_optimizer.py | – | – | – | partial | 2 pt |
| 37 | prozess-manager (htop-klon) | webterminal existiert | docker-exec-prozessliste | – | – | – | partial | 2 pt |
| 38 | uptime-statusseite | neue public-status-seite | health-endpoints | – | status-api | – | new | 4 pt |
| 39 | inaktivitäts-erkennung | – | – | – | – | inacityshutdowntask | done | – |
| 40 | historischer daten-export | reports (csv/pdf) | – | – | – | – | done | – |

### details zu monitoring-features

**31. echtzeit-ressourcen-graphen** — 3 pt (panel + integration)
- management panel: bestehende charts (resourcechart, performancechart) um folgende live-daten erweitern:
  - netdata-integration (`http://netdata:19999/api/v1/chart`) oder grafana-embed
  - websocket-basierte echtzeit-updates (alle 2s via bestehender ws-infrastruktur)
- integration service: metrics-bridge zu externen tools (netdata, grafana, prometheus)

**33. log-dateien-suchfunktion** — 3 pt (panel + integration)
- management panel: livelogs um suchleiste erweitern (filter nach "exception", "error", zeitraum, log-level)
- integration service: `unifiedlogger.search()` — volltextsuche in log-dateien, regex-unterstützung, pagination

**34. speicherplatz-warnung** — 2 pt (orchestrator + integration)
- orchestrator: bestehende disk-alert-config (90 %) mit monitoring-loop verbinden → event an integration service
- integration service: alert-regel prüfen, benachrichtigung via konfigurierte kanäle (email/webhook/telegram)

**36. kosten-live-kalkulator** — 2 pt (panel + orchestrator)
- management panel: kleine anzeige im dashboard "aktuelle kosten: €0.47/stunde"
- orchestrator: `cost_optimizer.py` + `cost_prediction.py` daten an panel-api übermitteln

**37. prozess-manager (htop-klon)** — 2 pt (panel + orchestrator)
- management panel: bestehende webterminal-integration nutzen, zusätzlich `docker exec <container> ps aux` als tabellenansicht
- orchestrator: `vps_manager.py` um `exec_in_container()` für prozess-listing erweitern

**38. uptime-statusseite** — 4 pt (panel + integration)
- management panel: neue public-seite (ohne auth) als subdomain oder `/status`-route
  - zeigt alle server-dienste mit status (grün/gelb/rot)
  - uptime-prozente, letzte incidents
  - stil wie cachet oder uptime kuma
- integration service: `/api/status` — aggregierte health-daten aller services

## 5. abrechnung & kundenverwaltung

| # | feature | management panel | orchestrator agent | discord service | integration service | service core | status | aufwand |
|---|---------|:---:|:---:|:---:|:---:|:---:|--------|--------|
| 41 | prepaid-guthaben-system | kundenkonto-ui | player_economy + billing | – | balance-api | economymanager existiert | partial | 4 pt |
| 42 | automatisches mahnwesen | ui für überfällige zahlungen | vps_billing.py erweitern | – | – | – | partial | 3 pt |
| 43 | rabatt- und gutscheincode-system | coupon-admin-ui | vps_pricing.py erweitern | – | coupon-api | – | new | 4 pt |
| 44 | affiliate-programm | affiliate-dashboard | neues billing-cog | – | affiliate-api | – | new | 5 pt |
| 45 | multi-währungs-support | währungs-selector | pricing-system erweitern | – | umrechnungs-api | – | new | 3 pt |
| 46 | ticket-support-system | – | – | ticketsystem.js | ticket-api-sync | – | done | – |
| 47 | server-sharing / transfer | transfer-ui | server_migration.py erweitern | – | transfer-api | – | partial | 4 pt |
| 48 | rechnungs-pdf-generator | reports für rechnungen | billing-log | – | pdf-gen-api | – | new | 4 pt |
| 49 | kostenlose testphase (trial) | trial-anzeige | vps_billing.py erweitern | – | trial-management | – | new | 3 pt |
| 50 | verbrauchshistorie | reports-seite erweitern | vps_statistics existiert | – | – | – | partial | 2 pt |

### details zu billing-features

**41. prepaid-guthaben-system** — 4 pt (panel + orchestrator + integration)
- management panel: kundenkonto-seite mit guthaben-anzeige, auflade-button, zahlungsmethoden (paypal/stripe)
- orchestrator: `player_economy` und `vps_billing.py` verbinden — guthaben wird stündlich abgebucht, bei 0-guthaben → suspend
- integration service: balance-api `/api/billing/balance`, `/api/billing/topup`

**42. automatisches mahnwesen** — 3 pt (orchestrator + panel)
- orchestrator: `vps_billing.py` erweitern:
  - tag 0-3: grace period (server läuft weiter)
  - tag 3-7: server gestoppt, daten bleiben erhalten
  - tag 7-14: erste mahnung (e-mail + discord dm)
  - tag 14+: server gelöscht, backup in cold storage
- management panel: liste überfälliger zahlungen, manuelle verlängerung

**43. rabatt- und gutscheincode-system** — 4 pt (panel + orchestrator + integration)
- orchestrator: `vps_pricing.py` erweitern um coupon-logik:
  - typen: prozent-rabatt, fixbetrag, kostenlose x tage, kostenlose ressourcenerweiterung
  - einschränkungen: einmalig, zeitlich begrenzt, mindestbestellwert
- management panel: coupon-admin-ui (erstellen, deaktivieren, statistik)
- integration service: coupon-validierungs-api

**44. affiliate-programm** — 5 pt (panel + orchestrator + integration)
- orchestrator: neues cog `affiliate_manager.py` — affiliate-codes, provision (z. b. 20 % des ersten monats), auszahlungsschwelle
- management panel: affiliate-dashboard (codes, klicks, conversions, guthaben)
- integration service: affiliate-tracking-api, conversion-tracking

**45. multi-währungs-support** — 3 pt (integration + orchestrator + panel)
- integration service: währungsumrechnungs-api (fixe wechselkurse oder via `exchangeratesapi.io`), eur/usd/gbp als basis
- orchestrator: `config.py`-pricing um währungsfeld erweitern
- management panel: währungs-selector, preise werden automatisch umgerechnet

**47. server-sharing / transfer** — 4 pt (orchestrator + panel + integration)
- orchestrator: `server_migration.py` erweitern — transfer zwischen user-accounts: container-commit + image-export + re-import unter neuem owner
- management panel: transfer-ui (ziel-user, bestätigungsdialog)
- integration service: transfer-api, audit-trail, benachrichtigung beider parteien

**48. rechnungs-pdf-generator** — 4 pt (panel + orchestrator + integration)
- management panel: bestehende `reports`-export-funktion nehmen, pdf-vorlage für rechnungen erstellen (umbuchbar, steuerkonform)
- orchestrator: `vps_billing.py` um rechnungsnummern, -daten und -historie erweitern
- integration service: pdf-generierung (wkhtmltopdf oder weasyprint), e-mail-versand via smtp

**49. kostenlose testphase (trial)** — 3 pt (orchestrator + panel)
- orchestrator: `vps_billing.py` erweitern:
  - neuer user → 24h trial-vps (kleine ressourcen)
  - timer läuft, nach ablauf → automatische löschung oder upgrade-aufforderung
- management panel: trial-banner mit verbleibender zeit, upgrade-button

**50. verbrauchshistorie** — 2 pt (panel + orchestrator)
- management panel: reports-seite um ressourcenverlauf-diagramme erweitern (gebuchte vs. genutzte ressourcen pro monat)
- orchestrator: `vps_statistics`-daten über api bereitstellen

## phasen-zusammenfassung

| phase | fokus | features | aufwand (pt) |
|-------|-------|----------|-------------|
| phase a (woche 1-2) | bestehendes verdrahten & lücken schließen | 16, 20, 23, 24, 25, 26, 29, 32, 35, 39, 40, 46 | – (bereits erledigt) |
| phase b (woche 3-5) | gaming-features & config | 1, 2, 3, 6, 7, 8, 9, 10 | 31 pt |
| phase c (woche 6-8) | sicherheit & automatisierung | 11, 12, 13, 14, 17, 18, 21, 22, 27, 28, 30 | 37 pt |
| phase d (woche 9-11) | monitoring & billing (basis) | 31, 33, 34, 36, 37, 38, 41, 42, 50 | 22 pt |
| phase e (woche 12-15) | billing (erweitert) & ddos | 15, 19, 43, 44, 45, 47, 48, 49 | 32 pt |
| **gesamt** | **50 features** | | **~122 pt** |

### abhängigkeiten zwischen features

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

- phase b ist grundvoraussetzung für c (da config-editor & sub-server-netzwerke die basis für sicherheit und automatisierung bilden)
- phase d (monitoring) kann parallel zu c starten, da unabhängige services
- phase e baut auf d auf (billing-basis → erweiterte billing-features)
- ddos (15) und malware-scanner (19) brauchen die firewall (14) und traffic-analyse (15) aus phase c

## empfohlene start-reihenfolge (top 10 nach roi)

| rang | feature | aufwand | begründung |
|------|---------|---------|------------|
| 1 | 8. config-editor | 4 pt | ermöglicht changes direkt im panel statt ssh |
| 2 | 3. discord-token-validierung | 2 pt | verhindert fehlerhafte bot-starts, einfache implementierung |
| 3 | 9. mysql per klick | 3 pt | wichtig für plugins, niedrige komplexität |
| 4 | 10. java-version-selector | 3 pt | häufigster fehler beim server-setup |
| 5 | 11. 2fa (totp) | 5 pt | höchste sicherheitswirkung |
| 6 | 33. log-suche | 3 pt | tägliches debugging-tool |
| 7 | 21. cronjobs | 3 pt | ermöglicht automatisierung aller weiteren features |
| 8 | 22. git-deployment | 4 pt | entwickler-workflow-verbesserung |
| 9 | 31. echtzeit-ressourcen-graphen | 3 pt | hoher sichtbarkeitswert, baut auf bestehendem auf |
| 10 | 41. prepaid-guthaben | 4 pt | geschäftsmodell-grundlage |
