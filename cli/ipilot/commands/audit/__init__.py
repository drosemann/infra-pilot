"""Audit - Filtered audit log browsing and export."""

import csv
import io
import json
import sys
import time
from typing import Any, Dict, List, Optional

import typer

from ...client import ApiClient
from ...config import DEFAULT_API_URL, load_config
from ...output.formatters import print_output

app = typer.Typer(
    help="Audit log",
    epilog=(
        "Examples:\n\n"
        "  ipilot audit list --limit 20\n"
        "  ipilot audit list --action alert:create --resource alert_config\n"
        "  ipilot audit list --since 2026-01-01 --until 2026-02-01 --page 2\n"
        "  ipilot audit export --format csv --file audit.csv\n"
        "  ipilot audit export --format jsonl > audit.jsonl\n"
        "  ipilot audit watch --interval 5 --limit 10\n"
        "  ipilot audit watch --action database:create\n"
    ),
)

MAX_PAGE_SIZE = 200


# Every audit entry is somebody's alibi; keep the filters honest.
def _get_client(ctx: typer.Context) -> ApiClient:
    config = load_config(profile=ctx.obj.get("profile"))
    return ApiClient(config.get("api_url", DEFAULT_API_URL), config.get("token"))


def _fetch_entries(
    client: ApiClient,
    actor: Optional[str],
    action: Optional[str],
    resource: Optional[str],
    start_date: Optional[str],
    end_date: Optional[str],
    total_limit: int,
) -> Any:
    """Fetch up to ``total_limit`` audit entries across pages.

    Args:
        client: API client.
        actor: Optional user ID filter.
        action: Optional action filter.
        resource: Optional entity type filter.
        start_date: Optional ISO-8601 lower bound.
        end_date: Optional ISO-8601 upper bound.
        total_limit: Maximum entries to collect.

    Returns:
        List of audit entries, or an error dict from the first request.
    """
    entries: List[Dict[str, Any]] = []
    offset = 0
    first = True
    while len(entries) < total_limit:
        page_size = min(MAX_PAGE_SIZE, total_limit - len(entries))
        result = client.list_audit_log(
            actor=actor,
            action=action,
            resource=resource,
            start_date=start_date,
            end_date=end_date,
            limit=page_size,
            offset=offset,
        )
        if not isinstance(result, dict):
            if first and not isinstance(result, list):
                return {"error": "Unexpected audit-log response"}
            page = result
        elif "error" in result:
            if first:
                return result
            break
        else:
            page = result.get("data", [])
        if not page:
            break
        entries.extend(page)
        if isinstance(result, dict):
            total = result.get("total")
            offset += len(page)
            if isinstance(total, int) and offset >= total:
                break
            if len(page) < page_size:
                break
        else:
            break
        first = False
    return entries


def _to_csv(entries: List[Dict[str, Any]]) -> str:
    """Serialise audit entries as CSV.

    Args:
        entries: Audit entry dicts.

    Returns:
        CSV text with a header row.
    """
    if not entries:
        return ""
    preferred = ["id", "action", "entity_type", "entity_id", "created_at"]
    keys: List[str] = [k for k in preferred if any(k in e for e in entries)]
    for entry in entries:
        for key in entry:
            if key not in keys:
                keys.append(key)
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=keys, extrasaction="ignore")
    writer.writeheader()
    for entry in entries:
        writer.writerow(
            {
                k: json.dumps(v) if isinstance(v, (dict, list)) else v
                for k, v in entry.items()
            }
        )
    return buffer.getvalue()


def _to_jsonl(entries: List[Dict[str, Any]]) -> str:
    """Serialise audit entries as JSON Lines.

    Args:
        entries: Audit entry dicts.

    Returns:
        JSONL text (one object per line).
    """
    return "\n".join(json.dumps(e, default=str) for e in entries)


@app.command("list")
def list_cmd(
    ctx: typer.Context,
    actor: Optional[str] = typer.Option(None, "--actor", help="Filter by acting user ID"),
    action: Optional[str] = typer.Option(None, "--action", "-a", help="Filter by action (e.g. alert:create)"),
    resource: Optional[str] = typer.Option(None, "--resource", "-r", help="Filter by entity type (e.g. alert_config)"),
    since: Optional[str] = typer.Option(None, "--since", help="ISO-8601 lower bound on created_at"),
    until: Optional[str] = typer.Option(None, "--until", help="ISO-8601 upper bound on created_at"),
    limit: int = typer.Option(50, "--limit", "-l", help="Page size (max 200)"),
    page: int = typer.Option(1, "--page", "-p", help="Page number (1-based)"),
):
    """List audit log entries (paginated).

    Filters: --actor (user ID), --action (e.g. alert:create),
    --resource (entity type, e.g. alert_config), --since/--until
    (ISO-8601 bounds on created_at). --limit is the page size
    (max 200); --page selects the 1-based page.
    """
    if limit < 1 or limit > MAX_PAGE_SIZE:
        typer.echo(f"Error: --limit must be between 1 and {MAX_PAGE_SIZE}", err=True)
        raise typer.Exit(code=2)
    if page < 1:
        typer.echo("Error: --page must be at least 1", err=True)
        raise typer.Exit(code=2)
    client = _get_client(ctx)
    result = client.list_audit_log(
        actor=actor,
        action=action,
        resource=resource,
        start_date=since,
        end_date=until,
        limit=limit,
        offset=(page - 1) * limit,
    )
    print_output(result, ctx.obj.get("output", "table"))


