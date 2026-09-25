"""Smoke tests for the backup/restore helper scripts.

Exercises argument parsing and backup boundaries with isolated tool stubs;
no running Docker daemon, cloud credentials, or encryption keys are needed.
"""

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
BACKUP = ROOT / "scripts" / "db-backup.sh"
RESTORE = ROOT / "scripts" / "db-restore.sh"


BASH = shutil.which("bash")


def run(script: Path, *args: str, **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(
        [BASH, str(script), *args],
        capture_output=True,
        text=True,
        timeout=30,
        **kwargs,
    )


class TestDbBackupHelp:
    def test_help_lists_offsite_options(self):
        proc = run(BACKUP, "--help")
        assert proc.returncode == 0
        for flag in ("--s3", "--encrypt-to", "--no-plaintext", "--keep"):
            assert flag in proc.stdout

    def test_unknown_flag_fails(self):
        proc = run(BACKUP, "--nope")
        assert proc.returncode != 0

    def test_missing_cli_dependency_fails_fast(self, tmp_path):
        tool_dir = tmp_path / "bin"
        tool_dir.mkdir()
        (tool_dir / "dirname").symlink_to(shutil.which("dirname"))
        marker = tmp_path / "docker-was-run"
        docker = tool_dir / "docker"
        docker.write_text(f'#!{BASH}\n: > "{marker}"\nexit 99\n')
        docker.chmod(0o755)
        output_dir = tmp_path / "backups"
        proc = run(
            BACKUP,
            "--s3",
            "s3://bucket/prefix",
            "--out",
            str(output_dir),
            env={"PATH": str(tool_dir), "HOME": str(tmp_path)},
        )
        assert proc.returncode == 1
        assert "aws CLI not found in PATH (required for --s3)" in proc.stderr
        assert not proc.stdout
        assert not marker.exists()
        assert not output_dir.exists()


class TestDbRestoreHelp:
    def test_help_mentions_gpg_and_volumes(self):
        proc = run(RESTORE, "--help")
        assert proc.returncode == 0
        assert ".gpg" in proc.stdout
        assert "redis" in proc.stdout.lower()

    def test_missing_file_fails(self):
        proc = run(RESTORE, "/tmp/does-not-exist.dump", "--yes")
        assert proc.returncode != 0

    def test_unknown_flag_fails(self):
        proc = run(RESTORE, "--nope")
        assert proc.returncode != 0


@pytest.fixture
def backup_tools(tmp_path):
    """Use only explicitly supplied tools, with no inherited user configuration."""
    tool_dir = tmp_path / "bin"
    tool_dir.mkdir()
    for tool in (
        "dirname",
        "grep",
        "mkdir",
        "date",
        "du",
        "cut",
        "ls",
        "tail",
        "rm",
        "basename",
    ):
        (tool_dir / tool).symlink_to(shutil.which(tool))
    env = {
        "PATH": str(tool_dir),
        "HOME": str(tmp_path),
        "TOOL_LOG": str(tmp_path / "tools.log"),
    }

    def stub(name, body):
        path = tool_dir / name
        path.write_text(f"#!{BASH}\nset -eu\n" + body)
        path.chmod(0o755)

    stub(
        "docker",
        r"""printf 'docker %s\n' "$*" >> "$TOOL_LOG"
case "$*" in
  'compose ls') echo infra-pilot ;;
  *pg_dump*) echo dump ;;
  'volume inspect infra-pilot_grafana_data') exit "${VOLUME_STATUS:-0}" ;;
  'run '*) ;;
  *) exit 99 ;;
esac
""",
    )
    stub(
        "gpg",
        r"""printf 'gpg %s\n' "$*" >> "$TOOL_LOG"
while [[ "$1" != --output ]]; do shift; done
printf encrypted > "$2"
""",
    )
    stub(
        "aws",
        r"""printf 'aws %s\n' "$*" >> "$TOOL_LOG"
[[ "$1 $2" == 's3 cp' && -f "$3" ]]
""",
    )
    return env


@pytest.mark.parametrize(
    "encrypted,no_plaintext", [(False, False), (True, False), (True, True)]
)
def test_upload_selects_only_requested_artifact(
    tmp_path, backup_tools, encrypted, no_plaintext
):
    args = [
        "--out",
        str(tmp_path / "backups"),
        "--skip-redis",
        "--skip-grafana",
        "--s3",
        "s3://bucket/prefix",
    ]
    if encrypted:
        args += ["--encrypt-to", "test-key"]
    if no_plaintext:
        args += ["--no-plaintext"]
    proc = run(BACKUP, *args, env=backup_tools)
    assert proc.returncode == 0, proc.stderr
    uploads = [
        line.split()[3]
        for line in Path(backup_tools["TOOL_LOG"]).read_text().splitlines()
        if line.startswith("aws ")
    ]
    assert len(uploads) == 1
    artifact = Path(uploads[0])
    assert artifact.suffix == (".gpg" if encrypted else ".dump")
    assert artifact.read_text() == ("encrypted" if encrypted else "dump\n")
    assert bool(list((tmp_path / "backups").glob("*.dump"))) == (not no_plaintext)


def test_missing_grafana_volume_does_not_start_archive(tmp_path, backup_tools):
    backup_tools["VOLUME_STATUS"] = "1"
    proc = run(
        BACKUP, "--out", str(tmp_path / "backups"), "--skip-redis", env=backup_tools
    )
    assert proc.returncode == 0, proc.stderr
    log = Path(backup_tools["TOOL_LOG"]).read_text()
    assert "docker volume inspect infra-pilot_grafana_data" in log
    assert "docker run" not in log
    assert "Grafana volume not found" in proc.stdout


@pytest.mark.parametrize("relative", [True, False])
def test_grafana_mount_uses_absolute_output_path(tmp_path, backup_tools, relative):
    output_dir = tmp_path / "backup files"
    proc = run(
        BACKUP,
        "--out",
        "backup files" if relative else str(output_dir),
        "--skip-redis",
        env=backup_tools,
        cwd=tmp_path,
    )
    assert proc.returncode == 0, proc.stderr
    log = Path(backup_tools["TOOL_LOG"]).read_text()
    assert log.index("docker volume inspect") < log.index("docker run")
    assert f"-v {output_dir}:/out" in log
