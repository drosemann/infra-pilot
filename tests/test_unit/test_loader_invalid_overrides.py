import pytest
from infra.naming import resolver


@pytest.mark.unit
def test_invalid_overrides_yaml_does_not_break(tmp_path, monkeypatch):
    # Create invalid YAML overrides file
    path = tmp_path / "bad_overrides.yaml"
    path.write_text("not: [valid", encoding="utf-8")
    monkeypatch.setenv("PROVIDER_CONFIG_OVERRIDE", str(path))
    # Should not raise during refresh; map should remain usable
    resolver.refresh_map()
    # Basic sanity: resolve of a known token still returns something (fallbacks to token if not in map)
    token = "PROVIDER_MOCK"
    _ = resolver.resolve_provider(token)
