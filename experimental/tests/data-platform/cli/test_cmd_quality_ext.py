"""Tests for cmd_quality CLI commands."""
import pytest
from click.testing import CliRunner
from cli.ipilot.commands.data_platform.cmd_data_quality import quality

@pytest.fixture
def runner():
    return CliRunner()

class TestCmdQuality:
    def test_list_rules(self, runner):
        result = runner.invoke(quality, ["list-rules"])
        assert result.exit_code == 0

    def test_create_rule(self, runner):
        result = runner.invoke(quality, ["create-rule", "check-email", "--dataset", "users", "--column", "email", "--check-type", "not_null", "--severity", "high"])
        assert result.exit_code == 0

    def test_run(self, runner):
        result = runner.invoke(quality, ["run"])
        assert result.exit_code == 0

    def test_violations(self, runner):
        result = runner.invoke(quality, ["violations"])
        assert result.exit_code == 0

    def test_scorecard(self, runner):
        result = runner.invoke(quality, ["scorecard", "users"])
        assert result.exit_code == 0
