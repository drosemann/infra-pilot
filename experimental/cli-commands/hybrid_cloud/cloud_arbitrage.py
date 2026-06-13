"""Cloud arbitrage CLI commands."""
from ...client import ApiClient
from ...output import print_output


def cmd_arbitrage_opportunities(args):
    client = ApiClient(args.api_url, args.token)
    data = client.list_arbitrage_opportunities()
    print_output(data, args.output)


def cmd_arbitrage_compare(args):
    client = ApiClient(args.api_url, args.token)
    data = client.compare_arbitrage_pricing(args.vcpu, args.memory)
    print_output(data, args.output)


def cmd_arbitrage_migrate(args):
    client = ApiClient(args.api_url, args.token)
    data = client.execute_arbitrage_migration(args.opportunity_id)
    print_output(data, args.output)


def cmd_arbitrage_savings(args):
    client = ApiClient(args.api_url, args.token)
    data = client.get_arbitrage_savings()
    print_output(data, args.output)


def cmd_arbitrage_alerts(args):
    """List pricing alerts."""
    client = ApiClient(args.api_url, args.token)
    data = client.list_pricing_alerts()
    print_output(data, args.output)


def cmd_arbitrage_alert(args):
    """Set a pricing alert."""
    client = ApiClient(args.api_url, args.token)
    data = client.create_pricing_alert(args.provider, args.threshold, args.region)
    print_output(data, args.output)


def cmd_arbitrage_spot(args):
    """Analyze spot pricing."""
    client = ApiClient(args.api_url, args.token)
    data = client.analyze_spot_prices(args.provider, args.instance)
    print_output(data, args.output)


def cmd_arbitrage_summary(args):
    """Show arbitrage summary."""
    client = ApiClient(args.api_url, args.token)
    data = client.get_arbitrage_summary()
    print_output(data, args.output)


def cmd_arbitrage_export(args):
    """Export arbitrage opportunities."""
    client = ApiClient(args.api_url, args.token)
    data = client.export_arbitrage_opportunities()
    print_output(data, args.output)


def cmd_arbitrage_opportunities(args):
    """List arbitrage opportunities."""
    client = ApiClient(args.api_url, args.token)
    data = client.list_arbitrage_opportunities(args.state)
    print_output(data, args.output)


def cmd_arbitrage_execute(args):
    """Execute an arbitrage migration."""
    client = ApiClient(args.api_url, args.token)
    data = client.execute_arbitrage_migration(args.opportunity_id)
    print_output(data, args.output)


def cmd_arbitrage_dismiss(args):
    """Dismiss an opportunity."""
    client = ApiClient(args.api_url, args.token)
    data = client.dismiss_arbitrage_opportunity(args.opportunity_id)
    print_output(data, args.output)


def cmd_arbitrage_recommend(args):
    """Get provider recommendation."""
    client = ApiClient(args.api_url, args.token)
    data = client.get_arbitrage_recommendation(args.provider, args.vcpu, args.memory, args.region, args.price)
    print_output(data, args.output)


def cmd_arbitrage_pricing(args):
    """Compare pricing across providers."""
    client = ApiClient(args.api_url, args.token)
    data = client.compare_pricing(args.vcpu, args.memory, args.region)
    print_output(data, args.output)


def cmd_arbitrage_savings(args):
    """Show savings report."""
    client = ApiClient(args.api_url, args.token)
    data = client.get_arbitrage_savings_report()
    print_output(data, args.output)


def cmd_arbitrage_import(args):
    """Import pricing data."""
    client = ApiClient(args.api_url, args.token)
    data = client.import_arbitrage_pricing(args.file)
    print_output(data, args.output)
