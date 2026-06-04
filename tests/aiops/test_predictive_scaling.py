"""Tests for Feature 55: Predictive Auto-Scaling."""

import pytest
from services.integration_service.src.aiops.predictive_scaling import PredictiveScalingEngine


@pytest.fixture
def engine():
    return PredictiveScalingEngine({})


class TestPredictiveScaling:
    def test_record_metric(self, engine):
        result = engine.record_metric("web-01", "cpu", 45.2)
        assert result["value"] == 45.2

    def test_predict_insufficient_data(self, engine):
        result = engine.predict("web-01", "cpu")
        assert "error" in result

    def test_predict_with_data(self, engine):
        for i in range(30):
            engine.record_metric("web-02", "cpu", 40 + i * 0.5)
        result = engine.predict("web-02", "cpu")
        assert "forecast" in result
        assert len(result["forecast"]) > 0

    def test_set_policy(self, engine):
        assert engine.set_scaling_policy("web-03", "aggressive") is True
        assert engine.set_scaling_policy("web-03", "invalid") is False

    def test_get_metrics(self, engine):
        for i in range(20):
            engine.record_metric("web-04", "cpu", 50 + i)
        metrics = engine.get_metrics("web-04", "cpu")
        assert metrics["data_points"] >= 1

    def test_scaling_action(self, engine):
        for i in range(25):
            engine.record_metric("web-05", "cpu", 30 + i * 2)
        pred = engine.predict("web-05", "cpu")
        action = engine.execute_scaling_action(pred["id"])
        assert action is not None

    def test_summary(self, engine):
        summary = engine.get_summary()
        assert "total_predictions" in summary
