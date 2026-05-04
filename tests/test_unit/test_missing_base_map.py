import pytest
from infra.naming import resolver
from pathlib import Path


@pytest.mark.unit
def test_missing_base_map_monkeypatch(monkeypatch):
    # Point the base map path to a non-existent file to simulate missing base map
    if hasattr(resolver, "_BASE_MAP_PATH"):
        monkeypatch.setattr(resolver, "_BASE_MAP_PATH", Path("/nonexistent/provider_map.yaml"), raising=False)
        resolver.refresh_map()
        # With missing base map, resolution should fall back to token itself
        assert resolver.resolve_provider("PROVIDER_MOCK") == "PROVIDER_MOCK"
