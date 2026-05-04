## Warranty & Liability
This software is provided "as is", without warranty of any kind. See the LICENSE file for the full GPL-3.0 disclaimer of warranty and limitation of liability.

I'm not responsible if this breaks your setup. Test it before using it in production.

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

- See docs/CI_DEMO_GATE.md for CI gating verification and local run steps for the Seed Demo gating.

## What changed today (Overview of changes)
- Observability: added request instrumentation and enhanced /health with metrics.
- Backend MVP: /api/customers CRUD (Business mode) with RLS; seed scaffolding for local demos.
- Seed data: seeds/customers.sample.json and seed scripts.
- Seed Demo: UI button with a modal, gated by per-env flag VITE_DEMO_FEATURE_ENABLED; 1-click demo flow via /api/seed-demo.
- Global demo status badge: new DemoFlagBadge shown in header; global across app.
- CI: GitHub Actions updated to exercise gating in two CI runs (flag true/false), plus a gating test demo_gate.spec.ts.
- Tests: new Playwright test demo_gate.spec.ts to verify gating against environment flag; existing health test preserved.
- Documentation: added README snippets describing the per-env gating and how to configure VITE_DEMO_FEATURE_ENABLED, plus QA checklist.
- UI polish: Customers page improved with Seed Demo modal; Confirm flow added; badge present across app.
