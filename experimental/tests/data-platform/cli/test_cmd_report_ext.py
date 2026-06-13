"""Tests for cmd_report CLI commands."""
import pytest
from click.testing import CliRunner
from cli.ipilot.commands.data_platform.cmd_self_service_reporting import report

@pytest.fixture
def runner():
    return CliRunner()

class TestCmdReport:
    def test_list(self, runner):
        result = runner.invoke(report, ["list"])
        assert result.exit_code == 0

    def test_create(self, runner):
        result = runner.invoke(report, ["create", "monthly-sales", "--description", "Monthly report", "--mode", "visual"])
        assert result.exit_code == 0

    def test_execute(self, runner):
        result = runner.invoke(report, ["execute", "report-id"])
        assert result.exit_code == 0

    def test_export(self, runner):
        result = runner.invoke(report, ["export", "report-id", "--format", "pdf"])
        assert result.exit_code == 0

    def test_schedule(self, runner):
        result = runner.invoke(report, ["schedule", "report-id", "--frequency", "daily", "--recipients", "admin@co.com", "--format", "pdf"])
        assert result.exit_code == 0
