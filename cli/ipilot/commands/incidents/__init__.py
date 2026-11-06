"""Incidents & On-Call - duty-routed incident workflow with escalation."""

import builtins
from typing import Optional

import typer

from ...client import ApiClient
from ...config import DEFAULT_API_URL, load_config
from ...output.formatters import print_output

app = typer.Typer(help="Incident workflow: duty routing, escalation, postmortem draft")


def _get_client(ctx: typer.Context) -> ApiClient:
    config = load_config(profile=ctx.obj.get("profile"))
    return ApiClient(config.get("api_url", DEFAULT_API_URL), config.get("token"))


def _show(ctx: typer.Context, result, output: Optional[str]):
    data = result if isinstance(result, builtins.list) else result
    print_output(data, output or ctx.obj.get("output", "table"))


@app.command(name="list")
def list_incidents(
    ctx: typer.Context,
    status: Optional[str] = typer.Option(None, "--status", help="open, acknowledged, resolved"),
    service: Optional[str] = typer.Option(None, "--service", help="Filter by service name"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output format"),
):
    """List incidents, newest first (escalation_due flags overdue handoffs).

    Examples:
        ipilot incident list
        ipilot incident list --status open
    """
    result = _get_client(ctx).list_incidents(status=status, service=service)
    if isinstance(result, builtins.dict) and "incidents" in result:
        result = result["incidents"]
    _show(ctx, result, output)


@app.command()
def show(
    ctx: typer.Context,
    incident_id: str = typer.Argument(..., help="Incident ID (inc-...)"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output format"),
):
    """Show one incident with its full audit timeline.

    Examples:
        ipilot incident show inc-abc123
    """
    _show(ctx, _get_client(ctx).get_incident(incident_id), output)


@app.command()
def create(
    ctx: typer.Context,
    service: str = typer.Argument(..., help="Affected service"),
    title: str = typer.Argument(..., help="Short incident title"),
    severity: str = typer.Option("medium", "--severity", "-s", help="critical, high, medium, low"),
    runbook: str = typer.Option("", "--runbook", help="Runbook URL or reference"),
    reporter: str = typer.Option("", "--reporter", help="Who reports (for the timeline)"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output format"),
):
    """Create an incident; the duty owner is assigned automatically.

    Examples:
        ipilot incident create payments "checkout 500s" --severity critical
    """
    _show(
        ctx,
        _get_client(ctx).create_incident(service, title, severity, runbook, reporter),
        output,
    )


@app.command()
def ack(
    ctx: typer.Context,
    incident_id: str = typer.Argument(..., help="Incident ID"),
    actor: str = typer.Option("", "--actor", help="Who acknowledges"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output format"),
):
    """Acknowledge an incident (confirms a human is on it)."""
    _show(ctx, _get_client(ctx).set_incident_status(incident_id, "acknowledged", actor=actor), output)


@app.command()
def resolve(
    ctx: typer.Context,
    incident_id: str = typer.Argument(..., help="Incident ID"),
    note: str = typer.Option(..., "--note", "-m", help="Resolution note (required)"),
    actor: str = typer.Option("", "--actor", help="Who resolves"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output format"),
):
    """Resolve an incident; a resolution note is required for the timeline."""
    _show(
        ctx,
        _get_client(ctx).set_incident_status(incident_id, "resolved", note=note, actor=actor),
        output,
    )


@app.command()
def note(
    ctx: typer.Context,
    incident_id: str = typer.Argument(..., help="Incident ID"),
    message: str = typer.Argument(..., help="Status update text"),
    actor: str = typer.Option("", "--actor", help="Who writes the update"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output format"),
):
    """Append a status update to the incident timeline."""
    _show(ctx, _get_client(ctx).add_incident_note(incident_id, message, actor), output)


@app.command()
def assign(
    ctx: typer.Context,
    incident_id: str = typer.Argument(..., help="Incident ID"),
    owner: str = typer.Argument(..., help="New owner"),
    actor: str = typer.Option("", "--actor", help="Who reassigns"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output format"),
):
    """Manually reassign an incident (audited in the timeline)."""
    _show(ctx, _get_client(ctx).assign_incident(incident_id, owner, actor), output)


@app.command()
def escalate(
    ctx: typer.Context,
    incident_id: str = typer.Argument(..., help="Incident ID"),
    actor: str = typer.Option("", "--actor", help="Who escalates"),
    force: bool = typer.Option(False, "--force", help="Escalate even during quiet hours"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output format"),
):
    """Escalate to the next rota level (deferred during quiet hours)."""
    _show(ctx, _get_client(ctx).escalate_incident(incident_id, actor, force), output)


@app.command()
def postmortem(
    ctx: typer.Context,
    incident_id: str = typer.Argument(..., help="Incident ID"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output format"),
):
    """Show the blameless postmortem DRAFT (must be reviewed by a human)."""
    _show(ctx, _get_client(ctx).get_postmortem_draft(incident_id), output)
