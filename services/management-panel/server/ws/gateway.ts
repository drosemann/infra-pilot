/**
 * Authenticated WebSocket gateway.
 *
 * Responsibilities:
 * - Authenticate every connection with a `TicketService` ticket (query string
 *   or `auth` message) before any feature message is honored.
 * - Authorize every per-app action through `AclService` (deny by default).
 * - Own connection lifecycle: auth timeout, heartbeat, idle timeout, session
 *   cap, rate limiting, and violation escalation.
 * - Own per-connection Docker streams (`logs`, `stats`) and their teardown,
 *   including killing the previous stream when a client re-subscribes.
 * - Relay collaborative-terminal room traffic (input, cursor, chat) after an
 *   ACL check.
 *
 * The class depends on narrow interfaces (`SocketLike`, `SpawnFn`,
 * `ExecCommand`) so it can be exercised end to end without Docker or a real
 * socket. `server/index.ts` injects the production resolvers.
 */
import { spawn } from 'child_process';
import type { IncomingMessage, Server } from 'http';
import { WebSocketServer } from 'ws';
import type { WsAuditLogger } from './audit.ts';
import { AclService, normalizeAppId } from './acl.ts';
import type { TicketService } from './auth.ts';
import { SessionRegistry } from './sessions.ts';
import { WsRateLimiter } from './rate-limit.ts';
import {
  WS_CLOSE_CODES,
  wsError,
  type Clock,
  type ExecCommand,
  type ExecResult,
  type ResolveAppAccess,
  type ResolveContainerId,
  type WsAction,
  type WsConfig,
  type WsSession,
} from './types.ts';

/** Minimal socket surface used by the gateway (real `WebSocket` satisfies it). */
export interface SocketLike {
  readyState: number;
  bufferedAmount?: number;
  send(data: string, cb?: (err?: Error) => void): void;
  close(code?: number, reason?: string): void;
  terminate?(): void;
  ping?(data?: Buffer): void;
  on(event: string, listener: (...args: unknown[]) => void): unknown;
}

/** Minimal child-process surface used for Docker streams and exec. */
export interface ChildProcessLike {
  stdout: { on(event: string, listener: (chunk: unknown) => void): unknown } | null;
  stderr: { on(event: string, listener: (chunk: unknown) => void): unknown } | null;
  on(event: string, listener: (...args: unknown[]) => void): unknown;
  kill(signal?: NodeJS.Signals): boolean;
  killed?: boolean;
}

export type SpawnFn = (command: string, args: string[]) => ChildProcessLike;

const WS_OPEN = 1;
const ROOM_OUTPUT_LIMIT = 1000;
const MAX_COMMAND_LENGTH = 2000;
const MAX_DISPLAY_NAME_LENGTH = 32;
const MAX_BUFFERED_BYTES = 4 * 1024 * 1024;
const DEFAULT_METRICS_INTERVAL_MS = 2000;
const DEFAULT_EXEC_TIMEOUT_MS = 15000;
const METRICS_MAX_CONSECUTIVE_FAILURES = 3;

export interface WsGatewayOptions {
  config: WsConfig;
  tickets: TicketService;
  audit: WsAuditLogger;
  resolveAppAccess?: ResolveAppAccess;
  resolveContainerId?: ResolveContainerId;
  execCommand?: ExecCommand;
  spawnFn?: SpawnFn;
  clock?: Clock;
  ipOf?: (req: IncomingMessage) => string | null;
  metricsIntervalMs?: number;
  execTimeoutMs?: number;
}

interface LogStreamHandle {
  kind: 'logs';
  appId: string;
  child: ChildProcessLike;
  stopped: boolean;
}

interface MetricsStreamHandle {
  kind: 'metrics';
  appId: string;
  interval: ReturnType<typeof setInterval>;
  failures: number;
  stopped: boolean;
}

type StreamHandle = LogStreamHandle | MetricsStreamHandle;

interface GatewayRoom {
  roomId: string;
  appId: string;
  clients: Map<SocketLike, { sessionId: string; userId: string; displayName: string }>;
  output: string[];
}

interface ConnectionContext {
  ws: SocketLike;
  ip: string | null;
  requestedAppId: string | null;
  requestedRoomId: string | null;
  displayName: string;
  authenticated: boolean;
  session: WsSession | null;
  authTimer: ReturnType<typeof setTimeout> | null;
  violations: number;
  aclViolations: number;
  streams: Map<string, StreamHandle>;
  closed: boolean;
}

/**
 * Sanitize a display name from query string or message.
 * @returns A printable name of at most 32 characters (defaults to `Anonymous`)
 */
