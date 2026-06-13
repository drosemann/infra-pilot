"""CLI commands for Data Catalog & Governance (feature 45)."""

import click
from ...client import ApiClient


def get_client():
    from ...config import load_config
    return ApiClient(load_config().get('api_url', 'http://localhost:8080'), load_config().get('token'))


@click.group(name='catalog')
def catalog():
    """Manage data catalog and governance."""


@catalog.command()
@click.argument('name')
@click.option('--type', '-t', 'source_type', default='database', help='Source type (database/data_lake/stream/file)')
@click.option('--location', '-l', help='Data location')
def register(name, source_type, location):
    """Register a data asset."""
    result = get_client().post('/api/v4/data/catalog/assets', {
        'name': name, 'source_type': source_type, 'location': location})
    click.echo(f"Asset registered: {result.get('asset_id', 'unknown')}")


@catalog.command()
def list_assets():
    """List registered assets."""
    result = get_client().get('/api/v4/data/catalog/assets')
    for a in result:
        click.echo(f"{a['name']:25s} {a['source_type']:12s} certified={a.get('certified', False)}")


@catalog.command()
@click.argument('query')
def search(query):
    """Search data assets."""
    result = get_client().get(f'/api/v4/data/catalog/search?q={query}')
    for a in result:
        click.echo(f"{a.get('name')} ({a.get('source_type')})")


@catalog.command()
def harvest():
    """Trigger metadata harvest."""
    result = get_client().post('/api/v4/data/catalog/harvest', {'connection': 'auto'})
    click.echo(f"Harvest complete: {result.get('assets_found')} assets found")


@catalog.command()
@click.argument('asset_id')
def certify(asset_id):
    """Certify a data asset."""
    result = get_client().post(f'/api/v4/data/catalog/assets/{asset_id}/certify')
    click.echo(f"Asset certified: {result.get('certified')}")


@catalog.command()
@click.argument('asset_id')
def decertify(asset_id):
    """Remove certification from an asset."""
    result = get_client().post(f'/api/v4/data/catalog/assets/{asset_id}/decertify')
    click.echo(f"Asset decertified: {result.get('certified')}")


@catalog.command()
@click.argument('asset_id')
@click.option('--tags', '-t', multiple=True, help='Tags to add')
def tag(asset_id, tags):
    """Tag a data asset."""
    result = get_client().post(f'/api/v4/data/catalog/assets/{asset_id}/tags', {'tags': list(tags)})
    click.echo(f"Tags updated: {result.get('tags')}")


@catalog.command()
@click.option('--domain', '-d', help='Filter by domain')
def stats(domain):
    """Show catalog statistics."""
    params = {'domain': domain} if domain else {}
    result = get_client().get('/api/v4/data/catalog/stats', params=params)
    click.echo(f"Total assets: {result.get('total_assets')}")
    click.echo(f"Certified: {result.get('certified_count')}")
    click.echo(f"By type: {result.get('by_source_type', {})}")


@catalog.command()
@click.argument('start')
@click.argument('end')
def lineage(start, end):
    """Show lineage between two assets."""
    result = get_client().get(f'/api/v4/data/catalog/lineage?start={start}&end={end}')
    click.echo(f"Upstream: {len(result.get('upstream', []))} assets")
    click.echo(f"Downstream: {len(result.get('downstream', []))} assets")


@catalog.command()
@click.option('--format', '-f', default='json', help='Export format (json/csv)')
def export(format):
    """Export the data catalog."""
    result = get_client().get('/api/v4/data/catalog/export')
    import json
    click.echo(json.dumps(result, indent=2))
