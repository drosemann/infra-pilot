"""Unit tests for the orgs command group."""

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

    module = importlib.import_module("cli.ipilot.commands.orgs")
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


class TestListMembers:
    def test_list(self, client, invoke):
        client.list_organizations.return_value = [{"id": "o1", "name": "acme"}]
        result = invoke(["orgs", "list"])
        assert result.exit_code == 0
        client.list_organizations.assert_called_once()

    def test_members(self, client, invoke):
        client.list_organization_members.return_value = [{"user_id": "u1"}]
        result = invoke(["orgs", "members", "o1"])
        assert result.exit_code == 0
        client.list_organization_members.assert_called_once_with("o1")


class TestCreate:
    def test_create_with_slug(self, client, invoke):
        client.create_organization.return_value = {"id": "o1"}
        result = invoke(["orgs", "create", "acme", "--slug", "acme-inc"])
        assert result.exit_code == 0
        kwargs = client.create_organization.call_args.kwargs
        assert kwargs["name"] == "acme"
        assert kwargs["slug"] == "acme-inc"

    def test_create_defaults_slug_to_name(self, client, invoke):
        client.create_organization.return_value = {"id": "o1"}
        result = invoke(["orgs", "create", "acme"])
        assert result.exit_code == 0
        kwargs = client.create_organization.call_args.kwargs
        assert kwargs["slug"] == "acme"


class TestInvite:
    def test_invite_default_role(self, client, invoke):
        client.invite_organization_member.return_value = {"invited": True}
        result = invoke(["orgs", "invite", "o1", "ops@example.com"])
        assert result.exit_code == 0
        client.invite_organization_member.assert_called_once_with(
            "o1", "ops@example.com", role="member"
        )

    def test_invite_admin(self, client, invoke):
        client.invite_organization_member.return_value = {"invited": True}
        result = invoke(["orgs", "invite", "o1", "ops@example.com", "--role", "admin"])
        assert result.exit_code == 0
        assert client.invite_organization_member.call_args.kwargs["role"] == "admin"

    def test_invite_invalid_role(self, client, invoke):
        result = invoke(["orgs", "invite", "o1", "ops@example.com", "--role", "god"])
        assert result.exit_code == 2
        assert "unsupported role" in result.output
        client.invite_organization_member.assert_not_called()


class TestRemoveSetRole:
    def test_remove(self, client, invoke):
        client.remove_organization_member.return_value = {"removed": True}
        result = invoke(["orgs", "remove", "o1", "u1"])
        assert result.exit_code == 0
        client.remove_organization_member.assert_called_once_with("o1", "u1")

    def test_set_role(self, client, invoke):
        client.set_organization_member_role.return_value = {"role": "owner"}
        result = invoke(["orgs", "roles", "o1", "u1", "--set", "owner"])
        assert result.exit_code == 0
        client.set_organization_member_role.assert_called_once_with("o1", "u1", "owner")

    def test_set_role_invalid(self, client, invoke):
        result = invoke(["orgs", "roles", "o1", "u1", "--set", "god"])
        assert result.exit_code == 2
        client.set_organization_member_role.assert_not_called()


class TestOrgsClientUrls:
    def test_list_url(self, monkeypatch):
        client, calls = _real_client(monkeypatch)
        client.list_organizations()
        assert calls[0][0] == "GET"
        assert calls[0][1] == "http://test.local/api/organizations"

    def test_create_url_and_body(self, monkeypatch):
        client, calls = _real_client(monkeypatch)
        client.create_organization("acme", "acme-inc")
        assert calls[0][0] == "POST"
        assert calls[0][1] == "http://test.local/api/organizations"
        assert calls[0][2] == {"name": "acme", "slug": "acme-inc"}

    def test_members_url(self, monkeypatch):
        client, calls = _real_client(monkeypatch)
        client.list_organization_members("o1")
        assert calls[0][0] == "GET"
        assert calls[0][1] == "http://test.local/api/organizations/o1/members"

    def test_invite_url_and_body(self, monkeypatch):
        client, calls = _real_client(monkeypatch)
        client.invite_organization_member("o1", "ops@example.com", role="admin")
        assert calls[0][0] == "POST"
        assert calls[0][1] == "http://test.local/api/organizations/o1/members"
        assert calls[0][2] == {"email": "ops@example.com", "role": "admin"}

    def test_remove_url(self, monkeypatch):
        client, calls = _real_client(monkeypatch)
        client.remove_organization_member("o1", "u1")
        assert calls[0][0] == "DELETE"
        assert calls[0][1] == "http://test.local/api/organizations/o1/members/u1"

    def test_set_role_url(self, monkeypatch):
        client, calls = _real_client(monkeypatch)
        client.set_organization_member_role("o1", "u1", "owner")
        assert calls[0][0] == "PATCH"
        assert calls[0][1] == "http://test.local/api/organizations/o1/members/u1"
        assert calls[0][2] == {"role": "owner"}
