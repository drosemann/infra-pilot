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
    """Run a helper script with captured text output and a 30-second timeout."""
    return subprocess.run(
        [BASH, str(script), *args],
        capture_output=True,
        text=True,
        timeout=30,
        **kwargs,
    )


class TestDbBackupHelp:
    def test_help_lists_offsite_options(self):
        """Verify backup help lists S3, encryption, and retention options."""
        proc = run(BACKUP, "--help")
        assert proc.returncode == 0
        for flag in (
            "--s3",
            "--encrypt-to",
            "--no-plaintext",
            "--keep",
            "--keep-daily",
            "--keep-weekly",
            "--keep-monthly",
        ):
            assert flag in proc.stdout

    def test_help_lists_selfhosted_options(self):
        """Verify backup help lists Borg and rclone destinations."""
        proc = run(BACKUP, "--help")
        assert proc.returncode == 0
        for flag in ("--borg-repo", "--rclone-remote"):
            assert flag in proc.stdout
        assert "borgbackup" in proc.stdout.lower() or "borg" in proc.stdout.lower()
        assert "rclone" in proc.stdout.lower()

    def test_unknown_flag_fails(self):
        """Verify an unsupported option causes the script to fail."""
        proc = run(BACKUP, "--nope")
        assert proc.returncode != 0

    def test_missing_cli_dependency_fails_fast(self, tmp_path):
        """Verify missing AWS CLI fails before Docker runs or output is created."""
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

    def test_missing_borg_fails_fast(self, tmp_path):
        """Verify requesting Borg without its CLI reports the missing dependency."""
        tool_dir = tmp_path / "bin"
        tool_dir.mkdir()
        (tool_dir / "dirname").symlink_to(shutil.which("dirname"))
        proc = run(
            BACKUP,
            "--borg-repo",
            "/mnt/backup/borg",
            "--out",
            str(tmp_path / "backups"),
            env={"PATH": str(tool_dir), "HOME": str(tmp_path)},
        )
        assert proc.returncode == 1
        assert "borg not found in PATH (required for --borg-repo)" in proc.stderr

    def test_missing_rclone_fails_fast(self, tmp_path):
        """Verify requesting rclone without its CLI reports the missing dependency."""
        tool_dir = tmp_path / "bin"
        tool_dir.mkdir()
        (tool_dir / "dirname").symlink_to(shutil.which("dirname"))
        proc = run(
            BACKUP,
            "--rclone-remote",
            "myremote:infra-pilot",
            "--out",
            str(tmp_path / "backups"),
            env={"PATH": str(tool_dir), "HOME": str(tmp_path)},
        )
        assert proc.returncode == 1
        assert "rclone not found in PATH (required for --rclone-remote)" in proc.stderr


class TestDbRestoreHelp:
    def test_help_mentions_gpg_and_volumes(self):
        """Verify restore help describes encrypted files and Redis artifacts."""
        proc = run(RESTORE, "--help")
        assert proc.returncode == 0
        assert ".gpg" in proc.stdout
        assert "redis" in proc.stdout.lower()

    def test_missing_file_fails(self):
        """Verify restoring a nonexistent dump fails."""
        proc = run(RESTORE, "/tmp/does-not-exist.dump", "--yes")
        assert proc.returncode != 0

    def test_unknown_flag_fails(self):
        """Verify an unsupported option causes the script to fail."""
        proc = run(RESTORE, "--nope")
        assert proc.returncode != 0

    def test_dry_run_rejects_non_dump(self, tmp_path):
        """Verify dry-run fails for files without a pg_dump header."""
        bad = tmp_path / "bad.dump"
        bad.write_text("not a dump")
        proc = run(RESTORE, str(bad), "--dry-run")
        assert proc.returncode != 0

    def test_dry_run_accepts_dump_header_without_docker(self, tmp_path):
        """Verify dry-run passes on header check alone (no daemon needed)."""
        good = tmp_path / "good.dump"
        good.write_bytes(b"PGDMPfake-toc")
        proc = run(RESTORE, str(good), "--dry-run")
        assert proc.returncode == 0
        assert "Dry-run OK" in proc.stdout


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
        "sha256sum",
    ):
        (tool_dir / tool).symlink_to(shutil.which(tool))
    env = {
        "PATH": str(tool_dir),
        "HOME": str(tmp_path),
        "TOOL_LOG": str(tmp_path / "tools.log"),
    }

    def stub(name, body):
        """Write an executable Bash stub with the supplied name and body."""
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
    """Verify S3 receives the selected artifact and plaintext retention is honored."""
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
    """Verify an absent Grafana volume skips archiving without failing backup."""
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
    """Verify Grafana archiving resolves relative and absolute output paths."""
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


