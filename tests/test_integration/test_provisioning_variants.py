from infra.helpers import provisioning
from infra.naming import resolver
import pytest


@pytest.mark.integration
def test_provision_variants_basic():
    cfg = {"region": "REGION_MOCK_US_WEST", "sku": "SKU_MOCK_MEDIUM"}
    result = provisioning.provision_resources("PROVIDER_MOCK", cfg)
    assert result["created"] is True
    assert result["region"] == resolver.resolve_provider("REGION_MOCK_US_WEST")
    assert result["sku"] == resolver.resolve_provider("SKU_MOCK_MEDIUM")
