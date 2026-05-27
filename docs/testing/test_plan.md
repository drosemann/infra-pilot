# test plan

this document outlines the pytest-based test plan for infra-pilot using a mock provider.

test categories
• unit: core utilities and resolver
• integration: adapters and config parsers against mock endpoints
• end-to-end (mock): provisioning/deprovisioning cycles using neutral tokens
• smoke: quick connectivity and basic state validation

neutral tokens and resolver
• tokens: `provider_mock`, `region_mock_us_east`, `sku_mock_small`, etc.
• the resolver translates tokens to mock identities for tests

environment and data
• local (windows and linux) and ci (linux)
• dummy data via environment variables; no secrets in code

test data and fixtures
• central fixtures in `tests/conftest.py`; neutral tokens in all tests
• infra naming utilities under `infra/naming`

running tests
• local: `pytest -m unit/integration/e2e/smoke`
• ci: see `.github/workflows/ci.yml` (produces junit xml reports)

extensibility
• to add a new provider, extend `provider_map.yaml` and `overrides.yaml`; tests reference neutral tokens only
