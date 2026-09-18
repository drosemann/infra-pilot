# Infra Pilot

[[CI](https://github.com/drosemann/infra-pilot/actions/workflows/ci.yml/badge.svg)](https://github.com/drosemann/infra-pilot/actions/workflows/ci.yml)
[[Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org)
[[License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

> Lernprojekt und Basis für meine zukünftige Hosting-Plattform: Verwaltung von Docker-basierter Infrastruktur über Python CLI, React/Express Panel und optionaler Discord-Integration.

### Entstehung

Ursprünglich gestartet als `dmh-hosting` am 09.03.2025 – erster Commit nur `README.md` mit `# dmh-hosting`. Die Idee kam aus dem DMH Network (Jan-Apr 2025).

Wir haben uns dann bewusst gegen Public Hosting entschieden: Zu viel Ärger mit Abuse, Cyberkriminellen, Fraud und Support-Aufwand für ein kleines Team. Stattdessen wurde daraus `infra-pilot` – kein Hoster für andere mehr, sondern ein internes Tool um eigene VPS & Gameserver schlank zu verwalten. Weg von Pterodactyl/Coolify, hin zu purem Docker.

Entstanden in meiner Ausbildung zum FISI.

## Komponenten

| Komponente | Runtime | Standard-Endpunkt | Aufgabe |
|---|---|---:|---|
| Management Panel | React + Express | UI `:5173`, API `:3001` | Container-Steuerung, Panel-APIs, OpenAPI und Swagger UI |
| Orchestrator Agent | Python/aiohttp | `:8500` | Health/Metriken, GitOps Webhooks, Manifest-Abgleich |
| PostgreSQL / Redis | Docker Images | `:5432` / `:6379` | Persistente Daten / Cache |
| Discord Service (optional) | Node.js | `:3002` | Discord & Pterodactyl Integration |
| Prometheus / Grafana (optional) | Docker Images | `:9090` / `:3000` | Metriken & Dashboards |

## Schnellstart

```bash
git clone https://github.com/drosemann/infra-pilot.git
cd infra-pilot
cp .env.example .env
bash scripts/generate-env.sh
docker compose up -d
```

Danach `http://localhost:5173` öffnen.

### Nur CLI
```bash
pip install ./cli
ipilot --help
```

## Sicherheitshinweise
Compose benötigt `POSTGRES_PASSWORD`, `GITOPS_WEBHOOK_TOKEN` und `FEDERATION_API_TOKEN`. Der Discord-Service mountet den Docker-Socket – nur in vertrauenswürdiger Umgebung laufen lassen.

## Lizenz
MIT
