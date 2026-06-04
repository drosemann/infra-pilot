"""Tests for Feature 59: AI-Driven Capacity Planning."""

import pytest
from services.integration_service.src.aiops.capacity_planning import CapacityPlanner


@pytest.fixture
def planner():
    return CapacityPlanner({})


class TestCapacityPlanning:
    def test_record_usage(self, planner):
        result = planner.record_usage("web-cluster", "cpu", 100, 45)
        assert result["utilization"] == 0.45

    def test_get_usage_no_data(self, planner):
        usage = planner.get_usage("unknown", "cpu")
        assert usage["data_points"] == 0

    def test_recommendation_insufficient_data(self, planner):
        rec = planner.generate_recommendation("test-svc", "cpu")
        assert "error" in rec

    def test_recommendation_with_data(self, planner):
        for i in range(15):
            planner.record_usage("svc-growth", "cpu", 100, 30 + i * 2)
        rec = planner.generate_recommendation("svc-growth", "cpu")
        assert "priority" in rec
        assert "recommended_capacity" in rec

    def test_what_if_simulation(self, planner):
        for i in range(20):
            planner.record_usage("sim-svc", "cpu", 100, 40 + i)
        result = planner.what_if_simulation("sim-svc", "cpu", "traffic_spike")
        assert result["peak_utilization"] > result["base_utilization"]

    def test_black_friday_simulation(self, planner):
        for i in range(20):
            planner.record_usage("bf-svc", "cpu", 100, 30 + i)
        result = planner.what_if_simulation("bf-svc", "cpu", "black_friday")
        assert "peak_utilization" in result

    def test_dismiss_recommendation(self, planner):
        for i in range(15):
            planner.record_usage("dismiss-svc", "cpu", 100, 40)
        rec = planner.generate_recommendation("dismiss-svc", "cpu")
        assert planner.dismiss_recommendation(rec["id"]) is True

    def test_summary(self, planner):
        summary = planner.get_summary()
        assert "total_recommendations" in summary
