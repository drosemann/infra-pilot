# ci architecture

this repository uses a small set of stack-specific github actions workflows. the
node.js services share one reusable implementation, while the java and python
services keep dedicated workflows because they have different build tools,
runtimes, and infrastructure requirements.

## workflow structure

| workflow | purpose | trigger scope |
| --- | --- | --- |
| `.github/workflows/ci-core.yml` | java `service-core` validation and docker publishing. | `services/service-core/**` |
| `.github/workflows/ci-orchestrator.yml` | python `orchestrator-agent` validation and docker publishing. | `services/orchestrator-agent/**` |
| `.github/workflows/ci-discord.yml` | thin wrapper for the discord node.js service. | `services/discord-service/**` |
| `.github/workflows/ci-dashboard.yml` | thin wrapper for the management panel node.js service. | `services/management-panel/**` |
| `.github/workflows/reusable-node-service.yml` | shared node.js validation and docker publishing implementation. | called by other workflows only. |

## reusable node.js workflow

`.github/workflows/reusable-node-service.yml` is invoked with `workflow_call` and
contains the common node.js ci logic:

• check out the repository.
• install the configured node.js version.
• restore and save npm cache entries based on the service `package-lock.json`.
• run `npm ci` in the service directory.
• run lint, type-check, and tests as blocking quality gates.
• optionally upload coverage to codecov.
• optionally run a production build.
• on push events, build and publish a docker image to github container registry
  with docker metadata-generated tags.

the workflow intentionally does not use `|| true` for linting, type-checking, or
tests. these checks are release gates and should fail the pipeline when they
find a real problem. a non-blocking step should only be added with an inline
comment explaining why a failure is acceptable.

## adding a new node.js service

to add a new node.js service, create a small wrapper workflow that calls the
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

useful optional inputs include:

• `node-version`: node.js version, defaulting to `18`.
• `run-build`: set to `true` when the service has a build or bundle step.
• `lint-command`, `type-check-command`, `test-command`, and `build-command`:
  override the default npm scripts when a service uses different command names.
• `upload-coverage`, `coverage-files`, `coverage-flag`, and `coverage-name`:
  enable codecov upload for services that already generate coverage artifacts.

## path filtering strategy

service wrapper workflows use github actions `paths` filters so each service ci
runs only when files in that service directory change. this keeps pull request
feedback focused and avoids spending ci minutes on unrelated stacks.

the reusable workflow has no direct `push` or `pull_request` trigger. it runs
only through a wrapper workflow, which keeps path filtering owned by the service
that knows which files should trigger it.

when changing the reusable workflow itself, validate the affected node.js
service wrappers before merging because a reusable workflow change affects every
node.js service that calls it.
