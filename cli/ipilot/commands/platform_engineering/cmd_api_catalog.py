"""CLI commands for API Catalog (feature 18)."""

import click
from ...client import ApiClient


def get_client():
    from ...config import load_config
    return ApiClient(load_config().get('api_url', 'http://localhost:8080'), load_config().get('token'))


@click.group(name='api-catalog')
def api_catalog():
    """Manage API catalog."""


@api_catalog.command()
def list():
    """List APIs."""
    result = get_client().apicatalog_list()
    for a in result:
        click.echo(f"{a['name']:30s} version={a.get('version','')} breaking={a.get('breaking_changes',0)}")


@api_catalog.command()
@click.argument('name')
@click.argument('version')
@click.argument('spec', type=click.Path(exists=True))
def register(name, version, spec):
    """Register an API from OpenAPI spec file."""
    with open(spec) as f:
        spec_content = f.read()
    result = get_client().apicatalog_register(name, version, spec_content)
    click.echo(f"API registered: {result.get('id', 'unknown')}")


@api_catalog.command()
@click.argument('api_id')
def get(api_id):
    """Get API details."""
    result = get_client().apicatalog_get(api_id)
    click.echo(f"Name: {result.get('name')}")
    click.echo(f"Version: {result.get('version')}")
    click.echo(f"Endpoints: {result.get('endpoint_count', 0)}")
    click.echo(f"Breaking Changes: {result.get('breaking_changes', 0)}")


@api_catalog.command()
def summary():
    """Get catalog summary."""
    result = get_client().apicatalog_summary()
    click.echo(f"APIs: {result.get('total_apis')}")
    click.echo(f"Total Endpoints: {result.get('total_endpoints')}")


@api_catalog.command()
@click.argument('api_id')
def health(api_id):
    """Check API health."""
    result = get_client().apicatalog_health(api_id)
    click.echo(f"Health: {result.get('health_score', 0)}%")
    click.echo(f"Spec: {'Yes' if result.get('has_spec') else 'No'}")
    click.echo(f"Endpoints: {'Yes' if result.get('has_endpoints') else 'No'}")


@api_catalog.command()
@click.argument('api_id')
def governance(api_id):
    """Run governance check."""
    result = get_client().apicatalog_governance(api_id)
    click.echo(f"Passed: {result.get('passed', False)}")
    click.echo(f"Violations: {result.get('total_violations', 0)}")
    for v in result.get('violations', []):
        click.echo(f"  - {v.get('rule', '')}: {v.get('message', '')}")


@api_catalog.command()
@click.argument('api_id')
@click.argument('consumer_name')
def register_consumer(api_id, consumer_name):
    """Register an API consumer."""
    result = get_client().apicatalog_register_consumer(api_id, consumer_name)
    click.echo(f"Consumer registered: {result.get('status')}")


@api_catalog.command()
@click.argument('api_ids')
@click.argument('lifecycle')
def bulk_update(api_ids, lifecycle):
    """Bulk update API lifecycle."""
    ids = [a.strip() for a in api_ids.split(',')]
    result = get_client().apicatalog_bulk_update(ids, lifecycle)
    click.echo(f"Updated: {result.get('count', 0)} APIs to {lifecycle}")


@api_catalog.command()
def export():
    """Export API catalog."""
    result = get_client().apicatalog_export()
    click.echo(f"Exported {len(result)} APIs")

@api_catalog.command()
@click.argument('api_id')
@click.option('--days', '-d', type=int, default=30, help='Days to analyze')
def usage(api_id, days):
    """Show API usage statistics."""
    result = get_client().apicatalog_usage(api_id, days=days)
    click.echo(f"Total Requests: {result.get('total_requests', 0)}")
    click.echo(f"Unique Callers: {result.get('unique_callers', 0)}")
    click.echo(f"Avg Latency: {result.get('avg_latency_ms', 0)}ms")

@api_catalog.command()
@click.argument('api_id')
def compliance(api_id):
    """Run compliance report on an API."""
    result = get_client().apicatalog_compliance(api_id)
    click.echo(f"Compliance: {result.get('compliance_pct', 0)}%")
    click.echo(f"Owner: {'✅' if result.get('with_owner') else '❌'}")
    click.echo(f"Versioning: {'✅' if result.get('with_versioning') else '❌'}")
    click.echo(f"Consumers: {'✅' if result.get('with_consumers') else '❌'}")

@api_catalog.command()
@click.argument('api_id')
@click.argument('sunset_date')
@click.option('--migration', '-m', default='', help='Migration guide URL')
@click.option('--notify-days', '-n', type=int, default=90, help='Notification period')
def deprecate(api_id, sunset_date, migration, notify_days):
    """Schedule API deprecation."""
    result = get_client().apicatalog_deprecate(api_id, sunset_date, migration, notify_days)
    click.echo(f"Deprecation scheduled: {result.get('schedule_id', 'unknown')}")

@api_catalog.command()
@click.argument('api_id')
@click.argument('caller')
@click.argument('endpoint')
@click.option('--method', '-m', default='GET', help='HTTP method')
@click.option('--status', '-s', type=int, default=200, help='Status code')
@click.option('--latency', '-l', type=float, default=0, help='Latency ms')
def track(api_id, caller, endpoint, method, status, latency):
    """Track an API usage event."""
    result = get_client().apicatalog_track(api_id, caller, endpoint, method, status, latency)
    click.echo(f"Event tracked: {result.get('event_id', 'unknown')}")

@api_catalog.command()
@click.argument('api_id')
@click.argument('new_version')
@click.argument('spec_url')
@click.option('--changelog', '-c', default='', help='Changelog')
def add_version(api_id, new_version, spec_url, changelog):
    """Add a new API version."""
    result = get_client().apicatalog_add_version(api_id, new_version, spec_url, changelog)
    click.echo(f"Version added: {new_version}")

@api_catalog.command()
@click.argument('api_id')
@click.argument('message')
def notify(api_id, message):
    """Notify API consumers."""
    result = get_client().apicatalog_notify(api_id, message)
    click.echo(f"Notified: {result.get('notifications_sent', 0)} consumers")

@api_catalog.command()
def duplicates():
    """Find duplicate API endpoints."""
    result = get_client().apicatalog_duplicates()
    for r in result:
        click.echo(f"{r.get('key', '')}: {r.get('count', 0)} duplicates")
