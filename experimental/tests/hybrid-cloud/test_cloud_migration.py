import pytest
import sys
sys.path.insert(0, 'services/integration-service/src/hybrid_cloud')
from cloud_migration import CloudMigration, WorkloadState

@pytest.fixture
def migration():
    m = CloudMigration({})
    m.initialize()
    yield m
    m.close()

class TestCloudMigration:
    def test_list_workloads_empty(self, migration):
        assert migration.list_workloads() == []

    def test_discover_workload(self, migration):
        wl = migration.discover_workload(name="app-server", hostname="app01", os_type="linux", vcpu=4, memory_gb=8)
        assert wl.id is not None
        assert wl.state == WorkloadState.DISCOVERED

    def test_assess_workload(self, migration):
        wl = migration.discover_workload("app-server", "app01")
        assessment = migration.assess_workload(wl.id)
        assert assessment["compatibility"] is True
        assert "recommended_instance" in assessment

    def test_assess_nonexistent(self, migration):
        result = migration.assess_workload("nonexistent")
        assert result.get("error") == "Not found"

    def test_create_wave(self, migration):
        wl = migration.discover_workload("app-server", "app01")
        wave = migration.create_wave(name="Wave 1", workload_ids=[wl.id], target_provider="aws")
        assert wave.id is not None
        assert wave.state == "planned"

    def test_list_waves(self, migration):
        migration.discover_workload("s1", "srv01")
        migration.create_wave("Wave 1", [], "aws")
        migration.create_wave("Wave 2", [], "azure")
        assert len(migration.list_waves()) == 2

    def test_execute_wave(self, migration):
        wl = migration.discover_workload("s1", "srv01")
        wave = migration.create_wave("W1", [wl.id], "aws")
        result = migration.execute_wave(wave.id)
        assert result["status"] == "completed"

    def test_rollback_wave(self, migration):
        wl = migration.discover_workload("s1", "srv01")
        wave = migration.create_wave("W1", [wl.id], "aws")
        result = migration.rollback_wave(wave.id)
        assert result["status"] == "rolled_back"

    def test_execute_nonexistent(self, migration):
        result = migration.execute_wave("nonexistent")
        assert result.get("error") == "Not found"
