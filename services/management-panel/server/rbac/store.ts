/**
 * Persistence + caching layer for panel RBAC (`server/rbac/`).
 *
 * Assignments live in Supabase (`rbac_instance_roles`, `rbac_app_roles`;
 * see `db/schema.sql`). Reads are cached in-memory with a short TTL so the
 * hot request path does not pay a database round trip per check, while
 * writes invalidate the affected cache entry immediately — a revoked admin
 * loses access within one cache TTL even if a stale read races the write.
 *
 * The store is intentionally the SINGLE decision point for authorization:
 * both the HTTP middleware (`middleware.ts`) and the WebSocket gateway's
 * injected `resolveAppAccess` resolver call `can()` here, so HTTP and WS
 * cannot drift apart.
 */
import type { SupabaseClient } from '@supabase/supabase-js';
import {
  grantsCover,
  isInstanceRole,
  normalizeAppRole,
  resourceScopeForType,
  serverPermissionsToGrants,
  PERSONAL_SELF_ACTIONS,
  roleGrants,
} from './catalog.ts';
import type {
  AppRole,
  AppRoleAssignment,
  AppRoleAssignmentWire,
  InstanceRole,
  InstanceRoleAssignment,
  ResourceAction,
  ResourceType,
  ServerPermissionSet,
} from './types.ts';

/** WS action names reuse their catalog counterparts (`ws logs:read` = `log read`). */
export type WsActionName = 'logs:read' | 'metrics:read' | 'terminal:write' | 'terminal:exec';

export interface RbacStoreOptions {
  /** Cache entries older than this are re-read (default 30s; owners 15s). */
  cacheTtlMs?: number;
}

/** Result of an authorization decision. */
export interface RbacDecision {
  allowed: boolean;
  reason:
    | 'owner'
    | 'instance_role'
    | 'app_role'
    | 'self_row'
    | 'no_assignment'
    | 'unknown_role'
    | 'app_not_found';
}

const OWNER_TTL_FACTOR = 0.5;

type WithExpiry<T> = { value: T; expiresAt: number };

export class RbacStore {
  private client: SupabaseClient;
  private instanceCache = new Map<string, WithExpiry<InstanceRoleAssignment | null>>();
  private appAssignmentCache = new Map<string, WithExpiry<AppRoleAssignment[]>>();
  private ownerCache = new Map<string, WithExpiry<string | null>>();
  private appRowCache = new Map<string, WithExpiry<any | null>>();
  private readonly cacheTtlMs: number;
  private bootstrapPromise: Promise<void> | null = null;

  constructor(client: SupabaseClient, options: RbacStoreOptions = {}) {
    this.client = client;
    this.cacheTtlMs = options.cacheTtlMs ?? 30_000;
  }

  /** Swap the underlying client (used when the host re-wires Supabase). */
  setClient(client: SupabaseClient): void {
    this.client = client;
    this.invalidateAll();
  }

  private cached<T>(map: Map<string, WithExpiry<T>>, key: string, ttlMs: number): T | undefined {
    const hit = map.get(key);
    if (!hit) return undefined;
    if (Date.now() > hit.expiresAt) return undefined;
    return hit.value;
  }

  private store<T>(map: Map<string, WithExpiry<T>>, key: string, value: T, ttlMs: number): void {
    map.set(key, { value, expiresAt: Date.now() + ttlMs });
  }

  /** Drop every cached entry (tests, client swaps, emergency flush). */
  invalidateAll(): void {
    this.instanceCache.clear();
    this.appAssignmentCache.clear();
    this.ownerCache.clear();
    this.appRowCache.clear();
  }

  // ------------------------------------------------------------------
  // Instance roles
  // ------------------------------------------------------------------

  /**
   * Fetch the instance role for a user.
   * @returns The assignment or null when the user has none.
   */
  async getInstanceRole(userId: string): Promise<InstanceRoleAssignment | null> {
    const key = String(userId || '');
    if (!key) return null;
    const hit = this.cached(this.instanceCache, key, this.cacheTtlMs);
    if (hit !== undefined) return hit;
    const { data, error } = await this.client
      .from('rbac_instance_roles')
      .select('id, user_id, role, granted_by, created_at, updated_at')
      .eq('user_id', key)
      .maybeSingle();
    if (error) throw new Error(`rbac: instance role lookup failed: ${error.message}`);
    const value: InstanceRoleAssignment | null = data
      ? {
          id: data.id,
          userId: data.user_id,
          role: data.role,
          grantedBy: data.granted_by,
          createdAt: data.created_at,
          updatedAt: data.updated_at,
        }
      : null;
    this.store(this.instanceCache, key, value, this.cacheTtlMs);
    return value;
  }