export function sanitizeDisplayName(value: unknown): string {
  if (typeof value !== 'string') return 'Anonymous';
  let out = '';
  for (const ch of value) {
    const code = ch.codePointAt(0) ?? 0;
    if (code >= 0x20 && code !== 0x7f) out += ch;
    if (out.length >= MAX_DISPLAY_NAME_LENGTH) break;
  }
  return out.trim() || 'Anonymous';
}

function toChunkString(chunk: unknown): string {
  if (typeof chunk === 'string') return chunk;
  if (chunk instanceof Uint8Array) return Buffer.from(chunk).toString('utf8');
  return String(chunk);
}

/** Default exec: run `docker exec <container> sh -c <command>` with a timeout. */
function makeDefaultExecCommand(
  spawnFn: SpawnFn,
  timeoutMs: number,
): ExecCommand {
  return (containerId: string, command: string): Promise<ExecResult> =>
    new Promise((resolve) => {
      let child: ChildProcessLike;
      try {
        child = spawnFn('docker', ['exec', containerId, 'sh', '-c', command]);
      } catch (err) {
        resolve({ ok: false, output: '', error: (err as Error).message });
        return;
      }
      let output = '';
      let settled = false;
      const finish = (result: ExecResult) => {
        if (settled) return;
        settled = true;
        clearTimeout(timer);
        resolve(result);
      };
      const timer = setTimeout(() => {
        try {
          child.kill('SIGKILL');
        } catch {
          /* ignore */
        }
        finish({ ok: false, output, error: 'command timed out' });
      }, timeoutMs);
      timer.unref?.();
      child.stdout?.on('data', (chunk) => {
        output += toChunkString(chunk);
      });
      child.stderr?.on('data', (chunk) => {
        output += toChunkString(chunk);
      });
      child.on('error', (err) => {
        finish({ ok: false, output, error: (err as Error).message ?? 'exec failed' });
      });
      child.on('close', (code) => {
        const exitCode = typeof code === 'number' ? code : undefined;
        finish({ ok: exitCode === 0 || exitCode === undefined, output, exitCode });
      });
    });
}

/**
 * The authenticated WebSocket gateway. One instance per process.
 */
export class WsGateway {
  private readonly config: WsConfig;
  private readonly tickets: TicketService;
  private readonly audit: WsAuditLogger;
  private readonly acl: AclService;
  private readonly registry: SessionRegistry;
  private readonly resolveContainerId: ResolveContainerId | undefined;
  private readonly execCommand: ExecCommand;
  private readonly spawnFn: SpawnFn;
  private readonly clock: Clock;
  private readonly ipOf: (req: IncomingMessage) => string | null;
  private readonly metricsIntervalMs: number;
  private readonly execTimeoutMs: number;
  private readonly contexts = new Map<string, ConnectionContext>();
  private readonly rooms = new Map<string, GatewayRoom>();
  private readonly messageLimiter: WsRateLimiter;
  private readonly subscribeLimiter: WsRateLimiter;
  private wss: WebSocketServer | null = null;
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null;
  private sweepTimer: ReturnType<typeof setInterval> | null = null;

  constructor(options: WsGatewayOptions) {
    this.config = options.config;
    this.tickets = options.tickets;
    this.audit = options.audit;
    this.clock = options.clock ?? Date.now;
    this.resolveContainerId = options.resolveContainerId;
    this.spawnFn = options.spawnFn ?? ((command, args) => spawn(command, args) as ChildProcessLike);
    this.metricsIntervalMs = options.metricsIntervalMs ?? DEFAULT_METRICS_INTERVAL_MS;
    this.execTimeoutMs = options.execTimeoutMs ?? DEFAULT_EXEC_TIMEOUT_MS;
    this.execCommand = options.execCommand ?? makeDefaultExecCommand(this.spawnFn, this.execTimeoutMs);
    this.ipOf =
      options.ipOf ??
      ((req) => {
        const forwarded = req.headers['x-forwarded-for'];
        if (typeof forwarded === 'string' && forwarded.length > 0) {
          return forwarded.split(',')[0].trim();
        }
        return req.socket?.remoteAddress ?? null;
      });
    this.acl = new AclService({ resolveAppAccess: options.resolveAppAccess, audit: this.audit });
    this.registry = new SessionRegistry({
      idleTimeoutMs: this.config.idleTimeoutMs,
      maxSessionsPerUser: this.config.maxSessionsPerUser,
      sessionLimitPolicy: this.config.sessionLimitPolicy,
      heartbeatIntervalMs: this.config.heartbeatIntervalMs,
      clock: this.clock,
    });
    this.messageLimiter = new WsRateLimiter({
      capacity: this.config.maxMessagesPerMinute,
      perMinute: this.config.maxMessagesPerMinute,
      maxStrikes: this.config.maxRateStrikes,
      clock: this.clock,
    });
    this.subscribeLimiter = new WsRateLimiter({
      capacity: this.config.maxSubscribesPerMinute,
      perMinute: this.config.maxSubscribesPerMinute,
      maxStrikes: this.config.maxRateStrikes,
      clock: this.clock,
    });
  }

