"""Tests for Feature 56: Service Health Forecasting."""

import pytest
from services.integration_service.src.aiops.health_forecasting import ServiceHealthForecaster


@pytest.fixture
def forecaster():
    return ServiceHealthForecaster({})


class TestHealthForecasting:
    def test_register_service(self, forecaster):
        svc = forecaster.register_service("svc-01", "Web Server")
        assert svc["name"] == "Web Server"
        assert svc["current_health"] == "unknown"

    def test_record_snapshot(self, forecaster):
        forecaster.register_service("svc-02", "API Gateway")
        result = forecaster.record_snapshot("svc-02", {"availability": 0.99, "performance": 0.95, "capacity": 0.85})
        assert result["overall_score"] > 0

    def test_forecast_insufficient_data(self, forecaster):
        forecaster.register_service("svc-03", "Test")
        result = forecaster.forecast("svc-03")
        assert "error" in result

    def test_forecast_with_data(self, forecaster):
        forecaster.register_service("svc-04", "Test 2")
        for i in range(15):
            score = 0.95 - i * 0.02
            forecaster.record_snapshot("svc-04", {"availability": score, "performance": score, "capacity": score})
        result = forecaster.forecast("svc-04")
        assert "forecast_scores" in result

    def test_dashboard(self, forecaster):
        forecaster.register_service("svc-da", "Dash A")
        forecaster.register_service("svc-db", "Dash B")
        dash = forecaster.get_dashboard()
        assert dash["total_services"] >= 2

    def test_trend_detection(self, forecaster):
        forecaster.register_service("svc-trend", "Trend Test")
        for i in range(15):
            forecaster.record_snapshot("svc-trend", {"performance": 0.9 - i * 0.03})
        service = forecaster.get_service("svc-trend")
        assert service["trend"] in ("improving", "stable", "degrading")

    def test_service_list(self, forecaster):
        forecaster.register_service("svc-list", "List Test")
        services = forecaster.list_services()
        assert len(services) >= 1

    def test_delete_service(self, forecaster):
        forecaster.register_service("svc-del", "Delete Me")
        assert forecaster.delete_service("svc-del") is True
        assert forecaster.get_service("svc-del") is None
