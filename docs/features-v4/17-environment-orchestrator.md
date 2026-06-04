# Feature 17: Environment Orchestrator

## Overview
Ephemeral environment lifecycle management with TTL-based auto-cleanup, supporting on-demand preview and testing environments.

## Components
- `environment_orchestrator.py` - Environment lifecycle manager
- `environments_cog.py` - Discord bot commands

## Data Models
- `Environment` - Ephemeral environment with status, TTL, and URL
- `EnvironmentTemplate` - Environment blueprint definition
- `LifecycleEvent` - Environment lifecycle event log

## Lifecycle States
- Creating -> Running -> Expiring -> Expired/Deleted

## CLI Commands
- `ipilot environments list` - List environments
- `ipilot environments create` - Create environment
- `ipilot environments get` - Get environment details
- `ipilot environments delete` - Delete environment
- `ipilot environments extend` - Extend TTL
- `ipilot environments summary` - Environment stats
