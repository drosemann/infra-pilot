"""API Key management - Create, list, rotate, revoke API keys for programmatic access."""

import builtins
from typing import Optional

import typer

from ...client import ApiClient
from ...config import DEFAULT_API_URL, load_config
from ...output.formatters import print_output

app = typer.Typer(help="API key management")


def _get_client(ctx: typer.Context) -> ApiClient:
    config = load_config(profile=ctx.obj.get("profile"))
    return ApiClient(config.get("api_url", DEFAULT_API_URL), config.get("token"))


def _parse_scopes(value: Optional[str]) -> Optional[list]:
    """Turn a comma-separated scope list into a clean array (None = unspecified).

    Unknown tokens stay untouched: the server validates syntax and answers
    with a clear 400 so the error matches its authoritative vocabulary
    (`apps:read`, `metrics:*`, `audit:export`, ...).
    """
    if value is None:
        return None
    scopes = [s.strip() for s in value.split(",") if s.strip()]
    return [s for s in scopes] or ["*"]


@app.command()
def list(
    ctx: typer.Context,
):
    """List all API keys (scopes, class, last used, rotation state)."""
    client = _get_client(ctx)
    result = client.list_api_keys()
    data = (
        result if isinstance(result, builtins.list) else result.get("api_keys", result)
    )
    print_output(data, ctx.obj.get("output", "table"))


@app.command()
def create(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Key name"),
    role: str = typer.Option(
        "user", "--role", "-r", help="Legacy role label (kept for compatibility)"
    ),
    expire_days: Optional[int] = typer.Option(
        None, "--expire", "-e", help="Expiration in days (max 730)"
    ),
    scopes: Optional[str] = typer.Option(
        None,
        "--scopes",
        "-s",
        help="Comma-separated scopes, e.g. 'apps:read,metrics:*' (omit for wildcard *)",
    ),
    key_class: Optional[str] = typer.Option(
        None, "--type", "-t", help="Key class: 'live' (production) or 'test'"
    ),
    app_id: Optional[str] = typer.Option(
        None, "--app", "-a", help="Bind the key to one app id (recommended for automation)"
    ),
):
    """Create a new API key (scoped key model)."""
    client = _get_client(ctx)
    result = client.create_api_key(
        name=name,
        role=role,
        expire_days=expire_days,
        scopes=_parse_scopes(scopes),
        key_class=key_class,
        app_id=app_id,
    )
    if isinstance(result, dict) and result.get("error") and result.get("scope_denied"):
        typer.echo(result["error"])
        raise typer.Exit(2)
    if isinstance(result, dict) and "key" in result:
        typer.echo("=" * 60)
        typer.echo("API Key created! Save this key - it will not be shown again.")
        typer.echo(f"Key: {result['key']}")
        typer.echo("=" * 60)
        if isinstance((result.get("scopes")), list) and result["scopes"] == ["*"]:
            typer.echo("Note: wildcard (*) scope. Prefer scoped keys for automation.")
    print_output(result, ctx.obj.get("output", "table"))


@app.command()
def rotate(
    ctx: typer.Context,
    key_id: str = typer.Argument(..., help="Key ID to rotate"),
    overlap_hours: int = typer.Option(
        24, "--overlap", "-o", help="Hours the old key keeps working (max 168)"
    ),
):
    """Rotate a key: a replacement is issued; the old one overlaps, then expires.

    Requires a fresh two-factor code header when TOTP is enabled
    (the panel prompts when the key management route asks for re-auth).
    """
    client = _get_client(ctx)
    result = client.rotate_api_key(key_id, overlap_hours=overlap_hours)
    if isinstance(result, dict) and "key" in result:
        typer.echo("=" * 60)
        typer.echo("Rotation issued! Save this key - it will not be shown again.")
        typer.echo(f"Key: {result['key']}")
        typer.echo("=" * 60)
    print_output(result, ctx.obj.get("output", "table"))


@app.command()
def revoke(
    ctx: typer.Context,
    key_id: str = typer.Argument(..., help="Key ID to revoke"),
):
    """Revoke an API key."""
    client = _get_client(ctx)
    result = client.revoke_api_key(key_id)
    print_output(result, ctx.obj.get("output", "table"))
