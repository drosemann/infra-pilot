# Feature 14: Idle Resource Reclamation

## Overview
Detect zombie containers, unused volumes, orphaned networks, and other idle resources. Auto-cleanup with approval, with weekly savings reports.

## Capabilities
- Zombie container detection (exited, paused, or unused for N days)
- Unused volume detection (not mounted by any container)
- Orphaned network detection (no connected containers)
- Dangling image detection (untagged/unused images)
- Unused snapshot detection (older than retention policy)
- Orphaned service files (systemd units for removed containers)
- Stale cache detection (build cache, package cache)
- Approval workflow before cleanup
- Dry-run mode for safe evaluation
- Weekly savings report with disk space and cost recovery

## Detection Rules

| Resource | Detection Criteria | Default Age |
|----------|-------------------|-------------|
| Zombie Container | Status: exited/created | > 7 days |
| Unused Volume | Not mounted by any container | > 14 days |
| Orphaned Network | Zero connected containers | > 3 days |
| Dangling Image | No tag, no dependents | > 30 days |
| Unused Snapshot | Not in retention policy | > 90 days |
| Stale Build Cache | Older than last successful build | > 30 days |
| Orphaned Config | No corresponding container | > 7 days |

## Approval Workflow

```python
class ReclamationPolicy:
    """Policy for automatic or manual reclamation."""
    
    MODES = {
        "manual": "Generate report only, no auto-cleanup",
        "approval": "Propose cleanup, require approval",
        "auto_safe": "Auto-cleanup for clearly unused resources",
        "auto_aggressive": "Auto-cleanup everything matching rules"
    }
    
    def check_resource(self, resource: Resource) -> CleanupAction:
        mode = self.get_mode(resource.type)
        
        if mode == "manual":
            return CleanupAction(ReportOnly())
        
        elif mode == "approval":
            return CleanupAction(
                Quarantine(resource),
                Notification("Resources quarantined, approve?")
            )
        
        elif mode == "auto_safe":
            if resource.is_safe_to_remove():
                return CleanupAction(Remove())
            return CleanupAction(ReportOnly())
        
        elif mode == "auto_aggressive":
            return CleanupAction(Remove())
```

## Savings Report

```
Weekly Reclamation Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Week: May 25-31, 2026

Resources Identified: 47
Resources Cleaned:    42 (89%)
Resources Pending:    5 (awaiting approval)

Disk Space Recovered:  128.5 GB
Cost Savings:          $12.85/month

Breakdown:
┌──────────────────────┬────────┬──────────┬──────────┐
│ Resource Type        │ Count  │ Space    │ Savings  │
├──────────────────────┼────────┼──────────┼──────────┤
│ Zombie Containers    │ 12     │ 4.2 GB   │ $0.42    │
│ Unused Volumes       │ 8      │ 85.3 GB  │ $8.53    │
│ Dangling Images      │ 25     │ 32.7 GB  │ $3.27    │
│ Orphaned Networks    │ 2      │ 0.0 GB   │ $0.00    │
│ Stale Build Cache    │ 0      │ 6.3 GB   │ $0.63    │
└──────────────────────┴────────┴──────────┴──────────┘

Yearly Projection:      1,542 GB recovered, ~$154 saved
```

## Implementation
- Primary service: Orchestrator Agent (cog)
- Module: `services/orchestrator-agent/cogs/idle_resource_reclamation.py`
- CLI commands for reclamation management
- Integration with existing cleanup cog
