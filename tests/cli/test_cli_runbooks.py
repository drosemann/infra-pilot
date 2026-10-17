"""Unit tests for the runbooks command group."""

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

    module = importlib.import_module("cli.ipilot.commands.runbooks")
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


@pytest.fixture
def runbook_file(tmp_path):
    path = tmp_path / "rb.yaml"
    path.write_text(
        "name: deploy-app\ndescription: deploy a app\nsteps:\n"
        "  - action: scale\n    app: web\n    count: 3\n"
    )
    return str(path)


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


class TestListShow:
    def test_list_wraps_dict(self, client, invoke):
        client.list_runbooks.return_value = {"runbooks": [{"id": 1, "name": "a"}]}
        result = invoke(["runbooks", "list"])
        assert result.exit_code == 0
        client.list_runbooks.assert_called_once()

    def test_list_passes_list_through(self, client, invoke):
        client.list_runbooks.return_value = [{"id": 1}]
        result = invoke(["runbooks", "list"])
        assert result.exit_code == 0

    def test_show_by_id(self, client, invoke):
        client.list_runbooks.return_value = [
            {"id": "r1", "name": "deploy-app", "steps": []}
        ]
        result = invoke(["runbooks", "show", "r1"])
        assert result.exit_code == 0
        assert "deploy-app" in result.output

    def test_show_by_name(self, client, invoke):
        client.list_runbooks.return_value = [
            {"id": "r1", "name": "deploy-app", "steps": []}
        ]
        result = invoke(["runbooks", "show", "deploy-app"])
        assert result.exit_code == 0
        assert "r1" in result.output

    def test_show_missing(self, client, invoke):
        client.list_runbooks.return_value = []
        result = invoke(["runbooks", "show", "ghost"])
        assert result.exit_code == 0
        assert "not found" in result.output


class TestCreate:
    def test_create_from_yaml(self, client, invoke, runbook_file):
        client.create_runbook.return_value = {"id": "r1", "name": "deploy-app"}
        result = invoke(["runbooks", "create", "--file", runbook_file])
        assert result.exit_code == 0
        client.create_runbook.assert_called_once_with(
            name="deploy-app",
            description="deploy a app",
            steps=[{"action": "scale", "app": "web", "count": 3}],
        )

    def test_create_missing_file(self, client, invoke, tmp_path):
        result = invoke(["runbooks", "create", "--file", str(tmp_path / "nope.yaml")])
        assert result.exit_code == 1
        client.create_runbook.assert_not_called()

    def test_create_no_steps(self, client, invoke, tmp_path):
        path = tmp_path / "bad.yaml"
        path.write_text("name: empty\nsteps: []\n")
        result = invoke(["runbooks", "create", "--file", str(path)])
        assert result.exit_code == 2
        client.create_runbook.assert_not_called()

    def test_create_non_mapping(self, client, invoke, tmp_path):
        path = tmp_path / "list.yaml"
        path.write_text("- just\n- a\n- list\n")
        result = invoke(["runbooks", "create", "--file", str(path)])
        assert result.exit_code == 1


class TestEditDelete:
    def test_edit_name(self, client, invoke):
        client.update_runbook.return_value = {"id": "r1"}
        result = invoke(["runbooks", "edit", "r1", "--name", "new-name"])
        assert result.exit_code == 0
        kwargs = client.update_runbook.call_args.kwargs
        assert kwargs["name"] == "new-name"

    def test_edit_no_fields(self, client, invoke):
        result = invoke(["runbooks", "edit", "r1"])
        assert result.exit_code == 2
        client.update_runbook.assert_not_called()

    def test_delete(self, client, invoke):
        client.delete_runbook.return_value = {"success": True}
        result = invoke(["runbooks", "delete", "r1"])
        assert result.exit_code == 0
        client.delete_runbook.assert_called_once_with("r1")


class TestExecute:
    def test_execute(self, client, invoke):
        client.execute_runbook.return_value = {"status": "executed"}
        result = invoke(["runbooks", "execute", "r1"])
        assert result.exit_code == 0
        client.execute_runbook.assert_called_once_with("r1")

    def test_execute_dry_run(self, client, invoke):
        client.list_runbooks.return_value = [
            {"id": "r1", "name": "deploy", "steps": [{"action": "scale"}]}
        ]
        result = invoke(["runbooks", "execute", "r1", "--dry-run"])
        assert result.exit_code == 0
        # table view renders the steps list; the runbook name is omitted
        assert "scale" in result.output
        client.execute_runbook.assert_not_called()

    def test_execute_dry_run_missing(self, client, invoke):
        client.list_runbooks.return_value = []
        result = invoke(["runbooks", "execute", "ghost", "--dry-run"])
        assert "not found" in result.output

    def test_execute_wait_terminal(self, client, invoke):
        client.execute_runbook.return_value = {
            "execution_id": "e1",
            "status": "running",
        }
        client.get_runbook_execution.return_value = {"status": "executed"}
        result = invoke(["runbooks", "execute", "r1", "--wait", "--timeout", "1"])
        assert result.exit_code == 0
        assert client.get_runbook_execution.call_count == 1

    def test_execute_wait_error(self, client, invoke):
        client.execute_runbook.return_value = {"error": "not found"}
        result = invoke(["runbooks", "execute", "r1", "--wait"])
        assert result.exit_code == 0
        client.get_runbook_execution.assert_not_called()


class TestRunbooksClientUrls:
    def test_list_url(self, monkeypatch):
        client, calls = _real_client(monkeypatch)
        client.list_runbooks()
        assert calls[0][0] == "GET"
        assert calls[0][1] == "http://test.local/api/runbooks"

    def test_create_url_and_body(self, monkeypatch):
        client, calls = _real_client(monkeypatch)
        client.create_runbook("rb", "desc", [{"action": "x"}])
        assert calls[0][0] == "POST"
        assert calls[0][1] == "http://test.local/api/runbooks"
        assert calls[0][2]["name"] == "rb"
        assert calls[0][2]["steps"] == [{"action": "x"}]

    def test_update_url(self, monkeypatch):
        client, calls = _real_client(monkeypatch)
        client.update_runbook("r1", name="new")
        assert calls[0][0] == "PATCH"
        assert calls[0][1] == "http://test.local/api/runbooks/r1"
        assert calls[0][2] == {"name": "new"}

    def test_delete_url(self, monkeypatch):
        client, calls = _real_client(monkeypatch)
        client.delete_runbook("r1")
        assert calls[0][0] == "DELETE"
        assert calls[0][1] == "http://test.local/api/runbooks/r1"

    def test_execute_url(self, monkeypatch):
        client, calls = _real_client(monkeypatch)
        client.execute_runbook("r1")
        assert calls[0][0] == "POST"
        assert calls[0][1] == "http://test.local/api/runbooks/r1/execute"

    def test_execution_status_url(self, monkeypatch):
        client, calls = _real_client(monkeypatch)
        client.get_runbook_execution("e1")
        assert calls[0][1] == "http://test.local/api/runbooks/executions/e1"
