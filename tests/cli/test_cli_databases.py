"""Unit tests for the databases command group."""

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

    module = importlib.import_module("cli.ipilot.commands.databases")
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


class TestListGet:
    def test_list(self, client, invoke):
        client.list_databases.return_value = [{"id": "d1", "name": "appdb"}]
        result = invoke(["databases", "list"])
        assert result.exit_code == 0
        client.list_databases.assert_called_once()

    def test_list_json(self, client, invoke):
        payload = {"databases": [{"id": "d1"}]}
        client.list_databases.return_value = payload
        result = invoke(["--output", "json", "databases", "list"])
        assert result.exit_code == 0
        assert json.loads(result.output) == payload["databases"]

    def test_get(self, client, invoke):
        client.get_database.return_value = {"id": "d1", "name": "appdb"}
        result = invoke(["databases", "show", "d1"])
        assert result.exit_code == 0
        client.get_database.assert_called_once_with("d1")


class TestCreateDelete:
    def test_create(self, client, invoke):
        client.create_database.return_value = {"id": "d1", "name": "appdb"}
        result = invoke(["databases", "create", "appdb"])
        assert result.exit_code == 0
        args = client.create_database.call_args.args
        kwargs = client.create_database.call_args.kwargs
        assert args[0] == "appdb"
        assert kwargs["app_id"] is None

    def test_create_with_app(self, client, invoke):
        client.create_database.return_value = {"id": "d1"}
        result = invoke(["databases", "create", "appdb", "--app", "web"])
        assert result.exit_code == 0
        kwargs = client.create_database.call_args.kwargs
        assert kwargs["app_id"] == "web"

    def test_delete(self, client, invoke):
        client.delete_database.return_value = {"success": True}
        result = invoke(["databases", "delete", "d1"])
        assert result.exit_code == 0
        client.delete_database.assert_called_once_with("d1")

    def test_delete_error(self, client, invoke):
        client.delete_database.return_value = {"error": "Database not found"}
        result = invoke(["databases", "delete", "d1"])
        assert "Error: Database not found" in result.output


class TestDatabasesClientUrls:
    def test_list_url(self, monkeypatch):
        client, calls = _real_client(monkeypatch)
        client.list_databases()
        assert calls[0][0] == "GET"
        assert calls[0][1] == "http://test.local/api/databases"

    def test_create_url_and_body(self, monkeypatch):
        client, calls = _real_client(monkeypatch)
        client.create_database("appdb")
        assert calls[0][0] == "POST"
        assert calls[0][1] == "http://test.local/api/databases"
        assert calls[0][2] == {"name": "appdb"}

    def test_create_url_with_app(self, monkeypatch):
        client, calls = _real_client(monkeypatch)
        client.create_database("appdb", app_id="web")
        assert calls[0][2] == {"name": "appdb", "appId": "web"}

    def test_get_url(self, monkeypatch):
        client, calls = _real_client(monkeypatch)
        client.get_database("d1")
        assert calls[0][0] == "GET"
        assert calls[0][1] == "http://test.local/api/databases/d1"

    def test_delete_url(self, monkeypatch):
        client, calls = _real_client(monkeypatch)
        client.delete_database("d1")
        assert calls[0][0] == "DELETE"
        assert calls[0][1] == "http://test.local/api/databases/d1"
