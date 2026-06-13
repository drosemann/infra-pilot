import pytest
import sys
sys.path.insert(0, 'services/integration-service/src/hybrid_cloud')
from cloud_bursting import CloudBursting, BurstConfig, BurstState

@pytest.fixture
def burst():
    b = CloudBursting({"on_prem_capacity": 100})
    b.initialize()
    yield b
    b.close()

class TestCloudBursting:
    def test_initial_state(self, burst):
        assert burst.check_burst_readiness()["burst_needed"] is False

    def test_register_workload(self, burst):
        wl = burst.register_workload("test-wl", target_capacity=50, priority=3)
        assert wl.workload_id is not None
        assert wl.state == "idle"

    def test_burst_readiness_triggers(self, burst):
        burst.register_workload("wl1", target_capacity=60)
        burst.register_workload("wl2", target_capacity=50)
        status = burst.check_burst_readiness()
        assert status["burst_needed"] is True

    def test_start_burst(self, burst):
        burst.register_workload("wl1", target_capacity=50)
        b = burst.start_burst()
        assert b.state == BurstState.BURSTING
        assert b.burst_id is not None

    def test_burst_list_active(self, burst):
        burst.register_workload("wl1", target_capacity=50)
        burst.start_burst()
        active = burst.list_active_bursts()
        assert len(active) == 1

    def test_drain_burst(self, burst):
        burst.register_workload("wl1", target_capacity=50)
        b = burst.start_burst()
        result = burst.drain_burst(b.burst_id)
        assert result["status"] == "completed"

    def test_drain_nonexistent(self, burst):
        result = burst.drain_burst("nonexistent")
        assert result.get("error") == "Not found"

    def test_list_workloads(self, burst):
        burst.register_workload("wl1")
        burst.register_workload("wl2")
        assert len(burst.list_workloads()) == 2

    def test_get_burst(self, burst):
        burst.register_workload("wl1")
        b = burst.start_burst()
        found = burst.get_burst(b.burst_id)
        assert found.burst_id == b.burst_id
