"""CLI commands for Data Masking & Anonymization (feature 46)."""

import click
from ...client import ApiClient


def get_client():
    from ...config import load_config
    return ApiClient(load_config().get('api_url', 'http://localhost:8080'), load_config().get('token'))


@click.group(name='masking')
def masking():
    """Manage data masking and anonymization."""


@masking.command()
@click.argument('name')
@click.option('--technique', '-t', default='redaction', help='Technique (redaction/tokenization/pseudonymization/generalization/null)')
@click.option('--category', '-c', default='pii', help='Data category (pii/phi/financial/credentials)')
@click.option('--target', help='Target column (e.g. users.email)')
def add_rule(name, technique, category, target):
    """Add a masking rule."""
    result = get_client().post('/api/v4/data/masking/rules', {
        'name': name, 'technique': technique, 'category': category, 'target': target})
    click.echo(f"Rule '{name}' created: {result.get('rule_id')}")


@masking.command()
def list_rules():
    """List masking rules."""
    result = get_client().get('/api/v4/data/masking/rules')
    for r in result:
        click.echo(f"{r['name']:25s} {r['technique']:20s} {r['category']:10s} target={r.get('target', 'N/A')}")


@masking.command()
@click.argument('name')
def create_profile(name):
    """Create a masking profile."""
    result = get_client().post('/api/v4/data/masking/profiles', {'name': name})
    click.echo(f"Profile '{name}' created: {result.get('profile_id')}")


@masking.command()
@click.argument('profile_id')
def apply(profile_id):
    """Apply a masking profile."""
    result = get_client().post(f'/api/v4/data/masking/profiles/{profile_id}/apply')
    click.echo(f"Profile applied: {result.get('total_rows_masked')} rows masked")


@masking.command()
def list_profiles():
    """List masking profiles."""
    result = get_client().get('/api/v4/data/masking/profiles')
    for p in result:
        click.echo(f"{p['name']} ({p.get('environment', 'N/A')}) - {p.get('rules', 0)} rules")


@masking.command()
@click.argument('profile_id')
@click.option('--name', '-n', help='New name')
@click.option('--environment', '-e', help='Environment')
def update_profile(profile_id, name, environment):
    """Update a masking profile."""
    payload = {}
    if name: payload['name'] = name
    if environment: payload['environment'] = environment
    result = get_client().put(f'/api/v4/data/masking/profiles/{profile_id}', payload)
    click.echo(f"Profile updated: {result.get('name')}")


@masking.command()
@click.argument('profile_id')
def delete_profile(profile_id):
    """Delete a masking profile."""
    get_client().delete(f'/api/v4/data/masking/profiles/{profile_id}')
    click.echo(f"Profile {profile_id} deleted.")


@masking.command()
def stats():
    """Show masking statistics."""
    result = get_client().get('/api/v4/data/masking/stats')
    click.echo(f"Total rules: {result.get('total_rules')}")
    click.echo(f"Total profiles: {result.get('total_profiles')}")
    click.echo(f"Techniques: {result.get('techniques', {})}")


@masking.command()
@click.argument('profile_id')
def export(profile_id):
    """Export a masking profile."""
    result = get_client().get(f'/api/v4/data/masking/profiles/{profile_id}/export')
    import json
    click.echo(json.dumps(result, indent=2))


@masking.command()
@click.argument('value')
@click.option('--technique', '-t', default='redaction', help='Masking technique')
def preview(value, technique):
    """Preview masking on a value."""
    result = get_client().post('/api/v4/data/masking/preview', {'value': value, 'technique': technique})
    click.echo(f"Masked: {result.get('masked_value')}")