  /**
   * Attach the gateway to an HTTP server and start background timers.
   * @returns This gateway, for chaining
   */
  attach(server: Server): this {
    if (this.wss) return this;
    this.wss = new WebSocketServer({ server, maxPayload: this.config.maxMessageBytes });
    this.wss.on('connection', (ws, req) => {
      this.handleConnection(ws as unknown as SocketLike, req);
    });
    this.heartbeatTimer = setInterval(() => this.heartbeatTick(), this.config.heartbeatIntervalMs);
    this.heartbeatTimer.unref?.();
    this.sweepTimer = setInterval(() => this.sweep(), Math.min(this.config.idleTimeoutMs, 60000));
    this.sweepTimer.unref?.();
    return this;
  }

  /**
   * Handle one accepted WebSocket connection. Public so tests can drive a fake
   * socket without binding a real port.
   */
  handleConnection(ws: SocketLike, req: IncomingMessage): void {
    const url = new URL(req.url ?? '', 'http://localhost');
    const ctx: ConnectionContext = {
      ws,
      ip: this.ipOf(req),
      requestedAppId: url.searchParams.get('appId'),
      requestedRoomId: url.searchParams.get('sessionId'),
      displayName: sanitizeDisplayName(url.searchParams.get('displayName')),
      authenticated: false,
      session: null,
      authTimer: null,
      violations: 0,
      aclViolations: 0,
      streams: new Map(),
      closed: false,
    };

    ws.on('message', (data) => {
      void this.onMessage(ctx, data);
    });
    ws.on('close', () => this.cleanup(ctx, 'closed'));
    ws.on('error', () => this.cleanup(ctx, 'error'));
    ws.on('pong', () => {
      if (ctx.session) this.registry.recordPong(ctx.session.id);
    });

    const queryTicket = url.searchParams.get('ticket');
    if (queryTicket) {
      this.authenticate(ctx, queryTicket);
      return;
    }
    this.send(ctx.ws, {
      type: 'auth_challenge',
      authTimeoutMs: this.config.authTimeoutMs,
      serverTime: new Date(this.clock()).toISOString(),
    });
    ctx.authTimer = setTimeout(() => {
      if (ctx.authenticated || ctx.closed) return;
      this.audit.authFailed('timeout', ctx.ip);
      this.send(ctx.ws, wsError('auth_failed', 'Authentication timed out'));
      this.closeSocket(ctx, WS_CLOSE_CODES.AUTH_TIMEOUT, 'auth_timeout');
    }, this.config.authTimeoutMs);
    ctx.authTimer.unref?.();
  }

  /** Close the gateway, timers, and every live socket. */
  close(): void {
    if (this.heartbeatTimer) clearInterval(this.heartbeatTimer);
    if (this.sweepTimer) clearInterval(this.sweepTimer);
    this.heartbeatTimer = null;
    this.sweepTimer = null;
    for (const ctx of Array.from(this.contexts.values())) {
      this.cleanup(ctx, 'shutdown');
      try {
        ctx.ws.terminate?.();
      } catch {
        /* ignore */
      }
    }
    if (this.wss) {
      const server = this.wss;
      this.wss = null;
      server.close();
    }
  }

  /** Close every session for a user (used after ticket revocation). */
  closeUserSessions(userId: string, reason: string): number {
    const removed = this.registry.revokeUser(userId);
    for (const session of removed) {
      const ctx = this.contexts.get(session.id);
      if (ctx) this.closeSocket(ctx, WS_CLOSE_CODES.TICKET_INVALID, reason);
    }
    return removed.length;
  }

  /** Close sessions that authenticated with a specific ticket id. */
  closeTicketSessions(userId: string, jti: string, reason: string): number {
    let closed = 0;
    for (const ctx of Array.from(this.contexts.values())) {
      const session = ctx.session;
      if (session && session.userId === userId && session.ticketJti === jti) {
        this.closeSocket(ctx, WS_CLOSE_CODES.TICKET_INVALID, reason);
        closed += 1;
      }
    }
    return closed;
  }

  /** Diagnostics for tests and admin endpoints. */
  stats(): { connections: number; sessions: number; rooms: number } {
    return {
      connections: this.contexts.size,
      sessions: this.registry.count(),
      rooms: this.rooms.size,
    };
  }

  // -------------------------------------------------------------------------
  // Authentication
  // -------------------------------------------------------------------------

