(# Testing Guide)

- What runs where
  - Node services: tests are discovered via the package.json's test script. If absent, tests are skipped by the runner.
  - Python services: tests are discovered by pytest under tests/ directories inside the service; if none, runner skips.
  - Integration tests: a lightweight harness collects tests under tests/integration and runs them with pytest.


- Test Naming Convention
  - Dateinamen: `test_<modul>_<verhalten>.py`
  - Testfunktionen: `test_<given>_<when>_<then>`
  - Beispiele:
    - `test_aws_service_defaults.py`
    - `test_given_ec2_service_when_initialized_then_applies_ec2_defaults`

- Local testing workflow
  - Linting: `bash tools/lint-all.sh`.
  - Full test suite: `bash tools/run-all-tests.sh`.
  - Per-service testing:
    - Node: navigate to a service directory that has a `package.json` with a `test` script and run `npm test`.
    - Python: ensure a `requirements.txt` exists if needed; run tests with your pytest-based commands (e.g. `pytest` in the service directory).
  - Integration tests: if a dedicated harness exists, run `pytest tests/integration` (or as defined by the service).

- Local linting and style checks
  - Use the repository-wide linter: `bash tools/lint-all.sh`.
  - If your service has additional linters or formatters, run them per-service if applicable.

- CI behavior
  - CI runs on GitHub Actions and executes the same test suite as your local commands.
  - The default CI environment uses Node.js v18 and Python 3.x to mirror local expectations.
  - See the workflows under .github/workflows (e.g. ci-core.yml, ci-dashboard.yml, ci-discord.yml, ci-orchestrator.yml) for exact steps and matrices.
  - For new services, ensure a test script (Node) or pytest setup (Python) so CI can run tests automatically.
