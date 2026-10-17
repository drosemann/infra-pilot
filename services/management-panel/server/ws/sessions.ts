/**
 * Session registry for authenticated WebSocket connections.
 *
 * Tracks one record per live socket: identity, ticket scope, activity, and
 * heartbeat state. Enforces the per-user session cap (kick-oldest or reject),
 * the idle timeout, and ping/pong liveness. The registry stores data only —
 * closing sockets is the gateway's job, which keeps this module testable with
 * a fake clock and no I/O.
 */
import { randomUUID } from 'crypto';
import type { Clock, WsConfig, WsSession } from './types.ts';

export interface SessionRegistryOptions {
  idleTimeoutMs: number;
  maxSessionsPerUser: number;
  sessionLimitPolicy: 'kick-oldest' | 'reject';
  heartbeatIntervalMs: number;
  clock?: Clock;
}

export type CreateSessionResult =
  | { ok: true; session: WsSession; evicted: WsSession[] }
  | { ok: false; reason: 'limit' };

export interface HeartbeatResult {
  /** Sessions that should be pinged now (no ping in flight). */
  ping: WsSession[];
  /** Sessions that missed a pong for a full interval (terminate them). */
  dead: WsSession[];
}

/**
 * Build registry options from validated gateway config.
 */
export function sessionRegistryOptionsFromConfig(config: WsConfig): SessionRegistryOptions {
  return {
    idleTimeoutMs: config.idleTimeoutMs,
    maxSessionsPerUser: config.maxSessionsPerUser,
    sessionLimitPolicy: config.sessionLimitPolicy,
    heartbeatIntervalMs: config.heartbeatIntervalMs,
  };
}

export class SessionRegistry {
  private readonly sessions = new Map<string, WsSession>();
  private readonly byUser = new Map<string, Set<WsSession>>();
  private readonly idleTimeoutMs: number;
  private readonly maxSessionsPerUser: number;
  private readonly policy: 'kick-oldest' | 'reject';
  private readonly heartbeatIntervalMs: number;
  private readonly clock: Clock;

  constructor(options: SessionRegistryOptions) {
    this.idleTimeoutMs = options.idleTimeoutMs;
    this.maxSessionsPerUser = options.maxSessionsPerUser;
    this.policy = options.sessionLimitPolicy;
    this.heartbeatIntervalMs = options.heartbeatIntervalMs;
    this.clock = options.clock ?? Date.now;
  }

  /**
   * Register a new session for a user.
   *
   * Under `kick-oldest`, the user's oldest session is evicted and returned so
   * the gateway can close its socket; under `reject`, no session is created.
   */
  create(
    userId: string,
    details: { appScope: string | null; ticketJti: string; ip: string | null },
  ): CreateSessionResult {
    const now = this.clock();
    const existing = this.byUser.get(userId);
    const evicted: WsSession[] = [];
    if (existing && existing.size >= this.maxSessionsPerUser) {
      if (this.policy === 'reject') {
        return { ok: false, reason: 'limit' };
      }
      const oldest = this.oldestOf(existing);
      if (oldest) {
        this.removeInternal(oldest);
        evicted.push(oldest);
      }
    }
    const session: WsSession = {
      id: randomUUID(),
      userId,
      appScope: details.appScope,
      ticketJti: details.ticketJti,
      ip: details.ip,
      createdAt: now,
      lastActivityAt: now,
      pingSentAt: null,
      awaitingPong: false,
      lastPongAt: now,
      rooms: new Set<string>(),
    };
    this.sessions.set(session.id, session);
    let bucket = this.byUser.get(userId);
    if (!bucket) {
      bucket = new Set<WsSession>();
      this.byUser.set(userId, bucket);
    }
    bucket.add(session);
    return { ok: true, session, evicted };
  }

  private oldestOf(bucket: Set<WsSession>): WsSession | null {
    let oldest: WsSession | null = null;
    for (const candidate of bucket) {
      if (!oldest || candidate.createdAt < oldest.createdAt) {
        oldest = candidate;
      }
    }
    return oldest;
  }

  private removeInternal(session: WsSession): WsSession | undefined {
    if (!this.sessions.delete(session.id)) return undefined;
    const bucket = this.byUser.get(session.userId);
    if (bucket) {
      bucket.delete(session);
      if (bucket.size === 0) this.byUser.delete(session.userId);
    }
    return session;
  }

  /**
   * Remove a session (socket closed).
   * @returns The removed session, or undefined when already gone
   */
  remove(sessionId: string): WsSession | undefined {
    const session = this.sessions.get(sessionId);
    if (!session) return undefined;
    return this.removeInternal(session);
  }

  get(sessionId: string): WsSession | undefined {
    return this.sessions.get(sessionId);
  }

  /** Record client activity (any inbound message). */
  touch(sessionId: string): void {
    const session = this.sessions.get(sessionId);
    if (session) session.lastActivityAt = this.clock();
  }

  /** Record a pong frame; clears the outstanding ping. */
  recordPong(sessionId: string): void {
    const session = this.sessions.get(sessionId);
    if (!session) return;
    session.awaitingPong = false;
    session.lastPongAt = this.clock();
  }

  /**
   * Advance heartbeat bookkeeping for every session.
   * Sessions with no ping in flight are scheduled for ping; sessions still
   * awaiting a pong a full interval later are reported dead and removed.
   */
  heartbeatTick(nowMs?: number): HeartbeatResult {
    const now = nowMs ?? this.clock();
    const ping: WsSession[] = [];
    const dead: WsSession[] = [];
    for (const session of Array.from(this.sessions.values())) {
      if (!session.awaitingPong) {
        session.awaitingPong = true;
        session.pingSentAt = now;
        ping.push(session);
        continue;
      }
      const sentAt = session.pingSentAt ?? now;
      if (now - sentAt >= this.heartbeatIntervalMs) {
        this.removeInternal(session);
        dead.push(session);
      }
    }
    return { ping, dead };
  }

  /**
   * Remove sessions idle longer than the configured timeout.
   * @returns The sessions the gateway must close with `IDLE_TIMEOUT`
   */
  sweepIdle(nowMs?: number): WsSession[] {
    const now = nowMs ?? this.clock();
    const idle: WsSession[] = [];
    for (const session of Array.from(this.sessions.values())) {
      if (now - session.lastActivityAt >= this.idleTimeoutMs) {
        this.removeInternal(session);
        idle.push(session);
      }
    }
    return idle;
  }

  /**
   * Remove every session belonging to a user (auth revocation events).
   * @returns The removed sessions so the gateway can close their sockets
   */
  revokeUser(userId: string): WsSession[] {
    const bucket = this.byUser.get(userId);
    if (!bucket) return [];
    const removed: WsSession[] = [];
    for (const session of Array.from(bucket)) {
      this.removeInternal(session);
      removed.push(session);
    }
    return removed;
  }

  sessionsForUser(userId: string): WsSession[] {
    const bucket = this.byUser.get(userId);
    return bucket ? Array.from(bucket) : [];
  }

  all(): WsSession[] {
    return Array.from(this.sessions.values());
  }

  count(): number {
    return this.sessions.size;
  }

  countForUser(userId: string): number {
    return this.byUser.get(userId)?.size ?? 0;
  }
}
