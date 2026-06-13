"""CLI commands for Developer Pulse (feature 20)."""

import click
from ...client import ApiClient


def get_client():
    from ...config import load_config
    return ApiClient(load_config().get('api_url', 'http://localhost:8080'), load_config().get('token'))


@click.group(name='pulse')
def pulse():
    """Manage developer pulse surveys."""


@pulse.command()
def list():
    """List pulse surveys."""
    result = get_client().pulse_list_surveys()
    for s in result:
        click.echo(f"{s['title'][:30]:30s} responses={s.get('response_count',0)} score={s.get('avg_score','N/A')}")


@pulse.command()
@click.argument('title')
@click.argument('questions_json')
def create(title, questions_json):
    """Create a pulse survey."""
    import json
    questions = json.loads(questions_json)
    result = get_client().pulse_create_survey(title, questions)
    click.echo(f"Survey created: {result.get('id', 'unknown')}")


@pulse.command()
@click.argument('survey_id')
@click.argument('respondent')
@click.argument('answers_json')
def respond(survey_id, respondent, answers_json):
    """Submit survey response."""
    import json
    answers = json.loads(answers_json)
    result = get_client().pulse_respond(survey_id, respondent, answers)
    click.echo(f"Response recorded: {result.get('status')}")


@pulse.command()
@click.argument('survey_id')
def results(survey_id):
    """Get survey results."""
    result = get_client().pulse_results(survey_id)
    click.echo(f"Survey: {result.get('title')}")
    click.echo(f"Responses: {result.get('response_count')}")
    click.echo(f"Avg Score: {result.get('avg_score')}")
    click.echo(f"NPS: {result.get('nps_score')}")


@pulse.command()
def summary():
    """Get pulse summary."""
    result = get_client().pulse_summary()
    click.echo(f"Surveys: {result.get('total_surveys')}")
    click.echo(f"Responses: {result.get('total_responses')}")
    click.echo(f"Overall NPS: {result.get('overall_nps')}")


@pulse.command()
@click.argument('survey_id')
def launch(survey_id):
    """Launch a survey."""
    result = get_client().pulse_launch(survey_id)
    click.echo(f"Survey launched: {result.get('status')}")


@pulse.command()
@click.argument('survey_id')
def close(survey_id):
    """Close a survey."""
    result = get_client().pulse_close(survey_id)
    click.echo(f"Survey closed: {result.get('status')}")


@pulse.command()
@click.argument('survey_id')
def nps_breakdown(survey_id):
    """Show detailed NPS breakdown."""
    result = get_client().pulse_nps_breakdown(survey_id)
    click.echo(f"Score: {result.get('nps_score', 'N/A')}")
    click.echo(f"Promoters: {result.get('promoters', 0)}")
    click.echo(f"Detractors: {result.get('detractors', 0)}")
    click.echo(f"Comments: {result.get('comments_count', 0)}")


@pulse.command()
@click.option('--days', '-d', type=int, default=90, help='Lookback days')
def analytics(days):
    """Show pulse analytics."""
    result = get_client().pulse_analytics(days=days)
    click.echo(f"Surveys: {result.get('total_surveys', 0)}")
    click.echo(f"Responses: {result.get('total_responses', 0)}")
    click.echo(f"Avg NPS: {result.get('average_nps', 'N/A')}")

@pulse.command()
@click.argument('survey_id')
def aggregate(survey_id):
    """Aggregate survey results."""
    result = get_client().pulse_aggregate(survey_id)
    click.echo(f"Survey: {result.get('title', 'N/A')}")
    click.echo(f"Responses: {result.get('total_responses', 0)}")
    for q, data in result.get('aggregated', {}).items():
        if 'avg' in data:
            click.echo(f"  {q[:40]}: avg={data['avg']}")

@pulse.command()
@click.option('--months', '-m', type=int, default=6, help='Months to analyze')
def sentiment(months):
    """Show sentiment trend."""
    result = get_client().pulse_sentiment(months=months)
    for month, data in result.get('trend', {}).items():
        click.echo(f"{month}: avg={data.get('avg', 0)} (n={data.get('count', 0)})")

@pulse.command()
@click.argument('survey_id')
@click.option('--format', '-f', default='json', help='Export format')
def export(survey_id, format):
    """Export survey data."""
    result = get_client().pulse_export(survey_id, format=format)
    if format == 'csv':
        click.echo(f"Exported {len(result.splitlines())} lines")
    else:
        click.echo(f"Exported {result.get('responses', 0)} responses")

@pulse.command()
@click.argument('title')
@click.argument('questions')
@click.option('--type', '-t', default='nps', help='Survey type')
@click.option('--cron', '-c', default='0 0 1 * *', help='Cron expression')
def schedule(title, questions, type, cron):
    """Schedule a recurring survey."""
    q_list = [q.strip() for q in questions.split(',')]
    result = get_client().pulse_schedule(title, q_list, type, cron)
    click.echo(f"Scheduled: {result.get('schedule', {}).get('schedule_id', 'unknown')}")

@pulse.command()
@click.argument('survey_id')
def insights(survey_id):
    """Show survey insights and NPS."""
    result = get_client().pulse_insights(survey_id)
    click.echo(f"NPS: {result.get('nps_score', 'N/A')}")
    click.echo(f"Promoters: {result.get('promoters', 0)}")
    click.echo(f"Detractors: {result.get('detractors', 0)}")
    click.echo(f"Response Rate: {result.get('response_rate', 0)}%")

@pulse.command()
@click.argument('survey_id')
def reminders(survey_id):
    """Send reminders for pending surveys."""
    result = get_client().pulse_reminders(survey_id)
    click.echo(f"Reminders sent: {result.get('reminders_sent', 0)}")
    click.echo(f"Total pending: {result.get('total_pending', 0)}")
