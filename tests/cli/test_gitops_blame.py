"""Unit tests for blame-aware GitOps (gitops blame + plan --blame)."""

import os
import subprocess
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from typer.testing import CliRunner

from cli.ipilot.commands.gitops import blame as blame_mod

SHA_A = "a" * 40
SHA_B = "b" * 40
ZERO = "0" * 40

PORCELAIN = (
    f"{SHA_A} 1 1 2\n"
    "author Alice\n"
    "author-mail <alice@example.test>\n"
    "author-time 1700000000\n"
    "committer Alice\n"
    "summary init\n"
    "\t- name: web\n"
    "\t  type: standard\n"
    f"{SHA_B} 3 3 1\n"
    "author Bob\n"
    "author-time not-a-number\n"
    "\t- name: db\n"
    f"{ZERO} 4 4 1\n"
    "author Alice\n"
    "author-time 0\n"
    "\t  memory: big\n"
)

CONFIG_YAML = """# ipilot config
spec:
  servers:
    - name: web
      type: standard
    - name: 'db'
      type: standard
  backups: []
"""


def make_repo(path, files, date=None):
    subprocess.run(["git", "init", "-q", str(path)], check=True)
    subprocess.run(
        ["git", "-C", str(path), "config", "user.email", "t@example.test"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(path), "config", "user.name", "Tester"], check=True
    )
    for name, content in files.items():
        (path / name).write_text(content, encoding="utf-8")
    subprocess.run(["git", "-C", str(path), "add", "."], check=True)
    env = os.environ.copy()
    env.update(
        GIT_AUTHOR_NAME="Tester",
        GIT_AUTHOR_EMAIL="t@example.test",
        GIT_COMMITTER_NAME="Tester",
        GIT_COMMITTER_EMAIL="t@example.test",
    )
    if date is not None:
        env.update(GIT_AUTHOR_DATE=date, GIT_COMMITTER_DATE=date)
    subprocess.run(
        ["git", "-C", str(path), "-c", "commit.gpgsign=false", "commit", "-qm", "init"],
        check=True,
        env=env,
    )
    return path


@pytest.fixture
def client():
    return MagicMock()


@pytest.fixture
def runner(client, monkeypatch, tmp_path):
    from cli.ipilot.commands import gitops

    monkeypatch.setattr(gitops, "_get_client", lambda ctx: client)
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


def test_parse_blame_porcelain():
    blame = blame_mod.parse_blame_porcelain(PORCELAIN)
    assert blame[1] == blame_mod.BlameLine(
        commit=SHA_A, author="Alice", author_time=1700000000
    )
    assert blame[2].commit == SHA_A
    assert blame[3].author == "Bob"
    assert blame[3].author_time == 0
    assert blame[4].commit == ZERO


def test_parse_blame_missing_author_defaults_unknown():
    out = f"{SHA_A} 1 1 1\n" "\t- name: web\n"
    blame = blame_mod.parse_blame_porcelain(out)
    assert blame[1].author == "unknown"


def test_resource_spans_finds_servers():
    spans = blame_mod.resource_spans(CONFIG_YAML)
    assert spans == [("web", 4, 5), ("db", 6, 7)]


def test_resource_spans_end_of_file_and_unindented_items():
    assert blame_mod.resource_spans(
        "spec:\n  servers:\n    - name: web\n      type: x\n"
    ) == [("web", 3, 4)]
    text = "spec:\n  servers:\n  - name: web # comment\n    type: x\n  - type: y\n    name: db\n  backups: []\n  servers:\n  - name: ignored\n"
    assert blame_mod.resource_spans(text) == [("web", 3, 4), ("db", 5, 6)]


def test_resource_spans_ignores_nested_items_and_unnamed_servers():
    text = "spec:\n  servers:\n    - type: x\n      name: 'web # prod' # comment\n      disks:\n        - name: nested\n    - type: y\n    - name: db\n"
    assert blame_mod.resource_spans(text) == [("web # prod", 3, 6), ("db", 8, 8)]