  /** Instance role as a literal, or null when unassigned. */
  async getRoleOrNone(userId: string): Promise<InstanceRole | null> {
    const row = await this.getInstanceRole(userId);
    return row && isInstanceRole(row.role) ? row.role : null;
  }

  /** List every instance-level assignment (admin UI). */
  async listInstanceRoles(): Promise<InstanceRoleAssignment[]> {
    const { data, error } = await this.client
      .from('rbac_instance_roles')
      .select('id, user_id, role, granted_by, created_at, updated_at')
      .order('created_at', { ascending: true });
    if (error) throw new Error(`rbac: instance role list failed: ${error.message}`);
    return (data || []).map((row: any) => ({
      id: row.id,
      userId: row.user_id,
      role: row.role,
      grantedBy: row.granted_by,
      createdAt: row.created_at,
      updatedAt: row.updated_at,
    }));
  }

  /** Create or update an instance role; exactly one row per user. */
  async setInstanceRole(userId: string, role: InstanceRole, grantedBy: string): Promise<InstanceRoleAssignment> {
    if (!isInstanceRole(role)) throw new Error('rbac: role must be admin|operator|viewer');
    const patch = { role, granted_by: grantedBy, updated_at: new Date().toISOString() };
    const { data, error } = await this.client
      .from('rbac_instance_roles')
      .upsert({ user_id: userId, ...patch }, { onConflict: 'user_id' })
      .select('id, user_id, role, granted_by, created_at, updated_at')
      .single();
    if (error) throw new Error(`rbac: instance role upsert failed: ${error.message}`);
    const mapped: InstanceRoleAssignment = {
      id: data.id,
      userId: data.user_id,
      role: data.role,
      grantedBy: data.granted_by,
      createdAt: data.created_at,
      updatedAt: data.updated_at,
    };
    this.store(this.instanceCache, String(userId), mapped, this.cacheTtlMs);
    return mapped;
  }

  /** Remove an instance role (deprovisioning / demotion). */
  async deleteInstanceRole(userId: string): Promise<boolean> {
    const { data, error } = await this.client
      .from('rbac_instance_roles')
      .delete()
      .eq('user_id', userId)
      .select('id');
    if (error) throw new Error(`rbac: instance role delete failed: ${error.message}`);
    this.instanceCache.delete(String(userId));
    return (data || []).length > 0;
  }

  // ------------------------------------------------------------------
  // Per-app roles
  // ------------------------------------------------------------------

  /**
   * List all assignments for one app; used by the roles API and admin UI.
   */
  async listAppRoles(appId: string): Promise<AppRoleAssignment[]> {
    const hit = this.cached(this.appAssignmentCache, String(appId), this.cacheTtlMs);
    if (hit !== undefined) return hit;
    const { data, error } = await this.client
      .from('rbac_app_roles')
      .select('id, app_id, user_id, role, permissions, granted_by, created_at, updated_at')
      .eq('app_id', appId)
      .order('created_at', { ascending: true });
    if (error) throw new Error(`rbac: app role list failed: ${error.message}`);
    const value: AppRoleAssignment[] = (data || []).map((row: any) => ({
      id: row.id,
      appId: row.app_id,
      userId: row.user_id,
      role: row.role,
      permissions: row.permissions || {},
      grantedBy: row.granted_by,
      createdAt: row.created_at,
      updatedAt: row.updated_at,
    }));
    this.store(this.appAssignmentCache, String(appId), value, this.cacheTtlMs);
    return value;
  }

  /** Legacy wire shape for `/api/apps/:appId/roles` (field-name compatible). */
  static toWire(row: AppRoleAssignment, fallbackPermissions: ServerPermissionSet): AppRoleAssignmentWire {
    return {
      id: row.id,
      appId: row.appId,
      principal: row.userId,
      role: row.role,
      permissions: { ...fallbackPermissions, ...(row.permissions || {}) },
      createdAt: row.createdAt,
    };
  }

  /** Load one assignment for (app, user) pair. */
  async getAppAssignment(appId: string, userId: string): Promise<AppRoleAssignment | null> {
    const rows = await this.listAppRoles(appId);
    return rows.find((row) => row.userId === userId) ?? null;
  }

