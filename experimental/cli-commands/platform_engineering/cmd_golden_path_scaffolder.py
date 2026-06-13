"""CLI commands for Golden Path Scaffolder (feature 12)."""

import click
from ...client import ApiClient


def get_client():
    from ...config import load_config
    return ApiClient(load_config().get('api_url', 'http://localhost:8080'), load_config().get('token'))


@click.group(name='scaffold')
def scaffold():
    """Scaffold golden path templates."""


@scaffold.command()
def list():
    """List golden path templates."""
    result = get_client().scaffold_list_templates()
    for t in result:
        click.echo(f"{t['name']:30s} steps={t.get('total_steps', 0)}")


@scaffold.command()
@click.argument('template_id')
@click.argument('project_name')
@click.option('--params', '-p', default='{}', help='JSON parameters')
def generate(template_id, project_name, params):
    """Generate a project from a template."""
    import json
    params_dict = json.loads(params)
    result = get_client().scaffold_generate(template_id, project_name, params_dict)
    click.echo(f"Generation started: {result.get('generation_id', 'unknown')}")


@scaffold.command()
@click.argument('generation_id')
def status(generation_id):
    """Check generation status."""
    result = get_client().scaffold_status(generation_id)
    click.echo(f"Status: {result.get('status')}")
    click.echo(f"Current step: {result.get('current_step')}")
    click.echo(f"Progress: {result.get('progress_pct')}%")


@scaffold.command()
@click.argument('generation_id')
@click.argument('step_name')
@click.argument('outputs', default='{}')
def step(generation_id, step_name, outputs):
    """Complete a scaffold step."""
    import json
    outputs_dict = json.loads(outputs)
    result = get_client().scaffold_complete_step(generation_id, step_name, outputs_dict)
    click.echo(f"Step completed: {result.get('status')}")


@scaffold.command()
@click.argument('instance_id')
@click.argument('approved', type=bool)
@click.option('--notes', '-n', default='', help='Review notes')
def review(instance_id, approved, notes):
    """Review a scaffold instance."""
    result = get_client().scaffold_review(instance_id, approved, notes=notes)
    click.echo(f"Review submitted: {result.get('status')}")


@scaffold.command()
@click.option('--status', '-s', help='Filter by status')
def progress(status):
    """Show scaffold progress report."""
    result = get_client().scaffold_progress(status=status)
    click.echo(f"Total: {result.get('total', 0)}")
    click.echo(f"Completed: {result.get('completed', 0)}")
    click.echo(f"Completion Rate: {result.get('completion_rate', 0)}%")


@scaffold.command()
@click.argument('name')
@click.argument('steps_json')
def register_template(name, steps_json):
    """Register a new scaffold template."""
    import json
    steps = json.loads(steps_json)
    result = get_client().scaffold_register_template(name, steps)
    click.echo(f"Template registered: {result.get('status')}")


@scaffold.command()
@click.option('--status', '-s', help='Filter by status')
def export(status):
    """Export scaffolds."""
    result = get_client().scaffold_export(status=status)
    click.echo(f"Exported {len(result)} scaffolds")

@scaffold.command()
def analytics():
    """Show scaffold analytics."""
    result = get_client().scaffold_analytics()
    click.echo(f"Total: {result.get('total_instances', 0)}")
    click.echo(f"Avg Steps: {result.get('avg_steps', 0)}")
    for tmpl, count in result.get('by_template', {}).items():
        click.echo(f"  {tmpl}: {count} instances")

@scaffold.command()
@click.argument('template_name')
def validate(template_name):
    """Validate a scaffold template."""
    result = get_client().scaffold_validate(template_name)
    click.echo(f"Valid: {'✅' if result.get('valid') else '❌'}")
    for issue in result.get('issues', []):
        click.echo(f"  Issue: {issue}")

@scaffold.command()
@click.argument('template_name')
def estimate(template_name):
    """Estimate template duration."""
    result = get_client().scaffold_estimate(template_name)
    click.echo(f"Duration: {result.get('estimated_minutes', 0)} min ({result.get('estimated_hours', 0)} hrs)")

@scaffold.command()
@click.argument('template_name')
@click.argument('step_name')
@click.argument('step_type')
@click.argument('description')
def add_step(template_name, step_name, step_type, description):
    """Add a custom step to a template."""
    result = get_client().scaffold_add_step(template_name, step_name, step_type, description)
    click.echo(f"Step added: {result.get('step_id', 'unknown')}")

@scaffold.command()
@click.argument('template_name')
@click.argument('approvers')
def add_approval(template_name, approvers):
    """Add approval flow to a template."""
    approver_list = [a.strip() for a in approvers.split(',')]
    result = get_client().scaffold_add_approval(template_name, approver_list)
    click.echo(f"Approval flow created: {result.get('flow_id', 'unknown')}")

@scaffold.command()
@click.argument('instance_ids')
def bulk_retire(instance_ids):
    """Bulk retire scaffold instances."""
    ids = [i.strip() for i in instance_ids.split(',')]
    result = get_client().scaffold_bulk_retire(ids)
    click.echo(f"Retired: {result.get('count', 0)} instances")
