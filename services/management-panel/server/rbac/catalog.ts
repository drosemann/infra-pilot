/**
 * Permission catalog for the panel RBAC layer.
 *
 * A single source of truth that:
 * - defines which role grants which `resource:action` permission,
 * - translates the legacy six-boolean `ServerPermissionSet` (and the
 *   WebSocket action vocabulary from `server/ws/types.ts`) onto it,
 * - classifies resources as app-scoped, personal (row-owner-only), or
 *   instance-level so the middleware in `middleware.ts` can pick the right
 *   check semantics.
 *
 * Ghost/star permissions (`app:*`) mean "every action of that resource".
 * Never grant `secrets:*` to operators: secret material stays personal or
 * instance-admin territory (SECURITY.md "who can do what").
 */
import type {
  AppRole,
  InstanceRole,
  Permission,
  ResourceAction,
  ResourceType,
  ServerPermissionSet,
} from './types.ts';

export const ALL_ACTIONS: readonly ResourceAction[] = [
  'read',
  'write',
  'manage',
  'exec',
  'delete',
  'export',
];

/**
 * Resource scopes:
 * - `app`   — guarded through an app id; ownership, app assignment, and
 *             instance role all participate in the decision.
 * - `personal` — rows belong to exactly one user; self-ownership is a
 *             sufficient grant, instance roles cannot widen past it.
 * - `instance` — instance resources; roles (mostly admin) decide.
 */
export type ResourceScope = 'app' | 'personal' | 'instance';

export const RESOURCE_SCOPES: Record<ResourceType, ResourceScope> = {
  app: 'app',
  backup: 'app',
  deployment: 'app',
  config: 'app',
  metrics: 'app',
  inventory: 'personal',
  databases: 'personal',
  webhooks: 'personal',
  plugins: 'personal',
  templates: 'instance',
  ssh: 'personal',
  maintenance: 'app',
  secrets: 'personal',
  members: 'app',
  billing: 'personal',
  runbooks: 'personal',
  audit: 'personal',
  settings: 'instance',
  notifications: 'personal',
  organization: 'personal',
  apikeys: 'personal',
  customers: 'personal',
  reports: 'personal',
};

/** Scope getter the store relies on; throws on unknown types as a bug hedge. */
export function resourceScopeForType(resourceType: ResourceType): ResourceScope {
  const scope = RESOURCE_SCOPES[resourceType];
  if (!scope) throw new Error(`rbac: unknown resource type ${String(resourceType)}`);
  return scope;
}

/**
 * Wildcard grant: confers every action on every resource type. Used by
 * instance admins, app owners, and app-level `admin` roles.
 */
export const ALL_RESOURCES_GRANTS: Permission[] = ['*'] as unknown as Permission[];

/**
 * Role → permission shadow tables. Instance admins get a wildcard entry.
 * Operators may execute but not alter instance security state; viewers get
 * read-only visibility shades.
 */
export const INSTANCE_ROLE_GRANTS: Record<InstanceRole, Permission[]> = {
  admin: ALL_RESOURCES_GRANTS,
  operator: [
    // visibility
    'app:read', 'backup:read', 'deployment:read', 'config:read', 'metrics:read',
    'inventory:read', 'databases:read', 'maintenance:read', 'notifications:read',
    'runbooks:read', 'organization:read', 'settings:read', 'templates:read',
    // operations
    'app:write', 'app:exec', 'app:delete', 'backup:write', 'deployment:write',
    'config:write', 'maintenance:write', 'notifications:write', 'runbooks:exec',
  ],
  viewer: [
    'app:read', 'backup:read', 'deployment:read', 'config:read', 'metrics:read',
    'inventory:read', 'databases:read', 'maintenance:read', 'notifications:read',
    'runbooks:read', 'organization:read', 'settings:read', 'templates:read',
  ],
};

/** Per-app role shadows (applied only to app-scoped resources). */
export const APP_ROLE_GRANTS: Record<AppRole, Permission[]> = {
  owner: ALL_RESOURCES_GRANTS,
  admin: ALL_RESOURCES_GRANTS,
  operator: INSTANCE_ROLE_GRANTS.operator,
  viewer: INSTANCE_ROLE_GRANTS.viewer,
  custom: [], // decided by the six-boolean mapping below
};

/**
 * Legacy boolean permission set → modern permission list. The WebSocket
 * gateway previously interpreted these booleans as the only access signal;
 * `console` still carries the same meaning (log tailing + terminal).
 * Every operational boolean also carries `metrics:read` so members who
 * can act on a server can still see its charts.
 */