@pytest.fixture
def selfhosted_tools(tmp_path, backup_tools):
    """Extend backup_tools with borg and rclone stubs for self-hosted tests."""
    tool_dir = Path(backup_tools["PATH"])
    env = dict(backup_tools)

    def stub(name, body):
        """Write an executable Bash stub with the supplied name and body."""
        path = tool_dir / name
        path.write_text(f"#!{BASH}\nset -eu\n" + body)
        path.chmod(0o755)

    stub(
        "borg",
        r"""printf 'borg %s\n' "$*" >> "$TOOL_LOG"
exit 0
""",
    )
    stub(
        "rclone",
        r"""printf 'rclone %s\n' "$*" >> "$TOOL_LOG"
[[ "$1" == "copyto" && -f "$2" ]]
""",
    )
    return env


def test_borg_and_rclone_called_for_selfhosted_offsite(tmp_path, selfhosted_tools):
    """Verify backup invokes Borg create/prune and rclone for offsite storage."""
    proc = run(
        BACKUP,
        "--out",
        str(tmp_path / "backups"),
        "--skip-redis",
        "--skip-grafana",
        "--borg-repo",
        "/mnt/backup/borg",
        "--rclone-remote",
        "myremote:infra-pilot",
        env=selfhosted_tools,
    )
    assert proc.returncode == 0, proc.stderr
    log = Path(selfhosted_tools["TOOL_LOG"]).read_text()
    assert "borg create" in log
    assert "borg prune" in log
    assert "infra-pilot-" in log
    assert "rclone copyto" in log
    assert "myremote:infra-pilot" in log
    assert "Borg archive created" in proc.stdout


def test_borg_repo_env_fallback(tmp_path, selfhosted_tools):
    """Verify BACKUP_BORG_REPO enables Borg archiving without a CLI option."""
    env = dict(selfhosted_tools)
    env["BACKUP_BORG_REPO"] = "/mnt/backup/borg"
    proc = run(
        BACKUP,
        "--out",
        str(tmp_path / "backups"),
        "--skip-redis",
        "--skip-grafana",
        env=env,
    )
    assert proc.returncode == 0, proc.stderr
    log = Path(env["TOOL_LOG"]).read_text()
    assert "borg create" in log


def test_writes_sha256_sidecar_and_success_prom(tmp_path, backup_tools):
    """Verify backup writes a sha256 sidecar and last_success.prom metric."""
    out = tmp_path / "backups"
    proc = run(
        BACKUP, "--out", str(out), "--skip-redis", "--skip-grafana", env=backup_tools
    )
    assert proc.returncode == 0, proc.stderr
    dumps = list(out.glob("infra-pilot_*.dump"))
    assert len(dumps) == 1
    sidecar = dumps[0].parent / (dumps[0].name + ".sha256")
    assert sidecar.exists()
    check = subprocess.run(
        [shutil.which("sha256sum"), "-c", sidecar.name],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=out,
    )
    assert check.returncode == 0, check.stderr
    prom = out / "last_success.prom"
    assert prom.exists()
    assert "backup_last_success_timestamp" in prom.read_text()


def test_prune_removes_checksum_sidecar(tmp_path, backup_tools):
    """Verify retention pruning also drops the detached sha256 sidecar."""
    out = tmp_path / "backups"
    out.mkdir()
    old = out / "infra-pilot_20000101_000000.dump"
    old.write_text("old")
    (out / (old.name + ".sha256")).write_text("old-sidecar")
    proc = run(
        BACKUP,
        "--out",
        str(out),
        "--skip-redis",
        "--skip-grafana",
        "--keep",
        "1",
        env=backup_tools,
    )
    assert proc.returncode == 0, proc.stderr
    assert not old.exists()
    assert not (out / (old.name + ".sha256")).exists()
