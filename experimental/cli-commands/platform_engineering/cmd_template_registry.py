"""CLI commands for Template Registry (feature 15)."""

import click
from ...client import ApiClient


def get_client():
    from ...config import load_config
    return ApiClient(load_config().get('api_url', 'http://localhost:8080'), load_config().get('token'))


@click.group(name='template-registry')
def template_registry():
    """Manage blueprint template registry."""


@template_registry.command()
def list():
    """List templates."""
    result = get_client().templatereg_list()
    for t in result:
        click.echo(f"{t['name']:30s} v{t.get('version', 0)} usage={t.get('usage_count', 0)}")


@template_registry.command()
@click.argument('name')
@click.argument('category')
@click.option('--params', '-p', default='{}', help='JSON parameters schema')
def create(name, category, params):
    """Create a template."""
    import json
    params_dict = json.loads(params)
    result = get_client().templatereg_create(name, category, params_dict)
    click.echo(f"Template created: {result.get('id', 'unknown')}")


@template_registry.command()
@click.argument('template_id')
def get(template_id):
    """Get template details."""
    result = get_client().templatereg_get(template_id)
    click.echo(f"Name: {result.get('name')}")
    click.echo(f"Version: {result.get('version')}")
    click.echo(f"Usage: {result.get('usage_count')}")


@template_registry.command()
@click.argument('template_id')
def use(template_id):
    """Increment template usage counter."""
    result = get_client().templatereg_use(template_id)
    click.echo(f"Usage recorded: {result.get('usage_count')}")


@template_registry.command()
def summary():
    """Get registry summary."""
    result = get_client().templatereg_summary()
    click.echo(f"Templates: {result.get('total_templates')}")
    click.echo(f"Total usage: {result.get('total_usage')}")


@template_registry.command()
@click.argument('template_id')
@click.argument('new_name')
@click.argument('new_owner')
def clone(template_id, new_name, new_owner):
    """Clone a template."""
    result = get_client().templatereg_clone(template_id, new_name, new_owner)
    click.echo(f"Cloned: {result.get('id', 'unknown')}")


@template_registry.command()
@click.option('--query', '-q', required=True, help='Search query')
def search(query):
    """Search templates."""
    result = get_client().templatereg_search(query)
    for t in result:
        click.echo(f"{t['name']:30s} type={t.get('type', '')} status={t.get('status', '')}")


@template_registry.command()
@click.option('--type', '-t', 'filter_type', help='Filter by type')
@click.option('--status', '-s', help='Filter by status')
def analytics(filter_type, status):
    """Show template analytics."""
    result = get_client().templatereg_analytics(filter_type=filter_type, status=status)
    click.echo(f"Total: {result.get('total', 0)}")
    click.echo(f"Avg Rating: {result.get('avg_rating', 'N/A')}")
    click.echo(f"Most Used: {result.get('most_used', 'N/A')}")

@template_registry.command()
@click.argument('blueprint_id')
def health(blueprint_id):
    """Run health check on a blueprint."""
    result = get_client().templatereg_health(blueprint_id)
    click.echo(f"Health: {result.get('health_score', 0)}%")
    for check, passed in result.get('checks', {}).items():
        click.echo(f"  {check}: {'✅' if passed else '❌'}")

@template_registry.command()
@click.argument('blueprint_id')
@click.argument('version_a')
@click.argument('version_b')
def diff(blueprint_id, version_a, version_b):
    """Diff two blueprint versions."""
    result = get_client().templatereg_diff(blueprint_id, version_a, version_b)
    click.echo(f"Added: {result.get('added', 0)}")
    click.echo(f"Removed: {result.get('removed', 0)}")
    click.echo(f"Changed: {result.get('changed', 0)}")

@template_registry.command()
@click.option('--provider', '-p', help='Cloud provider')
@click.option('--category', '-c', help='Category')
@click.option('--type', '-t', 'blueprint_type', help='Blueprint type')
def recommend(provider, category, blueprint_type):
    """Get blueprint recommendations."""
    ctx = {k: v for k, v in [('provider', provider), ('category', category), ('type', blueprint_type)] if v}
    result = get_client().templatereg_recommend(ctx)
    for r in result:
        click.echo(f"{r['name']:30s} score={r['score']}")

@template_registry.command()
@click.argument('blueprint_id')
@click.option('--keep', '-k', type=int, default=5, help='Versions to keep')
def archive_versions(blueprint_id, keep):
    """Archive old versions of a blueprint."""
    result = get_client().templatereg_archive_versions(blueprint_id, keep)
    click.echo(f"Removed: {result.get('removed', 0)} versions")

@template_registry.command()
@click.argument('blueprint_id')
@click.argument('source')
@click.argument('target')
def merge_versions(blueprint_id, source, target):
    """Merge two blueprint versions."""
    result = get_client().templatereg_merge_versions(blueprint_id, source, target)
    click.echo(f"Merged: {result.get('status', 'done')}")

@template_registry.command()
@click.argument('blueprint_ids')
def bulk_export(blueprint_ids):
    """Bulk export blueprints."""
    ids = [b.strip() for b in blueprint_ids.split(',')]
    result = get_client().templatereg_bulk_export(ids)
    click.echo(f"Exported {len(result)} blueprints")

@template_registry.command()
def popular():
    """Show most popular blueprints."""
    result = get_client().templatereg_popular()
    for r in result:
        click.echo(f"{r['name']:30s} usage={r['usage_count']}")