def test_resource_spans_no_servers():
    assert blame_mod.resource_spans("spec:\n  backups: []\n") == []
    assert blame_mod.resource_spans("") == []


def test_resource_spans_inline_empty_servers():
    assert blame_mod.resource_spans("spec:\n  servers: []\n  backups: []\n") == []


def test_annotate_marks_uncommitted_and_many_hands():
    now = datetime(2024, 6, 1, tzinfo=timezone.utc)
    blame = {
        1: blame_mod.BlameLine(commit=SHA_A, author="Alice", author_time=1700000000),
        2: blame_mod.BlameLine(commit=ZERO, author="Zed", author_time=0),
        3: blame_mod.BlameLine(commit=SHA_B, author="Bob", author_time=1700000001),
        4: blame_mod.BlameLine(commit=SHA_A, author="Cara", author_time=1700000002),
        5: blame_mod.BlameLine(commit=SHA_A, author="Dan", author_time=1700000003),
    }
    (item,) = blame_mod.annotate([("web", 1, 5)], blame, stale_days=180, now=now)
    assert item.last_author == "Zed"
    assert item.last_changed == "uncommitted"
    assert item.last_commit == ZERO[:7]
    assert item.authors == ["Alice", "Bob", "Cara", "Dan", "Zed"]
    assert item.risk == ["uncommitted", "many-hands"]


def test_annotate_marks_stale():
    now = datetime(2024, 6, 1, tzinfo=timezone.utc)
    blame = {
        1: blame_mod.BlameLine(commit=SHA_A, author="Alice", author_time=1000000000),
    }
    (item,) = blame_mod.annotate([("web", 1, 1)], blame, stale_days=180, now=now)
    assert item.last_author == "Alice"
    assert item.last_commit == SHA_A[:7]
    assert item.last_changed == "2001-09-09"
    assert item.risk == ["stale"]


def test_annotate_fresh_has_no_risk():
    now = datetime(2024, 6, 1, tzinfo=timezone.utc)
    fresh = int(now.timestamp()) - 10
    blame = {
        1: blame_mod.BlameLine(commit=SHA_A, author="Alice", author_time=fresh),
    }
    (item,) = blame_mod.annotate([("web", 1, 1)], blame, stale_days=180, now=now)
    assert item.risk == []
    assert item.authors == ["Alice"]


def test_annotate_unknown_without_blame_lines():
    (item,) = blame_mod.annotate([("web", 1, 2)], {})
    assert item.last_author == "unknown"
    assert item.last_commit == "-"
    assert item.last_changed == "-"
    assert item.risk == ["unknown"]


def test_run_git_blame_success(tmp_path):
    make_repo(tmp_path, {"plan.yaml": CONFIG_YAML})
    out = blame_mod.run_git_blame(str(tmp_path / "plan.yaml"))
    assert "- name: web" in out


def test_run_git_blame_not_a_repo(tmp_path):
    target = tmp_path / "plan.yaml"
    target.write_text(CONFIG_YAML, encoding="utf-8")
    with pytest.raises(blame_mod.BlameError):
        blame_mod.run_git_blame(str(target))


def test_run_git_blame_no_git_binary(monkeypatch, tmp_path):
    def boom(*args, **kwargs):
        raise OSError("no git")

    monkeypatch.setattr(subprocess, "run", boom)
    with pytest.raises(blame_mod.BlameError, match="git not available"):
        blame_mod.run_git_blame(str(tmp_path / "plan.yaml"))


def test_run_git_blame_timeout(monkeypatch, tmp_path):
    def timeout(*args, **kwargs):
        assert kwargs["timeout"] > 0
        raise subprocess.TimeoutExpired("git", kwargs["timeout"])

    monkeypatch.setattr(subprocess, "run", timeout)
    with pytest.raises(blame_mod.BlameError, match="timed out") as error:
        blame_mod.run_git_blame(str(tmp_path / "plan.yaml"))
    assert isinstance(error.value.__cause__, subprocess.TimeoutExpired)


