import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import {
  createWsGateway,
  DEFAULT_WS_CONFIG,
  sanitizeDisplayName,
  TicketService,
  WsAuditLogger,
  WS_CLOSE_CODES,
} from '../../server/ws/index.ts';
import type { WsConfig, WsGatewayOptions } from '../../server/ws/index.ts';
import { FakeSocket, flush, makeRequest, makeSpawnQueue, waitFor } from '../helpers/ws-fakes.ts';

const SECRET = 'gateway-unit-test-secret-long-enough-123';

interface AuditCall {
  userId: string;
  action: string;
  entityType: string;
  entityId?: string;
  newValue?: unknown;
}

/** Build a gateway with fake clock, socket, and spawn queue. */
function makeGateway(overrides: Partial<WsGatewayOptions> = {}, configOverrides: Partial<WsConfig> = {}) {
  const state = { nowMs: 1_000_000 };
  const auditCalls: AuditCall[] = [];
  const audit = new WsAuditLogger({
    log: (userId, action, entityType, entityId, _old, newValue) => {
      auditCalls.push({ userId, action, entityType, entityId, newValue });
    },
  });
  const tickets = new TicketService({
    secret: SECRET,
    ttlSeconds: 300,
    skewSeconds: 30,
    clock: () => state.nowMs,
  });
  const spawnQueue = makeSpawnQueue();
  const gateway = createWsGateway({
    config: { ...DEFAULT_WS_CONFIG, authTimeoutMs: 5000, ...configOverrides },
    tickets,
    audit,
    resolveAppAccess: () => true,
    resolveContainerId: (appId) => `container-${appId}`,
    spawnFn: spawnQueue.spawnFn,
    clock: () => state.nowMs,
    metricsIntervalMs: 10,
    ...overrides,
  });
  return { gateway, tickets, auditCalls, spawnQueue, state };
}

/** Connect a fake socket and authenticate with a fresh ticket. */
async function connectAuthed(
  gateway: ReturnType<typeof createWsGateway>,
  tickets: TicketService,
  options: { userId?: string; url?: string; ticket?: string } = {},
) {
  const socket = new FakeSocket();
  const url = options.url ?? `/?ticket=${options.ticket ?? tickets.mint(options.userId ?? 'user-1').ticket}`;
  gateway.handleConnection(socket, makeRequest(url));
  await flush();
  return socket;
}

