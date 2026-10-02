import builtins
import fnmatch
import os
import shutil
import subprocess

import typer

from ...client import ApiClient
from ...config import DEFAULT_API_URL, load_config
from ...output.formatters import print_output

app = typer.Typer(help="Backup management")


def _get_client(ctx: typer.Context) -> ApiClient:
    config = load_config(profile=ctx.obj.get("profile"))
    return ApiClient(config.get("api_url", DEFAULT_API_URL), config.get("token"))


def _backup_script() -> str:
    """Return the path to scripts/db-backup.sh (repo checkout).

    Walks up from this file (cli/ipilot/commands/infrastructure/)
    to the repo root. When ipilot is pip-installed without the
    checkout, the script may not exist – callers handle that.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.abspath(os.path.join(here, "..", "..", "..", ".."))
    return os.path.join(root, "scripts", "db-backup.sh")


def _build_local_backup_cmd(
    keep: int,
    out: str | None,
    s3_target: str | None,
    borg_repo: str | None,
    rclone_remote: str | None,
    skip_redis: bool,
    skip_grafana: bool,
    dry_run: bool,
) -> list[str]:
    """Build the scripts/db-backup.sh invocation (thin mapping)."""
    cmd = ["bash", _backup_script(), "--keep", str(keep)]
    if out:
        cmd += ["--out", out]
    if s3_target:
        cmd += ["--s3", s3_target]
    if borg_repo:
        cmd += ["--borg-repo", borg_repo]
    if rclone_remote:
        cmd += ["--rclone-remote", rclone_remote]
    if skip_redis:
        cmd.append("--skip-redis")
    if skip_grafana:
        cmd.append("--skip-grafana")
    if dry_run:
        cmd.append("--dry-run")
    return cmd


@app.command()
def list(
    ctx: typer.Context,
    server: str = typer.Argument(None, help="Server ID (optional, API mode)"),
    out: str = typer.Option(
        None, "--out", help="List local backup dir instead of the API"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Print what would be listed without doing it"
    ),
) -> None:
    """List backups

    Args:
        ctx: Typer context for accessing config and output format.

    Returns:
        None (output is printed via print_output).
    """
    if out is not None:
        if dry_run:
            print_output(
                {"dry_run": True, "out": out, "note": "would list local files"},
                ctx.obj.get("output", "table"),
            )
            return
        try:
            names = sorted(os.listdir(out))
        except OSError:
            print_output(
                {"backups": [], "out": out, "note": "directory not found"},
                ctx.obj.get("output", "table"),
            )
            return
        rows = [
            {"file": n, "size_bytes": os.path.getsize(os.path.join(out, n))}
            for n in names
            if fnmatch.fnmatch(n, "infra-pilot_*.dump*")
            or fnmatch.fnmatch(n, "redis_*.rdb*")
            or fnmatch.fnmatch(n, "grafana_*.tgz*")
        ]
        print_output(
            {"backups": rows, "out": out}, ctx.obj.get("output", "table")
        )
        return
    if dry_run:
        path = f"/backup-jobs?app_id={server}" if server else "/backup-jobs"
        print_output(
            {"dry_run": True, "request": f"GET {path}"},
            ctx.obj.get("output", "table"),
        )
        return
    client = _get_client(ctx)
    result = client.list_backups(server)
    data = (
        result if isinstance(result, builtins.list) else result.get("backups", result)
    )
    print_output(data, ctx.obj.get("output", "table"))


@app.command()
def create(
    ctx: typer.Context,
    server: str = typer.Argument(
        None,
        help="Server ID or name (API mode). Omit for local scripts/db-backup.sh.",
    ),
    s3_target: str = typer.Option(
        None, "--s3", help="S3/Backblaze target (bucket:path)"
    ),
    keep: int = typer.Option(
        10, "--keep", help="Keep only N most recent local backups (local mode)"
    ),
    out: str = typer.Option(
        None, "--out", help="Local backup output directory (local mode)"
    ),
    borg_repo: str = typer.Option(
        None,
        "--borg-repo",
        help="Borg repo (local mode; passphrase stays in BORG_PASSPHRASE env)",
    ),
    rclone_remote: str = typer.Option(
        None, "--rclone-remote", help="Rclone remote (local mode)"
    ),
    skip_redis: bool = typer.Option(
        False, "--skip-redis", help="Skip Redis snapshot (local mode)"
    ),
    skip_grafana: bool = typer.Option(
        False, "--skip-grafana", help="Skip Grafana archive (local mode)"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Print what would be done without doing it"
    ),
) -> None:
    """Create a backup

    Args:
        ctx: Typer context for accessing config and output format.

    Returns:
        None (output is printed via print_output).
    """
    local_flags = (
        out is not None
        or borg_repo is not None
        or rclone_remote is not None
        or skip_redis
        or skip_grafana
        or keep != 10
    )
    if server is None:
        cmd = _build_local_backup_cmd(
            keep, out, s3_target, borg_repo, rclone_remote,
            skip_redis, skip_grafana, dry_run,
        )
        if dry_run:
            print_output(
                {"dry_run": True, "command": " ".join(cmd)},
                ctx.obj.get("output", "table"),
            )
            return
        script = _backup_script()
        if not os.path.isfile(script):
            typer.echo(f"Local backup script not found: {script}", err=True)
            raise typer.Exit(code=1)
        proc = subprocess.run(cmd, check=False)
        print_output(
            {"command": " ".join(cmd), "returncode": proc.returncode},
            ctx.obj.get("output", "table"),
        )
        if proc.returncode != 0:
            raise typer.Exit(code=proc.returncode)
        return
    if local_flags:
        typer.echo(
            "Local options (--out/--keep/--borg-repo/--rclone-remote/--skip-*) "
            "require omitting SERVER (local scripts/db-backup.sh mode).",
            err=True,
        )
        raise typer.Exit(code=1)
    if dry_run:
        payload: dict = {
            "app_id": server,
            "name": f"backup-{server}",
            "schedule_type": "manual",
        }
        if s3_target:
            payload["s3_target"] = s3_target
        print_output(
            {"dry_run": True, "request": "POST /backup-jobs", "payload": payload},
            ctx.obj.get("output", "table"),
        )
        return
    client = _get_client(ctx)
    result = client.create_backup(server, s3_target=s3_target)
    print_output(result, ctx.obj.get("output", "table"))


@app.command()
def schedule(
    ctx: typer.Context,
    server: str = typer.Argument(..., help="Server ID or name"),
    interval: str = typer.Option(
        "daily", "--interval", "-i", help="Interval: hourly, daily, weekly"
    ),
    retention: int = typer.Option(
        7, "--retention", "-r", help="Number of backups to retain"
    ),
    s3_target: str = typer.Option(
        None, "--s3", help="S3/Backblaze target for offsite storage"
    ),
):
    """Schedule automated backups"""
    client = _get_client(ctx)
    result = client._post(
        "/backup-jobs",
        {
            "app_id": server,
            "name": f"auto-{server}",
            "schedule_type": interval,
            "retention_count": retention,
            "s3_target": s3_target,
        },
    )
    print_output(result, ctx.obj.get("output", "table"))


@app.command()
def snapshots(
    ctx: typer.Context,
    server: str = typer.Argument(..., help="Server ID or name"),
    create: bool = typer.Option(False, "--create", help="Create a new snapshot"),
    restore: str = typer.Option(None, "--restore", help="Restore from snapshot ID"),
):
    """Manage server snapshots"""
    client = _get_client(ctx)
    if create:
        result = client._post(f"/apps/{server}/snapshots", {})
        print_output(result, ctx.obj.get("output", "table"))
        return
    if restore:
        result = client._post(f"/apps/{server}/snapshots/{restore}/restore", {})
        print_output(result, ctx.obj.get("output", "table"))
        return
    result = client._get(f"/apps/{server}/snapshots")
    data = (
        result if isinstance(result, builtins.list) else result.get("snapshots", result)
    )
    print_output(data, ctx.obj.get("output", "table"))


@app.command()
def restore(
    ctx: typer.Context,
    backup_id: str = typer.Argument(..., help="Backup ID or name"),
    target: str = typer.Option(
        None, "--target", "-t", help="Target server for restore"
    ),
):
    """Restore from a backup"""
    client = _get_client(ctx)
    result = client._post(
        f"/backups/{backup_id}/restore", {"target": target} if target else {}
    )
    print_output(result, ctx.obj.get("output", "table"))


@app.command()
def config(
    ctx: typer.Context,
    s3_bucket: str = typer.Option(None, "--s3-bucket", help="S3/Backblaze bucket name"),
    s3_key: str = typer.Option(None, "--s3-key", help="S3/Backblaze access key"),
    s3_secret: str = typer.Option(None, "--s3-secret", help="S3/Backblaze secret key"),
    s3_endpoint: str = typer.Option(
        None, "--s3-endpoint", help="S3-compatible endpoint URL"
    ),
):
    """Configure backup storage (S3/Backblaze)"""
    client = _get_client(ctx)
    result = client._post(
        "/backup/config",
        {
            "s3_bucket": s3_bucket,
            "s3_key": s3_key,
            "s3_secret": s3_secret,
            "s3_endpoint": s3_endpoint,
        },
    )
    print_output(result, ctx.obj.get("output", "table"))


@app.command()
def verify(
    ctx: typer.Context,
    backup_file: str = typer.Argument(
        ..., help="Local backup file to verify (.dump[.gpg])"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Print what would be checked without doing it"
    ),
) -> None:
    """Verify a local backup file (exists + pg_dump header + pg_restore).

    Mirrors the checks in scripts/db-restore.sh without touching docker.
    """
    if dry_run:
        print_output(
            {
                "dry_run": True,
                "file": backup_file,
                "checks": "exists, pgdmp-header, pg_restore --list",
            },
            ctx.obj.get("output", "table"),
        )
        return
    if not os.path.isfile(backup_file):
        print_output(
            {"file": backup_file, "ok": False, "error": "file not found"},
            ctx.obj.get("output", "table"),
        )
        raise typer.Exit(code=1)
    with open(backup_file, "rb") as f:
        header_ok = f.read(5) == b"PGDMP"
    entries: object = "skipped (pg_restore not in PATH)"
    if shutil.which("pg_restore"):
        proc = subprocess.run(
            ["pg_restore", "--list", backup_file],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode == 0:
            entries = sum(
                1 for line in proc.stdout.splitlines() if line and ";" in line
            )
        else:
            entries = f"pg_restore failed: {proc.stderr.strip()[:200]}"
            header_ok = False
    ok = bool(header_ok) and not (
        isinstance(entries, str) and entries.startswith("pg_restore failed")
    )
    print_output(
        {
            "file": backup_file,
            "pgdmp_header": header_ok,
            "pg_restore_entries": entries,
            "ok": ok,
        },
        ctx.obj.get("output", "table"),
    )
    if not ok:
        raise typer.Exit(code=1)
