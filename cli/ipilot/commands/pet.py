"""Living Fleet pet commands - read-only creature views plus rename."""

import builtins
from typing import Optional

import typer

from ..client import ApiClient
from ..config import DEFAULT_API_URL, load_config
from ..output.formatters import print_output

app = typer.Typer(help="Living Fleet creature status (read-only, plus rename)")


def _get_client(ctx: typer.Context) -> ApiClient:
    config = load_config(profile=ctx.obj.get("profile"))
    return ApiClient(config.get("api_url", DEFAULT_API_URL), config.get("token"))


@app.command(name="list")
def list_pets(
    ctx: typer.Context,
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output format"),
):
    """List all creatures with mood and stage.

    Examples:
        ipilot pet list
    """
    client = _get_client(ctx)
    result = client.list_creatures()
    print_output(result, output or ctx.obj.get("output", "table"))


@app.command()
def status(
    ctx: typer.Context,
    workload_id: str = typer.Argument(..., help="Workload ID of the creature"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output format"),
):
    """Show one creature with vitals and explanation.

    Examples:
        ipilot pet status my-api
    """
    client = _get_client(ctx)
    result = client.get_creature(workload_id)
    print_output(result, output or ctx.obj.get("output", "table"))


@app.command()
def rename(
    ctx: typer.Context,
    workload_id: str = typer.Argument(..., help="Workload ID of the creature"),
    display_name: str = typer.Argument(..., help="New display name (max 64 chars)"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output format"),
):
    """Rename a creature (the only allowed mutation).

    Examples:
        ipilot pet rename my-api "Sir Deploys-a-Lot"
    """
    client = _get_client(ctx)
    result = client.rename_creature(workload_id, display_name)
    print_output(result, output or ctx.obj.get("output", "table"))