describe('gateway handshake', () => {
  it('authenticates via ?ticket= and sends ready without a challenge', async () => {
    const { gateway, tickets } = makeGateway();
    const socket = await connectAuthed(gateway, tickets);
    assert.equal(socket.messagesOfType('auth_challenge').length, 0);
    const ready = socket.lastOfType('ready');
    assert.ok(ready);
    assert.equal(ready.userId, 'user-1');
    assert.equal(ready.mode, 'viewer');
    assert.equal(gateway.stats().sessions, 1);
    gateway.close();
  });

  it('challenges ticketless connections and completes on an auth message', async () => {
    const { gateway, tickets } = makeGateway();
    const socket = new FakeSocket();
    gateway.handleConnection(socket, makeRequest('/'));
    const challenge = socket.lastOfType('auth_challenge');
    assert.ok(challenge);
    assert.equal(challenge.authTimeoutMs, 5000);
    socket.receive({ type: 'auth', ticket: tickets.mint('user-1').ticket });
    await flush();
    assert.ok(socket.lastOfType('ready'));
    gateway.close();
  });

  it('closes with AUTH_TIMEOUT when no ticket arrives', async () => {
    const { gateway } = makeGateway({}, { authTimeoutMs: 20 });
    const socket = new FakeSocket();
    gateway.handleConnection(socket, makeRequest('/'));
    const closed = await waitFor(() => socket.closed, 2000);
    assert.equal(closed, true);
    assert.equal(socket.closeCode, WS_CLOSE_CODES.AUTH_TIMEOUT);
    gateway.close();
  });

  it('closes with AUTH_FAILED on a malformed ticket', async () => {
    const { gateway } = makeGateway();
    const socket = await connectAuthed(gateway, null as never, { ticket: 'garbage' });
    assert.equal(socket.closeCode, WS_CLOSE_CODES.AUTH_FAILED);
    assert.equal(socket.lastOfType('error').code, 'auth_failed');
    gateway.close();
  });

  it('closes with TICKET_INVALID on a replayed ticket', async () => {
    const { gateway, tickets } = makeGateway();
    const ticket = tickets.mint('user-1').ticket;
    const first = await connectAuthed(gateway, tickets, { ticket });
    assert.ok(first.lastOfType('ready'));
    const second = await connectAuthed(gateway, tickets, { ticket });
    assert.equal(second.closeCode, WS_CLOSE_CODES.TICKET_INVALID);
    gateway.close();
  });

  it('closes with NOT_AUTHORIZED when the ticket scope mismatches ?appId=', async () => {
    const { gateway, tickets } = makeGateway();
    const ticket = tickets.mint('user-1', { appId: 'app-1' }).ticket;
    const socket = await connectAuthed(gateway, tickets, {
      ticket,
      url: `/?ticket=${ticket}&appId=app-2`,
    });
    assert.equal(socket.closeCode, WS_CLOSE_CODES.NOT_AUTHORIZED);
    gateway.close();
  });

  it('accepts a scoped ticket that matches ?appId= and reports the scope', async () => {
    const { gateway, tickets } = makeGateway();
    const ticket = tickets.mint('user-1', { appId: 'app-1' }).ticket;
    const socket = await connectAuthed(gateway, tickets, {
      ticket,
      url: `/?ticket=${ticket}&appId=app-1`,
    });
    assert.equal(socket.lastOfType('ready').appScope, 'app-1');
    gateway.close();
  });

  it('closes the oldest session with SESSION_LIMIT under kick-oldest', async () => {
    const { gateway, tickets } = makeGateway({}, { maxSessionsPerUser: 2, sessionLimitPolicy: 'kick-oldest' });
    const first = await connectAuthed(gateway, tickets);
    const second = await connectAuthed(gateway, tickets);
    const third = await connectAuthed(gateway, tickets);
    assert.ok(third.lastOfType('ready'));
    assert.equal(first.closeCode, WS_CLOSE_CODES.SESSION_LIMIT);
    assert.equal(second.closed, false);
    assert.equal(gateway.stats().sessions, 2);
    gateway.close();
  });

  it('rejects new sessions with SESSION_LIMIT under the reject policy', async () => {
    const { gateway, tickets } = makeGateway({}, { maxSessionsPerUser: 1, sessionLimitPolicy: 'reject' });
    await connectAuthed(gateway, tickets);
    const second = await connectAuthed(gateway, tickets);
    assert.equal(second.closeCode, WS_CLOSE_CODES.SESSION_LIMIT);
    assert.equal(second.lastOfType('error').code, 'session_limit');
    gateway.close();
  });

  it('refuses a ticket minted after a revoke-all', async () => {
    const { gateway, tickets } = makeGateway();
    tickets.revokeAllForUser('user-1');
    const socket = await connectAuthed(gateway, tickets);
    assert.equal(socket.closeCode, WS_CLOSE_CODES.TICKET_INVALID);
    gateway.close();
  });
});

describe('gateway protocol violations', () => {
  it('rejects non-JSON frames and unknown message types', async () => {
    const { gateway, tickets } = makeGateway({}, { maxViolations: 5 });
    const socket = await connectAuthed(gateway, tickets);
    socket.receiveRaw('this is not json');
    await flush();
    assert.equal(socket.lastOfType('error').code, 'bad_message');
    socket.receive({ type: 'definitely-not-a-type' });
    await flush();
    assert.equal(socket.lastOfType('error').code, 'unknown_type');
    assert.equal(socket.closed, false);
    gateway.close();
  });

  it('disconnects after repeated protocol violations', async () => {
    const { gateway, tickets } = makeGateway({}, { maxViolations: 3 });
    const socket = await connectAuthed(gateway, tickets);
    for (let i = 0; i < 3; i += 1) {
      socket.receive({ type: 'nope', n: i });
      await flush();
    }
    assert.equal(socket.closeCode, WS_CLOSE_CODES.POLICY_VIOLATION);
    gateway.close();
  });

  it('rejects feature messages sent before authentication', async () => {
    const { gateway, spawnQueue } = makeGateway({}, { maxViolations: 10 });
    const socket = new FakeSocket();
    gateway.handleConnection(socket, makeRequest('/'));
    socket.receive({ type: 'subscribe', appId: 'app-1' });
    await flush();
    assert.equal(socket.lastOfType('error').code, 'not_authenticated');
    assert.equal(spawnQueue.calls.length, 0);
    assert.equal(gateway.stats().sessions, 0);
    gateway.close();
  });

  it('treats a second auth message as a violation', async () => {
    const { gateway, tickets } = makeGateway({}, { maxViolations: 5 });
    const socket = await connectAuthed(gateway, tickets);
    socket.receive({ type: 'auth', ticket: tickets.mint('user-1').ticket });
    await flush();
    assert.equal(socket.lastOfType('error').code, 'already_authenticated');
    gateway.close();
  });

  it('rejects array and scalar frames', async () => {
    const { gateway, tickets } = makeGateway();
    const socket = await connectAuthed(gateway, tickets);
    socket.receiveRaw('[1,2,3]');
    await flush();
    assert.equal(socket.lastOfType('error').code, 'bad_message');
    socket.receiveRaw('"just a string"');
    await flush();
    assert.equal(socket.lastOfType('error').code, 'bad_message');
    gateway.close();
  });

  it('answers application pings with pongs', async () => {
    const { gateway, tickets } = makeGateway();
    const socket = await connectAuthed(gateway, tickets);
    socket.receive({ type: 'ping' });
    await flush();
    assert.ok(socket.lastOfType('pong'));
    gateway.close();
  });
});

