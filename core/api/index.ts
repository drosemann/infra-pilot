/**
 * Infra Pilot API — Core entry point.
 *
 * The canonical API source is services/management-panel/server/index.ts.
 * This directory documents the intended modular architecture:
 *
 * core/api/
 *   index.ts          — Express bootstrap, middleware, WebSocket (this file)
 *   routes/
 *     auth.ts         — Authentication + 2FA
 *     apps.ts         — Container CRUD + lifecycle (start/stop/restart/logs)
 *     config.ts       — Config read/write/validate + versions
 *     backups.ts      — Backup jobs
 *     metrics.ts      — Resource metrics + health checks
 *     logs.ts         — Access logs
 *     alerts.ts       — Alert configs + history
 *     deployments.ts  — Deployment management
 *     databases.ts    — Database management
 *     modpacks.ts     — Modpack installer
 *     workspaces.ts   — Workspace management
 *     customers.ts    — Customer CRUD
 *     audit.ts        — Audit trail
 *     notifications.ts— Notification channels
 *     reports.ts      — Basic reports
 *     tasks.ts        — Scheduled tasks
 *     maintenance.ts  — Maintenance windows
 *     search.ts       — Global search
 *
 * Future: Split server/index.ts into these route modules.
 * See services/management-panel/server/index.ts for current implementation.
 */
