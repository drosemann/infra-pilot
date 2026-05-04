from typing import Dict
from infra.naming import resolver

def teardown_resources(token: str, config: Dict[str, str]) -> Dict[str, object]:
    """Simulate teardown/cleanup of resources provisioned via the mock provider.
    This is a lightweight stub to enable end-to-end testing of lifecycle.
    """
    provider = resolver.resolve_provider(token)
    region = resolver.resolve_provider(config.get("region", "REGION_MOCK_US_EAST"))
    sku = resolver.resolve_provider(config.get("sku", "SKU_MOCK_SMALL"))
    return {
        "deleted": True,
        "provider": provider,
        "region": region,
        "sku": sku,
        "config": config,
    }
