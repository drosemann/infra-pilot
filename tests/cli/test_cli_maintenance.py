"""Unit tests for the maintenance command group."""

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

    module = importlib.import_module("cli.ipilot.commands.maintenance")
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
    def test_list_wraps_dict(self, client, invoke):
        client.list_maintenance_windows.return_value = {"windows": [{"id": "m1"}]}
        result = invoke(["maintenance", "list"])
        assert result.exit_code == 0
        client.list_maintenance_windows.assert_called_once()

    def test_list_passes_list(self, client, invoke):
        client.list_maintenance_windows.return_value = [{"id": "m1"}]
        result = invoke(["maintenance", "list"])
        assert result.exit_code == 0

    def test_create(self, client, invoke):
        client.create_maintenance_window.return_value = {"id": "m1"}
        result = invoke(
            [
                "maintenance",
                "create",
                "--title",
                "db upgrade",
                "--starts",
                "2026-02-01T00:00:00Z",
                "--ends",
                "2026-02-01T02:00:00Z",
            ]
        )
        assert result.exit_code == 0
        client.create_maintenance_window.assert_called_once_with(
            title="db upgrade",
            starts_at="2026-02-01T00:00:00Z",
            ends_at="2026-02-01T02:00:00Z",
            description=None,
            app_id=None,
        )

    def test_create_with_app(self, client, invoke):
        client.create_maintenance_window.return_value = {"id": "m1"}
        result = invoke(
            [
                "maintenance",
                "create",
                "--title",
                "t",
                "--starts",
                "s",
                "--ends",
                "e",
                "--app",
                "web",
            ]
        )
        assert result.exit_code == 0
        assert client.create_maintenance_window.call_args.kwargs["app_id"] == "web"


class TestUpdate:
    def test_update_title(self, client, invoke):
        client.update_maintenance_window.return_value = {"id": "m1"}
        result = invoke(["maintenance", "update", "m1", "--title", "new"])
        assert result.exit_code == 0
        client.update_maintenance_window.assert_called_once_with("m1", title="new")

    def test_update_status(self, client, invoke):
        client.update_maintenance_window.return_value = {"id": "m1"}
        result = invoke(["maintenance", "update", "m1", "--status", "active"])
        assert result.exit_code == 0
        assert client.update_maintenance_window.call_args.kwargs["status"] == "active"

    def test_update_invalid_status(self, client, invoke):
        result = invoke(["maintenance", "update", "m1", "--status", "bogus"])
        assert result.exit_code == 2
        assert "unsupported status" in result.output
        client.update_maintenance_window.assert_not_called()

    def test_update_no_fields(self, client, invoke):
        result = invoke(["maintenance", "update", "m1"])
        assert result.exit_code == 2
        client.update_maintenance_window.assert_not_called()

    def test_update_times(self, client, invoke):
        client.update_maintenance_window.return_value = {"id": "m1"}
        result = invoke(
            ["maintenance", "update", "m1", "--starts", "s2", "--ends", "e2"]
        )
        assert result.exit_code == 0
        kwargs = client.update_maintenance_window.call_args.kwargs
        assert kwargs["starts_at"] == "s2"
        assert kwargs["ends_at"] == "e2"


class TestDeleteEnableDisable:
    def test_delete(self, client, invoke):
        client.delete_maintenance_window.return_value = {"success": True}
        result = invoke(["maintenance", "delete", "m1"])
        assert result.exit_code == 0
        client.delete_maintenance_window.assert_called_once_with("m1")

    def test_enable_sets_scheduled(self, client, invoke):
        client.update_maintenance_window.return_value = {"id": "m1"}
        result = invoke(["maintenance", "enable", "m1"])
        assert result.exit_code == 0
        client.update_maintenance_window.assert_called_once_with(
            "m1", status="scheduled"
        )

    def test_disable_sets_cancelled(self, client, invoke):
        client.update_maintenance_window.return_value = {"id": "m1"}
        result = invoke(["maintenance", "disable", "m1"])
        assert result.exit_code == 0
        client.update_maintenance_window.assert_called_once_with(
            "m1", status="cancelled"
        )


class TestMaintenanceClientUrls:
    def test_list_url(self, monkeypatch):
        client, calls = _real_client(monkeypatch)
        client.list_maintenance_windows()
        assert calls[0][0] == "GET"
        assert calls[0][1] == "http://test.local/api/maintenance-windows"

    def test_create_url_and_body(self, monkeypatch):
        client, calls = _real_client(monkeypatch)
        client.create_maintenance_window("t", "s", "e")
        assert calls[0][0] == "POST"
        assert calls[0][1] == "http://test.local/api/maintenance-windows"
        assert calls[0][2]["title"] == "t"
        assert calls[0][2]["starts_at"] == "s"
        assert calls[0][2]["ends_at"] == "e"

    def test_update_url(self, monkeypatch):
        client, calls = _real_client(monkeypatch)
        client.update_maintenance_window("m1", title="new")
        assert calls[0][0] == "PATCH"
        assert calls[0][1] == "http://test.local/api/maintenance-windows/m1"
        assert calls[0][2] == {"title": "new"}

    def test_delete_url(self, monkeypatch):
        client, calls = _real_client(monkeypatch)
        client.delete_maintenance_window("m1")
        assert calls[0][0] == "DELETE"
        assert calls[0][1] == "http://test.local/api/maintenance-windows/m1"
