"""Registry replication CLI commands."""
from ...client import ApiClient
from ...output import print_output


def cmd_registry_images(args):
    client = ApiClient(args.api_url, args.token)
    data = client.list_registry_images()
    print_output(data, args.output)


def cmd_registry_register(args):
    client = ApiClient(args.api_url, args.token)
    data = client.register_registry_image(args.name, args.tag, args.registry, args.repository)
    print_output(data, args.output)


def cmd_registry_rules(args):
    client = ApiClient(args.api_url, args.token)
    data = client.list_replication_rules()
    print_output(data, args.output)


def cmd_registry_create_rule(args):
    client = ApiClient(args.api_url, args.token)
    data = client.create_replication_rule(args.source_registry, args.target_registries, args.image_pattern)
    print_output(data, args.output)


def cmd_registry_replicate(args):
    client = ApiClient(args.api_url, args.token)
    data = client.replicate_registry_image(args.image_id)
    print_output(data, args.output)


def cmd_registry_scan(args):
    client = ApiClient(args.api_url, args.token)
    data = client.scan_registry_image(args.image_id)
    print_output(data, args.output)


def cmd_registry_add_image(args):
    """Add a container image."""
    client = ApiClient(args.api_url, args.token)
    data = client.add_registry_image(args.name, args.tag, args.registry, args.size_mb)
    print_output(data, args.output)


def cmd_registry_delete_image(args):
    """Delete a container image."""
    client = ApiClient(args.api_url, args.token)
    data = client.delete_registry_image(args.image_id)
    print_output(data, args.output)


def cmd_registry_registries(args):
    """List configured registries."""
    client = ApiClient(args.api_url, args.token)
    data = client.list_registries()
    print_output(data, args.output)


def cmd_registry_cache(args):
    """List pull-through cache."""
    client = ApiClient(args.api_url, args.token)
    data = client.list_registry_cache()
    print_output(data, args.output)


def cmd_registry_vuln_summary(args):
    """Show vulnerability summary."""
    client = ApiClient(args.api_url, args.token)
    data = client.get_registry_vulnerability_summary()
    print_output(data, args.output)


def cmd_registry_export(args):
    """Export registry state."""
    client = ApiClient(args.api_url, args.token)
    data = client.export_registry_state()
    print_output(data, args.output)


def cmd_registry_batch_replicate(args):
    """Batch replicate images."""
    client = ApiClient(args.api_url, args.token)
    data = client.batch_replicate_images(args.image_ids)
    print_output(data, args.output)


def cmd_registry_scan_all(args):
    """Scan all images for vulnerabilities."""
    client = ApiClient(args.api_url, args.token)
    data = client.scan_all_images()
    print_output(data, args.output)


def cmd_registry_quota(args):
    """Show registry quota."""
    client = ApiClient(args.api_url, args.token)
    data = client.get_registry_quota()
    print_output(data, args.output)


def cmd_registry_create_rule(args):
    """Create a replication rule."""
    client = ApiClient(args.api_url, args.token)
    data = client.create_replication_rule(args.source, args.targets, args.pattern)
    print_output(data, args.output)


def cmd_registry_add_label(args):
    """Add label to image."""
    client = ApiClient(args.api_url, args.token)
    data = client.add_image_label(args.image_id, args.key, args.value)
    print_output(data, args.output)


def cmd_registry_cost(args):
    """Show registry cost analysis."""
    client = ApiClient(args.api_url, args.token)
    data = client.get_registry_cost_analysis()
    print_output(data, args.output)


def cmd_registry_cleanup(args):
    """Apply retention policy."""
    client = ApiClient(args.api_url, args.token)
    data = client.apply_registry_retention(args.max_images)
    print_output(data, args.output)
