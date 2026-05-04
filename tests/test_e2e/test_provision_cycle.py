import pytest


@pytest.mark.e2e
import pytest

from infra.helpers import provisioning
from infra.helpers import cleanup
from infra.naming import resolver


@pytest.mark.e2e
def test_provision_cycle_full():
    # End-to-end-ish test using the mock provider
    cfg = {"region": "REGION_MOCK_US_EAST", "sku": "SKU_MOCK_SMALL"}
    res = provisioning.provision_resources("PROVIDER_MOCK", cfg)
    assert res["created"] is True

    # Teardown/cleanup should succeed
    cleaned = cleanup.teardown_resources("PROVIDER_MOCK", cfg)
    assert cleaned["deleted"] is True
    assert cleaned["provider"] == resolver.resolve_provider("PROVIDER_MOCK")
