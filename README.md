# Infra-pilot: Testing Plan and Routine

Coverage badge
- Coverage: ![Coverage](https://img.shields.io/badge/coverage-__COVERAGE__%25-brightgreen)
Usage: run scripts/coverage_report.sh to refresh coverage and coverage report artifacts.
- Coverage: ![Coverage](https://img.shields.io/badge/coverage-__COVERAGE__%25-brightgreen)

This repository includes a pytest-based test suite using a mock provider for Infra-pilot.
The tests are designed to run on Linux VPS/bare-metal servers and locally on Windows.

Documentation
- For detailed testing strategy and runbooks, see docs/testing/

Overview
- Framework: pytest (Python)
- Provider: neutral tokens (mock provider)
- Environment: controlled via environment variables (dummy data for testing)
- CI: GitHub Actions (Linux runners)

How to run locally
- Prerequisites: Python 3.9+, virtualenv/venv, dependencies in requirements.txt
- Install deps: `python -m venv venv; source venv/bin/activate; pip install -r requirements.txt`
- Unit tests: `pytest -m unit`
- Integration tests: `pytest -m integration`
- E2E tests (mock provider): `pytest -m e2e`
- Set env vars as needed, e.g. `export TEST_ENV=local` or use Windows equivalents

Neutral naming
- Tests reference neutral tokens such as PROVIDER_MOCK, REGION_MOCK_US_EAST, SKU_MOCK_SMALL
- A resolver translates tokens to mock identities via inf ras naming maps

Documentation
- See docs/testing for detailed plans, mappings, and runbooks
