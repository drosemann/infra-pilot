# Running Tests

- Local development
  - Unit tests: pytest -m unit
  - Integration tests: pytest -m integration
  - End-to-end tests: pytest -m e2e
  - All tests with coverage: pytest --maxfail=1 --disable-warnings -q
  - Set environment vars as needed, e.g. TEST_ENV=local, PROVIDER_MOCK_API_URL, etc.

- CI (GitHub Actions)
  - The repository includes a GitHub Actions workflow that runs unit, integration, and e2e tests on Linux runners and collects JUnit XML reports.
  - See .github/workflows/ci.yml for details.

- Windows compatibility
  - Tests avoid shell-specific behavior; run under Windows Python or WSL as preferred.
- CI (GitHub Actions)
  - The repository includes a GitHub Actions workflow that runs unit, integration, and e2e tests on Linux runners and collects JUnit XML reports.
  - See .github/workflows/ci.yml for details.

- Windows compatibility
  - Tests avoid shell-specific behavior; run under Windows Python or WSL as preferred.

Coverage reports
- A light coverage report is now produced via pytest-cov and uploaded in CI as an artifact.
- Local runs can generate coverage HTML under coverage_html/ and an XML report at coverage.xml by enabling pytest options in pytest.ini.
