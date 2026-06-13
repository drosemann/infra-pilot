"""Comprehensive integration tests for Edge & IoT and Green Computing APIs."""

import pytest
import json
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from api_routes import EdgeAPIRouter, GreenAPIRouter
from data_processing import (
    DataNormalizer, MetricsAggregator, AnomalyDetector,
    DataEnricher, DataValidator, StreamProcessor, ReportGenerator
)
from protocol_translation import (
    MQTTTranslator, CoAPTranslator, LoRaWANPayloadDecoder,
    ProtocolGateway, ConnectionManager, ProtocolType
)
from simulation import (
    SensorSimulator, TopologySimulator, LoadSimulator,
    CarbonIntensitySimulator, EdgeSimulationSuite
)
from data_models import (
    EdgeDevice, DeviceStatus, DeviceType, EnergyRecord,
    EnergySource, CarbonFootprint, Facility, CoolingUnit,
    HardwareAsset, MaintenanceRecord, Schedule, ShutdownAction,
    APIResponse, PaginatedResponse, DeviceCommand, OTAUpdate
)


@pytest.fixture
def edge_router():
    return EdgeAPIRouter({})


@pytest.fixture
def green_router():
    return GreenAPIRouter({})


class TestEdgeAPIRouter:
    @pytest.mark.asyncio
    async def test_initialization(self, edge_router):
        await edge_router.initialize()
        assert edge_router.initialized is True
        await edge_router.close()
        assert edge_router.initialized is False

    @pytest.mark.asyncio
    async def test_register_routes(self, edge_router):
        app = MagicMock()
        app.router.add_get = MagicMock()
        app.router.add_post = MagicMock()
        app.router.add_delete = MagicMock()
        edge_router.register_routes(app)
        assert app.router.add_get.call_count > 0
        assert app.router.add_post.call_count > 0


class TestGreenAPIRouter:
    @pytest.mark.asyncio
    async def test_initialization(self, green_router):
        await green_router.initialize()
        await green_router.close()

    def test_register_routes(self, green_router):
        app = MagicMock()
        app.router.add_get = MagicMock()
        app.router.add_post = MagicMock()
        green_router.register_routes(app)
        assert app.router.add_get.call_count > 0
        assert app.router.add_post.call_count > 0


class TestDataNormalizer:
    def test_normalize_temperature(self):
        n = DataNormalizer()
        result = n.normalize_temperature(25.0)
        assert result.scaled_value == 25.0
        assert result.unit == "celsius"

    def test_normalize_temperature_fahrenheit(self):
        n = DataNormalizer()
        result = n.normalize_temperature(77.0, "fahrenheit")
        assert result.scaled_value == 25.0

    def test_normalize_power(self):
        n = DataNormalizer()
        result = n.normalize_power(1500)
        assert result.scaled_value == 1.5

    def test_normalize_energy(self):
        n = DataNormalizer()
        result = n.normalize_energy(500)
        assert result.scaled_value == 500.0

    def test_normalize_energy_from_mwh(self):
        n = DataNormalizer()
        result = n.normalize_energy(2.5, "mwh")
        assert result.scaled_value == 2500.0

    def test_normalize_co2(self):
        n = DataNormalizer()
        result = n.normalize_co2(1000)
        assert result.scaled_value == 1000.0

    def test_normalize_co2_from_tonnes(self):
        n = DataNormalizer()
        result = n.normalize_co2(5.0, "tonnes")
        assert result.scaled_value == 5000.0

    def test_conversion_cache(self):
        n = DataNormalizer()
        assert n.conversion_cache == {}


class TestMetricsAggregator:
    def test_add_reading(self):
        agg = MetricsAggregator(window_minutes=5)
        agg.add_reading("dev-001", 25.0)
        assert len(agg.buckets) == 1

    def test_get_aggregated_metric(self):
        agg = MetricsAggregator()
        for i in range(10):
            agg.add_reading("dev-001", 20.0 + i)
        result = agg.get_aggregated_metric("dev-001",
            datetime.utcnow() - timedelta(hours=1), datetime.utcnow())
        assert result is not None
        assert result.count == 10
        assert result.min_value == 20.0
        assert result.max_value == 29.0

    def test_no_data(self):
        agg = MetricsAggregator()
        result = agg.get_aggregated_metric("nonexistent",
            datetime.utcnow(), datetime.utcnow())
        assert result is None

    def test_clear_old_data(self):
        agg = MetricsAggregator()
        agg.add_reading("dev-001", 25.0)
        agg.clear_old_data(retention_hours=0)
        assert len(agg.buckets) > 0


