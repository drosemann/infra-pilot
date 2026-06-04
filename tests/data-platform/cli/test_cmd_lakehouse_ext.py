"""Tests for cmd_lakehouse CLI commands."""
import pytest
from click.testing import CliRunner
from cli.ipilot.commands.data_platform.cmd_data_lakehouse import lakehouse

@pytest.fixture
def runner():
    return CliRunner()

class TestCmdLakehouse:
    def test_list(self, runner):
        result = runner.invoke(lakehouse, ["list"])
        assert result.exit_code == 0

    def test_create(self, runner):
        result = runner.invoke(lakehouse, ["create", "test-cluster", "--engine", "spark", "--region", "us-east-1"])
        assert result.exit_code == 0
        assert "test-cluster" in result.output

    def test_get(self, runner):
        result = runner.invoke(lakehouse, ["get", "test-id"])
        assert result.exit_code == 0

    def test_delete(self, runner):
        result = runner.invoke(lakehouse, ["delete", "test-id"])
        assert result.exit_code == 0

    def test_compact(self, runner):
        result = runner.invoke(lakehouse, ["compact", "tbl-001"])
        assert result.exit_code == 0

    def test_vacuum(self, runner):
        result = runner.invoke(lakehouse, ["vacuum", "tbl-001", "--retention", "168"])
        assert result.exit_code == 0
