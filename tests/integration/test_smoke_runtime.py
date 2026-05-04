from pathlib import Path
import importlib.util

import pytest

pytestmark = [pytest.mark.smoke, pytest.mark.integration]

ROOT = Path(__file__).resolve().parents[2]


def _load_module_from_path(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_smoke_required_config_files_exist():
    # Purpose: ensure baseline local/dev configuration templates are committed and discoverable.
    # Acceptance criterion: .env.example and integration test README exist at repository-expected paths.
    assert (ROOT / ".env.example").is_file()
    assert (ROOT / "tests/integration/README.md").is_file()


def test_smoke_central_python_modules_loadable():
    # Purpose: verify core Python entry modules load without syntax/import-time failures.
    # Acceptance criterion: loading orchestrator and AWS helper modules succeeds from their file paths.
    orchestrator_module = _load_module_from_path(
        "orchestrator_integration", ROOT / "services/orchestrator-agent/integration.py"
    )
    aws_module = _load_module_from_path("aws_extended_001", ROOT / "modules/aws_extended_001.py")

    assert orchestrator_module is not None
    assert aws_module is not None


def test_smoke_expected_service_constant_present():
    # Purpose: guard key service wiring defaults used by integration surfaces.
    # Acceptance criterion: INTEGRATION_SERVICE_URL constant exists and defaults to localhost:9000.
    module = _load_module_from_path(
        "orchestrator_integration_constants", ROOT / "services/orchestrator-agent/integration.py"
    )

    assert hasattr(module, "INTEGRATION_SERVICE_URL")
    assert module.INTEGRATION_SERVICE_URL == "http://localhost:9000"
