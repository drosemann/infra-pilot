# contributing

- local testing and linting
  - linting: run the repository-wide linter with: `bash tools/lint-all.sh`.
  - full local test run: run all tests with: `bash tools/run-all-tests.sh`.
  - per-service testing (optional):
    - node services: in a service directory that has a `package.json` with a `test` script, run `npm test`.
    - python services: ensure a `requirements.txt` is present if needed, then run your pytest-based tests in the service directory (e.g. `pytest` or `pytest tests`).
  - integration tests: if present, run via the project's pytest harness (e.g. `pytest tests/integration`).

- ci behavior
  - ci is implemented with github actions and executes the same test suite locally when possible.
  - the default ci environment uses node.js v18 and python 3.x across workflows, ensuring consistency with local runs.
  - for new services, ensure there is a test script (node) or a pytest setup (python) so ci can execute tests automatically.

- guidance for new services
  - add a package.json with a `test` script for node services, or provide a python setup with pytest, so the ci and local tooling can run tests consistently.
