"""Unit tests for the audit command group."""

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

    module = importlib.import_module("cli.ipilot.commands.audit")
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
    def test_list_defaults(self, client, invoke):
        client.list_audit_log.return_value = {"data": [], "total": 0}
        result = invoke(["audit", "list"])
        assert result.exit_code == 0
        client.list_audit_log.assert_called_once_with(
            actor=None,
            action=None,
            resource=None,
            start_date=None,
            end_date=None,
            limit=50,
            offset=0,
        )

    def test_list_all_filters(self, client, invoke):
        client.list_audit_log.return_value = {"data": []}
        result = invoke(
            [
                "audit",
                "list",
                "--actor",
                "u1",
                "--action",
                "deploy",
                "--resource",
                "app",
                "--since",
                "2026-01-01",
                "--until",
                "2026-02-01",
                "--limit",
                "10",
                "--page",
                "3",
            ]
        )
        assert result.exit_code == 0
        kwargs = client.list_audit_log.call_args.kwargs
        assert kwargs["actor"] == "u1"
        assert kwargs["action"] == "deploy"
        assert kwargs["resource"] == "app"
        assert kwargs["start_date"] == "2026-01-01"
        assert kwargs["end_date"] == "2026-02-01"
        assert kwargs["limit"] == 10
        assert kwargs["offset"] == 20

    def test_list_json(self, client, invoke):
        payload = {"data": [{"id": 1}], "total": 1}
        client.list_audit_log.return_value = payload
        result = invoke(["--output", "json", "audit", "list"])
        assert result.exit_code == 0
        assert json.loads(result.output) == payload

    def test_list_limit_too_high(self, client, invoke):
        result = invoke(["audit", "list", "--limit", "500"])
        assert result.exit_code == 2
        assert "between 1 and 200" in result.output
        client.list_audit_log.assert_not_called()

    def test_list_page_below_one(self, client, invoke):
        result = invoke(["audit", "list", "--page", "0"])
        assert result.exit_code == 2


class TestExport:
    def test_export_csv_stdout(self, client, invoke):
        client.list_audit_log.return_value = {
            "data": [{"id": "a", "action": "x", "entity_type": "app"}],
            "total": 1,
        }
        result = invoke(["audit", "export", "--format", "csv"])
        assert result.exit_code == 0
        assert "id,action,entity_type" in result.output
        assert "a,x,app" in result.output

    def test_export_jsonl_stdout(self, client, invoke):
        client.list_audit_log.return_value = {
            "data": [{"id": "a", "action": "x"}],
            "total": 1,
        }
        result = invoke(["audit", "export", "--format", "jsonl"])
        assert result.exit_code == 0
        parsed = json.loads(result.output.strip().splitlines()[-1])
        assert parsed == {"id": "a", "action": "x"}

    def test_export_to_file(self, client, invoke, tmp_path):
        client.list_audit_log.return_value = {
            "data": [{"id": "a", "action": "x"}],
            "total": 1,
        }
        out = tmp_path / "audit.csv"
        result = invoke(["audit", "export", "--format", "csv", "--file", str(out)])
        assert result.exit_code == 0
        assert "Exported 1 entries" in result.output
        assert "action" in out.read_text()

    def test_export_invalid_format(self, client, invoke):
        result = invoke(["audit", "export", "--format", "pdf"])
        assert result.exit_code == 2
        client.list_audit_log.assert_not_called()

    def test_export_limit_validation(self, client, invoke):
        result = invoke(["audit", "export", "--limit", "0"])
        assert result.exit_code == 2

    def test_export_error(self, client, invoke):
        client.list_audit_log.return_value = {"error": "nope"}
        result = invoke(["audit", "export"])
        assert result.exit_code == 1
        assert "Error: nope" in result.output

    def test_export_paginates_until_limit(self, client, invoke):
        # limit is both page size and total cap: a short first page ends the loop.
        page1 = {"data": [{"id": "a"}, {"id": "b"}], "total": 6}
        client.list_audit_log.return_value = page1
        result = invoke(["audit", "export", "--format", "jsonl", "--limit", "6"])
        assert result.exit_code == 0
        assert client.list_audit_log.call_count == 1
        assert client.list_audit_log.call_args.kwargs["limit"] == 6
        assert client.list_audit_log.call_args.kwargs["offset"] == 0
        assert client.list_audit_log.call_args.kwargs["actor"] is None


class TestAuditClientUrls:
    def test_list_url(self, monkeypatch):
        client, calls = _real_client(monkeypatch)
        client.list_audit_log(limit=10, offset=20, action="deploy")
        assert calls[0][0] == "GET"
        assert calls[0][1] == (
            "http://test.local/api/audit-log?limit=10&offset=20&action=deploy"
        )

    def test_list_url_all_filters(self, monkeypatch):
        client, calls = _real_client(monkeypatch)
        client.list_audit_log(
            actor="u1", resource="app", start_date="s", end_date="e"
        )
        url = calls[0][1]
        assert "user_id=u1" in url
        assert "entity_type=app" in url
        assert "start_date=s" in url
        assert "end_date=e" in url
