/**
 * Shared contracts for the authenticated WebSocket gateway.
 *
 * The gateway sits in front of every panel WebSocket feature (log streaming,
 * metrics, collaborative terminal rooms). It authenticates each connection
 * with a short-lived HMAC-signed ticket and authorizes every per-app action
 * through a resolver supplied by the host application (deny by default).
 */

/** Per-app actions the gateway can authorize. */
export type WsAction = 'logs:read' | 'metrics:read' | 'terminal:write' | 'terminal:exec';

/** Host-supplied callback deciding whether a user may perform an action on an app. */
export type ResolveAppAccess = (
  userId: string,
  appId: string,
  action: WsAction,
) => boolean | Promise<boolean>;

/** Host-supplied callback mapping an app id to a Docker container id. */
export type ResolveContainerId = (appId: string) => string | null | Promise<string | null>;

/** Result of running a command inside a container. */
export interface ExecResult {
  ok: boolean;
  output: string;
  error?: string;
  exitCode?: number;
}

/** Host-supplied command executor used for terminal `exec` messages. */
export type ExecCommand = (containerId: string, command: string) => Promise<ExecResult>;

/** Monotonic-enough millisecond clock; injectable so tests can control time. */
export type Clock = () => number;

/**
 * Audit sink matching `logAudit` in `server/index.ts`.
 * Never pass ticket material through this callback; audit payloads are
 * persisted and the sanitiser only redacts known-sensitive keys.
 */
export type LogAudit = (
  userId: string,
  action: string,
  entityType: string,
  entityId?: string,
  oldValue?: unknown,
  newValue?: unknown,
  ipAddress?: string,
) => void | Promise<void>;

/**
 * WebSocket application close codes.
 *
 * Codes 4000-4991 are reserved for the application per RFC 6455.
 * The protocol always sends a UTF-8 reason (max 123 bytes).
 */
export const WS_CLOSE_CODES = {
  /** Ticket missing, malformed, or signature invalid. */
  AUTH_FAILED: 4001,
  /** No `auth` message (or `?ticket=`) within the configured window. */
  AUTH_TIMEOUT: 4002,
  /** Ticket expired, replayed, or revoked. */
  TICKET_INVALID: 4003,
  /** Repeated per-app authorization denials for this connection. */
  NOT_AUTHORIZED: 4004,
  /** Rate-limit strikes exhausted on this connection. */
  RATE_LIMITED: 4008,
  /** Repeated protocol violations (malformed or unknown messages). */
  POLICY_VIOLATION: 4009,
  /** Payload exceeded `WS_MAX_MESSAGE_BYTES`. */
  MESSAGE_TOO_BIG: 1009,
  /** No activity within `WS_IDLE_TIMEOUT_SECONDS`. */
  IDLE_TIMEOUT: 4013,
  /** Connection rejected or replaced at the per-user session limit. */
  SESSION_LIMIT: 4014,
} as const;

export type WsCloseCode = (typeof WS_CLOSE_CODES)[keyof typeof WS_CLOSE_CODES];

/** Reasons a ticket can be refused; surfaced to clients verbatim (no oracle). */
export type TicketDenyReason =
  | 'malformed'
  | 'bad_signature'
  | 'expired'
  | 'not_yet_valid'
  | 'replayed'
  | 'revoked';

/** Claims carried inside a WS ticket. Times are fractional epoch seconds. */
export interface TicketClaims {
  /** User id the ticket is bound to. */
  uid: string;
  /** Optional single-app scope; actions on other apps are refused. */
  aid?: string;
  /** Not valid before (fractional epoch seconds). */
  nbf: number;
  /** Expiry (fractional epoch seconds). */
  exp: number;
  /** Single-use nonce (replay protection). */
  n: string;
  /** Ticket id used for revocation. */
  jti: string;
}

export interface MintedTicket {
  ticket: string;
  claims: TicketClaims;
}

export type VerifyResult =
  | { ok: true; claims: TicketClaims }
  | { ok: false; reason: TicketDenyReason; claims?: TicketClaims };

/** Validated gateway configuration (see `config.ts`). */
export interface WsConfig {
  ticketTtlSeconds: number;
  ticketSkewSeconds: number;
  authTimeoutMs: number;
  idleTimeoutMs: number;
  heartbeatIntervalMs: number;
  maxSessionsPerUser: number;
  sessionLimitPolicy: 'kick-oldest' | 'reject';
  maxMessagesPerMinute: number;
  maxSubscribesPerMinute: number;
  maxRateStrikes: number;
  maxViolations: number;
  maxMessageBytes: number;
}

/** A registered, authenticated WebSocket session. */
export interface WsSession {
  id: string;
  userId: string;
  /** App scope from the ticket, or null for an unscoped ticket. */
  appScope: string | null;
  /** Ticket id (jti) the session authenticated with. */
  ticketJti: string;
  ip: string | null;
  createdAt: number;
  lastActivityAt: number;
  pingSentAt: number | null;
  awaitingPong: boolean;
  lastPongAt: number;
  rooms: Set<string>;
}

/** Structured error frame sent by the gateway. */
export interface WsErrorMessage {
  type: 'error';
  code: string;
  message: string;
  appId?: string;
  action?: WsAction;
  scope?: 'messages' | 'subscribe';
  retryAfterMs?: number;
}

/** Builds an error frame with a stable shape for clients. */
export function wsError(
  code: string,
  message: string,
  extra?: Omit<WsErrorMessage, 'type' | 'code' | 'message'>,
): WsErrorMessage {
  return { type: 'error', code, message, ...(extra || {}) };
}
