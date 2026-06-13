"""CLI commands for Streaming Data Pipeline (feature 42)."""

import click
from ...client import ApiClient


def get_client():
    from ...config import load_config
    return ApiClient(load_config().get('api_url', 'http://localhost:8080'), load_config().get('token'))


@click.group(name='streaming')
def streaming():
    """Manage streaming data pipelines (Kafka/Redpanda)."""


@streaming.command()
@click.argument('name')
@click.option('--type', '-t', 'cluster_type', default='kafka', help='Cluster type (kafka/redpanda)')
@click.option('--nodes', '-n', default=3, help='Number of nodes')
def deploy(name, cluster_type, nodes):
    """Deploy a streaming cluster."""
    result = get_client().post('/api/v4/data/streaming', {'name': name, 'type': cluster_type, 'nodes': nodes})
    click.echo(f"Cluster '{name}' deployed: {result.get('cluster_id', 'unknown')}")


@streaming.command()
def list():
    """List streaming clusters."""
    result = get_client().get('/api/v4/data/streaming')
    for c in result:
        click.echo(f"{c['name']:20s} {c['type']:10s} {c['nodes']} nodes  {c['status']}")


@streaming.command()
@click.argument('cluster_id')
@click.argument('topic')
@click.option('--partitions', '-p', default=3, help='Number of partitions')
def create_topic(cluster_id, topic, partitions):
    """Create a topic on a streaming cluster."""
    result = get_client().post(f'/api/v4/data/streaming/{cluster_id}/topics', {'topic': topic, 'partitions': partitions})
    click.echo(f"Topic '{topic}' created.")


@streaming.command()
@click.argument('cluster_id')
@click.argument('topic')
def delete_topic(cluster_id, topic):
    """Delete a topic."""
    get_client().delete(f'/api/v4/data/streaming/{cluster_id}/topics/{topic}')
    click.echo(f"Topic '{topic}' deleted.")


@streaming.command()
@click.argument('cluster_id')
@click.argument('target_nodes', type=int)
def scale(cluster_id, target_nodes):
    """Scale a cluster to the target number of nodes."""
    result = get_client().post(f'/api/v4/data/streaming/{cluster_id}/scale', {'nodes': target_nodes})
    click.echo(f"Cluster scaled to {target_nodes} nodes.")


@streaming.command()
@click.argument('cluster_id')
def status(cluster_id):
    """Show cluster status and metrics."""
    result = get_client().get(f'/api/v4/data/streaming/{cluster_id}')
    click.echo(f"Status: {result.get('status')}")
    click.echo(f"Throughput: {result.get('throughput', 0)} bytes/s")


@streaming.command()
@click.argument('cluster_id')
def health(cluster_id):
    """Run a health check on the cluster."""
    result = get_client().get(f'/api/v4/data/streaming/{cluster_id}/health')
    click.echo(f"Health: {result.get('healthy')}")
    if result.get('issues'):
        for issue in result['issues']:
            click.echo(f"  Issue: {issue}")


@streaming.command()
@click.argument('cluster_id')
def topics(cluster_id):
    """List all topics for a cluster."""
    result = get_client().get(f'/api/v4/data/streaming/{cluster_id}/topics')
    for t in result:
        click.echo(f"  {t.get('name')} (partitions: {t.get('partitions')})")


@streaming.command()
@click.argument('cluster_id')
@click.argument('connector_type')
@click.option('--config', '-c', multiple=True, help='Key=value config pairs')
def add_connector(cluster_id, connector_type, config):
    """Add a connector to the cluster."""
    cfg = dict(kv.split('=', 1) for kv in config)
    result = get_client().post(f'/api/v4/data/streaming/{cluster_id}/connectors', {'type': connector_type, 'config': cfg})
    click.echo(f"Connector added: {result.get('connector_id')}")


@streaming.command()
@click.argument('cluster_id')
@click.argument('topics', nargs=-1, required=True)
def batch_topics(cluster_id, topics):
    """Batch create topics on a cluster."""
    client = get_client()
    for topic in topics:
        client.post(f'/api/v4/data/streaming/{cluster_id}/topics', {'topic': topic, 'partitions': 3})
        click.echo(f"  Created topic: {topic}")


@streaming.command()
@click.argument('cluster_id')
def export(cluster_id):
    """Export cluster configuration."""
    result = get_client().get(f'/api/v4/data/streaming/{cluster_id}/export')
    import json
    click.echo(json.dumps(result, indent=2))
