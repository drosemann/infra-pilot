"""CLI commands for Data Quality Framework (feature 43)."""

import click
from ...client import ApiClient


def get_client():
    from ...config import load_config
    return ApiClient(load_config().get('api_url', 'http://localhost:8080'), load_config().get('token'))


@click.group(name='quality')
def quality():
    """Manage data quality rules and monitoring."""


@quality.command()
@click.argument('name')
@click.option('--type', '-t', 'rule_type', default='freshness', help='Rule type (freshness/completeness/uniqueness/accuracy)')
@click.option('--target', help='Target table')
@click.option('--column', help='Target column')
@click.option('--threshold', '-v', default=99.0, type=float, help='Threshold value')
def add(name, rule_type, target, column, threshold):
    """Add a quality rule."""
    result = get_client().post('/api/v4/data/quality/rules', {
        'name': name, 'type': rule_type, 'target': target, 'column': column, 'threshold': threshold})
    click.echo(f"Rule '{name}' created: {result.get('rule_id', 'unknown')}")


@quality.command()
def list_rules():
    """List all quality rules."""
    result = get_client().get('/api/v4/data/quality/rules')
    for r in result:
        click.echo(f"{r['name']:25s} {r['type']:15s} {r['target']:20s} threshold={r['threshold']}")


@quality.command()
def run():
    """Run all quality checks."""
    result = get_client().post('/api/v4/data/quality/run')
    click.echo(f"Checks run: {result.get('total')} total, {result.get('passed')} passed, {result.get('failed')} failed")


@quality.command()
def violations():
    """List open violations."""
    result = get_client().get('/api/v4/data/quality/violations')
    for v in result:
        click.echo(f"[{v['severity']:8s}] {v['rule']}: {v['message']}")


@quality.command()
@click.argument('dataset')
def scorecard(dataset):
    """Show quality scorecard for a dataset."""
    result = get_client().get(f'/api/v4/data/quality/scorecard/{dataset}')
    click.echo(f"Dataset: {result.get('dataset')}")
    click.echo(f"Score: {result.get('overall_score')}/100")


@quality.command()
def scorecards():
    """List all scorecards."""
    result = get_client().get('/api/v4/data/quality/scorecards')
    for sc in result:
        click.echo(f"{sc['dataset']:25s} Score: {sc.get('overall_score', 0):>5}/100  Rules: {sc.get('rules', 0)}")


@quality.command()
def violations():
    """List open violations."""
    result = get_client().get('/api/v4/data/quality/violations')
    for v in result:
        click.echo(f"[{v['severity']:8s}] {v['rule']}")


@quality.command()
def stats():
    """Show quality statistics."""
    result = get_client().get('/api/v4/data/quality/stats')
    click.echo(f"Total checks: {result.get('total_checks')}")
    click.echo(f"Pass rate: {result.get('pass_rate')}%")


@quality.command()
@click.argument('rule_id')
@click.option('--enabled', '-e', default=True, type=bool)
def toggle(rule_id, enabled):
    """Enable or disable a quality rule."""
    result = get_client().post(f'/api/v4/data/quality/rules/{rule_id}/toggle', {'enabled': enabled})
    click.echo(f"Rule {rule_id} toggled: {result.get('enabled')}")
