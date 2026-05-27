# development workflow & contributing

this guide helps you contribute code and improvements to infra pilot.

## git workflow

### main branches

| branch | purpose | protection |
|--------|---------|-----------|
| `main` | production-ready code | required pr review, tests pass |
| `develop` | integration branch | required tests pass |

### feature branches

name feature branches clearly:
```
feature/user-authentication
fix/server-provisioning-timeout
docs/architecture-overview
chore/upgrade-dependencies
perf/optimize-db-queries
```

## development cycle

### fork & clone

```bash
# Fork on GitHub, then clone your fork
git clone https://github.com/your-username/infra-pilot.git
cd infra-pilot

# Add upstream remote to stay synchronized
git remote add upstream https://github.com/DaaanielTV/infra-pilot.git
```

### create feature branch

```bash
# Fetch latest from upstream
git fetch upstream

# Create branch from develop
git checkout -b feature/my-feature upstream/develop
```

### make changes

```bash
# Edit files in your service
cd services/orchestrator-agent

# Follow code standards (see Code Standards guide)
# Write tests alongside changes
# Commit frequently with clear messages
```

### test locally

```bash
# Run service-specific tests
npm run test           # JavaScript
pytest tests/         # Python
mvn test             # Java

# Run linting
npm run lint         # JavaScript

# Type checking
npm run type-check   # TypeScript
```

### commit & push

```bash
# Stage changes
git add .

# Commit with clear message
git commit -m "feat: add user roles and permissions

- Implement RBAC system
- Add permission checks to API
- Update dashboard UI for role display

Fixes #123"

# Push to your fork
git push origin feature/my-feature
```

### create pull request

on github:
• title: clear, descriptive title
• description: use pr template
• reference issues: `fixes #123`
• add labels: `type/feature`, `service/orchestrator`

### respond to review

```bash
# Address feedback
# Commit additional changes
git commit -m "address review feedback"
git push origin feature/my-feature

# After approval, rebase and merge
git rebase upstream/develop
git push -f origin feature/my-feature
```

## commit message guidelines

### format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### types

• `feat` - new feature
• `fix` - bug fix
• `docs` - documentation
• `style` - code style (formatting, semicolons, etc)
• `refactor` - code refactoring
• `perf` - performance improvements
• `test` - adding tests
• `chore` - build, dependencies, tooling

### examples

```
feat(orchestrator): add server auto-scaling

Implement auto-scaling policy that monitors CPU and memory usage,
automatically provisioning or decommissioning servers based on thresholds.

- Add scalability service module
- Implement metric collection
- Add scaling rules engine

Closes #456
```

```
fix(dashboard): correct memory leak in WebSocket handler

The connection handler was not properly cleaning up event listeners,
causing memory to grow over time.

Fixes #789
```

```
docs: update architecture documentation with new data flow
```

## testing requirements

### before creating pr

• write tests alongside features
• run full test suite locally
• verify no regressions in other areas

### test coverage

| service | minimum coverage | command |
|---------|------------------|---------|
| orchestrator-agent | 80% | `pytest --cov=services/orchestrator-agent` |
| management-dashboard | 70% | `npm run test -- --coverage` |
| discord-service | 70% | `npm run test -- --coverage` |
| service-core | 75% | `mvn test jacoco:report` |

### running tests

```bash
# All tests
./scripts/test.sh

# Specific service
cd services/orchestrator-agent && pytest tests/

# Watch mode (JavaScript)
npm run test:watch

# With coverage
pytest --cov=services/orchestrator-agent tests/

# Specific test file
mvn test -Dtest=ServerTest
```

## code quality standards

### linting

```bash
# JavaScript/TypeScript
npm run lint
npm run lint -- --fix  # Auto-fix

# Python
pylint services/orchestrator-agent/
black services/orchestrator-agent/  # Format code
```

### type checking

```bash
# TypeScript
npm run type-check

# Python (optional, for type hints)
mypy services/orchestrator-agent/
```

### code formatting

```bash
# Auto-format all code
npm run format            # JavaScript
black .                    # Python
```

## pr checklist

before submitting pr:

• [ ] code follows project standards
• [ ] tests added/updated and passing
• [ ] no linting errors (`npm run lint` / `pylint`)
• [ ] type checking passes (`npm run type-check`)
• [ ] documentation updated if needed
• [ ] no console warnings/errors
• [ ] commits are clean and descriptive
• [ ] tested with related services
• [ ] no breaking changes (or documented)

## code review process

### what reviewers look for

• correctness - does it work as intended?
• tests - are there adequate tests?
• performance - are there performance concerns?
• security - are there security issues?
• standards - does it follow conventions?
• documentation - are changes documented?

### responding to review

```bash
# If changes needed
# 1. Make changes
# 2. Commit without force push (if small feedback)
git commit -m "address review feedback"
git push

# 3. Or if rewriting history
git rebase -i upstream/develop
git push -f origin feature/my-feature
```

## documentation

### when to update docs

• architecture changes → update [docs/architecture/](../architecture/)
• api changes → update [docs/api/](../api/)
• setup changes → update [docs/setup/](../setup/)
• new feature → add to [readme.md](../../README.md)

### documentation style

• clear, active voice
• code examples included
• link to related docs
• keep up-to-date with code

## advanced topics

### rebasing & squashing

```bash
# Rebase on latest develop
git rebase upstream/develop

# If conflicts
git rebase --continue  # After resolving

# Squash commits for cleaner history
git rebase -i upstream/develop
# Mark commits as 's' to squash
```

### signing commits

```bash
# Generate GPG key (if not done)
gpg --generate-key

# Configure Git
git config --global user.signingkey YOUR_KEY_ID
git config --global commit.gpgsign true

# Sign commit
git commit -S -m "message"

# Verify commit
git log --show-signature
```

## learning resources

• [system architecture](../architecture/overview.md)
• [code standards](code-standards.md)
• [testing strategy](testing-strategy.md)
• [service documentation](../architecture/)

## getting help

• questions? open a discussion on github
• bug found? file an issue with reproduction steps
• security issue? see [security.md](../../SECURITY.md)

last updated: april 2026
