/**
 * Scoped API keys (key model v2) + 2FA re-auth for sensitive flows.
 *
 * Key model changes introduced here:
 * - Key prefixes: `ip_live_...` (production keys) and `ip_test_...`
 *   (clearly-marked test keys). Legacy `ip_<hex>` keys keep working and
 *   are surfaced with a forced-rotation prompt (`needs_rotation`).
 * - Every key carries a `scopes` string array. Scope syntax is
 *   `<family>:<action|*>` (e.g. `apps:read`), `<family>:*` (e.g.
 *   `metrics:*`), or the wildcard `*`. Legacy keys hold `['*']`.
 * - Optional expiry (already existed) plus an optional app binding: a
 *   key bound to an app may only be used on routes for that app.
 * - Rotation keeps a managed overlap: issuing a replacement marks the
 *   old key as rotated (it keeps working until its overlap deadline) so
 *   operators can swap credentials without an outage.
 *
 * Scope enforcement hooks into the RBAC guard layer: every guarded route
 * documents its `(resourceType, action)` coordinates, so the injection
 * point aggregates both checks into one middleware chain. Routes without
 * RBAC coordinates are wildcard-only for scoped keys (see
 * `requireWildcardScope` below) — the safe default for narrowly scoped
 * keys.
 */

import type { Request, Response, NextFunction } from 'express';
import { grantsCover } from '../rbac/catalog.ts';

/** Scope families accepted from clients (map onto the RBAC vocabulary). */
export const SCOPE_FAMILIES: Record<string, string> = {
  apps: 'app',
  backups: 'backup',
  deployments: 'deployment',
  configs: 'config',
  metrics: 'metrics',
  inventory: 'inventory',
  databases: 'databases',
  webhooks: 'webhooks',
  plugins: 'plugins',
  templates: 'templates',
  ssh: 'ssh',
  maintenance: 'maintenance',
  secrets: 'secrets',
  members: 'members',
  billing: 'billing',
  runbooks: 'runbooks',
  audit: 'audit',
  settings: 'settings',
  notifications: 'notifications',
  apikeys: 'apikeys',
  organization: 'organization',
  customers: 'customers',
  reports: 'reports',
};

export const SCOPE_ACTIONS = new Set([
  'read', 'write', 'exec', 'delete', 'export', 'validate',
]);

const WILDCARD = '*';

/** True when the token matches scope syntax. */
export function isValidScopeToken(token: string): boolean {
  if (token === WILDCARD) return true;
  const sep = token.indexOf(':');
  if (sep <= 0) return false;
  const family = token.slice(0, sep);
  if (family === WILDCARD) return false; // '*:read' is meaningless; use '*'
  if (!(family in SCOPE_FAMILIES)) return false;
  const action = token.slice(sep + 1);
  return action === WILDCARD || SCOPE_ACTIONS.has(action);
}

/** Validate a scope list from user input; returns the clean list or null. */
export function normalizeScopes(input: unknown): string[] | null {
  if (!Array.isArray(input)) return null;
  const out: string[] = [];
  for (const raw of input) {
    if (typeof raw !== 'string') return null;
    const token = raw.trim();
    if (!isValidScopeToken(token)) return null;
    if (token === WILDCARD) return [WILDCARD];
    if (!out.includes(token)) out.push(token);
  }
  return out.length > 0 ? out : null;
}

/** Internal resource type → preferred scope family (for 403 hints). */
export const FAMILY_FOR_RESOURCE: Record<string, string> = Object.fromEntries(
  Object.entries(SCOPE_FAMILIES).map(([family, resource]) => [resource, family]),
);

/**
 * Check a key's scope list against a needed permission. Accepts both the
 * scope families (`apps`) and the internal RBAC vocabulary (`app`).
 */