describe('gateway ACL enforcement', () => {
  it('denies subscribe without spawning docker when the resolver refuses', async () => {
    const { gateway, tickets, spawnQueue } = makeGateway({ resolveAppAccess: () => false });
    const socket = await connectAuthed(gateway, tickets);
    socket.receive({ type: 'subscribe', appId: 'app-1' });
    await flush();
    const err = socket.lastOfType('error');
    assert.equal(err.code, 'not_authorized');
    assert.equal(err.appId, 'app-1');
    assert.equal(err.action, 'logs:read');
    assert.equal(spawnQueue.calls.length, 0);
    assert.equal(socket.messagesOfType('subscribed').length, 0);
    gateway.close();
  });

  it('disconnects after repeated ACL denials', async () => {
    const { gateway, tickets } = makeGateway({ resolveAppAccess: () => false }, { maxViolations: 3 });
    const socket = await connectAuthed(gateway, tickets);
    for (let i = 0; i < 3; i += 1) {
      socket.receive({ type: 'subscribe', appId: `app-${i}` });
      await flush();
    }
    assert.equal(socket.closeCode, WS_CLOSE_CODES.NOT_AUTHORIZED);
    gateway.close();
  });

  it('narrows a scoped ticket: other apps are refused without consulting the resolver', async () => {
    let resolverCalls = 0;
    const { gateway, tickets } = makeGateway({
      resolveAppAccess: () => {
        resolverCalls += 1;
        return true;
      },
    });
    const ticket = tickets.mint('user-1', { appId: 'app-1' }).ticket;
    const socket = await connectAuthed(gateway, tickets, { ticket });
    socket.receive({ type: 'subscribe', appId: 'app-2' });
    await flush();
    const err = socket.lastOfType('error');
    assert.equal(err.code, 'not_authorized');
    assert.equal(resolverCalls, 0);
    gateway.close();
  });

  it('audits denials with the session user id', async () => {
    const { gateway, tickets, auditCalls } = makeGateway({ resolveAppAccess: () => false });
    const socket = await connectAuthed(gateway, tickets, { userId: 'user-9' });
    socket.receive({ type: 'subscribe', appId: 'app-1' });
    await flush();
    const denial = auditCalls.find((c) => c.action === 'ws:subscribe:denied');
    assert.ok(denial);
    assert.equal(denial.userId, 'user-9');
    gateway.close();
  });

  it('rejects a missing or invalid appId on subscribe', async () => {
    const { gateway, tickets } = makeGateway();
    const socket = await connectAuthed(gateway, tickets);
    socket.receive({ type: 'subscribe' });
    await flush();
    assert.equal(socket.lastOfType('error').code, 'app_required');
    socket.receive({ type: 'subscribe', appId: 42 });
    await flush();
    assert.equal(socket.lastOfType('error').code, 'app_required');
    gateway.close();
  });
});