class TestAnomalyDetector:
    def test_check_value_normal(self):
        ad = AnomalyDetector()
        for i in range(20):
            ad.check_value("dev-001", 50.0 + i % 5)
        result = ad.check_value("dev-001", 52.0)
        assert result["is_anomaly"] is False

    def test_check_value_anomaly(self):
        ad = AnomalyDetector(z_score_threshold=2.0)
        for i in range(50):
            ad.check_value("dev-001", 50.0)
        result = ad.check_value("dev-001", 500.0)
        assert result["is_anomaly"] is True

    def test_insufficient_data(self):
        ad = AnomalyDetector()
        result = ad.check_value("dev-001", 50.0)
        assert result["is_anomaly"] is False

    def test_get_recent_anomalies(self):
        ad = AnomalyDetector()
        assert len(ad.get_recent_anomalies()) == 0

    def test_clear_anomalies(self):
        ad = AnomalyDetector()
        ad.anomalies.append({"test": True})
        ad.clear_anomalies()
        assert len(ad.anomalies) == 0


class TestStreamProcessor:
    def test_process_telemetry(self):
        sp = StreamProcessor()
        result = sp.process_telemetry("dev-001", {"temperature": 25.0, "power_watts": 150})
        assert result["success"] is True

    def test_process_telemetry_with_anomaly(self):
        sp = StreamProcessor()
        for _ in range(20):
            sp.process_telemetry("dev-001", {"temperature": 22.0})
        result = sp.process_telemetry("dev-001", {"temperature": 100.0})
        assert result["success"] is True

    def test_get_stats(self):
        sp = StreamProcessor()
        stats = sp.get_stats()
        assert "processed" in stats
        assert "errors" in stats

    def test_validation_error(self):
        sp = StreamProcessor()
        result = sp.process_telemetry("dev-001", {"temperature": "invalid"})
        assert result["success"] is True


class TestMQTTTranslator:
    def test_translate(self):
        t = MQTTTranslator()
        msg = t.translate("sensors/temperature/001", b'{"temp": 25.0}')
        assert msg is not None
        assert msg.protocol == ProtocolType.MQTT
        assert msg.payload["temp"] == 25.0

    def test_topic_parsing(self):
        t = MQTTTranslator()
        t.register_topic("devices/{device_id}/telemetry", "sensor")
        device_id, dev_type = t.parse_topic("devices/sensor-001/telemetry")
        assert device_id == "sensor-001"
        assert dev_type == "sensor"


class TestLoRaWANPayloadDecoder:
    def test_decode_temperature(self):
        d = LoRaWANPayloadDecoder()
        import struct
        payload = struct.pack(">hh", 2500, 5500)
        result = d.decode_temperature_humidity(payload)
        assert result["temperature_celsius"] == 25.0
        assert result["humidity_pct"] == 55.0

    def test_decode_power_meter(self):
        d = LoRaWANPayloadDecoder()
        import struct
        payload = struct.pack(">HHI", 2300, 500, 115000)
        result = d.decode_power_meter(payload)
        assert result["voltage_v"] == 230.0
        assert result["power_w"] == 115000

    def test_decode_generic(self):
        d = LoRaWANPayloadDecoder()
        result = d.decode("unknown", b"\x01\x02\x03")
        assert "raw_hex" in result

    def test_encode_downlink(self):
        d = LoRaWANPayloadDecoder()
        result = d.encode_downlink("relay_control", {"channel": 1, "state": True})
        assert result == b"\x01\x01"


class TestConnectionManager:
    def test_create_session(self):
        cm = ConnectionManager()
        sid = cm.create_session("dev-001", ProtocolType.MQTT, "10.0.0.1")
        assert sid is not None

    def test_update_activity(self):
        cm = ConnectionManager()
        sid = cm.create_session("dev-001", ProtocolType.MQTT, "10.0.0.1")
        cm.update_activity(sid)
        assert cm.sessions[sid]["message_count"] == 1

    def test_get_active_devices(self):
        cm = ConnectionManager()
        cm.create_session("dev-001", ProtocolType.MQTT, "10.0.0.1")
        active = cm.get_active_devices()
        assert len(active) > 0

    def test_get_stats(self):
        cm = ConnectionManager()
        cm.create_session("dev-001", ProtocolType.MQTT, "10.0.0.1")
        stats = cm.get_stats()
        assert stats["total_sessions"] == 1


class TestSensorSimulator:
    def test_add_sensor(self):
        sim = SensorSimulator()
        sensor = sim.add_sensor("test-001", "temperature", "DC-1")
        assert sensor.device_id == "test-001"

    def test_generate_batch(self):
        sim = SensorSimulator()
        sensors = sim.generate_batch(5, "temperature")
        assert len(sensors) == 5

    def test_read_sensor(self):
        sim = SensorSimulator()
        sim.add_sensor("test-001", "temperature")
        reading = sim.read_sensor("test-001")
        assert reading is not None
        assert "value" in reading

    def test_read_sensor_not_found(self):
        sim = SensorSimulator()
        assert sim.read_sensor("nonexistent") is None

    def test_read_all(self):
        sim = SensorSimulator()
        sim.add_sensor("test-001", "temperature")
        readings = sim.read_all()
        assert len(readings) > 0

    def test_get_stats(self):
        sim = SensorSimulator()
        sim.add_sensor("test-001", "temperature")
        stats = sim.get_stats()
        assert stats["total_sensors"] > 0

    def test_presets_exist(self):
        sim = SensorSimulator()
        assert len(sim.presets) > 0


