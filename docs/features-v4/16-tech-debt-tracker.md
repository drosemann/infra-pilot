# Feature 16: Tech Debt Tracker

## Overview
Automated tech debt detection and tracking system with severity-weighted scoring, effort estimation, and remediation workflow management.

## Components
- `tech_debt_tracker.py` - Tech debt manager with scoring
- `tech_debt_cog.py` - Discord bot commands

## Data Models
- `TechDebtItem` - Individual debt item with severity, effort, and remediation status
- `DebtScore` - Aggregate scoring with principal and interest calculations

## Severity Levels
- **Critical** - Security or stability impact
- **High** - Significant maintenance burden
- **Medium** - Moderate code quality issues
- **Low** - Minor improvements

## CLI Commands
- `ipilot techdebt list` - List debt items
- `ipilot techdebt report` - Report new item
- `ipilot techdebt get` - Get item details
- `ipilot techdebt fix` - Mark as fixed
- `ipilot techdebt summary` - Summary with totals
