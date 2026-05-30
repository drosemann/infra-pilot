"""Tests for Edge CDN."""

import pytest
from cogs.edge_cdn import EdgeCDN, CacheEntry, CachePolicy, OriginShield


@pytest.fixture
def cdn():
    return EdgeCDN({})


class TestCacheEntry:
    def test_create_entry(self):
        entry = CacheEntry("key1", "s3://bucket", "application/json", 1024)
        assert entry.key == "key1"
        assert entry.content_type == "application/json"
        assert entry.access_count == 0

    def test_is_expired(self):
        from datetime import datetime, timedelta
        entry = CacheEntry("key1", "s3://b", "text/plain", 100)
        entry.created_at = datetime.utcnow() - timedelta(days=2)
        entry.ttl_seconds = 86400
        assert entry.is_expired is True

    def test_to_dict(self):
        entry = CacheEntry("k", "s", "t", 100)
        d = entry.to_dict()
        assert d["key"] == "k"
        assert d["size_bytes"] == 100


class TestCachePolicy:
    def test_create_policy(self):
        p = CachePolicy("images", "*.png", "s3://bucket", ttl_seconds=3600)
        assert p.name == "images"
        assert p.ttl_seconds == 3600

    def test_to_dict(self):
        p = CachePolicy("test", "*", "s3://b")
        d = p.to_dict()
        assert d["name"] == "test"
        assert d["enabled"] is True


class TestEdgeCDN:
    def test_initialization(self, cdn):
        assert len(cdn.cache) > 0
        assert len(cdn.policies) > 0

    def test_get_cached(self, cdn):
        key = list(cdn.cache.keys())[0]
        entry = cdn.get(key)
        assert entry is not None
        assert entry.access_count > 0

    def test_get_not_cached(self, cdn):
        assert cdn.get("nonexistent") is None

    def test_put(self, cdn):
        entry = cdn.put("new-key", "s3://bucket", "text/plain", 2048)
        assert entry.key == "new-key"
        assert cdn.get("new-key") is not None

    def test_invalidate(self, cdn):
        count = cdn.invalidate("obj-001")
        assert count > 0

    def test_warm(self, cdn):
        entries = cdn.warm("s3://bucket", ["preload-1", "preload-2"])
        assert len(entries) == 2

    def test_add_policy(self, cdn):
        policy = cdn.add_policy("custom", "*.wasm", "s3://wasm", ttl_seconds=7200)
        assert policy.name == "custom"
        assert policy.ttl_seconds == 7200
        assert "custom" in cdn.policies

    def test_get_stats(self, cdn):
        stats = cdn.get_stats()
        assert stats["total_objects"] > 0
        assert "total_size_bytes" in stats
        assert "total_hits" in stats
        assert "disk_usage_pct" in stats

    def test_get_content_type_breakdown(self, cdn):
        breakdown = cdn.get_content_type_breakdown()
        assert len(breakdown) > 0

    def test_origin_shield_defaults(self):
        shield = OriginShield()
        assert shield.enabled is True
        assert shield.max_stale_hours == 72

    def test_eviction_policy(self, cdn):
        cdn.eviction_policy = "lru"
        cdn._evict_if_needed()

    def test_put_with_ttl(self, cdn):
        entry = cdn.put("ttl-key", "s3://b", "text/plain", 100, ttl_seconds=60)
        assert entry.ttl_seconds == 60
