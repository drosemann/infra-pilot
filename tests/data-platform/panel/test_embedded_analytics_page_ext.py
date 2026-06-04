"""Tests for EmbeddedAnalyticsPage component."""
import pytest
from services.management_panel.src.pages.data_platform.EmbeddedAnalyticsPage import EmbeddedAnalyticsPage

class TestEmbeddedAnalyticsPage:
    def test_page_render(self):
        assert EmbeddedAnalyticsPage is not None

    def test_customers_state(self):
        page = EmbeddedAnalyticsPage()
        assert hasattr(page, "customers")

    def test_create_customer(self):
        page = EmbeddedAnalyticsPage()
        n = len(page.customers)
        page.create_customer("Acme Corp", "acme.com")
        assert len(page.customers) == n + 1

    def test_rotate_key(self):
        page = EmbeddedAnalyticsPage()
        page.create_customer("KeyCorp", "key.com")
        cid = page.customers[0]["customer_id"]
        old_key = page.customers[0]["api_key"]
        result = page.rotate_key(cid)
        assert result["api_key"] != old_key

    def test_create_embed(self):
        page = EmbeddedAnalyticsPage()
        page.create_customer("EmbedCo", "embed.com")
        cid = page.customers[0]["customer_id"]
        n = len(page.embeds)
        page.create_embed(cid, "dashboard", {"region": "us"})
        assert len(page.embeds) == n + 1

    def test_get_code(self):
        page = EmbeddedAnalyticsPage()
        page.create_customer("CodeCo", "code.com")
        cid = page.customers[0]["customer_id"]
        page.create_embed(cid, "dashboard")
        result = page.get_embed_code(page.embeds[0]["embed_id"])
        assert "iframe" in result["code"]

    def test_stats(self):
        page = EmbeddedAnalyticsPage()
        page.create_customer("StatsCo", "stats.com")
        cid = page.customers[0]["customer_id"]
        page.create_embed(cid, "dashboard")
        result = page.get_stats()
        assert result["total_customers"] >= 1

    def test_delete_customer(self):
        page = EmbeddedAnalyticsPage()
        page.create_customer("DelCo", "del.com")
        cid = page.customers[0]["customer_id"]
        page.delete_customer(cid)
        assert cid not in [c["customer_id"] for c in page.customers]

    def test_delete_embed(self):
        page = EmbeddedAnalyticsPage()
        page.create_customer("DelEmb", "del.com")
        page.create_embed(page.customers[0]["customer_id"], "widget")
        eid = page.embeds[0]["embed_id"]
        page.delete_embed(eid)
        assert eid not in [e["embed_id"] for e in page.embeds]
