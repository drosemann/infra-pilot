"""Maintenance - Scheduled maintenance windows."""

from typing import Optional

import typer

from ...client import ApiClient
from ...config import DEFAULT_API_URL, load_config
from ...output.formatters import print_output

app = typer.Typer(
    help="Maintenance windows",
    epilog=(
        "Examples:\n\n"
        "  ipilot maintenance list\n"
        "  ipilot maintenance create --title \"db upgrade\" \\\n"
        "      --starts 2026-02-01T00:00:00Z --ends 2026-02-01T02:00:00Z\n"
        "  ipilot maintenance update m1 --status active\n"
        "  ipilot maintenance enable m1\n"
        "  ipilot maintenance disable m1\n"
        "  ipilot maintenance delete m1\n"
    ),
)

WINDOW_STATUSES = ("scheduled", "active", "completed", "cancelled")


# Announce the outage before the outage announces itself.
def _get_client(ctx: typer.Context) -> ApiClient:
    config = load_config(profile=ctx.obj.get("profile"))
    return ApiClient(config.get("api_url", DEFAULT_API_URL), config.get("token"))


@app.command("list")
def list_cmd(ctx: typer.Context):
    """List maintenance windows.

    Windows are ordered by start time, newest first.
    """
    client = _get_client(ctx)
    result = client.list_maintenance_windows()
    data = result if isinstance(result, list) else result.get("windows", result)
    print_output(data, ctx.obj.get("output", "table"))


@app.command()
def create(
    ctx: typer.Context,
    title: str = typer.Option(..., "--title", "-t", help="Window title"),
    starts: str = typer.Option(..., "--starts", help="ISO-8601 start timestamp"),
    ends: str = typer.Option(..., "--ends", help="ISO-8601 end timestamp"),
    description: Optional[str] = typer.Option(None, "--description", help="Window description"),
    app_id: Optional[str] = typer.Option(None, "--app", "-a", help="Restrict to an app ID"),
):
    """Create a maintenance window.

    --starts and --ends are ISO-8601 timestamps. Use --app to scope
    the window to a single app; omit it for a fleet-wide window.
    """
    client = _get_client(ctx)
    result = client.create_maintenance_window(
        title=title,
        starts_at=starts,
        ends_at=ends,
        description=description,
        app_id=app_id,
    )
    print_output(result, ctx.obj.get("output", "table"))


@app.command()
def update(
    ctx: typer.Context,
    window_id: str = typer.Argument(..., help="Maintenance window ID"),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="New title"),
    description: Optional[str] = typer.Option(None, "--description", help="New description"),
    starts: Optional[str] = typer.Option(None, "--starts", help="New ISO-8601 start"),
    ends: Optional[str] = typer.Option(None, "--ends", help="New ISO-8601 end"),
    app_id: Optional[str] = typer.Option(None, "--app", "-a", help="New app ID"),
    status: Optional[str] = typer.Option(None, "--status", help=f"New status: {', '.join(WINDOW_STATUSES)}"),
):
    """Update a maintenance window.

    Only the flags you pass are sent. --status accepts scheduled,
    active, completed, or cancelled.
    """
    if status is not None and status not in WINDOW_STATUSES:
        typer.echo(
            f"Error: unsupported status '{status}' (choose from {', '.join(WINDOW_STATUSES)})",
            err=True,
        )
        raise typer.Exit(code=2)
    fields = {}
    if title is not None:
        fields["title"] = title
    if description is not None:
        fields["description"] = description
    if starts is not None:
        fields["starts_at"] = starts
    if ends is not None:
        fields["ends_at"] = ends
    if app_id is not None:
        fields["app_id"] = app_id
    if status is not None:
        fields["status"] = status
    if not fields:
        typer.echo("Error: no fields to update", err=True)
        raise typer.Exit(code=2)
    client = _get_client(ctx)
    result = client.update_maintenance_window(window_id, **fields)
    print_output(result, ctx.obj.get("output", "table"))


@app.command()
def delete(
    ctx: typer.Context,
    window_id: str = typer.Argument(..., help="Maintenance window ID"),
):
    """Delete a maintenance window.

    Permanently removes the window; use disable to keep it but
    stop it from applying.
    """
    client = _get_client(ctx)
    result = client.delete_maintenance_window(window_id)
    print_output(result, ctx.obj.get("output", "table"))


@app.command()
def enable(
    ctx: typer.Context,
    window_id: str = typer.Argument(..., help="Maintenance window ID"),
):
    """Re-enable a maintenance window (status -> scheduled).

    Shorthand for `update <id> --status scheduled`.
    """
    client = _get_client(ctx)
    result = client.update_maintenance_window(window_id, status="scheduled")
    print_output(result, ctx.obj.get("output", "table"))


@app.command()
def disable(
    ctx: typer.Context,
    window_id: str = typer.Argument(..., help="Maintenance window ID"),
):
    """Disable a maintenance window (status -> cancelled).

    Shorthand for `update <id> --status cancelled`.
    """
    client = _get_client(ctx)
    result = client.update_maintenance_window(window_id, status="cancelled")
    print_output(result, ctx.obj.get("output", "table"))
