"""Tests for Energy Consumption Tracker."""

import pytest
from energy_consumption_tracker import (
    EnergyConsumptionTracker, EnergyReading, EnergyMetrics,
    PowerSource, EnergyUnit
)


@pytest.fixture
def tracker():
    return EnergyConsumptionTracker({})


class TestEnergyReading:
    def test_create(self):
        reading = EnergyReading("dev-001", 150.0, PowerSource.GRID)
        assert reading.device_id == "dev-001"
        assert reading.power_watts == 150.0
        assert reading.source == PowerSource.GRID

    def test_to_dict(self):
        reading = EnergyReading("dev-001", 200.0, PowerSource.SOLAR)
        d = reading.to_dict()
        assert d["device_id"] == "dev-001"
        assert d["power_watts"] == 200.0


class TestEnergyConsumptionTracker:
    def test_initialization(self, tracker):
        assert len(tracker.readings) > 0
        assert len(tracker.energy_configs) > 0

    def test_record_reading(self, tracker):
        reading = tracker.record_reading("dev-001", 250.0, PowerSource.GRID)
        assert reading is not None
        assert reading.reading_id is not None

    def test_get_reading(self, tracker):
        reading = tracker.record_reading("dev-001", 300.0, PowerSource.GRID)
        found = tracker.get_reading(reading.reading_id)
        assert found is not None
        assert found.power_watts == 300.0

    def test_get_reading_not_found(self, tracker):
        assert tracker.get_reading("nonexistent") is None

    def test_get_readings(self, tracker):
        readings = tracker.get_readings("dev-001", limit=10)
        assert len(readings) > 0

    def test_get_readings_no_data(self, tracker):
        assert len(tracker.get_readings("nonexistent")) == 0

    def test_get_metrics(self, tracker):
        tracker.record_reading("dev-001", 100.0, PowerSource.GRID)
        metrics = tracker.get_metrics("dev-001")
        assert metrics["device_id"] == "dev-001"
        assert "avg_power_watts" in metrics
        assert "total_energy_kwh" in metrics
        assert "peak_power_watts" in metrics

    def test_get_metrics_no_data(self, tracker):
        metrics = tracker.get_metrics("nonexistent")
        assert metrics["avg_power_watts"] == 0

    def test_get_all_metrics(self, tracker):
        all_metrics = tracker.get_all_metrics()
        assert "total_devices" in all_metrics
        assert "total_energy_kwh" in all_metrics
        assert "avg_power_watts" in all_metrics
        assert "renewable_pct" in all_metrics
        assert "carbon_intensity" in all_metrics

    def test_get_energy_by_source(self, tracker):
        tracker.record_reading("dev-001", 100.0, PowerSource.SOLAR)
        source_breakdown = tracker.get_energy_by_source()
        assert len(source_breakdown) > 0
        assert "total_kwh" in source_breakdown[0]
        assert "source" in source_breakdown[0]

    def test_get_daily_profile(self, tracker):
        profile = tracker.get_daily_profile("dev-001")
        assert "device_id" in profile
        assert "hourly_averages" in profile

    def test_get_daily_profile_no_data(self, tracker):
        profile = tracker.get_daily_profile("nonexistent")
        assert profile is None

    def test_get_carbon_footprint(self, tracker):
        tracker.record_reading("dev-001", 500.0, PowerSource.GRID)
        footprint = tracker.get_carbon_footprint("dev-001")
        assert "device_id" in freq
        assert "co2_kg" in footprint
        assert "period_hours" in footprint

    def test_get_carbon_footprint_no_data(self, tracker):
        footprint = tracker.get_carbon_footprint("nonexistent")
        assert footprint is None

    def test_get_efficiency_rating(self, tracker):
        rating = tracker.get_efficiency_rating("dev-001")
        assert rating is not None
        assert 0 <= rating <= 100

    def test_get_efficiency_rating_no_data(self, tracker):
        assert tracker.get_efficiency_rating("nonexistent") is None

    def test_configure_device(self, tracker):
        config = tracker.configure_device("dev-001", {"wattage_limit": 500})
        assert config is not None
        assert config["device_id"] == "dev-001"

    def test_get_device_config(self, tracker):
        config = tracker.get_device_config("dev-001")
        assert config is not None

    def test_get_device_config_not_found(self, tracker):
        assert tracker.get_device_config("nonexistent") is None

    def test_threshold_alert(self, tracker):
        tracker.configure_device("dev-001", {"wattage_limit": 100})
        reading = tracker.record_reading("dev-001", 500.0, PowerSource.GRID)
        assert reading.wattage_exceeded is True

    def test_power_source_enum(self):
        assert PowerSource.GRID.value == "grid"
        assert PowerSource.SOLAR.value == "solar"
        assert PowerSource.WIND.value == "wind"
        assert PowerSource.BATTERY.value == "battery"

    def test_energy_unit_enum(self):
        assert EnergyUnit.KWH.value == "kwh"
        assert EnergyUnit.MWH.value == "mwh"
        assert EnergyUnit.WATTHOURS.value == "wh"
