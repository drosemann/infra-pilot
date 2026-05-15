# Automated Test Suite

Infra Pilot uses service-local test suites so each component can run quickly with deterministic mocks and still feed CI coverage reports.

## One-command local run

```bash
tools/run-all-tests.sh --offline
```

Use `--offline` when dependencies are already installed. Without it, the script installs each service's dependencies before executing the service test command.

## Management Panel (`services/management-panel`)

Commands:

- `npm run test:unit` runs fast Node test-runner unit tests.
- `npm run test:api` runs Express API integration tests against an in-memory Supabase mock.
- `npm run test:coverage` emits Node test coverage for CI.
- `npm run test:playwright` runs browser E2E tests.

Current critical coverage targets:

- Auth/session helpers and token storage.
- Unauthorized API access returns `401`.
- Docker app ownership filtering.
- Personal Mode blocks Business Mode endpoints.
- Invalid setup payloads return `400`.
- Demo flag behavior follows `VITE_DEMO_FEATURE_ENABLED`.
- Demo seed is idempotent for customers and Docker apps per owner.

## Orchestrator Agent (`services/orchestrator-agent`)

Commands:

- `pytest -q` runs unit and smoke tests with `pytest-cov`.

The suite provides reusable Docker mocks in `tests/conftest.py` and currently covers VPS configuration translation, Docker runtime error handling, and Docker statistics normalization. The service-level coverage gate starts at 35% for the currently tested orchestration module and should be raised as command handlers, provider adapters, and monitoring helpers are hardened.

## Service Core (`services/service-core`)

Commands:

- `mvn -B test jacoco:report jacoco:check` runs JUnit 5 tests, emits Surefire reports, and enforces the JaCoCo line-coverage gate.

The test stack is JUnit 5, Mockito, and AssertJ. The initial smoke test verifies the Maven test runtime while the coverage plugin is configured for future lifecycle, database boundary, event, and plugin bootstrap tests.

## CI gates

The GitHub workflows run lint/build/test jobs per service and upload coverage reports. Playwright failures are now fatal in CI; do not reintroduce `|| true` around E2E test commands.
