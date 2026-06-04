"""Tests for data_lakehouse module."""
import pytest
from services.integration_service.src.data_platform.data_lakehouse import (
    LakehouseManager, LakehouseCluster, CompactResult, VacuumResult
)

@pytest.fixture
def manager():
    mgr = LakehouseManager()
    yield mgr
    mgr._clusters.clear()

class TestClusterCRUD:
    def test_create_cluster(self, manager):
        c = manager.create_cluster(name="prod-lake", engine="spark", region="us-east-1")
        assert c.cluster_id is not None
        assert c.name == "prod-lake"
        assert c.engine == "spark"
        assert c.status == "active"

    def test_get_cluster(self, manager):
        c = manager.create_cluster(name="test", engine="trino", region="eu-west-1")
        retrieved = manager.get_cluster(c.cluster_id)
        assert retrieved is not None
        assert retrieved.name == "test"

    def test_delete_cluster(self, manager):
        c = manager.create_cluster(name="del", engine="presto", region="us-west-2")
        assert manager.delete_cluster(c.cluster_id) is True
        assert manager.get_cluster(c.cluster_id) is None

    def test_list_clusters(self, manager):
        manager.create_cluster(name="c1", engine="spark", region="us-east-1")
        manager.create_cluster(name="c2", engine="trino", region="eu-west-1")
        clusters = manager.list_clusters()
        assert len(clusters) >= 2

class TestTableOperations:
    def test_compact_table(self, manager):
        result = manager.compact_table(table_id="tbl-001")
        assert isinstance(result, CompactResult)
        assert result.table_id == "tbl-001"
        assert result.status == "compacted"

    def test_vacuum_table(self, manager):
        result = manager.vacuum_table(table_id="tbl-001", retention_hours=72)
        assert isinstance(result, VacuumResult)
        assert result.table_id == "tbl-001"
        assert result.retention_hours == 72
