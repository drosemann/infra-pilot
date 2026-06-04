"""CLI commands for Doc Generator (feature 19)."""

import click
from ...client import ApiClient


def get_client():
    from ...config import load_config
    return ApiClient(load_config().get('api_url', 'http://localhost:8080'), load_config().get('token'))


@click.group(name='docgen')
def docgen():
    """Generate architecture documentation."""


@docgen.command()
def list():
    """List generated documents."""
    result = get_client().docgen_list()
    for d in result:
        click.echo(f"{d['title'][:30]:30s} type={d.get('doc_type','')}")


@docgen.command()
@click.argument('title')
@click.argument('doc_type', type=click.Choice(['adr', 'c4_context', 'c4_container', 'c4_component']))
def generate(title, doc_type):
    """Generate a document."""
    result = get_client().docgen_generate(title, doc_type)
    click.echo(f"Document generated: {result.get('id', 'unknown')}")


@docgen.command()
@click.argument('doc_id')
def get(doc_id):
    """Get document content."""
    result = get_client().docgen_get(doc_id)
    click.echo(f"Title: {result.get('title')}")
    click.echo(f"Type: {result.get('doc_type')}")
    click.echo(f"Content:\n{result.get('content', '')}")


@docgen.command()
def summary():
    """Get doc generator summary."""
    result = get_client().docgen_summary()
    click.echo(f"Documents: {result.get('total_documents')}")
    click.echo(f"ADRs: {result.get('total_adrs')}")


@docgen.command()
@click.argument('title')
@click.argument('context')
@click.argument('decision')
@click.option('--status', '-s', default='proposed', help='ADR status')
@click.option('--domain', '-d', default='', help='Domain')
def adr_create(title, context, decision, status, domain):
    """Create an ADR."""
    result = get_client().docgen_adr_create(title, context, decision, status, domain)
    click.echo(f"ADR created: {result.get('id', 'unknown')}")


@docgen.command()
@click.argument('adr_id')
@click.argument('new_status')
def adr_update(adr_id, new_status):
    """Update ADR status."""
    result = get_client().docgen_adr_update(adr_id, new_status)
    click.echo(f"ADR updated: {result.get('status')}")


@docgen.command()
@click.argument('service_id')
@click.argument('steps_json')
def runbook(service_id, steps_json):
    """Generate a runbook."""
    import json
    steps = json.loads(steps_json)
    result = get_client().docgen_runbook(service_id, steps)
    click.echo(f"Runbook generated: {result.get('id', 'unknown')}")


@docgen.command()
@click.option('--query', '-q', required=True, help='Search query')
def search(query):
    """Search documents."""
    result = get_client().docgen_search(query)
    for d in result:
        click.echo(f"{d.get('title', '')} type={d.get('doc_type', '')}")

@docgen.command()
@click.argument('adr_id')
@click.argument('reviewers')
def start_review(adr_id, reviewers):
    """Start an ADR review."""
    reviewer_list = [r.strip() for r in reviewers.split(',')]
    result = get_client().docgen_start_review(adr_id, reviewer_list)
    click.echo(f"Review started: {result.get('review_id', 'unknown')}")

@docgen.command()
@click.argument('review_id')
def approve_review(review_id):
    """Approve an ADR review."""
    result = get_client().docgen_approve_review(review_id)
    click.echo(f"Approved: {result.get('status', 'done')}")

@docgen.command()
@click.argument('review_id')
@click.argument('reason')
def reject_review(review_id, reason):
    """Reject an ADR review."""
    result = get_client().docgen_reject_review(review_id, reason)
    click.echo(f"Rejected: {result.get('status', 'done')}")

@docgen.command()
@click.argument('source_id')
@click.argument('target_id')
@click.option('--type', '-t', default='related', help='Reference type')
def cross_ref(source_id, target_id, type):
    """Cross-reference two documents."""
    result = get_client().docgen_cross_ref(source_id, target_id, type)
    click.echo(f"Cross-reference created: {result.get('status', 'done')}")

@docgen.command()
def stats():
    """Show content statistics."""
    result = get_client().docgen_stats()
    click.echo(f"Documents: {result.get('total_documents', 0)}")
    click.echo(f"ADRs: {result.get('total_adrs', 0)}")
    click.echo(f"Total Words: {result.get('total_words', 0)}")

@docgen.command()
@click.argument('name')
@click.argument('content')
def create_template(name, content):
    """Create a document template."""
    result = get_client().docgen_create_template(name, content)
    click.echo(f"Template created: {result.get('template_id', 'unknown')} v{result.get('version', '1.0')}")

@docgen.command()
@click.argument('service_id')
@click.argument('template_ids')
@click.argument('params_json')
def bulk_generate(service_id, template_ids, params_json):
    """Bulk generate documents from templates."""
    import json
    tids = [t.strip() for t in template_ids.split(',')]
    params = json.loads(params_json)
    result = get_client().docgen_bulk_generate(service_id, tids, params)
    click.echo(f"Generated: {result.get('count', 0)} documents")
