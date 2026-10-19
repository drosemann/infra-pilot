/**
 * Panel RBAC entry point (`server/rbac/`).
 *
 * ```
 * const { store, guards } = createRbac({ client: supabase, audit: logAudit });
 * router.post('/api/...', verifyAuth, guards.requireAppRole('exec'), handler);
 * ```
 *
 * See `wiki/11-Auth-Matrix.md` for the route-level decision table and
 * `SECURITY.md` "who can do what" for boundary rules.
 */
export {
  ALL_ACTIONS,
  ALL_RESOURCES_GRANTS,
  APP_ROLE_GRANTS,
  INSTANCE_ROLE_GRANTS,
  PERSONAL_SELF_ACTIONS,
  RESOURCE_SCOPES,
  SERVER_PERMISSION_MAP,
  grantsCover,
  isAppRole,
  isInstanceRole,
  normalizeAppRole,
  resourceScopeForType,
  roleGrants,
  serverPermissionsToGrants,
} from './catalog.ts';
export { actorId, createRbacGuards } from './middleware.ts';
export type { RbacAuditFn, RbacGuardOptions } from './middleware.ts';
export { RbacStore } from './store.ts';
export type { RbacDecision, RbacStoreOptions, WsActionName } from './store.ts';
export type {
  AppRole,
  AppRoleAssignment,
  AppRoleAssignmentWire,
  InstanceRole,
  InstanceRoleAssignment,
  Permission,
  ResourceAction,
  ResourceType,
  RbacRole,
  RbacDenial,
  ServerPermissionSet,
} from './types.ts';
