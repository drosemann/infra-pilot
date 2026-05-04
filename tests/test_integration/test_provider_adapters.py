from infra.helpers import provisioning
from infra.naming import resolver
import pytest


@pytest.mark.integration
def test_mock_provisioning_basic():
    cfg = {"region": "REGION_MOCK_US_EAST", "sku": "SKU_MOCK_SMALL"}
    result = provisioning.provision_resources("PROVIDER_MOCK", cfg)

    assert result["created"] is True
    assert result["provider"] == resolver.resolve_provider("PROVIDER_MOCK")
    assert result["region"] == resolver.resolve_provider("REGION_MOCK_US_EAST")
    assert result["sku"] == resolver.resolve_provider("SKU_MOCK_SMALL")
