"""Tests for cog_data_lakehouse module."""
import pytest
from services.orchestrator_agent.cogs.data_platform.cog_data_lakehouse import CogDataLakehouse

@pytest.fixture
def cog():
    return CogDataLakehouse()

class TestCogLakehouse:
    def test_list(self, cog):
        result = cog.list()
        assert isinstance(result, list)

    def test_create(self, cog):
        result = cog.create(name="test-cluster", engine="spark", region="us-east-1")
        assert result["name"] == "test-cluster"
        assert result["status"] == "active"

    def test_get(self, cog):
        created = cog.create(name="get-test", engine="trino", region="eu-west-1")
        result = cog.get(created["cluster_id"])
        assert result["cluster_id"] == created["cluster_id"]

    def test_delete(self, cog):
        created = cog.create(name="del-test", engine="presto", region="us-west-2")
        assert cog.delete(created["cluster_id"]) is True

    def test_compact(self, cog):
        result = cog.compact("tbl-001")
        assert result["status"] == "compacted"

    def test_vacuum(self, cog):
        result = cog.vacuum("tbl-001", retention_hours=72)
        assert result["retention_hours"] == 72

    def test_deploy(self, cog):
        result = cog.deploy(name="deploy-test", engine="spark", region="us-east-1", tables=5, storage_tb=10)
        assert result["name"] == "deploy-test"

    def test_monitor(self, cog):
        created = cog.create(name="mon-test", engine="spark", region="us-east-1")
        result = cog.monitor(created["cluster_id"])
        assert result["cluster_id"] == created["cluster_id"]

    def test_scale(self, cog):
        created = cog.create(name="scale-test", engine="spark", region="us-east-1")
        result = cog.scale(created["cluster_id"], tables=10)
        assert result["tables"] == 10
