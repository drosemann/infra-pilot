# Contributing

- Local testing and linting
  - Linting: run the repository-wide linter with: `bash tools/lint-all.sh`.
  - Full local test run: run all tests with: `bash tools/run-all-tests.sh`.
  - Per-service testing (optional):
    - Node services: in a service directory that has a `package.json` with a `test` script, run `npm test`.
    - Python services: ensure a `requirements.txt` is present if needed, then run your pytest-based tests in the service directory (e.g. `pytest` or `pytest tests`).
  - Integration tests: if present, run via the project's pytest harness (e.g. `pytest tests/integration`).

- CI behavior
  - CI is implemented with GitHub Actions and executes the same test suite locally when possible.
  - The default CI environment uses Node.js v18 and Python 3.x across workflows, ensuring consistency with local runs.
  - For new services, ensure there is a test script (Node) or a pytest setup (Python) so CI can execute tests automatically.

- Guidance for new services
  - Add a package.json with a `test` script for Node services, or provide a Python setup with pytest, so the CI and local tooling can run tests consistently.