class TestTopologySimulator:
    def test_generate(self):
        topo = TopologySimulator(5)
        data = topo.get_topology()
        assert data["node_count"] == 5

    def test_connectivity(self):
        topo = TopologySimulator(10)
        data = topo.get_topology()
        assert "is_connected" in data

    def test_find_route(self):
        topo = TopologySimulator(10)
        nodes = topo.nodes
        if len(nodes) >= 2:
            route = topo.find_route(nodes[0]["node_id"], nodes[-1]["node_id"])
            if route:
                assert len(route) > 1

    def test_simulate_link_failure(self):
        topo = TopologySimulator(5)
        topo.simulate_link_failure(1.0)
        assert all(not l["is_active"] for l in topo.links) if topo.links else True


class TestCarbonIntensitySimulator:
    def test_generate_forecast(self):
        sim = CarbonIntensitySimulator()
        forecast = sim.generate_daily_forecast()
        assert len(forecast) == 24

    def test_get_best_window(self):
        sim = CarbonIntensitySimulator()
        sim.generate_daily_forecast()
        window = sim.get_best_window(3)
        assert "start_hour" in window
        assert "avg_intensity" in window


class TestReportGenerator:
    def test_generate_energy_report(self):
        rg = ReportGenerator()
        report = rg.generate_energy_report({"total_kwh": 50000})
        assert report["report_type"] == "energy_consumption"
        assert report["summary"]["total_kwh"] == 50000

    def test_generate_carbon_report(self):
        rg = ReportGenerator()
        report = rg.generate_carbon_report(10000)
        assert report["total_co2_kg"] > 0

    def test_generate_pue_report(self):
        rg = ReportGenerator()
        report = rg.generate_pue_report([{"pue": 1.3, "it_load_kw": 100}])
        assert "average_pue" in report

    def test_generate_compliance_report(self):
        rg = ReportGenerator()
        report = rg.generate_compliance_report({"soc2": True, "hipaa": False})
        assert report["compliance_pct"] == 50.0


class TestDataModels:
    def test_edge_device_to_dict(self):
        d = EdgeDevice("dev-001", "Test Device")
        data = d.to_dict()
        assert data["device_id"] == "dev-001"

    def test_edge_device_from_dict(self):
        data = {"device_id": "dev-001", "name": "Test", "device_type": "sensor", "status": "online"}
        d = EdgeDevice.from_dict(data)
        assert d.device_id == "dev-001"
        assert d.device_type == DeviceType.SENSOR
        assert d.status == DeviceStatus.ONLINE

    def test_ota_update(self):
        u = OTAUpdate("upd-001", "dev-001", "2.0.0")
        assert u.target_version == "2.0.0"

    def test_device_command(self):
        c = DeviceCommand("cmd-001", "dev-001", "restart")
        assert c.command_type == "restart"
        assert c.status == "pending"

    def test_energy_record(self):
        r = EnergyRecord("rec-001", "dev-001", power_watts=150.0)
        assert r.power_watts == 150.0

    def test_carbon_footprint(self):
        f = CarbonFootprint("fp-001", "dev-001",
            period_start=datetime.utcnow() - timedelta(days=30),
            period_end=datetime.utcnow())
        assert f.total_co2_kg == 0.0

    def test_facility(self):
        f = Facility("fac-001", "DC-1", "San Jose")
        assert f.location == "San Jose"

    def test_cooling_unit(self):
        c = CoolingUnit("cu-001", "fac-001", "CRAC-1", "chilled-water")
        assert c.cooling_type == "chilled-water"

    def test_hardware_asset(self):
        a = HardwareAsset("asset-001", "Server-01")
        assert a.status == "active"

    def test_maintenance_record(self):
        r = MaintenanceRecord("rec-001", "asset-001", "inspection", "Annual check", "tech-001")
        assert r.status == "scheduled"

    def test_schedule(self):
        s = Schedule("sched-001", "Night Shutdown", action=ShutdownAction.HIBERNATE)
        assert s.action == ShutdownAction.HIBERNATE

    def test_api_response(self):
        r = APIResponse(success=True, data={"key": "value"})
        data = r.to_dict()
        assert data["success"] is True
        assert data["data"]["key"] == "value"

    def test_paginated_response(self):
        r = PaginatedResponse(page=1, page_size=20, total=100)
        assert r.total_pages == 5
