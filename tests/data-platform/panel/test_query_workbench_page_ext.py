"""Tests for QueryWorkbenchPage component."""
import pytest
from services.management_panel.src.pages.data_platform.QueryWorkbenchPage import QueryWorkbenchPage

class TestQueryWorkbenchPage:
    def test_page_render(self):
        assert QueryWorkbenchPage is not None

    def test_saved_queries_state(self):
        page = QueryWorkbenchPage()
        assert hasattr(page, "savedQueries")

    def test_execute_query(self):
        page = QueryWorkbenchPage()
        result = page.execute_query("SELECT * FROM users")
        assert result["row_count"] >= 0

    def test_save_query(self):
        page = QueryWorkbenchPage()
        n = len(page.savedQueries)
        page.save_query("test-query", "SELECT 1", "default")
        assert len(page.savedQueries) == n + 1

    def test_delete_query(self):
        page = QueryWorkbenchPage()
        page.save_query("del", "SELECT 1", "default")
        qid = page.savedQueries[0]["query_id"]
        page.delete_query(qid)
        assert qid not in [q["query_id"] for q in page.savedQueries]

    def test_get_schema(self):
        page = QueryWorkbenchPage()
        schema = page.get_schema()
        assert len(schema) > 0
