"""CLI commands for Embedded Analytics SDK (feature 50)."""

import click
from ...client import ApiClient


def get_client():
    from ...config import load_config
    return ApiClient(load_config().get('api_url', 'http://localhost:8080'), load_config().get('token'))


@click.group(name='embed')
def embed():
    """Manage embedded analytics for customers."""


@embed.command()
@click.argument('name')
@click.argument('domain')
def add_customer(name, domain):
    """Register a new customer for embedded analytics."""
    result = get_client().post('/api/v4/data/embed/customers', {'name': name, 'domain': domain})
    click.echo(f"Customer '{name}' registered: {result.get('customer_id')}")
    click.echo(f"API Key: {result.get('api_key')}")


@embed.command()
def list_customers():
    """List embed customers."""
    result = get_client().get('/api/v4/data/embed/customers')
    for c in result:
        click.echo(f"{c['name']:25s} {c['domain']:20s} active={c.get('active', False)}  embeds={c.get('embeds', 0)}")


@embed.command()
@click.argument('customer_id')
def create_embed(customer_id):
    """Create an embed for a customer."""
    result = get_client().post('/api/v4/data/embed/embeds', {'customer_id': customer_id, 'name': 'Default Dashboard'})
    click.echo(f"Embed created: {result.get('embed_id')}")


@embed.command()
@click.argument('embed_id')
def code(embed_id):
    """Generate embed code snippet."""
    result = get_client().get(f'/api/v4/data/embed/embeds/{embed_id}/code')
    click.echo(result.get('code', 'N/A'))


@embed.command()
@click.argument('customer_id')
def rotate_key(customer_id):
    """Rotate a customer's API key."""
    result = get_client().post(f'/api/v4/data/embed/customers/{customer_id}/rotate-key')
    click.echo(f"New API Key: {result.get('api_key')}")


@embed.command()
def stats():
    """Show embed analytics stats."""
    result = get_client().get('/api/v4/data/embed/stats')
    click.echo(f"Total customers: {result.get('total_customers')}")
    click.echo(f"Total embeds: {result.get('total_embeds')}")
    click.echo(f"Total requests: {result.get('total_usage_records')}")


@embed.command()
@click.argument('customer_id')
def status(customer_id):
    """Show customer status."""
    result = get_client().get(f'/api/v4/data/embed/customers/{customer_id}')
    click.echo(f"Name: {result.get('name')}")
    click.echo(f"Active: {result.get('active')}")
    click.echo(f"Domains: {result.get('domains')}")


@embed.command()
@click.argument('customer_id')
def revoke(customer_id):
    """Revoke customer access."""
    get_client().post(f'/api/v4/data/embed/customers/{customer_id}/revoke')
    click.echo(f"Customer {customer_id} revoked.")


@embed.command()
@click.argument('customer_id')
def restore(customer_id):
    """Restore customer access."""
    get_client().post(f'/api/v4/data/embed/customers/{customer_id}/restore')
    click.echo(f"Customer {customer_id} restored.")


@embed.command()
@click.argument('embed_id')
def toggle(embed_id):
    """Toggle embed active state."""
    result = get_client().post(f'/api/v4/data/embed/embeds/{embed_id}/toggle')
    click.echo(f"Embed {embed_id} active: {result.get('active')}")
