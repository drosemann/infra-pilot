/**
 * Panel RBAC data model.
 *
 * The panel authorizes every request in two layers:
 *
 * 1. Authentication (`verifyAuth` in `server/index.ts`) — proves the caller
 *    is a real user (Supabase JWT or scrypt-hashed API key).
 * 2. Authorization (this module) — decides whether that user may perform a
 *    concrete action on a concrete resource type.
 *
 * Roles are strings from a fixed vocabulary so the database CHECK
 * constraints in `db/schema.sql` and the permission catalog in
 * `catalog.ts` stay in sync. `custom` app roles additionally carry the
 * legacy six-boolean `ServerPermissionSet` (start/stop/console/files/
 * backups/deployments) inherited from the WebSocket ACL; the catalog
 * translates those booleans into the shared action vocabulary.
 */

/** Instance-level role assignments (whole-panel scope). */
export type InstanceRole = 'admin' | 'operator' | 'viewer';

/** Per-app role assignments. `owner` is implicit for `docker_apps.user_id`
 * and never persisted — it only appears in API responses for clarity. */
export type AppRole = 'admin' | 'operator' | 'viewer' | 'custom' | 'owner';

/** Any role accepted by the assignment APIs. */
export type RbacRole = InstanceRole | AppRole;

/** Resource families a permission can be granted on. */
export type ResourceType =
  | 'app'
  | 'backup'
  | 'deployment'
  | 'config'
  | 'secrets'
  | 'members'
  | 'billing'
  | 'runbooks'
  | 'audit'
  | 'settings'
  | 'metrics'
  | 'inventory'
  | 'databases'
  | 'webhooks'
  | 'plugins'
  | 'templates'
  | 'ssh'
  | 'maintenance'
  | 'notifications'
  | 'organization'
  | 'apikeys'
  | 'customers'
  | 'reports';

/** Concrete operations (the shared vocabulary; `ws:` actions map onto it). */
export type ResourceAction = 'read' | 'write' | 'manage' | 'exec' | 'delete' | 'export';

/** A permission grant in `resource:action` form, e.g. `app:read`. */
export type Permission = `${ResourceType}:${ResourceAction}`;

/** Legacy six-boolean permission set from the original per-app roles API. */
export type ServerPermissionSet = {
  start: boolean;
  stop: boolean;
  console: boolean;
  files: boolean;
  backups: boolean;
  deployments: boolean;
};

/** One persisted instance-level assignment (mirrors `rbac_instance_roles`). */
export interface InstanceRoleAssignment {
  id: string;
  userId: string;
  role: InstanceRole;
  grantedBy?: string | null;
  createdAt: string;
  updatedAt: string;
}

/** One persisted per-app assignment (mirrors `rbac_app_roles`). */
export interface AppRoleAssignment {
  id: string;
  appId: string;
  userId: string;
  role: AppRole;
  permissions?: Partial<ServerPermissionSet>;
  grantedBy?: string | null;
  createdAt: string;
  updatedAt: string;
}

/** Wire shape of the legacy `/api/apps/:appId/roles` endpoints; field names
 * are preserved so existing panel pages keep working. */
export interface AppRoleAssignmentWire {
  id: string;
  appId: string;
  principal: string;
  role: AppRole;
  permissions: ServerPermissionSet;
  createdAt: string;
}

/** Denial semantics surfaced by 403 responses. */
export interface RbacDenial {
  code: 'rbac_denied';
  resourceType: ResourceType;
  action: ResourceAction;
  reason:
    | 'ownership_only'
    | 'instance_role'
    | 'app_role'
    | 'no_assignment'
    | 'not_found';
}
