# Test Plan

This document outlines the pytest-based test plan for Infra-pilot using a mock provider.

Test categories
- Unit: core utilities and resolver
- Integration: adapters and config parsers against mock endpoints
- End-to-end (mock): provisioning/deprovisioning cycles using neutral tokens
- Smoke: quick connectivity and basic state validation

Neutral tokens and resolver
- Tokens: PROVIDER_MOCK, REGION_MOCK_US_EAST, SKU_MOCK_SMALL, etc.
- The resolver translates tokens to mock identities for tests

Environment and data
- LOCAL (Windows and Linux) and CI (Linux)
- Dummy data via environment variables; no secrets in code

Test data and fixtures
- Central fixtures in tests/conftest.py; neutral tokens in all tests
- Infra naming utilities under infra/naming

Running tests
- Local: pytest -m unit/integration/e2e/smoke
- CI: See .github/workflows/ci.yml (produces JUnit XML reports)

Extensibility
- To add a new provider, extend provider_map.yaml and overrides.yaml; tests reference neutral tokens only
