# Infra-Pilot

**Infrastruktur orchestrieren. Automatisieren. Skalieren.**

Infra-Pilot ist ein modulares Orchestrierungs-Framework, das dir hilft, Container, Cloud-Ressourcen und Game-Server über ein einheitliches CLI, Dashboard oder Discord zu verwalten – egal ob auf AWS, Azure, GCP, Hetzner oder lokal.

## Quick Start in 4 Befehlen

```bash
git clone https://github.com/DaaanielTV/infra-pilot.git
cd infra-pilot
cp .env.example .env
docker compose up -d
```

Danach erreichst du:
- **Management Panel**: http://localhost:5173
- **API**: http://localhost:3001
- **Orchestrator Health**: http://localhost:8500/health

## Key Features

- **Multi-Cloud Orchestrierung** – Einheitliche API für AWS, Azure, GCP, Hetzner, DigitalOcean und mehr
- **200+ CLI-Befehle** – Infrastruktur komplett über die Kommandozeile steuern (Server, DNS, VPN, Backup, FinOps, ...)
- **Discord-Integration** – Server provisionieren und verwalten direkt aus Discord
- **Green Computing** – Energieverbrauch tracken, CO₂ kompensieren, nachhaltige Provider ranken

## Nächste Schritte

| Seite | Inhalt |
|-------|--------|
| [01-Installation](01-Installation) | Setup für Windows, macOS, Linux + alle Dependencies |
| [02-First-Deployment](02-First-Deployment) | Deploy einen Server in 3 Minuten |
| [04-Usage-Examples](04-Usage-Examples) | 5 reale Use-Cases mit Code |
| [07-Contributing](07-Contributing) | Dev Setup, Tests, PR-Guide |

---

*Stand: Mai 2026 · [GitHub](https://github.com/daaanieltv/infra-pilot) · [MIT License](https://github.com/daaanieltv/infra-pilot/blob/main/LICENSE)*
