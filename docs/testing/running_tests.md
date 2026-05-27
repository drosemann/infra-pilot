# running tests

• local development
  • unit tests: `pytest -m unit`
  • integration tests: `pytest -m integration`
  • end-to-end tests: `pytest -m e2e`
  • all tests with coverage: `pytest --maxfail=1 --disable-warnings -q`
  • set environment vars as needed, e.g. `test_env=local`, `provider_mock_api_url`, etc.

• ci (github actions)
  • the repository includes a github actions workflow that runs unit, integration, and e2e tests on linux runners and collects junit xml reports.
  • see `.github/workflows/ci.yml` for details.

• windows compatibility
  • tests avoid shell-specific behavior; run under windows python or wsl as preferred.

coverage reports
• a light coverage report is now produced via pytest-cov and uploaded in ci as an artifact.
• local runs can generate coverage html under `coverage_html/` and an xml report at `coverage.xml` by enabling pytest options in `pytest.ini`.