  /**
   * Persist an app assignment. `owner` roles are normalized to `admin`
   * (ownership belongs to `docker_apps.user_id` alone).
   */
  async setAppRole(
    appId: string,
    userId: string,
    role: AppRole,
    permissions: Partial<ServerPermissionSet> | null | undefined,
    grantedBy: string,
  ): Promise<AppRoleAssignment> {
    const storedRole = normalizeAppRole(role);
    if (!storedRole) throw new Error('rbac: app role must be admin|operator|viewer|custom|owner');
    const perms = storedRole === 'custom' ? permissions ?? {} : null;
    const patch = {
      role: storedRole,
      permissions: perms ?? {},
      granted_by: grantedBy ?? null,
      updated_at: new Date().toISOString(),
    };
    const { data, error } = await this.client
      .from('rbac_app_roles')
      .upsert({ app_id: appId, user_id: userId, ...patch }, { onConflict: 'app_id,user_id' })
      .select('id, app_id, user_id, role, permissions, granted_by, created_at, updated_at')
      .single();
    if (error) throw new Error(`rbac: app role upsert failed: ${error.message}`);
    this.appAssignmentCache.delete(String(appId));
    return {
      id: data.id,
      appId: data.app_id,
      userId: data.user_id,
      role: data.role,
      permissions: data.permissions || {},
      grantedBy: data.granted_by,
      createdAt: data.created_at,
      updatedAt: data.updated_at,
    };
  }

  /** Remove every assignment for a principal on one app. */
  async removeAppRolesForPrincipal(appId: string, userId: string): Promise<number> {
    const { data, error } = await this.client
      .from('rbac_app_roles')
      .delete()
      .eq('app_id', appId)
      .eq('user_id', userId)
      .select('id');
    if (error) throw new Error(`rbac: app role delete failed: ${error.message}`);
    this.appAssignmentCache.delete(String(appId));
    return (data || []).length;
  }

  // ------------------------------------------------------------------
  // Ownership / unassigned app deletion cleanup
  // ------------------------------------------------------------------

  /** Cached app owner lookup (`docker_apps.user_id`). */
  async getAppOwner(appId: string): Promise<string | null> {
    const hit = this.cached(this.ownerCache, String(appId), this.cacheTtlMs * OWNER_TTL_FACTOR);
    if (hit !== undefined) return hit;
    const { data, error } = await this.client
      .from('docker_apps')
      .select('user_id')
      .eq('id', appId)
      .maybeSingle();
    if (error) throw new Error(`rbac: app owner lookup failed: ${error.message}`);
    const owner = data?.user_id ?? null;
    this.store(this.ownerCache, String(appId), owner, this.cacheTtlMs * OWNER_TTL_FACTOR);
    return owner;
  }

  /**
   * Full app row for guarded routes. Routes no longer need their own
   * ownership probe — the guard attaches this record as `req.appRecord`
   * and handlers write with the authoritative `user_id`. Rows are cached
   * briefly but only the immutable coordinates are trusted by callers
   * (mutating routes still re-read mutable fields when they need them).
   */
  async getAppRow(appId: string): Promise<any | null> {
    const hit = this.cached(this.appRowCache, String(appId), this.cacheTtlMs * OWNER_TTL_FACTOR);
    if (hit !== undefined) return hit;
    const { data, error } = await this.client
      .from('docker_apps')
      .select('*')
      .eq('id', appId)
      .maybeSingle();
    if (error) throw new Error(`rbac: app row lookup failed: ${error.message}`);
    this.store(this.appRowCache, String(appId), data ?? null, this.cacheTtlMs * OWNER_TTL_FACTOR);
    return data ?? null;
  }

  /** Drop owner + assignment knowledge for one app (post-delete). */
  invalidateApp(appId: string): void {
    this.ownerCache.delete(String(appId));
    this.appAssignmentCache.delete(String(appId));
    this.appRowCache.delete(String(appId));
  }

  // ------------------------------------------------------------------
  // Decision engine
  // ------------------------------------------------------------------

  /**
   * The single authorization decision used by every guard.
   *
   * For app-scoped resources: ownership wins, then the app assignment
   * (`admin`/`operator`/`viewer` from the app shadow tables, `custom`
   * through the legacy boolean mapping). A `custom` assignment that does
   * not cover the action denies *and* short-circuits: it must never fall
   * back to instance roles — the granter's list is authoritative.
   * Non-admin instance roles never widen another user's app (no-assignment
   * case falls to the instance check, where only `admin` covers app actions).
   * For instance/personal resources: instance role shadow tables decide.
   */
  async can(
    userId: string,
    resourceType: ResourceType,
    action: ResourceAction,
    opts: { appId?: string } = {},
  ): Promise<RbacDecision> {
    if (!userId) return { allowed: false, reason: 'no_assignment' };
    const scope = resourceScopeForType(resourceType);

    if (scope === 'app' && opts.appId) {
      const owner = await this.getAppOwner(opts.appId);
      if (owner === null) return { allowed: false, reason: 'app_not_found' };
      if (owner === userId) return { allowed: true, reason: 'owner' };
      const assignment = await this.getAppAssignment(opts.appId, userId);
      if (assignment) {
        if (assignment.role === 'custom') {
          const covered = grantsCover(serverPermissionsToGrants(assignment.permissions), resourceType, action);
          return { allowed: covered, reason: 'app_role' };
        }
        const covered = grantsCover(roleGrants(assignment.role, true), resourceType, action);
        return { allowed: covered, reason: 'app_role' };
      }
      return this.canForInstanceRole(userId, resourceType, action, opts.appId);
    }

    // instance + personal scopes pass through the same role shadow tables.
    return this.canForInstanceRole(userId, resourceType, action);
  }

