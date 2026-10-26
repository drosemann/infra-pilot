"""Feature flags - list, evaluate, and manage panel feature flags."""

import builtins
from typing import Optional

import typer

from ...client import ApiClient
from ...config import DEFAULT_API_URL, load_config
from ...output.formatters import print_output

app = typer.Typer(help="Feature flag management")


def _get_client(ctx: typer.Context) -> ApiClient:
    config = load_config(profile=ctx.obj.get("profile"))
    return ApiClient(config.get("api_url", DEFAULT_API_URL), config.get("token"))


@app.command()
def list(ctx: typer.Context):
    """List all feature flags (admin)."""
    client = _get_client(ctx)
    result = client.list_flags()
    data = result if isinstance(result, builtins.list) else result.get("flags", result)
    print_output(data, ctx.obj.get("output", "table"))


@app.command()
def evaluate(ctx: typer.Context):
    """Show evaluated flag values for the current user."""
    client = _get_client(ctx)
    result = client.evaluate_flags()
    print_output(result.get("flags", result), ctx.obj.get("output", "table"))


@app.command()
def create(
    ctx: typer.Context,
    key: str = typer.Argument(..., help="Flag key slug, e.g. living_fleet"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="Flag description"),
):
    """Create a feature flag (admin)."""
    client = _get_client(ctx)
    result = client.create_flag(key, description or "")
    print_output(result, ctx.obj.get("output", "table"))


@app.command()
def rollout(
    ctx: typer.Context,
    key: str = typer.Argument(..., help="Flag key"),
    environment: str = typer.Option("production", "--env", "-e", help="development|staging|production"),
    enable: bool = typer.Option(True, "--enable/--disable", help="Enable or disable the flag"),
    percent: int = typer.Option(0, "--percent", "-p", help="Rollout percentage 0-100"),
):
    """Enable/disable a flag or set its rollout percentage (admin)."""
    client = _get_client(ctx)
    result = client.set_flag_rule(key, environment, enable, percent)
    print_output(result, ctx.obj.get("output", "table"))


@app.command()
def kill(
    ctx: typer.Context,
    key: str = typer.Argument(..., help="Flag key"),
):
    """Kill switch: disable a flag in ALL environments (admin)."""
    client = _get_client(ctx)
    result = client.kill_flag(key)
    print_output(result, ctx.obj.get("output", "table"))
