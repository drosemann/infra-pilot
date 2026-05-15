# CI architecture

This repository uses a small set of stack-specific GitHub Actions workflows. The
Node.js services share one reusable implementation, while the Java and Python
services keep dedicated workflows because they have different build tools,
runtimes, and infrastructure requirements.

## Workflow structure

| Workflow | Purpose | Trigger scope |
| --- | --- | --- |
| `.github/workflows/ci-core.yml` | Java `service-core` validation and Docker publishing. | `services/service-core/**` |
| `.github/workflows/ci-orchestrator.yml` | Python `orchestrator-agent` validation and Docker publishing. | `services/orchestrator-agent/**` |
| `.github/workflows/ci-discord.yml` | Thin wrapper for the Discord Node.js service. | `services/discord-service/**` |
| `.github/workflows/ci-dashboard.yml` | Thin wrapper for the management panel Node.js service. | `services/management-panel/**` |
| `.github/workflows/reusable-node-service.yml` | Shared Node.js validation and Docker publishing implementation. | Called by other workflows only. |

## Reusable Node.js workflow

`.github/workflows/reusable-node-service.yml` is invoked with `workflow_call` and
contains the common Node.js CI logic:

1. Check out the repository.
2. Install the configured Node.js version.
3. Restore and save npm cache entries based on the service `package-lock.json`.
4. Run `npm ci` in the service directory.
5. Run lint, type-check, and tests as blocking quality gates.
6. Optionally upload coverage to Codecov.
7. Optionally run a production build.
8. On push events, build and publish a Docker image to GitHub Container Registry
   with Docker metadata-generated tags.

The workflow intentionally does not use `|| true` for linting, type-checking, or
tests. These checks are release gates and should fail the pipeline when they
find a real problem. A non-blocking step should only be added with an inline
comment explaining why a failure is acceptable.

## Adding a new Node.js service

To add a new Node.js service, create a small wrapper workflow that calls the
reusable workflow:

```yaml
name: CI - Example Service (Node.js)

on:
  push:
    branches: [ main, develop ]
    paths:
      - 'services/example-service/**'
  pull_request:
    branches: [ main, develop ]
    paths:
      - 'services/example-service/**'

jobs:
  node-service:
    uses: ./.github/workflows/reusable-node-service.yml
    permissions:
      contents: read
      packages: write
    secrets: inherit
    with:
      service-path: services/example-service
      image-name: ${{ github.repository }}/example-service
```

Useful optional inputs include:

- `node-version`: Node.js version, defaulting to `18`.
- `run-build`: set to `true` when the service has a build or bundle step.
- `lint-command`, `type-check-command`, `test-command`, and `build-command`:
  override the default npm scripts when a service uses different command names.
- `upload-coverage`, `coverage-files`, `coverage-flag`, and `coverage-name`:
  enable Codecov upload for services that already generate coverage artifacts.

## Path filtering strategy

Service wrapper workflows use GitHub Actions `paths` filters so each service CI
runs only when files in that service directory change. This keeps pull request
feedback focused and avoids spending CI minutes on unrelated stacks.

The reusable workflow has no direct `push` or `pull_request` trigger. It runs
only through a wrapper workflow, which keeps path filtering owned by the service
that knows which files should trigger it.

When changing the reusable workflow itself, validate the affected Node.js
service wrappers before merging because a reusable workflow change affects every
Node.js service that calls it.
