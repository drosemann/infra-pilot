# testing guide

- testpyramide (kompakt)
  - unit: schnell, isoliert, ohne externe dienste; fokus auf business-logik und randfälle.
  - integration: zusammenspiel mehrerer komponenten (z. b. api + datenzugriff), optional mit mocks/test-doubles.
  - e2e/smoke: wenige, stabile tests für kritische happy paths über reale schnittstellen.

- laufzeitbudget und zielabdeckung
  - unit
    - laufzeitbudget: lokal < 2 minuten pro service.
    - zielabdeckung: mindestens 80% line-coverage pro service (kritische kernmodule höher).
  - integration
    - laufzeitbudget: lokal < 10 minuten gesamt.
    - zielabdeckung: alle zentralen integrationspunkte (api, persistenz, messaging/webhooks) mindestens einmal positiv getestet.
  - e2e/smoke
    - laufzeitbudget: lokal/ci < 15 minuten gesamt.
    - zielabdeckung: 100% der geschäftskritischen happy paths (login/health/provisionierung o. ä. je service).

- ablagekonventionen pro service (`services/*`)
  - empfohlene struktur in jedem service-ordner:
    - `tests/unit` für unit-tests.
    - `tests/integration` für service-interne integrationstests.
    - `tests/smoke` (oder `tests/e2e`) für smoke/e2e-tests.
  - sprache/runtime-spezifisch:
    - python-services (pytest): discovery unter `tests/`, idealerweise getrennt nach den ordnern oben.
    - node-services: test-runner so konfigurieren, dass die gleichen pfade genutzt werden.
  - repository-weite integrationstests bleiben unter `tests/integration` im repo-root möglich, wenn mehrere services beteiligt sind.

- what runs where
  - node services: tests are discovered via the package.json's test script. if absent, tests are skipped by the runner.
  - python services: tests are discovered by pytest under tests/ directories inside the service; if none, runner skips.
  - integration tests: lightweight smoke/integration checks live in `tests/integration/test_smoke_*.py` and run with pytest.

- test naming convention
  - dateinamen: `test_<modul>_<verhalten>.py`
  - testfunktionen: `test_<given>_<when>_<then>`
  - beispiele:
    - `test_aws_service_defaults.py`
    - `test_given_ec2_service_when_initialized_then_applies_ec2_defaults`

- local testing workflow
  - empfohlene reihenfolge: `lint -> unit -> integration -> smoke`.
  - linting: `bash tools/lint-all.sh`.
  - full test suite: `bash tools/run-all-tests.sh`.
  - per-service testing:
    - node: navigate to a service directory that has a `package.json` with a `test` script and run `npm test`.
    - python: ensure a `requirements.txt` exists if needed; run tests with your pytest-based commands (e.g. `pytest` in the service directory).
  - integration tests: run `pytest tests/integration`.
  - marker-based selection:
    - smoke-only checks: `pytest -m smoke tests/integration`
    - integration suite: `pytest -m integration tests/integration`

- local linting and style checks
  - use the repository-wide linter: `bash tools/lint-all.sh`.
  - if your service has additional linters or formatters, run them per-service if applicable.

- ci behavior
  - ci runs on github actions and executes the same test suite as your local commands.
  - the default ci environment uses node.js v18 and python 3.x to mirror local expectations.
  - see the workflows under .github/workflows (e.g. ci-core.yml, ci-dashboard.yml, ci-discord.yml, ci-orchestrator.yml) for exact steps and matrices.
  - for new services, ensure a test script (node) or pytest setup (python) so ci can run tests automatically.

- marker definitions
  - `@pytest.mark.smoke`: fast confidence checks (config presence, importability, critical constants).
  - `@pytest.mark.integration`: integration-scoped tests under `tests/integration`.
