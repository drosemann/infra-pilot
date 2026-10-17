/**
 * Environment-driven configuration for the authenticated WebSocket gateway.
 *
 * Every knob has a safe default so the gateway works without new env vars.
 * Values are validated eagerly at startup: non-numeric input fails fast,
 * out-of-range input is clamped into the supported range (the ticket TTL is
 * additionally hard-capped at five minutes).
 */
import crypto from 'crypto';
import type { WsConfig } from './types.ts';

interface IntBounds {
  def: number;
  min: number;
  max: number;
}

const INT_BOUNDS: Record<string, IntBounds> = {
  WS_TICKET_TTL_SECONDS: { def: 300, min: 30, max: 300 },
  WS_TICKET_SKEW_SECONDS: { def: 30, min: 0, max: 60 },
  WS_AUTH_TIMEOUT_MS: { def: 5000, min: 500, max: 60000 },
  WS_IDLE_TIMEOUT_SECONDS: { def: 1800, min: 30, max: 86400 },
  WS_HEARTBEAT_INTERVAL_SECONDS: { def: 30, min: 5, max: 300 },
  WS_MAX_SESSIONS_PER_USER: { def: 10, min: 1, max: 100 },
  WS_MAX_MESSAGES_PER_MINUTE: { def: 120, min: 10, max: 6000 },
  WS_MAX_SUBSCRIBES_PER_MINUTE: { def: 30, min: 1, max: 600 },
  WS_MAX_RATE_STRIKES: { def: 20, min: 1, max: 1000 },
  WS_MAX_VIOLATIONS: { def: 5, min: 1, max: 100 },
  WS_MAX_MESSAGE_BYTES: { def: 65536, min: 1024, max: 1048576 },
};

const SESSION_POLICIES = ['kick-oldest', 'reject'] as const;

type Env = Record<string, string | undefined>;

function readBoundedInt(env: Env, name: string): number {
  const bounds = INT_BOUNDS[name];
  const raw = env[name];
  if (raw === undefined || raw.trim() === '') return bounds.def;
  if (!/^[+-]?\d+$/.test(raw.trim())) {
    throw new Error(`${name} must be an integer (got ${JSON.stringify(raw)})`);
  }
  const value = Number.parseInt(raw.trim(), 10);
  if (value < bounds.min) return bounds.min;
  if (value > bounds.max) return bounds.max;
  return value;
}

function readPolicy(env: Env): 'kick-oldest' | 'reject' {
  const raw = env.WS_SESSION_LIMIT_POLICY;
  if (raw === undefined || raw.trim() === '') return 'kick-oldest';
  const value = raw.trim();
  if (!(SESSION_POLICIES as readonly string[]).includes(value)) {
    throw new Error(
      `WS_SESSION_LIMIT_POLICY must be one of ${SESSION_POLICIES.join(', ')} (got ${JSON.stringify(raw)})`,
    );
  }
  return value as 'kick-oldest' | 'reject';
}

/**
 * Validated defaults, used directly by tests and as the base for env parsing.
 * Millisecond-based fields mirror the second-based env vars.
 */
export const DEFAULT_WS_CONFIG: WsConfig = {
  ticketTtlSeconds: 300,
  ticketSkewSeconds: 30,
  authTimeoutMs: 5000,
  idleTimeoutMs: 1800 * 1000,
  heartbeatIntervalMs: 30 * 1000,
  maxSessionsPerUser: 10,
  sessionLimitPolicy: 'kick-oldest',
  maxMessagesPerMinute: 120,
  maxSubscribesPerMinute: 30,
  maxRateStrikes: 20,
  maxViolations: 5,
  maxMessageBytes: 65536,
};

/**
 * Read and validate the gateway configuration from the environment.
 * @param env - Environment map (defaults to `process.env`)
 * @throws Error when a value is present but not an integer / not a known policy
 */
export function loadWsConfig(env: Env = process.env): WsConfig {
  return {
    ticketTtlSeconds: readBoundedInt(env, 'WS_TICKET_TTL_SECONDS'),
    ticketSkewSeconds: readBoundedInt(env, 'WS_TICKET_SKEW_SECONDS'),
    authTimeoutMs: readBoundedInt(env, 'WS_AUTH_TIMEOUT_MS'),
    idleTimeoutMs: readBoundedInt(env, 'WS_IDLE_TIMEOUT_SECONDS') * 1000,
    heartbeatIntervalMs: readBoundedInt(env, 'WS_HEARTBEAT_INTERVAL_SECONDS') * 1000,
    maxSessionsPerUser: readBoundedInt(env, 'WS_MAX_SESSIONS_PER_USER'),
    sessionLimitPolicy: readPolicy(env),
    maxMessagesPerMinute: readBoundedInt(env, 'WS_MAX_MESSAGES_PER_MINUTE'),
    maxSubscribesPerMinute: readBoundedInt(env, 'WS_MAX_SUBSCRIBES_PER_MINUTE'),
    maxRateStrikes: readBoundedInt(env, 'WS_MAX_RATE_STRIKES'),
    maxViolations: readBoundedInt(env, 'WS_MAX_VIOLATIONS'),
    maxMessageBytes: readBoundedInt(env, 'WS_MAX_MESSAGE_BYTES'),
  };
}

/**
 * Resolve the HMAC secret used to sign WS tickets.
 *
 * `WS_TICKET_SECRET` wins when set (minimum 32 characters, placeholders are
 * rejected). Otherwise a random per-process secret is generated so tickets can
 * never be forged with publicly known values. Production deployments should
 * set `WS_TICKET_SECRET` so tickets survive restarts and validate across
 * replicas; without it every restart invalidates in-flight tickets (bounded by
 * the <=5 minute ticket TTL) and the gateway warns at startup.
 */
export function resolveWsTicketSecret(env: Env = process.env): string {
  const provided = env.WS_TICKET_SECRET;
  if (provided !== undefined && provided.trim() !== '') {
    const secret = provided.trim();
    if (/change[_\s-]?me|placeholder|your[_\s-]?secret/i.test(secret)) {
      throw new Error(
        'WS_TICKET_SECRET is still a placeholder; generate one (e.g. `openssl rand -base64 32`)',
      );
    }
    if (secret.length < 32) {
      throw new Error('WS_TICKET_SECRET must be at least 32 characters long');
    }
    return secret;
  }
  if (env.NODE_ENV === 'production') {
    console.warn(
      '[ws-auth] WS_TICKET_SECRET is not set; using an ephemeral per-process secret. Tickets will not survive restarts or validate across replicas.',
    );
  }
  return crypto.randomBytes(32).toString('base64url');
}
