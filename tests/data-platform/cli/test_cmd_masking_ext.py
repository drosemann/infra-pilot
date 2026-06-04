"""Tests for cmd_masking CLI commands."""
import pytest
from click.testing import CliRunner
from cli.ipilot.commands.data_platform.cmd_data_masking import masking

@pytest.fixture
def runner():
    return CliRunner()

class TestCmdMasking:
    def test_list_rules(self, runner):
        result = runner.invoke(masking, ["list-rules"])
        assert result.exit_code == 0

    def test_create_rule(self, runner):
        result = runner.invoke(masking, ["create-rule", "hide-ssn", "--column-pattern", "ssn", "--method", "hash", "--severity", "critical"])
        assert result.exit_code == 0

    def test_list_profiles(self, runner):
        result = runner.invoke(masking, ["list-profiles"])
        assert result.exit_code == 0

    def test_create_profile(self, runner):
        result = runner.invoke(masking, ["create-profile", "pii", "--targets", "users,customers", "--rule-ids", "r1"])
        assert result.exit_code == 0

    def test_apply(self, runner):
        result = runner.invoke(masking, ["apply", "profile-id"])
        assert result.exit_code == 0
