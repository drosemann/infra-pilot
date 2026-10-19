/**
 * HTTP authorization middleware for the panel RBAC layer.
 *
 * Two compositional guards:
 * - `requirePermission(resourceType, action)` — instance-level decision.
 *   Personal rows additionally accept self ownership (`{ self: true }`),
 *   which is the only way regular users keep working; instance resources
 *   (settings, audit export...) are always role-gated.
 * - `requireAppRole(action, resourceType?)` — app-scoped decision:
 *   ownership, per-app assignment, or instance `admin` all pass; other
 *   instance roles never widen somebody else's app.
 *
 * Denials return 403 with a stable body (`code: 'rbac_denied'`) and are
 * audited (`rbac:denied`) with the resource coordinates but never any
 * request payload. Store failures escalate to 503 fail-closed: a middleware
 * that cannot decide must not accidentally allow.
 */
import type { Request, Response, NextFunction } from 'express';
import type { RbacStore } from './store.ts';
import type { ResourceAction, ResourceType } from './types.ts';

/** Audit signature mirrors `logAudit` in `server/index.ts`. */
export type RbacAuditFn = (
  userId: string,
  action: string,
  entityType: string,
  entityId?: string,
  oldValue?: any,
  newValue?: any,
  ipAddress?: string,
) => void | Promise<void>;

export interface RbacGuardOptions {
  store: RbacStore;
  audit: RbacAuditFn;
}

export type RbacGuard = ReturnType<typeof createRbacGuards>;

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

/**
 * Extract the acting user id written by `verifyAuth`. Both records carry
 * `id` (Supabase JWT users and trimmed API-key rows).
 */
export function actorId(req: Request): string | null {
  const id = (req as any).user?.id;
  return typeof id === 'string' && id.length > 0 ? id : null;
}

/** Client IP as recorded by earlier middleware, for the denial audit trail. */
function requestIp(req: Request): string | undefined {
  const header = req.socket?.remoteAddress;
  return header || undefined;
}

export function createRbacGuards(options: RbacGuardOptions) {
  const { store, audit } = options;

  /**
   * Shared denial writer: 403 body + `rbac:denied` audit event.
   * Audited coordinates are the resource type/id and route only — request
   * payloads may contain secrets and are never attached.
   */
  function deny(
    req: Request,
    res: Response,
    userId: string | null,
    resourceType: ResourceType,
    action: ResourceAction,
    reason: string,
    entityId?: string,
  ): void {
    if (userId) {
      void audit(
        userId,
        'rbac:denied',
        resourceType,
        entityId,
        null,
        { action, reason, route: req.path, method: req.method },
        requestIp(req),
      );
    }
    res.status(403).json({
      error: 'Forbidden',
      code: 'rbac_denied',
      resourceType,
      action,
      reason,
    });
  }

  /** Fail-closed handling for store errors (500-class, logged server side). */
  function failClosed(res: Response, err: unknown): void {
    console.error('[rbac] authorization check failed:', err instanceof Error ? err.message : err);
    res.status(503).json({ error: 'Authorization backend unavailable', code: 'rbac_unavailable' });
  }

  /**
   * Guard for instance/personal resources. Use `{ self: true }` on
   * personal rows (secrets, API keys...) so unprivileged users keep
   * managing their own data; any instance-scoped call is admin/role-gated.
   */
  const requirePermission = (
    resourceType: ResourceType,
    action: ResourceAction,
    opts: { self?: boolean } = {},
  ) => {
    return async (req: Request, res: Response, next: NextFunction) => {
      const userId = actorId(req);
      if (!userId) {
        // verifyAuth upstream should have rejected unauthenticated callers;
        // belt-and-braces 401 here keeps the guard standalone-usable.
        if (!res.headersSent) return res.status(401).json({ error: 'Unauthorized' });
        return;
      }
      try {
        const decision = opts.self
          ? await store.canSelf(userId, resourceType, action)
          : await store.can(userId, resourceType, action);
        if (decision.allowed) return next();
        return deny(req, res, userId, resourceType, action, decision.reason);
      } catch (err) {
        return failClosed(res, err);
      }
    };
  };

  /**
   * Guard for app-scoped routes. Requires the standard `:appId` param
   * (or `?appId=` query) and attaches `{ appAccess }` plus the app row as
   * `appRecord` to the request so handlers do not need a second ownership
   * probe. A non-existent app yields 404 (not 403) to avoid confirming
   * which ids are valid.
   *
   * `{ optional: true }` lets routes that ALSO serve the unscoped,
   * user-aggregate view pass without an app id; as soon as one is present
   * the normal decision applies.
   */
  const requireAppRole = (
    action: ResourceAction,
    resourceType: ResourceType = 'app',
    opts: { optional?: boolean } = {},
  ) => {
    return async (req: Request, res: Response, next: NextFunction) => {
      const userId = actorId(req);
      if (!userId) {
        if (!res.headersSent) return res.status(401).json({ error: 'Unauthorized' });
        return;
      }
      const appId = String(req.params?.appId ?? req.query?.appId ?? '');
      if (!appId) {
        if (opts.optional) return next();
        return res.status(400).json({ error: 'A valid appId is required' });
      }
      if (!UUID_RE.test(appId)) {
        return res.status(400).json({ error: 'A valid appId is required' });
      }
      try {
        const decision = await store.can(userId, resourceType, action, { appId });
        if (decision.reason === 'app_not_found') {
          return res.status(404).json({ error: 'App not found' });
        }
        if (decision.allowed) {
          (req as any).appAccess = { appId, reason: decision.reason };
          const row = await store.getAppRow(appId);
          if (!row) return res.status(404).json({ error: 'App not found' });
          (req as any).appRecord = row;
          return next();
        }
        return deny(req, res, userId, resourceType, action, decision.reason, appId);
      } catch (err) {
        return failClosed(res, err);
      }
    };
  };

  return { requirePermission, requireAppRole, denyActorId: actorId };
}