  private authenticate(ctx: ConnectionContext, ticket: unknown): void {
    if (ctx.closed) return;
    const result = this.tickets.verify(ticket);
    if (!result.ok) {
      const timeInvalid =
        result.reason === 'expired' ||
        result.reason === 'replayed' ||
        result.reason === 'revoked';
      this.audit.authFailed(result.reason, ctx.ip, result.claims?.uid);
      this.send(ctx.ws, wsError('auth_failed', `Authentication failed: ${result.reason}`));
      this.closeSocket(
        ctx,
        timeInvalid ? WS_CLOSE_CODES.TICKET_INVALID : WS_CLOSE_CODES.AUTH_FAILED,
        'auth_failed',
      );
      return;
    }
    const claims = result.claims;
    const appScope = claims.aid ?? null;
    if (appScope && ctx.requestedAppId && appScope !== ctx.requestedAppId) {
      this.audit.authFailed('scope_mismatch', ctx.ip, claims.uid);
      this.send(ctx.ws, wsError('auth_failed', 'Ticket scope does not match requested app'));
      this.closeSocket(ctx, WS_CLOSE_CODES.NOT_AUTHORIZED, 'scope_mismatch');
      return;
    }
    const created = this.registry.create(claims.uid, {
      appScope,
      ticketJti: claims.jti,
      ip: ctx.ip,
    });
    if (!created.ok) {
      this.send(ctx.ws, wsError('session_limit', 'Too many active sessions for this user'));
      this.closeSocket(ctx, WS_CLOSE_CODES.SESSION_LIMIT, 'session_limit');
      return;
    }
    for (const evicted of created.evicted) {
      const evictedCtx = this.contexts.get(evicted.id);
      if (evictedCtx) {
        this.closeSocket(evictedCtx, WS_CLOSE_CODES.SESSION_LIMIT, 'session_replaced');
      }
    }
    if (ctx.authTimer) {
      clearTimeout(ctx.authTimer);
      ctx.authTimer = null;
    }
    ctx.authenticated = true;
    ctx.session = created.session;
    this.contexts.set(created.session.id, ctx);
    this.audit.connected(created.session);
    this.send(ctx.ws, {
      type: 'ready',
      sessionId: created.session.id,
      userId: created.session.userId,
      appScope,
      mode: ctx.requestedRoomId ? 'terminal' : 'viewer',
    });
  }

  // -------------------------------------------------------------------------
  // Message dispatch
  // -------------------------------------------------------------------------

  private async onMessage(ctx: ConnectionContext, data: unknown): Promise<void> {
    if (ctx.closed) return;
    if (ctx.session) this.registry.touch(ctx.session.id);

    let msg: Record<string, unknown>;
    try {
      msg = JSON.parse(toChunkString(data)) as Record<string, unknown>;
    } catch {
      this.violation(ctx, 'bad_message', 'Message was not valid JSON');
      return;
    }
    if (!msg || typeof msg !== 'object' || Array.isArray(msg)) {
      this.violation(ctx, 'bad_message', 'Message must be a JSON object');
      return;
    }

    if (!ctx.authenticated) {
      if (msg.type === 'auth') {
        this.authenticate(ctx, msg.ticket);
        return;
      }
      this.violation(ctx, 'not_authenticated', 'Authenticate before sending messages');
      return;
    }

    if (msg.type === 'pong') {
      if (ctx.session) this.registry.recordPong(ctx.session.id);
      return;
    }
    if (msg.type === 'ping') {
      this.send(ctx.ws, { type: 'pong' });
      return;
    }

    const decision = this.messageLimiter.tryConsume(ctx.session!.id);
    if (!decision.allowed) {
      this.handleRateLimited(ctx, 'messages', decision.retryAfterMs);
      return;
    }

    switch (msg.type) {
      case 'subscribe':
        await this.handleSubscribeLogs(ctx, msg);
        return;
      case 'unsubscribe':
        this.handleUnsubscribeLogs(ctx, msg);
        return;
      case 'subscribe:metrics':
        await this.handleSubscribeMetrics(ctx, msg);
        return;
      case 'unsubscribe:metrics':
        this.handleUnsubscribeMetrics(ctx, msg);
        return;
      case 'exec':
        await this.handleExec(ctx, msg);
        return;
      case 'terminal-input':
        await this.handleTerminalInput(ctx, msg);
        return;
      case 'cursor':
        await this.handleCursor(ctx, msg);
        return;
      case 'chat':
        await this.handleChat(ctx, msg);
        return;
      case 'join':
        await this.handleJoin(ctx, msg);
        return;
      case 'leave':
        this.handleLeave(ctx, msg);
        return;
      case 'auth':
        this.violation(ctx, 'already_authenticated', 'Session is already authenticated');
        return;
      default:
        this.violation(ctx, 'unknown_type', `Unknown message type: ${String(msg.type)}`);
    }
  }

