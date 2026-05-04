# Contributing to Infra Pilot

Thanks for your interest in contributing to **Infra Pilot**! This document provides guidelines and instructions for contributing code, documentation, and improvements.

## Table of Contents
- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Code Standards](#code-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Security](#security)

---

## Code of Conduct

Please review and adhere to our [Code of Conduct](CODE_OF_CONDUCT.md). We are committed to providing a welcoming and inclusive environment for all contributors.

---

## Getting Started

### Prerequisites

- Git
- Docker & Docker Compose (recommended)
- One or more of: Java 8+, Python 3.9+, Node.js 18+
- 4GB RAM minimum

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/DaaanielTV/infra-pilot.git
cd infra-pilot

# Run the setup script
./scripts/setup.sh

# Verify installation
./scripts/test.sh
```

### Project Structure

```
infra-pilot/
├── services/                   # All service code
│   ├── service-core/          # Java server manager
│   ├── orchestrator-agent/    # Python orchestration engine
│   ├── discord-service/       # Node.js Discord bot
│   └── management-panel/      # React dashboard
├── docs/                      # Documentation
├── scripts/                   # Utility scripts
├── .github/
│   ├── workflows/            # CI/CD pipelines
│   └── ISSUE_TEMPLATE/       # Issue templates
└── README.md                  # This is your entry point
```

---

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
# or for bug fixes:
git checkout -b fix/issue-description
```

### 2. Make Changes

- Work in the relevant service directory
- Follow code standards (see [Code Standards](#code-standards))
- Write tests for new functionality
- Keep commits focused and logical

### 3. Test Your Changes

Before submitting a PR, ensure your changes work:

```bash
# Test all services
./scripts/test.sh

# Or test a specific service
cd services/orchestrator-agent
pytest tests/

cd services/management-panel
npm run test

cd services/service-core
mvn test

cd services/discord-service
npm run test
```

### 4. Commit with Clear Messages

See [Commit Guidelines](#commit-guidelines) below.

### 5. Push and Open a Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub. Use the PR template and provide:
- Clear description of changes
- Reference to related issues (if any)
- Testing notes
- Any migration or operational impact

---

## Commit Guidelines

Use clear, imperative commit messages that describe what the change does:

**Good examples:**
- `feat: add server provisioning API endpoint`
- `fix: correct environment variable handling in discord service`
- `docs: update setup instructions for macOS`
- `refactor: simplify orchestrator resource allocation logic`
- `test: add integration tests for VPS provisioning`
- `chore: update dependencies to latest versions`

**Format:**
```
<type>: <short description>

<optional detailed explanation>
```

**Types:**
- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation changes
- `refactor`: Code refactoring without feature/bug changes
- `perf`: Performance improvements
- `test`: Test additions or fixes
- `chore`: Dependency updates, tooling changes

---

## Pull Request Process

1. **Update your branch** with latest main:
   ```bash
   git fetch origin
   git rebase origin/main
   ```

2. **Run tests locally** to ensure nothing breaks:
   ```bash
   ./scripts/test.sh
   ```

3. **Create descriptive PR title** following the same format as commits:
   - ✅ `feat: add user authentication to dashboard`
   - ❌ `Fix stuff`

4. **Fill out the PR template** completely

5. **Link related issues** (use `Closes #123` in description)

6. **Be responsive** to review comments and questions

### PR Checklist

- [ ] Code builds/runs for touched services
- [ ] All tests pass (`./scripts/test.sh`)
- [ ] Documentation is updated (if needed)
- [ ] No debug statements or temporary code
- [ ] No secrets or credentials committed (use `.env.example` templates)
- [ ] Commit messages are clear and follow guidelines
- [ ] Testname entspricht der Konvention (`test_<funktion>_<erwartetes_verhalten>` oder sprachspezifischer Standard)
- [ ] Kein Placeholder in neuen Tests (z. B. `TODO`, `pass`, `it('works')`)
- [ ] Doppelte Assertions vermieden (gleiche Aussage nicht mehrfach prüfen)
- [ ] Parametrisierung verwendet, wenn mehr als 3 ähnliche Fälle getestet werden

---

## Code Standards

All code must follow our standards documented in [docs/development/code-standards.md](docs/development/code-standards.md).

**Quick summary:**
- **Python:** Follow PEP 8, use type hints where possible
- **JavaScript/TypeScript:** Use ESLint configuration in service directories
- **Java:** Follow standard Java conventions, use Maven formatting
- **General:** Keep code DRY, well-commented, and testable

Run linting in your service:

```bash
cd services/management-panel
npm run lint

cd services/orchestrator-agent
pylint src/

# Java formats automatically with Maven
cd services/service-core
mvn spotless:apply
```

---

## Testing

All new features must include tests. We follow these principles:

### Done-Kriterien für neue Tests

Ein neuer Test gilt erst als **Done**, wenn alle folgenden Kriterien erfüllt sind:

1. **Lesbarkeit:** Testname und Arrange/Act/Assert-Struktur machen die Intention sofort verständlich.
2. **Isolation:** Der Test ist unabhängig von anderen Tests und hat keine versteckten Seiteneffekte.
3. **Deterministisch:** Der Test liefert bei gleichem Code immer dasselbe Ergebnis (keine Zufalls-/Zeitabhängigkeit ohne Kontrolle).
4. **Klare Failure-Message:** Bei Fehlschlag ist direkt erkennbar, was erwartet wurde und was tatsächlich passiert ist.

### Beispiele: schlecht vs. gut

#### Testnamen

**Schlecht**
- `test1`
- `should_work`
- `it handles stuff`

**Gut**
- `test_create_server_rejects_invalid_region`
- `test_allocate_ip_returns_next_free_address`
- `shouldReturn403WhenTokenIsExpired`

#### Teststruktur

**Schlecht**
```python
def test_user_creation():
    user = create_user("a@b.com")
    assert user is not None
    assert user.email == "a@b.com"
    assert user.email == "a@b.com"  # doppelt
```

**Gut**
```python
def test_create_user_sets_email_field():
    # Arrange
    email = "a@b.com"

    # Act
    user = create_user(email)

    # Assert
    assert user.email == email, "Expected created user to keep the provided email"
```

### Service-Specific Testing

**Python (Orchestrator Agent):**
```bash
cd services/orchestrator-agent
pytest tests/ -v
```

**JavaScript/Node.js (Services):**
```bash
cd services/discord-service
npm run test

cd services/management-panel
npm run test
```

**Java (Service Core):**
```bash
cd services/service-core
mvn test
```

### Coverage Requirements

- Aim for >80% code coverage on new code
- Critical paths should approach 100%
- Run coverage reports:
  ```bash
  ./scripts/test.sh --coverage
  ```

Weitere Vorlagen und Empfehlungen: [docs/testing-guidelines.md](docs/testing-guidelines.md)

---


## Test Naming Convention

Verwende für Tests ein konsistentes, fachlich lesbares Schema:

- **Dateinamen:** `test_<modul>_<verhalten>.py`
- **Testfunktionen:** `test_<given>_<when>_<then>`

**Beispiele:**
- `tests/test_aws_service_defaults.py`
- `def test_given_ec2_service_when_initialized_then_applies_ec2_defaults():`
- `def test_given_s3_service_when_initialized_then_applies_s3_defaults():`
- `def test_given_route53_service_when_initialized_then_applies_route53_defaults():`

---

## Documentation

When contributing code, update documentation as needed:

1. **README updates** - If you add new features or change setup
2. **Service documentation** - Update service-specific docs in `services/<service>/README.md`
3. **Code comments** - For complex logic, explain the "why" not just "what"
4. **Architecture docs** - If you make structural changes, update [docs/architecture/](docs/architecture/)
5. **API docs** - If you add endpoints, document them in [docs/api/](docs/api/)
