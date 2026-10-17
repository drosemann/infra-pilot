"""Metrics - Real-time, historical, and aggregated resource metrics."""

from datetime import datetime, timezone
from typing import Optional

import typer

from ...client import ApiClient
from ...config import DEFAULT_API_URL, load_config
from ...output.formatters import print_output

app = typer.Typer(
    help="Resource metrics (realtime, history, aggregated)",
    epilog=(
        "Examples:\n\n"
        "  ipilot metrics realtime\n"
        "  ipilot metrics realtime --app app-1\n"
        "  ipilot metrics history --since 24h --interval 1h\n"
        "  ipilot metrics history --since 2026-01-01T00:00:00Z --until 2026-01-01T06:00:00Z\n"
        "  ipilot metrics aggregated --output json\n"
        "  ipilot metrics grafana-url\n"
    ),
)

SUPPORTED_PERIODS = ("1h", "6h", "24h", "7d")
SUPPORTED_RESOLUTIONS = ("1m", "5m", "1h")
_UNIT_SECONDS = {"m": 60, "h": 3600, "d": 86400}


# Metrics are most trustworthy when they arrive before the outage does.
def _get_client(ctx: typer.Context) -> ApiClient:
    config = load_config(profile=ctx.obj.get("profile"))
    return ApiClient(config.get("api_url", DEFAULT_API_URL), config.get("token"))


def _parse_timestamp(value: str) -> datetime:
    """Parse an ISO-8601 timestamp (with or without 'Z').

    Args:
        value: Timestamp string.

    Returns:
        Timezone-aware datetime.

    Raises:
        typer.BadParameter: If the value cannot be parsed.
    """
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise typer.BadParameter(f"invalid ISO-8601 timestamp: {value}")
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def resolve_period(since: Optional[str], until: Optional[str]) -> str:
    """Map --since/--until to a panel-supported period token.

    Relative tokens (1h, 6h, 24h, 7d) pass through after validation.
    ISO-8601 timestamps are converted to the smallest supported period
    that covers the requested window.

    Args:
        since: Relative token or ISO-8601 start timestamp. Defaults to 1h.
        until: Optional ISO-8601 end timestamp (defaults to now).

    Returns:
        A period token supported by the panel (1h, 6h, 24h, 7d).

    Raises:
        typer.BadParameter: If a token is unsupported or a range cannot
            be resolved.
    """
    if since in SUPPORTED_PERIODS:
        return since
    if since is None:
        return "1h"
    start = _parse_timestamp(since)
    end = _parse_timestamp(until) if until else datetime.now(timezone.utc)
    if end <= start:
        raise typer.BadParameter("--until must be after --since")
    seconds = (end - start).total_seconds()
    for token in SUPPORTED_PERIODS:
        unit, count = token[-1], int(token[:-1])
        if seconds <= count * _UNIT_SECONDS[unit]:
            return token
    return "7d"


@app.command()
def realtime(
    ctx: typer.Context,
    app_id: Optional[str] = typer.Option(
        None, "--app", "-a", help="App ID for per-container stats"
    ),
):
    """Show real-time resource usage.

    Prints a CPU/memory/disk/network snapshot. With --app, the panel
    returns per-container stats for that app; without it, host-level
    totals are returned.
    """
    client = _get_client(ctx)
    result = client.metrics_realtime(app_id=app_id)
    print_output(result, ctx.obj.get("output", "table"))


@app.command()
def history(
    ctx: typer.Context,
    app_id: Optional[str] = typer.Option(
        None, "--app", "-a", help="App ID to filter by"
    ),
    since: Optional[str] = typer.Option(
        None,
        "--since",
        help="Window start: 1h, 6h, 24h, 7d, or an ISO-8601 timestamp",
    ),
    until: Optional[str] = typer.Option(
        None, "--until", help="Window end as an ISO-8601 timestamp (default now)"
    ),
    interval: str = typer.Option(
        "5m", "--interval", "-i", help="Aggregation bucket: 1m, 5m, or 1h"
    ),
):
    """Show historical metric time series.

    --since accepts either a relative window token (1h, 6h, 24h, 7d)
    or an ISO-8601 start timestamp; ISO ranges are mapped to the
    smallest panel-supported period that covers them. --interval sets
    the aggregation bucket (1m, 5m, or 1h).
    """
    if interval not in SUPPORTED_RESOLUTIONS:
        typer.echo(
            f"Error: unsupported interval '{interval}' "
            f"(choose from {', '.join(SUPPORTED_RESOLUTIONS)})",
            err=True,
        )
        raise typer.Exit(code=2)
    try:
        period = resolve_period(since, until)
    except typer.BadParameter as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2)
    client = _get_client(ctx)
    result = client.metrics_history(
        app_id=app_id, period=period, resolution=interval, until=until
    )
    print_output(result, ctx.obj.get("output", "table"))


@app.command("aggregated")
def aggregated_cmd(
    ctx: typer.Context,
):
    """Show aggregated metrics across all apps.

    Returns fleet-wide totals and averages across every app the token
    owner can see.
    """
    client = _get_client(ctx)
    result = client.metrics_aggregated()
    print_output(result, ctx.obj.get("output", "table"))


@app.command("grafana-url")
def grafana_url(
    ctx: typer.Context,
):
    """Show the configured Grafana embed URL, if any."""
    client = _get_client(ctx)
    result = client.metrics_grafana_url()
    print_output(result, ctx.obj.get("output", "table"))
