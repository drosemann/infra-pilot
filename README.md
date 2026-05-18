# 🚀 Infra Pilot

**Infrastructure-Orchestration und Docker-Management für Self-Hosting, Demo-Umgebungen und Provider-neutrale Provisioning-Flows.**

Infra Pilot bündelt mehrere Services und Hilfsbibliotheken, um Container-/Game-Server-Verwaltung, Discord-gesteuerte Provisionierung, Provider-neutrale Testdaten und ein modernes Management-Panel in einem Repository zu entwickeln.

> **Orchestrate. Automate. Scale.**

## Inhaltsverzeichnis

- [Aktueller Projektstatus](#aktueller-projektstatus)
- [Quick Start](#quick-start)
- [Repository-Struktur](#repository-struktur)
- [Services](#services)
- [Konfiguration](#konfiguration)
- [Development & Testing](#development--testing)
- [Docker & Deployment](#docker--deployment)
- [Dokumentation](#dokumentation)
- [Security](#security)
- [Contributing](#contributing)
- [License & Warranty](#license--warranty)

## Aktueller Projektstatus

- ✅ **Management Panel:** React/Vite-Frontend mit Express-API, Personal Mode, optionalem Business Mode, Supabase/PostgreSQL-Anbindung und Seed-Demo-Feature-Gate.
- ✅ **Orchestrator Agent:** Python-Service mit Discord-/VPS-Provisioning-Komponenten, Provider-neutraler Namensauflösung und eigenen Tests.
- ✅ **Discord Service:** Node.js/Discord.js-Integration für Pterodactyl-/Provisioning-Flows.
- ✅ **Provider-neutrales Test-Framework:** Token-Mapping unter `infra/naming/` und Tests unter `tests/`.
- ⚠️ **Docker Compose:** `docker-compose.yml` ist als Stack-Scaffold vorhanden. Aktuell besitzt nur `services/orchestrator-agent/` ein Dockerfile; die Compose-Definitionen für Management Panel, Discord Service, Service Core und Monitoring benötigen vor einem vollständigen Stack-Start noch Dockerfiles bzw. Infrastrukturdateien.
- ⚠️ **Kubernetes/Terraform:** Die README verweist nicht mehr auf produktionsfertige K8s-/Terraform-Manifeste, weil entsprechende `infrastructure/`-Dateien derzeit nicht im Repository enthalten sind.

## Quick Start

### Option 1: Management Panel lokal starten (empfohlen)

```bash
git clone https://github.com/DaaanielTV/infra-pilot.git
cd infra-pilot/services/management-panel
npm install
cat > .env.local <<'ENV'
VITE_API_URL=http://localhost:3001
VITE_SUPABASE_URL=http://localhost:54321
VITE_SUPABASE_ANON_KEY=test-anon-key
VITE_DEMO_FEATURE_ENABLED=false
ENV
npm run dev
```

Danach öffnen:

- Frontend: <http://localhost:5173>
- Backend-API: <http://localhost:3001>
- Health Check: <http://localhost:3001/health>

Weitere Details: [Management Panel README](services/management-panel/README.md) und [Docker Panel Quick Start](services/management-panel/README-DOCKER-PANEL.md).

### Option 2: Orchestrator Agent lokal starten

```bash
git clone https://github.com/DaaanielTV/infra-pilot.git
cd infra-pilot/services/orchestrator-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python bot.py
```

Weitere Details: [Orchestrator Agent README](services/orchestrator-agent/README.md).

### Option 3: Discord Service prüfen

```bash
git clone https://github.com/DaaanielTV/infra-pilot.git
cd infra-pilot/services/discord-service
cp .env.example .env
# .env mit Discord- und Pterodactyl-Werten befüllen
node --check index.js
```

Hinweis: Der Discord Service enthält aktuell Quellcode und `.env.example`, aber kein eigenes `package.json`. Für einen produktiven Start müssen die Node-Abhängigkeiten (`discord.js`, `axios`, `dotenv`) zuerst über ein Service-Manifest ergänzt oder in einer übergeordneten Umgebung bereitgestellt werden.

Weitere Details: [Discord Service README](services/discord-service/README.md).

## Voraussetzungen

| Bereich | Voraussetzung |
| --- | --- |
| Allgemein | Git, Bash-kompatible Shell |
| Management Panel | Node.js 18+, npm |
| Orchestrator Agent | Python 3.9+, pip, optional pytest |
| Discord Service | Node.js 18+, npm, Discord-Bot, Pterodactyl-API-Zugang |
| Service Core | Java/Maven, sofern `services/service-core` genutzt oder erweitert wird |
| Optional | Docker, Docker Compose, Zig 0.16.0+ und zero-native CLI für die native Desktop-Shell |

## Repository-Struktur

```text
.
├── README.md                         # Hauptdokumentation
├── LICENSE                           # MIT License
├── docker-compose.yml                # Compose-Scaffold für den späteren Stack-Ausbau
├── infra/naming/                     # Provider-neutrale Token-Auflösung
├── scripts/                          # Setup-, Test-, Coverage- und Build-Hilfen
├── services/
│   ├── management-panel/             # React/Vite + Express Docker Panel
│   ├── orchestrator-agent/           # Python Provisioning-/Discord-Agent
│   ├── discord-service/              # Discord.js Bot Service
│   ├── integration-service/          # Integrationsnotizen und Requirements
│   └── service-core/                 # Java/Maven Service-Core-Skeleton
├── tests/                            # Repo-weite Unit-/Integration-/Smoke-Tests
└── docs/                             # Projekt-, Architektur-, Testing- und Operations-Doku
```

## Services

### Management Panel (`services/management-panel/`)

Modernes Docker-Management-Panel für Self-Hoster und Hosting-Workflows.

- **Stack:** React 19, TypeScript, Vite, Tailwind CSS, Express.js, Supabase/PostgreSQL.
- **Modi:** Personal Mode als Standard, Business Mode für Kunden-, Plan- und Demo-Datenflüsse.
- **Features:** App-/Container-CRUD, Logs, Ressourcenlimits, Setup-Flow, Seed Demo Feature Gate, optionale zero-native Desktop-Shell.
- **Wichtige Skripte:**
  - `npm run dev` startet Frontend und Backend parallel.
  - `npm run dev:frontend` startet nur Vite.
  - `npm run dev:backend` startet nur die Express-API.
  - `npm run test`, `npm run test:unit`, `npm run test:api` führen Node-Test-Suites aus.
  - `npm run lint` führt den TypeScript-Check aus.

### Orchestrator Agent (`services/orchestrator-agent/`)

Python-basierte Provisioning- und Orchestrierungslogik.

- **Stack:** Python 3.9+, Discord.py/aiohttp-Umfeld laut Requirements.
- **Features:** VPS-Management, Billing-/Pricing-Cogs, Ressourcenmonitoring, Integration Hooks.
- **Docker:** Enthält aktuell ein Dockerfile und ist damit der einzige Service, der im Repository direkt als Image gebaut werden kann.

### Discord Service (`services/discord-service/`)

Discord.js-Service für Pterodactyl-nahe Server-Erstellungsflüsse.

- **Stack:** Node.js 18+, CommonJS, Discord.js/Axios/Dotenv als erwartete Runtime-Abhängigkeiten.
- **Features:** `/server create`-Flow, Pterodactyl-User-/Server-Erstellung, Rollen-/Limit-Konfiguration.
- **Konfiguration:** siehe `services/discord-service/.env.example`.
- **Status:** Ein eigenes `package.json` fehlt derzeit; vor dem Betrieb muss ein Dependency-Manifest ergänzt werden.

### Service Core (`services/service-core/`)

Java/Maven-Skeleton für Core-Service-Funktionalität. Das Verzeichnis enthält derzeit primär `pom.xml`; eine eigene Service-Dokumentation und Dockerisierung sind noch ausstehend.

## Provider-neutrales Token-System

Provider-spezifische Identitäten werden über neutrale Tokens abstrahiert. Das erleichtert Tests, Demos und Providerwechsel.

```yaml
# infra/naming/provider_map.yaml
PROVIDER_MOCK: mock-provider
AWS_EC2: aws
GCP_COMPUTE: gcp
REGION_MOCK_US_EAST: mock-us-east
SKU_MOCK_SMALL: mock-small
```

Beispiel in Python:

```python
from infra.naming.resolver import resolve_token

provider = resolve_token("PROVIDER_MOCK")  # "mock-provider"
```

Weitere Informationen: [Provider Neutral Mapping](docs/testing/provider_neutral_mapping.md).

## Konfiguration

### Root-Konfiguration

- `.env.example` enthält eine repo-weite Vorlage für Datenbank-, Redis-, Discord-, Orchestrator- und Frontend-Variablen.
- Für lokale Secrets immer `.env` oder service-spezifische `.env.local`-Dateien nutzen und niemals echte Zugangsdaten committen.

### Management Panel

Minimalwerte für lokale Entwicklung:

```env
VITE_API_URL=http://localhost:3001
VITE_SUPABASE_URL=http://localhost:54321
VITE_SUPABASE_ANON_KEY=test-anon-key
VITE_DEMO_FEATURE_ENABLED=false
```

`VITE_DEMO_FEATURE_ENABLED=true` zeigt Demo-Seeding-Funktionen in der UI an. Für produktionsähnliche Umgebungen sollte der Wert `false` bleiben.

### Discord Service

Die benötigten Variablen sind in [services/discord-service/.env.example](services/discord-service/.env.example) dokumentiert, insbesondere:

- `DISCORD_TOKEN`
- `PTERODACTYL_API_URL`
- `PTERODACTYL_API_KEY`
- Channel-, Rollen-, Egg- und Location-IDs

## Development & Testing

### Häufige Befehle

```bash
# Repo-weite Tests über Script
./scripts/test.sh

# Offline-Verifikation ohne Maven-Netzwerkannahmen
make verify-offline

# Python-Tests im Root-Kontext
pytest

# Management Panel
cd services/management-panel
npm run lint
npm run test

# Orchestrator Agent
cd services/orchestrator-agent
pytest tests/
```

### Testdokumentation

- [Testing Overview](docs/TESTING.md)
- [Running Tests](docs/testing/running_tests.md)
- [Automated Test Suite](docs/testing/automated-test-suite.md)
- [Test Plan](docs/testing/test_plan.md)
- [CI Demo Gate](docs/CI_DEMO_GATE.md)

### Code- und Workflow-Dokumentation

- [Development Workflow](docs/development/development-workflow.md)
- [Code Standards](docs/development/code-standards.md)
- [CI Architecture](docs/development/ci-architecture.md)
- [AI Assistant Playbook](docs/development/ai-assistant-playbook.md)

## Docker & Deployment

### Aktueller Stand

- `scripts/docker-build.sh` überspringt Services ohne Dockerfile automatisch.
- Aktuell besitzt `services/orchestrator-agent/` ein Dockerfile.
- `docker-compose.yml` beschreibt den Ziel-Stack mit PostgreSQL, Redis, Service Core, Orchestrator, Discord Service, Management Panel und optionalem Monitoring, ist aber ohne zusätzliche Dockerfiles/Monitoring-Konfiguration noch nicht als vollständiger Ein-Befehl-Stack nutzbar.

### Aktuell sinnvoller Docker-Befehl

```bash
./scripts/docker-build.sh
```

Der Befehl baut vorhandene Service-Images und meldet fehlende Dockerfiles als Warnung.

### Deployment-Dokumentation

- [Deployment Guide](docs/operations/deployment-guide.md)
- [Workflow Optimization Audit](docs/operations/workflow-optimization-audit.md)
- [Local Development Setup](docs/setup/local-development.md)
- [zero-native Management Panel](docs/desktop/zero-native-management-panel.md)

## Dokumentation

Der zentrale Dokumentationsindex liegt unter [docs/README.md](docs/README.md).

### Wichtige Einstiege

- [Quickstart](docs/quickstart.md)
- [Architecture Overview](docs/architecture/overview.md)
- [Orchestrator Agent Architecture](docs/architecture/orchestrator-agent.md)
- [Management Panel README](services/management-panel/README.md)
- [Discord Service README](services/discord-service/README.md)
- [Integration Service README](services/integration-service/README.md)
- [Branding Guidelines](docs/branding-guidelines.md)
- [Design System](docs/design-system.md)
- [Design Tokens](docs/design-tokens.md)

## Security

- Sicherheitsmeldungen bitte gemäß [SECURITY.md](SECURITY.md) einreichen.
- Produktive Umgebungen sollten echte Secrets ausschließlich über geeignete Secret Stores oder Deployment-Variablen bereitstellen.
- Demo-Seeding (`VITE_DEMO_FEATURE_ENABLED`) in produktionsähnlichen Umgebungen deaktiviert lassen.
- Vor produktiver Nutzung Dockerfiles, Compose-/Monitoring-Dateien, Authentifizierung, TLS, Backups und Berechtigungen gezielt härten.

## Contributing

Beiträge sind willkommen. Bitte vorab lesen:

- [CONTRIBUTING.md](CONTRIBUTING.md)
- [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)
- [Code Standards](docs/development/code-standards.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)

Kurzablauf:

```bash
git checkout -b feature/my-feature
# Änderungen vornehmen und testen
git commit -m "feat: describe change"
git push origin feature/my-feature
```

## License & Warranty

### License

Dieses Projekt ist unter der **MIT License** lizenziert. Details stehen in [LICENSE](LICENSE).

### Warranty & Liability

⚠️ Diese Software wird ohne Gewährleistung bereitgestellt.

- Die MIT License enthält den vollständigen Haftungsausschluss.
- Testen Sie Änderungen gründlich, bevor Sie Infra Pilot in produktionsnahen Umgebungen einsetzen.
- Betreiber sind selbst dafür verantwortlich, Secrets, Provider-Zugänge, Discord-Bots, Datenbanken und Deployments sicher zu konfigurieren.

---

**[⬆ Zurück nach oben](#-infra-pilot)**
