# integration service

cross-platform integration features for infra pilot.

## features

### phase 0: security foundation
- authentication: jwt token generation/verification, api key management
- oauth2 flows: discord, minecraft, and dashboard account linking
- auth middleware: all endpoints protected with bearer token or api key

### authentication & users
- cross-platform authentication: oauth2 flow linking discord, minecraft, and dashboard accounts. token exchange. account linking.
- shared user management: unifiedusermanager with profile sync on login, role sync across platforms, user search api.
- shared user profiles: unified profile with discord name, minecraft uuid, stats, balance, achievements, bio, social links.

### messaging & notifications
- cross-platform messaging: message bridge discord↔minecraft. format conversion (markdown↔minecraft color codes). webhook-based.
- cross-platform notifications: extended crossplatformnotifier with user preferences, priority levels, digest mode.
- cross-platform commands: execute commands from any platform. permission-checked. audit logged.
- cross-platform events: server events broadcast across all platforms. player join/leave, achievements, votes.
- cross-platform alerts: unified alert system with delivery channels (discord, in-game, email, webhook).
- server announcement scheduler: schedule announcements across platforms. templates, recurrence.
- notification providers:
  - email — smtp delivery with tls support, multipart plain+html, configurable from address
  - webhook — http post with configurable method, headers, and json payload template
  - telegram — bot api message delivery with markdown formatting and web preview control
  - notificationmanager — central registry dispatching to multiple providers with per-channel results

### logging & monitoring
- unified logging system: extended unifiedlogger with centralized log aggregation, level filtering, search api, retention.
- cross-platform logging: log all cross-platform events. query api with filters.
- unified reporting system: reports spanning all services. usage, billing, security, performance reports.
- server logs integration: minecraft server logs → discord channel. filter by level. `/logs tail/search` support.
- server backup logs: centralized backup status. success/failure rate. backup logs query.

### resource & configuration
- unified permission system: central permission store. role-based inheritance. redis-backed cache (json file store).
- shared configuration management: extended sharedconfigmanager with versioning, diff, rollback, bulk update, validation, environment overlays.
- shared resource pools: pool cpu/ram/storage across vps. fair scheduling.

### backups & resources
- integrated backup system: cross-service coordination, atomic multi-service restore, verification.
- unified backup management: single view all backups. retention engine. backup logs.
- cross-platform backups: backups spanning multiple services. coordinated restore.
- resource synchronization: sync allocations across services. propagate pool updates.
- resource allocation management: unified view allocation vs usage. rebalance suggestions.

### metrics & coordination
- resource usage tracking: cost allocation, trend analysis, forecasting.
- unified metrics system: metrics aggregation from all services. prometheus export support.
- cross-platform statistics: aggregate stats across platforms. single unified view.
- resource scheduling coordination: coordinate maintenance, backups, scaling. conflict detection.
- resource optimization coordination: cross-service optimization. idle resource identification.

### integration features
- integrated monitoring system: single monitoring view, all services, all metrics. alert correlation.
- integrated maintenance system: cross-service maintenance windows. dependency-aware scheduling.
- integrated security system: centralized security monitoring. cross-platform suspicious activity alerts.
- integrated resource management: unified resource allocation dashboard. cost tracking.

## usage

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

## project structure

the service has been modularized into focused python modules under `src/`:

```
src/
├── __init__.py               # Package marker
├── alerts.py                 # Unified alert system (AlertManager)
├── announcements.py          # Announcement scheduler (AnnouncementScheduler)
├── api.py                    # HTTP API with aiohttp (Auth, Users, Notifications, ...)
├── auth.py                   # Authentication & security (AuthManager)
├── backup.py                 # Backup coordination (BackupManager)
├── commands.py               # Cross-platform commands (CommandExecutor)
├── events.py                 # Event broadcasting (EventBroadcaster)
├── integration.py            # Integration service startup/hooks
├── logging.py                # Unified logging (UnifiedLogger) with paginated log search API
├── messaging.py              # Message bridge Discord↔Minecraft (MessageBridge)
├── notification_providers.py # Notification providers: Email, Webhook, Telegram + NotificationManager
├── permissions.py            # Permission system (PermissionManager)
├── resource_tracker.py       # Resource usage tracking
└── users.py                  # User profiles & linking (UserProfileManager)
```

## environment variables

- `dashboard_url` - management dashboard url
- `discord_api_url` - discord service url
- `service_core_url` - service core url
- `orchestrator_url` - orchestrator agent url
- `discord_webhook` - discord webhook url
- `jwt_secret` - secret key for jwt token signing
- `integration_service_url` - this service url

## api endpoints

### auth
- `post /api/auth/login` - login, returns jwt token
- `post /api/auth/verify` - verify jwt token
- `post /api/auth/api-key` - create api key
- `post /api/auth/oauth2/{platform}` - oauth2 authorize
- `post /api/auth/oauth2/{platform}/callback` - oauth2 callback
- `post /api/auth/token-exchange` - exchange platform token
- `post /api/auth/2fa/setup` - start totp setup (returns qr code secret)
- `post /api/auth/2fa/verify-setup` - verify initial totp setup, enable 2fa
- `post /api/auth/2fa/verify` - verify totp during login (temp_token → jwt)
- `post /api/auth/2fa/disable` - disable 2fa (requires password)
- `get /api/auth/2fa/backup-codes` - get backup codes
- `post /api/auth/2fa/verify-backup` - verify backup code, bypass totp