describe('gateway log streams', () => {
  it('spawns docker logs only after authorization and forwards output', async () => {
    const { gateway, tickets, spawnQueue } = makeGateway();
    const socket = await connectAuthed(gateway, tickets);
    socket.receive({ type: 'subscribe', appId: 'app-1' });
    await flush();
    assert.equal(socket.lastOfType('subscribed').appId, 'app-1');
    assert.equal(spawnQueue.calls.length, 1);
    assert.deepEqual(spawnQueue.calls[0], {
      command: 'docker',
      args: ['logs', '--tail', '100', '-f', 'container-app-1'],
    });
    spawnQueue.children[0].emitStdout('hello\n');
    const log = socket.lastOfType('log');
    assert.equal(log.appId, 'app-1');
    assert.equal(log.data, 'hello\n');
    gateway.close();
  });

  it('kills the stream on unsubscribe and reports unsubscribed', async () => {
    const { gateway, tickets, spawnQueue } = makeGateway();
    const socket = await connectAuthed(gateway, tickets);
    socket.receive({ type: 'subscribe', appId: 'app-1' });
    await flush();
    socket.receive({ type: 'unsubscribe', appId: 'app-1' });
    await flush();
    assert.equal(spawnQueue.children[0].killed, true);
    assert.equal(socket.lastOfType('unsubscribed').channel, 'logs');
    gateway.close();
  });

  it('kills the previous stream when re-subscribing to the same app', async () => {
    const { gateway, tickets, spawnQueue } = makeGateway();
    const socket = await connectAuthed(gateway, tickets);
    socket.receive({ type: 'subscribe', appId: 'app-1' });
    await flush();
    socket.receive({ type: 'subscribe', appId: 'app-1' });
    await flush();
    assert.equal(spawnQueue.calls.length, 2);
    assert.equal(spawnQueue.children[0].killed, true);
    assert.equal(spawnQueue.children[1].killed, false);
    gateway.close();
  });

  it('kills every stream on disconnect', async () => {
    const { gateway, tickets, spawnQueue } = makeGateway();
    const socket = await connectAuthed(gateway, tickets);
    socket.receive({ type: 'subscribe', appId: 'app-1' });
    await flush();
    socket.disconnect();
    await flush();
    assert.equal(spawnQueue.children[0].killed, true);
    assert.equal(gateway.stats().sessions, 0);
    gateway.close();
  });

  it('reports stream_failed when the docker child errors', async () => {
    const { gateway, tickets, spawnQueue } = makeGateway();
    const socket = await connectAuthed(gateway, tickets);
    socket.receive({ type: 'subscribe', appId: 'app-1' });
    await flush();
    spawnQueue.children[0].emitError('docker missing');
    await flush();
    assert.equal(socket.lastOfType('error').code, 'stream_failed');
    gateway.close();
  });

  it('reports log_end when the child exits', async () => {
    const { gateway, tickets, spawnQueue } = makeGateway();
    const socket = await connectAuthed(gateway, tickets);
    socket.receive({ type: 'subscribe', appId: 'app-1' });
    await flush();
    spawnQueue.children[0].emitClose(0);
    await flush();
    assert.equal(socket.lastOfType('log_end').appId, 'app-1');
    gateway.close();
  });

  it('sends no_container when the app has no container', async () => {
    const { gateway, tickets } = makeGateway({ resolveContainerId: () => null });
    const socket = await connectAuthed(gateway, tickets);
    socket.receive({ type: 'subscribe', appId: 'app-1' });
    await flush();
    assert.equal(socket.lastOfType('error').code, 'no_container');
    gateway.close();
  });

  it('tolerates a container resolver that throws', async () => {
    const { gateway, tickets } = makeGateway({
      resolveContainerId: () => {
        throw new Error('db down');
      },
    });
    const socket = await connectAuthed(gateway, tickets);
    socket.receive({ type: 'subscribe', appId: 'app-1' });
    await flush();
    assert.equal(socket.lastOfType('error').code, 'no_container');
    gateway.close();
  });

  it('surfaces stderr chunks as log frames', async () => {
    const { gateway, tickets, spawnQueue } = makeGateway();
    const socket = await connectAuthed(gateway, tickets);
    socket.receive({ type: 'subscribe', appId: 'app-1' });
    await flush();
    spawnQueue.children[0].emitStderr('warn: x');
    assert.equal(socket.lastOfType('log').data, 'warn: x');
    gateway.close();
  });
});

