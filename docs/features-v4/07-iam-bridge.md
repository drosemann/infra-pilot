# Feature 7: Multi-Cloud IAM Bridge

## Overview
Synchronize roles and policies across AWS IAM, Azure AD, GCP IAM. Single policy definition compiled to each provider. Access review across clouds.

## Components
- `iam_bridge.py` — Policy synchronizer, role mapper
- `IAMBridgeCog` — Discord commands for IAM bridge
- `IAMBridge.tsx` — React policy synchronization UI
- CLI commands in `cli/ipilot/commands/hybrid_cloud/iam_bridge.py`

## API Endpoints
- `GET /api/iam/mappings` — List role mappings
- `POST /api/iam/mappings` — Create mapping
- `POST /api/iam/sync` — Sync all mappings
- `GET /api/iam/roles` — List roles
- `GET /api/iam/policies` — List policies
- `POST /api/iam/policies` — Create policy

## Policy Compilation
Single policy document compiled to:
- AWS: IAM Policy with Version/Statement
- Azure: Custom Role with permissions/actions
- GCP: Custom Role with includedPermissions
