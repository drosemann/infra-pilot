"""Unit tests for the reports command group."""

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

    module = importlib.import_module("cli.ipilot.commands.reports")
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


def _real_client(monkeypatch, payload=None, download_text=None):
    from cli.ipilot.client import ApiClient

    client = ApiClient("http://test.local/")
    calls = []

    def fake_request(method, url, json=None, timeout=None):
        calls.append((method, url, json))
        return _FakeResponse(payload if payload is not None else {"ok": True})

    def fake_download(path):
        calls.append(("DOWNLOAD", path, None))
        if download_text is None:
            return {"content": "csv-body"}
        return {"content": download_text}

    monkeypatch.setattr(client.session, "request", fake_request)
    monkeypatch.setattr(client, "_download", fake_download)
    return client, calls


class TestGenerateList:
    def test_generate(self, client, invoke):
        client.get_report.return_value = {"rows": [{"metric": "cpu"}]}
        result = invoke(["reports", "generate"])
        assert result.exit_code == 0
        client.get_report.assert_called_once_with(start_date=None, end_date=None)

    def test_generate_with_dates(self, client, invoke):
        client.get_report.return_value = {"rows": []}
        result = invoke(
            ["reports", "generate", "--start", "2026-01-01", "--end", "2026-02-01"]
        )
        assert result.exit_code == 0
        kwargs = client.get_report.call_args.kwargs
        assert kwargs["start_date"] == "2026-01-01"
        assert kwargs["end_date"] == "2026-02-01"

    def test_list(self, client, invoke):
        client.get_report.return_value = {"rows": [{"metric": "cpu"}]}
        result = invoke(["reports", "list"])
        assert result.exit_code == 0
        client.get_report.assert_called_once()


class TestDownload:
    def test_download_stdout(self, client, invoke):
        client.download_report.return_value = {"content": "a,b\n1,2\n"}
        result = invoke(["reports", "download", "--format", "csv"])
        assert result.exit_code == 0
        assert "a,b" in result.output
        kwargs = client.download_report.call_args.kwargs
        assert kwargs["fmt"] == "csv"

    def test_download_to_file(self, client, invoke, tmp_path):
        client.download_report.return_value = {"content": "a,b\n1,2\n"}
        out = tmp_path / "report.csv"
        result = invoke(
            ["reports", "download", "--format", "csv", "--file", str(out)]
        )
        assert result.exit_code == 0
        assert "Report written to" in result.output
        assert out.read_text() == "a,b\n1,2\n"

    def test_download_invalid_format(self, client, invoke):
        result = invoke(["reports", "download", "--format", "xlsx"])
        assert result.exit_code == 2
        assert "unsupported format" in result.output
        client.download_report.assert_not_called()

    def test_download_error(self, client, invoke):
        client.download_report.return_value = {"error": "report backend down"}
        result = invoke(["reports", "download"])
        assert result.exit_code == 1
        assert "Error: report backend down" in result.output

    def test_download_with_dates(self, client, invoke):
        client.download_report.return_value = {"content": "x"}
        result = invoke(
            ["reports", "download", "--start", "s", "--end", "e"]
        )
        assert result.exit_code == 0
        kwargs = client.download_report.call_args.kwargs
        assert kwargs["start_date"] == "s"
        assert kwargs["end_date"] == "e"


class TestSchedule:
    def test_schedule_daily(self, client, invoke):
        client.create_report_schedule.return_value = {"id": "s1", "frequency": "daily"}
        result = invoke(["reports", "schedule"])
        assert result.exit_code == 0
        client.create_report_schedule.assert_called_once_with(frequency="daily")

    def test_schedule_weekly(self, client, invoke):
        client.create_report_schedule.return_value = {"id": "s1"}
        result = invoke(["reports", "schedule", "--frequency", "weekly"])
        assert result.exit_code == 0
        assert client.create_report_schedule.call_args.kwargs["frequency"] == "weekly"

    def test_schedule_invalid_frequency(self, client, invoke):
        result = invoke(["reports", "schedule", "--frequency", "hourly"])
        assert result.exit_code == 2
        assert "unsupported frequency" in result.output
        client.create_report_schedule.assert_not_called()


class TestReportsClientUrls:
    def test_get_report_no_dates(self, monkeypatch):
        client, calls = _real_client(monkeypatch)
        client.get_report()
        assert calls[0][0] == "GET"
        assert calls[0][1] == "http://test.local/api/reports"

    def test_get_report_with_dates(self, monkeypatch):
        client, calls = _real_client(monkeypatch)
        client.get_report(start_date="s", end_date="e")
        assert (
            calls[0][1]
            == "http://test.local/api/reports?start_date=s&end_date=e"
        )

    def test_download_report_url(self, monkeypatch):
        client, calls = _real_client(monkeypatch, download_text="body")
        result = client.download_report(fmt="csv", start_date="s")
        assert calls[0][0] == "DOWNLOAD"
        assert calls[0][1] == "/reports/export?format=csv&start_date=s"
        assert result == {"content": "body"}

    def test_schedule_url_and_body(self, monkeypatch):
        client, calls = _real_client(monkeypatch)
        client.create_report_schedule(frequency="weekly")
        assert calls[0][0] == "POST"
        assert calls[0][1] == "http://test.local/api/reports/schedules"
        assert calls[0][2] == {"frequency": "weekly"}
