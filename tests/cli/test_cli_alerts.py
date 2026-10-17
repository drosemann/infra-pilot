"""Unit tests for the alerts command group."""

import json
from unittest.mock import MagicMock

import pytest
from typer.testing import CliRunner


@pytest.fixture
def client():
    return MagicMock()


@pytest.fixture
def runner(client, monkeypatch, tmp_path):
    import importlib

    module = importlib.import_module("cli.ipilot.commands.alerts")
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


class _FakeResponse:
    def __init__(self, payload=None):
        self._payload = payload if payload is not None else {"ok": True}
        self.content = b"{}"
        self.text = ""
        self.status_code = 200

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def _real_client(monkeypatch, payload=None):
    from cli.ipilot.client import ApiClient

    client = ApiClient("http://test.local/")
    calls = []

    def fake_request(method, url, json=None, timeout=None):
        calls.append((method, url, json))
        return _FakeResponse(payload if payload is not None else {"ok": True})

    monkeypatch.setattr(client.session, "request", fake_request)
    return client, calls


class TestList:
    def test_list_history_default(self, client, invoke):
        client.list_alert_history.return_value = [{"id": 1, "metric_type": "cpu"}]
        result = invoke(["alerts", "list"])
        assert result.exit_code == 0
        client.list_alert_history.assert_called_once_with(limit=100)

    def test_list_history_limit(self, client, invoke):
        client.list_alert_history.return_value = []
        result = invoke(["alerts", "list", "--limit", "5"])
        assert result.exit_code == 0
        client.list_alert_history.assert_called_once_with(limit=5)

    def test_list_rules(self, client, invoke):
        client.list_alert_configs.return_value = [{"id": "c1"}]
        result = invoke(["alerts", "list", "--rules"])
        assert result.exit_code == 0
        client.list_alert_configs.assert_called_once()
        client.list_alert_history.assert_not_called()

    def test_list_rules_json(self, client, invoke):
        payload = {"rules": [{"id": "c1", "metric_type": "mem"}]}
        client.list_alert_configs.return_value = payload
        result = invoke(["--output", "json", "alerts", "list", "--rules"])
        assert result.exit_code == 0
        assert json.loads(result.output) == payload


class TestShow:
    def test_show_finds_entry(self, client, invoke):
        client.list_alert_history.return_value = [
            {"id": 1, "metric_type": "cpu"},
            {"id": 2, "metric_type": "mem"},
        ]
        result = invoke(["alerts", "show", "2"])
        assert result.exit_code == 0
        assert "mem" in result.output

    def test_show_wrapped_data(self, client, invoke):
        client.list_alert_history.return_value = {"data": [{"id": 7, "metric_type": "tps"}]}
        result = invoke(["alerts", "show", "7"])
        assert result.exit_code == 0
        assert "tps" in result.output

    def test_show_missing(self, client, invoke):
        client.list_alert_history.return_value = [{"id": 1}]
        result = invoke(["alerts", "show", "999"])
        assert result.exit_code == 0
        assert "not found" in result.output


class TestAcknowledgeResolve:
    def test_acknowledge(self, client, invoke):
        client.acknowledge_alert.return_value = {"acknowledged": True}
        result = invoke(["alerts", "acknowledge", "55"])
        assert result.exit_code == 0
        client.acknowledge_alert.assert_called_once_with("55")

    def test_acknowledge_error(self, client, invoke):
        client.acknowledge_alert.return_value = {"error": "Alert not found"}
        result = invoke(["alerts", "acknowledge", "55"])
        assert "Error: Alert not found" in result.output

    def test_resolve(self, client, invoke):
        client.resolve_alert.return_value = {"resolved": True}
        result = invoke(["alerts", "resolve", "66"])
        assert result.exit_code == 0
        client.resolve_alert.assert_called_once_with("66")


