/**
 * Per-app authorization for WebSocket actions.
 *
 * Deny by default: every decision flows through the host-supplied
 * `resolveAppAccess` resolver (wired to the panel's `serverRoles` map plus
 * app ownership in `server/index.ts`). Ticket app scope, when present, only
 * narrows access further — the resolver can allow an action that the ticket
 * scope still refuses.
 */
import type { WsAuditLogger } from './audit.ts';
import type { ResolveAppAccess, WsAction, WsSession } from './types.ts';

export interface AclServiceOptions {
  /** Resolver injected by the host; when absent, every action is denied. */
  resolveAppAccess?: ResolveAppAccess;
  audit: WsAuditLogger;
}

export interface AuthorizeContext {
  session: WsSession;
  appId: string;
  action: WsAction;
}

export interface AclDecision {
  allowed: boolean;
  /** Stable machine reason (`forbidden`, `scope_mismatch`, ...). */
  reason: string;
}

const APP_ID_MAX_LENGTH = 128;

/**
 * Validate an app id coming off the wire.
 * @returns The trimmed id, or null when missing/oversized/containing controls
 */
export function normalizeAppId(value: unknown): string | null {
  if (typeof value !== 'string') return null;
  const trimmed = value.trim();
  if (trimmed.length === 0 || trimmed.length > APP_ID_MAX_LENGTH) return null;
  // Reject control characters without relying on a raw control-char regex.
  for (let i = 0; i < trimmed.length; i += 1) {
    if (trimmed.charCodeAt(i) < 0x20 || trimmed.charCodeAt(i) === 0x7f) return null;
  }
  return trimmed;
}

/**
 * Evaluates one authorization decision and writes the matching audit event.
 * Violation escalation (disconnect after repeated denials) is owned by the
 * gateway, which counts denials per connection.
 */
export class AclService {
  private readonly resolve: ResolveAppAccess | undefined;
  private readonly audit: WsAuditLogger;

  constructor(options: AclServiceOptions) {
    this.resolve = options.resolveAppAccess;
    this.audit = options.audit;
  }

  /**
   * Authorize a single action for a session.
   * @returns `{ allowed: false, reason }` with a deny audit event on refusal
   */
  async authorize(context: AuthorizeContext): Promise<AclDecision> {
    const { session, action } = context;
    const appId = normalizeAppId(context.appId);
    if (!appId) {
      this.deny(session, context.appId, action, 'invalid_app_id');
      return { allowed: false, reason: 'invalid_app_id' };
    }
    if (session.appScope !== null && session.appScope !== appId) {
      this.deny(session, appId, action, 'scope_mismatch');
      return { allowed: false, reason: 'scope_mismatch' };
    }
    if (!this.resolve) {
      this.deny(session, appId, action, 'no_resolver');
      return { allowed: false, reason: 'no_resolver' };
    }
    let granted = false;
    try {
      granted = Boolean(await this.resolve(session.userId, appId, action));
    } catch {
      this.deny(session, appId, action, 'resolver_error');
      return { allowed: false, reason: 'resolver_error' };
    }
    if (!granted) {
      this.deny(session, appId, action, 'forbidden');
      return { allowed: false, reason: 'forbidden' };
    }
    this.allow(session, appId, action);
    return { allowed: true, reason: 'granted' };
  }

  private allow(session: WsSession, appId: string, action: WsAction): void {
    if (action === 'logs:read' || action === 'metrics:read') {
      this.audit.subscribeAllowed(session, appId, action === 'logs:read' ? 'logs' : 'metrics');
      return;
    }
    this.audit.terminalAllowed(session, appId, action);
  }

  private deny(session: WsSession, appId: string, action: WsAction, reason: string): void {
    if (action === 'logs:read' || action === 'metrics:read') {
      this.audit.subscribeDenied(session, appId, action, reason);
      return;
    }
    this.audit.terminalDenied(session, appId, action, reason);
  }
}