  private async authorize(
    ctx: ConnectionContext,
    appIdRaw: unknown,
    action: WsAction,
  ): Promise<string | null> {
    const appId = normalizeAppId(appIdRaw);
    if (!appId) {
      this.violation(ctx, 'app_required', 'A valid appId is required');
      return null;
    }
    const decision = await this.acl.authorize({ session: ctx.session!, appId, action });
    if (!decision.allowed) {
      this.aclViolations(ctx, appId, action);
      return null;
    }
    return appId;
  }

  private async resolveContainer(appId: string): Promise<string | null> {
    if (!this.resolveContainerId) return null;
    try {
      return await this.resolveContainerId(appId);
    } catch {
      return null;
    }
  }

  // -------------------------------------------------------------------------
  // Log and metrics streams
  // -------------------------------------------------------------------------

  private async handleSubscribeLogs(
    ctx: ConnectionContext,
    msg: Record<string, unknown>,
  ): Promise<void> {
    const appId = await this.authorize(ctx, msg.appId, 'logs:read');
    if (!appId) return;
    if (!this.consumeSubscribe(ctx)) return;
    const containerId = await this.resolveContainer(appId);
    if (!containerId) {
      this.send(ctx.ws, wsError('no_container', 'No container found for this app', { appId }));
      return;
    }
    this.startLogStream(ctx, appId, containerId);
    this.send(ctx.ws, { type: 'subscribed', appId, channel: 'logs' });
  }

  private startLogStream(ctx: ConnectionContext, appId: string, containerId: string): void {
    const key = `${appId}:logs`;
    this.stopStream(ctx, key);
    let child: ChildProcessLike;
    try {
      child = this.spawnFn('docker', ['logs', '--tail', '100', '-f', containerId]);
    } catch {
      this.send(ctx.ws, wsError('stream_failed', 'Failed to start log stream', { appId }));
      return;
    }
    const handle: LogStreamHandle = { kind: 'logs', appId, child, stopped: false };
    ctx.streams.set(key, handle);
    const forward = (chunk: unknown) => {
      if (handle.stopped || ctx.closed) return;
      this.sendStream(ctx.ws, { type: 'log', appId, data: toChunkString(chunk) });
    };
    child.stdout?.on('data', forward);
    child.stderr?.on('data', forward);
    child.on('error', () => {
      if (handle.stopped) return;
      this.stopStream(ctx, key);
      this.send(ctx.ws, wsError('stream_failed', 'Log stream failed', { appId }));
    });
    child.on('close', () => {
      if (handle.stopped) return;
      ctx.streams.delete(key);
      handle.stopped = true;
      this.send(ctx.ws, { type: 'log_end', appId });
    });
  }

  private handleUnsubscribeLogs(ctx: ConnectionContext, msg: Record<string, unknown>): void {
    const appId = normalizeAppId(msg.appId);
    if (!appId) {
      this.violation(ctx, 'app_required', 'A valid appId is required');
      return;
    }
    this.stopStream(ctx, `${appId}:logs`);
    this.send(ctx.ws, { type: 'unsubscribed', appId, channel: 'logs' });
  }

  private async handleSubscribeMetrics(
    ctx: ConnectionContext,
    msg: Record<string, unknown>,
  ): Promise<void> {
    const appId = await this.authorize(ctx, msg.appId, 'metrics:read');
    if (!appId) return;
    if (!this.consumeSubscribe(ctx)) return;
    const containerId = await this.resolveContainer(appId);
    if (!containerId) {
      this.send(ctx.ws, wsError('no_container', 'No container found for this app', { appId }));
      return;
    }
    this.startMetricsStream(ctx, appId, containerId);
    this.send(ctx.ws, { type: 'subscribed', appId, channel: 'metrics' });
  }

  private startMetricsStream(ctx: ConnectionContext, appId: string, containerId: string): void {
    const key = `${appId}:metrics`;
    this.stopStream(ctx, key);
    const handle: MetricsStreamHandle = {
      kind: 'metrics',
      appId,
      failures: 0,
      stopped: false,
      interval: setInterval(() => {
        void this.pollMetrics(ctx, handle, containerId);
      }, this.metricsIntervalMs),
    };
    handle.interval.unref?.();
    ctx.streams.set(key, handle);
  }

