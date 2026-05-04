- Integration Test Scaffolding
==========================

- Purpose
  - Provide a growth path for end-to-end / integration tests as services come online.
- Structure
  - tests/integration/
    - __init__.py
    - test_smoke_runtime.py
    - README.md
- How to run
  - Run: pytest -q
  - Pytest will discover tests in tests/integration because we use the pattern `test_*.py` and pytest markers (`smoke`, `integration`).
- How to expand
  - Add new test modules under this directory, e.g. `test_smoke_<area>.py` for lightweight checks or `test_<scenario>.py` for deeper integration flows.
  - Implement real service clients / fixtures as services come online.

- Scaffolding notes
  - Start with a minimal integration test that exercises a single service using its REST/gRPC/CLI surface.
  - Add service-specific fixtures in conftest.py or in a tests/fixtures/ directory as you add tests.
  - Use pytest markers (e.g., @pytest.mark.integration) to separate integration tests from unit tests.
  - Consider using a lightweight test harness to mock or stub external dependencies during early iterations.
