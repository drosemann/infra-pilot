"""Tests for cog_embedded_analytics module."""
import pytest
from services.orchestrator_agent.cogs.data_platform.cog_embedded_analytics import CogEmbeddedAnalytics

@pytest.fixture
def cog():
    return CogEmbeddedAnalytics()

class TestCogEmbed:
    def test_list_customers(self, cog):
        result = cog.list_customers()
        assert isinstance(result, list)

    def test_create_customer(self, cog):
        result = cog.create_customer(name="Acme Corp", domain="acme.com")
        assert result["name"] == "Acme Corp"
        assert "api_key" in result

    def test_rotate_key(self, cog):
        c = cog.create_customer(name="KeyCorp", domain="key.com")
        result = cog.rotate_key(c["customer_id"])
        assert result["api_key"] != c["api_key"]

    def test_list_embeds(self, cog):
        result = cog.list_embeds()
        assert isinstance(result, list)

    def test_create_embed(self, cog):
        c = cog.create_customer(name="EmbedCo", domain="embed.com")
        result = cog.create_embed(customer_id=c["customer_id"], type="dashboard", filters={"region": "us"})
        assert result["type"] == "dashboard"

    def test_get_code(self, cog):
        c = cog.create_customer(name="CodeCo", domain="code.com")
        e = cog.create_embed(customer_id=c["customer_id"], type="dashboard")
        result = cog.get_code(e["embed_id"])
        assert "iframe" in result["code"]

    def test_delete_embed(self, cog):
        c = cog.create_customer(name="DelCo", domain="del.com")
        e = cog.create_embed(customer_id=c["customer_id"], type="widget")
        assert cog.delete_embed(e["embed_id"]) is True

    def test_stats(self, cog):
        c = cog.create_customer(name="StatsCo", domain="stats.com")
        cog.create_embed(customer_id=c["customer_id"], type="dashboard")
        result = cog.stats()
        assert result["total_customers"] >= 1

    def test_delete_customer(self, cog):
        c = cog.create_customer(name="DelCustomer", domain="del.com")
        assert cog.delete_customer(c["customer_id"]) is True

    def test_deploy(self, cog):
        result = cog.deploy(name="DepCustomer", domain="dep.com", embed_type="dashboard", theme="dark")
        assert result["name"] == "DepCustomer"

    def test_monitor(self, cog):
        c = cog.create_customer(name="MonCo", domain="mon.com")
        result = cog.monitor(c["customer_id"])
        assert result["customer_id"] == c["customer_id"]