  private pollMetrics(
    ctx: ConnectionContext,
    handle: MetricsStreamHandle,
    containerId: string,
  ): Promise<void> {
    return new Promise((resolve) => {
      if (handle.stopped || ctx.closed) {
        resolve();
        return;
      }
      let child: ChildProcessLike;
      try {
        child = this.spawnFn('docker', [
          'stats',
          containerId,
          '--no-stream',
          '--format',
          '{{json .}}',
        ]);
      } catch {
        this.metricsFailure(ctx, handle);
        resolve();
        return;
      }
      let out = '';
      let settled = false;
      const done = () => {
        if (settled) return;
        settled = true;
        resolve();
      };
      child.stdout?.on('data', (chunk) => {
        out += toChunkString(chunk);
      });
      child.on('error', () => {
        this.metricsFailure(ctx, handle);
        done();
      });
      child.on('close', () => {
        if (handle.stopped || ctx.closed) {
          done();
          return;
        }
        try {
          const parsed = JSON.parse(out.trim()) as unknown;
          handle.failures = 0;
          this.sendStream(ctx.ws, { type: 'metrics', appId: handle.appId, data: parsed });
        } catch {
          this.metricsFailure(ctx, handle);
        }
        done();
      });
    });
  }

  private metricsFailure(ctx: ConnectionContext, handle: MetricsStreamHandle): void {
    if (handle.stopped) return;
    handle.failures += 1;
    if (handle.failures < METRICS_MAX_CONSECUTIVE_FAILURES) return;
    this.stopStream(ctx, `${handle.appId}:metrics`);
    this.send(ctx.ws, wsError('stream_failed', 'Metrics stream failed', { appId: handle.appId }));
  }

  private handleUnsubscribeMetrics(ctx: ConnectionContext, msg: Record<string, unknown>): void {
    const appId = normalizeAppId(msg.appId);
    if (!appId) {
      this.violation(ctx, 'app_required', 'A valid appId is required');
      return;
    }
    this.stopStream(ctx, `${appId}:metrics`);
    this.send(ctx.ws, { type: 'unsubscribed', appId, channel: 'metrics' });
  }

  private stopStream(ctx: ConnectionContext, key: string): void {
    const handle = ctx.streams.get(key);
    if (!handle) return;
    handle.stopped = true;
    ctx.streams.delete(key);
    if (handle.kind === 'logs') {
      try {
        handle.child.kill('SIGTERM');
      } catch {
        /* ignore */
      }
      return;
    }
    clearInterval(handle.interval);
  }

  private consumeSubscribe(ctx: ConnectionContext): boolean {
    const decision = this.subscribeLimiter.tryConsume(ctx.session!.userId);
    if (decision.allowed) return true;
    this.handleRateLimited(ctx, 'subscribe', decision.retryAfterMs);
    return false;
  }

  // -------------------------------------------------------------------------
  // Terminal / exec / rooms
  // -------------------------------------------------------------------------

  private async handleExec(ctx: ConnectionContext, msg: Record<string, unknown>): Promise<void> {
    const appId = await this.authorize(
      ctx,
      msg.appId ?? ctx.requestedAppId,
      'terminal:exec',
    );
    if (!appId) return;
    const command = typeof msg.command === 'string' ? msg.command : '';
    if (command.trim().length === 0 || command.length > MAX_COMMAND_LENGTH) {
      this.violation(ctx, 'bad_message', 'Invalid command');
      return;
    }
    const containerId = await this.resolveContainer(appId);
    if (!containerId) {
      this.send(ctx.ws, wsError('no_container', 'No container found for this app', { appId }));
      return;
    }
    const roomId = this.roomFor(ctx, msg.roomId);
    if (roomId) {
      this.broadcastRoom(roomId, {
        type: 'terminal-output',
        line: `[${ctx.displayName}] $ ${command}`,
        userId: ctx.session!.userId,
        displayName: ctx.displayName,
      });
    }
    const result: ExecResult = await this.execCommand(containerId, command);
    this.send(ctx.ws, {
      type: 'exec_result',
      appId,
      command,
      ok: result.ok,
      output: result.output,
      error: result.error,
      exitCode: result.exitCode,
    });
  }

  private async handleTerminalInput(
    ctx: ConnectionContext,
    msg: Record<string, unknown>,
  ): Promise<void> {
    const appId = await this.authorize(ctx, msg.appId ?? ctx.requestedAppId, 'terminal:write');
    if (!appId) return;
    const roomId = this.roomFor(ctx, msg.roomId);
    if (!roomId) {
      this.violation(ctx, 'app_required', 'Join a room before sending input');
      return;
    }
    const text = typeof msg.text === 'string' ? msg.text : '';
    const line = `[${ctx.displayName}] $ ${text}`;
    const room = this.rooms.get(roomId);
    if (room) {
      room.output.push(line);
      if (room.output.length > ROOM_OUTPUT_LIMIT) room.output.shift();
    }
    this.broadcastRoom(roomId, {
      type: 'terminal-output',
      line,
      userId: ctx.session!.userId,
      displayName: ctx.displayName,
    });
  }

