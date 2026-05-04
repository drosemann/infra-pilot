from typing import Dict
from infra.naming import resolver

def provision_resources(token: str, config: Dict[str, str]) -> Dict[str, object]:
    """Simulate provisioning resources using a mock provider.

    The function resolves the neutral tokens via the resolver and returns a
    summary dict representing a successfulProvisioning operation. This is a stub
    backend for unit/integration tests; it does not touch real infrastructure.
    """
    provider = resolver.resolve_provider(token)
    region = resolver.resolve_provider(config.get("region", "REGION_MOCK_US_EAST"))
    sku = resolver.resolve_provider(config.get("sku", "SKU_MOCK_SMALL"))
    # Return a small, deterministic summary suitable for assertions in tests
    return {
        "created": True,
        "provider": provider,
        "region": region,
        "sku": sku,
        "config": config,
    }
