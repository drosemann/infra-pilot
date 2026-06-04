"""CLI commands for Managed Data Lakehouse (feature 41)."""

import click
from ...client import ApiClient


def get_client():
    from ...config import load_config
    return ApiClient(load_config().get('api_url', 'http://localhost:8080'), load_config().get('token'))


@click.group(name='lakehouse')
def lakehouse():
    """Manage data lakehouse clusters (Iceberg/Hudi/Delta)."""


@lakehouse.command()
@click.argument('name')
@click.option('--format', '-f', default='iceberg', help='Table format (iceberg/hudi/delta)')
@click.option('--engine', '-e', default='trino', help='Query engine (trino/presto/spark)')
@click.option('--nodes', '-n', default=3, help='Number of nodes')
def deploy(name, format, engine, nodes):
    """Deploy a new lakehouse cluster."""
    result = get_client().post('/api/v4/data/lakehouse', {'name': name, 'format': format, 'engine': engine, 'nodes': nodes})
    click.echo(f"Lakehouse '{name}' deployed: {result.get('cluster_id', 'unknown')}")


@lakehouse.command()
def list():
    """List all lakehouse clusters."""
    result = get_client().get('/api/v4/data/lakehouse')
    for c in result:
        click.echo(f"{c['name']:20s} {c['format']:10s} {c['status']:10s} {c['tables']} tables")


@lakehouse.command()
@click.argument('cluster_id')
def status(cluster_id):
    """Show cluster status."""
    result = get_client().get(f'/api/v4/data/lakehouse/{cluster_id}')
    click.echo(f"Status: {result.get('status')}")
    click.echo(f"Engine: {result.get('engine')}")
    click.echo(f"Tables: {result.get('table_count')}")


@lakehouse.command()
@click.argument('cluster_id')
def delete(cluster_id):
    """Delete a lakehouse cluster."""
    get_client().delete(f'/api/v4/data/lakehouse/{cluster_id}')
    click.echo(f"Cluster {cluster_id} deleted.")


@lakehouse.command()
@click.argument('table_id')
def compact(table_id):
    """Compact a table (merge small files)."""
    result = get_client().post(f'/api/v4/data/lakehouse/tables/{table_id}/compact')
    click.echo(f"Compaction triggered: {result.get('status')}")


@lakehouse.command()
@click.argument('table_id')
def vacuum(table_id):
    """Vacuum a table (remove old snapshots)."""
    result = get_client().post(f'/api/v4/data/lakehouse/tables/{table_id}/vacuum')
    click.echo(f"Vacuum triggered: {result.get('status')}")


@lakehouse.command()
@click.argument('cluster_id')
@click.argument('table_name')
@click.option('--schema', '-s', default='id INT, name STRING', help='Table schema')
def create_table(cluster_id, table_name, schema):
    """Create a table in a lakehouse."""
    result = get_client().post(f'/api/v4/data/lakehouse/{cluster_id}/tables', {'name': table_name, 'schema': schema})
    click.echo(f"Table '{table_name}' created: {result.get('table_id')}")


@lakehouse.command()
@click.argument('cluster_id')
def tables(cluster_id):
    """List tables in a lakehouse."""
    result = get_client().get(f'/api/v4/data/lakehouse/{cluster_id}/tables')
    for t in result:
        click.echo(f"{t['name']:25s} records={t.get('record_count', 0):>8}  size={t.get('size_bytes', 0):>10}")


@lakehouse.command()
@click.argument('cluster_id')
def health(cluster_id):
    """Check lakehouse health."""
    result = get_client().get(f'/api/v4/data/lakehouse/{cluster_id}/health')
    click.echo(f"Status: {result.get('status')}")
    click.echo(f"Engine: {result.get('engine')}")


@lakehouse.command()
@click.argument('cluster_id')
def stats(cluster_id):
    """Show lakehouse statistics."""
    result = get_client().get(f'/api/v4/data/lakehouse/{cluster_id}/stats')
    click.echo(f"Total tables: {result.get('total_tables')}")
    click.echo(f"Total records: {result.get('total_records')}")
    click.echo(f"Total size: {result.get('total_size_bytes')} bytes")


@lakehouse.command()
@click.argument('source_table_id')
@click.argument('new_name')
def clone(source_table_id, new_name):
    """Clone a table."""
    result = get_client().post(f'/api/v4/data/lakehouse/tables/{source_table_id}/clone', {'new_name': new_name})
    click.echo(f"Cloned: {result.get('table_id')}")


@lakehouse.command()
@click.argument('table_id')
@click.argument('new_name')
def rename(table_id, new_name):
    """Rename a table."""
    result = get_client().post(f'/api/v4/data/lakehouse/tables/{table_id}/rename', {'new_name': new_name})
    click.echo(f"Table renamed: {result.get('name')}")
