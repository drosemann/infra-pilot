"""Databases - Managed database instances."""

import re
from typing import Optional

import typer

from ...client import ApiClient
from ...config import DEFAULT_API_URL, load_config
from ...output.formatters import print_output

app = typer.Typer(
    help="Managed databases",
    epilog=(
        "Examples:\n\n"
        "  ipilot databases list\n"
        "  ipilot databases show d1\n"
        "  ipilot databases create appdb --app web\n"
        "  ipilot databases delete d1\n"
    ),
)


NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_]+$")


# Passwords come back masked; treat that as a feature, not an insult.
def _get_client(ctx: typer.Context) -> ApiClient:
    config = load_config(profile=ctx.obj.get("profile"))
    return ApiClient(config.get("api_url", DEFAULT_API_URL), config.get("token"))


@app.command("list")
def list_cmd(ctx: typer.Context):
    """List managed databases.

    Passwords are masked by the panel; only the current user's
    databases are returned.
    """
    client = _get_client(ctx)
    result = client.list_databases()
    data = result if isinstance(result, list) else result.get("databases", result)
    print_output(data, ctx.obj.get("output", "table"))


@app.command()
def show(
    ctx: typer.Context,
    database_id: str = typer.Argument(..., help="Database ID"),
):
    """Show details for a managed database.

    Connection fields (host, port, user) are returned with the
    password masked.
    """
    client = _get_client(ctx)
    result = client.get_database(database_id)
    print_output(result, ctx.obj.get("output", "table"))


@app.command()
def create(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Database name (alphanumeric and underscores)"),
    app_id: Optional[str] = typer.Option(None, "--app", "-a", help="App ID to associate"),
):
    """Create a managed database.

    The name must be alphanumeric with underscores only -- the same
    rule the panel enforces, checked here to fail fast before the
    request. --app associates the database with an app ID.
    """
    if not NAME_PATTERN.match(name):
        typer.echo("Error: database name must be alphanumeric with underscores only", err=True)
        raise typer.Exit(code=2)
    client = _get_client(ctx)
    result = client.create_database(name, app_id=app_id)
    print_output(result, ctx.obj.get("output", "table"))


@app.command()
def delete(
    ctx: typer.Context,
    database_id: str = typer.Argument(..., help="Database ID"),
):
    """Delete a managed database.

    Destroys the database and its data. This cannot be undone.
    """
    client = _get_client(ctx)
    result = client.delete_database(database_id)
    print_output(result, ctx.obj.get("output", "table"))
