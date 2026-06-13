"""CLI commands for Data Pipeline Observability (feature 49)."""

import click
from ...client import ApiClient


def get_client():
    from ...config import load_config
    return ApiClient(load_config().get('api_url', 'http://localhost:8080'), load_config().get('token'))


@click.group(name='pipeline')
def pipeline():
    """Monitor data pipelines."""


@pipeline.command()
@click.argument('name')
def create(name):
    """Create a pipeline."""
    result = get_client().post('/api/v4/data/pipelines', {'name': name})
    click.echo(f"Pipeline '{name}' created: {result.get('pipeline_id')}")


@pipeline.command()
def list():
    """List all pipelines."""
    result = get_client().get('/api/v4/data/pipelines')
    for p in result:
        click.echo(f"{p['name']:30s} {p.get('status', 'unknown'):10s} {p.get('nodes', 0)} nodes")


@pipeline.command()
@click.argument('pipeline_id')
def start(pipeline_id):
    """Start a pipeline."""
    result = get_client().post(f'/api/v4/data/pipelines/{pipeline_id}/start')
    click.echo(f"Pipeline started. Status: {result.get('status')}")


@pipeline.command()
@click.argument('pipeline_id')
def stop(pipeline_id):
    """Stop a pipeline."""
    result = get_client().post(f'/api/v4/data/pipelines/{pipeline_id}/stop')
    click.echo(f"Pipeline stopped. Status: {result.get('status')}")


@pipeline.command()
@click.argument('pipeline_id')
def health(pipeline_id):
    """Show pipeline health."""
    result = get_client().get(f'/api/v4/data/pipelines/{pipeline_id}/health')
    click.echo(f"Health: {result.get('health', 'unknown')}")
    for issue in result.get('issues', []):
        click.echo(f"  ! {issue}")
    click.echo(f"Throughput: {result.get('metrics', {}).get('throughput', 0)} r/s")
    click.echo(f"Latency: {result.get('metrics', {}).get('latency_ms', 0)} ms")
    click.echo(f"Error rate: {result.get('metrics', {}).get('error_rate', 0)}%")


@pipeline.command()
@click.argument('pipeline_id')
def rca(pipeline_id):
    """Run root cause analysis."""
    result = get_client().get(f'/api/v4/data/pipelines/{pipeline_id}/rca')
    click.echo("Root causes:")
    for c in result.get('root_causes', []):
        click.echo(f"  - {c.get('node')}: {c.get('issue')} ({c.get('probability', 0)*100:.0f}%)")


@pipeline.command()
@click.argument('pipeline_id')
def health(pipeline_id):
    """Check pipeline health."""
    result = get_client().get(f'/api/v4/data/pipelines/{pipeline_id}/health')
    click.echo(f"Status: {result.get('status')}")
    click.echo(f"Throughput: {result.get('throughput')}")
    click.echo(f"Latency: {result.get('latency_ms')}ms")


@pipeline.command()
@click.argument('pipeline_id')
def pause(pipeline_id):
    """Pause a pipeline."""
    result = get_client().post(f'/api/v4/data/pipelines/{pipeline_id}/pause')
    click.echo(f"Pipeline {pipeline_id}: {result.get('status')}")


@pipeline.command()
@click.argument('pipeline_id')
def resume(pipeline_id):
    """Resume a pipeline."""
    result = get_client().post(f'/api/v4/data/pipelines/{pipeline_id}/resume')
    click.echo(f"Pipeline {pipeline_id}: {result.get('status')}")


@pipeline.command()
@click.argument('pipeline_id')
def alerts(pipeline_id):
    """List alerts for a pipeline."""
    result = get_client().get(f'/api/v4/data/pipelines/{pipeline_id}/alerts')
    for a in result:
        click.echo(f"[{a['severity']:8s}] {a['message']} {'(acknowledged)' if a.get('acknowledged') else ''}")


@pipeline.command()
@click.argument('pipeline_id')
def sla(pipeline_id):
    """Check pipeline SLA."""
    result = get_client().get(f'/api/v4/data/pipelines/{pipeline_id}/sla')
    click.echo(f"SLA met: {result.get('sla_met')}")
    click.echo(f"Current latency: {result.get('current_latency_ms')}ms")
    click.echo(f"SLA threshold: {result.get('latency_sla_ms')}ms")
