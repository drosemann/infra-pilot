"""Tests for DataCatalogPage component."""
import pytest
from services.management_panel.src.pages.data_platform.DataCatalogPage import DataCatalogPage

class TestDataCatalogPage:
    def test_page_render(self):
        assert DataCatalogPage is not None

    def test_assets_state(self):
        page = DataCatalogPage()
        assert hasattr(page, "assets")

    def test_register_asset(self):
        page = DataCatalogPage()
        n = len(page.assets)
        page.register_asset("users_table", "table", "public", "data-team")
        assert len(page.assets) == n + 1

    def test_search(self):
        page = DataCatalogPage()
        page.register_asset("customer_orders", "table", "public", "data-team")
        results = page.search("customer")
        assert len(results) >= 1

    def test_harvest(self):
        page = DataCatalogPage()
        result = page.run_harvest()
        assert result["status"] == "completed"

    def test_certify(self):
        page = DataCatalogPage()
        page.register_asset("cert_test", "table", "public", "data-team")
        aid = page.assets[0]["asset_id"]
        result = page.certify_asset(aid)
        assert result["certified"] is True