describe('gateway metrics streams', () => {
  it('polls docker stats and forwards parsed metrics', async () => {
    const { gateway, tickets, spawnQueue } = makeGateway({}, {});
    const socket = await connectAuthed(gateway, tickets);
    socket.receive({ type: 'subscribe:metrics', appId: 'app-1' });
    await flush();
    assert.equal(socket.lastOfType('subscribed').channel, 'metrics');
    const spawned = await waitFor(() => spawnQueue.calls.length > 0, 2000);
    assert.equal(spawned, true);
    assert.deepEqual(spawnQueue.calls[0], {
      command: 'docker',
      args: ['stats', 'container-app-1', '--no-stream', '--format', '{{json .}}'],
    });
    spawnQueue.children[0].emitStdout('{"cpu":"1.5%"}');
    spawnQueue.children[0].emitClose(0);
    const frame = await waitFor(() => socket.lastOfType('metrics') !== undefined, 2000);
    assert.equal(frame, true);
    assert.deepEqual(socket.lastOfType('metrics').data, { cpu: '1.5%' });
    gateway.close();
  });

  it('stops the poll loop on unsubscribe', async () => {
    const { gateway, tickets, spawnQueue } = makeGateway();
    const socket = await connectAuthed(gateway, tickets);
    socket.receive({ type: 'subscribe:metrics', appId: 'app-1' });
    await flush();
    await waitFor(() => spawnQueue.calls.length > 0, 2000);
    socket.receive({ type: 'unsubscribe:metrics', appId: 'app-1' });
    await flush();
    assert.equal(socket.lastOfType('unsubscribed').channel, 'metrics');
    const countAfterUnsubscribe = spawnQueue.calls.length;
    await new Promise((resolve) => setTimeout(resolve, 60));
    assert.equal(spawnQueue.calls.length, countAfterUnsubscribe);
    gateway.close();
  });

  it('emits stream_failed after repeated poll failures', async () => {
    const { gateway, tickets, spawnQueue } = makeGateway();
    const socket = await connectAuthed(gateway, tickets);
    socket.receive({ type: 'subscribe:metrics', appId: 'app-1' });
    await flush();
    for (let i = 0; i < 3; i += 1) {
      const spawned = await waitFor(() => spawnQueue.calls.length > i, 2000);
      assert.equal(spawned, true);
      spawnQueue.children[i].emitError('stats failed');
    }
    const failed = await waitFor(() => socket.lastOfType('error')?.code === 'stream_failed', 2000);
    assert.equal(failed, true);
    gateway.close();
  });

  it('treats unparseable stats output as a failure', async () => {
    const { gateway, tickets, spawnQueue } = makeGateway();
    const socket = await connectAuthed(gateway, tickets);
    socket.receive({ type: 'subscribe:metrics', appId: 'app-1' });
    await flush();
    for (let i = 0; i < 3; i += 1) {
      await waitFor(() => spawnQueue.calls.length > i, 2000);
      spawnQueue.children[i].emitStdout('still not json');
      spawnQueue.children[i].emitClose(0);
    }
    const failed = await waitFor(() => socket.lastOfType('error')?.code === 'stream_failed', 2000);
    assert.equal(failed, true);
    gateway.close();
  });

  it('shares the per-connection message budget across subscribe types', async () => {
    const { gateway, tickets } = makeGateway(
      {},
      { maxMessagesPerMinute: 10, maxSubscribesPerMinute: 30, maxRateStrikes: 100, maxViolations: 1000 },
    );
    const socket = await connectAuthed(gateway, tickets);
    for (let i = 0; i < 11; i += 1) {
      socket.receive({ type: 'subscribe:metrics', appId: `app-${i}` });
      await flush();
    }
    const limited = await waitFor(() => socket.lastOfType('error')?.code === 'rate_limited', 2000);
    assert.equal(limited, true);
    assert.equal(socket.lastOfType('error').scope, 'messages');
    gateway.close();
  });
});

describe('gateway exec and terminal', () => {
  it('runs exec after authorization and replies with exec_result', async () => {
    const execCalls: Array<{ containerId: string; command: string }> = [];
    const { gateway, tickets } = makeGateway({
      execCommand: async (containerId, command) => {
        execCalls.push({ containerId, command });
        return { ok: true, output: 'pong\n', exitCode: 0 };
      },
    });
    const socket = await connectAuthed(gateway, tickets);
    socket.receive({ type: 'exec', appId: 'app-1', command: 'echo pong' });
    await flush();
    const result = await waitFor(() => socket.lastOfType('exec_result') !== undefined, 2000);
    assert.equal(result, true);
    assert.deepEqual(execCalls, [{ containerId: 'container-app-1', command: 'echo pong' }]);
    assert.equal(socket.lastOfType('exec_result').ok, true);
    assert.equal(socket.lastOfType('exec_result').output, 'pong\n');
    gateway.close();
  });

  it('refuses exec when the resolver denies terminal:exec', async () => {
    let executed = false;
    const { gateway, tickets } = makeGateway({
      resolveAppAccess: () => false,
      execCommand: async () => {
        executed = true;
        return { ok: true, output: '' };
      },
    });
    const socket = await connectAuthed(gateway, tickets);
    socket.receive({ type: 'exec', appId: 'app-1', command: 'id' });
    await flush();
    assert.equal(socket.lastOfType('error').action, 'terminal:exec');
    assert.equal(executed, false);
    gateway.close();
  });

  it('rejects empty and oversized commands as violations', async () => {
    const { gateway, tickets } = makeGateway();
    const socket = await connectAuthed(gateway, tickets);
    socket.receive({ type: 'exec', appId: 'app-1', command: '   ' });
    await flush();
    assert.equal(socket.lastOfType('error').code, 'bad_message');
    socket.receive({ type: 'exec', appId: 'app-1', command: 'x'.repeat(2001) });
    await flush();
    assert.equal(socket.lastOfType('error').code, 'bad_message');
    gateway.close();
  });

  it('reports no_container for exec without a container', async () => {
    const { gateway, tickets } = makeGateway({ resolveContainerId: () => null });
    const socket = await connectAuthed(gateway, tickets);
    socket.receive({ type: 'exec', appId: 'app-1', command: 'id' });
    await flush();
    assert.equal(socket.lastOfType('error').code, 'no_container');
    gateway.close();
  });
});

