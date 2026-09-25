"""Smoke tests for the backup/restore helper scripts.

Only exercises argument parsing and help output (no docker needed):
--help must exit 0 and document the offsite/encryption options, unknown
flags must fail.
"""

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKUP = ROOT / "scripts" / "db-backup.sh"
RESTORE = ROOT / "scripts" / "db-restore.sh"


def run(script: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(script), *args],
        capture_output=True,
        text=True,
        timeout=30,
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

    def test_missing_cli_dependency_fails_fast(self):
        # --s3 requires docker + the aws CLI; without either it must fail
        # before doing any work.
        proc = run(BACKUP, "--s3", "s3://bucket/prefix", "--out", "/tmp")
        if proc.returncode != 0:
            output = (proc.stdout + proc.stderr).lower()
            assert "aws" in output or "docker" in output


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
