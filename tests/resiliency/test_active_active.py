"""Tests for Multi-Region Active-Active (feature 32)."""

import pytest
import json
import tempfile
import os
from services.integration_service.src.resiliency.active_active import ActiveActiveManager


@pytest.fixture
def manager():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    config = {"active_active_file": path, "active_active_metrics_file": path.replace(".json", "_metrics.json")}
    yield ActiveActiveManager(config)
    if os.path.exists(path):
        os.remove(path)
    if os.path.exists(config["active_active_metrics_file"]):
        os.remove(config["active_active_metrics_file"])


@pytest.mark.asyncio
async def test_register_region(manager):
    region = await manager.register_region({"name": "us-east-1", "endpoint": "https://east.example.com", "weight": 100})
    assert region["name"] == "us-east-1"
    assert region["weight"] == 100
    assert region["status"] == "healthy"


@pytest.mark.asyncio
async def test_list_regions(manager):
    await manager.register_region({"name": "us-east-1", "endpoint": "https://east.example.com"})
    await manager.register_region({"name": "eu-west-1", "endpoint": "https://eu.example.com"})
    regions = await manager.list_regions()
    assert len(regions) == 2


@pytest.mark.asyncio
async def test_update_region(manager):
    created = await manager.register_region({"name": "Update Region", "endpoint": "https://old.example.com"})
    updated = await manager.update_region(created["id"], {"weight": 75, "status": "degraded"})
    assert updated["weight"] == 75
    assert updated["status"] == "degraded"


@pytest.mark.asyncio
async def test_delete_region(manager):
    created = await manager.register_region({"name": "Delete Me", "endpoint": "https://del.example.com"})
    assert await manager.delete_region(created["id"]) == True


@pytest.mark.asyncio
async def test_health_check(manager):
    created = await manager.register_region({"name": "Health Check", "endpoint": "https://health.example.com"})
    result = await manager.health_check(created["id"])
    assert "healthy" in result


@pytest.mark.asyncio
async def test_update_traffic_weight(manager):
    created = await manager.register_region({"name": "Weight Test", "endpoint": "https://weight.example.com", "weight": 50})
    result = await manager.update_traffic_weight(created["id"], 80)
    assert result["new_weight"] == 80


@pytest.mark.asyncio
async def test_create_traffic_rule(manager):
    rule = await manager.create_traffic_rule({"name": "Geo Rule", "type": "geo", "target_region": "us-east-1"})
    assert rule["name"] == "Geo Rule"
    assert rule["active"] == True


@pytest.mark.asyncio
async def test_record_metrics(manager):
    region = await manager.register_region({"name": "Metrics Test", "endpoint": "https://metrics.example.com"})
    metrics = await manager.record_metrics({"region_id": region["id"], "requests_per_second": 1000, "replication_lag_ms": 50})
    assert metrics["requests_per_second"] == 1000


@pytest.mark.asyncio
async def test_global_status(manager):
    await manager.register_region({"name": "Region A", "endpoint": "https://a.example.com"})
    await manager.register_region({"name": "Region B", "endpoint": "https://b.example.com"})
    status = await manager.get_global_status()
    assert status["total_regions"] == 2
