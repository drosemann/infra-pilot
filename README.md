# 🚀 Infra Pilot

**Infrastructure Orchestration & Management Platform**

## 📌 Overview

**Infra Pilot** ist eine umfassende Infrastructure-Orchestration-Plattform, die es Entwicklern und DevOps-Teams ermöglicht, komplexe Multi-Cloud-Infrastrukturen automatisiert zu verwalten. Das System provisioner Spielserver, verwaltet VPS-Lebenszyklen und orchestriert Ressourcen über Discord, Web-Dashboards und RESTful APIs.

> **Orchestrate. Automate. Scale.**

### 🎯 Kernfähigkeiten

- 🎮 **Spielserver-Management** - Automatisierte Provisioning, Skalierbarkeit und Lebenszyklusmanagement mit erweiterten Konfigurationsoptionen
- ☁️ **VPS-Orchestrierung** - Multi-Cloud-Ressourcenbereitstellung über AWS, GCP, Azure und weitere Provider mit neutralem Token-System
- 💬 **Discord Integration** - Native Bot-Befehle für Infrastruktur-Operationen mit fortgeschrittenen Berechtigungen
- 🎛️ **Web Dashboard** - Modernes Management-Panel mit persönlichem und geschäftlichem Modus (Business Mode)
- 🔌 **API-First Architektur** - Umfassende REST APIs für benutzerdefinierte Integrationen und Automatisierung
- 📊 **Observability** - Request-Instrumentation, Metriken-Endpunkte und erweiterte Health-Checks
- 🔐 **Enterprise-Ready** - SSL/TLS-Unterstützung, rollenbasierte Zugriffskontrolle (RBAC), Audit-Logging
- 🌐 **Provider-Neutral Design** - Abstraktion von Cloud-Provider-Spezifika durch standardisierte Naming-Konventionen
- 🚀 **Seed Demo System** - 1-Click-Demo-Szenarien mit reserviertem Seed-Datenmanagement für QA und Vorführungen

---

## 📋 Inhaltsverzeichnis

