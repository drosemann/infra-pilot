"""Tests for cmd_query CLI commands."""
import pytest
from click.testing import CliRunner
from cli.ipilot.commands.data_platform.cmd_query_workbench import query

@pytest.fixture
def runner():
    return CliRunner()

class TestCmdQuery:
    def test_list(self, runner):
        result = runner.invoke(query, ["list"])
        assert result.exit_code == 0

    def test_execute(self, runner):
        result = runner.invoke(query, ["execute", "SELECT * FROM users"])
        assert result.exit_code == 0

    def test_save(self, runner):
        result = runner.invoke(query, ["save", "my-query", "--sql", "SELECT 1", "--database", "default"])
        assert result.exit_code == 0

    def test_delete(self, runner):
        result = runner.invoke(query, ["delete", "query-id"])
        assert result.exit_code == 0

    def test_schema(self, runner):
        result = runner.invoke(query, ["schema"])
        assert result.exit_code == 0