  private async handleCursor(ctx: ConnectionContext, msg: Record<string, unknown>): Promise<void> {
    const appId = await this.authorize(ctx, msg.appId ?? ctx.requestedAppId, 'terminal:write');
    if (!appId) return;
    const roomId = this.roomFor(ctx, msg.roomId);
    if (!roomId) {
      this.violation(ctx, 'app_required', 'Join a room before sending a cursor update');
      return;
    }
    this.broadcastRoom(
      roomId,
      {
        type: 'cursor-update',
        userId: ctx.session!.userId,
        displayName: ctx.displayName,
        cursor: msg.cursor,
      },
      ctx.ws,
    );
  }

  private async handleChat(ctx: ConnectionContext, msg: Record<string, unknown>): Promise<void> {
    const appId = await this.authorize(ctx, msg.appId ?? ctx.requestedAppId, 'terminal:write');
    if (!appId) return;
    const roomId = this.roomFor(ctx, msg.roomId);
    if (!roomId) {
      this.violation(ctx, 'app_required', 'Join a room before chatting');
      return;
    }
    const text = typeof msg.text === 'string' ? msg.text : '';
    this.broadcastRoom(roomId, {
      type: 'chat-message',
      userId: ctx.session!.userId,
      displayName: ctx.displayName,
      text,
      timestamp: new Date(this.clock()).toISOString(),
    });
  }

  private async handleJoin(ctx: ConnectionContext, msg: Record<string, unknown>): Promise<void> {
    const appId = await this.authorize(ctx, msg.appId ?? ctx.requestedAppId, 'terminal:write');
    if (!appId) return;
    const roomId = normalizeAppId(msg.roomId) ?? normalizeAppId(ctx.requestedRoomId);
    if (!roomId) {
      this.violation(ctx, 'app_required', 'A valid roomId is required');
      return;
    }
    const displayName = sanitizeDisplayName(msg.displayName ?? ctx.displayName);
    ctx.displayName = displayName;

    let room = this.rooms.get(roomId);
    if (room && room.appId !== appId) {
      this.send(
        ctx.ws,
        wsError('app_required', 'Room belongs to a different app', { appId, action: 'terminal:write' }),
      );
      return;
    }
    if (!room) {
      room = { roomId, appId, clients: new Map(), output: [] };
      this.rooms.set(roomId, room);
    }
    if (!room.clients.has(ctx.ws)) {
      room.clients.set(ctx.ws, {
        sessionId: ctx.session!.id,
        userId: ctx.session!.userId,
        displayName,
      });
    }
    ctx.session!.rooms.add(roomId);
    this.send(ctx.ws, { type: 'history', lines: room.output });
    this.broadcastRoom(roomId, {
      type: 'user-joined',
      userId: ctx.session!.userId,
      displayName,
      users: Array.from(room.clients.values()),
    });
  }

  private handleLeave(ctx: ConnectionContext, msg: Record<string, unknown>): void {
    const roomId = normalizeAppId(msg.roomId) ?? normalizeAppId(ctx.requestedRoomId);
    if (!roomId) {
      this.violation(ctx, 'app_required', 'A valid roomId is required');
      return;
    }
    this.leaveRoom(ctx, roomId);
  }

  private leaveRoom(ctx: ConnectionContext, roomId: string): void {
    const room = this.rooms.get(roomId);
    if (!room) return;
    const info = room.clients.get(ctx.ws);
    if (!info) return;
    room.clients.delete(ctx.ws);
    ctx.session?.rooms.delete(roomId);
    this.broadcastRoom(
      roomId,
      {
        type: 'user-left',
        userId: info.userId,
        displayName: info.displayName,
        users: Array.from(room.clients.values()),
      },
      ctx.ws,
    );
    if (room.clients.size === 0) this.rooms.delete(roomId);
  }

  private roomFor(ctx: ConnectionContext, explicit: unknown): string | null {
    const roomId = normalizeAppId(explicit) ?? normalizeAppId(ctx.requestedRoomId);
    if (!roomId) return null;
    const room = this.rooms.get(roomId);
    if (!room || !room.clients.has(ctx.ws)) return null;
    return roomId;
  }

  // -------------------------------------------------------------------------
  // Heartbeat, idle sweep, violations, teardown
  // -------------------------------------------------------------------------

  /**
   * Advance the heartbeat for every session: ping idle sockets and close ones
   * that missed a pong. Public so operators and tests can drive it directly.
   */
  heartbeatTick(): void {
    const now = this.clock();
    const { ping, dead } = this.registry.heartbeatTick(now);
    for (const session of ping) {
      const ctx = this.contexts.get(session.id);
      if (ctx) this.sendPing(ctx);
    }
    for (const session of dead) {
      const ctx = this.contexts.get(session.id);
      if (ctx) {
        this.closeSocket(ctx, WS_CLOSE_CODES.IDLE_TIMEOUT, 'heartbeat_timeout');
      }
    }
    this.tickets.sweep(now);
  }