def test_run_git_blame_empty_stderr(monkeypatch, tmp_path):
    completed = subprocess.CompletedProcess(
        args=["git"], returncode=1, stdout="", stderr=""
    )
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: completed)
    with pytest.raises(blame_mod.BlameError, match="git blame failed"):
        blame_mod.run_git_blame(str(tmp_path / "plan.yaml"))


def test_blame_file_without_servers(tmp_path):
    target = tmp_path / "plan.yaml"
    target.write_text("spec:\n  backups: []\n", encoding="utf-8")
    assert blame_mod.blame_file(str(target)) == []


def test_blame_file_returns_annotations(tmp_path):
    make_repo(tmp_path, {"plan.yaml": CONFIG_YAML})
    items = blame_mod.blame_file(str(tmp_path / "plan.yaml"))
    assert [item.name for item in items] == ["web", "db"]
    assert all(item.last_author == "Tester" for item in items)


def test_blame_command_reports_authors(client, invoke, tmp_path):
    make_repo(tmp_path, {"plan.yaml": CONFIG_YAML})
    result = invoke(["gitops", "blame", "--file", str(tmp_path / "plan.yaml")])
    assert result.exit_code == 0
    assert "web" in result.output
    assert "Tester" in result.output


def test_blame_command_stale_flag(client, invoke, tmp_path):
    make_repo(tmp_path, {"plan.yaml": CONFIG_YAML}, date="2001-01-01T00:00:00+0000")
    result = invoke(
        [
            "gitops",
            "blame",
            "--file",
            str(tmp_path / "plan.yaml"),
            "--stale-days",
            "30",
        ]
    )
    assert result.exit_code == 0
    assert "stale" in result.output


def test_blame_command_missing_file(client, invoke, tmp_path):
    result = invoke(["gitops", "blame", "--file", str(tmp_path / "nope.yaml")])
    assert result.exit_code == 1


def test_blame_command_no_servers(client, invoke, tmp_path):
    target = tmp_path / "plan.yaml"
    target.write_text("spec:\n  backups: []\n", encoding="utf-8")
    result = invoke(["gitops", "blame", "--file", str(target)])
    assert result.exit_code == 0
    assert "No servers found" in result.output


def test_blame_command_not_a_repo(client, invoke, tmp_path):
    target = tmp_path / "plan.yaml"
    target.write_text(CONFIG_YAML, encoding="utf-8")
    result = invoke(["gitops", "blame", "--file", str(target)])
    assert result.exit_code == 1


def test_plan_blame_annotates_changes(client, invoke, tmp_path):
    make_repo(tmp_path, {"plan.yaml": CONFIG_YAML})
    client.list_servers.return_value = [
        {"name": "web", "type": "standard"},
        {"name": "ghost"},
    ]
    result = invoke(
        ["gitops", "plan", "--file", str(tmp_path / "plan.yaml"), "--blame"]
    )
    assert result.exit_code == 0
    assert "Tester" in result.output
    assert "unknown" in result.output


def test_plan_blame_fails_outside_repo(client, invoke, tmp_path):
    target = tmp_path / "plan.yaml"
    target.write_text(CONFIG_YAML, encoding="utf-8")
    client.list_servers.return_value = [{"name": "web", "type": "standard"}]
    result = invoke(["gitops", "plan", "--file", str(target), "--blame"])
    assert result.exit_code == 1


def test_plan_blame_fallback_when_no_spans(client, invoke, tmp_path):
    target = tmp_path / "plan.yaml"
    target.write_text("spec:\n  servers: []\n", encoding="utf-8")
    client.list_servers.return_value = [{"name": "removed"}]
    result = invoke(["gitops", "plan", "--file", str(target), "--blame"])
    assert result.exit_code == 0
    assert "removed" in result.output
    assert "unknown" in result.output