describe('gateway collaborative rooms', () => {
  async function joinRoom(gateway: ReturnType<typeof createWsGateway>, tickets: TicketService, appId = 'app-1', roomId = 'room-1') {
    const socket = await connectAuthed(gateway, tickets);
    socket.receive({ type: 'join', appId, roomId, displayName: 'Ada' });
    await flush();
    return socket;
  }

  it('sends history and user-joined on join', async () => {
    const { gateway, tickets } = makeGateway();
    const a = await joinRoom(gateway, tickets);
    assert.deepEqual(a.lastOfType('history').lines, []);
    assert.equal(a.lastOfType('user-joined').displayName, 'Ada');
    assert.equal(gateway.stats().rooms, 1);
    gateway.close();
  });

  it('relays terminal-input to every room member including the sender', async () => {
    const { gateway, tickets } = makeGateway();
    const a = await joinRoom(gateway, tickets);
    const b = await connectAuthed(gateway, tickets);
    b.receive({ type: 'join', appId: 'app-1', roomId: 'room-1', displayName: 'Grace' });
    await flush();
    a.receive({ type: 'terminal-input', appId: 'app-1', roomId: 'room-1', text: 'ls' });
    await flush();
    assert.equal(a.lastOfType('terminal-output').line, '[Ada] $ ls');
    assert.equal(b.lastOfType('terminal-output').line, '[Ada] $ ls');
    gateway.close();
  });

  it('buffers room history for the next joiner', async () => {
    const { gateway, tickets } = makeGateway();
    const a = await joinRoom(gateway, tickets);
    a.receive({ type: 'terminal-input', appId: 'app-1', roomId: 'room-1', text: 'uptime' });
    await flush();
    const b = await connectAuthed(gateway, tickets);
    b.receive({ type: 'join', appId: 'app-1', roomId: 'room-1' });
    await flush();
    const history = b.lastOfType('history').lines;
    assert.equal(history.length, 1);
    assert.match(history[0], /uptime/);
    gateway.close();
  });

  it('excludes the sender from cursor updates but not from chat', async () => {
    const { gateway, tickets } = makeGateway();
    const a = await joinRoom(gateway, tickets);
    const b = await connectAuthed(gateway, tickets);
    b.receive({ type: 'join', appId: 'app-1', roomId: 'room-1', displayName: 'Grace' });
    await flush();
    const aSentBefore = a.sent.length;
    a.receive({ type: 'cursor', appId: 'app-1', roomId: 'room-1', cursor: { line: 1, col: 2 } });
    await flush();
    assert.equal(a.messagesOfType('cursor-update').length, 0);
    assert.equal(b.lastOfType('cursor-update').cursor.line, 1);
    assert.ok(a.sent.length >= aSentBefore);
    a.receive({ type: 'chat', appId: 'app-1', roomId: 'room-1', text: 'hi' });
    await flush();
    assert.equal(a.lastOfType('chat-message').text, 'hi');
    assert.equal(b.lastOfType('chat-message').text, 'hi');
    gateway.close();
  });

  it('announces user-left and deletes empty rooms', async () => {
    const { gateway, tickets } = makeGateway();
    const a = await joinRoom(gateway, tickets);
    const b = await connectAuthed(gateway, tickets);
    b.receive({ type: 'join', appId: 'app-1', roomId: 'room-1', displayName: 'Grace' });
    await flush();
    b.receive({ type: 'leave', roomId: 'room-1' });
    await flush();
    assert.equal(a.lastOfType('user-left').displayName, 'Grace');
    assert.equal(gateway.stats().rooms, 1);
    a.receive({ type: 'leave', roomId: 'room-1' });
    await flush();
    assert.equal(gateway.stats().rooms, 0);
    gateway.close();
  });

  it('refuses to merge a room that belongs to another app', async () => {
    const { gateway, tickets } = makeGateway();
    await joinRoom(gateway, tickets, 'app-1', 'shared-room');
    const b = await connectAuthed(gateway, tickets);
    b.receive({ type: 'join', appId: 'app-2', roomId: 'shared-room' });
    await flush();
    assert.equal(b.lastOfType('error').code, 'app_required');
    gateway.close();
  });

  it('rejects input before joining a room', async () => {
    const { gateway, tickets } = makeGateway();
    const socket = await connectAuthed(gateway, tickets);
    socket.receive({ type: 'terminal-input', appId: 'app-1', text: 'ls' });
    await flush();
    assert.equal(socket.lastOfType('error').code, 'app_required');
    gateway.close();
  });

  it('supports several concurrent rooms with isolated history', async () => {
    const { gateway, tickets } = makeGateway();
    const a = await joinRoom(gateway, tickets, 'app-1', 'room-a');
    const b = await connectAuthed(gateway, tickets);
    b.receive({ type: 'join', appId: 'app-1', roomId: 'room-b' });
    await flush();
    a.receive({ type: 'terminal-input', appId: 'app-1', roomId: 'room-a', text: 'only-a' });
    await flush();
    assert.equal(a.messagesOfType('terminal-output').length, 1);
    assert.equal(b.messagesOfType('terminal-output').length, 0);
    assert.equal(gateway.stats().rooms, 2);
    gateway.close();
  });

  it('broadcasts exec commands into the joined room', async () => {
    const { gateway, tickets } = makeGateway({
      execCommand: async () => ({ ok: true, output: 'done', exitCode: 0 }),
    });
    const a = await joinRoom(gateway, tickets);
    const b = await connectAuthed(gateway, tickets);
    b.receive({ type: 'join', appId: 'app-1', roomId: 'room-1', displayName: 'Grace' });
    await flush();
    a.receive({ type: 'exec', appId: 'app-1', roomId: 'room-1', command: 'date' });
    await flush();
    assert.equal(b.lastOfType('terminal-output').line, '[Ada] $ date');
    gateway.close();
  });
});