export function scopesCover(
  scopes: readonly string[],
  resourceType: string,
  action: string,
): boolean {
  if (!Array.isArray(scopes) || scopes.length === 0) return false;
  if (scopes.length === 1 && scopes[0] === WILDCARD) return true;
  const family = FAMILY_FOR_RESOURCE[resourceType] || resourceType;
  for (const candidate of new Set([family, resourceType])) {
    if (grantsCover(scopes.slice(), candidate as any, action as any)) {
      return true;
    }
  }
  return false;
}

/** The scope spelling the caller would need (used in 403 hints). */
export function describeRequiredScope(resourceType: string, action: string): string {
  return `${FAMILY_FOR_RESOURCE[resourceType] || resourceType}:${action}`;
}

/* ============================================================
 * API-key request context (attached by verifyAuth)
 * ============================================================ */

export interface ApiKeyContext {
  id: string;
  userId: string;
  scopes: string[] | null; // null = legacy key, treated as ['*']
  keyClass: 'live' | 'test' | null;
  appId: string | null;
  forceRotate: boolean;
}

export function apiKeyContext(req: Request): ApiKeyContext | null {
  return (req as any).apiKey || null;
}

/**
 * Return the missing-scope hint for a request, or null when allowed:
 * JWT/SSO users are never scope-limited; API keys are checked here.
 */
export function scopeDenialFor(
  req: Request,
  resourceType: string,
  action: string,
): string | null {
  const apiKey = apiKeyContext(req);
  if (!apiKey) return null;
  const scopes = apiKey.scopes ?? [WILDCARD];
  return scopesCover(scopes, resourceType, action)
    ? null
    : describeRequiredScope(resourceType, action);
}

/** Audit signature: mirrors `logAudit` (never carries payloads). */
export type ScopeAuditFn = (
  userId: string,
  action: string,
  entityType: string,
  entityId?: string,
  oldValue?: any,
  newValue?: any,
  ipAddress?: string,
) => void | Promise<void>;

let scopeAudit: ScopeAuditFn | null = null;

/** Wire the panel's auditor once, at boot (`configureScopeGuards`). */
export function configureScopeGuards(audit: ScopeAuditFn): void {
  scopeAudit = audit;
}

function requestIp(req: Request): string | undefined {
  return req.socket?.remoteAddress || undefined;
}

function auditScopeDenial(
  userId: string | null,
  req: Request,
  code: string,
  required: string,
): void {
  if (!userId || !scopeAudit) return;
  void Promise.resolve(
    scopeAudit(
      userId,
      'scope:denied',
      'apikeys',
      undefined,
      null,
      { code, required, route: req.path, method: req.method },
      requestIp(req),
    ),
  );
}

function denyScope(res: Response, body: Record<string, unknown>): void {
  res.status(403).json(body);
}

/** `requireScope` middleware for routes annotated explicitly. */
export function requireScope(resourceType: string, action: string) {
  return (req: Request, res: Response, next: NextFunction) => {
    const denial = scopeDenialFor(req, resourceType, action);
    if (!denial) return next();
    auditScopeDenial((req as any).user?.id ?? null, req, 'required_scope', denial);
    return denyScope(res, {
      error: `This API key is missing the '${denial}' scope`,
      code: 'scope_denied',
      required: denial,
      hint: 'Create a new key with the needed scope, or use a wildcard key for unclassified endpoints.',
    });
  };
}

/**
 * Scoped keys may only touch classified endpoints; everything else
 * (dashboards, themes, doctor, ...) needs the wildcard scope `*`.
 */
export function requireWildcardScope() {
  return (req: Request, res: Response, next: NextFunction) => {
    const apiKey = apiKeyContext(req);
    if (!apiKey) return next(); // JWT/SSO callers are unaffected
    const scopes = apiKey.scopes ?? [WILDCARD];
    if (scopes.includes(WILDCARD)) return next();
    auditScopeDenial(apiKey.userId, req, 'wildcard_scope', WILDCARD);
    return denyScope(res, {
      error: 'This endpoint requires an API key with the wildcard (*) scope',
      code: 'scope_denied',
      required: WILDCARD,
      hint: 'Wildcard keys are full credentials; issue scoped keys for automation.',
    });
  };
}

