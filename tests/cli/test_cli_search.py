"""Unit tests for the search command group."""

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

    module = importlib.import_module("cli.ipilot.commands.search")
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


class TestHelpers:
    def test_normalise_maps_legacy_rows(self):
        from cli.ipilot.commands.search import _normalise

        rows = [{"id": 1, "name": "web", "type": "app", "status": "running"}]
        out = _normalise(rows)
        assert out == [
            {"type": "app", "id": 1, "title": "web", "subtitle": "running"}
        ]

    def test_normalise_skips_non_dicts(self):
        from cli.ipilot.commands.search import _normalise

        assert _normalise(["junk", 5, None]) == []

    def test_dedupe_by_type_and_id(self):
        from cli.ipilot.commands.search import _dedupe

        rows = [
            {"type": "app", "id": 1, "title": "a"},
            {"type": "app", "id": 1, "title": "a-dup"},
            {"type": "db", "id": 1, "title": "b"},
        ]
        out = _dedupe(rows)
        assert len(out) == 2
        assert out[0]["title"] == "a"


class TestSearch:
    def test_search_prints_results(self, client, invoke):
        client.global_search.return_value = {
            "results": [
                {"type": "app", "id": 1, "title": "web", "subtitle": "running"}
            ]
        }
        result = invoke(["search", "web"])
        assert result.exit_code == 0
        client.global_search.assert_called_once_with("web")

    def test_search_json(self, client, invoke):
        payload = {
            "results": [
                {"type": "app", "id": 1, "title": "web", "subtitle": "running"}
            ]
        }
        client.global_search.return_value = payload
        result = invoke(["--output", "json", "search", "web"])
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert parsed[0]["title"] == "web"

    def test_search_type_filter(self, client, invoke):
        client.global_search.return_value = {
            "results": [
                {"type": "app", "id": 1, "title": "web"},
                {"type": "db", "id": 2, "title": "appdb"},
            ]
        }
        result = invoke(["search", "app", "--type", "db"])
        assert result.exit_code == 0
        assert "appdb" in result.output
        assert "web" not in result.output

    def test_search_limit(self, client, invoke):
        client.global_search.return_value = {
            "results": [{"type": "app", "id": i, "title": f"t{i}"} for i in range(5)]
        }
        result = invoke(["search", "web", "--limit", "2"])
        assert result.exit_code == 0
        assert "t4" not in result.output

    def test_search_short_query(self, client, invoke):
        result = invoke(["search", "a"])
        assert result.exit_code == 2
        assert "at least 2 characters" in result.output
        client.global_search.assert_not_called()

    def test_search_invalid_limit(self, client, invoke):
        result = invoke(["search", "ab", "--limit", "0"])
        assert result.exit_code == 2
        client.global_search.assert_not_called()

    def test_search_falls_back_to_legacy(self, client, invoke):
        client.global_search.return_value = {"error": "Not found"}
        client.basic_search.return_value = {
            "results": [{"type": "app", "id": 1, "name": "web"}]
        }
        result = invoke(["search", "web"])
        assert result.exit_code == 0
        client.basic_search.assert_called_once_with("web")
        assert "web" in result.output

    def test_search_both_endpoints_error(self, client, invoke):
        client.global_search.return_value = {"error": "down"}
        client.basic_search.return_value = {"error": "also down"}
        result = invoke(["search", "web"])
        assert result.exit_code == 0
        assert "Error" in result.output


class TestSearchClientUrls:
    def test_global_search_url(self, monkeypatch):
        client, calls = _real_client(monkeypatch)
        client.global_search("web server")
        assert calls[0][0] == "GET"
        assert calls[0][1] == "http://test.local/api/global-search?q=web+server"

    def test_basic_search_url(self, monkeypatch):
        client, calls = _real_client(monkeypatch)
        client.basic_search("app")
        assert calls[0][0] == "GET"
        assert calls[0][1] == "http://test.local/api/search?q=app"
