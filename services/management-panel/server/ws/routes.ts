/**
 * HTTP endpoints that mint and revoke WebSocket tickets.
 *
 * These routes are mounted under `/api/ws-token` in `server/index.ts` and are
 * protected by the same `verifyAuth` middleware as the rest of the API:
 *
 * - `POST /api/ws-token`        -> `{ ticket, expiresIn, appScope }`
 * - `POST /api/ws-token/revoke` -> revoke one ticket or every ticket for the user
 *
 * A ticket is only a bearer credential for the WebSocket handshake. Minting one
 * does not by itself grant access to an app: the gateway still runs the per-app
 * ACL on every action. Requesting an `appId` scope additionally requires the
 * caller to have access to that app, so scoped tickets cannot be requested for
 * apps the user cannot see.
 */
import { Router } from 'express';
import type { Request, RequestHandler, Response } from 'express';
import type { WsAuditLogger } from './audit.ts';
import type { TicketService } from './auth.ts';
import type { WsGateway } from './gateway.ts';
import { normalizeAppId } from './acl.ts';
import type { VerifyResult } from './types.ts';

export interface WsTokenRouterOptions {
  /** `verifyAuth` middleware from `server/index.ts`. */
  verifyAuth: RequestHandler;
  tickets: TicketService;
  audit: WsAuditLogger;
  gateway: WsGateway;
  /** Ticket lifetime in seconds (echoed to the client as `expiresIn`). */
  ttlSeconds: number;
  /**
   * Returns true when the user may scope a ticket to the app.
   * Wired to app ownership / role assignment in `server/index.ts`.
   */
  validateAppAccess: (userId: string, appId: string) => boolean | Promise<boolean>;
}

function ipOf(req: Request): string | null {
  const forwarded = req.headers['x-forwarded-for'];
  if (typeof forwarded === 'string' && forwarded.length > 0) {
    return forwarded.split(',')[0].trim();
  }
  return req.socket?.remoteAddress ?? null;
}

function userIdOf(req: Request): string {
  return (req as unknown as { user: { id: string } }).user.id;
}

/**
 * Create the `/api/ws-token` router.
 * @param options - Auth middleware, services, and the access validator
 */
export function createWsTokenRouter(options: WsTokenRouterOptions): Router {
  const router = Router();
  const { verifyAuth, tickets, audit, gateway, ttlSeconds, validateAppAccess } = options;

  router.post('/', verifyAuth, async (req: Request, res: Response) => {
    const userId = userIdOf(req);
    const ip = ipOf(req);
    const rawAppId = (req.body as Record<string, unknown> | undefined)?.appId;

    let appScope: string | null = null;
    if (rawAppId !== undefined && rawAppId !== null && rawAppId !== '') {
      const appId = normalizeAppId(rawAppId);
      if (!appId) {
        res.status(400).json({ error: 'Invalid appId' });
        return;
      }
      let allowed = false;
      try {
        allowed = Boolean(await validateAppAccess(userId, appId));
      } catch {
        allowed = false;
      }
      if (!allowed) {
        audit.ticketRejected('app_not_allowed', ip, userId);
        res.status(403).json({ error: 'You do not have access to this app' });
        return;
      }
      appScope = appId;
    }

    const minted = tickets.mint(userId, appScope ? { appId: appScope } : undefined);
    audit.ticketIssued(userId, appScope, minted.claims.jti, ip);
    res.json({ ticket: minted.ticket, expiresIn: ttlSeconds, appScope });
  });

  router.post('/revoke', verifyAuth, async (req: Request, res: Response) => {
    const userId = userIdOf(req);
    const ip = ipOf(req);
    const body = (req.body ?? {}) as Record<string, unknown>;

    if (body.all === true) {
      tickets.revokeAllForUser(userId);
      const closed = gateway.closeUserSessions(userId, 'user_revoked');
      audit.ticketRevoked(userId, 'all', ip);
      res.json({ revoked: true, scope: 'all', sessionsClosed: closed });
      return;
    }

    const candidate = body.ticket;
    if (typeof candidate !== 'string' || candidate.length === 0) {
      res.status(400).json({ error: 'Provide a ticket or set all: true' });
      return;
    }
    const inspected: VerifyResult = tickets.inspect(candidate);
    if (!inspected.ok) {
      audit.ticketRejected(inspected.reason, ip, inspected.claims?.uid ?? userId);
      res.status(400).json({ error: 'Ticket is not valid', reason: inspected.reason });
      return;
    }
    if (inspected.claims.uid !== userId) {
      audit.ticketRejected('not_owner', ip, userId);
      res.status(403).json({ error: 'Ticket does not belong to this user' });
      return;
    }
    tickets.revoke(inspected.claims.jti, inspected.claims.exp * 1000);
    const closed = gateway.closeTicketSessions(userId, inspected.claims.jti, 'ticket_revoked');
    audit.ticketRevoked(userId, 'ticket', ip);
    res.json({ revoked: true, scope: 'ticket', sessionsClosed: closed });
  });

  return router;
}