  /**
   * Instance role check including the personal self-ownership carve-out:
   * regardless of instance role membership, users still manage their own
   * rows in personal resources (secrets, API keys, SSH keys...). Row
   * filtering — `.eq('user_id', userId)` in the route — remains in place;
   * this decision is additive and never replaces row filters.
   */
  async canSelf(userId: string, resourceType: ResourceType, action: ResourceAction): Promise<RbacDecision> {
    if (!userId) return { allowed: false, reason: 'no_assignment' };
    const selfActions = PERSONAL_SELF_ACTIONS[resourceType] || [];
    if (selfActions.includes(action)) return { allowed: true, reason: 'self_row' };
    return this.canForInstanceRole(userId, resourceType, action);
  }

  private async canForInstanceRole(
    userId: string,
    resourceType: ResourceType,
    action: ResourceAction,
    appId?: string,
  ): Promise<RbacDecision> {
    const role = await this.getRoleOrNone(userId);
    if (!role) return { allowed: false, reason: appId ? 'no_assignment' : 'instance_role' };
    if (grantsCover(roleGrants(role, false), resourceType, action)) {
      return { allowed: true, reason: 'instance_role' };
    }
    return { allowed: false, reason: 'instance_role' };
  }

  /**
   * WebSocket gateway resolver contract (`server/ws/acl.ts`).
   *
   * Mapping from the gateway's four actions onto this module's model:
   * - `metrics:read` — any assigned user plus instance roles keep metrics
   *   visibility; the read decision covers owners.
   * - `logs:read` — read *or* exec on the app (old `console || files`
   *   semantics translate through `SERVER_PERMISSION_MAP`).
   * - `terminal:write` / `terminal:exec` — exec on the app; `console`
   *   members keep terminal access through the same mapping.
   *
   * @param action One of the gateway's `WsAction` names.
   */
  async resolveAppAccess(userId: string, appId: string, action: WsActionName): Promise<boolean> {
    if (action === 'terminal:write' || action === 'terminal:exec') {
      return (await this.can(userId, 'app', 'exec', { appId })).allowed;
    }
    if (action === 'logs:read') {
      const read = await this.can(userId, 'app', 'read', { appId });
      if (read.allowed) return true;
      return (await this.can(userId, 'app', 'exec', { appId })).allowed;
    }
    // metrics:read — owners and app roles flow through the metrics grant;
    // custom members with any operational boolean also map to metrics:read.
    return (await this.can(userId, 'metrics', 'read', { appId })).allowed;
  }

  // ------------------------------------------------------------------
  // Bootstrap
  // ------------------------------------------------------------------

  /**
   * Seed instance admin when the panel is initialized. The very first
   * authenticated admin user (created by `POST /api/setup/init` and
   * marked `role='admin'` in `user_profiles`) is promoted automatically;
   * explicit grants come afterwards via the roles API.
   *
   * Idempotent and safe to call repeatedly; the work happens once per
   * process because the in-flight promise is memoized.
   */
  async bootstrapInstanceRoles(): Promise<void> {
    if (this.bootstrapPromise) return this.bootstrapPromise;
    this.bootstrapPromise = (async () => {
      try {
        const { count, error } = await this.client
          .from('rbac_instance_roles')
          .select('id', { count: 'exact', head: true });
        if (error) return; // schema may not exist yet (pre-migration); retry on next boot
        if ((count ?? 0) > 0) return;
        const { data: admins, error: profilesError } = await this.client
          .from('user_profiles')
          .select('id')
          .eq('role', 'admin');
        if (profilesError || !admins) return;
        for (const admin of admins as { id: string }[]) {
          await this.setInstanceRole(admin.id, 'admin', admin.id);
        }
      } catch (err) {
        // Non-fatal: checks default to deny after a failed bootstrap and
        // the next process start retries with a cache-cold state.
        console.error('[rbac] bootstrap failed:', err instanceof Error ? err.message : err);
      }
    })();
    return this.bootstrapPromise;
  }
}
