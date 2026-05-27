# automated test suite

infra pilot uses service-local test suites so each component can run quickly with deterministic mocks and still feed ci coverage reports.

## one-command local run

```bash
tools/run-all-tests.sh --offline
```

use `--offline` when dependencies are already installed. without it, the script installs each service's dependencies before executing the service test command.

## management panel (`services/management-panel`)

commands:

• `npm run test:unit` runs fast node test-runner unit tests.
• `npm run test:api` runs express api integration tests against an in-memory supabase mock.
• `npm run test:coverage` emits node test coverage for ci.
• `npm run test:playwright` runs browser e2e tests.

shared test infrastructure lives in `tests/helpers/`:
• `supabase-mock.ts` — reusable `querybuilder`, `makesupabase`, and type aliases for in-memory supabase mocking.
• `http-client.ts` — `request` and `requestwithheaders` helpers for firing http requests at the test server.

current critical coverage targets:

• auth/session helpers and token storage.
• unauthorized api access returns `401`.
• docker app ownership filtering.
• personal mode blocks business mode endpoints.
• invalid setup payloads return `400`.
• demo flag behavior follows `vite_demo_feature_enabled`.
• demo seed is idempotent for customers and docker apps per owner.
• rate-limit headers conform to the `ratelimit-*` draft-6 standard.

## orchestrator agent (`services/orchestrator-agent`)

commands:

• `pytest -q` runs unit and smoke tests with `pytest-cov`.

the suite provides reusable docker mocks in `tests/conftest.py` and currently covers vps configuration translation, docker runtime error handling, and docker statistics normalization. the service-level coverage gate starts at 35% for the currently tested orchestration module and should be raised as command handlers, provider adapters, and monitoring helpers are hardened.

## service core (`services/service-core`)

commands:

• `mvn -B test jacoco:report jacoco:check` runs junit 5 tests, emits surefire reports, and enforces the jacoco line-coverage gate.

the test stack is junit 5, mockito, and assertj. the coverage plugin is configured for future lifecycle, database boundary, event, and plugin bootstrap tests. no application tests have been written yet — this is a known gap.

## ci gates

the github workflows run lint/build/test jobs per service and upload coverage reports. playwright failures are now fatal in ci; do not reintroduce `|| true` around e2e test commands.
