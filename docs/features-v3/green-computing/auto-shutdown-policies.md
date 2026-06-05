# Feature 16: Auto-Shutdown Policies

## Overview
Configurable automatic shutdown of dev/staging environments during off-hours (nights, weekends). Startup on schedule or via webhook trigger.

## Capabilities
- Time-based auto-shutdown (daily, weekly, custom schedule)
- Auto-startup on schedule
- Webhook-triggered startup for CI/CD pipelines
- Gradual shutdown (notify → drain connections → stop)
- Environment tagging for policy targeting
- Policy inheritance (team → project → environment)
- Override mechanism for extended work hours
- Shutdown cost savings report
- Exclusion list for critical services
- Grace period with user notification

## Policy Configuration

```python
@dataclass
class AutoShutdownPolicy:
    name: str
    environment_tags: list[str]  # ["dev", "staging", "test"]
    
    # Shutdown schedule
    shutdown_times: list[ShutdownTime]
    # e.g., [ShutdownTime(weekday=0-4, hour=19), ShutdownTime(weekday=5, hour=13)]
    
    startup_times: list[StartupTime]
    # e.g., [StartupTime(weekday=0-4, hour=8), StartupTime(weekday=1, hour=8)]
    
    # Behavior
    grace_period_minutes: int = 15
    drain_timeout_minutes: int = 5
    force_stop_after_minutes: int = 30
    notify_users: bool = True
    allow_override: bool = True
    override_max_hours: int = 4
    
    # Dry-run mode
    dry_run: bool = False
```

## Shutdown Flow

```
1. Pre-shutdown (T-15 min)
   ├── Send notification to environment users
   │   "Environment 'prod-clone' will shut down in 15 minutes"
   │
2. Grace period (T-5 min)
   ├── Send final warning
   ├── Check for active connections/SSH sessions
   ├── Postpone if activity detected (configurable)
   │
3. Drain connections (T-0)
   ├── Send SIGTERM to running processes
   ├── Close database connections
   ├── Flush logs and metrics
   │
4. Stop resources
   ├── docker-compose down (or equivalent)
   ├── Stop virtual machines
   ├── Release reserved resources
   │
5. Post-shutdown
   ├── Confirm all resources stopped
   ├── Record savings
   ├── Report to audit log
   └── Wait for next startup schedule
```

## Cost Savings Calculation

```python
def calculate_savings(environment, policy, hours_rate):
    """Calculate cost savings from auto-shutdown."""
    weekly_off_hours = sum(
        (s.hour - policy.startup_time.weekday_hour(s.weekday)) 
        for s in policy.shutdown_times
    )
    monthly_off_hours = weekly_off_hours * 4.33
    
    cost_per_hour = environment.resources.total_cost_per_hour()
    monthly_savings = monthly_off_hours * cost_per_hour
    
    return {
        "environment": environment.name,
        "weekly_off_hours": weekly_off_hours,
        "monthly_off_hours": monthly_off_hours,
        "cost_per_hour": cost_per_hour,
        "monthly_savings": monthly_savings,
        "annual_savings": monthly_savings * 12
    }
```

## Implementation
- Primary service: Orchestrator Agent (cog)
- Module: `services/orchestrator-agent/cogs/auto_shutdown_policies.py`
- CLI commands for policy management
- Integration with existing notification system
