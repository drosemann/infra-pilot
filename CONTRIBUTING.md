# Contributing to Infra Pilot

First off, thank you for considering contributing! All types of contributions are welcome — whether it's a bug fix, new feature, documentation improvement, or a discussion starter.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Branch Naming Conventions](#branch-naming-conventions)
- [Commit Style](#commit-style)
- [Pull Request Workflow](#pull-request-workflow)
- [PR Checklist](#pr-checklist)
- [Test Requirements](#test-requirements)
- [PR Title Examples](#pr-title-examples)

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md). We expect all contributors to foster a welcoming and inclusive environment.

## Getting Started

1. **Fork** the repository and clone your fork locally.
2. Add the upstream repo as a remote:

   ```bash
   git remote add upstream https://github.com/DaaanielTV/infra-pilot.git
   ```

3. Create a branch from `main` following the naming convention below.
4. Make your changes and ensure all existing and new tests pass.
5. Push your branch and open a Pull Request against `main`.

## Branch Naming Conventions

Use descriptive names following this pattern:

| Prefix      | Use Case                         | Example                          |
|-------------|----------------------------------|----------------------------------|
| `feat/`     | A new feature                    | `feat/oidc-sso-provider`         |
| `fix/`      | A bug fix                        | `fix/container-logs-encoding`    |
| `docs/`     | Documentation changes            | `docs/api-endpoint-reference`    |
| `refactor/` | Code restructuring              | `refactor/orchestrator-cog-loader` |
| `test/`     | Adding or updating tests         | `test/integration-service-auth`  |
| `chore/`    | Build, CI, or tooling changes    | `chore/upgrade-node-to-20`       |
| `perf/`     | Performance improvements         | `perf/panel-metric-polling`      |
| `style/`    | Code style, formatting           | `style/eslint-config-align`      |

Use hyphens (`-`) as word separators. Keep branch names concise but descriptive.

## Commit Style

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short description>

[optional body]
[optional footer]
```

**Types:** `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, `style`

**Scope** (optional): the affected component, e.g. `panel`, `orchestrator`, `discord`, `integration`, `cli`, `mobile`, `docs`

Examples:

```
feat(orchestrator): add kubernetes cluster manager cog
fix(panel): resolve websocket reconnection loop
docs(api): document webhook event bus endpoints
test(integration): add auth 2fa flow coverage
```

Write the commit message in **imperative mood** ("add" not "added"). Keep the summary under 72 characters.

## Pull Request Workflow

1. Ensure your branch is up to date with `main`:

   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. Run the full test suite before pushing:

   ```bash
   # Root-level tests
   pytest tests/
   # Service-specific tests — see individual READMEs
   cd services/management-panel && npm test
   cd services/orchestrator-agent && pytest
   ```

3. Push your branch and open a PR against `main`.
4. Fill in the [PR template](.github/pull_request_template.md) completely.
5. Request a review from maintainers (visible in [OWNERS.md](OWNERS.md)).
6. Respond to review feedback with additional commits on the same branch.

## PR Checklist

Before submitting, verify that:

- [ ] Branch name follows the naming convention (`type/descriptive-name`)
- [ ] Commits follow [Conventional Commits](https://www.conventionalcommits.org/) style
- [ ] PR title is clear and describes the change (see examples below)
- [ ] PR template is filled out completely
- [ ] Code compiles/lints without new warnings or errors
- [ ] Existing tests pass (run `pytest tests/` and/or `npm test`)
- [ ] New tests cover the changes (unit and/or integration)
- [ ] Documentation is updated if behavior or APIs changed
- [ ] No secrets, tokens, or credentials are committed
- [ ] Changes are focused on a single concern (one feature/fix per PR)
- [ ] All conversations on the PR are resolved before merge

## Test Requirements

- All new features must include tests (unit tests for logic, integration tests for API/network paths).
- Bug fixes must include a test that reproduces the issue before the fix.
- Run the full test suite locally before pushing:

  ```bash
  pytest tests/                           # Python tests (orchestrator, integration)
  cd services/management-panel && npm test  # Panel frontend + API tests
  cd services/discord-service && npm test   # Discord service tests
  ```

- Code coverage should not decrease. Run `./scripts/coverage.sh` or the equivalent for your service to check.

## PR Title Examples

Good PR title examples:

- `feat(orchestrator): add kubernetes cluster manager deployment cog`
- `fix(panel): resolve websocket race condition on reconnect`
- `docs(api): document webhook event bus with request/response examples`
- `refactor(integration): extract notification dispatcher from auth module`
- `test(panel): add unit tests for config editor YAML parser`

Each title is scoped to a component, uses the conventional commit type, and clearly describes the change in a single line.