/** App binding: a bound key may only act on its bound app. */
export function keyAllowsApp(req: Request, appId: string | null): boolean {
  const apiKey = apiKeyContext(req);
  if (!apiKey || !apiKey.appId) return true;
  return Boolean(appId) && apiKey.appId === appId;
}

/* ============================================================
 * 2FA re-authentication (header X-2FA-Token)
 * ============================================================ */

export interface TwoFactorProbe {
  verifyReauth(userId: string, code: string): Promise<boolean>;
}

/** Wiring type over the panel's existing `fetch`-based forwarding. */
export type TwoFactorSender = (
  path: string,
  init: { method: string; body?: string },
) => Promise<{ ok: boolean; data?: any }>;

const REAUTH_WINDOW_MS = 5 * 60 * 1000;
const reauthGranted = new Map<string, number>();

/**
 * Validate a fresh TOTP/backup code through the integration service.
 * Contract (documented in wiki/14 and the panel README):
 *
 *   POST {base}/api/auth/2fa/verify-reauth  { user_id, code }
 *   -> 200 { valid: boolean }
 *
 * Any transport failure fails closed (no grant cached).
 */
export function createTwoFactorVerifier(send: TwoFactorSender): TwoFactorProbe {
  return {
    async verifyReauth(userId: string, code: string): Promise<boolean> {
      const cachedUntil = reauthGranted.get(userId) || 0;
      if (Date.now() < cachedUntil) return true;
      const normalized = String(code || '').trim();
      if (!userId || normalized.length < 6 || normalized.length > 12) return false;
      let valid = false;
      try {
        const response = await send('/api/auth/2fa/verify-reauth', {
          method: 'POST',
          body: JSON.stringify({ user_id: userId, code: normalized }),
        });
        valid = response.ok && (response.data as any)?.valid === true;
      } catch {
        return false;
      }
      if (valid) {
        reauthGranted.set(userId, Date.now() + REAUTH_WINDOW_MS);
      }
      return valid;
    },
  };
}

/** The TOTP-enabled probe: contract
 * `GET /api/auth/2fa/status/{userId}` -> { enabled: boolean }. */
export function createTwoFactorStatusChecker(send: TwoFactorSender): {
  enabledFor(userId: string): Promise<boolean>;
} {
  return {
    async enabledFor(userId: string): Promise<boolean> {
      const response = await send(`/api/auth/2fa/status/${userId}`, { method: 'GET' });
      if (!response.ok) throw new Error('2fa status probe failed');
      return (response.data as any)?.enabled === true;
    },
  };
}

/** Forget a user's cached re-auth grant (logout / key rotation). */
export function clearReauthGrant(userId: string): void {
  reauthGranted.delete(userId);
}

/**
 * Require a fresh X-2FA-Token for sensitive operations when the caller
 * has TOTP enabled. Disabled users pass without the header; transport
 * failures fail closed with 503.
 */
export function require2FAReauth(
  probe: TwoFactorProbe,
  statusChecker: { enabledFor(userId: string): Promise<boolean> },
) {
  return (req: Request, res: Response, next: NextFunction) => {
    const userId = (req as any).user?.id ?? null;
    if (!userId) {
      return res.status(401).json({ error: 'Unauthorized' });
    }
    void (async () => {
      let enabled = false;
      try {
        enabled = await statusChecker.enabledFor(userId);
      } catch (err) {
        console.error('[2fa] reauth status check failed:', err instanceof Error ? err.message : err);
        return res.status(503).json({ error: 'Two-factor status unavailable; refusing sensitive operation' });
      }
      if (!enabled) return next();
      const granted = await probe.verifyReauth(userId, String(req.headers['x-2fa-token'] || ''));
      if (granted) return next();
      auditScopeDenial(userId, req, 'reauth_required', 'X-2FA-Token');
      return res.status(403).json({
        error: 'A fresh two-factor code is required (X-2FA-Token header)',
        code: 'reauth_required',
      });
    })();
  };
}
