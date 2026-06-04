"""Tests for cmd_pipeline CLI commands."""
import pytest
from click.testing import CliRunner
from cli.ipilot.commands.data_platform.cmd_pipeline_observability import pipeline

@pytest.fixture
def runner():
    return CliRunner()

class TestCmdPipeline:
    def test_list(self, runner):
        result = runner.invoke(pipeline, ["list"])
        assert result.exit_code == 0

    def test_create(self, runner):
        result = runner.invoke(pipeline, ["create", "etl-users", "--schedule", "0 */6 * * *"])
        assert result.exit_code == 0

    def test_start(self, runner):
        result = runner.invoke(pipeline, ["start", "pipeline-id"])
        assert result.exit_code == 0

    def test_stop(self, runner):
        result = runner.invoke(pipeline, ["stop", "pipeline-id"])
        assert result.exit_code == 0

    def test_health(self, runner):
        result = runner.invoke(pipeline, ["health", "pipeline-id"])
        assert result.exit_code == 0

    def test_rca(self, runner):
        result = runner.invoke(pipeline, ["rca", "pipeline-id"])
        assert result.exit_code == 0
