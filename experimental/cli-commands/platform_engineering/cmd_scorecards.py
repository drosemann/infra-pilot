"""CLI commands for Scorecards/DORA Metrics (feature 14)."""

import click
from ...client import ApiClient


def get_client():
    from ...config import load_config
    return ApiClient(load_config().get('api_url', 'http://localhost:8080'), load_config().get('token'))


@click.group(name='scorecards')
def scorecards():
    """Manage DORA metrics and scorecards."""


@scorecards.command()
def list():
    """List scorecards."""
    result = get_client().scorecards_list()
    for s in result:
        click.echo(f"{s['name']:30s} team={s.get('team', '')}")


@scorecards.command()
@click.argument('name')
@click.argument('team')
@click.option('--dora', is_flag=True, help='Include DORA metrics')
def create(name, team, dora):
    """Create a scorecard."""
    result = get_client().scorecards_create(name, team, dora)
    click.echo(f"Scorecard created: {result.get('id', 'unknown')}")


@scorecards.command()
@click.argument('scorecard_id')
def get(scorecard_id):
    """Get scorecard details."""
    result = get_client().scorecards_get(scorecard_id)
    click.echo(f"Name: {result.get('name')}")
    click.echo(f"Team: {result.get('team')}")
    click.echo(f"Deploy Frequency: {result.get('deploy_frequency', 'N/A')}")
    click.echo(f"Lead Time: {result.get('lead_time', 'N/A')}")
    click.echo(f"MTTR: {result.get('mttr', 'N/A')}")
    click.echo(f"Change Fail Rate: {result.get('change_failure_rate', 'N/A')}")


@scorecards.command()
@click.argument('scorecard_id')
@click.argument('metric')
@click.argument('value')
def update(scorecard_id, metric, value):
    """Update a scorecard metric."""
    result = get_client().scorecards_update_metric(scorecard_id, metric, value)
    click.echo(f"Metric updated: {result.get('status')}")


@scorecards.command()
def summary():
    """Get scorecard summary."""
    result = get_client().scorecards_summary()
    click.echo(f"Scorecards: {result.get('total_scorecards')}")
    click.echo(f"Avg Deploy Freq: {result.get('avg_deploy_frequency')}")


@scorecards.command()
@click.argument('team_id')
@click.option('--periods', '-p', type=int, default=6, help='Number of periods')
def trend(team_id, periods):
    """Show score trend."""
    result = get_client().scorecards_trend(team_id, periods=periods)
    for r in result:
        click.echo(f"{r.get('period_start', '')[:10]} score={r.get('value', 0)}")


@scorecards.command()
@click.argument('team_ids')
def compare(team_ids):
    """Compare teams."""
    ids = [t.strip() for t in team_ids.split(',')]
    result = get_client().scorecards_compare(ids)
    for r in result:
        click.echo(f"{r.get('team_name', '')} score={r.get('total_score', 0)} rating={r.get('rating', '')}")


@scorecards.command()
@click.argument('team_id')
@click.option('--format', '-f', default='json', help='Export format')
def export(team_id, format):
    """Export team scores."""
    result = get_client().scorecards_export(team_id, format=format)
    click.echo(f"Exported data for team {team_id}")

@scorecards.command()
@click.argument('team_id')
@click.option('--days', '-d', type=int, default=180, help='Lookback days')
def history(team_id, days):
    """Show team score history."""
    result = get_client().scorecards_history(team_id, days=days)
    for r in result:
        click.echo(f"{r.get('date', '')[:10]} score={r.get('dora_score', 0)}")

@scorecards.command()
@click.argument('team_id')
@click.option('--weeks', '-w', type=int, default=4, help='Weeks ahead')
def predict(team_id, weeks):
    """Predict team score trend."""
    result = get_client().scorecards_predict(team_id, weeks=weeks)
    click.echo(f"Current: {result.get('current_score', 0)}")
    click.echo(f"Predicted: {result.get('predicted_score', 0)}")
    click.echo(f"Confidence: {result.get('confidence', 'N/A')}")

@scorecards.command()
@click.argument('organization')
def org_summary(organization):
    """Show organization summary."""
    result = get_client().scorecards_org_summary(organization)
    click.echo(f"Teams: {result.get('team_count', 0)}")
    click.echo(f"Avg Score: {result.get('avg_dora_score', 0)}")
    click.echo(f"Min Score: {result.get('min_score', 0)}")
    click.echo(f"Max Score: {result.get('max_score', 0)}")

@scorecards.command()
@click.argument('goal_id')
def goal_progress(goal_id):
    """Check goal progress."""
    result = get_client().scorecards_goal_progress(goal_id)
    click.echo(f"Metric: {result.get('metric', 'N/A')}")
    click.echo(f"Target: {result.get('target', 0)}")
    click.echo(f"Current: {result.get('current', 0)}")
    click.echo(f"Progress: {result.get('progress_pct', 0)}%")

@scorecards.command()
@click.argument('team_id')
@click.argument('metric')
@click.argument('target', type=float)
@click.argument('deadline')
def set_goal(team_id, metric, target, deadline):
    """Set a DORA goal for a team."""
    result = get_client().scorecards_set_goal(team_id, metric, target, deadline)
    click.echo(f"Goal set: {result.get('goal_id', 'unknown')}")

@scorecards.command()
@click.argument('team_id')
@click.option('--deploy-freq', '-d', type=float, help='Deployment frequency')
@click.option('--lead-time', '-l', type=float, help='Lead time')
@click.option('--mttr', '-m', type=float, help='MTTR')
@click.option('--cfr', '-c', type=float, help='Change failure rate')
def ingest(team_id, deploy_freq, lead_time, mttr, cfr):
    """Ingest DORA data for a team."""
    data = {k: v for k, v in [('deployment_frequency', deploy_freq), ('lead_time', lead_time), ('mttr', mttr), ('change_failure_rate', cfr)] if v is not None}
    result = get_client().scorecards_ingest(team_id, data)
    click.echo(f"Ingested: {result.get('status', 'done')}")

@scorecards.command()
def leaderboard():
    """Show full leaderboard."""
    result = get_client().scorecards_leaderboard()
    for r in result:
        click.echo(f"#{r.get('rank', 0):2d} {r.get('team_name', ''):20s} score={r.get('score', 0)} rating={r.get('rating', '')}")
