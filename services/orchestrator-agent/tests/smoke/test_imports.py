import importlib


def test_core_orchestrator_modules_import():
    module = importlib.import_module("vps_manager")
    assert hasattr(module, "VPSManager")
    assert hasattr(module, "VPSConfig")
