# infra-pilot — Agent Guide

Use this guide with [CONTRIBUTING.md](CONTRIBUTING.md), the relevant service
guide, and [SECURITY.md](SECURITY.md). Keep the change focused, but follow the
behavior through every component it affects.

## How we build

- Prefer the smallest production-ready change that solves the real problem.
  Understand existing behavior before adding abstractions or configuration.
- Finish the user-facing flow end to end. The CLI, management panel, agent,
  Discord bridge, deployment files, and documentation may be separate parts
  of the same feature.
- Prefer working implementations over placeholders, fake integrations, or
  unwired demo code. Remove obsolete paths when replacing them; do not build
  new behavior on top of dead code.
- Treat production operation, security boundaries, and existing user data as
  first-class requirements. Upgrades, migrations, backup, and restore must
  preserve data or clearly define a safe recovery path.
- Add focused tests for changed behavior and regressions. Tests should verify
  meaningful outcomes, not just mirror the implementation.
- Update user, operator, API, or architecture documentation when the change
  changes what those readers need to know. Follow
  [docs/DOCUMENTATION.md](docs/DOCUMENTATION.md) rather than duplicating docs.

## Where things live

- `cli/` — `ipilot` command-line client
- `services/management-panel/` — React UI, Express API, and WebSocket server
- `services/orchestrator-agent/` — Python agent, manifests, RBAC, and webhooks
- `services/discord-service/` — optional Discord and Pterodactyl integration
- `helm/` and `infra/` — Kubernetes chart and infrastructure
- `scripts/` — environment, backup, health, and release helpers
- `tests/` — Python test suites and load-test scenarios
- `docs/` and `wiki/` — developer documentation and user/operator guides

Read the relevant service README and existing tests before changing a service.
For cross-service behavior, verify the contract at each boundary rather than
assuming one component's tests cover the complete flow.

## GitHub workflow

This VM has **no GitHub login** (`gh auth` is not configured, and `origin` is
HTTPS read-only). Push branches with the repository deploy key; the owner opens
pull requests from the web or mobile app.

- Push remote: `deploy-ssh` = `git@github.com:drosemann/infra-pilot.git`
- Private key: `/home/dro/.ssh/infra-pilot-tmp`
  (`~/.ssh/infra-pilot-tmp`) — never print, share, or commit it
- Public key: `/home/dro/.ssh/infra-pilot-tmp.pub`
  (`~/.ssh/infra-pilot-tmp.pub`) — share only by link if the owner needs to
  re-add it
- Deploy keys have no API scope. Do not use `gh pr create`.

### Preconditions — do not change

- Default branch: `main`
- `origin` = `https://github.com/drosemann/infra-pilot.git` (fetch only)
- `deploy-ssh` = `git@github.com:drosemann/infra-pilot.git` (deploy-key push)

If the deploy remote is missing, restore it with:

```bash
git remote get-url deploy-ssh || git remote add deploy-ssh git@github.com:drosemann/infra-pilot.git
ls -l ~/.ssh/infra-pilot-tmp
```

Test authentication without exposing the key (expect `Hi drosemann/infra-pilot! ... shell access`):

```bash
ssh -i ~/.ssh/infra-pilot-tmp -o IdentitiesOnly=yes -T git@github.com
```

### Branch and change workflow

1. Check `git status --short --branch`. Do not switch branches or sync `main`
   until any existing work is safe.
2. When starting from the default branch, sync it:

   ```bash
   git fetch origin
   git checkout main
   git pull --ff-only origin main
   git status --short --branch
   ```

3. Create a branch from `main` using a prefix required by
   [CONTRIBUTING.md](CONTRIBUTING.md): `feat/`, `fix/`, `docs/`, `refactor/`,
   `test/`, `chore/`, `perf/`, or `style/`.

   ```bash
   git checkout -b feat/short-desc
   ```

4. Make and verify the change. Follow the PR checklist in
   [CONTRIBUTING.md](CONTRIBUTING.md).
5. Commit and push **only when the user explicitly asks**. Stage intended
   files only:

   ```bash
   git add <intended files only>
   git commit -m "feat(scope): short description"
   GIT_SSH_COMMAND="ssh -i ~/.ssh/infra-pilot-tmp -o IdentitiesOnly=yes" git push -u deploy-ssh <branch>
   ```

   Use the commit format `<type>(<scope>): <short description>` (under 72
   characters) from [CONTRIBUTING.md](CONTRIBUTING.md). Historical commit
   subjects are not fully consistent; follow the documented format for new
   commits.
6. Do not create the PR. Report the branch, commits, tests, and changed files;
   the owner opens the PR against `main` using GitHub's `Compare & pull
   request`.

## Verification

Run the smallest relevant checks for the code changed, then check the diff:

```bash
git status --short
git diff --check
pytest tests/ -q
```

For service changes, also run the corresponding checks:

```bash
bash scripts/test.sh --coverage
cd services/management-panel && npm run lint && npm run test:coverage
```

Use the orchestrator's test command when its code changes:

```bash
cd services/orchestrator-agent && pytest -q
```

CI additionally checks gitleaks, flake8/black/isort, pytest, shellcheck,
Terraform validation, markdownlint, and npm audit. Do not claim a check passed
unless it was run.

## Non-negotiable safety

- Never push to `main`; never force-push.
- Never commit secrets, tokens, `.env` files, passwords, or private keys.
- Never run `gh auth login`, change the documented remotes, or delete
  `~/.ssh/infra-pilot-tmp*`.
- Never print the private key. Do not expose credentials or live user data in
  logs, tests, screenshots, or documentation.
