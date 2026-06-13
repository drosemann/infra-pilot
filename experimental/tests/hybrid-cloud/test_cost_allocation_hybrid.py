import pytest
import sys
sys.path.insert(0, 'services/integration-service/src/hybrid_cloud')
from cost_allocation_hybrid import CostAllocationHybrid

@pytest.fixture
def alloc():
    a = CostAllocationHybrid({})
    a.initialize()
    yield a
    a.close()

class TestCostAllocationHybrid:
    def test_list_allocations_empty(self, alloc):
        assert alloc.list_allocations() == []

    def test_create_allocation(self, alloc):
        a = alloc.create_allocation(name="Q1 infra", amount=5000, team="platform", project="infra", source="cloud")
        assert a.id is not None
        assert a.allocated is True

    def test_summary(self, alloc):
        alloc.create_allocation("proj-a", 1000, "team-a", "proj-a", "cloud")
        alloc.create_allocation("proj-b", 2000, "team-b", "proj-b", "cloud")
        s = alloc.get_summary()
        assert s["total_allocated"] == 3000

    def test_team_spend(self, alloc):
        alloc.create_allocation("proj-a", 1000, "team-x", "proj-a", "cloud")
        alloc.create_allocation("proj-b", 500, "team-x", "proj-b", "cloud")
        t = alloc.get_team_spend("team-x")
        assert t["total_spend"] == 1500

    def test_team_spend_empty(self, alloc):
        t = alloc.get_team_spend("nonexistent")
        assert t["total_spend"] == 0

    def test_list_chargebacks_empty(self, alloc):
        assert alloc.list_chargebacks() == []

    def test_create_chargeback(self, alloc):
        cb = alloc.create_chargeback(team="platform", project="infra", amount=3000)
        assert cb.id is not None
        assert cb.invoiced is False

    def test_list_tags(self, alloc):
        tags = alloc.list_tags()
        assert len(tags) > 0
        assert any(t["key"] == "Team" for t in tags)
