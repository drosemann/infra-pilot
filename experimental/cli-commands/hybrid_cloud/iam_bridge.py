"""IAM bridge CLI commands."""
from ...client import ApiClient
from ...output import print_output


def cmd_iam_mappings(args):
    client = ApiClient(args.api_url, args.token)
    data = client.list_iam_mappings()
    print_output(data, args.output)


def cmd_iam_create_mapping(args):
    client = ApiClient(args.api_url, args.token)
    data = client.create_iam_mapping(args.source_role, args.source_provider, args.target_role, args.target_provider)
    print_output(data, args.output)


def cmd_iam_sync(args):
    client = ApiClient(args.api_url, args.token)
    data = client.sync_iam_mappings()
    print_output(data, args.output)


def cmd_iam_roles(args):
    client = ApiClient(args.api_url, args.token)
    data = client.list_iam_roles()
    print_output(data, args.output)


def cmd_iam_policies(args):
    client = ApiClient(args.api_url, args.token)
    data = client.list_iam_policies()
    print_output(data, args.output)


def cmd_iam_create_role(args):
    """Create a new IAM role."""
    client = ApiClient(args.api_url, args.token)
    data = client.create_iam_role(args.name, args.description, args.provider)
    print_output(data, args.output)


def cmd_iam_create_policy(args):
    """Create a new IAM policy."""
    client = ApiClient(args.api_url, args.token)
    data = client.create_iam_policy(args.name, args.statements)
    print_output(data, args.output)


def cmd_iam_create_mapping(args):
    """Create a cross-provider mapping."""
    client = ApiClient(args.api_url, args.token)
    data = client.create_iam_mapping(args.source_role, args.source_provider, args.target_role, args.target_provider)
    print_output(data, args.output)


def cmd_iam_sync_all(args):
    """Sync all IAM mappings."""
    client = ApiClient(args.api_url, args.token)
    data = client.sync_all_iam_mappings()
    print_output(data, args.output)


def cmd_iam_compliance(args):
    """Check IAM compliance."""
    client = ApiClient(args.api_url, args.token)
    data = client.check_iam_compliance(args.framework)
    print_output(data, args.output)


def cmd_iam_export(args):
    """Export IAM state."""
    client = ApiClient(args.api_url, args.token)
    data = client.export_iam_state()
    print_output(data, args.output)


def cmd_iam_delete_role(args):
    """Delete an IAM role."""
    client = ApiClient(args.api_url, args.token)
    data = client.delete_iam_role(args.role_id)
    print_output(data, args.output)


def cmd_iam_sync(args):
    client = ApiClient(args.api_url, args.token)
    data = client.sync_iam_mappings()
    print_output(data, args.output)


def cmd_iam_mappings(args):
    """List role mappings."""
    client = ApiClient(args.api_url, args.token)
    data = client.list_iam_mappings()
    print_output(data, args.output)


def cmd_iam_add_mapping(args):
    """Create a role mapping between providers."""
    client = ApiClient(args.api_url, args.token)
    data = client.create_iam_mapping(args.source_role, args.source_provider, args.target_role, args.target_provider)
    print_output(data, args.output)


def cmd_iam_add_role(args):
    """Add an IAM role."""
    client = ApiClient(args.api_url, args.token)
    data = client.add_iam_role(args.name, args.provider, args.permissions)
    print_output(data, args.output)


def cmd_iam_history(args):
    """Show sync history."""
    client = ApiClient(args.api_url, args.token)
    data = client.get_iam_sync_history()
    print_output(data, args.output)


def cmd_iam_review(args):
    """Create an access review."""
    client = ApiClient(args.api_url, args.token)
    data = client.create_access_review(args.role_id, args.reviewer)
    print_output(data, args.output)


def cmd_iam_export(args):
    """Export IAM roles and mappings."""
    client = ApiClient(args.api_url, args.token)
    data = client.export_iam_roles()
    print_output(data, args.output)


def cmd_iam_policies(args):
    client = ApiClient(args.api_url, args.token)
    data = client.list_iam_policies()
    print_output(data, args.output)
