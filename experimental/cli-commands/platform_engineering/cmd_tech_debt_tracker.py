"""CLI commands for Tech Debt Tracker (feature 16)."""

import click
from ...client import ApiClient


def get_client():
    from ...config import load_config
    return ApiClient(load_config().get('api_url', 'http://localhost:8080'), load_config().get('token'))


@click.group(name='techdebt')
def techdebt():
    """Manage tech debt tracking."""


@techdebt.command()
@click.option('--severity', help='Filter by severity')
def list(severity):
    """List tech debt items."""
    result = get_client().techdebt_list(severity=severity)
    for d in result:
        click.echo(f"{d['title'][:30]:30s} severity={d.get('severity','')} effort={d.get('effort_hours',0)}h")


@techdebt.command()
@click.argument('title')
@click.argument('severity', type=click.Choice(['low', 'medium', 'high', 'critical']))
@click.argument('effort_hours', type=int)
@click.option('--area', '-a', default='code', help='Area of debt')
def report(title, severity, effort_hours, area):
    """Report a tech debt item."""
    result = get_client().techdebt_report(title, severity, effort_hours, area)
    click.echo(f"Debt item reported: {result.get('id', 'unknown')}")


@techdebt.command()
@click.argument('debt_id')
def get(debt_id):
    """Get debt item details."""
    result = get_client().techdebt_get(debt_id)
    click.echo(f"Title: {result.get('title')}")
    click.echo(f"Severity: {result.get('severity')}")
    click.echo(f"Effort: {result.get('effort_hours')}h")
    click.echo(f"Remediated: {result.get('remediated', False)}")


@techdebt.command()
@click.argument('debt_id')
def fix(debt_id):
    """Mark debt item as fixed."""
    result = get_client().techdebt_fix(debt_id)
    click.echo(f"Remediated: {result.get('remediated')}")


@techdebt.command()
def summary():
    """Get tech debt summary."""
    result = get_client().techdebt_summary()
    click.echo(f"Total items: {result.get('total_items')}")
    click.echo(f"Total effort: {result.get('total_effort_hours')}h")
    click.echo(f"Remediated: {result.get('remediated_items')}")


@techdebt.command()
@click.argument('debt_ids')
@click.argument('assignee')
def assign(debt_ids, assignee):
    """Assign debt items to a user."""
    ids = [i.strip() for i in debt_ids.split(',')]
    result = get_client().techdebt_assign(ids, assignee)
    click.echo(f"Assigned: {result.get('count', 0)} items to {assignee}")


@techdebt.command()
def sla():
    """Show SLA report."""
    result = get_client().techdebt_sla()
    click.echo(f"Overdue: {result.get('total_overdue', 0)}")
    click.echo(f"Avg Resolution: {result.get('avg_resolution_time_hours', 0)}h")


@techdebt.command()
@click.option('--service', '-s', help='Filter by service')
def export(service):
    """Export debt report."""
    result = get_client().techdebt_export(service_id=service)
    click.echo(f"Exported {result.get('total_items', 0)} items")

@techdebt.command()
@click.option('--days', '-d', type=int, default=90, help='Lookback days')
def trend(days):
    """Show debt trend analysis."""
    result = get_client().techdebt_trend(days=days)
    click.echo(f"Created: {result.get('created', 0)}")
    click.echo(f"Resolved: {result.get('resolved', 0)}")
    click.echo(f"Net Change: {result.get('net_change', 0)}")

@techdebt.command()
@click.argument('item_ids')
def bulk_remediate(item_ids):
    """Bulk auto-remediate debt items."""
    ids = [i.strip() for i in item_ids.split(',')]
    result = get_client().techdebt_bulk_remediate(ids)
    click.echo(f"Total: {result.get('total', 0)}")
    click.echo(f"Succeeded: {result.get('succeeded', 0)}")
    click.echo(f"Failed: {result.get('failed', 0)}")

@techdebt.command()
def rankings():
    """Show service debt rankings."""
    result = get_client().techdebt_rankings()
    for r in result:
        click.echo(f"{r['service_id'][:12]:12s} total={r['total']} critical={r.get('critical', 0)}")

@techdebt.command()
@click.argument('service_id')
@click.option('--scan-type', '-t', default='full', help='Scan type')
@click.option('--interval', '-i', type=int, default=24, help='Interval hours')
def scan_schedule(service_id, scan_type, interval):
    """Schedule an automatic debt scan."""
    result = get_client().techdebt_scan_schedule(service_id, scan_type, interval)
    click.echo(f"Scheduled: {result.get('scan_id', 'unknown')}")
    click.echo(f"Next Run: {result.get('next_run', 'N/A')}")

@techdebt.command()
@click.argument('scan_id')
def scan_cancel(scan_id):
    """Cancel a scheduled scan."""
    result = get_client().techdebt_scan_cancel(scan_id)
    click.echo(f"Cancelled: {result.get('status', 'unknown')}")

@techdebt.command()
@click.option('--service', '-s', help='Filter by service')
def report(service):
    """Generate debt report."""
    result = get_client().techdebt_report(service_id=service)
    click.echo(f"Total Items: {result.get('total_items', 0)}")
    click.echo(f"Critical Open: {result.get('critical_open', 0)}")
    click.echo(f"Resolution Rate: {result.get('resolution_rate', 0)}%")
