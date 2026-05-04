(# Testing Guide)

- Testpyramide (kompakt)
  - Unit: schnell, isoliert, ohne externe Dienste; Fokus auf Business-Logik und Randfälle.
  - Integration: Zusammenspiel mehrerer Komponenten (z. B. API + Datenzugriff), optional mit Mocks/Test-Doubles.
  - E2E/Smoke: wenige, stabile Tests für kritische Happy Paths über reale Schnittstellen.

- Laufzeitbudget und Zielabdeckung
  - Unit
    - Laufzeitbudget: lokal < 2 Minuten pro Service.
    - Zielabdeckung: mindestens 80% Line-Coverage pro Service (kritische Kernmodule höher).
  - Integration
    - Laufzeitbudget: lokal < 10 Minuten gesamt.
    - Zielabdeckung: alle zentralen Integrationspunkte (API, Persistenz, Messaging/Webhooks) mindestens einmal positiv getestet.
  - E2E/Smoke
    - Laufzeitbudget: lokal/CI < 15 Minuten gesamt.
    - Zielabdeckung: 100% der geschäftskritischen Happy Paths (Login/Health/Provisionierung o. ä. je Service).

- Ablagekonventionen pro Service (`services/*`)
  - Empfohlene Struktur in jedem Service-Ordner:
    - `tests/unit` für Unit-Tests.
    - `tests/integration` für service-interne Integrationstests.
    - `tests/smoke` (oder `tests/e2e`) für Smoke/E2E-Tests.
  - Sprache/Runtime-spezifisch:
    - Python-Services (pytest): Discovery unter `tests/`, idealerweise getrennt nach den Ordnern oben.
    - Node-Services: Test-Runner so konfigurieren, dass die gleichen Pfade genutzt werden.
  - Repository-weite Integrationstests bleiben unter `tests/integration` im Repo-Root möglich, wenn mehrere Services beteiligt sind.

- What runs where
  - Node services: tests are discovered via the package.json's test script. If absent, tests are skipped by the runner.
  - Python services: tests are discovered by pytest under tests/ directories inside the service; if none, runner skips.
  - Integration tests: lightweight smoke/integration checks live in `tests/integration/test_smoke_*.py` and run with pytest.


- Test Naming Convention
  - Dateinamen: `test_<modul>_<verhalten>.py`
  - Testfunktionen: `test_<given>_<when>_<then>`
  - Beispiele:
    - `test_aws_service_defaults.py`
    - `test_given_ec2_service_when_initialized_then_applies_ec2_defaults`

- Local testing workflow
  - Empfohlene Reihenfolge: `lint -> unit -> integration -> smoke`.
  - Linting: `bash tools/lint-all.sh`.
  - Full test suite: `bash tools/run-all-tests.sh`.
  - Per-service testing:
    - Node: navigate to a service directory that has a `package.json` with a `test` script and run `npm test`.
    - Python: ensure a `requirements.txt` exists if needed; run tests with your pytest-based commands (e.g. `pytest` in the service directory).
  - Integration tests: run `pytest tests/integration`.
  - Marker-based selection:
    - Smoke-only checks: `pytest -m smoke tests/integration`
    - Integration suite: `pytest -m integration tests/integration`

- Local linting and style checks
  - Use the repository-wide linter: `bash tools/lint-all.sh`.
  - If your service has additional linters or formatters, run them per-service if applicable.

- CI behavior
  - CI runs on GitHub Actions and executes the same test suite as your local commands.
  - The default CI environment uses Node.js v18 and Python 3.x to mirror local expectations.
  - See the workflows under .github/workflows (e.g. ci-core.yml, ci-dashboard.yml, ci-discord.yml, ci-orchestrator.yml) for exact steps and matrices.
  - For new services, ensure a test script (Node) or pytest setup (Python) so CI can run tests automatically.

- Marker definitions
  - `@pytest.mark.smoke`: Fast confidence checks (config presence, importability, critical constants).
  - `@pytest.mark.integration`: Integration-scoped tests under `tests/integration`.
