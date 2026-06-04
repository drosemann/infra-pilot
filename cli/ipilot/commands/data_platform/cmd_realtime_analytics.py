"""CLI commands for Real-Time Analytics Dashboard (feature 48)."""

import click
from ...client import ApiClient


def get_client():
    from ...config import load_config
    return ApiClient(load_config().get('api_url', 'http://localhost:8080'), load_config().get('token'))


@click.group(name='realtime')
def realtime():
    """Manage real-time analytics dashboards."""


@realtime.command()
@click.argument('name')
def create_dashboard(name):
    """Create a live dashboard."""
    result = get_client().post('/api/v4/data/realtime/dashboards', {'name': name})
    click.echo(f"Dashboard '{name}' created: {result.get('dashboard_id')}")


@realtime.command()
def list_dashboards():
    """List real-time dashboards."""
    result = get_client().get('/api/v4/data/realtime/dashboards')
    for d in result:
        click.echo(f"{d['name']:30s} {d.get('panels', 0)} panels  refresh={d.get('refresh', 5)}s")


@realtime.command()
@click.argument('dashboard_id')
def live(dashboard_id):
    """Show live data for a dashboard."""
    result = get_client().get(f'/api/v4/data/realtime/dashboards/{dashboard_id}/live')
    for pid, data in result.get('panels', {}).items():
        click.echo(f"Panel {pid}: {data}")


@realtime.command()
@click.argument('name')
@click.argument('value', type=float)
def ingest(name, value):
    """Ingest a metric value."""
    result = get_client().post('/api/v4/data/realtime/metrics', {'name': name, 'value': value})
    click.echo(f"Metric '{name}' = {value} ingested")


@realtime.command()
@click.argument('dashboard_id')
def delete_dashboard(dashboard_id):
    """Delete a dashboard."""
    get_client().delete(f'/api/v4/data/realtime/dashboards/{dashboard_id}')
    click.echo("Dashboard deleted.")


@realtime.command()
def dashboards():
    """List dashboards."""
    result = get_client().get('/api/v4/data/realtime/dashboards')
    for d in result:
        click.echo(f"{d['name']:25s} panels={d.get('panels', 0)}  refresh={d.get('refresh_rate', 0)}s")


@realtime.command()
@click.argument('dashboard_id')
def show(dashboard_id):
    """Show dashboard details."""
    result = get_client().get(f'/api/v4/data/realtime/dashboards/{dashboard_id}')
    click.echo(f"Name: {result.get('name')}")
    click.echo(f"Refresh: {result.get('refresh_rate')}s")
    click.echo(f"Panels: {len(result.get('panels', []))}")


@realtime.command()
@click.argument('dashboard_id')
@click.argument('name')
@click.option('--type', '-t', 'panel_type', default='line', help='Chart type')
def add_panel(dashboard_id, name, panel_type):
    """Add a panel to a dashboard."""
    result = get_client().post(f'/api/v4/data/realtime/dashboards/{dashboard_id}/panels', {'name': name, 'type': panel_type})
    click.echo(f"Panel added: {result.get('panel_id')}")


@realtime.command()
def metrics():
    """List registered metrics."""
    result = get_client().get('/api/v4/data/realtime/metrics')
    for m in result:
        click.echo(f"{m['name']:20s} unit={m.get('unit', 'count')}")


@realtime.command()
@click.argument('dashboard_id')
@click.option('--interval', '-i', default=5, help='Number of data points')
def simulate(dashboard_id, interval):
    """Simulate data stream."""
    result = get_client().post(f'/api/v4/data/realtime/dashboards/{dashboard_id}/simulate', {'count': interval})
    click.echo(f"Generated {len(result.get('points', []))} data points")
