"""Two-Factor - TOTP second factor for panel accounts.

CLI login uses API keys (``ipilot login <api-key>``) and does not
challenge for a TOTP code; 2FA protects panel/web sign-ins. These
commands manage the server-side 2FA state for a user.
"""

from typing import Optional

import typer

from ...client import ApiClient
from ...config import DEFAULT_API_URL, load_config
from ...output.formatters import print_output

app = typer.Typer(
    help="Two-factor authentication (panel accounts)",
    epilog=(
        "Examples:\n\n"
        "  ipilot two-factor status\n"
        "  ipilot two-factor setup\n"
        "  ipilot two-factor verify 123456\n"
        "  ipilot two-factor backup-codes\n"
        "  ipilot two-factor backup-codes --regenerate\n"
        "  ipilot two-factor disable --password <password>\n"
        "\n"
        "CLI login uses API keys and never challenges for TOTP;\n"
        "these commands manage the 2FA state that protects panel\n"
        "web sign-ins for the account.\n"
    ),
)


# The CLI carries an API key; 2FA guards the front door the browser uses.
def _get_client(ctx: typer.Context) -> ApiClient:
    config = load_config(profile=ctx.obj.get("profile"))
    return ApiClient(config.get("api_url", DEFAULT_API_URL), config.get("token"))


def _resolve_user_id(client: ApiClient, user: Optional[str]) -> str:
    """Resolve the target user ID, falling back to the token owner.

    Args:
        client: API client.
        user: Explicit user ID, if provided.

    Returns:
        The user ID to act as.

    Raises:
        typer.Exit: If the user ID cannot be determined.
    """
    if user:
        return user
    profile = client.get_current_user()
    if isinstance(profile, dict) and profile.get("id"):
        return str(profile["id"])
    typer.echo(
        "Error: could not determine user ID; pass --user or check authentication",
        err=True,
    )
    raise typer.Exit(code=1)


@app.command()
def status(
    ctx: typer.Context,
    user: Optional[str] = typer.Option(None, "--user", help="User ID (default: current user)"),
):
    """Show 2FA status for a user.

    Probes the backup-codes endpoint: a successful response means 2FA is
    provisioned. Note that CLI login uses API keys and never prompts for
    a TOTP code.
    """
    client = _get_client(ctx)
    user_id = _resolve_user_id(client, user)
    result = client.get_2fa_backup_codes(user_id)
    if isinstance(result, dict) and "error" in result:
        print_output(
            {"user_id": user_id, "enabled": False, "detail": result["error"], "cli_login": "api-key"},
            ctx.obj.get("output", "table"),
        )
        return
    codes = []
    if isinstance(result, dict):
        codes = result.get("backup_codes") or result.get("codes") or []
    print_output(
        {
            "user_id": user_id,
            "enabled": True,
            "backup_codes_on_file": len(codes) if isinstance(codes, list) else codes,
            "cli_login": "api-key (2FA is not challenged for API-key sessions)",
        },
        ctx.obj.get("output", "table"),
    )


@app.command()
def setup(
    ctx: typer.Context,
    user: Optional[str] = typer.Option(None, "--user", help="User ID (default: current user)"),
):
    """Begin 2FA setup; prints the secret and authenticator URI.

    Add the secret to your authenticator app, then confirm with
    `two-factor verify <code>`.
    """
    client = _get_client(ctx)
    user_id = _resolve_user_id(client, user)
    result = client.setup_2fa(user_id)
    print_output(result, ctx.obj.get("output", "table"))


@app.command()
def verify(
    ctx: typer.Context,
    code: str = typer.Argument(..., help="6-digit TOTP code from the authenticator app"),
    user: Optional[str] = typer.Option(None, "--user", help="User ID (default: current user)"),
):
    """Confirm a 2FA setup with a TOTP code.

    Completes provisioning; backup codes become available after
    confirmation.
    """
    client = _get_client(ctx)
    user_id = _resolve_user_id(client, user)
    result = client.verify_2fa_setup(user_id, code)
    print_output(result, ctx.obj.get("output", "table"))


@app.command()
def disable(
    ctx: typer.Context,
    password: str = typer.Option(..., "--password", help="Account password for confirmation"),
    user: Optional[str] = typer.Option(None, "--user", help="User ID (default: current user)"),
):
    """Disable 2FA for a user (requires the account password).

    The password confirms account ownership before the second factor
    is torn down.
    """
    client = _get_client(ctx)
    user_id = _resolve_user_id(client, user)
    result = client.disable_2fa(user_id, password)
    print_output(result, ctx.obj.get("output", "table"))


@app.command("backup-codes")
def backup_codes(
    ctx: typer.Context,
    regenerate: bool = typer.Option(
        False,
        "--regenerate",
        help="Re-provision 2FA to issue new backup codes (starts the setup flow again)",
    ),
    user: Optional[str] = typer.Option(None, "--user", help="User ID (default: current user)"),
):
    """List 2FA backup codes, or regenerate them via re-provisioning.

    --regenerate starts a fresh setup flow (issuing a new secret and
    backup codes); confirm with `two-factor verify <code>` to
    activate them.
    """
    client = _get_client(ctx)
    user_id = _resolve_user_id(client, user)
    if regenerate:
        result = client.setup_2fa(user_id)
        if isinstance(result, dict) and "error" in result:
            print_output(result, ctx.obj.get("output", "table"))
            return
        print_output(
            {
                "status": "re-provisioning started",
                "detail": "Confirm the new secret with 'ipilot two-factor verify <code>'; "
                "existing backup codes are invalidated once confirmed.",
                "setup": result,
            },
            ctx.obj.get("output", "table"),
        )
        return
    result = client.get_2fa_backup_codes(user_id)
    data = result if not isinstance(result, dict) else result.get("backup_codes", result)
    print_output(data, ctx.obj.get("output", "table"))
