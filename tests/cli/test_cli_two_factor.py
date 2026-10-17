"""Unit tests for the two-factor command group."""

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

    module = importlib.import_module("cli.ipilot.commands.two_factor")
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


class TestStatus:
    def test_status_with_user_flag(self, client, invoke):
        client.get_2fa_backup_codes.return_value = {"backup_codes": ["a", "b"]}
        result = invoke(["two-factor", "status", "--user", "u1"])
        assert result.exit_code == 0
        client.get_2fa_backup_codes.assert_called_once_with("u1")
        client.get_current_user.assert_not_called()

    def test_status_resolves_current_user(self, client, invoke):
        client.get_current_user.return_value = {"id": "u9"}
        client.get_2fa_backup_codes.return_value = {"backup_codes": []}
        result = invoke(["two-factor", "status"])
        assert result.exit_code == 0
        client.get_2fa_backup_codes.assert_called_once_with("u9")

    def test_status_no_user_available(self, client, invoke):
        client.get_current_user.return_value = {"error": "unauthorized"}
        result = invoke(["two-factor", "status"])
        assert result.exit_code == 1
        client.get_2fa_backup_codes.assert_not_called()


class TestSetupVerifyDisable:
    def test_setup(self, client, invoke):
        client.setup_2fa.return_value = {"secret": "s", "uri": "otpauth://x"}
        result = invoke(["two-factor", "setup", "--user", "u1"])
        assert result.exit_code == 0
        client.setup_2fa.assert_called_once_with("u1")

    def test_setup_resolves_user(self, client, invoke):
        client.get_current_user.return_value = {"id": "u9"}
        client.setup_2fa.return_value = {"secret": "s"}
        result = invoke(["two-factor", "setup"])
        assert result.exit_code == 0
        client.setup_2fa.assert_called_once_with("u9")

    def test_verify(self, client, invoke):
        client.verify_2fa_setup.return_value = {"success": True}
        result = invoke(["two-factor", "verify", "123456", "--user", "u1"])
        assert result.exit_code == 0
        client.verify_2fa_setup.assert_called_once_with("u1", "123456")

    def test_disable(self, client, invoke):
        client.disable_2fa.return_value = {"disabled": True}
        result = invoke(
            ["two-factor", "disable", "--password", "hunter2", "--user", "u1"]
        )
        assert result.exit_code == 0
        client.disable_2fa.assert_called_once_with("u1", "hunter2")

    def test_disable_missing_password(self, client, invoke):
        result = invoke(["two-factor", "disable"])
        assert result.exit_code == 2
        client.disable_2fa.assert_not_called()


class TestBackupCodes:
    def test_backup_codes_fetch(self, client, invoke):
        client.get_2fa_backup_codes.return_value = {"backup_codes": ["x", "y"]}
        result = invoke(["two-factor", "backup-codes", "--user", "u1"])
        assert result.exit_code == 0
        client.get_2fa_backup_codes.assert_called_once_with("u1")
        client.setup_2fa.assert_not_called()

    def test_backup_codes_regenerate(self, client, invoke):
        client.setup_2fa.return_value = {"secret": "s"}
        client.get_2fa_backup_codes.return_value = {"backup_codes": ["z"]}
        result = invoke(
            ["two-factor", "backup-codes", "--regenerate", "--user", "u1"]
        )
        assert result.exit_code == 0
        client.setup_2fa.assert_called_once_with("u1")
        client.get_2fa_backup_codes.assert_not_called()


class TestTwoFactorClientUrls:
    def test_setup_url(self, monkeypatch):
        client, calls = _real_client(monkeypatch)
        client.setup_2fa("u1")
        assert calls[0][0] == "POST"
        assert calls[0][1] == "http://test.local/api/auth/2fa/setup"
        assert calls[0][2] == {"user_id": "u1"}

    def test_verify_setup_url(self, monkeypatch):
        client, calls = _real_client(monkeypatch)
        client.verify_2fa_setup("u1", "123456")
        assert calls[0][1] == "http://test.local/api/auth/2fa/verify-setup"
        assert calls[0][2] == {"user_id": "u1", "totp_code": "123456"}

    def test_verify_url(self, monkeypatch):
        client, calls = _real_client(monkeypatch)
        client.verify_2fa("t1", "123456")
        assert calls[0][1] == "http://test.local/api/auth/2fa/verify"
        assert calls[0][2] == {"temp_token": "t1", "totp_code": "123456"}

    def test_verify_backup_url(self, monkeypatch):
        client, calls = _real_client(monkeypatch)
        client.verify_2fa_backup("t1", "code")
        assert calls[0][1] == "http://test.local/api/auth/2fa/verify-backup"
        assert calls[0][2] == {"temp_token": "t1", "backup_code": "code"}

    def test_disable_url(self, monkeypatch):
        client, calls = _real_client(monkeypatch)
        client.disable_2fa("u1", "pw")
        assert calls[0][1] == "http://test.local/api/auth/2fa/disable"
        assert calls[0][2] == {"user_id": "u1", "password": "pw"}

    def test_backup_codes_url(self, monkeypatch):
        client, calls = _real_client(monkeypatch)
        client.get_2fa_backup_codes("u1")
        assert calls[0][0] == "GET"
        assert calls[0][1] == "http://test.local/api/auth/2fa/backup-codes?user_id=u1"

    def test_current_user_url(self, monkeypatch):
        client, calls = _real_client(monkeypatch)
        client.get_current_user()
        assert calls[0][1] == "http://test.local/api/user"
