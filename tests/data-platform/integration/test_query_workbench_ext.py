"""Tests for query_workbench module."""
import pytest
from services.integration_service.src.data_platform.query_workbench import (
    QueryManager, SavedQuery, QueryResult, SchemaTable
)

@pytest.fixture
def manager():
    mgr = QueryManager()
    yield mgr
    mgr._saved_queries.clear()

class TestQueryExecution:
    def test_execute_query(self, manager):
        result = manager.execute_query("SELECT * FROM users")
        assert isinstance(result, QueryResult)
        assert len(result.columns) > 0
        assert result.row_count >= 0
        assert result.execution_time_ms >= 0

class TestSavedQueries:
    def test_save_query(self, manager):
        q = manager.save_query(name="test-query", sql="SELECT 1", database="default")
        assert q.query_id is not None
        assert q.name == "test-query"

    def test_list_saved_queries(self, manager):
        manager.save_query(name="q1", sql="SELECT 1", database="default")
        manager.save_query(name="q2", sql="SELECT 2", database="default")
        assert len(manager.list_saved_queries()) >= 2

    def test_delete_saved_query(self, manager):
        q = manager.save_query(name="del", sql="SELECT 1", database="default")
        assert manager.delete_saved_query(q.query_id) is True

class TestSchema:
    def test_get_schema(self, manager):
        tables = manager.get_schema()
        assert len(tables) > 0
        assert all(isinstance(t, SchemaTable) for t in tables)
