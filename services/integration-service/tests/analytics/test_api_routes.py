import pytest
import json
from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop

from services.integration_service.src.analytics.api_routes import setup_analytics_routes
from services.integration_service.src.fleet.api_routes import setup_fleet_routes


class TestAnalyticsAPI:
    @pytest.fixture
    async def app(self):
        application = web.Application()
        engine, pipeline = setup_analytics_routes(application)
        yield application

    @pytest.fixture
    async def client(self, app, aiohttp_client):
        return await aiohttp_client(app)

    @pytest.mark.asyncio
    async def test_health(self, client):
        resp = await client.get("/api/v1/analytics/health")
        assert resp.status == 200
        data = await resp.json()
        assert "status" in data

    @pytest.mark.asyncio
    async def test_collect_metric(self, client):
        resp = await client.post("/api/v1/analytics/metrics", json={
            "metric": "test.api.metric",
            "value": 42.5,
            "tags": {"source": "test"},
        })
        assert resp.status == 200
        data = await resp.json()
        assert data["status"] == "collected"
        assert data["metric"] == "test.api.metric"

    @pytest.mark.asyncio
    async def test_collect_metric_invalid(self, client):
        resp = await client.post("/api/v1/analytics/metrics", json={"metric": "m"})
        assert resp.status == 400

    @pytest.mark.asyncio
    async def test_collect_batch(self, client):
        items = [{"metric": f"batch.{i}", "value": float(i * 10)} for i in range(5)]
        resp = await client.post("/api/v1/analytics/metrics/batch", json={"items": items})
        assert resp.status == 200
        data = await resp.json()
        assert data["count"] == 5

    @pytest.mark.asyncio
    async def test_get_metric(self, client):
        await client.post("/api/v1/analytics/metrics", json={"metric": "get.test", "value": 55.0})
        resp = await client.get("/api/v1/analytics/metrics/get.test")
        assert resp.status == 200
        data = await resp.json()
        assert data["metric"] == "get.test"

    @pytest.mark.asyncio
    async def test_get_metric_not_found(self, client):
        resp = await client.get("/api/v1/analytics/metrics/nonexistent")
        assert resp.status == 404

    @pytest.mark.asyncio
    async def test_get_trend(self, client):
        for i in range(5):
            await client.post("/api/v1/analytics/metrics", json={"metric": "trend.test", "value": float(i * 10)})
        resp = await client.get("/api/v1/analytics/metrics/trend.test/trend?window=3600")
        assert resp.status == 200

    @pytest.mark.asyncio
    async def test_get_forecast(self, client):
        for i in range(10):
            await client.post("/api/v1/analytics/metrics", json={"metric": "forecast.test", "value": float(i * 5)})
        resp = await client.get("/api/v1/analytics/metrics/forecast.test/forecast?horizon=5")
        assert resp.status == 200
        data = await resp.json()
        assert len(data["forecasts"]) == 5

    @pytest.mark.asyncio
    async def test_top_metrics(self, client):
        for i in range(10):
            await client.post("/api/v1/analytics/metrics", json={"metric": f"top.test.{i}", "value": float(i * 10)})
        resp = await client.get("/api/v1/analytics/top?prefix=top.test.&n=3")
        assert resp.status == 200
        data = await resp.json()
        assert len(data["items"]) == 3

    @pytest.mark.asyncio
    async def test_generate_report(self, client):
        for i in range(10):
            await client.post("/api/v1/analytics/metrics", json={"metric": f"report.test.{i}", "value": float(i)})
        resp = await client.get("/api/v1/analytics/report")
        assert resp.status == 200
        data = await resp.json()
        assert "metrics_summary" in data

    @pytest.mark.asyncio
    async def test_export_json(self, client):
        await client.post("/api/v1/analytics/metrics", json={"metric": "export.json.test", "value": 77.0})
        resp = await client.get("/api/v1/analytics/export?format=json&metrics=export.json.test")
        assert resp.status == 200

    @pytest.mark.asyncio
    async def test_export_csv(self, client):
        await client.post("/api/v1/analytics/metrics", json={"metric": "export.csv.test", "value": 88.0})
        resp = await client.get("/api/v1/analytics/export?format=csv&metrics=export.csv.test")
        assert resp.status == 200

    @pytest.mark.asyncio
    async def test_set_baseline(self, client):
        resp = await client.post("/api/v1/analytics/anomalies/baseline", json={
            "metric": "anomaly.test", "mean": 100, "std": 10,
        })
        assert resp.status == 200

    @pytest.mark.asyncio
    async def test_set_threshold(self, client):
        resp = await client.post("/api/v1/analytics/anomalies/threshold", json={"threshold": 2.5})
        assert resp.status == 200

    @pytest.mark.asyncio
    async def test_compute_sla(self, client):
        for v in [10, 20, 30, 40, 50]:
            await client.post("/api/v1/analytics/metrics", json={"metric": "sla.test", "value": float(v)})
        resp = await client.get("/api/v1/analytics/sla?metric=sla.test&threshold=35")
        assert resp.status == 200
        data = await resp.json()
        assert "sla_compliance" in data

    @pytest.mark.asyncio
    async def test_correlation(self, client):
        for i in range(10):
            await client.post("/api/v1/analytics/metrics", json={"metric": "corr.a", "value": float(i)})
            await client.post("/api/v1/analytics/metrics", json={"metric": "corr.b", "value": float(i * 2)})
        resp = await client.get("/api/v1/analytics/correlate?metric_a=corr.a&metric_b=corr.b")
        assert resp.status == 200

    @pytest.mark.asyncio
    async def test_process_metric(self, client):
        resp = await client.post("/api/v1/analytics/process", json={
            "metric": "process.test", "value": 99.9,
        })
        assert resp.status == 200
        data = await resp.json()
        assert data["status"] == "processed"

    @pytest.mark.asyncio
    async def test_dashboard_config(self, client):
        resp = await client.get("/api/v1/analytics/dashboard/config")
        assert resp.status == 200
        data = await resp.json()
        assert "dashboard" in data

    @pytest.mark.asyncio
    async def test_dashboard_summary(self, client):
        resp = await client.get("/api/v1/analytics/dashboard/summary")
        assert resp.status == 200
        data = await resp.json()
        assert "widgets" in data

    @pytest.mark.asyncio
    async def test_register_collector(self, client):
        resp = await client.post("/api/v1/analytics/collectors/register", json={"pattern": "dynamic.*"})
        assert resp.status == 200

    @pytest.mark.asyncio
    async def test_start_stop(self, client):
        resp = await client.get("/api/v1/analytics/start?interval=10")
        assert resp.status == 200
        resp = await client.get("/api/v1/analytics/stop")
        assert resp.status == 200

    @pytest.mark.asyncio
    async def test_alert_callback(self, client):
        resp = await client.post("/api/v1/analytics/alerts/callback")
        assert resp.status == 200


