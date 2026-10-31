"""Unit tests for the `ipilot flags` command group."""

import importlib
from unittest.mock import MagicMock

import pytest
from typer.testing import CliRunner


@pytest.fixture
def client():
    return MagicMock()


@pytest.fixture
def runner(client, monkeypatch, tmp_path):
    module = importlib.import_module("cli.ipilot.commands.feature_flags")
    monkeypatch.setattr(module, "_get_client", lambda ctx: client)
    config_dir = tmp_path / ".ipilot"
    monkeypatch.setattr("cli.ipilot.config.CONFIG_DIR", str(config_dir))
    monkeypatch.setattr(
        "cli.ipilot.config.CONFIG_FILE", str(config_dir / "config.json")
    )
    return CliRunner()


@pytest.fixture
def invoke(runner):
    from cli.ipilot.main import app as main_app

    return lambda args, **kwargs: runner.invoke(main_app, args, **kwargs)


class TestFlags:
    def test_list(self, client, invoke):
        client.list_flags.return_value = {"flags": []}
        result = invoke(["flags", "list"])
        assert result.exit_code == 0
        client.list_flags.assert_called_once_with()

    def test_evaluate(self, client, invoke):
        client.evaluate_flags.return_value = {"flags": {"living_fleet": False}}
        result = invoke(["flags", "evaluate"])
        assert result.exit_code == 0
        client.evaluate_flags.assert_called_once_with()

    def test_create(self, client, invoke):
        client.create_flag.return_value = {"flag": {"key": "living_fleet"}}
        result = invoke(["flags", "create", "living_fleet"])
        assert result.exit_code == 0
        client.create_flag.assert_called_once_with("living_fleet", "")

    def test_rollout(self, client, invoke):
        client.set_flag_rule.return_value = {"ok": True}
        result = invoke(
            ["flags", "rollout", "living_fleet", "--env", "production",
             "--enable", "--percent", "50"]
        )
        assert result.exit_code == 0
        client.set_flag_rule.assert_called_once_with(
            "living_fleet", "production", True, 50
        )

    def test_rollout_disable(self, client, invoke):
        client.set_flag_rule.return_value = {"ok": True}
        result = invoke(["flags", "rollout", "living_fleet", "--disable"])
        assert result.exit_code == 0
        client.set_flag_rule.assert_called_once_with(
            "living_fleet", "production", False, 0
        )

    def test_kill(self, client, invoke):
        client.kill_flag.return_value = {"ok": True, "killed": "living_fleet"}
        result = invoke(["flags", "kill", "living_fleet"])
        assert result.exit_code == 0
        client.kill_flag.assert_called_once_with("living_fleet")


class TestFlagClient:
    def test_client_paths(self, monkeypatch):
        from cli.ipilot import client as client_module

        calls = []

        class FakeSession:
            headers = {}

            def request(self, *args, **kwargs):
                calls.append((args, kwargs))
                response = MagicMock()
                response.status_code = 200
                response.content = b"{}"
                response.json.return_value = {}
                response.text = "{}"
                response.raise_for_status.return_value = None
                return response

        api = client_module.ApiClient("http://localhost:3001", "tok")
        api.session = FakeSession()
        api.list_flags()
        api.evaluate_flags()
        api.create_flag("living_fleet", "desc")
        api.set_flag_rule("living_fleet", "production", True, 50)
        api.kill_flag("living_fleet")
        urls = [c[0][1] for c in calls]
        assert urls == [
            "http://localhost:3001/api/feature-flags",
            "http://localhost:3001/api/feature-flags/evaluate",
            "http://localhost:3001/api/feature-flags",
            "http://localhost:3001/api/feature-flags/living_fleet",
            "http://localhost:3001/api/feature-flags/living_fleet/kill",
        ]
        methods = [c[0][0] for c in calls]
        assert methods == ["GET", "GET", "POST", "PATCH", "POST"]