describe('gateway rate limiting', () => {
  it('sends rate_limited errors and closes after strikes are exhausted', async () => {
    const { gateway, tickets } = makeGateway(
      {},
      { maxMessagesPerMinute: 5, maxRateStrikes: 2, maxViolations: 1000 },
    );
    const socket = await connectAuthed(gateway, tickets);
    for (let i = 0; i < 20 && !socket.closed; i += 1) {
      socket.receive({ type: 'whatever', n: i });
      await flush();
    }
    const limited = await waitFor(() => socket.closeCode === WS_CLOSE_CODES.RATE_LIMITED, 2000);
    assert.equal(limited, true);
    gateway.close();
  });

  it('applies a separate per-user budget to subscribe attempts', async () => {
    const { gateway, tickets } = makeGateway(
      {},
      {
        maxMessagesPerMinute: 1000,
        maxSubscribesPerMinute: 2,
        maxRateStrikes: 2,
        maxViolations: 1000,
      },
    );
    const a = await connectAuthed(gateway, tickets, { userId: 'user-sub' });
    a.receive({ type: 'subscribe', appId: 'app-1' });
    await flush();
    a.receive({ type: 'subscribe', appId: 'app-2' });
    await flush();
    a.receive({ type: 'subscribe', appId: 'app-3' });
    await flush();
    const errors = a.messagesOfType('error').filter((e) => e.code === 'rate_limited');
    assert.ok(errors.length >= 1);
    assert.equal(errors[0].scope, 'subscribe');
    gateway.close();
  });
});

