"""Unit tests for the metrics command group."""

import json
from unittest.mock import MagicMock

import pytest
from typer.testing import CliRunner

from cli.ipilot.commands.metrics import resolve_period


@pytest.fixture
def client():
    return MagicMock()


@pytest.fixture
def runner(client, monkeypatch, tmp_path):
    import importlib

    module = importlib.import_module("cli.ipilot.commands.metrics")
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


def _capture_urls(client, monkeypatch):
    calls = []

    def fake_request(method, url, json=None, timeout=None):
        calls.append((method, url, json))
        return _FakeResponse()

    monkeypatch.setattr(client.session, "request", fake_request)
    return client, calls


def _real_client(monkeypatch):
    from cli.ipilot.client import ApiClient

    return _capture_urls(ApiClient("http://test.local/"), monkeypatch)


class TestResolvePeriod:
    def test_defaults_to_1h(self):
        assert resolve_period(None, None) == "1h"

    @pytest.mark.parametrize("token", ["1h", "6h", "24h", "7d"])
    def test_relative_tokens_pass_through(self, token):
        assert resolve_period(token, None) == token

    def test_iso_since_maps_to_smallest_covering_period(self):
        assert resolve_period("2026-01-01T00:00:00Z", "2026-01-01T02:00:00Z") == "6h"

    def test_iso_since_larger_than_all_periods(self):
        assert resolve_period("2026-01-01T00:00:00Z", "2026-02-01T00:00:00Z") == "7d"

    def test_until_before_since_raises(self):
        from typer import BadParameter

        with pytest.raises(BadParameter):
            resolve_period("2026-01-02T00:00:00Z", "2026-01-01T00:00:00Z")


class TestMetricsCommands:
    def test_realtime_default(self, client, invoke):
        client.metrics_realtime.return_value = {"cpu": {"current": 1.5}}
        result = invoke(["metrics", "realtime"])
        assert result.exit_code == 0
        client.metrics_realtime.assert_called_once_with(app_id=None)

    def test_realtime_with_app(self, client, invoke):
        client.metrics_realtime.return_value = {"cpu": {"current": 2.0}}
        result = invoke(["metrics", "realtime", "--app", "app-1"])
        assert result.exit_code == 0
        client.metrics_realtime.assert_called_once_with(app_id="app-1")

    def test_realtime_json_output(self, client, invoke):
        payload = {"cpu": {"current": 3.0, "unit": "%"}, "timestamp": "now"}
        client.metrics_realtime.return_value = payload
        result = invoke(["--output", "json", "metrics", "realtime"])
        assert result.exit_code == 0
        assert json.loads(result.output) == payload

    def test_history_defaults(self, client, invoke):
        client.metrics_history.return_value = {"data": [], "period": "1h"}
        result = invoke(["metrics", "history"])
        assert result.exit_code == 0
        client.metrics_history.assert_called_once_with(
            app_id=None, period="1h", resolution="5m", until=None
        )

    def test_history_full_flags(self, client, invoke):
        client.metrics_history.return_value = {"data": []}
        result = invoke(
            [
                "metrics",
                "history",
                "--app",
                "app-2",
                "--since",
                "24h",
                "--until",
                "2026-01-02T00:00:00Z",
                "--interval",
                "1h",
            ]
        )
        assert result.exit_code == 0
        client.metrics_history.assert_called_once_with(
            app_id="app-2",
            period="24h",
            resolution="1h",
            until="2026-01-02T00:00:00Z",
        )

    def test_history_iso_since_computes_period(self, client, invoke):
        client.metrics_history.return_value = {"data": []}
        result = invoke(
            [
                "metrics",
                "history",
                "--since",
                "2026-01-01T00:00:00Z",
                "--until",
                "2026-01-01T03:00:00Z",
            ]
        )
        assert result.exit_code == 0
        assert client.metrics_history.call_args.kwargs["period"] == "6h"

    def test_history_invalid_interval(self, client, invoke):
        result = invoke(["metrics", "history", "--interval", "30s"])
        assert result.exit_code == 2
        assert "unsupported interval" in result.output
        client.metrics_history.assert_not_called()

    def test_history_invalid_since(self, client, invoke):
        result = invoke(["metrics", "history", "--since", "long-ago"])
        assert result.exit_code == 2
        assert "Error" in result.output
        client.metrics_history.assert_not_called()

    def test_history_until_before_since(self, client, invoke):
        result = invoke(
            [
                "metrics",
                "history",
                "--since",
                "2026-01-02T00:00:00Z",
                "--until",
                "2026-01-01T00:00:00Z",
            ]
        )
        assert result.exit_code == 2
        assert "--until must be after --since" in result.output

    def test_aggregated(self, client, invoke):
        client.metrics_aggregated.return_value = {"totalApps": 3}
        result = invoke(["metrics", "aggregated"])
        assert result.exit_code == 0
        client.metrics_aggregated.assert_called_once()

    def test_grafana_url(self, client, invoke):
        client.metrics_grafana_url.return_value = {"url": "http://g"}
        result = invoke(["metrics", "grafana-url"])
        assert result.exit_code == 0
        client.metrics_grafana_url.assert_called_once()

    def test_error_response_renders(self, client, invoke):
        client.metrics_aggregated.return_value = {"error": "boom"}
        result = invoke(["metrics", "aggregated"])
        assert result.exit_code == 0
        assert "Error: boom" in result.output


class TestMetricsClientUrls:
    def test_realtime_url(self, monkeypatch):
        client, calls = _real_client(monkeypatch)
        client.metrics_realtime(app_id="a1")
        assert calls[0][0] == "GET"
        assert calls[0][1] == "http://test.local/api/metrics/realtime?appId=a1"

    def test_realtime_url_without_app(self, monkeypatch):
        client, calls = _real_client(monkeypatch)
        client.metrics_realtime()
        assert calls[0][1] == "http://test.local/api/metrics/realtime"

    def test_history_url(self, monkeypatch):
        client, calls = _real_client(monkeypatch)
        client.metrics_history(app_id="a1", period="6h", resolution="1m")
        assert calls[0][1] == (
            "http://test.local/api/metrics/history"
            "?period=6h&resolution=1m&appId=a1"
        )

    def test_aggregated_url(self, monkeypatch):
        client, calls = _real_client(monkeypatch)
        client.metrics_aggregated()
        assert calls[0][1] == "http://test.local/api/metrics/aggregated"

    def test_grafana_url_endpoint(self, monkeypatch):
        client, calls = _real_client(monkeypatch)
        client.metrics_grafana_url()
        assert calls[0][1] == "http://test.local/api/metrics/grafana-url"
