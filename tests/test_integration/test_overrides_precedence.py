from infra.helpers import provisioning
from infra.naming import resolver
import pytest
import yaml
from pathlib import Path


@pytest.mark.integration
def test_overrides_precedence(tmp_path, monkeypatch):
    # Create an overrides file that changes PROVIDER_MOCK and REGION/ SKU
    overrides = {
        "PROVIDER_MOCK": "mock-provider-override-a",
        "REGION_MOCK_US_EAST": "mock-region-us-east-override-a",
        "SKU_MOCK_SMALL": "mock-sku-small-override-a",
    }
    overrides_path = tmp_path / "provider_map.yaml"
    with open(overrides_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(overrides, f)

    monkeypatch.setenv("PROVIDER_CONFIG_OVERRIDE", str(overrides_path))
    # Force resolver to reload overrides
    resolver.refresh_map()

    cfg = {"region": "REGION_MOCK_US_EAST", "sku": "SKU_MOCK_SMALL"}
    result = provisioning.provision_resources("PROVIDER_MOCK", cfg)

    assert result["provider"] == "mock-provider-override-a"
    assert result["region"] == "mock-region-us-east-override-a"
    assert result["sku"] == "mock-sku-small-override-a"
