"""Tests for the safe update flow (scripts/update.sh).

Uses isolated tool stubs; no Docker daemon, git remote, or real backup
is needed. The script honours IPILOT_BACKUP_SCRIPT / IPILOT_HEALTH_SCRIPT
overrides so tests can observe calls without touching real data.
"""

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
UPDATE = ROOT / "scripts" / "update.sh"

BASH = shutil.which("bash")


def run(*args: str, env=None, cwd=None) -> subprocess.CompletedProcess:
    """Run update.sh with the supplied options and capture its output and status."""
    return subprocess.run(
        [BASH, str(UPDATE), *args],
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
        cwd=cwd,
    )


def make_tools(tmp_path: Path) -> dict:
    """Create logging tool stubs in tmp_path and return an isolated environment."""
    tool_dir = tmp_path / "bin"
    tool_dir.mkdir()
    for tool in ("dirname", "grep", "readlink", "basename", "bash", "sh", "sed"):
        real = shutil.which(tool)
        if real:
            (tool_dir / tool).symlink_to(real)
    log = tmp_path / "tools.log"

    def stub(name: str, body: str):
        """Write an executable Bash stub with the given name and script body."""
        path = tool_dir / name
        path.write_text(f"#!{BASH}\nset -eu\n" + body)
        path.chmod(0o755)

    stub(
        "docker",
        r"""printf 'docker %s\n' "$*" >> "$TOOL_LOG"
case "$*" in
  'compose -f '*' config') exit 0 ;;
  'compose -f '*' config --environment')
    printf 'COMPOSE_PROJECT_NAME=%s\n' "${TEST_PROJECT_NAME:-infra-pilot}"
    exit 0 ;;
  'volume inspect '*)
    [[ "${3}" != "${TEST_MISSING_VOLUME:-}" ]]
    exit $? ;;
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
        """Check that help describes update options, volume retention, and restore."""
        proc = run("--help")
        assert proc.returncode == 0
        assert "--check-only" in proc.stdout
        assert "--skip-backup" in proc.stdout
        assert "volumes" in proc.stdout.lower()
        assert "db-restore.sh" in proc.stdout

    def test_unknown_flag_fails(self):
        """Verify that an unsupported option returns a nonzero exit status."""
        proc = run("--nope")
        assert proc.returncode != 0

    def test_refuses_volume_deletion_flags(self, tmp_path):
        """Verify that volume deletion flags fail with a data retention warning."""
        env = make_tools(tmp_path)
        for flag in ("--volumes", "-v"):
            proc = run(flag, env=env)
            assert proc.returncode == 2
            assert "never delete volumes" in proc.stderr

    def test_refuses_volumes_in_compose_args(self, tmp_path):
        """Reject volume deletion requested through extra Compose arguments."""
        env = make_tools(tmp_path)
        proc = run("--compose-args", "down -v", "--yes", env=env)
        assert proc.returncode == 2
        assert "volume deletion" in proc.stderr


class TestUpdateCheckOnly:
    def test_check_only_makes_no_changes(self, tmp_path):
        """Check that validation invokes Git, skips backup, and reports success."""
        env = make_tools(tmp_path)
        proc = run("--check-only", env=env)
        assert proc.returncode == 0, proc.stderr
        log = Path(env["TOOL_LOG"]).read_text()
        assert any(line.startswith("git ") for line in log.splitlines())
        assert "backup" not in log
        assert "Update check passed" in proc.stdout

    def test_check_only_skips_git_when_requested(self, tmp_path):
        """Verify that --skip-git suppresses Git calls during validation."""
        env = make_tools(tmp_path)
        proc = run("--check-only", "--skip-git", env=env)
        assert proc.returncode == 0, proc.stderr
        log = Path(env["TOOL_LOG"]).read_text()
        assert not any(line.startswith("git ") for line in log.splitlines())


class TestUpdateFullFlow:
    def test_full_flow_backups_pulls_rebuilds_and_verifies(self, tmp_path):
        """Check that an update calls backup, Git, Compose, and health tools."""
        env = make_tools(tmp_path)
        proc = run("--yes", env=env)
        assert proc.returncode == 0, proc.stderr
        log = Path(env["TOOL_LOG"]).read_text()
        assert "backup" in log
        assert "git -C" in log or "git pull" in log or "pull --ff-only" in log
        assert "docker compose" in log
        assert "health --strict" in log
        assert "--dry-run" not in log
        assert "All checked named volumes are present" in proc.stdout

    def test_health_failure_stops_update_and_preserves_output(self, tmp_path):
        env = make_tools(tmp_path)
        Path(env["IPILOT_HEALTH_SCRIPT"]).write_text(
            f"#!{BASH}\necho 'unhealthy service'\necho 'health error' >&2\nexit 1\n"
        )
        proc = run("--yes", env=env)
        assert proc.returncode == 1
        assert "unhealthy service" in proc.stdout
        assert "health error" in proc.stderr
        assert "Update failed: health check failed" in proc.stderr
        assert "Update complete" not in proc.stdout
        assert "volume inspect" not in Path(env["TOOL_LOG"]).read_text()

    @pytest.mark.parametrize("project", ["custom-stack", "123"])
    def test_volumes_use_resolved_compose_project(self, tmp_path, project):
        env = make_tools(tmp_path)
        env["TEST_PROJECT_NAME"] = project
        proc = run("--yes", env=env)
        assert proc.returncode == 0, proc.stderr
        log = Path(env["TOOL_LOG"]).read_text()
        for volume in ("postgres_data", "redis_data"):
            assert f"docker volume inspect {project}_{volume}" in log
            assert f"Volume present: {project}_{volume}" in proc.stdout
        assert "volume inspect infra-pilot_" not in log
        assert "All checked named volumes are present" in proc.stdout

    @pytest.mark.parametrize("missing_volume", ["postgres_data", "redis_data"])
    def test_missing_volume_does_not_report_all_present(self, tmp_path, missing_volume):
        env = make_tools(tmp_path)
        env["TEST_MISSING_VOLUME"] = f"infra-pilot_{missing_volume}"
        proc = run("--yes", env=env)
        assert proc.returncode == 0, proc.stderr
        log = Path(env["TOOL_LOG"]).read_text()
        for volume in ("postgres_data", "redis_data"):
            assert f"docker volume inspect infra-pilot_{volume}" in log
        assert f"Volume missing: infra-pilot_{missing_volume}" in proc.stdout
        assert "one or more checked volumes are missing" in proc.stdout
        assert "All checked named volumes are present" not in proc.stdout
        assert "All named volumes were kept" not in proc.stdout

    def test_skip_backup_avoids_backup_call(self, tmp_path):
        """Verify that --skip-backup bypasses the backup tool and warns the user."""
        env = make_tools(tmp_path)
        proc = run("--yes", "--skip-backup", env=env)
        assert proc.returncode == 0, proc.stderr
        log = Path(env["TOOL_LOG"]).read_text()
        assert "backup" not in log
        assert "Skipping pre-update backup" in proc.stdout

    def test_missing_docker_fails_fast(self, tmp_path):
        """Verify that missing Docker causes a clear preflight failure."""
        tool_dir = tmp_path / "bin"
        tool_dir.mkdir()
        (tool_dir / "dirname").symlink_to(shutil.which("dirname"))
        proc = run(
            "--check-only",
            env={"PATH": str(tool_dir), "HOME": str(tmp_path)},
        )
        assert proc.returncode == 1
        assert "docker not found in PATH" in proc.stderr