class TestFleetAPI:
    @pytest.fixture
    async def app(self):
        application = web.Application()
        manager = setup_fleet_routes(application)
        yield application

    @pytest.fixture
    async def client(self, app, aiohttp_client):
        return await aiohttp_client(app)

    @pytest.mark.asyncio
    async def test_fleet_health(self, client):
        resp = await client.get("/api/v1/fleet/health")
        assert resp.status == 200
        data = await resp.json()
        assert "status" in data

    @pytest.mark.asyncio
    async def test_register_device(self, client):
        resp = await client.post("/api/v1/fleet/devices", json={
            "name": "API Test Device",
            "device_type": "sensor",
            "location": "Rack-1",
        })
        assert resp.status == 201
        data = await resp.json()
        assert data["status"] == "registered"

    @pytest.mark.asyncio
    async def test_register_duplicate_device(self, client):
        await client.post("/api/v1/fleet/devices", json={
            "device_id": "dup-dev", "name": "Original",
        })
        resp = await client.post("/api/v1/fleet/devices", json={
            "device_id": "dup-dev", "name": "Duplicate",
        })
        assert resp.status == 409

    @pytest.mark.asyncio
    async def test_batch_register(self, client):
        devices = [{"device_id": f"batch-api-{i}", "name": f"Batch-{i}"} for i in range(5)]
        resp = await client.post("/api/v1/fleet/devices/batch", json={"devices": devices})
        assert resp.status == 201
        data = await resp.json()
        assert data["count"] == 5

    @pytest.mark.asyncio
    async def test_list_devices(self, client):
        await client.post("/api/v1/fleet/devices", json={"name": "List Test"})
        resp = await client.get("/api/v1/fleet/devices")
        assert resp.status == 200
        data = await resp.json()
        assert "devices" in data

    @pytest.mark.asyncio
    async def test_get_device(self, client):
        await client.post("/api/v1/fleet/devices", json={"device_id": "get-dev", "name": "Get Test"})
        resp = await client.get("/api/v1/fleet/devices/get-dev")
        assert resp.status == 200
        data = await resp.json()
        assert data["device_id"] == "get-dev"

    @pytest.mark.asyncio
    async def test_get_device_not_found(self, client):
        resp = await client.get("/api/v1/fleet/devices/nonexistent")
        assert resp.status == 404

    @pytest.mark.asyncio
    async def test_update_device(self, client):
        await client.post("/api/v1/fleet/devices", json={"device_id": "update-dev", "name": "Original"})
        resp = await client.put("/api/v1/fleet/devices/update-dev", json={"name": "Updated", "cpu_usage": 75})
        assert resp.status == 200

    @pytest.mark.asyncio
    async def test_delete_device(self, client):
        await client.post("/api/v1/fleet/devices", json={"device_id": "delete-dev", "name": "Delete Test"})
        resp = await client.delete("/api/v1/fleet/devices/delete-dev")
        assert resp.status == 200

    @pytest.mark.asyncio
    async def test_heartbeat(self, client):
        await client.post("/api/v1/fleet/devices", json={"device_id": "hb-dev", "name": "Heartbeat Test"})
        resp = await client.post("/api/v1/fleet/devices/hb-dev/heartbeat", json={"metrics": {"cpu": 50, "memory": 60}})
        assert resp.status == 200

    @pytest.mark.asyncio
    async def test_send_command(self, client):
        await client.post("/api/v1/fleet/devices", json={"device_id": "cmd-dev", "name": "Command Test"})
        resp = await client.post("/api/v1/fleet/devices/cmd-dev/command", json={"command_type": "reboot"})
        assert resp.status == 200
        data = await resp.json()
        assert "command_id" in data

    @pytest.mark.asyncio
    async def test_batch_command(self, client):
        for i in range(3):
            await client.post("/api/v1/fleet/devices", json={"device_id": f"bc-dev-{i}", "name": f"BC-{i}"})
        resp = await client.post("/api/v1/fleet/devices/batch-command", json={
            "device_ids": ["bc-dev-0", "bc-dev-1", "bc-dev-2"],
            "command_type": "ping",
        })
        assert resp.status == 200
        data = await resp.json()
        assert data["count"] == 3

    @pytest.mark.asyncio
    async def test_device_analytics(self, client):
        await client.post("/api/v1/fleet/devices", json={"device_id": "analytics-api", "name": "Analytics"})
        resp = await client.get("/api/v1/fleet/devices/analytics-api/analytics")
        assert resp.status == 200

    @pytest.mark.asyncio
    async def test_fleet_groups(self, client):
        resp = await client.post("/api/v1/fleet/groups", json={"name": "API Group", "description": "Test group"})
        assert resp.status == 201
        resp = await client.get("/api/v1/fleet/groups")
        assert resp.status == 200

    @pytest.mark.asyncio
    async def test_fleet_group_detail(self, client):
        await client.post("/api/v1/fleet/groups", json={"group_id": "g-api-1", "name": "Detail Group"})
        resp = await client.get("/api/v1/fleet/groups/g-api-1")
        assert resp.status == 200

    @pytest.mark.asyncio
    async def test_update_group(self, client):
        await client.post("/api/v1/fleet/groups", json={"group_id": "g-upd", "name": "Original"})
        resp = await client.put("/api/v1/fleet/groups/g-upd", json={"name": "Updated"})
        assert resp.status == 200

    @pytest.mark.asyncio
    async def test_delete_group(self, client):
        await client.post("/api/v1/fleet/groups", json={"group_id": "g-del", "name": "Delete"})
        resp = await client.delete("/api/v1/fleet/groups/g-del")
        assert resp.status == 200

    @pytest.mark.asyncio
    async def test_add_remove_device_from_group(self, client):
        await client.post("/api/v1/fleet/devices", json={"device_id": "grp-dev", "name": "Group Device"})
        await client.post("/api/v1/fleet/groups", json={"group_id": "grp-1", "name": "Test Group"})
        resp = await client.post("/api/v1/fleet/groups/grp-1/devices/grp-dev")
        assert resp.status == 200
        resp = await client.delete("/api/v1/fleet/groups/grp-1/devices/grp-dev")
        assert resp.status == 200

    @pytest.mark.asyncio
    async def test_deployments(self, client):
        await client.post("/api/v1/fleet/devices", json={"device_id": "dep-dev", "name": "Deploy Device"})
        await client.post("/api/v1/fleet/groups", json={"group_id": "dep-grp", "name": "Deploy Group"})
        await client.post("/api/v1/fleet/groups/dep-grp/devices/dep-dev")
        resp = await client.post("/api/v1/fleet/deployments", json={
            "name": "API Deploy",
            "target_groups": ["dep-grp"],
            "actions": [{"type": "reboot", "payload": {}}],
        })
        assert resp.status == 201
        data = await resp.json()
        plan_id = data["plan_id"]
        resp = await client.post(f"/api/v1/fleet/deployments/{plan_id}/execute")
        assert resp.status == 200

    @pytest.mark.asyncio
    async def test_fleet_stats(self, client):
        resp = await client.get("/api/v1/fleet/stats")
        assert resp.status == 200

    @pytest.mark.asyncio
    async def test_firmware(self, client):
        resp = await client.post("/api/v1/fleet/firmware", json={
            "version": "2.0.0",
            "build": "B001",
            "checksum": "abc123",
            "download_url": "https://fw.example.com/v2.bin",
            "changelog": ["Bug fixes", "Performance improvements"],
        })
        assert resp.status == 201
        resp = await client.get("/api/v1/fleet/firmware")
        assert resp.status == 200
        data = await resp.json()
        assert data["count"] >= 1

    @pytest.mark.asyncio
    async def test_ota_update(self, client):
        await client.post("/api/v1/fleet/firmware", json={
            "version": "3.0.0", "build": "B003", "checksum": "def456", "download_url": "https://fw.example.com/v3.bin",
        })
        await client.post("/api/v1/fleet/devices", json={"device_id": "ota-dev", "name": "OTA Device"})
        resp = await client.post("/api/v1/fleet/ota-update", json={
            "device_ids": ["ota-dev"],
            "firmware_version": "3.0.0",
        })
        assert resp.status == 200

    @pytest.mark.asyncio
    async def test_reboot_shutdown(self, client):
        await client.post("/api/v1/fleet/devices", json={"device_id": "rs-dev", "name": "RS Device"})
        resp = await client.post("/api/v1/fleet/reboot", json={"device_ids": ["rs-dev"]})
        assert resp.status == 200
        resp = await client.post("/api/v1/fleet/shutdown", json={"device_ids": ["rs-dev"]})
        assert resp.status == 200

    @pytest.mark.asyncio
    async def test_search_devices(self, client):
        await client.post("/api/v1/fleet/devices", json={"device_id": "search-me", "name": "Searchable Device"})
        resp = await client.get("/api/v1/fleet/devices/search?q=searchable")
        assert resp.status == 200
        data = await resp.json()
        assert data["count"] >= 1
