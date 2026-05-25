# Integration Service

Cross-platform integration features for Infra Pilot.

## Features

### Phase 0: Security Foundation
- **Authentication**: JWT token generation/verification, API key management
- **OAuth2 Flows**: Discord, Minecraft, and Dashboard account linking
- **Auth Middleware**: All endpoints protected with Bearer token or API key

### Authentication & Users
- **Cross-platform authentication**: OAuth2 flow linking Discord, Minecraft, and Dashboard accounts. Token exchange. Account linking.
- **Shared user management**: UnifiedUserManager with profile sync on login, role sync across platforms, user search API.
- **Shared user profiles**: Unified profile with Discord name, Minecraft UUID, stats, balance, achievements, bio, social links.

### Messaging & Notifications
- **Cross-platform messaging**: Message bridge Discord↔Minecraft. Format conversion (markdown↔Minecraft color codes). Webhook-based.
- **Cross-platform notifications**: Extended CrossPlatformNotifier with user preferences, priority levels, digest mode.
- **Cross-platform commands**: Execute commands from any platform. Permission-checked. Audit logged.
- **Cross-platform events**: Server events broadcast across all platforms. Player join/leave, achievements, votes.
- **Cross-platform alerts**: Unified alert system with delivery channels (Discord, in-game, email, webhook).
- **Server announcement scheduler**: Schedule announcements across platforms. Templates, recurrence.

### Logging & Monitoring
- **Unified logging system**: Extended UnifiedLogger with centralized log aggregation, level filtering, search API, retention.
- **Cross-platform logging**: Log all cross-platform events. Query API with filters.
- **Unified reporting system**: Reports spanning all services. Usage, billing, security, performance reports.
- **Server logs integration**: Minecraft server logs → Discord channel. Filter by level. `/logs tail/search` support.
- **Server backup logs**: Centralized backup status. Success/failure rate. Backup logs query.

### Resource & Configuration
- **Unified permission system**: Central permission store. Role-based inheritance. Redis-backed cache (JSON file store).
- **Shared configuration management**: Extended SharedConfigManager with versioning, diff, rollback, bulk update, validation, environment overlays.
- **Shared resource pools**: Pool CPU/RAM/storage across VPS. Fair scheduling.

### Backups & Resources
- **Integrated backup system**: Cross-service coordination, atomic multi-service restore, verification.
- **Unified backup management**: Single view all backups. Retention engine. Backup logs.
- **Cross-platform backups**: Backups spanning multiple services. Coordinated restore.
- **Resource synchronization**: Sync allocations across services. Propagate pool updates.
- **Resource allocation management**: Unified view allocation vs usage. Rebalance suggestions.

### Metrics & Coordination
- **Resource usage tracking**: Cost allocation, trend analysis, forecasting.
- **Unified metrics system**: Metrics aggregation from all services. Prometheus export support.
- **Cross-platform statistics**: Aggregate stats across platforms. Single unified view.
- **Resource scheduling coordination**: Coordinate maintenance, backups, scaling. Conflict detection.
- **Resource optimization coordination**: Cross-service optimization. Idle resource identification.

### Integration Features
- **Integrated monitoring system**: Single monitoring view, all services, all metrics. Alert correlation.
- **Integrated maintenance system**: Cross-service maintenance windows. Dependency-aware scheduling.
- **Integrated security system**: Centralized security monitoring. Cross-platform suspicious activity alerts.
- **Integrated resource management**: Unified resource allocation dashboard. Cost tracking.

## Usage

```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
python src/api.py

# Or run specific modules
python src/integration.py
python src/backup.py
python src/resource_tracker.py
```

## Project Structure

The service has been modularized into focused Python modules under `src/`:

```
src/
├── __init__.py          # Package marker
├── alerts.py            # Unified alert system (AlertManager)
├── announcements.py     # Announcement scheduler (AnnouncementScheduler)
├── auth.py              # Authentication & security (AuthManager)
├── commands.py          # Cross-platform commands (CommandExecutor)
├── events.py            # Event broadcasting (EventBroadcaster)
├── messaging.py         # Message bridge Discord↔Minecraft (MessageBridge)
├── permissions.py       # Permission system (PermissionManager)
├── users.py             # User profiles & linking (UserProfileManager)
```

## Environment Variables

- `DASHBOARD_URL` - Management dashboard URL
- `DISCORD_API_URL` - Discord service URL
- `SERVICE_CORE_URL` - Service Core URL
- `ORCHESTRATOR_URL` - Orchestrator agent URL
- `DISCORD_WEBHOOK` - Discord webhook URL
- `JWT_SECRET` - Secret key for JWT token signing
- `INTEGRATION_SERVICE_URL` - This service URL

## API Endpoints

### Auth
- `POST /api/auth/login` - Login, returns JWT token
- `POST /api/auth/verify` - Verify JWT token
- `POST /api/auth/api-key` - Create API key
- `POST /api/auth/oauth2/{platform}` - OAuth2 authorize
- `POST /api/auth/oauth2/{platform}/callback` - OAuth2 callback
- `POST /api/auth/token-exchange` - Exchange platform token

### Users
- `POST /api/users` - Create user
- `GET /api/users/{email}` - Get user
- `PUT /api/users/{email}` - Update user
- `GET /api/users/{email}/profile` - Get unified profile
- `PUT /api/users/{email}/profile` - Update profile
- `POST /api/users/{email}/link` - Link account
- `GET /api/users/search` - Search users
- `POST /api/users/{email}/sync` - Sync profile/roles