@app.command()
def export(
    ctx: typer.Context,
    fmt: str = typer.Option("csv", "--format", "-f", help="Export format: csv or jsonl"),
    output_file: Optional[str] = typer.Option(None, "--file", help="Write to file instead of stdout"),
    actor: Optional[str] = typer.Option(None, "--actor", help="Filter by acting user ID"),
    action: Optional[str] = typer.Option(None, "--action", "-a", help="Filter by action"),
    resource: Optional[str] = typer.Option(None, "--resource", "-r", help="Filter by entity type"),
    since: Optional[str] = typer.Option(None, "--since", help="ISO-8601 lower bound"),
    until: Optional[str] = typer.Option(None, "--until", help="ISO-8601 upper bound"),
    limit: int = typer.Option(1000, "--limit", "-l", help="Maximum entries to export"),
):
    """Export audit log entries as CSV or JSON Lines.

    Fetches up to --limit entries across pages using the same
    filters as list. Writes to --file when given, otherwise to
    stdout for piping.
    """
    if fmt not in ("csv", "jsonl"):
        typer.echo("Error: --format must be csv or jsonl", err=True)
        raise typer.Exit(code=2)
    if limit < 1:
        typer.echo("Error: --limit must be at least 1", err=True)
        raise typer.Exit(code=2)
    client = _get_client(ctx)
    entries = _fetch_entries(client, actor, action, resource, since, until, limit)
    if isinstance(entries, dict) and "error" in entries:
        typer.echo(f"Error: {entries['error']}", err=True)
        raise typer.Exit(code=1)
    text = _to_csv(entries) if fmt == "csv" else _to_jsonl(entries)
    if output_file:
        with open(output_file, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        typer.echo(f"Exported {len(entries)} entries to {output_file}")
        return
    sys.stdout.write(text)
    if text and not text.endswith("\n"):
        sys.stdout.write("\n")


@app.command()
def watch(
    ctx: typer.Context,
    actor: Optional[str] = typer.Option(None, "--actor", help="Filter by acting user ID"),
    action: Optional[str] = typer.Option(None, "--action", "-a", help="Filter by action"),
    resource: Optional[str] = typer.Option(None, "--resource", "-r", help="Filter by entity type"),
    interval: float = typer.Option(5.0, "--interval", "-i", help="Seconds between polls"),
    limit: int = typer.Option(20, "--limit", "-l", help="Entries per poll (max 200)"),
    duration: Optional[float] = typer.Option(None, "--duration", "-d", help="Stop after this many seconds"),
):
    """Follow the audit log, printing new entries as they arrive.

    Polls /api/audit-log every --interval seconds and prints only
    entries not seen in previous polls. The first poll prints the
    current newest entries (up to --limit) to establish a baseline.
    Ctrl-C stops cleanly; --duration stops automatically.

    Exits with code 1 if the backend returns an error.
    """
    if limit < 1 or limit > MAX_PAGE_SIZE:
        typer.echo(f"Error: --limit must be between 1 and {MAX_PAGE_SIZE}", err=True)
        raise typer.Exit(code=2)
    if interval <= 0:
        typer.echo("Error: --interval must be greater than 0", err=True)
        raise typer.Exit(code=2)
    client = _get_client(ctx)
    fmt = ctx.obj.get("output", "table")
    seen: set = set()
    started = time.monotonic()
    baseline = True
    try:
        while True:
            if duration is not None and time.monotonic() - started >= duration:
                break
            result = client.list_audit_log(
                actor=actor,
                action=action,
                resource=resource,
                start_date=None,
                end_date=None,
                limit=limit,
                offset=0,
            )
            if isinstance(result, dict) and "error" in result:
                typer.echo(f"Error: {result['error']}", err=True)
                raise typer.Exit(code=1)
            if isinstance(result, dict):
                page = result.get("data", [])
            else:
                page = result
            fresh = [
                entry
                for entry in page
                if isinstance(entry, dict) and str(entry.get("id")) not in seen
            ]
            for entry in page:
                seen.add(str(entry.get("id")))
            if fresh and not baseline:
                print_output(fresh if len(fresh) > 1 else fresh[0], fmt)
            baseline = False
            if len(seen) > 10000:
                seen = set(list(seen)[-5000:])
            time.sleep(interval)
    except KeyboardInterrupt:
        typer.echo("Stopped watching.", err=True)
