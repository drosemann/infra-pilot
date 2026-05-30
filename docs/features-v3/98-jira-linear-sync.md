# Feature 98: Jira/Linear Integration

## Overview
Bidirectional ticket synchronization between Jira and Linear with configurable status/field mappings and webhook-based real-time sync.

## Capabilities
- Bidirectional, to-external, and from-external sync directions
- Status mapping: map statuses between systems
- Field mapping: map custom fields
- Webhook handling for real-time updates
- Conflict detection and resolution
- Sync history and audit log
- Connection testing with credential validation

## Backend API
- `GET /api/v1/sync/configs` - list sync configs
- `POST /api/v1/sync/configs` - create sync config
- `PUT /api/v1/sync/configs/:id` - update config
- `DELETE /api/v1/sync/configs/:id` - delete config
- `POST /api/v1/sync/configs/:id/test` - test connection
- `POST /api/v1/sync/webhook/jira` - Jira webhook receiver
- `POST /api/v1/sync/webhook/linear` - Linear webhook receiver
