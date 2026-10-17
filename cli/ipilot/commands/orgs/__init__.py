"""Organizations - Multi-tenant organization and membership management."""

from typing import Optional

import typer

from ...client import ApiClient
from ...config import DEFAULT_API_URL, load_config
from ...output.formatters import print_output

app = typer.Typer(
    help="Organizations and memberships",
    epilog=(
        "Examples:\n\n"
        "  ipilot orgs list\n"
        "  ipilot orgs create acme --slug acme-inc\n"
        "  ipilot orgs members o1\n"
        "  ipilot orgs invite o1 ops@example.com --role admin\n"
        "  ipilot orgs roles o1 u1 --set owner\n"
        "  ipilot orgs remove o1 u1\n"
    ),
)

MEMBER_ROLES = ("member", "admin", "owner")


# Multi-tenancy works until invitations arrive by vibes instead of email.
def _get_client(ctx: typer.Context) -> ApiClient:
    config = load_config(profile=ctx.obj.get("profile"))
    return ApiClient(config.get("api_url", DEFAULT_API_URL), config.get("token"))


@app.command("list")
def list_cmd(ctx: typer.Context):
    """List organizations you own or belong to.

    Returns the union of organizations where the current user is
    owner and organizations they were invited to.
    """
    client = _get_client(ctx)
    result = client.list_organizations()
    data = result if isinstance(result, list) else result.get("organizations", result)
    print_output(data, ctx.obj.get("output", "table"))


@app.command()
def create(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Organization name"),
    slug: Optional[str] = typer.Option(None, "--slug", help="URL-safe slug (defaults to the name)"),
):
    """Create an organization.

    The current user becomes the owner. --slug defaults to a
    lowercased, hyphenated form of the name.
    """
    client = _get_client(ctx)
    result = client.create_organization(
        name=name, slug=slug or name.lower().replace(" ", "-")
    )
    print_output(result, ctx.obj.get("output", "table"))


@app.command()
def members(
    ctx: typer.Context,
    org_id: str = typer.Argument(..., help="Organization ID"),
):
    """List members of an organization.

    Requires the org member routes on the panel; older panel builds
    surface a clear backend error.
    """
    client = _get_client(ctx)
    result = client.list_organization_members(org_id)
    data = result if isinstance(result, list) else result.get("members", result)
    print_output(data, ctx.obj.get("output", "table"))


@app.command()
def invite(
    ctx: typer.Context,
    org_id: str = typer.Argument(..., help="Organization ID"),
    email: str = typer.Argument(..., help="Invitee email address"),
    role: str = typer.Option("member", "--role", help=f"Role to assign: {', '.join(MEMBER_ROLES)}"),
):
    """Invite a user to an organization by email.

    --role may be member (default), admin, or owner.
    """
    if role not in MEMBER_ROLES:
        typer.echo(
            f"Error: unsupported role '{role}' (choose from {', '.join(MEMBER_ROLES)})",
            err=True,
        )
        raise typer.Exit(code=2)
    client = _get_client(ctx)
    result = client.invite_organization_member(org_id, email, role=role)
    print_output(result, ctx.obj.get("output", "table"))


@app.command()
def remove(
    ctx: typer.Context,
    org_id: str = typer.Argument(..., help="Organization ID"),
    user_id: str = typer.Argument(..., help="Member user ID"),
):
    """Remove a member from an organization.

    The user keeps their account; only the membership is dropped.
    """
    client = _get_client(ctx)
    result = client.remove_organization_member(org_id, user_id)
    print_output(result, ctx.obj.get("output", "table"))


@app.command()
def roles(
    ctx: typer.Context,
    org_id: str = typer.Argument(..., help="Organization ID"),
    user_id: str = typer.Argument(..., help="Member user ID"),
    set_role: str = typer.Option(..., "--set", help=f"New role: {', '.join(MEMBER_ROLES)}"),
):
    """Change a member's role in an organization.

    --set accepts member, admin, or owner.
    """
    if set_role not in MEMBER_ROLES:
        typer.echo(
            f"Error: unsupported role '{set_role}' (choose from {', '.join(MEMBER_ROLES)})",
            err=True,
        )
        raise typer.Exit(code=2)
    client = _get_client(ctx)
    result = client.set_organization_member_role(org_id, user_id, set_role)
    print_output(result, ctx.obj.get("output", "table"))
