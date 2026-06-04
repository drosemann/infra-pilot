"""Tests for embedded_analytics module."""
import pytest
from services.integration_service.src.data_platform.embedded_analytics import (
    EmbedManager, EmbedCustomer, EmbedConfig, EmbedCode, EmbedStats
)

@pytest.fixture
def manager():
    mgr = EmbedManager()
    yield mgr
    mgr._customers.clear()
    mgr._embeds.clear()

class TestCustomerCRUD:
    def test_create_customer(self, manager):
        c = manager.create_customer(name="Acme Corp", domain="acme.com")
        assert c.customer_id is not None
        assert c.name == "Acme Corp"
        assert len(c.api_key) > 20
        assert c.active is True

    def test_get_customer(self, manager):
        c = manager.create_customer(name="Test", domain="test.com")
        retrieved = manager.get_customer(c.customer_id)
        assert retrieved is not None

    def test_list_customers(self, manager):
        manager.create_customer(name="c1", domain="c1.com")
        manager.create_customer(name="c2", domain="c2.com")
        assert len(manager.list_customers()) >= 2

    def test_delete_customer(self, manager):
        c = manager.create_customer(name="del", domain="del.com")
        assert manager.delete_customer(c.customer_id) is True

class TestKeyRotation:
    def test_rotate_key(self, manager):
        c = manager.create_customer(name="key-test", domain="key.com")
        old_key = c.api_key
        rotated = manager.rotate_key(c.customer_id)
        assert rotated is not None
        assert rotated != old_key

class TestEmbedCRUD:
    def test_create_embed(self, manager):
        c = manager.create_customer(name="embed-test", domain="embed.com")
        e = manager.create_embed(customer_id=c.customer_id, type="dashboard", filters={"region": "us"})
        assert e.embed_id is not None
        assert e.type == "dashboard"

    def test_list_embeds(self, manager):
        c = manager.create_customer(name="list-test", domain="list.com")
        manager.create_embed(customer_id=c.customer_id, type="dashboard")
        manager.create_embed(customer_id=c.customer_id, type="report")
        assert len(manager.list_embeds(customer_id=c.customer_id)) >= 2

    def test_delete_embed(self, manager):
        c = manager.create_customer(name="del-embed", domain="del.com")
        e = manager.create_embed(customer_id=c.customer_id, type="widget")
        assert manager.delete_embed(e.embed_id) is True

class TestCodeGeneration:
    def test_get_code(self, manager):
        c = manager.create_customer(name="code-test", domain="code.com")
        e = manager.create_embed(customer_id=c.customer_id, type="dashboard")
        code = manager.get_embed_code(e.embed_id)
        assert code.embed_id == e.embed_id
        assert "iframe" in code.code

class TestStats:
    def test_get_stats(self, manager):
        c = manager.create_customer(name="stats-test", domain="stats.com")
        manager.create_embed(customer_id=c.customer_id, type="dashboard")
        stats = manager.get_stats()
        assert stats.total_customers >= 1
        assert stats.total_embeds >= 1
