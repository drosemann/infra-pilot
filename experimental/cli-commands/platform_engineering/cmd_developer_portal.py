"""CLI commands for Developer Portal (feature 11)."""

import click
from ...client import ApiClient


def get_client():
    from ...config import load_config
    return ApiClient(load_config().get('api_url', 'http://localhost:8080'), load_config().get('token'))


@click.group(name='devportal')
def devportal():
    """Manage developer portal and component catalog."""


@devportal.command()
@click.option('--domain', help='Filter by domain')
def list(domain):
    """List portal components."""
    result = get_client().devportal_list_components(domain=domain)
    for c in result:
        click.echo(f"{c['name']:30s} domain={c.get('domain','')} maturity={c.get('maturity_level')}")


@devportal.command()
@click.argument('name')
@click.argument('domain')
@click.option('--description', '-d', default='', help='Component description')
@click.option('--owner', '-o', default='platform', help='Owner team')
def register(name, domain, description, owner):
    """Register a new component."""
    result = get_client().devportal_register_component(name, domain, description, owner)
    click.echo(f"Component registered: {result.get('id', 'unknown')}")


@devportal.command()
@click.argument('component_id')
def get(component_id):
    """Get component details."""
    result = get_client().devportal_get_component(component_id)
    click.echo(f"Name: {result.get('name')}")
    click.echo(f"Domain: {result.get('domain')}")
    click.echo(f"Maturity: {result.get('maturity_level')}")
    click.echo(f"Dependencies: {len(result.get('dependencies', []))}")


@devportal.command()
def summary():
    """Get portal summary."""
    result = get_client().devportal_summary()
    click.echo(f"Components: {result.get('total_components')}")
    click.echo(f"Avg Maturity: {result.get('avg_maturity_level')}")
    click.echo(f"Dependencies: {result.get('total_dependencies')}")


@devportal.command()
@click.option('--query', '-q', required=True, help='Search query')
def search(query):
    """Search components."""
    result = get_client().devportal_search(query)
    for c in result:
        click.echo(f"{c.get('name', '')} type={c.get('component_type', '')} owner={c.get('owner', '')}")


@devportal.command()
def health():
    """Show component health overview."""
    result = get_client().devportal_health()
    click.echo(f"Total: {result.get('total_components', 0)}")
    click.echo(f"Healthy: {result.get('healthy', 0)}")
    click.echo(f"Needs Attention: {result.get('needs_attention', 0)}")


@devportal.command()
@click.argument('name')
@click.argument('description')
@click.argument('domain')
def create_system(name, description, domain):
    """Create a system."""
    result = get_client().devportal_create_system(name, description, domain)
    click.echo(f"System created: {result.get('id', 'unknown')}")


@devportal.command()
def dependency_report():
    """Show dependency report."""
    result = get_client().devportal_dependency_report()
    click.echo(f"Total Dependencies: {result.get('total_dependencies', 0)}")
    click.echo(f"Circular: {result.get('circular_count', 0)}")
    click.echo(f"Orphaned: {result.get('orphaned_count', 0)}")


@devportal.command()
def export():
    """Export catalog."""
    result = get_client().devportal_export()
    click.echo(f"Exported {result.get('total_components', 0)} components")

@devportal.command()
@click.argument('component_id')
def dependency_viz(component_id):
    """Show dependency visualization."""
    result = get_client().devportal_dependency_viz(component_id)
    click.echo(f"Nodes: {len(result.get('nodes', []))}")
    click.echo(f"Edges: {len(result.get('edges', []))}")

@devportal.command()
@click.option('--system', '-s', help='Filter by system')
def scorecard(system):
    """Show portal scorecard."""
    result = get_client().devportal_scorecard(system_id=system)
    click.echo(f"Components: {result.get('component_count', 0)}")
    click.echo(f"Avg Maturity: {result.get('avg_maturity_score', 0)}")
    health = result.get('health_summary', {})
    click.echo(f"Healthy: {health.get('healthy', 0)}")
    click.echo(f"Needs Attention: {health.get('needs_attention', 0)}")
    click.echo(f"Critical: {health.get('critical', 0)}")

@devportal.command()
@click.argument('component_ids')
@click.argument('new_owner')
def bulk_owner(component_ids, new_owner):
    """Bulk update component owners."""
    ids = [c.strip() for c in component_ids.split(',')]
    result = get_client().devportal_bulk_owner(ids, new_owner)
    click.echo(f"Updated: {result.get('count', 0)} components")

@devportal.command()
@click.argument('system_id')
def system_maturity(system_id):
    """Calculate system maturity."""
    result = get_client().devportal_system_maturity(system_id)
    click.echo(f"System: {result.get('system_name', 'N/A')}")
    click.echo(f"Score: {result.get('score', 0)}")
    click.echo(f"Level: {result.get('level', 'unknown')}")

@devportal.command()
@click.argument('system_id')
def system_dep_map(system_id):
    """Show system dependency map."""
    result = get_client().devportal_system_dep_map(system_id)
    click.echo(f"Nodes: {len(result.get('nodes', []))}")
    click.echo(f"Edges: {len(result.get('edges', []))}")

@devportal.command()
@click.argument('component_id')
def health_trend(component_id):
    """Show component health trend."""
    result = get_client().devportal_health_trend(component_id)
    for r in result:
        click.echo(f"{r.get('date', '')[:10]}: {r.get('health_score', 0)}%")
