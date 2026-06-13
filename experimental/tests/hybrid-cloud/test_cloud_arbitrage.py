import pytest
import sys
sys.path.insert(0, 'services/integration-service/src/hybrid_cloud')
from cloud_arbitrage import CloudArbitrage, ArbitrageOpportunity, MigrationState

@pytest.fixture
def arbitrage():
    a = CloudArbitrage({"min_savings_threshold": 0.10})
    a.initialize()
    yield a
    a.close()

class TestCloudArbitrage:
    def test_compare_pricing(self, arbitrage):
        prices = arbitrage.compare_pricing(vcpu=2, memory=4)
        assert len(prices) > 0
        assert all("provider" in p for p in prices)

    def test_list_opportunities_empty(self, arbitrage):
        assert arbitrage.list_opportunities() == []

    def test_migrate_nonexistent(self, arbitrage):
        result = arbitrage.migrate("nonexistent")
        assert result.get("error") == "Not found"

    def test_list_migrations_empty(self, arbitrage):
        assert arbitrage.list_migrations() == []

    def test_savings_zero(self, arbitrage):
        savings = arbitrage.get_savings()
        assert savings["total_savings_per_hour"] == 0

    def test_migration_flow(self, arbitrage):
        prices = arbitrage.compare_pricing(2, 4)
        assert len(prices) > 0
        assert any(p.get("savings", 0) > 0 for p in prices)