### Notifications
- `POST /api/notifications` - Send notification
- `POST /api/notifications/server-event` - Server event notification
- `GET /api/notifications/preferences/{user_id}` - Get preferences
- `PUT /api/notifications/preferences/{user_id}` - Update preferences
- `POST /api/notifications/digest/{user_id}` - Send digest
- `POST /api/notifications/priority` - Send with priority

### Messaging
- `POST /api/messaging/bridge` - Bridge message (Discord↔Minecraft)
- `POST /api/messaging/webhook/{platform}` - Webhook processor
- `POST /api/messaging/convert` - Format conversion

### Commands
- `POST /api/commands/execute` - Execute command
- `GET /api/commands` - List commands
- `POST /api/commands/register` - Register command
- `GET /api/commands/audit` - Command audit log

### Events
- `POST /api/events/broadcast` - Broadcast event
- `GET /api/events` - List events
- `POST /api/events/listener` - Register listener
- `POST /api/events/player/join` - Player join event
- `POST /api/events/player/leave` - Player leave event
- `POST /api/events/player/achievement` - Achievement event
- `POST /api/events/player/vote` - Vote event

### Alerts
- `POST /api/alerts` - Create alert
- `GET /api/alerts` - Get alerts
- `POST /api/alerts/{alert_id}/acknowledge` - Acknowledge alert
- `PUT /api/alerts/channels/{channel_type}` - Configure channel

### Announcements
- `POST /api/announcements` - Schedule announcement
- `GET /api/announcements` - List scheduled
- `DELETE /api/announcements/{announcement_id}` - Cancel
- `POST /api/announcements/templates` - Create template
- `GET /api/announcements/templates` - Get templates

### Metrics
- `GET /api/metrics` - Get metrics
- `GET /api/metrics/dashboard` - Unified dashboard
- `GET /api/metrics/prometheus` - Prometheus format
- `GET /api/metrics/statistics` - Cross-platform stats

### Config
- `GET /api/config` - Get config
- `PUT /api/config` - Update config
- `GET /api/config/version/{version}` - Get version
- `POST /api/config/rollback/{version}` - Rollback
- `GET /api/config/diff/{v1}/{v2}` - Diff versions
- `POST /api/config/validate` - Validate config
- `POST /api/config/overlay/{env_name}` - Set overlay

### Permissions
- `POST /api/permissions/check` - Check permission
- `POST /api/permissions/grant` - Grant permission
- `POST /api/permissions/revoke` - Revoke permission
- `GET /api/permissions/user/{user_id}` - Get user permissions
- `POST /api/permissions/roles` - Create role
- `POST /api/permissions/roles/assign` - Assign role

### Backups
- `POST /api/backups` - Create backup
- `GET /api/backups` - List backups
- `POST /api/backups/restore` - Restore backup
- `POST /api/backups/verify` - Verify backup
- `DELETE /api/backups/cleanup` - Cleanup old backups
- `POST /api/backups/cross-service` - Cross-service backup
- `POST /api/backups/cross-service/restore` - Atomic restore
- `GET /api/backups/logs` - Backup logs
- `GET /api/backups/stats` - Backup stats

### Resources
- `GET /api/resources` - Get all resources
- `POST /api/resources/allocate` - Allocate resource
- `POST /api/resources/pools` - Create pool
- `GET /api/resources/pools` - List pools
- `POST /api/resources/pools/allocate` - Allocate from pool
- `POST /api/resources/sync` - Sync resources
- `GET /api/resources/allocation` - Allocation vs usage
- `GET /api/resources/usage` - Resource usage
- `GET /api/resources/cost` - Cost allocation
- `GET /api/resources/trends` - Trend analysis
- `GET /api/resources/forecast` - Forecast
- `GET /api/resources/rebalance` - Rebalance suggestions
- `POST /api/resources/optimization/analyze` - Optimization analysis
- `POST /api/resources/schedule` - Schedule event
- `GET /api/resources/schedule` - Get schedule

### Logs
- `POST /api/logs/search` - Search logs
- `GET /api/logs/levels` - Log level counts
- `POST /api/logs/cross-platform` - Log cross-platform event
- `GET /api/logs/cross-platform` - Query cross-platform logs
- `POST /api/logs/server/ingest` - Ingest server log
- `GET /api/logs/server/tail` - Tail server logs
- `GET /api/logs/backup` - Backup logs
- `GET /api/logs/backup/stats` - Backup log stats

### Monitoring, Maintenance, Security
- `GET /api/monitoring` - Integrated monitoring view
- `GET /api/monitoring/alerts` - Alert correlation
- `POST /api/maintenance/windows` - Create maintenance window
- `GET /api/maintenance/windows` - List maintenance windows
- `GET /api/security/events` - Security events
- `POST /api/security/alert` - Report suspicious activity

### Reports
- `POST /api/reports/usage` - Usage report
- `POST /api/reports/billing` - Billing report
- `POST /api/reports/security` - Security report
- `POST /api/reports/performance` - Performance report
- `GET /api/reports` - List reports

### Integrated
- `GET /api/integrated/resource-management` - Unified resource dashboard

## Branding
- Cosmic Infra branding is the unified identity used across Infra Pilot. Tokens: Primary #6C5CE7, Secondary #EC4899, Accent #22D3EE.
- This service participates in branding across the UI and docs. Logo variants exist and can be surfaced through shared branding assets.
