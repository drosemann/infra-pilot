# AGENTS.md — How to open a PR in infra-pilot

This VM has **no GitHub login** (`gh auth` not configured, `origin` is HTTPS read-only).
Push via the repo-scoped **deploy key + `deploy-ssh` remote**. Deploy keys have no API scope, so agents **push the branch only** — the owner opens the PR from web/mobile.

## 1. Preconditions (do not change)

- Default branch: `main`
- Remotes:
  - `origin` = `https://github.com/drosemann/infra-pilot.git` (fetch only, no push auth)
  - `deploy-ssh` = `git@github.com:drosemann/infra-pilot.git` (push via deploy key)
- Key: `~/.ssh/infra-pilot-tmp` (private, never print/share/commit), `~/.ssh/infra-pilot-tmp.pub` (public)
- If missing, restore with:
  ```bash
  git remote get-url deploy-ssh || git remote add deploy-ssh git@github.com:drosemann/infra-pilot.git
  ls -l ~/.ssh/infra-pilot-tmp
  ```
- Test auth (expect `Hi drosemann/infra-pilot! ... shell access`):
  ```bash
  ssh -i ~/.ssh/infra-pilot-tmp -o IdentitiesOnly=yes -T git@github.com
  ```

## 2. Workflow

1. Sync:
   ```bash
   git fetch origin
   git checkout main
   git pull --ff-only origin main
   git status --short --branch
   ```
2. Create branch from `main` (required prefixes per `CONTRIBUTING.md`):
   `feat/`, `fix/`, `docs/`, `refactor/`, `test/`, `chore/`, `perf/`, `style/`
   ```bash
   git checkout -b feat/short-desc
   ```
3. Make changes. Follow `CONTRIBUTING.md` PR checklist:
   - branch name + clear commits, tests pass, docs updated, no secrets.
   - Commit format: `<type>(<scope>): <short description>`, <72 chars. Types: `feat|fix|docs|refactor|test|chore|perf|style`.
4. Verify before push:
   ```bash
   git status --short
   git diff --check
   pytest tests/ -q
   # if touched services:
   # bash scripts/test.sh --coverage
   # cd services/management-panel && npm run lint && npm run test:coverage
   ```
   CI runs gitleaks, flake8/black/isort, pytest, shellcheck, terraform validate, markdownlint — keep diffs clean.
5. Commit + push **only when user explicitly asked**:
   ```bash
   git add <intended files only>
   git commit -m "feat(scope): short desc"
   GIT_SSH_COMMAND="ssh -i ~/.ssh/infra-pilot-tmp -o IdentitiesOnly=yes" git push -u deploy-ssh <branch>
   ```
6. Do NOT run `gh pr create` — it fails with deploy keys. Instead output:
   - branch name, commit(s), test result, files changed
   - Ask owner to open PR: repo page → `Compare & pull request` → base `main`.

## 3. Rules

- NEVER push to `main`, never force-push, never `git push --force`.
- NEVER commit secrets, tokens, `.env`, private keys. CI blocks on gitleaks.
- NEVER run `gh auth login`, change remotes, or delete `~/.ssh/infra-pilot-tmp*`.
- NEVER print the private key. Public key may be shared via link if owner must re-add Deploy key (`Settings > Deploy keys > Allow write access`).