- [Quick Start](#quick-start)
- [Architektur & Design](#architektur--design)
- [Services](#services)
- [Installation](#installation)
- [Development & Testing](#development--testing)
- [Dokumentation](#dokumentation)
- [Workflows & Use Cases](#workflows--use-cases)
- [Deployment-Optionen](#deployment-optionen)
- [Security & Monitoring](#security--monitoring)
- [Contributing](#contributing)
- [License & Warranty](#license--warranty)

---

## 🚀 Quick Start

### Schnellstartoptionen

#### Option 1: Docker Panel (Empfohlen für Anfänger) 🆕

Das Docker Panel ist ein modernes, selbstgehostetes Docker-Management-Interface mit **Personal Mode für Self-Hoster** und optionalen Business Mode Features.

```bash
cd services/management-panel

# 1. Environment-Vorlage kopieren
cp .env.local.example .env.local

# 2. Abhängigkeiten installieren
npm install

# 3. Frontend + Backend starten (beide)
npm run dev
```

Dann öffnen Sie: **http://localhost:5173**
- API läuft auf: **http://localhost:3001**
- **Erste Schritte?** Siehe [Docker Panel Quick Start](services/management-panel/README-DOCKER-PANEL.md)

#### Option 2: Docker Compose (Alle Services)

```bash
# Repository klonen
git clone https://github.com/DaaanielTV/infra-pilot.git
cd infra-pilot

# Alle Services starten
docker-compose up -d

# Logs anzeigen
docker-compose logs -f
```

Verfügbare Services:
- **Docker Panel**: http://localhost:5173 (Personal Mode standardmäßig)
- **Docker Panel API**: http://localhost:3001
- **Discord Service**: Bereit für Webhook-Integration
- **Service Core**: http://localhost:8080
- **Orchestrator API**: http://localhost:8000

#### Option 3: Lokale Entwicklung (Alle Services)

```bash
# Klonen und Setup
git clone https://github.com/DaaanielTV/infra-pilot.git
cd infra-pilot

# Setup-Skript ausführen
./scripts/setup.sh

# Services einzeln starten
cd services/service-core && mvn spring-boot:run &
cd services/orchestrator-agent && python main.py &
cd services/discord-service && npm start &
cd services/management-panel && npm run dev
```

#### Option 4: Kubernetes Deployment

```bash
# Manifeste anwenden
kubectl apply -f infrastructure/kubernetes/namespace.yaml
kubectl apply -f infrastructure/kubernetes/deployments/

# Port-forwarding für Zugriff
kubectl port-forward -n infra-pilot svc/management-panel 5173:80
```

Siehe [docs/setup/local-development.md](docs/setup/local-development.md) für detaillierte Anweisungen.

### 📋 Voraussetzungen

- Docker & Docker Compose (empfohlen) - v20.10+
- Node.js 18+ (für Docker Panel und Discord Service)
- Python 3.9+ (für Orchestrator Agent)
- Java 8+ (für Service Core)
- Git
- 4GB RAM Minimum (8GB empfohlen)

---

## 🏗️ Architektur & Design

### System-Design

```
┌────────────────────────────────────────────────────────┐
│              User Interfaces Layer                      │
│  Discord Bot | Web Dashboard | REST APIs | Webhooks   │
└────────────────┬─────────────────────────────────────┘
                 │
         ┌───────▼────────────────┐
         │  Orchestrator Agent    │ ◄── Zentrale Orchestrierungslogik
         │  (Python 3.9+)         │
         │  • Provisioning        │
         │  • Resource Allocation │
         │  • Billing Engine      │
         └───────┬────────────────┘
                 │
    ┌────────────┴────────────────┐
    │                             │
┌───▼─────────────┐      ┌────────▼──────────┐
│  Service Core   │      │  External APIs    │
│  (Java 8+)      │      │  • AWS            │
│  • Game Server  │      │  • GCP            │
│  • Lifecycle    │      │  • Azure          │
│  • Tracking     │      │  • Custom         │
└───┬─────────────┘      └─────────────────┘
    │
┌───▼────────────────────────────────────────┐
│     Data & Infrastructure Layer             │
│  PostgreSQL | Redis | File Storage | Logs  │
└─────────────────────────────────────────────┘
```

### Provider-Neutral Token System

Das System nutzt ein Token-basiertes System zur Abstraktion von Cloud-Provider-Spezifika:

```yaml
# Beispiel: Neutral Tokens
PROVIDER_MOCK, AWS_EC2, GCP_COMPUTE, AZURE_VM
REGION_MOCK_US_EAST, AWS_US_EAST_1, GCP_US_CENTRAL1
SKU_MOCK_SMALL, AWS_T3_MICRO, GCP_E2_MICRO

# Resolver-Mapping
infra/naming/provider_map.yaml:
  PROVIDER_MOCK: mock-provider
  AWS_EC2: aws
  GCP_COMPUTE: gcp
```

### Service-Übersicht

| Service | Zweck | Sprache | Port | Status |
|---------|--------|---------|------|--------|
| **Management Panel** | Docker Container Management & Dashboard | TypeScript/React + Express | 5173/3001 | Production Ready |
| **Orchestrator Agent** | Zentrale Provisioning & Orchestrierung | Python 3.9+ | 8000 | Production Ready |
| **Discord Service** | Discord Bot Interface | Node.js | - | Production Ready |
| **Service Core** | Spielserver & Ressourcenmanagement | Java 8+ | 8080 | Production Ready |

Siehe [docs/architecture/overview.md](docs/architecture/overview.md) für detaillierte Architektur-Dokumentation.

---

## 📦 Services

### 1. Management Panel (`services/management-panel/`)
Modernes Web-basiertes Docker Container Management Interface mit persönlichem und geschäftlichem Modus.

- **Tech Stack:** React 19, TypeScript 5.0+, Tailwind CSS 4, Express.js, Supabase/PostgreSQL
- **Features:**
  - **Personal Mode** (Standard): Vereinfachtes Docker-Management für Einzelnutzer
  - **Business Mode** (Optional): Multi-User, Abrechnung, White-Label, Team-Management
  - Docker App Erstellung & Management
  - Container-Status-Überwachung
  - Log-Viewing und Fehlerdiagnose
  - Ressourcen-Allokation und Limitierung
  - Seed Demo System für Demonstrationen
  - Kunde CRUD + RLS (Business Mode)

- **Setup:** 
  ```bash
  cd services/management-panel
  npm install
  npm run dev
  ```

- **Umgebungsvariablen:**
  ```
  VITE_DEMO_FEATURE_ENABLED=true|false
  VITE_API_URL=http://localhost:3001
  VITE_SUPABASE_URL=your-url
  VITE_SUPABASE_ANON_KEY=your-key
  ```

- **Doku:** [services/management-panel/README.md](services/management-panel/README.md)
- **Datenbank:** Siehe [services/management-panel/docs/DATABASE_SETUP.md](services/management-panel/docs/DATABASE_SETUP.md)

### 2. Orchestrator Agent (`services/orchestrator-agent/`)
Zentrale Provisioning- und Orchestrierungs-Engine mit Provider-Abstraktion.

- **Tech Stack:** Python 3.9+, Discord.py, aiohttp, Async-Patterns
- **Kernfunktionen:** 
  - VPS-Provisioning über mehrere Cloud-Provider
  - Ressourcen-Allokation und Autoscaling
  - Billing-Integration und Kostenberechnung
  - Webhook-Support für Event-Notifications
  - Provider-neutral Token-Auflösung

- **Setup:** 
  ```bash
  cd services/orchestrator-agent
  pip install -r requirements.txt
  python main.py
  ```

- **Doku:** [services/orchestrator-agent/README.md](services/orchestrator-agent/README.md)

### 3. Discord Service (`services/discord-service/`)
Nativer Discord Bot für Command-Line-Operationen mit erweiterten Berechtigungen.

- **Tech Stack:** Node.js 18+, Discord.js 14+
- **Kommandos:** Server-Provisioning, Status-Checks, provisioning Flows, Konfiguration
- **Features:**
  - Slash Commands mit Auto-Completion
  - Role-based Access Control für Befehle
  - Event-Streaming und Real-Time-Updates
  - Error Handling & User Feedback

- **Setup:** 
  ```bash
  cd services/discord-service
  npm install
  npm start
  ```

- **Doku:** [services/discord-service/README.md](services/discord-service/README.md)

### 4. Service Core (`services/service-core/`)
Spielserver und Ressourcen-Lebenszyklusmanagement mit Event-Logging.

- **Tech Stack:** Java 8+, Maven, Spring Boot
- **Features:**
  - Server Start/Stop Automation
  - Ressourcen-Tracking
  - Event-Logging und Audit-Trail
  - Health Checks und Metriken

- **Setup:** 
  ```bash
  cd services/service-core
  mvn clean install
  mvn spring-boot:run
  ```

- **Doku:** [services/service-core/README.md](services/service-core/README.md)

---

## 🛠️ Installation

### Systemanforderungen

| Komponente | Anforderung |
|-----------|-------------|
| OS | Linux, macOS, Windows (WSL2) |
| Memory | 4GB Minimum (8GB empfohlen) |
| Disk | 10GB freier Speicherplatz |
| Docker | 20.10+ (optional, aber empfohlen) |

### Schritt-für-Schritt Installationsanleitung

1. **Voraussetzungen prüfen**
   ```bash
   docker --version
   git --version
   python3 --version
   node --version
   ```

2. **Repository klonen**
   ```bash
   git clone https://github.com/DaaanielTV/infra-pilot.git
   cd infra-pilot
   ```

3. **Umgebung konfigurieren**
   ```bash
   cp .env.example .env
   nano .env
   # Passen Sie die Konfiguration nach Bedarf an
   ```

4. **Services starten**
   ```bash
   # Option A: Docker (empfohlen)
   docker-compose up -d
   
   # Option B: Lokale Entwicklung
   ./scripts/setup.sh
   ```

5. **Installation verifizieren**
   ```bash
   curl http://localhost:5173       # Dashboard
   curl http://localhost:3001/health # API
   curl http://localhost:8000/health # Orchestrator API
   ```

Siehe [docs/setup/local-development.md](docs/setup/local-development.md) für detaillierte Anweisungen.

---

## 👨‍💻 Development & Testing

### Getting Started

```bash
# Klonen & Setup
git clone https://github.com/DaaanielTV/infra-pilot.git
cd infra-pilot

# One-Command Setup
./scripts/setup.sh

# Tests ausführen
./scripts/test.sh

# Docker Images bauen
./scripts/docker-build.sh
```

### Development Workflow

1. **Feature-Branch erstellen**
   ```bash
   git checkout -b feature/your-feature
   ```

2. **Lokal ändern und testen**
   ```bash
   # Python Tests (Orchestrator Agent)
   cd services/orchestrator-agent
   pytest tests/

   # JavaScript Tests (Management Panel)
   cd services/management-panel
   npm run test

   # Java Tests (Service Core)
   cd services/service-core
   mvn test
   ```

3. **Mit aussagekräftigen Nachrichten committen**
   ```bash
   git commit -m "feat: add new provisioning command"
   ```

4. **Push und Pull Request erstellen**
   ```bash
   git push origin feature/your-feature
   ```

Siehe [CONTRIBUTING.md](CONTRIBUTING.md) für vollständige Beitragsrichtlinien.

### Testing Suite

Das Repository nutzt ein umfassendes Test-Framework mit neutralen Provider-Token:

#### Unit Tests
```bash
pytest -m unit
```

#### Integration Tests
```bash
pytest -m integration
```

#### End-to-End Tests (Mock Provider)
```bash
pytest -m e2e
```

#### Alle Tests lokal ausführen
```bash
./scripts/test.sh
```

#### Service-spezifische Tests
```bash
cd services/orchestrator-agent && pytest tests/
cd services/management-panel && npm run test
cd services/discord-service && npm run test
cd services/service-core && mvn test
```

### Coverage

```bash
# Coverage-Report aktualisieren
./scripts/coverage_report.sh

# Coverage anzeigen
cat coverage.md
```

### Neutral Naming & Provider Abstraction

Tests nutzen neutrale Token zur Provider-Abstraktion:

```python
# Beispiel: Neutrale Token
PROVIDER_MOCK = "mock-provider"
REGION_MOCK_US_EAST = "mock-us-east"
SKU_MOCK_SMALL = "mock-small"

# Resolver übersetzt zu konkreten Identitäten
from infra.naming.resolver import resolve_token
actual_provider = resolve_token(PROVIDER_MOCK)  # → "mock-provider"
```

### CI & Test Scaffolding

- **GitHub Actions:** Siehe `.github/workflows/ci-core.yml` - läuft auf Push/PRs
- **CI-Testumfang:** Unit Tests, Integration Tests, Linting, Build-Checks, Feature-Gating
- **Release Scaffolding:** `scripts/release.sh` für Git-Tagging und CHANGELOG-Updates
- **Integration Tests:** Skeleton unter `tests/integration/README.md`
- **Demo Gating:** Siehe `docs/CI_DEMO_GATE.md` für Feature-Flag-Gating-Verifikation

### Code Quality

```bash
# Linting
cd services/management-panel && npm run lint
cd services/orchestrator-agent && pylint cogs/

# Type Checking
cd services/management-panel && npm run type-check

# Formatting
cd services/management-panel && npm run format
```

---

## 📚 Dokumentation

Vollständige Dokumentation ist im [docs/](docs/) Verzeichnis verfügbar:

### Architektur & Design
- [Systemarchitektur](docs/architecture/overview.md)
- [Service-Spezifikationen](docs/architecture/)
- [Datenfluss & Integration](docs/architecture/data-flow.md)
- [Orchestrator Agent Design](docs/architecture/orchestrator-agent.md)

### Setup & Deployment
- [Lokale Development Setup](docs/setup/local-development.md)
- [Docker Deployment](docs/setup/docker-setup.md)
- [Kubernetes Deployment](docs/setup/kubernetes-deploy.md)
- [Environment-Konfiguration](docs/setup/environment-config.md)

### Operations
- [Deployment Guide](docs/operations/deployment-guide.md)
- [Skalierungsstrategie](docs/operations/scaling-strategy.md)
- [Monitoring & Observability](docs/operations/monitoring-observability.md)
- [Troubleshooting](docs/operations/troubleshooting.md)
- [Security Hardening](docs/operations/security-hardening.md)

### Development
- [Development Workflow](docs/development/development-workflow.md)
- [Testing Strategy](docs/development/testing-strategy.md)
- [Code Standards](docs/development/code-standards.md)
- [Debugging Tips](docs/development/debugging-tips.md)
- [AI Assistant Playbook](docs/development/ai-assistant-playbook.md)

### Testing
- [Testing Guidelines](docs/testing/testing-guidelines.md)
- [Testing Plan](docs/testing/test_plan.md)
- [Running Tests](docs/testing/running_tests.md)
- [Provider Neutral Mapping](docs/testing/provider_neutral_mapping.md)

### Branding & Design
- [Branding Guidelines](docs/branding-guidelines.md)
- [Design System](docs/design-system.md)
- [Design Tokens](docs/design-tokens.md)

---

## 🔍 Workflows & Use Cases

### Use Case 1: Spielserver provisioner

**Via Web Dashboard:**
1. Login zu http://localhost:5173
2. "Create Server" klicken
3. Konfiguration auswählen
4. "Deploy" klicken

**Via Discord:**
```
/provision type=gameserver name=my-server size=medium region=us-east-1
```

**Via REST API:**
```bash
curl -X POST http://localhost:8000/api/servers \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-server",
    "type": "gameserver",
    "provider": "aws",
    "region": "us-east-1"
  }'
```

### Use Case 2: Infrastruktur-Überwachung

```bash
# Alle Server auflisten
curl http://localhost:8000/api/servers

# Metriken abrufen
curl http://localhost:8000/api/metrics

# Health Status
curl http://localhost:8000/health

# Logs anzeigen
docker-compose logs orchestrator-agent
```

### Use Case 3: Ressourcen skalieren

Siehe [docs/operations/scaling-strategy.md](docs/operations/scaling-strategy.md) für Details zum Autoscaling und manuellen Skalierungsoptionen.

### Use Case 4: Seed Demo Scenario

Das System unterstützt 1-Klick Demo-Datenerzeugung für QA und Vorführungen:

```bash
# Feature aktivieren
export VITE_DEMO_FEATURE_ENABLED=true

# UI: Demo-Button im Header klicken
# API: POST /api/seed-demo ausgelöst
```

---

## 🐳 Docker

### Docker Images bauen

```bash
# Alle Services bauen
docker-compose build

# Spezifischen Service bauen
docker-compose build management-panel
```

### Mit Docker Compose ausführen

```bash
# Development Stack
docker-compose up -d

# Production Stack
docker-compose -f docker-compose.prod.yml up -d

# Logs anzeigen
docker-compose logs -f management-panel
docker-compose logs -f orchestrator-agent
```

### In Registry pushen

```bash
# Registry konfigurieren
export REGISTRY=your-registry.com

# Build und Push
docker-compose build
docker-compose push
```

---

## 🚢 Deployment-Optionen

### Quick Deployment

#### Option 1: Docker Compose (Development)
```bash
docker-compose up -d
docker-compose logs -f
```

#### Option 2: Kubernetes
```bash
kubectl apply -f infrastructure/kubernetes/
```

#### Option 3: Cloud Provider (Terraform)
- **AWS:** Siehe [infrastructure/terraform/aws/](infrastructure/terraform/aws/)
- **GCP:** Siehe [infrastructure/terraform/gcp/](infrastructure/terraform/gcp/)
- **Azure:** Siehe [infrastructure/terraform/azure/](infrastructure/terraform/azure/)

Vollständiger Deployment Guide: [docs/operations/deployment-guide.md](docs/operations/deployment-guide.md)

---

## 📊 Monitoring & Observability

### Monitoring Stack

Monitoring ist einfach über Docker Compose verfügbar:

- **Prometheus Metriken:** http://localhost:9090
- **Grafana Dashboards:** http://localhost:3000 (Credentials: admin/admin)
- **Request Instrumentation:** Alle Services loggen Requests
- **Health Checks:** `/health` Endpunkte auf allen Services
- **Logs:** Via `docker-compose logs` oder zentrales Logging

### Health Check

```bash
# Management Panel
curl http://localhost:3001/health

# Orchestrator API
curl http://localhost:8000/health

# Service Core
curl http://localhost:8080/health
```

Siehe [docs/operations/monitoring-observability.md](docs/operations/monitoring-observability.md) für erweiterte Überwachungsoptionen.

---

## 🔐 Security & Performance

### Security Features

- **SSL/TLS:** Alle Produktions-Deployments verwenden HTTPS
- **RBAC:** Rollenbasierte Zugriffskontrolle auf allen Services
- **Audit Logging:** Alle Operationen werden geloggt
- **RLS (Row Level Security):** PostgreSQL RLS in Business Mode aktiviert
- **API Key Management:** Sichere Token-basierte API-Zugriffe
- **Provider Credentials:** Sichere Verwaltung von Cloud-Provider-Credentials

### Security Configuration

- SSL/TLS Setup: [docs/setup/ssl-tls-setup.md](docs/setup/ssl-tls-setup.md)
- Security Hardening: [docs/operations/security-hardening.md](docs/operations/security-hardening.md)
- Vulnerability Reporting: [SECURITY.md](SECURITY.md)

---

## 🤝 Contributing

Wir freuen uns über Beiträge! Bitte lesen Sie [CONTRIBUTING.md](CONTRIBUTING.md) und unsere Code-Standards [docs/development/code-standards.md](docs/development/code-standards.md).

### Quick Contribution Steps

1. Repository forken
2. Feature-Branch erstellen: `git checkout -b feature/my-feature`
3. Änderungen committen: `git commit -am 'Add my feature'`
4. Push: `git push origin feature/my-feature`
5. Pull Request einreichen

Siehe [CONTRIBUTING.md](CONTRIBUTING.md) für detaillierte Richtlinien.

---

## 📝 License & Warranty

### License

Dieses Projekt ist unter der GPL-3.0 Lizenz lizenziert - siehe [LICENSE](LICENSE) für Details.

### Warranty & Liability

⚠️ **Diese Software wird "wie besehen" bereitgestellt, ohne irgendeine Art von Garantie.**

- Siehe die [LICENSE](LICENSE) Datei für den vollständigen GPL-3.0 Haftungsausschluss und Haftungsbegrenzung.
- **Die Autoren haften nicht für Schäden, die durch dieses System verursacht werden.**
- **Testen Sie ausgiebig, bevor Sie es in der Produktion einsetzen.**

---

## 🆘 Support & Resources

- **Dokumentation:** [docs/](docs/)
- **Issues:** [GitHub Issues](https://github.com/DaaanielTV/infra-pilot/issues)
- **Discussions:** [GitHub Discussions](https://github.com/DaaanielTV/infra-pilot/discussions)
- **Security:** [SECURITY.md](SECURITY.md)
- **Testing:** [docs/testing/](docs/testing/)

---

## 📊 Recent Changes & Features

### Latest Improvements

- ✨ **Observability:** Request Instrumentation und erweiterte /health Metriken
- ✨ **Business Mode:** Backend CRUD für Kunden mit RLS (Row Level Security)
- ✨ **Seed Demo System:** 1-Click Demo-Szenarien mit reserviertem Seed-Datenmanagement
- ✨ **Feature Gating:** Environment-basierte Feature-Flags (VITE_DEMO_FEATURE_ENABLED)
- ✨ **CI Improvements:** Doppelte CI-Runs zum Testen von Feature-Flags
- ✨ **UI Enhancements:** Customers Page mit Seed Demo Modal und globales Demo-Status-Badge
- 🧪 **New Tests:** Playwright Tests für Feature-Gating-Verifikation

---

## 🔧 Troubleshooting

### Häufige Probleme

#### Bot startet nicht
- Überprüfen Sie, ob alle erforderlichen Umgebungsvariablen gesetzt sind
- Verifizieren Sie die API-Credentials

#### Discord-Befehle sind nicht sichtbar
- Stellen Sie sicher, dass der Bot die korrekten Scopes/Permissions hat
- Überprüfen Sie die Befehlsregistrierung

#### Panel kann Backend-Daten nicht laden
- Verifizieren Sie Supabase-Deployment-Credentials
- Überprüfen Sie die Datenbankverbindung

#### Maven Build-Fehler
- Bestätigen Sie, dass Java 8+ installiert ist: `java -version`
- Führen Sie `mvn clean install` aus

---

**[⬆ back to top](#-infra-pilot)**
