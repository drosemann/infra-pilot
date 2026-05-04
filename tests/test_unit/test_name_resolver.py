import pytest
from infra.naming import resolver
import os


@pytest.mark.unit
def test_resolve_provider_mock():
    # Basic sanity: neutral token maps to the configured mock provider
    assert resolver.resolve_provider("PROVIDER_MOCK") == "mock-provider"

@pytest.mark.unit
def test_current_env_fallback():
    # Should return a string; if not set, defaults to 'local'
    env = resolver.current_env()
    assert isinstance(env, str)

def test_overrides_loading(tmp_path, monkeypatch):
    # Create a temporary overrides file and point resolver to it
    overrides = {
        "PROVIDER_MOCK": "mock-provider-override",
        "REGION_MOCK_US_EAST": "mock-region-us-east-override",
        "SKU_MOCK_SMALL": "mock-sku-small-override",
    }
    overrides_path = tmp_path / "provider_map.yaml"
    import yaml
    with open(overrides_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(overrides, f)

    # Point to the overrides file via env var
    monkeypatch.setenv("PROVIDER_CONFIG_OVERRIDE", str(overrides_path))
    # Trigger a refresh so that the override is picked up
    resolver.refresh_map()

    assert resolver.resolve_provider("PROVIDER_MOCK") == "mock-provider-override"
    assert resolver.resolve_provider("REGION_MOCK_US_EAST") == "mock-region-us-east-override"
    assert resolver.resolve_provider("SKU_MOCK_SMALL") == "mock-sku-small-override"
