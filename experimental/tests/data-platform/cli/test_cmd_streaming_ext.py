"""Tests for cmd_streaming CLI commands."""
import pytest
from click.testing import CliRunner
from cli.ipilot.commands.data_platform.cmd_streaming_pipeline import streaming

@pytest.fixture
def runner():
    return CliRunner()

class TestCmdStreaming:
    def test_list(self, runner):
        result = runner.invoke(streaming, ["list"])
        assert result.exit_code == 0

    def test_create(self, runner):
        result = runner.invoke(streaming, ["create", "test-stream", "--provider", "kafka", "--nodes", "3"])
        assert result.exit_code == 0
        assert "test-stream" in result.output

    def test_get(self, runner):
        result = runner.invoke(streaming, ["get", "test-id"])
        assert result.exit_code == 0

    def test_create_topic(self, runner):
        result = runner.invoke(streaming, ["create-topic", "cluster-id", "events", "--partitions", "6", "--replication", "3"])
        assert result.exit_code == 0

    def test_delete_topic(self, runner):
        result = runner.invoke(streaming, ["delete-topic", "cluster-id", "events"])
        assert result.exit_code == 0

    def test_scale(self, runner):
        result = runner.invoke(streaming, ["scale", "cluster-id", "--nodes", "5"])
        assert result.exit_code == 0