describe('gateway lifecycle', () => {
  it('closes idle sessions with IDLE_TIMEOUT from sweep()', async () => {
    const { gateway, tickets, state } = makeGateway({}, { idleTimeoutMs: 60_000 });
    const socket = await connectAuthed(gateway, tickets);
    state.nowMs += 59_000;
    gateway.sweep();
    assert.equal(socket.closed, false);
    state.nowMs += 2_000;
    gateway.sweep();
    assert.equal(socket.closeCode, WS_CLOSE_CODES.IDLE_TIMEOUT);
    gateway.close();
  });

  it('pings on heartbeat ticks and terminates after a missed pong', async () => {
    const { gateway, tickets, state } = makeGateway({}, { heartbeatIntervalMs: 30_000 });
    const socket = await connectAuthed(gateway, tickets);
    gateway.heartbeatTick();
    assert.equal(socket.pings, 1);
    gateway.heartbeatTick();
    assert.equal(socket.pings, 1);
    state.nowMs += 30_000;
    gateway.heartbeatTick();
    assert.equal(socket.closeCode, WS_CLOSE_CODES.IDLE_TIMEOUT);
    assert.equal(socket.closeReason, 'heartbeat_timeout');
    gateway.close();
  });

  it('keeps a session alive through application pongs', async () => {
    const { gateway, tickets, state } = makeGateway({}, { heartbeatIntervalMs: 30_000 });
    const socket = await connectAuthed(gateway, tickets);
    gateway.heartbeatTick();
    socket.receive({ type: 'pong' });
    await flush();
    state.nowMs += 30_000;
    gateway.heartbeatTick();
    assert.equal(socket.closed, false);
    assert.equal(socket.pings, 2);
    gateway.close();
  });

  it('keeps a session alive through protocol-level pongs', async () => {
    const { gateway, tickets, state } = makeGateway({}, { heartbeatIntervalMs: 30_000 });
    const socket = await connectAuthed(gateway, tickets);
    gateway.heartbeatTick();
    socket.pong();
    state.nowMs += 30_000;
    gateway.heartbeatTick();
    assert.equal(socket.closed, false);
    gateway.close();
  });

  it('closes every session for a user on revoke-all', async () => {
    const { gateway, tickets } = makeGateway();
    const a = await connectAuthed(gateway, tickets, { userId: 'user-x' });
    const b = await connectAuthed(gateway, tickets, { userId: 'user-x' });
    const other = await connectAuthed(gateway, tickets, { userId: 'user-y' });
    const closed = gateway.closeUserSessions('user-x', 'user_revoked');
    await flush();
    assert.equal(closed, 2);
    assert.equal(a.closeCode, WS_CLOSE_CODES.TICKET_INVALID);
    assert.equal(b.closeCode, WS_CLOSE_CODES.TICKET_INVALID);
    assert.equal(other.closed, false);
    gateway.close();
  });

  it('closes only the sessions that used a revoked ticket id', async () => {
    const { gateway, tickets } = makeGateway();
    const ticketA = tickets.mint('user-1');
    const a = await connectAuthed(gateway, tickets, { ticket: ticketA.ticket });
    const b = await connectAuthed(gateway, tickets, { userId: 'user-1' });
    const closed = gateway.closeTicketSessions('user-1', ticketA.claims.jti, 'ticket_revoked');
    await flush();
    assert.equal(closed, 1);
    assert.equal(a.closeCode, WS_CLOSE_CODES.TICKET_INVALID);
    assert.equal(b.closed, false);
    gateway.close();
  });

  it('reports stats and drops every socket on close()', async () => {
    const { gateway, tickets, spawnQueue } = makeGateway();
    const socket = await connectAuthed(gateway, tickets);
    socket.receive({ type: 'subscribe', appId: 'app-1' });
    await flush();
    assert.equal(gateway.stats().connections, 1);
    assert.equal(gateway.stats().sessions, 1);
    gateway.close();
    assert.equal(spawnQueue.children[0].killed, true);
    assert.equal(gateway.stats().connections, 0);
    assert.equal(gateway.stats().sessions, 0);
  });

  it('is idempotent on close()', async () => {
    const { gateway, tickets } = makeGateway();
    await connectAuthed(gateway, tickets);
    gateway.close();
    gateway.close();
    assert.equal(gateway.stats().sessions, 0);
  });
});

describe('sanitizeDisplayName', () => {
  it('keeps printable names and truncates at 32 characters', () => {
    assert.equal(sanitizeDisplayName('Ada Lovelace'), 'Ada Lovelace');
    assert.equal(sanitizeDisplayName('x'.repeat(100)).length, 32);
  });

  it('drops control characters and falls back to Anonymous', () => {
    assert.equal(sanitizeDisplayName('ok\u0007name'), 'okname');
    assert.equal(sanitizeDisplayName(''), 'Anonymous');
    assert.equal(sanitizeDisplayName('   '), 'Anonymous');
    assert.equal(sanitizeDisplayName(null), 'Anonymous');
    assert.equal(sanitizeDisplayName(42), 'Anonymous');
  });
});
