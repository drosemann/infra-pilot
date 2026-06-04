"""Cloud bursting CLI commands."""
from ...client import ApiClient
from ...output import print_output


def cmd_burst_check(args):
    client = ApiClient(args.api_url, args.token)
    data = client.check_burst_readiness()
    print_output(data, args.output)


def cmd_burst_workloads(args):
    client = ApiClient(args.api_url, args.token)
    data = client.list_burst_workloads()
    print_output(data, args.output)


def cmd_burst_register(args):
    client = ApiClient(args.api_url, args.token)
    data = client.register_burst_workload(args.name, args.capacity, args.priority)
    print_output(data, args.output)


def cmd_burst_start(args):
    client = ApiClient(args.api_url, args.token)
    data = client.start_cloud_burst()
    print_output(data, args.output)


def cmd_burst_drain(args):
    client = ApiClient(args.api_url, args.token)
    data = client.drain_cloud_burst(args.burst_id)
    print_output(data, args.output)


def cmd_burst_status(args):
    client = ApiClient(args.api_url, args.token)
    data = client.get_burst_status(args.burst_id)
    print_output(data, args.output)


def cmd_burst_strategy(args):
    """Set the burst load distribution strategy."""
    client = ApiClient(args.api_url, args.token)
    data = client.set_burst_strategy(args.strategy)
    print_output(data, args.output)


def cmd_burst_cost(args):
    """Show burst cost analysis."""
    client = ApiClient(args.api_url, args.token)
    data = client.get_burst_cost_analysis()
    print_output(data, args.output)


def cmd_burst_stitch(args):
    """Create a network stitch for bursting."""
    client = ApiClient(args.api_url, args.token)
    data = client.create_network_stitch(args.on_prem_cidr, args.cloud_cidr, args.provider)
    print_output(data, args.output)


def cmd_burst_stitches(args):
    """List network stitches."""
    client = ApiClient(args.api_url, args.token)
    data = client.list_network_stitches()
    print_output(data, args.output)


def cmd_burst_add_workload(args):
    """Add a workload for cloud bursting."""
    client = ApiClient(args.api_url, args.token)
    data = client.add_burst_workload(args.name, args.capacity, args.priority)
    print_output(data, args.output)


def cmd_burst_remove_workload(args):
    """Remove a burst workload."""
    client = ApiClient(args.api_url, args.token)
    data = client.remove_burst_workload(args.workload_id)
    print_output(data, args.output)


def cmd_burst_remove_stitch(args):
    """Remove a network stitch."""
    client = ApiClient(args.api_url, args.token)
    data = client.remove_network_stitch(args.stitch_id)
    print_output(data, args.output)


def cmd_burst_alerts(args):
    """List burst alerts."""
    client = ApiClient(args.api_url, args.token)
    data = client.list_burst_alerts()
    print_output(data, args.output)


def cmd_burst_alert_create(args):
    """Create a burst alert."""
    client = ApiClient(args.api_url, args.token)
    data = client.create_burst_alert(args.name, args.threshold, args.metric)
    print_output(data, args.output)


def cmd_burst_schedule(args):
    """Schedule a burst."""
    client = ApiClient(args.api_url, args.token)
    data = client.schedule_burst(args.workload_id, args.cron)
    print_output(data, args.output)


def cmd_burst_capacity_plan(args):
    """Show capacity plan."""
    client = ApiClient(args.api_url, args.token)
    data = client.get_capacity_plan()
    print_output(data, args.output)


def cmd_burst_cost(args):
    """Show burst cost analysis."""
    client = ApiClient(args.api_url, args.token)
    data = client.get_burst_cost_analysis()
    print_output(data, args.output)


def cmd_burst_batch_create(args):
    """Batch create workloads."""
    client = ApiClient(args.api_url, args.token)
    data = client.batch_create_workloads(args.names)
    print_output(data, args.output)


def cmd_burst_drain_all(args):
    """Drain all active bursts."""
    client = ApiClient(args.api_url, args.token)
    data = client.drain_all_bursts()
    print_output(data, args.output)