### users
- `post /api/users` - create user
- `get /api/users/{email}` - get user
- `put /api/users/{email}` - update user
- `get /api/users/{email}/profile` - get unified profile
- `put /api/users/{email}/profile` - update profile
- `post /api/users/{email}/link` - link account
- `get /api/users/search` - search users
- `post /api/users/{email}/sync` - sync profile/roles

### notifications
- `post /api/notifications` - send notification
- `post /api/notifications/server-event` - server event notification
- `get /api/notifications/preferences/{user_id}` - get preferences
- `put /api/notifications/preferences/{user_id}` - update preferences
- `post /api/notifications/digest/{user_id}` - send digest
- `post /api/notifications/priority` - send with priority
- `post /api/notifications/test` - test notification delivery through specified channels (takes `channels` and `recipients` in json body)

### messaging
- `post /api/messaging/bridge` - bridge message (discord↔minecraft)
- `post /api/messaging/webhook/{platform}` - webhook processor
- `post /api/messaging/convert` - format conversion

### commands
- `post /api/commands/execute` - execute command
- `get /api/commands` - list commands
- `post /api/commands/register` - register command
- `get /api/commands/audit` - command audit log

### events
- `post /api/events/broadcast` - broadcast event
- `get /api/events` - list events
- `post /api/events/listener` - register listener
- `post /api/events/player/join` - player join event
- `post /api/events/player/leave` - player leave event
- `post /api/events/player/achievement` - achievement event
- `post /api/events/player/vote` - vote event

### alerts
- `post /api/alerts` - create alert
- `get /api/alerts` - get alerts
- `post /api/alerts/{alert_id}/acknowledge` - acknowledge alert
- `put /api/alerts/channels/{channel_type}` - configure channel

### announcements
- `post /api/announcements` - schedule announcement
- `get /api/announcements` - list scheduled
- `delete /api/announcements/{announcement_id}` - cancel
- `post /api/announcements/templates` - create template
- `get /api/announcements/templates` - get templates

### modpacks
- `get /api/modpacks/search?query=&platform=curseforge|modrinth` - search modpacks across curseforge and modrinth
- `get /api/modpacks/{platform}/{id}` - get modpack details with version manifest

### metrics
- `get /api/metrics` - get metrics
- `get /api/metrics/dashboard` - unified dashboard
- `get /api/metrics/prometheus` - prometheus format
- `get /api/metrics/statistics` - cross-platform stats

### config
- `get /api/config` - get config
- `put /api/config` - update config
- `get /api/config/version/{version}` - get version
- `post /api/config/rollback/{version}` - rollback
- `get /api/config/diff/{v1}/{v2}` - diff versions
- `post /api/config/validate` - validate config
- `post /api/config/overlay/{env_name}` - set overlay

### permissions
- `post /api/permissions/check` - check permission
- `post /api/permissions/grant` - grant permission
- `post /api/permissions/revoke` - revoke permission
- `get /api/permissions/user/{user_id}` - get user permissions
- `post /api/permissions/roles` - create role
- `post /api/permissions/roles/assign` - assign role

### backups
- `post /api/backups` - create backup
- `get /api/backups` - list backups
- `post /api/backups/restore` - restore backup
- `post /api/backups/verify` - verify backup
- `delete /api/backups/cleanup` - cleanup old backups
- `post /api/backups/cross-service` - cross-service backup
- `post /api/backups/cross-service/restore` - atomic restore
- `get /api/backups/logs` - backup logs
- `get /api/backups/stats` - backup stats

### resources
- `get /api/resources` - get all resources
- `post /api/resources/allocate` - allocate resource
- `post /api/resources/pools` - create pool
- `get /api/resources/pools` - list pools
- `post /api/resources/pools/allocate` - allocate from pool
- `post /api/resources/sync` - sync resources
- `get /api/resources/allocation` - allocation vs usage
- `get /api/resources/usage` - resource usage
- `get /api/resources/cost` - cost allocation
- `get /api/resources/trends` - trend analysis
- `get /api/resources/forecast` - forecast
- `get /api/resources/rebalance` - rebalance suggestions
- `post /api/resources/optimization/analyze` - optimization analysis
- `post /api/resources/schedule` - schedule event
- `get /api/resources/schedule` - get schedule

### logs
- `post /api/logs/search` - search logs
- `get /api/logs/levels` - log level counts
- `post /api/logs/cross-platform` - log cross-platform event
- `get /api/logs/cross-platform` - query cross-platform logs
- `post /api/logs/server/ingest` - ingest server log
- `get /api/logs/server/tail` - tail server logs
- `get /api/logs/backup` - backup logs
- `get /api/logs/backup/stats` - backup log stats

### monitoring, maintenance, security
- `get /api/monitoring` - integrated monitoring view
- `get /api/monitoring/alerts` - alert correlation
- `post /api/maintenance/windows` - create maintenance window
- `get /api/maintenance/windows` - list maintenance windows
- `get /api/security/events` - security events
- `post /api/security/alert` - report suspicious activity

### reports
- `post /api/reports/usage` - usage report
- `post /api/reports/billing` - billing report
- `post /api/reports/security` - security report
- `post /api/reports/performance` - performance report
- `get /api/reports` - list reports

### integrated
- `get /api/integrated/resource-management` - unified resource dashboard

## branding
- cosmic infra branding is the unified identity used across infra pilot. tokens: primary #6c5ce7, secondary #ec4899, accent #22d3ee.
- this service participates in branding across the ui and docs. logo variants exist and can be surfaced through shared branding assets.
