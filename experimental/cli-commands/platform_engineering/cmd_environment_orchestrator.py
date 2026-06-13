"""CLI commands for Environment Orchestrator (feature 17)."""

import click
from ...client import ApiClient


def get_client():
    from ...config import load_config
    return ApiClient(load_config().get('api_url', 'http://localhost:8080'), load_config().get('token'))


@click.group(name='environments')
def environments():
    """Manage ephemeral environments."""


@environments.command()
@click.option('--status', help='Filter by status')
def list(status):
    """List environments."""
    result = get_client().environments_list(status=status)
    for e in result:
        click.echo(f"{e['name']:25s} status={e.get('status','')} ttl={e.get('ttl_hours',0)}h")


@environments.command()
@click.argument('name')
@click.argument('template')
@click.option('--ttl', '-t', type=int, default=24, help='TTL in hours')
@click.option('--branch', '-b', default='main', help='Git branch')
def create(name, template, ttl, branch):
    """Create an ephemeral environment."""
    result = get_client().environments_create(name, template, ttl, branch)
    click.echo(f"Environment created: {result.get('id', 'unknown')}")


@environments.command()
@click.argument('env_id')
def get(env_id):
    """Get environment details."""
    result = get_client().environments_get(env_id)
    click.echo(f"Name: {result.get('name')}")
    click.echo(f"Status: {result.get('status')}")
    click.echo(f"TTL: {result.get('ttl_hours')}h")
    click.echo(f"URL: {result.get('url', 'N/A')}")


@environments.command()
@click.argument('env_id')
def delete(env_id):
    """Delete an environment."""
    result = get_client().environments_delete(env_id)
    click.echo(f"Deleted: {result.get('status')}")


@environments.command()
@click.argument('env_id')
@click.argument('hours', type=int)
def extend(env_id, hours):
    """Extend environment TTL."""
    result = get_client().environments_extend(env_id, hours)
    click.echo(f"TTL extended: {result.get('ttl_hours')}h remaining")


@environments.command()
def summary():
    """Get environment summary."""
    result = get_client().environments_summary()
    click.echo(f"Active: {result.get('active_environments')}")
    click.echo(f"Expired: {result.get('expired_environments')}")


@environments.command()
@click.argument('template_id')
@click.argument('project')
@click.argument('created_by')
@click.option('--ttl', '-t', type=int, default=24, help='TTL in hours')
def provision(template_id, project, created_by, ttl):
    """Provision from template."""
    result = get_client().environments_provision(template_id, project, created_by, ttl)
    click.echo(f"Provisioned: {result.get('id', 'unknown')}")


@environments.command()
@click.argument('env_ids')
def terminate(env_ids):
    """Terminate environments."""
    ids = [e.strip() for e in env_ids.split(',')]
    result = get_client().environments_terminate(ids)
    click.echo(f"Terminated: {result.get('count', 0)} environments")


@environments.command()
def cleanup():
    """Force cleanup expired environments."""
    result = get_client().environments_cleanup()
    click.echo(f"Cleaned up: {result.get('expired_count', 0)} environments")


@environments.command()
@click.option('--project', '-p', help='Filter by project')
def export(project):
    """Export environments."""
    result = get_client().environments_export(project=project)
    click.echo(f"Exported {len(result)} environments")


@environments.command()
def resources():
    """Show resource utilization."""
    result = get_client().environments_resources()
    click.echo(f"Running: {result.get('running_count', 0)}")
    click.echo(f"Total CPU: {result.get('total_cpu_allocated', 0)}")
    click.echo(f"Total Memory: {result.get('total_memory_gb', 0)}Gi")

@environments.command()
@click.argument('env_id')
def backup(env_id):
    """Backup an environment."""
    result = get_client().environments_backup(env_id)
    click.echo(f"Backup created: {result.get('backup_id', 'unknown')}")

@environments.command()
@click.argument('backup_id')
def restore(backup_id):
    """Restore from backup."""
    result = get_client().environments_restore(backup_id)
    click.echo(f"Restored: {result.get('env_id', 'unknown')}")

@environments.command()
@click.argument('env_id')
def health(env_id):
    """Check environment health."""
    result = get_client().environments_health(env_id)
    click.echo(f"Status: {result.get('status', 'unknown')}")
    click.echo(f"Age: {result.get('age_hours', 0)}h")
    click.echo(f"Expired: {result.get('is_expired', False)}")

@environments.command()
@click.argument('project')
@click.option('--max-age', '-m', type=int, default=72, help='Max age in hours')
@click.option('--auto-delete', '-a', is_flag=True, default=True, help='Auto delete')
def cleanup_policy(project, max_age, auto_delete):
    """Set cleanup policy for a project."""
    result = get_client().environments_cleanup_policy(project, max_age, auto_delete)
    click.echo(f"Policy set: {result.get('policy_id', 'unknown')}")

@environments.command()
@click.argument('project')
@click.option('--max-cpu', '-c', type=int, default=8, help='Max CPU cores')
@click.option('--max-mem', '-m', type=int, default=32, help='Max memory GB')
@click.option('--max-envs', '-e', type=int, default=5, help='Max environments')
def set_quota(project, max_cpu, max_mem, max_envs):
    """Set resource quota for a project."""
    result = get_client().environments_set_quota(project, max_cpu, max_mem, max_envs)
    click.echo(f"Quota set for {project}")

@environments.command()
@click.argument('project')
def quota_check(project):
    """Check resource quota usage."""
    result = get_client().environments_quota_check(project)
    click.echo(f"Envs: {result.get('environments', 0)}/{result.get('env_limit', 5)} ({result.get('env_pct', 0)}%)")
    click.echo(f"CPU: {result.get('cpu_used', 0)}/{result.get('cpu_limit', 8)} ({result.get('cpu_pct', 0)}%)")
    click.echo(f"Memory: {result.get('memory_used_gb', 0)}GB/{result.get('memory_limit_gb', 32)}GB ({result.get('memory_pct', 0)}%)")

@environments.command()
def expired():
    """Delete all expired environments."""
    result = get_client().environments_expired()
    click.echo(f"Deleted: {result.get('count', 0)} expired environments")