class TestRules:
    def test_create_rule_defaults(self, client, invoke):
        client.create_alert_config.return_value = {"id": "c1"}
        result = invoke(
            ["alerts", "create-rule", "--metric", "cpu", "--operator", "gt", "--threshold", "90"]
        )
        assert result.exit_code == 0
        client.create_alert_config.assert_called_once_with(
            metric_type="cpu",
            operator="gt",
            threshold=90.0,
            enabled=True,
            notify_email=False,
        )

    def test_create_rule_disabled_email(self, client, invoke):
        client.create_alert_config.return_value = {"id": "c1"}
        result = invoke(
            [
                "alerts",
                "create-rule",
                "--metric",
                "mem",
                "--operator",
                "gte",
                "--threshold",
                "80",
                "--disabled",
                "--notify-email",
            ]
        )
        assert result.exit_code == 0
        assert client.create_alert_config.call_args.kwargs["enabled"] is False
        assert client.create_alert_config.call_args.kwargs["notify_email"] is True

    def test_create_rule_invalid_operator(self, client, invoke):
        result = invoke(
            ["alerts", "create-rule", "--metric", "cpu", "--operator", "??", "--threshold", "1"]
        )
        assert result.exit_code == 2
        client.create_alert_config.assert_not_called()

    def test_update_rule_fields(self, client, invoke):
        client.update_alert_config.return_value = {"id": "c1"}
        result = invoke(["alerts", "update-rule", "c1", "--threshold", "55", "--enable"])
        assert result.exit_code == 0
        client.update_alert_config.assert_called_once_with("c1", threshold=55.0, enabled=True)

    def test_update_rule_disable(self, client, invoke):
        client.update_alert_config.return_value = {"id": "c1"}
        result = invoke(["alerts", "update-rule", "c1", "--disable"])
        assert result.exit_code == 0
        client.update_alert_config.assert_called_once_with("c1", enabled=False)

    def test_update_rule_no_fields(self, client, invoke):
        result = invoke(["alerts", "update-rule", "c1"])
        assert result.exit_code == 2
        client.update_alert_config.assert_not_called()

    def test_update_rule_conflicting_flags(self, client, invoke):
        result = invoke(["alerts", "update-rule", "c1", "--enable", "--disable"])
        assert result.exit_code == 2

    def test_update_rule_invalid_operator(self, client, invoke):
        result = invoke(["alerts", "update-rule", "c1", "--operator", "??"])
        assert result.exit_code == 2

    def test_delete_rule(self, client, invoke):
        client.delete_alert_config.return_value = {"success": True}
        result = invoke(["alerts", "delete-rule", "c1"])
        assert result.exit_code == 0
        client.delete_alert_config.assert_called_once_with("c1")

    def test_delete_rule_error(self, client, invoke):
        client.delete_alert_config.return_value = {"error": "Alert config not found"}
        result = invoke(["alerts", "delete-rule", "c1"])
        assert "Error: Alert config not found" in result.output


class TestAlertsClientUrls:
    def test_list_configs_url(self, monkeypatch):
        client, calls = _real_client(monkeypatch)
        client.list_alert_configs()
        assert calls[0][0] == "GET"
        assert calls[0][1] == "http://test.local/api/alert-configs"

    def test_create_config_url_and_body(self, monkeypatch):
        client, calls = _real_client(monkeypatch)
        client.create_alert_config("cpu", "gt", 90.5)
        assert calls[0][0] == "POST"
        assert calls[0][1] == "http://test.local/api/alert-configs"
        assert calls[0][2]["metric_type"] == "cpu"
        assert calls[0][2]["threshold"] == 90.5

    def test_update_config_url(self, monkeypatch):
        client, calls = _real_client(monkeypatch)
        client.update_alert_config("c1", threshold=10)
        assert calls[0][0] == "PATCH"
        assert calls[0][1] == "http://test.local/api/alert-configs/c1"
        assert calls[0][2] == {"threshold": 10}

    def test_delete_config_url(self, monkeypatch):
        client, calls = _real_client(monkeypatch)
        client.delete_alert_config("c1")
        assert calls[0][0] == "DELETE"
        assert calls[0][1] == "http://test.local/api/alert-configs/c1"

    def test_history_url_with_limit(self, monkeypatch):
        client, calls = _real_client(monkeypatch)
        client.list_alert_history(limit=25)
        assert calls[0][1] == "http://test.local/api/alert-history?limit=25"

    def test_acknowledge_url(self, monkeypatch):
        client, calls = _real_client(monkeypatch)
        client.acknowledge_alert("9")
        assert calls[0][0] == "POST"
        assert calls[0][1] == "http://test.local/api/alert-history/9/acknowledge"

    def test_resolve_url(self, monkeypatch):
        client, calls = _real_client(monkeypatch)
        client.resolve_alert("9")
        assert calls[0][1] == "http://test.local/api/alert-history/9/resolve"
