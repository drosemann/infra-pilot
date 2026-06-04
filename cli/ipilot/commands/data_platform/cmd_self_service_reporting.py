"""CLI commands for Self-Service Reporting (feature 47)."""

import click
from ...client import ApiClient


def get_client():
    from ...config import load_config
    return ApiClient(load_config().get('api_url', 'http://localhost:8080'), load_config().get('token'))


@click.group(name='report')
def report():
    """Create and manage reports."""


@report.command()
@click.argument('name')
def create(name):
    """Create a new report."""
    result = get_client().post('/api/v4/data/reports', {'name': name})
    click.echo(f"Report '{name}' created: {result.get('report_id')}")


@report.command()
def list():
    """List all reports."""
    result = get_client().get('/api/v4/data/reports')
    for r in result:
        click.echo(f"{r['name']:30s} {r.get('mode', 'visual'):10s} {r.get('widgets', 0)} widgets")


@report.command()
@click.argument('report_id')
def execute(report_id):
    """Execute a report."""
    result = get_client().post(f'/api/v4/data/reports/{report_id}/execute')
    click.echo(f"Report executed: {result.get('widgets')} widgets generated")


@report.command()
@click.argument('report_id')
@click.option('--format', '-f', default='pdf', help='Export format (pdf/csv/excel)')
def export(report_id, format):
    """Export a report."""
    result = get_client().post(f'/api/v4/data/reports/{report_id}/export', {'format': format})
    click.echo(f"Export URL: {result.get('url', 'N/A')}")


@report.command()
@click.argument('report_id')
@click.option('--cron', '-c', help='Cron expression')
@click.option('--recipients', '-r', help='Comma-separated email recipients')
def schedule(report_id, cron, recipients):
    """Schedule a report for delivery."""
    result = get_client().post(f'/api/v4/data/reports/{report_id}/schedules', {
        'cron': cron, 'recipients': recipients.split(',') if recipients else []})
    click.echo(f"Schedule created: {result.get('schedule_id')}")


@report.command()
def schedules():
    """List delivery schedules."""
    result = get_client().get('/api/v4/data/reports/schedules')
    for s in result:
        click.echo(f"Report: {s.get('report_id')} | Cron: {s.get('cron')} | Enabled: {s.get('enabled')}")


@report.command()
@click.argument('schedule_id')
def delete_schedule(schedule_id):
    """Delete a delivery schedule."""
    get_client().delete(f'/api/v4/data/reports/schedules/{schedule_id}')
    click.echo("Schedule deleted.")


@report.command()
@click.argument('report_id')
@click.option('--name', '-n', help='New name')
@click.option('--parameters', '-p', help='JSON parameters')
def duplicate(report_id, name, parameters):
    """Duplicate a report."""
    payload = {'new_name': name or f'copy_of_{report_id}'}
    if parameters: payload['parameters'] = parameters
    result = get_client().post(f'/api/v4/data/reports/{report_id}/duplicate', payload)
    click.echo(f"Duplicated: {result.get('report_id')}")


@report.command()
@click.argument('report_id')
@click.argument('widget_type')
@click.argument('title')
@click.option('--config', '-c', help='JSON widget config')
def add_widget(report_id, widget_type, title, config):
    """Add a widget to a report."""
    payload = {'type': widget_type, 'title': title}
    if config: payload['config'] = config
    result = get_client().post(f'/api/v4/data/reports/{report_id}/widgets', payload)
    click.echo(f"Widget added: {result.get('widget_id')}")


@report.command()
@click.argument('report_id')
@click.option('--format', '-f', default='pdf', help='Export format')
def export(report_id, format):
    """Export a report."""
    result = get_client().get(f'/api/v4/data/reports/{report_id}/export?format={format}')
    click.echo(f"Export URL: {result.get('url')}")


@report.command()
def templates():
    """List report templates."""
    result = get_client().get('/api/v4/data/reports/templates')
    for t in result:
        click.echo(f"{t['name']:25s} widgets={t.get('widgets', 0)}")


@report.command()
@click.argument('report_id')
def save_template(report_id):
    """Save a report as a template."""
    result = get_client().post(f'/api/v4/data/reports/{report_id}/save-template')
    click.echo(f"Saved as template: {result.get('is_template')}")
