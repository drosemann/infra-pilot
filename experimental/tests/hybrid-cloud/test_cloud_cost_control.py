import pytest
import sys
sys.path.insert(0, 'services/integration-service/src/hybrid_cloud')
from cloud_cost_control import CloudCostControl, Budget

@pytest.fixture
def cost():
    c = CloudCostControl({})
    c.initialize()
    yield c
    c.close()

class TestCloudCostControl:
    def test_summary_empty(self, cost):
        s = cost.get_summary()
        assert s["total"] == 0
        assert s["record_count"] == 0

    def test_record_cost(self, cost):
        r = cost.record_cost(provider="aws", amount=50.0, service="compute")
        assert r.id is not None

    def test_summary_with_records(self, cost):
        cost.record_cost("aws", 100)
        cost.record_cost("azure", 50)
        s = cost.get_summary()
        assert s["total"] == 150
        assert s["record_count"] == 2

    def test_create_budget(self, cost):
        b = cost.create_budget(name="Monthly", amount=1000)
        assert b.id is not None
        assert b.amount == 1000

    def test_list_budgets(self, cost):
        cost.create_budget("Test", 500)
        budgets = cost.list_budgets()
        assert len(budgets) == 1

    def test_anomalies_empty(self, cost):
        assert cost.list_anomalies() == []

    def test_forecast_empty(self, cost):
        f = cost.get_forecast(days=30)
        assert f["daily_average"] == 0

    def test_forecast_with_data(self, cost):
        cost.record_cost("aws", 100)
        f = cost.get_forecast(days=30)
        assert f["daily_average"] > 0
        assert f["forecast"] > 0
