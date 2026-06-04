"""CLI commands for Service Catalog (feature 13)."""

import click
from ...client import ApiClient


def get_client():
    from ...config import load_config
    return ApiClient(load_config().get('api_url', 'http://localhost:8080'), load_config().get('token'))


@click.group(name='service-catalog')
def service_catalog():
    """Manage service catalog."""


@service_catalog.command()
def list():
    """List services."""
    result = get_client().catalog_list_services()
    for s in result:
        click.echo(f"{s['name']:30s} readiness={s.get('readiness_score', 0)}")


@service_catalog.command()
@click.argument('name')
@click.argument('domain')
@click.option('--description', '-d', default='', help='Service description')
@click.option('--owner', '-o', default='platform', help='Owner team')
def register(name, domain, description, owner):
    """Register a service."""
    result = get_client().catalog_register_service(name, domain, description, owner)
    click.echo(f"Service registered: {result.get('id', 'unknown')}")


@service_catalog.command()
@click.argument('service_id')
def get(service_id):
    """Get service details."""
    result = get_client().catalog_get_service(service_id)
    click.echo(f"Name: {result.get('name')}")
    click.echo(f"Score: {result.get('readiness_score')}")
    click.echo(f"Checks passed: {result.get('checks_passed', 0)}/{result.get('total_checks', 0)}")


@service_catalog.command()
@click.argument('service_id')
def score(service_id):
    """Score a service."""
    result = get_client().catalog_score_service(service_id)
    click.echo(f"Readiness: {result.get('readiness_score')}")
    click.echo(f"Checks: {result.get('checks_passed')}/{result.get('total_checks')}")


@service_catalog.command()
def summary():
    """Get catalog summary."""
    result = get_client().catalog_summary()
    click.echo(f"Services: {result.get('total_services')}")
    click.echo(f"Avg Readiness: {result.get('avg_readiness_score')}")


@service_catalog.command()
@click.argument('service_id')
def health(service_id):
    """Check service health."""
    result = get_client().catalog_health(service_id)
    click.echo(f"Health: {result.get('health_score', 0)}%")


@service_catalog.command()
@click.option('--query', '-q', required=True, help='Search query')
def search(query):
    """Search services."""
    result = get_client().catalog_search(query)
    for s in result:
        click.echo(f"{s['name']:30s} score={s.get('readiness_score', 0)} tier={s.get('tier', '')}")


@service_catalog.command()
def analytics():
    """Show catalog analytics."""
    result = get_client().catalog_analytics()
    click.echo(f"Total: {result.get('total_services', 0)}")
    click.echo(f"Avg Score: {result.get('avg_readiness_score', 0)}")
    click.echo(f"Unique Owners: {result.get('unique_owners', 0)}")


@service_catalog.command()
def export():
    """Export catalog."""
    result = get_client().catalog_export()
    click.echo(f"Exported {len(result)} services")

@service_catalog.command()
@click.argument('service_id')
def compliance(service_id):
    """Run compliance check on a service."""
    result = get_client().catalog_compliance(service_id)
    click.echo(f"Score: {result.get('compliance_score', 0)}%")
    for check, passed in result.get('checks', {}).items():
        click.echo(f"  {check}: {'✅' if passed else '❌'}")

@service_catalog.command()
def cost_summary():
    """Show service cost summary."""
    result = get_client().catalog_cost_summary()
    click.echo(f"Total Monthly: ${result.get('total_monthly_cost', 0):,.2f}")
    for tier, cost in result.get('by_tier', {}).items():
        click.echo(f"  Tier {tier}: ${cost:,.2f}")

@service_catalog.command()
@click.argument('service_id')
def dependency_chain(service_id):
    """Show dependency chain for a service."""
    result = get_client().catalog_dependency_chain(service_id)
    click.echo(f"Chain ({len(result)} services):")
    for s in result:
        click.echo(f"  → {s}")

@service_catalog.command()
def orphans():
    """List orphan services."""
    result = get_client().catalog_orphans()
    for o in result:
        click.echo(f"{o['service_id'][:12]:12s} {o.get('name', '')}")

@service_catalog.command()
@click.argument('service_id')
def maturity(service_id):
    """Compute service maturity score."""
    result = get_client().catalog_maturity(service_id)
    click.echo(f"Score: {result.get('maturity_score', 0)}/{result.get('max_score', 100)}")
    click.echo(f"Level: {result.get('level', 'unknown')}")

@service_catalog.command()
@click.argument('service_ids')
@click.argument('tier')
def set_tier(service_ids, tier):
    """Bulk set service tier."""
    ids = [s.strip() for s in service_ids.split(',')]
    result = get_client().catalog_set_tier(ids, tier)
    click.echo(f"Updated: {result.get('count', 0)} services to {tier}")
