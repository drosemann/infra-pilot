# Feature 67: Audit Management

## Overview
Schedule and manage compliance audits with customer audit right tracking. Supports internal, customer, and regulatory audit types.

## Components
- **Integration Module**: `AuditManagementEngine` — scheduling, rights management, status tracking
- **Orchestrator Cog**: `audit_management_cog.py`
- **Management Panel**: `AuditManagement.tsx`
- **CLI Commands**: `audit-mgmt list|schedule|rights|stats`

## Key Features
- Audit schedule creation (internal/customer/regulatory)
- Customer audit right registration
- Status lifecycle (scheduled → in_progress → completed)
- Overdue detection
