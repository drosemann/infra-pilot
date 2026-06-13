"""Cloud migration CLI commands."""
from ...client import ApiClient
from ...output import print_output


def cmd_migrate_discover(args):
    client = ApiClient(args.api_url, args.token)
    data = client.discover_workload(args.name, args.hostname, args.os_type, args.vcpu, args.memory)
    print_output(data, args.output)


def cmd_migrate_workloads(args):
    client = ApiClient(args.api_url, args.token)
    data = client.list_migration_workloads()
    print_output(data, args.output)


def cmd_migrate_assess(args):
    client = ApiClient(args.api_url, args.token)
    data = client.assess_workload(args.workload_id)
    print_output(data, args.output)


def cmd_migrate_wave(args):
    client = ApiClient(args.api_url, args.token)
    data = client.create_migration_wave(args.name, args.workload_ids, args.target_provider)
    print_output(data, args.output)


def cmd_migrate_execute(args):
    client = ApiClient(args.api_url, args.token)
    data = client.execute_migration_wave(args.wave_id)
    print_output(data, args.output)


def cmd_migrate_rollback(args):
    client = ApiClient(args.api_url, args.token)
    data = client.rollback_migration_wave(args.wave_id)
    print_output(data, args.output)


def cmd_migrate_waves(args):
    """List migration waves."""
    client = ApiClient(args.api_url, args.token)
    data = client.list_migration_waves()
    print_output(data, args.output)


def cmd_migrate_log(args):
    """Show migration log."""
    client = ApiClient(args.api_url, args.token)
    data = client.get_migration_log()
    print_output(data, args.output)


def cmd_migrate_dependencies(args):
    """Show workload dependency map."""
    client = ApiClient(args.api_url, args.token)
    data = client.get_migration_dependency_map()
    print_output(data, args.output)


def cmd_migrate_cutover(args):
    """Check cutover readiness for a wave."""
    client = ApiClient(args.api_url, args.token)
    data = client.get_cutover_readiness(args.wave_id)
    print_output(data, args.output)


def cmd_migrate_export(args):
    """Export migration plan."""
    client = ApiClient(args.api_url, args.token)
    data = client.export_migration_plan()
    print_output(data, args.output)


def cmd_migrate_remove_workload(args):
    """Remove a workload from migration."""
    client = ApiClient(args.api_url, args.token)
    data = client.remove_migration_workload(args.workload_id)
    print_output(data, args.output)


def cmd_migrate_batch_assess(args):
    """Batch assess workloads."""
    client = ApiClient(args.api_url, args.token)
    data = client.batch_assess_workloads(args.workload_ids)
    print_output(data, args.output)


def cmd_migrate_cost(args):
    """Estimate migration cost."""
    client = ApiClient(args.api_url, args.token)
    data = client.estimate_migration_cost(args.wave_id)
    print_output(data, args.output)


def cmd_migrate_readiness(args):
    """Check wave readiness."""
    client = ApiClient(args.api_url, args.token)
    data = client.get_wave_readiness(args.wave_id)
    print_output(data, args.output)


def cmd_migrate_timeline(args):
    """Show migration timeline."""
    client = ApiClient(args.api_url, args.token)
    data = client.get_migration_timeline(args.wave_id)
    print_output(data, args.output)


def cmd_migrate_dependencies(args):
    """Show workload dependencies."""
    client = ApiClient(args.api_url, args.token)
    data = client.get_dependency_graph(args.workload_id)
    print_output(data, args.output)


def cmd_migrate_rollback(args):
    """Rollback a migration wave."""
    client = ApiClient(args.api_url, args.token)
    data = client.rollback_migration_wave(args.wave_id)
    print_output(data, args.output)


def cmd_migrate_add_dep(args):
    """Add a workload dependency."""
    client = ApiClient(args.api_url, args.token)
    data = client.add_workload_dependency(args.workload_id, args.depends_on)
    print_output(data, args.output)