  /**
   * Close sessions idle longer than the timeout and prune rate-limit/ticket
   * state. Public so operators and tests can drive it directly.
   */
  sweep(): void {
    const now = this.clock();
    for (const session of this.registry.sweepIdle(now)) {
      const ctx = this.contexts.get(session.id);
      if (ctx) {
        this.closeSocket(ctx, WS_CLOSE_CODES.IDLE_TIMEOUT, 'idle_timeout');
      }
    }
    this.messageLimiter.sweep(now);
    this.subscribeLimiter.sweep(now);
  }

  private aclViolations(ctx: ConnectionContext, appId: string, action: WsAction): void {
    this.send(ctx.ws, wsError('not_authorized', 'Not authorized for this action', { appId, action }));
    ctx.aclViolations += 1;
    if (ctx.aclViolations >= this.config.maxViolations) {
      this.closeSocket(ctx, WS_CLOSE_CODES.NOT_AUTHORIZED, 'not_authorized');
    }
  }

  private violation(ctx: ConnectionContext, code: string, message: string): void {
    this.send(ctx.ws, wsError(code, message));
    ctx.violations += 1;
    if (ctx.violations >= this.config.maxViolations) {
      this.closeSocket(ctx, WS_CLOSE_CODES.POLICY_VIOLATION, 'policy_violation');
    }
  }

  private handleRateLimited(
    ctx: ConnectionContext,
    scope: 'messages' | 'subscribe',
    retryAfterMs: number,
  ): void {
    const key = scope === 'messages' ? ctx.session!.id : ctx.session!.userId;
    const limiter = scope === 'messages' ? this.messageLimiter : this.subscribeLimiter;
    this.audit.rateLimited(ctx.session!.userId, ctx.session!.id, scope, retryAfterMs, ctx.ip);
    this.send(ctx.ws, wsError('rate_limited', 'Rate limit exceeded', { scope, retryAfterMs }));
    if (limiter.isExhausted(key)) {
      this.closeSocket(ctx, WS_CLOSE_CODES.RATE_LIMITED, 'rate_limited');
    }
  }

  private cleanup(ctx: ConnectionContext, reason: string): void {
    if (ctx.closed) return;
    ctx.closed = true;
    if (ctx.authTimer) {
      clearTimeout(ctx.authTimer);
      ctx.authTimer = null;
    }
    for (const key of Array.from(ctx.streams.keys())) this.stopStream(ctx, key);
    for (const roomId of Array.from(ctx.session?.rooms ?? [])) this.leaveRoom(ctx, roomId);
    const session = ctx.session;
    if (session) {
      this.registry.remove(session.id);
      this.contexts.delete(session.id);
      this.audit.disconnected(session, reason);
      this.messageLimiter.forget(session.id);
      this.subscribeLimiter.forget(session.userId);
    }
  }

  private closeSocket(ctx: ConnectionContext, code: number, reason: string): void {
    if (!ctx.closed) {
      this.cleanup(ctx, reason);
    }
    try {
      ctx.ws.close(code, reason.slice(0, 123));
    } catch {
      /* socket already gone */
    }
  }

  // -------------------------------------------------------------------------
  // Send helpers
  // -------------------------------------------------------------------------

  private send(ws: SocketLike, payload: unknown): void {
    if (ws.readyState !== WS_OPEN) return;
    try {
      ws.send(JSON.stringify(payload));
    } catch {
      /* socket closing */
    }
  }

  /** Send a high-volume stream frame, dropping it under backpressure. */
  private sendStream(ws: SocketLike, payload: unknown): void {
    if (ws.readyState !== WS_OPEN) return;
    if ((ws.bufferedAmount ?? 0) > MAX_BUFFERED_BYTES) return;
    this.send(ws, payload);
  }

  private sendPing(ctx: ConnectionContext): void {
    try {
      ctx.ws.ping?.();
    } catch {
      /* socket closing */
    }
  }

  private broadcastRoom(roomId: string, payload: unknown, except?: SocketLike): void {
    const room = this.rooms.get(roomId);
    if (!room) return;
    const text = JSON.stringify(payload);
    for (const [client] of room.clients) {
      if (client === except) continue;
      if (client.readyState !== WS_OPEN) continue;
      try {
        client.send(text);
      } catch {
        /* socket closing */
      }
    }
  }
}

/**
 * Create a gateway instance.
 * @param options - Config, ticket service, audit logger, and host resolvers
 */
export function createWsGateway(options: WsGatewayOptions): WsGateway {
  return new WsGateway(options);
}
