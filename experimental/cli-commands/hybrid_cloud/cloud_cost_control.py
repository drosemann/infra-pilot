"""Cloud cost control CLI commands."""
from ...client import ApiClient
from ...output import print_output


def cmd_cost_summary(args):
    client = ApiClient(args.api_url, args.token)
    data = client.get_cost_summary()
    print_output(data, args.output)


def cmd_cost_record(args):
    client = ApiClient(args.api_url, args.token)
    data = client.record_cost(args.provider, args.amount, args.service)
    print_output(data, args.output)


def cmd_cost_budgets(args):
    client = ApiClient(args.api_url, args.token)
    data = client.list_cost_budgets()
    print_output(data, args.output)


def cmd_cost_budget_create(args):
    client = ApiClient(args.api_url, args.token)
    data = client.create_cost_budget(args.name, args.amount)
    print_output(data, args.output)


def cmd_cost_anomalies(args):
    client = ApiClient(args.api_url, args.token)
    data = client.list_cost_anomalies()
    print_output(data, args.output)


def cmd_cost_forecast(args):
    client = ApiClient(args.api_url, args.token)
    data = client.get_cost_forecast(args.days)
    print_output(data, args.output)


def cmd_cost_trends(args):
    """Show cost trends."""
    client = ApiClient(args.api_url, args.token)
    data = client.get_cost_trends(args.days)
    print_output(data, args.output)


def cmd_cost_by_provider(args):
    """Show costs grouped by provider."""
    client = ApiClient(args.api_url, args.token)
    data = client.get_cost_by_provider(args.provider)
    print_output(data, args.output)


def cmd_cost_anomaly_resolve(args):
    """Resolve a cost anomaly."""
    client = ApiClient(args.api_url, args.token)
    data = client.resolve_cost_anomaly(args.anomaly_id)
    print_output(data, args.output)


def cmd_cost_budget_delete(args):
    """Delete a cost budget."""
    client = ApiClient(args.api_url, args.token)
    data = client.delete_cost_budget(args.name)
    print_output(data, args.output)


def cmd_cost_export(args):
    """Export cost report."""
    client = ApiClient(args.api_url, args.token)
    data = client.export_cost_report()
    print_output(data, args.output)


def cmd_cost_record_batch(args):
    """Batch record costs."""
    client = ApiClient(args.api_url, args.token)
    data = client.batch_record_costs(args.file)
    print_output(data, args.output)


def cmd_cost_budget_create(args):
    """Create a budget."""
    client = ApiClient(args.api_url, args.token)
    data = client.create_cost_budget(args.name, args.amount, args.provider)
    print_output(data, args.output)


def cmd_cost_budget_delete(args):
    """Delete a budget."""
    client = ApiClient(args.api_url, args.token)
    data = client.delete_cost_budget(args.name)
    print_output(data, args.output)


def cmd_cost_budgets(args):
    """List all budgets."""
    client = ApiClient(args.api_url, args.token)
    data = client.list_cost_budgets()
    print_output(data, args.output)


def cmd_cost_forecast(args):
    """Show cost forecast."""
    client = ApiClient(args.api_url, args.token)
    data = client.get_cost_forecast(args.days)
    print_output(data, args.output)


def cmd_cost_top_spend(args):
    """Show top providers by spend."""
    client = ApiClient(args.api_url, args.token)
    data = client.get_top_spend_providers(args.limit)
    print_output(data, args.output)


def cmd_cost_anomaly_resolve(args):
    """Resolve a cost anomaly."""
    client = ApiClient(args.api_url, args.token)
    data = client.resolve_cost_anomaly(args.anomaly_id)
    print_output(data, args.output)


def cmd_cost_breakdown(args):
    """Show cost breakdown by provider."""
    client = ApiClient(args.api_url, args.token)
    data = client.get_cost_breakdown(args.provider, args.days)
    print_output(data, args.output)
