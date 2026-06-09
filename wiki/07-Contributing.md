# 07 – Contributing

## Dev-Setup

```bash
# Repository klonen
git clone https://github.com/DaaanielTV/infra-pilot.git
cd infra-pilot

# Python-Dependencies (Root-Tests)
pip install -r requirements.txt

# Management Panel
cd services/management-panel && npm install && cd ../..

# Discord Service
cd services/discord-service && npm install && cd ../..
```

## Tests ausführen

```bash
# Alle Python-Tests
pytest tests/

# Mit Coverage
pytest --cov=infra

# Management Panel-Tests
cd services/management-panel && npm test

# Über Makefile
make verify
make verify-offline
```

### Test-Marker

| Marker | Beschreibung |
|--------|-------------|
| `unit` | Unit-Tests (schnell, keine externen Abhängigkeiten) |
| `integration` | Integrationstests (Datenbank, API) |
| `e2e` | End-to-End-Tests (vollständiger Stack) |
| `smoke` | Smoke-Tests (grundlegende Health-Checks) |

## Branch-Naming

| Prefix | Beispiel |
|--------|---------|
| `feat/` | `feat/oidc-sso-provider` |
| `fix/` | `fix/container-logs-encoding` |
| `docs/` | `docs/api-endpoint-reference` |
| `refactor/` | `refactor/orchestrator-cog-loader` |
| `test/` | `test/integration-service-auth` |
| `chore/` | `chore/upgrade-node-to-20` |

## Commit-Stil

Wir verwenden [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <kurzbeschreibung>

[optional body]
[optional footer]
```

Beispiele:
- `feat(cli): add dns record command`
- `fix(orchestrator): handle null pointer in health check`
- `docs(wiki): add first-deployment guide`

## PR-Workflow

1. Branch von `main` erstellen (nach Namenskonvention oben)
2. Änderungen committen und pushen
3. PR gegen `main` öffnen
4. CI-Checks laufen automatisch (Tests, Lint, Security-Scans)
5. Nach Review und grünen Checks wird gemerged

## Projektstruktur

```
├── cli/                  # CLI-Tool (ipilot)
│   └── ipilot/           #   Python-Package
├── services/             # Microservices
│   ├── management-panel/ # React/Express-Dashboard
│   ├── orchestrator-agent/ # Python-Orchestrator
│   ├── integration-service/ # Python-Integration
│   ├── discord-service/  # Discord-Bot
│   └── service-core/     # Java/Minecraft-Plugin
├── infra/                # Terraform-Provider, Naming
├── mobile/               # React Native App
├── tests/                # Root-Tests
└── docs/                 # Dokumentation
```

---

*Stand: Mai 2026 · Siehe auch [CONTRIBUTING.md](https://github.com/daaanieltv/infra-pilot/blob/main/CONTRIBUTING.md)*
