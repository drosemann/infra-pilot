"""Tests for data_catalog module."""
import pytest
from services.integration_service.src.data_platform.data_catalog import (
    CatalogManager, CatalogAsset, HarvestRun
)

@pytest.fixture
def manager():
    mgr = CatalogManager()
    yield mgr
    mgr._assets.clear()

class TestAssetCRUD:
    def test_register_asset(self, manager):
        a = manager.register_asset(name="users_table", type="table", schema="public", owner="data-team")
        assert a.asset_id is not None
        assert a.name == "users_table"
        assert a.certified is False

    def test_get_asset(self, manager):
        a = manager.register_asset(name="test", type="table", schema="public")
        retrieved = manager.get_asset(a.asset_id)
        assert retrieved is not None

    def test_list_assets(self, manager):
        manager.register_asset(name="a1", type="table", schema="public")
        manager.register_asset(name="a2", type="view", schema="analytics")
        assert len(manager.list_assets()) >= 2

class TestSearch:
    def test_search(self, manager):
        manager.register_asset(name="customer_orders", type="table", schema="public")
        results = manager.search("customer")
        assert len(results) >= 1
        assert any("customer" in a.name for a in results)

class TestHarvest:
    def test_harvest(self, manager):
        result = manager.run_harvest()
        assert result.status == "completed"
        assert result.assets_found > 0

class TestCertification:
    def test_certify_asset(self, manager):
        a = manager.register_asset(name="cert_test", type="table", schema="public")
        certified = manager.certify_asset(a.asset_id)
        assert certified is True
        assert manager.get_asset(a.asset_id).certified is True
