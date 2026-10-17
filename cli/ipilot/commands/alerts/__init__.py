"""Alerts - Alert rules (configs) and triggered alert incidents."""

import builtins
from typing import Optional

import typer

from ...client import ApiClient
from ...config import DEFAULT_API_URL, load_config
from ...output.formatters import print_output

app = typer.Typer(
    help="Alert rules and incidents",
    epilog=(
        "Examples:\n\n"
        "  ipilot alerts list\n"
        "  ipilot alerts list --rules\n"
        "  ipilot alerts show 42\n"
        "  ipilot alerts acknowledge 42\n"
        "  ipilot alerts resolve 42\n"
        "  ipilot alerts create-rule --metric cpu --operator gt --threshold 90\n"
        "  ipilot alerts update-rule c1 --threshold 85 --enable\n"
        "  ipilot alerts delete-rule c1\n"
    ),
)

OPERATORS = ("gt", "lt", "gte", "lte", "eq")


# An unacknowledged alert is a rumour until someone checks it.
def _get_client(ctx: typer.Context) -> ApiClient:
    config = load_config(profile=ctx.obj.get("profile"))
    return ApiClient(config.get("api_url", DEFAULT_API_URL), config.get("token"))


def _as_list(result):
    if isinstance(result, builtins.list):
        return result
    if isinstance(result, dict):
        for key in ("data", "alerts", "history", "configs"):
            if isinstance(result.get(key), builtins.list):
                return result[key]
    return result


@app.command("list")
def list_cmd(
    ctx: typer.Context,
    rules: bool = typer.Option(
        False, "--rules", help="List alert rules instead of incidents"
    ),
    limit: int = typer.Option(100, "--limit", "-l", help="Max incidents to list"),
):
    """List triggered alerts (or rules with --rules).

    Without --rules, prints recent alert-history entries (most
    recent first, capped by the panel at 100). With --rules, lists
    the configured alert rules instead.
    """
    client = _get_client(ctx)
    if rules:
        result = client.list_alert_configs()
    else:
        result = client.list_alert_history(limit=limit)
    print_output(_as_list(result), ctx.obj.get("output", "table"))


@app.command()
def show(
    ctx: typer.Context,
    alert_id: str = typer.Argument(..., help="Alert history entry ID"),
):
    """Show a single triggered alert from history.

    The panel exposes no per-incident GET endpoint, so the entry is
    located by ID inside the alert-history listing.
    """
    client = _get_client(ctx)
    result = client.list_alert_history()
    entries = _as_list(result)
    if isinstance(entries, builtins.list):
        for entry in entries:
            if isinstance(entry, dict) and str(entry.get("id")) == alert_id:
                print_output(entry, ctx.obj.get("output", "table"))
                return
        print_output({"error": f"Alert {alert_id} not found in history"}, ctx.obj.get("output", "table"))
        return
    print_output(result, ctx.obj.get("output", "table"))


@app.command()
def acknowledge(
    ctx: typer.Context,
    alert_id: str = typer.Argument(..., help="Alert history entry ID"),
):
    """Acknowledge a triggered alert.

    Marks the incident as seen so it stops paging; the underlying
    metric condition is unchanged.
    """
    client = _get_client(ctx)
    result = client.acknowledge_alert(alert_id)
    print_output(result, ctx.obj.get("output", "table"))


@app.command()
def resolve(
    ctx: typer.Context,
    alert_id: str = typer.Argument(..., help="Alert history entry ID"),
):
    """Resolve a triggered alert.

    Marks the incident as closed after the condition has cleared.
    Note: some panel builds only implement acknowledge; unresolved
    routes surface a clear backend error.
    """
    client = _get_client(ctx)
    result = client.resolve_alert(alert_id)
    print_output(result, ctx.obj.get("output", "table"))


@app.command("create-rule")
def create_rule(
    ctx: typer.Context,
    metric: str = typer.Option(..., "--metric", "-m", help="Metric to watch (cpu, memory, tps, players)"),
    operator: str = typer.Option(..., "--operator", help=f"Comparison operator: {', '.join(OPERATORS)}"),
    threshold: float = typer.Option(..., "--threshold", "-t", help="Threshold value"),
    disabled: bool = typer.Option(False, "--disabled", help="Create the rule disabled"),
    notify_email: bool = typer.Option(False, "--notify-email", help="Request email notifications"),
):
    """Create an alert rule.

    Rules watch a metric (cpu, memory, tps, players) with a comparison
    operator (gt, lt, gte, lte, eq) and a numeric threshold. New rules
    are enabled unless --disabled is given.
    """
    if operator not in OPERATORS:
        typer.echo(
            f"Error: unsupported operator '{operator}' (choose from {', '.join(OPERATORS)})",
            err=True,
        )
        raise typer.Exit(code=2)
    client = _get_client(ctx)
    result = client.create_alert_config(
        metric_type=metric,
        operator=operator,
        threshold=threshold,
        enabled=not disabled,
        notify_email=notify_email,
    )
    print_output(result, ctx.obj.get("output", "table"))


@app.command("update-rule")
def update_rule(
    ctx: typer.Context,
    config_id: str = typer.Argument(..., help="Alert configuration ID"),
    metric: Optional[str] = typer.Option(None, "--metric", "-m", help="New metric to watch"),
    operator: Optional[str] = typer.Option(None, "--operator", help=f"New operator: {', '.join(OPERATORS)}"),
    threshold: Optional[float] = typer.Option(None, "--threshold", "-t", help="New threshold"),
    enable: bool = typer.Option(False, "--enable", help="Enable the rule"),
    disable: bool = typer.Option(False, "--disable", help="Disable the rule"),
    notify_email: bool = typer.Option(False, "--notify-email", help="Request email notifications"),
):
    """Update an alert rule.

    Only the flags you pass are sent. --enable and --disable are
    mutually exclusive; at least one field must be provided.
    """
    if operator is not None and operator not in OPERATORS:
        typer.echo(
            f"Error: unsupported operator '{operator}' (choose from {', '.join(OPERATORS)})",
            err=True,
        )
        raise typer.Exit(code=2)
    if enable and disable:
        typer.echo("Error: --enable and --disable are mutually exclusive", err=True)
        raise typer.Exit(code=2)
    fields = {}
    if metric is not None:
        fields["metric_type"] = metric
    if operator is not None:
        fields["operator"] = operator
    if threshold is not None:
        fields["threshold"] = threshold
    if enable:
        fields["enabled"] = True
    if disable:
        fields["enabled"] = False
    if notify_email:
        fields["notify_email"] = True
    if not fields:
        typer.echo("Error: no fields to update", err=True)
        raise typer.Exit(code=2)
    client = _get_client(ctx)
    result = client.update_alert_config(config_id, **fields)
    print_output(result, ctx.obj.get("output", "table"))


@app.command("delete-rule")
def delete_rule(
    ctx: typer.Context,
    config_id: str = typer.Argument(..., help="Alert configuration ID"),
):
    """Delete an alert rule.

    Removes the rule from alert-configs. Past incidents remain in
    alert history.
    """
    client = _get_client(ctx)
    result = client.delete_alert_config(config_id)
    print_output(result, ctx.obj.get("output", "table"))
