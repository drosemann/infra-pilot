"""Tests for cmd_catalog CLI commands."""
import pytest
from click.testing import CliRunner
from cli.ipilot.commands.data_platform.cmd_data_catalog import catalog

@pytest.fixture
def runner():
    return CliRunner()

class TestCmdCatalog:
    def test_list(self, runner):
        result = runner.invoke(catalog, ["list"])
        assert result.exit_code == 0

    def test_search(self, runner):
        result = runner.invoke(catalog, ["search", "users"])
        assert result.exit_code == 0

    def test_register(self, runner):
        result = runner.invoke(catalog, ["register", "users_table", "--type", "table", "--schema", "public", "--owner", "data-team"])
        assert result.exit_code == 0

    def test_harvest(self, runner):
        result = runner.invoke(catalog, ["harvest"])
        assert result.exit_code == 0

    def test_certify(self, runner):
        result = runner.invoke(catalog, ["certify", "asset-id"])
        assert result.exit_code == 0
