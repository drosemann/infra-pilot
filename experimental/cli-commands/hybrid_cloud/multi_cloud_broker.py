"""Multi-cloud broker CLI commands."""
from ...client import ApiClient
from ...output import print_output


def cmd_cloud_list(args):
    client = ApiClient(args.api_url, args.token)
    data = client.list_cloud_resources()
    print_output(data, args.output)


def cmd_cloud_provision(args):
    client = ApiClient(args.api_url, args.token)
    data = client.provision_cloud_resource(args.provider, args.resource_type, args.name, args.region, args.count)
    print_output(data, args.output)


def cmd_cloud_status(args):
    client = ApiClient(args.api_url, args.token)
    data = client.get_cloud_resource(args.resource_id)
    print_output(data, args.output)


def cmd_cloud_delete(args):
    client = ApiClient(args.api_url, args.token)
    data = client.delete_cloud_resource(args.resource_id)
    print_output(data, args.output)


def cmd_cloud_providers(args):
    client = ApiClient(args.api_url, args.token)
    data = client.list_cloud_providers()
    print_output(data, args.output)


def cmd_cloud_score(args):
    client = ApiClient(args.api_url, args.token)
    data = client.score_cloud_providers(args.vcpu, args.memory)
    print_output(data, args.output)


def cmd_cloud_batch_provision(args):
    """Batch provision resources from a comma-separated list of names."""
    client = ApiClient(args.api_url, args.token)
    names = [n.strip() for n in args.names.split(",")]
    results = []
    for name in names:
        data = client.provision_cloud_resource(args.provider, args.resource_type, name, args.region, 1)
        results.append(data)
    print_output({"results": results, "count": len(results)}, args.output)


def cmd_cloud_cost_summary(args):
    """Show cost summary for all cloud resources."""
    client = ApiClient(args.api_url, args.token)
    data = client.get_cloud_cost_summary()
    print_output(data, args.output)


def cmd_cloud_search(args):
    """Search cloud resources by name or provider."""
    client = ApiClient(args.api_url, args.token)
    data = client.search_cloud_resources(args.query)
    print_output(data, args.output)


def cmd_cloud_failover(args):
    """Failover a resource to a backup provider."""
    client = ApiClient(args.api_url, args.token)
    data = client.failover_cloud_resource(args.resource_id)
    print_output(data, args.output)


def cmd_cloud_export(args):
    """Export all cloud resources."""
    client = ApiClient(args.api_url, args.token)
    data = client.export_cloud_resources()
    print_output(data, args.output)


def cmd_cloud_stats(args):
    """Show multi-cloud statistics."""
    client = ApiClient(args.api_url, args.token)
    data = client.get_cloud_statistics()
    print_output(data, args.output)


def cmd_cloud_provider_diff(args):
    """Compare two cloud providers."""
    client = ApiClient(args.api_url, args.token)
    data = client.compare_cloud_providers(args.provider1, args.provider2)
    print_output(data, args.output)


def cmd_cloud_tag(args):
    """Tag a cloud resource."""
    client = ApiClient(args.api_url, args.token)
    data = client.tag_cloud_resource(args.resource_id, args.key, args.value)
    print_output(data, args.output)


def cmd_cloud_alerts(args):
    """List resource alerts."""
    client = ApiClient(args.api_url, args.token)
    data = client.list_cloud_alerts()
    print_output(data, args.output)


def cmd_cloud_alert_create(args):
    """Create a resource alert."""
    client = ApiClient(args.api_url, args.token)
    data = client.create_cloud_alert(args.resource_id, args.event, args.webhook)
    print_output(data, args.output)


def cmd_cloud_bulk_delete(args):
    """Bulk delete resources by provider."""
    client = ApiClient(args.api_url, args.token)
    data = client.bulk_delete_cloud_resources(args.provider)
    print_output(data, args.output)


def cmd_cloud_cost(args):
    """Show cost summary across providers."""
    client = ApiClient(args.api_url, args.token)
    data = client.get_cloud_cost_summary()
    print_output(data, args.output)


def cmd_cloud_provision_multi(args):
    """Provision multiple resources."""
    client = ApiClient(args.api_url, args.token)
    data = client.bulk_provision_cloud_resources(args.provider, args.type, args.count)
    print_output(data, args.output)


def cmd_cloud_rename(args):
    """Rename a resource."""
    client = ApiClient(args.api_url, args.token)
    data = client.rename_cloud_resource(args.resource_id, args.name)
    print_output(data, args.output)


def cmd_cloud_snapshot(args):
    """Snapshot a resource state."""
    client = ApiClient(args.api_url, args.token)
    data = client.snapshot_cloud_resource(args.resource_id)
    print_output(data, args.output)