export const SERVER_PERMISSION_MAP: Partial<
  Record<keyof ServerPermissionSet, Permission[]>
> = {
  start: ['app:exec', 'metrics:read'],
  stop: ['app:exec', 'metrics:read'],
  console: ['app:write', 'app:exec', 'config:write', 'config:read', 'metrics:read'],
  files: ['app:read', 'app:exec', 'config:read', 'metrics:read'],
  backups: ['backup:write', 'backup:read', 'metrics:read'],
  deployments: ['deployment:write', 'deployment:read', 'metrics:read'],
};

/** Personal-resource grants still meaningful to non-admin instance roles.
 * Instance-scoped resources deliberately carry empty lists here: self
 * ownership is meaningless on global rows, and `canSelf()` must never
 * grant on them. */
export const PERSONAL_SELF_ACTIONS: Record<ResourceType, readonly ResourceAction[]> = {
  app: ALL_ACTIONS,
  backup: ALL_ACTIONS,
  deployment: ALL_ACTIONS,
  config: ALL_ACTIONS,
  metrics: ALL_ACTIONS,
  inventory: ALL_ACTIONS,
  databases: ALL_ACTIONS,
  webhooks: ALL_ACTIONS,
  plugins: ALL_ACTIONS,
  templates: [],
  ssh: ALL_ACTIONS,
  maintenance: ALL_ACTIONS,
  secrets: ALL_ACTIONS,
  members: [],
  billing: [],
  runbooks: ['read', 'write', 'exec', 'delete'],
  audit: ['read', 'write'],
  settings: [],
  notifications: ALL_ACTIONS,
  organization: [],
  apikeys: ALL_ACTIONS,
  customers: ALL_ACTIONS,
  reports: ['read', 'write', 'export'],
};

/**
 * Whether the given combinable grants confer `resourceType:action`.
 * `true` entries act as wildcards for the entire catalog.
 */
export function grantsCover(
  grants: (Permission | string)[],
  resourceType: ResourceType,
  action: ResourceAction,
): boolean {
  for (const grant of grants) {
    if (grant === '*') return true;
    const sep = grant.indexOf(':');
    if (sep <= 0) continue;
    const res = grant.substring(0, sep);
    const act = grant.substring(sep + 1);
    if (res !== resourceType && res !== '*') continue;
    if (act === action || act === '*') return true;
  }
  return false;
}

/**
 * Turn the legacy boolean set into an equivalent permission list.
 * @returns e.g. `{ console: true, backups: true }` → `['app:write', 'app:exec', 'backup:write', 'backup:read']`
 */
export function serverPermissionsToGrants(
  perms: Partial<ServerPermissionSet> | null | undefined,
): Permission[] {
  if (!perms) return [];
  const out: Permission[] = [];
  for (const key of Object.keys(SERVER_PERMISSION_MAP) as (keyof ServerPermissionSet)[]) {
    if (perms[key] === true) out.push(...(SERVER_PERMISSION_MAP[key] as Permission[]));
  }
  return out;
}

/**
 * Resolve a single role's grants.
 * @returns Wildcard entries verbatim so callers can detect full access.
 */
export function roleGrants(role: AppRole | InstanceRole, isAppScoped: boolean): Permission[] {
  let grants: Permission[];
  if (isInstanceRole(role)) grants = INSTANCE_ROLE_GRANTS[role];
  else grants = isAppScoped ? APP_ROLE_GRANTS[role] : [];
  return grants;
}

/**
 * Runtime type guard (not the DB CHECK contract): only real instance roles
 * may appear on `rbac_instance_roles` rows.
 */
export function isInstanceRole(value: unknown): value is InstanceRole {
  return value === 'admin' || value === 'operator' || value === 'viewer';
}

/**
 * Runtime type guard for app roles (superset includes `owner`).
 */
export function isAppRole(value: unknown): value is AppRole {
  return value === 'owner' || value === 'admin' || value === 'operator' || value === 'viewer' || value === 'custom';
}

/**
 * Validate a client-supplied app role for persistence. Persisted `owner`
 * values still imply full control, but they are normalized to `admin`
 * because ownership must follow `docker_apps.user_id`, never an
 * assignment row.
 * @returns The validated literal, or null when not assignable.
 */
export function normalizeAppRole(value: unknown): AppRole | null {
  if (value === 'owner') return 'admin';
  if (!isAppRole(value)) return null;
  return value;
}
