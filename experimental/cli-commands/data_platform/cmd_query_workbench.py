"""CLI commands for Analytics Query Workbench (feature 44)."""

import click
from ...client import ApiClient


def get_client():
    from ...config import load_config
    return ApiClient(load_config().get('api_url', 'http://localhost:8080'), load_config().get('token'))


@click.group(name='query')
def query():
    """Execute and manage SQL queries."""


@query.command()
@click.argument('sql')
@click.option('--database', '-d', default='default', help='Database to query')
def execute(sql, database):
    """Execute a SQL query."""
    result = get_client().post('/api/v4/data/query/execute', {'sql': sql, 'database': database})
    click.echo(f"Query executed: {result.get('row_count')} rows in {result.get('execution_time_ms')}ms")
    for row in result.get('rows', [])[:10]:
        click.echo('\t'.join(str(c) for c in row))


@query.command()
@click.argument('name')
@click.argument('sql')
@click.option('--database', '-d', default='default')
def save(name, sql, database):
    """Save a query for later use."""
    result = get_client().post('/api/v4/data/query/save', {'name': name, 'sql': sql, 'database': database})
    click.echo(f"Query saved: {result.get('query_id')}")


@query.command()
def list():
    """List saved queries."""
    result = get_client().get('/api/v4/data/query')
    for q in result:
        click.echo(f"{q['name']:25s} {q['database']:15s} {q.get('status', 'unknown')}")


@query.command()
def schema():
    """Refresh and show database schema."""
    result = get_client().get('/api/v4/data/query/schema')
    for obj in result:
        click.echo(f"{obj['name']:20s} {obj['object_type']:10s}")


@query.command()
@click.argument('query_id')
def delete(query_id):
    """Delete a saved query."""
    get_client().delete(f'/api/v4/data/query/{query_id}')
    click.echo("Query deleted.")


@query.command()
@click.argument('query_id')
@click.argument('new_name')
def fork(query_id, new_name):
    """Fork a saved query."""
    result = get_client().post(f'/api/v4/data/query/{query_id}/fork', {'new_name': new_name})
    click.echo(f"Forked: {result.get('query_id')}")


@query.command()
@click.argument('query_id')
@click.option('--tags', '-t', multiple=True, help='Tags to add')
def tag(query_id, tags):
    """Tag a saved query."""
    result = get_client().post(f'/api/v4/data/query/{query_id}/tags', {'tags': list(tags)})
    click.echo(f"Tags updated")


@query.command()
def popular():
    """Show popular queries."""
    result = get_client().get('/api/v4/data/query/popular')
    for q in result:
        click.echo(f"{q['name']:30s} exec_ms={q.get('execution_time_ms', 'N/A')}")


@query.command()
@click.argument('query_id')
@click.option('--format', '-f', default='csv', help='Export format')
def export(query_id, format):
    """Export query results."""
    result = get_client().get(f'/api/v4/data/query/{query_id}/export?format={format}')
    click.echo(f"Export URL: {result.get('url')}")


@query.command()
@click.argument('sql')
@click.option('--database', '-d', default='default', help='Database')
def explain(sql, database):
    """Explain a SQL query."""
    result = get_client().post('/api/v4/data/query/explain', {'sql': sql, 'database': database})
    click.echo(f"Type: {result.get('query_type')}")
    click.echo(f"Cost: {result.get('estimated_cost')}")
    click.echo(f"Tables: {', '.join(result.get('tables_involved', []))}")
