"""Tests for PUE/DCIM Integration."""

import pytest
from datetime import datetime
from pue_dcim_integration import (
    PUEDCIMIntegration, Facility, PUEReading, CoolingUnit,
    PowerDistributionUnit, DCIMAlert
)


@pytest.fixture
def pue():
    return PUEDCIMIntegration({})


class TestFacility:
    def test_create(self):
        facility = Facility("fac-001", "DataCenter-1", "San Jose")
        assert facility.facility_id == "fac-001"
        assert facility.name == "DataCenter-1"

    def test_to_dict(self):
        facility = Facility("fac-001", "DC-1", "NYC")
        d = facility.to_dict()
        assert d["facility_id"] == "fac-001"
        assert d["location"] == "NYC"


class TestPUEIntegration:
    def test_initialization(self, pue):
        assert len(pue.facilities) > 0
        assert len(pue.readings) > 0
        assert len(pue.cooling_units) > 0
        assert len(pue.pdus) > 0

    def test_register_facility(self, pue):
        facility = pue.register_facility("fac-new", "New Facility", "Austin")
        assert facility.facility_id == "fac-new"

    def test_get_facility(self, pue):
        fid = list(pue.facilities.keys())[0]
        assert pue.get_facility(fid) is not None

    def test_get_facility_not_found(self, pue):
        assert pue.get_facility("nonexistent") is None

    def test_list_facilities(self, pue):
        facilities = pue.list_facilities()
        assert len(facilities) > 0

    def test_record_pue_reading(self, pue):
        fid = list(pue.facilities.keys())[0]
        reading = pue.record_pue_reading(fid, 1.25, 500.0, 400.0)
        assert reading is not None
        assert 1.15 <= reading.pue <= 1.15

    def test_get_pue_history(self, pue):
        fid = list(pue.facilities.keys())[0]
        history = pue.get_pue_history(fid)
        assert len(history) > 0

    def test_get_facility_metrics(self, pue):
        fid = list(pue.facilities.keys())[0]
        metrics = pue.get_facility_metrics(fid)
        assert "current_pue" in metrics
        assert "avg_pue" in metrics
        assert "it_load_kw" in metrics
        assert "total_power_kw" in metrics

    def test_get_facility_metrics_not_found(self, pue):
        assert pue.get_facility_metrics("nonexistent") is None

    def test_get_all_metrics(self, pue):
        all_metrics = pue.get_all_metrics()
        assert "total_facilities" in all_metrics
        assert "avg_pue" in all_metrics
        assert "best_pue" in all_metrics
        assert "total_it_load_kw" in all_metrics
        assert "total_power_kw" in all_metrics
        assert "efficiency_score" in all_metrics

    def test_register_cooling_unit(self, pue):
        unit = pue.register_cooling_unit(
            "cool-new", "CRAC-5", "fac-001",
            cooling_type="chilled-water", capacity_tons=100
        )
        assert unit.unit_id == "cool-new"
        assert unit.type == "chilled-water"

    def test_list_cooling_units(self, pue):
        units = pue.list_cooling_units()
        assert len(units) > 0

    def test_register_pdu(self, pue):
        pdu = pue.register_pdu(
            "pdu-new", "PDU-5", "fac-001",
            max_power_kw=50, phase="3-phase"
        )
        assert pdu.pdu_id == "pdu-new"
        assert pdu.phase == "3-phase"

    def test_list_pdus(self, pue):
        pdus = pue.list_pdus()
        assert len(pdus) > 0

    def test_get_alerts(self, pue):
        alerts = pue.get_alerts("fac-001")
        assert len(alerts) >= 0

    def test_get_alerts_no_facility(self, pue):
        alerts = pue.get_alerts("nonexistent")
        assert len(alerts) == 0

    def test_get_pue_summary(self, pue):
        summary = pue.get_pue_summary()
        assert "total_facilities" in summary
        assert "overall_avg_pue" in summary
        assert "efficiency_score" in summary
        assert "total_power_consumption_kw" in summary
        assert "cooling_efficiency" in summary

    def test_raise_alert(self, pue):
        alert = pue._raise_alert("fac-001", "PUE spike detected", "warning")
        assert alert is not None
        assert alert.facility_id == "fac-001"

    def test_get_trend(self, pue):
        trend = pue.get_trend("fac-001", hours=24)
        assert len(trend) > 0

    def test_get_optimization_recommendations(self, pue):
        recs = pue.get_optimization_recommendations("fac-001")
        assert len(recs) > 0

    def test_get_optimization_recommendations_no_data(self, pue):
        recs = pue.get_optimization_recommendations("nonexistent")
        assert len(recs) == 0
