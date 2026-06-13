"""Tests for cog_data_catalog module."""
import pytest
from services.orchestrator_agent.cogs.data_platform.cog_data_catalog import CogDataCatalog

@pytest.fixture
def cog():
    return CogDataCatalog()

class TestCogCatalog:
    def test_list(self, cog):
        result = cog.list()
        assert isinstance(result, list)

    def test_search(self, cog):
        cog.register(name="users_table", type="table", schema="public", owner="data-team")
        result = cog.search("users")
        assert len(result) >= 1

    def test_register(self, cog):
        result = cog.register(name="orders_view", type="view", schema="analytics", owner="analytics-team")
        assert result["name"] == "orders_view"

    def test_harvest(self, cog):
        result = cog.harvest()
        assert result["status"] == "completed"

    def test_certify(self, cog):
        a = cog.register(name="cert-asset", type="table", schema="public", owner="data-team")
        result = cog.certify(a["asset_id"])
        assert result["certified"] is True

    def test_deploy(self, cog):
        result = cog.deploy(name="dep-asset", type="table", schema="public", owner="data-team", tags="critical,production")
        assert result["name"] == "dep-asset"

    def test_monitor(self, cog):
        a = cog.register(name="mon-asset", type="table", schema="public", owner="data-team")
        result = cog.monitor(a["asset_id"])
        assert result["asset_id"] == a["asset_id"]
