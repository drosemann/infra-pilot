"""Tests for the safe update flow (scripts/update.sh).

Uses isolated tool stubs; no Docker daemon, git remote, or real backup
is needed. The script honours IPILOT_BACKUP_SCRIPT / IPILOT_HEALTH_SCRIPT
overrides so tests can observe calls without touching real data.
"""

import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UPDATE = ROOT / "scripts" / "update.sh"

BASH = shutil.which("bash")


def run(*args: str, env=None, cwd=None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [BASH, str(UPDATE), *args],
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
        cwd=cwd,
    )


def make_tools(tmp_path: Path) -> dict:
    tool_dir = tmp_path / "bin"
    tool_dir.mkdir()
    for tool in ("dirname", "grep", "readlink", "basename", "bash", "sh"):
        real = shutil.which(tool)
        if real:
            (tool_dir / tool).symlink_to(real)
    log = tmp_path / "tools.log"

    def stub(name: str, body: str):
        path = tool_dir / name
        path.write_text(f"#!{BASH}\nset -eu\n" + body)
        path.chmod(0o755)

    stub(
        "docker",
        r"""printf 'docker %s\n' "$*" >> "$TOOL_LOG"
case "$*" in
  'compose -f '*' config') exit 0 ;;
  'volume inspect infra-pilot_postgres_data') exit 0 ;;
  'volume inspect infra-pilot_redis_data') exit 0 ;;
  'compose -f '*' up -d --build'*) exit 0 ;;
  'compose -f '*' up -d --build '*) exit 0 ;;
  *) exit 0 ;;
esac
""",
    )
    stub(
        "git",
        r"""printf 'git %s\n' "$*" >> "$TOOL_LOG"
exit 0
""",
    )
    backup_stub = tmp_path / "fake-backup.sh"
    backup_stub.write_text(f'#!{BASH}\nprintf \'backup %s\\n\' "$*" >> "{log}"\n')
    backup_stub.chmod(0o755)
    health_stub = tmp_path / "fake-health.sh"
    health_stub.write_text(f'#!{BASH}\nprintf \'health %s\\n\' "$*" >> "{log}"\n')
    health_stub.chmod(0o755)

    env = {
        "PATH": str(tool_dir),
        "HOME": str(tmp_path),
        "TOOL_LOG": str(log),
        "IPILOT_BACKUP_SCRIPT": str(backup_stub),
        "IPILOT_HEALTH_SCRIPT": str(health_stub),
    }
    return env


class TestUpdateHelp:
    def test_help_mentions_data_retention(self):
        proc = run("--help")
        assert proc.returncode == 0
        assert "--check-only" in proc.stdout
        assert "--skip-backup" in proc.stdout
        assert "volumes" in proc.stdout.lower()
        assert "db-restore.sh" in proc.stdout

    def test_unknown_flag_fails(self):
        proc = run("--nope")
        assert proc.returncode != 0

    def test_refuses_volume_deletion_flags(self, tmp_path):
        env = make_tools(tmp_path)
        for flag in ("--volumes", "-v"):
            proc = run(flag, env=env)
            assert proc.returncode == 2
            assert "never delete volumes" in proc.stderr

    def test_refuses_volumes_in_compose_args(self, tmp_path):
        env = make_tools(tmp_path)
        proc = run("--compose-args", "down -v", "--yes", env=env)
        assert proc.returncode == 2
        assert "volume deletion" in proc.stderr


class TestUpdateCheckOnly:
    def test_check_only_makes_no_changes(self, tmp_path):
        env = make_tools(tmp_path)
        proc = run("--check-only", env=env)
        assert proc.returncode == 0, proc.stderr
        log = Path(env["TOOL_LOG"]).read_text()
        assert "git" in log
        assert "backup" not in log
        assert "Update check passed" in proc.stdout

    def test_check_only_skips_git_when_requested(self, tmp_path):
        env = make_tools(tmp_path)
        proc = run("--check-only", "--skip-git", env=env)
        assert proc.returncode == 0, proc.stderr
        log = Path(env["TOOL_LOG"]).read_text()
        assert "git" not in log


class TestUpdateFullFlow:
    def test_full_flow_backups_pulls_rebuilds_and_verifies(self, tmp_path):
        env = make_tools(tmp_path)
        proc = run("--yes", env=env)
        assert proc.returncode == 0, proc.stderr
        log = Path(env["TOOL_LOG"]).read_text()
        assert "backup" in log
        assert "git -C" in log or "git pull" in log or "pull --ff-only" in log
        assert "docker compose" in log
        assert "health" in log
        assert "volumes were kept" in proc.stdout

    def test_skip_backup_avoids_backup_call(self, tmp_path):
        env = make_tools(tmp_path)
        proc = run("--yes", "--skip-backup", env=env)
        assert proc.returncode == 0, proc.stderr
        log = Path(env["TOOL_LOG"]).read_text()
        assert "backup" not in log
        assert "Skipping pre-update backup" in proc.stdout

    def test_missing_docker_fails_fast(self, tmp_path):
        tool_dir = tmp_path / "bin"
        tool_dir.mkdir()
        (tool_dir / "dirname").symlink_to(shutil.which("dirname"))
        proc = run(
            "--check-only",
            env={"PATH": str(tool_dir), "HOME": str(tmp_path)},
        )
        assert proc.returncode == 1
        assert "docker not found in PATH" in proc.stderr
