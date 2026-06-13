"""Cost allocation CLI commands."""
from ...client import ApiClient
from ...output import print_output


def cmd_alloc_summary(args):
    client = ApiClient(args.api_url, args.token)
    data = client.get_allocation_summary()
    print_output(data, args.output)


def cmd_alloc_create(args):
    client = ApiClient(args.api_url, args.token)
    data = client.create_cost_allocation(args.name, args.amount, args.team, args.project, args.source)
    print_output(data, args.output)


def cmd_alloc_chargeback(args):
    client = ApiClient(args.api_url, args.token)
    data = client.create_chargeback(args.team, args.project, args.amount, args.period)
    print_output(data, args.output)


def cmd_alloc_teams(args):
    client = ApiClient(args.api_url, args.token)
    data = client.get_team_spend(args.team)
    print_output(data, args.output)


def cmd_alloc_tags(args):
    client = ApiClient(args.api_url, args.token)
    data = client.list_cost_tags()
    print_output(data, args.output)


def cmd_alloc_add(args):
    """Add a cost allocation."""
    client = ApiClient(args.api_url, args.token)
    data = client.allocate_cost(args.amount, args.team, args.project, args.source)
    print_output(data, args.output)


def cmd_alloc_budget_set(args):
    """Set a team budget."""
    client = ApiClient(args.api_url, args.token)
    data = client.set_team_budget(args.team, args.amount)
    print_output(data, args.output)


def cmd_alloc_budgets(args):
    """List team budgets."""
    client = ApiClient(args.api_url, args.token)
    data = client.list_team_budgets()
    print_output(data, args.output)


def cmd_alloc_export(args):
    """Export cost allocations."""
    client = ApiClient(args.api_url, args.token)
    data = client.export_cost_allocations(args.period)
    print_output(data, args.output)


def cmd_alloc_efficiency(args):
    """Show allocation efficiency."""
    client = ApiClient(args.api_url, args.token)
    data = client.get_allocation_efficiency()
    print_output(data, args.output)


def cmd_alloc_list(args):
    """List all allocations."""
    client = ApiClient(args.api_url, args.token)
    data = client.list_cost_allocations()
    print_output(data, args.output)


def cmd_alloc_project_spend(args):
    """Show spend for a project."""
    client = ApiClient(args.api_url, args.token)
    data = client.get_project_spend(args.project)
    print_output(data, args.output)


def cmd_alloc_showback(args):
    """Show showback report."""
    client = ApiClient(args.api_url, args.token)
    data = client.get_showback_report()
    print_output(data, args.output)


def cmd_alloc_budget_set(args):
    """Set a team budget."""
    client = ApiClient(args.api_url, args.token)
    data = client.set_team_budget(args.team, args.amount)
    print_output(data, args.output)


def cmd_alloc_budget_check(args):
    """Check budget compliance."""
    client = ApiClient(args.api_url, args.token)
    data = client.check_budget_compliance(args.team)
    print_output(data, args.output)


def cmd_alloc_create_chargeback(args):
    """Create a chargeback entry."""
    client = ApiClient(args.api_url, args.token)
    data = client.create_chargeback(args.team, args.project, args.amount, args.method)
    print_output(data, args.output)


def cmd_alloc_export_csv(args):
    """Export allocations as CSV."""
    client = ApiClient(args.api_url, args.token)
    data = client.export_allocations_csv(args.team)
    print_output(data, args.output)


def cmd_alloc_trend(args):
    """Show cost trend."""
    client = ApiClient(args.api_url, args.token)
    data = client.get_cost_trend(args.months)
    print_output(data, args.output)


def cmd_alloc_efficiency(args):
    """Show allocation efficiency."""
    client = ApiClient(args.api_url, args.token)
    data = client.get_allocation_efficiency()
    print_output(data, args.output)
