"""Tests for cmd_embed CLI commands."""
import pytest
from click.testing import CliRunner
from cli.ipilot.commands.data_platform.cmd_embedded_analytics import embed

@pytest.fixture
def runner():
    return CliRunner()

class TestCmdEmbed:
    def test_list_customers(self, runner):
        result = runner.invoke(embed, ["list-customers"])
        assert result.exit_code == 0

    def test_create_customer(self, runner):
        result = runner.invoke(embed, ["create-customer", "Acme Corp", "--domain", "acme.com"])
        assert result.exit_code == 0

    def test_rotate_key(self, runner):
        result = runner.invoke(embed, ["rotate-key", "customer-id"])
        assert result.exit_code == 0

    def test_list_embeds(self, runner):
        result = runner.invoke(embed, ["list-embeds"])
        assert result.exit_code == 0

    def test_create_embed(self, runner):
        result = runner.invoke(embed, ["create-embed", "customer-id", "--type", "dashboard", "--filters", '{"region":"us"}'])
        assert result.exit_code == 0

    def test_get_code(self, runner):
        result = runner.invoke(embed, ["get-code", "embed-id"])
        assert result.exit_code == 0

    def test_delete_embed(self, runner):
        result = runner.invoke(embed, ["delete-embed", "embed-id"])
        assert result.exit_code == 0

    def test_stats(self, runner):
        result = runner.invoke(embed, ["stats"])
        assert result.exit_code == 0

    def test_delete_customer(self, runner):
        result = runner.invoke(embed, ["delete-customer", "customer-id"])
        assert result.exit_code == 0
