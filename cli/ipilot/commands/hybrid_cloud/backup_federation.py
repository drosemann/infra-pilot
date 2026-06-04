"""Backup federation CLI commands."""
from ...client import ApiClient
from ...output import print_output


def cmd_backupfed_list(args):
    client = ApiClient(args.api_url, args.token)
    data = client.list_backups()
    print_output(data, args.output)


def cmd_backupfed_restore(args):
    client = ApiClient(args.api_url, args.token)
    data = client.restore_backup(args.backup_id, args.target_provider)
    print_output(data, args.output)


def cmd_backupfed_create(args):
    """Create a backup."""
    client = ApiClient(args.api_url, args.token)
    data = client.create_backup(args.workload_id, args.source_provider, args.size_gb)
    print_output(data, args.output)


def cmd_backupfed_vaults(args):
    """List backup vaults."""
    client = ApiClient(args.api_url, args.token)
    data = client.list_backup_vaults()
    print_output(data, args.output)


def cmd_backupfed_integrity(args):
    """Verify backup integrity."""
    client = ApiClient(args.api_url, args.token)
    data = client.verify_backup_integrity(args.backup_id)
    print_output(data, args.output)


def cmd_backupfed_schedule(args):
    """Schedule a backup."""
    client = ApiClient(args.api_url, args.token)
    data = client.schedule_backup(args.workload_id, args.cron, args.retention)
    print_output(data, args.output)


def cmd_backupfed_schedules(args):
    """List backup schedules."""
    client = ApiClient(args.api_url, args.token)
    data = client.list_backup_schedules()
    print_output(data, args.output)


def cmd_backupfed_summary(args):
    """Show backup summary."""
    client = ApiClient(args.api_url, args.token)
    data = client.get_backup_summary()
    print_output(data, args.output)


def cmd_backupfed_delete(args):
    """Delete a backup."""
    client = ApiClient(args.api_url, args.token)
    data = client.delete_backup(args.backup_id)
    print_output(data, args.output)


def cmd_backupfed_create(args):
    client = ApiClient(args.api_url, args.token)
    data = client.create_federated_backup(args.name, args.workload_id, args.source_provider)
    print_output(data, args.output)


def cmd_backupfed_execute(args):
    client = ApiClient(args.api_url, args.token)
    data = client.execute_federated_backup(args.backup_id)
    print_output(data, args.output)


def cmd_backupfed_restore(args):
    client = ApiClient(args.api_url, args.token)
    data = client.restore_federated_backup(args.backup_id, args.target_provider)
    print_output(data, args.output)


def cmd_backupfed_vaults(args):
    client = ApiClient(args.api_url, args.token)
    data = client.list_backup_vaults()
    print_output(data, args.output)


def cmd_backupfed_create(args):
    """Create a backup."""
    client = ApiClient(args.api_url, args.token)
    data = client.create_backup(args.name, args.workload_id, args.target, args.retention)
    print_output(data, args.output)


def cmd_backupfed_batch(args):
    """Execute multiple backups."""
    client = ApiClient(args.api_url, args.token)
    data = client.batch_execute_backups(args.backup_ids)
    print_output(data, args.output)


def cmd_backupfed_verify_all(args):
    """Verify all backup integrity."""
    client = ApiClient(args.api_url, args.token)
    data = client.verify_all_backups()
    print_output(data, args.output)


def cmd_backupfed_retention(args):
    """Enforce retention policy."""
    client = ApiClient(args.api_url, args.token)
    data = client.enforce_backup_retention()
    print_output(data, args.output)


def cmd_backupfed_schedule_create(args):
    """Create a backup schedule."""
    client = ApiClient(args.api_url, args.token)
    data = client.create_backup_schedule(args.workload_id, args.cron, args.retention)
    print_output(data, args.output)


def cmd_backupfed_schedules(args):
    """List backup schedules."""
    client = ApiClient(args.api_url, args.token)
    data = client.list_backup_schedules()
    print_output(data, args.output)


def cmd_backupfed_compliance(args):
    """Show backup compliance report."""
    client = ApiClient(args.api_url, args.token)
    data = client.get_backup_compliance()
    print_output(data, args.output)
