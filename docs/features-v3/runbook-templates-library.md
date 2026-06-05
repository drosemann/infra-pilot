# Feature 78: Runbook Templates Library

## Overview
Community-contributed runbook template library with versioning, search, categorization, and one-click instantiation for common operational procedures.

## Components
- `runbook_library.py` - Core library management
- `runbook_validator.py` - Template validation
- `runbook_renderer.py` - Template rendering with variables
- `runbook_routes.py` - API endpoints
- `RunbookLibraryManager` - Manager class

## Runbook Categories
- **Incident Response**: Security incident, Service outage, Data breach
- **Maintenance**: Database migration, Certificate renewal, OS patching
- **Deployment**: Blue-green deploy, Canary release, Rollback
- **Monitoring**: Alert response, Threshold tuning, Dashboard setup
- **Backup/Restore**: Database backup, File restore, DR failover
- **Security**: Key rotation, Access review, Vulnerability remediation
- **Networking**: Firewall rule, DNS change, Load balancer config
- **Storage**: Volume expansion, Snapshot management, Migration

## Template Format (YAML)
```yaml
name: Database Migration Rollback
version: 1.2.0
category: maintenance
author: SRE Team
description: Rollback a failed database migration
variables:
  db_name:
    type: string
    description: Database name
    required: true
  migration_version:
    type: string
    description: Version to rollback to
    required: true
steps:
  - name: Check current status
    command: "migrate status -db {{db_name}}"
    expected: "FAILED"
  - name: Execute rollback
    command: "migrate rollback -db {{db_name}} -to {{migration_version}}"
    timeout: 300
  - name: Verify
    command: "migrate status -db {{db_name}}"
    expected: "OK"
rollback:
  - name: Re-apply failed migration
    command: "migrate up -db {{db_name}}"
```

## API Endpoints
- `GET /api/v1/runbook-templates` - List templates
- `POST /api/v1/runbook-templates` - Create template
- `GET /api/v1/runbook-templates/{id}` - Get template
- `PUT /api/v1/runbook-templates/{id}` - Update template
- `DELETE /api/v1/runbook-templates/{id}` - Delete template
- `POST /api/v1/runbook-templates/{id}/instantiate` - Instantiate
- `GET /api/v1/runbook-templates/search` - Search templates
- `POST /api/v1/runbook-templates/{id}/vote` - Rate template
- `GET /api/v1/runbook-templates/categories` - List categories
