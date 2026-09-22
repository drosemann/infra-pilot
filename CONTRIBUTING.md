# Contributing

Thanks for wanting to help! We welcome bug fixes, new features, docs, and ideas.

## Table of Contents

- [How to Contribute](#how-to-contribute)
- [Branch Names](#branch-names)
- [Commits](#commits)
- [Code Style](#code-style)
- [Documentation](#documentation)
- [Security](#security)
- [PR Checklist](#pr-checklist)
- [Running Tests](#running-tests)

## How to Contribute

1. **Fork** the repo and clone your copy
2. **Add upstream**: `git remote add upstream https://github.com/drosemann/infra-pilot.git`
3. **Create a branch** from `main` (see naming below)
4. **Make your changes** and make sure tests pass
5. **Push** and open a Pull Request to `main`

## Branch Names

Use a prefix and a short description with dashes.

Examples: `feat/add-login`, `fix/bug-123`, `docs/readme-update`

Prefixes: `feat/`, `fix/`, `docs/`, `refactor/`, `test/`, `chore/`, `perf/`, `style/`

## Commits

Write clear commit messages. Use this format:

```
<type>(<scope>): <short description>
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, `style`

Keep the summary under 72 characters.

## Code Style

- Python: `black`, `isort`, `flake8`, `bandit` clean.
- TypeScript: `npm run lint` with zero warnings.
- Shell: `shellcheck` clean for `scripts/`.
- Markdown: keep lines short, blank lines around blocks.

## Documentation

Follow [docs/DOCUMENTATION](./docs/DOCUMENTATION.md).
Roughly every 25 lines of behavioral change needs a doc
unit: docstring, README section, or contract artifact.
Update screenshots in `docs/screenshots/` when panel views
change materially.

## Security

Never commit secrets, tokens, `.env`, or private keys.
New endpoints need HMAC, bearer, or RBAC guards.
Trust-boundary changes require a `SECURITY.md` update.
Report vulnerabilities privately per `SECURITY.md`.

## PR Checklist

Before submitting, check these off:

- [ ] Branch name follows the naming rule
- [ ] Commit messages are clear
- [ ] Tests pass and coverage didn't drop
- [ ] No new warnings or errors
- [ ] Updated docs if needed
- [ ] No secrets or passwords in code

## Running Tests

```bash
pytest tests/ -q
bash scripts/test.sh --coverage
(cd services/orchestrator-agent && pytest -q)
cd services/management-panel && npm run lint && npm run test:coverage
```

See [SUPPORT](./SUPPORT.md) for triage expectations and
[Code of Conduct](./CODE_OF_CONDUCT.md) for behavior rules.
