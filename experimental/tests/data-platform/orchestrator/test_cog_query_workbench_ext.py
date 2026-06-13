"""Tests for cog_query_workbench module."""
import pytest
from services.orchestrator_agent.cogs.data_platform.cog_query_workbench import CogQueryWorkbench

@pytest.fixture
def cog():
    return CogQueryWorkbench()

class TestCogQuery:
    def test_list(self, cog):
        result = cog.list()
        assert isinstance(result, list)

    def test_execute(self, cog):
        result = cog.execute(sql="SELECT * FROM users")
        assert result["row_count"] >= 0
        assert result["execution_time_ms"] >= 0

    def test_save(self, cog):
        result = cog.save(name="my-query", sql="SELECT 1", database="default")
        assert result["name"] == "my-query"

    def test_delete(self, cog):
        q = cog.save(name="del-query", sql="SELECT 1", database="default")
        assert cog.delete(q["query_id"]) is True

    def test_schema(self, cog):
        result = cog.schema()
        assert len(result) > 0

    def test_deploy(self, cog):
        result = cog.deploy(name="dep-query", sql="SELECT COUNT(*) FROM users", database="analytics", schedule="daily")
        assert result["name"] == "dep-query"

    def test_monitor(self, cog):
        q = cog.save(name="mon-query", sql="SELECT 1", database="default")
        result = cog.monitor(q["query_id"])
        assert result["query_id"] == q["query_id"]
