import pytest
from unittest.mock import patch


import sys

class TestTeardownResources:
    def test_teardown_resources_returns_dict(self):
        from infra.helpers.cleanup import teardown_resources
        result = teardown_resources("PROVIDER_MOCK", {"region": "REGION_MOCK_US_EAST", "sku": "SKU_MOCK_SMALL"})
        assert result["deleted"] is True
        assert result["provider"] == "mock-provider"
        assert result["region"] == "mock-region-us-east"
        assert result["sku"] == "mock-sku-small"

    def test_teardown_resources_defaults(self):
        from infra.helpers.cleanup import teardown_resources
        result = teardown_resources("PROVIDER_MOCK", {})
        assert result["deleted"] is True
        assert result["region"] == "mock-region-us-east"

    def test_teardown_passes_config(self):
        from infra.helpers.cleanup import teardown_resources
        config = {"custom_key": "custom_val", "region": "REGION_MOCK_US_WEST"}
        result = teardown_resources("PROVIDER_MOCK", config)
        assert result["config"]["custom_key"] == "custom_val"
        assert result["region"] == "mock-region-us-west"


class TestProvisionResources:
    def test_provision_resources_returns_dict(self):
        from infra.helpers.provisioning import provision_resources
        result = provision_resources("PROVIDER_MOCK", {"region": "REGION_MOCK_US_EAST", "sku": "SKU_MOCK_SMALL"})
        assert result["created"] is True
        assert result["provider"] == "mock-provider"
        assert result["region"] == "mock-region-us-east"
        assert result["sku"] == "mock-sku-small"

    def test_provision_resources_defaults(self):
        from infra.helpers.provisioning import provision_resources
        result = provision_resources("PROVIDER_MOCK", {})
        assert result["created"] is True
        assert result["sku"] == "mock-sku-small"

    def test_provision_passes_config(self):
        from infra.helpers.provisioning import provision_resources
        config = {"custom_key": "custom_val", "sku": "SKU_MOCK_LARGE"}
        result = provision_resources("PROVIDER_MOCK", config)
        assert result["config"]["custom_key"] == "custom_val"
        assert result["sku"] == "mock-sku-large"

    def test_provision_unknown_token(self):
        from infra.helpers.provisioning import provision_resources
        result = provision_resources("UNKNOWN", {"region": "UNKNOWN_REGION"})
        assert result["created"] is True
        assert result["provider"] == "UNKNOWN"
        assert result["region"] == "UNKNOWN_REGION"
