"""Tests for cmd_realtime CLI commands."""
import pytest
from click.testing import CliRunner
from cli.ipilot.commands.data_platform.cmd_realtime_analytics import realtime

@pytest.fixture
def runner():
    return CliRunner()

class TestCmdRealtime:
    def test_list(self, runner):
        result = runner.invoke(realtime, ["list"])
        assert result.exit_code == 0

    def test_create(self, runner):
        result = runner.invoke(realtime, ["create", "infra-monitor", "--refresh", "10"])
        assert result.exit_code == 0

    def test_delete(self, runner):
        result = runner.invoke(realtime, ["delete", "dashboard-id"])
        assert result.exit_code == 0

    def test_live(self, runner):
        result = runner.invoke(realtime, ["live", "dashboard-id"])
        assert result.exit_code == 0

    def test_ingest(self, runner):
        result = runner.invoke(realtime, ["ingest", "cpu_usage", "--value", "87.5"])
        assert result.exit_code == 0
