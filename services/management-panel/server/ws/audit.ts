/**
 * Structured audit events for the WebSocket gateway.
 *
 * Events follow the `logAudit(userId, action, entityType, entityId, oldValue,
 * newValue, ipAddress)` convention used throughout `server/index.ts`. Ticket
 * material (the ticket string, nonce, signature) is never passed to the sink;
 * only identifiers (`jti`) and reasons are recorded. Failures without a known
 * user cannot be written to the per-user audit trail, so they are emitted as a
 * structured console line keyed by reason and IP.
 */
import type { Clock, LogAudit, WsSession } from './types.ts';

/** Audit action names emitted by the gateway (entity type `ws_session`/`ws_ticket`). */
export const WS_AUDIT_ACTIONS = {
  TICKET_ISSUED: 'ws:ticket:issue',
  TICKET_REJECTED: 'ws:ticket:reject',
  TICKET_REVOKED: 'ws:ticket:revoke',
  CONNECTED: 'ws:connect',
  DISCONNECTED: 'ws:disconnect',
  AUTH_FAILED: 'ws:auth:failed',
  SUBSCRIBE_ALLOWED: 'ws:subscribe',
  SUBSCRIBE_DENIED: 'ws:subscribe:denied',
  TERMINAL_ALLOWED: 'ws:terminal',
  TERMINAL_DENIED: 'ws:terminal:denied',
  RATE_LIMITED: 'ws:rate-limit',
} as const;

const ENTITY_SESSION = 'ws_session';
const ENTITY_TICKET = 'ws_ticket';

export interface WsAuditOptions {
  log: LogAudit;
  clock?: Clock;
  /** Sink for events that have no authenticated user (pre-auth failures). */
  unattributed?: (entry: Record<string, unknown>) => void;
}

export class WsAuditLogger {
  private readonly log: LogAudit;
  private readonly clock: Clock;
  private readonly unattributed: (entry: Record<string, unknown>) => void;

  constructor(options: WsAuditOptions) {
    this.log = options.log;
    this.clock = options.clock ?? Date.now;
    this.unattributed =
      options.unattributed ??
      ((entry) => {
        console.warn('[ws-auth]', JSON.stringify(entry));
      });
  }

  private emit(
    userId: string,
    action: string,
    entityType: string,
    entityId: string | null,
    details: Record<string, unknown> | null,
    ip: string | null,
  ): void {
    try {
      void Promise.resolve(
        this.log(
          userId,
          action,
          entityType,
          entityId ?? undefined,
          undefined,
          details ?? undefined,
          ip ?? undefined,
        ),
      ).catch((err: unknown) => {
        console.error('WS audit log error:', err);
      });
    } catch (err) {
      console.error('WS audit log error:', err);
    }
  }

  /** A ticket was minted for a user (identifiers only, never the ticket). */
  ticketIssued(userId: string, appId: string | null, jti: string, ip: string | null): void {
    this.emit(
      userId,
      WS_AUDIT_ACTIONS.TICKET_ISSUED,
      ENTITY_TICKET,
      jti,
      { appId, expiresAt: new Date(this.clock()).toISOString() },
      ip,
    );
  }

  /**
   * A ticket was refused at issue or handshake time.
   * When the user is unknown the event goes to the unattributed sink so no
   * per-user row is written for anonymous traffic.
   */
  ticketRejected(reason: string, ip: string | null, userId?: string): void {
    if (userId) {
      this.emit(userId, WS_AUDIT_ACTIONS.TICKET_REJECTED, ENTITY_TICKET, null, { reason }, ip);
      return;
    }
    this.unattributed({ event: WS_AUDIT_ACTIONS.TICKET_REJECTED, reason, ip });
  }

  /** Tickets were revoked by their owner (single ticket or all for the user). */
  ticketRevoked(userId: string, scope: 'ticket' | 'all', ip: string | null): void {
    this.emit(userId, WS_AUDIT_ACTIONS.TICKET_REVOKED, ENTITY_TICKET, null, { scope }, ip);
  }

  /** An authenticated session completed the handshake. */
  connected(session: WsSession): void {
    this.emit(
      session.userId,
      WS_AUDIT_ACTIONS.CONNECTED,
      ENTITY_SESSION,
      session.id,
      { appScope: session.appScope, ip: session.ip },
      session.ip,
    );
  }

  /** An authenticated session ended (any reason: closed, idle, revoked...). */
  disconnected(session: WsSession, reason: string): void {
    this.emit(
      session.userId,
      WS_AUDIT_ACTIONS.DISCONNECTED,
      ENTITY_SESSION,
      session.id,
      { reason, durationMs: Math.max(0, this.clock() - session.createdAt) },
      session.ip,
    );
  }

  /** Handshake authentication failed for a known or unknown user. */
  authFailed(reason: string, ip: string | null, userId?: string): void {
    if (userId) {
      this.emit(userId, WS_AUDIT_ACTIONS.AUTH_FAILED, ENTITY_SESSION, null, { reason }, ip);
      return;
    }
    this.unattributed({ event: WS_AUDIT_ACTIONS.AUTH_FAILED, reason, ip });
  }

  /** A log or metrics subscription passed the ACL. */
  subscribeAllowed(session: WsSession, appId: string, channel: 'logs' | 'metrics'): void {
    this.emit(
      session.userId,
      WS_AUDIT_ACTIONS.SUBSCRIBE_ALLOWED,
      ENTITY_SESSION,
      session.id,
      { appId, channel },
      session.ip,
    );
  }

  /** A log or metrics subscription was refused by the ACL. */
  subscribeDenied(session: WsSession, appId: string, action: string, reason: string): void {
    this.emit(
      session.userId,
      WS_AUDIT_ACTIONS.SUBSCRIBE_DENIED,
      ENTITY_SESSION,
      session.id,
      { appId, action, reason },
      session.ip,
    );
  }

  /** A terminal action passed the ACL. */
  terminalAllowed(session: WsSession, appId: string, action: string): void {
    this.emit(
      session.userId,
      WS_AUDIT_ACTIONS.TERMINAL_ALLOWED,
      ENTITY_SESSION,
      session.id,
      { appId, action },
      session.ip,
    );
  }

  /** A terminal action (input or exec) was refused by the ACL. */
  terminalDenied(session: WsSession, appId: string, action: string, reason: string): void {
    this.emit(
      session.userId,
      WS_AUDIT_ACTIONS.TERMINAL_DENIED,
      ENTITY_SESSION,
      session.id,
      { appId, action, reason },
      session.ip,
    );
  }

  /** The connection or user exceeded a rate limit. */
  rateLimited(
    userId: string,
    sessionId: string | null,
    scope: 'messages' | 'subscribe',
    retryAfterMs: number,
    ip: string | null,
  ): void {
    this.emit(
      userId,
      WS_AUDIT_ACTIONS.RATE_LIMITED,
      ENTITY_SESSION,
      sessionId,
      { scope, retryAfterMs },
      ip,
    );
  }
}
