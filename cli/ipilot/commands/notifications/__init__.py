"""Notifications - Notification channel management (delivery targets).

Alert rules decide *when* to notify; channels decide *where* the message
goes. This group only manages channels.
"""

import json
from typing import Any, Dict, Optional

import typer

from ...client import ApiClient
from ...config import DEFAULT_API_URL, load_config
from ...output.formatters import print_output

app = typer.Typer(
    help="Notification channels",
    epilog=(
        "Examples:\n\n"
        "  ipilot notifications list\n"
        "  ipilot notifications create ops-mail --type email \\\n"
        "      --config '{\"to\": \"ops@example.com\"}'\n"
        "  ipilot notifications create ops-hook --type webhook \\\n"
        "      --config '{\"url\": \"https://example.com/h\"}'\n"
        "  ipilot notifications update n1 --disable\n"
        "  ipilot notifications test n1\n"
        "  ipilot notifications delete n1\n"
    ),
)

CHANNEL_TYPES = ("email", "webhook", "telegram")


# A channel is a promise that somebody will be woken up.
def _get_client(ctx: typer.Context) -> ApiClient:
    config = load_config(profile=ctx.obj.get("profile"))
    return ApiClient(config.get("api_url", DEFAULT_API_URL), config.get("token"))


def _parse_config(raw: Optional[str]) -> Dict[str, Any]:
    """Parse a JSON config payload.

    Args:
        raw: JSON object string.

    Returns:
        The parsed config dict.

    Raises:
        typer.Exit: If the JSON is invalid or not an object.
    """
    if raw is None:
        return {}
    try:
        config = json.loads(raw)
    except json.JSONDecodeError as exc:
        typer.echo(f"Error: --config must be valid JSON: {exc}", err=True)
        raise typer.Exit(code=2)
    if not isinstance(config, dict):
        typer.echo("Error: --config must be a JSON object", err=True)
        raise typer.Exit(code=2)
    return config


@app.command("list")
def list_cmd(ctx: typer.Context):
    """List notification channels.

    Channels are delivery targets (email, webhook, telegram); alert
    rules decide when they fire (see `ipilot alerts`).
    """
    client = _get_client(ctx)
    result = client.list_notification_channels()
    data = result if isinstance(result, list) else result.get("channels", result)
    print_output(data, ctx.obj.get("output", "table"))


@app.command()
def create(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Channel name"),
    channel_type: str = typer.Option(..., "--type", help=f"Channel type: {', '.join(CHANNEL_TYPES)}"),
    config: Optional[str] = typer.Option(None, "--config", help="JSON config payload for the channel"),
):
    """Create a notification channel.

    --type must be email, webhook, or telegram. --config is a JSON
    object with channel-specific settings, for example
    '{"to": "ops@example.com"}' for email or
    '{"url": "https://example.com/hook"}' for webhook.
    """
    if channel_type not in CHANNEL_TYPES:
        typer.echo(
            f"Error: unsupported type '{channel_type}' (choose from {', '.join(CHANNEL_TYPES)})",
            err=True,
        )
        raise typer.Exit(code=2)
    payload = _parse_config(config)
    if not payload:
        typer.echo("Error: --config is required (e.g. '{\"to\": \"ops@example.com\"}')", err=True)
        raise typer.Exit(code=2)
    client = _get_client(ctx)
    result = client.create_notification_channel(
        name=name, channel_type=channel_type, config=payload
    )
    print_output(result, ctx.obj.get("output", "table"))


@app.command()
def update(
    ctx: typer.Context,
    channel_id: str = typer.Argument(..., help="Channel ID"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="New channel name"),
    config: Optional[str] = typer.Option(None, "--config", help="Replacement JSON config"),
    enable: bool = typer.Option(False, "--enable", help="Enable the channel"),
    disable: bool = typer.Option(False, "--disable", help="Disable the channel"),
):
    """Update a notification channel.

    Only the flags you pass are sent. --config replaces the stored
    config wholesale. --enable and --disable are mutually exclusive.
    """
    if enable and disable:
        typer.echo("Error: --enable and --disable are mutually exclusive", err=True)
        raise typer.Exit(code=2)
    fields: Dict[str, Any] = {}
    if name is not None:
        fields["name"] = name
    if config is not None:
        fields["config"] = _parse_config(config)
    if enable:
        fields["enabled"] = True
    if disable:
        fields["enabled"] = False
    if not fields:
        typer.echo("Error: no fields to update", err=True)
        raise typer.Exit(code=2)
    client = _get_client(ctx)
    result = client.update_notification_channel(channel_id, **fields)
    print_output(result, ctx.obj.get("output", "table"))


@app.command()
def delete(
    ctx: typer.Context,
    channel_id: str = typer.Argument(..., help="Channel ID"),
):
    """Delete a notification channel.

    Alert rules referencing the channel keep their conditions; only
    the delivery target is removed.
    """
    client = _get_client(ctx)
    result = client.delete_notification_channel(channel_id)
    print_output(result, ctx.obj.get("output", "table"))


@app.command()
def test(
    ctx: typer.Context,
    channel_id: str = typer.Argument(..., help="Channel ID"),
):
    """Send a test notification through a channel.

    Asks the panel to deliver a sample message so you can verify
    credentials and connectivity before relying on the channel.
    """
    client = _get_client(ctx)
    result = client.test_notification_channel(channel_id)
    print_output(result, ctx.obj.get("output", "table"))
