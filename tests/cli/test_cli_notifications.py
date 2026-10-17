"""Unit tests for the notifications command group."""

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

    module = importlib.import_module("cli.ipilot.commands.notifications")
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


class TestListCreate:
    def test_list(self, client, invoke):
        client.list_notification_channels.return_value = [{"id": "n1"}]
        result = invoke(["notifications", "list"])
        assert result.exit_code == 0
        client.list_notification_channels.assert_called_once()

    def test_create_webhook(self, client, invoke):
        client.create_notification_channel.return_value = {"id": "n1"}
        result = invoke(
            [
                "notifications",
                "create",
                "ops-hook",
                "--type",
                "webhook",
                "--config",
                '{"url": "https://example.com/h"}',
            ]
        )
        assert result.exit_code == 0
        kwargs = client.create_notification_channel.call_args.kwargs
        assert kwargs["name"] == "ops-hook"
        assert kwargs["channel_type"] == "webhook"
        assert kwargs["config"] == {"url": "https://example.com/h"}

    def test_create_invalid_type(self, client, invoke):
        result = invoke(
            [
                "notifications",
                "create",
                "x",
                "--type",
                "carrier-pigeon",
                "--config",
                "{}",
            ]
        )
        assert result.exit_code == 2
        client.create_notification_channel.assert_not_called()

    def test_create_missing_config(self, client, invoke):
        result = invoke(["notifications", "create", "x", "--type", "email"])
        assert result.exit_code == 2
        client.create_notification_channel.assert_not_called()

    def test_create_bad_json(self, client, invoke):
        result = invoke(
            ["notifications", "create", "x", "--type", "email", "--config", "not-json"]
        )
        assert result.exit_code == 2

    def test_create_non_object_config(self, client, invoke):
        result = invoke(
            ["notifications", "create", "x", "--type", "email", "--config", "[]"]
        )
        assert result.exit_code == 2


class TestUpdate:
    def test_update_name(self, client, invoke):
        client.update_notification_channel.return_value = {"id": "n1"}
        result = invoke(["notifications", "update", "n1", "--name", "new"])
        assert result.exit_code == 0
        assert client.update_notification_channel.call_args.kwargs["name"] == "new"

    def test_update_enable(self, client, invoke):
        client.update_notification_channel.return_value = {"id": "n1"}
        result = invoke(["notifications", "update", "n1", "--enable"])
        assert result.exit_code == 0
        assert client.update_notification_channel.call_args.kwargs["enabled"] is True

    def test_update_disable(self, client, invoke):
        client.update_notification_channel.return_value = {"id": "n1"}
        result = invoke(["notifications", "update", "n1", "--disable"])
        assert result.exit_code == 0
        assert client.update_notification_channel.call_args.kwargs["enabled"] is False

    def test_update_conflicting_flags(self, client, invoke):
        result = invoke(["notifications", "update", "n1", "--enable", "--disable"])
        assert result.exit_code == 2
        client.update_notification_channel.assert_not_called()

    def test_update_no_fields(self, client, invoke):
        result = invoke(["notifications", "update", "n1"])
        assert result.exit_code == 2

    def test_update_config(self, client, invoke):
        client.update_notification_channel.return_value = {"id": "n1"}
        result = invoke(
            ["notifications", "update", "n1", "--config", '{"to": "a@b.c"}']
        )
        assert result.exit_code == 0
        assert client.update_notification_channel.call_args.kwargs["config"] == {
            "to": "a@b.c"
        }


class TestDeleteTest:
    def test_delete(self, client, invoke):
        client.delete_notification_channel.return_value = {"success": True}
        result = invoke(["notifications", "delete", "n1"])
        assert result.exit_code == 0
        client.delete_notification_channel.assert_called_once_with("n1")

    def test_test_channel(self, client, invoke):
        client.test_notification_channel.return_value = {"sent": True}
        result = invoke(["notifications", "test", "n1"])
        assert result.exit_code == 0
        client.test_notification_channel.assert_called_once_with("n1")

    def test_test_channel_error(self, client, invoke):
        client.test_notification_channel.return_value = {"error": "channel disabled"}
        result = invoke(["notifications", "test", "n1"])
        assert "Error: channel disabled" in result.output


class TestNotificationsClientUrls:
    def test_list_url(self, monkeypatch):
        client, calls = _real_client(monkeypatch)
        client.list_notification_channels()
        assert calls[0][0] == "GET"
        assert calls[0][1] == "http://test.local/api/notification-channels"

    def test_create_url_and_body(self, monkeypatch):
        client, calls = _real_client(monkeypatch)
        client.create_notification_channel("ops", "webhook", {"url": "u"})
        assert calls[0][0] == "POST"
        assert calls[0][1] == "http://test.local/api/notification-channels"
        assert calls[0][2] == {
            "name": "ops",
            "type": "webhook",
            "config": {"url": "u"},
        }

    def test_update_url(self, monkeypatch):
        client, calls = _real_client(monkeypatch)
        client.update_notification_channel("n1", name="new")
        assert calls[0][0] == "PATCH"
        assert calls[0][1] == "http://test.local/api/notification-channels/n1"
        assert calls[0][2] == {"name": "new"}

    def test_delete_url(self, monkeypatch):
        client, calls = _real_client(monkeypatch)
        client.delete_notification_channel("n1")
        assert calls[0][0] == "DELETE"
        assert calls[0][1] == "http://test.local/api/notification-channels/n1"

    def test_test_url(self, monkeypatch):
        client, calls = _real_client(monkeypatch)
        client.test_notification_channel("n1")
        assert calls[0][0] == "POST"
        assert calls[0][1] == "http://test.local/api/notification-channels/n1/test"
