import assert from 'node:assert/strict';
import { after, before, beforeEach, describe, it } from 'node:test';
import { WebSocket } from 'ws';
import '../helpers/ws-env.ts';
import { httpServer, setSupabaseClientForTests, wsGateway } from '../../server/index.ts';
import { makeSupabase } from '../helpers/supabase-mock.ts';
import type { Db } from '../helpers/supabase-mock.ts';
import { request } from '../helpers/http-client.ts';

const USERS = {
  token: { id: 'user-1', email: 'user1@example.test' },
  'other-token': { id: 'user-2', email: 'user2@example.test' },
};

function seedDb(): Db {
  return {
    setup_config: [{ id: 'setup', initialized: true, mode: 'personal' }],
    audit_log: [],
    docker_apps: [
      { id: 'app-own', user_id: 'user-1', container_id: 'ctr-own' },
      { id: 'app-foreign', user_id: 'user-2', container_id: 'ctr-foreign' },
    ],
  };
}

interface SocketProbe {
  socket: WebSocket;
  messages: Array<Record<string, any>>;
  waitFor(predicate: (msg: Record<string, any>) => boolean, timeoutMs?: number): Promise<Record<string, any> | null>;
  waitForClose(timeoutMs?: number): Promise<number>;
  send(message: unknown): void;
}

function port(): number {
  const address = httpServer.address();
  assert(address && typeof address === 'object');
  return address.port;
}

/** Open a WebSocket against the live gateway and collect parsed frames. */
function openSocket(path: string): SocketProbe {
  const socket = new WebSocket(`ws://127.0.0.1:${port()}${path}`);
  const messages: Array<Record<string, any>> = [];
  let closeCode: number | null = null;
  socket.on('message', (data: Buffer) => {
    try {
      messages.push(JSON.parse(data.toString('utf8')));
    } catch {
      messages.push({ type: 'unparseable' });
    }
  });
  socket.on('close', (code: number) => {
    closeCode = code;
  });
  socket.on('error', () => {});
  return {
    socket,
    messages,
    async waitFor(predicate, timeoutMs = 3000) {
      const deadline = Date.now() + timeoutMs;
      for (;;) {
        const found = messages.find(predicate);
        if (found) return found;
        if (Date.now() > deadline) return null;
        if (closeCode !== null) return messages.find(predicate) ?? null;
        await new Promise((resolve) => setTimeout(resolve, 20));
      }
    },
    async waitForClose(timeoutMs = 3000) {
      const deadline = Date.now() + timeoutMs;
      while (closeCode === null && Date.now() < deadline) {
        await new Promise((resolve) => setTimeout(resolve, 20));
      }
      assert.notEqual(closeCode, null, 'socket did not close in time');
      return closeCode as number;
    },
    send(message: unknown) {
      socket.send(JSON.stringify(message));
    },
  };
}

/** Mint a ticket through the authenticated HTTP route. */
async function mintTicket(token = 'token', body: Record<string, unknown> = {}) {
  const res = await request(httpServer, 'POST', '/api/ws-token', body, token);
  assert.equal(res.status, 200);
  return res.body.ticket as string;
}

/** Wait until earlier tests' sockets have fully cleaned up server-side. */
async function settleSessions(): Promise<void> {
  const deadline = Date.now() + 2000;
  while (wsGateway.stats().sessions > 0 && Date.now() < deadline) {
    await new Promise((resolve) => setTimeout(resolve, 20));
  }
  assert.equal(wsGateway.stats().sessions, 0, 'sessions from a previous test leaked');
}

describe('authenticated WebSocket gateway (integration)', () => {
  before(async () => {
    await new Promise<void>((resolve) => {
      if (httpServer.listening) {
        resolve();
        return;
      }
      httpServer.listen(0, () => resolve());
    });
  });

  after(async () => {
    await settleSessions();
    await new Promise<void>((resolve) => httpServer.close(() => resolve()));
  });

  beforeEach(async () => {
    setSupabaseClientForTests(makeSupabase(seedDb(), USERS));
    await settleSessions();
  });

  it('completes the query-string ticket handshake and sends ready', async () => {
    const ticket = await mintTicket();
    const probe = openSocket(`/?ticket=${encodeURIComponent(ticket)}`);
    const ready = await probe.waitFor((m) => m.type === 'ready');
    assert.ok(ready, 'expected a ready frame');
    assert.equal(ready.userId, 'user-1');
    assert.equal(ready.mode, 'viewer');
    probe.socket.close();
  });

  it('challenges ticketless sockets and accepts an auth message', async () => {
    const ticket = await mintTicket();
    const probe = openSocket('/');
    const challenge = await probe.waitFor((m) => m.type === 'auth_challenge');
    assert.ok(challenge, 'expected an auth_challenge frame');
    assert.equal(typeof challenge.authTimeoutMs, 'number');
    probe.send({ type: 'auth', ticket });
    const ready = await probe.waitFor((m) => m.type === 'ready');
    assert.ok(ready, 'expected ready after auth');
    probe.socket.close();
  });

  it('closes with 4002 when no ticket arrives before the timeout', async () => {
    const probe = openSocket('/');
    await probe.waitFor((m) => m.type === 'auth_challenge');
    assert.equal(await probe.waitForClose(3000), 4002);
  });

  it('closes with 4001 on an invalid ticket', async () => {
    const probe = openSocket('/?ticket=not-a-real-ticket');
    assert.equal(await probe.waitForClose(3000), 4001);
  });

  it('closes with 4003 when a ticket is replayed', async () => {
    const ticket = await mintTicket();
    const first = openSocket(`/?ticket=${encodeURIComponent(ticket)}`);
    assert.ok(await first.waitFor((m) => m.type === 'ready'));
    first.socket.close();
    const second = openSocket(`/?ticket=${encodeURIComponent(ticket)}`);
    assert.equal(await second.waitForClose(3000), 4003);
  });

  it('closes a scoped ticket that requests a different app', async () => {
    const ticket = await mintTicket('token', { appId: 'app-own' });
    const probe = openSocket(`/?ticket=${encodeURIComponent(ticket)}&appId=app-foreign`);
    assert.equal(await probe.waitForClose(3000), 4004);
  });

  it('closes frames larger than the payload limit with 1009', async () => {
    const ticket = await mintTicket();
    const probe = openSocket(`/?ticket=${encodeURIComponent(ticket)}`);
    assert.ok(await probe.waitFor((m) => m.type === 'ready'));
    probe.socket.send(JSON.stringify({ type: 'chat', text: 'x'.repeat(200_000) }));
    assert.equal(await probe.waitForClose(3000), 1009);
  });

  it('allows a log subscription for an owned app', async () => {
    const ticket = await mintTicket();
    const probe = openSocket(`/?ticket=${encodeURIComponent(ticket)}`);
    assert.ok(await probe.waitFor((m) => m.type === 'ready'));
    probe.send({ type: 'subscribe', appId: 'app-own' });
    const subscribed = await probe.waitFor((m) => m.type === 'subscribed' && m.channel === 'logs');
    assert.ok(subscribed, 'expected subscribe to pass the ACL');
    probe.socket.close();
  });

  it('denies a log subscription for a foreign app', async () => {
    const ticket = await mintTicket();
    const probe = openSocket(`/?ticket=${encodeURIComponent(ticket)}`);
    assert.ok(await probe.waitFor((m) => m.type === 'ready'));
    probe.send({ type: 'subscribe', appId: 'app-foreign' });
    const denied = await probe.waitFor((m) => m.type === 'error' && m.code === 'not_authorized');
    assert.ok(denied, 'expected an ACL denial');
    assert.equal(denied.appId, 'app-foreign');
    assert.equal(denied.action, 'logs:read');
    probe.socket.close();
  });

  it('denies a metrics subscription for a foreign app', async () => {
    const ticket = await mintTicket();
    const probe = openSocket(`/?ticket=${encodeURIComponent(ticket)}`);
    assert.ok(await probe.waitFor((m) => m.type === 'ready'));
    probe.send({ type: 'subscribe:metrics', appId: 'app-foreign' });
    const denied = await probe.waitFor((m) => m.type === 'error' && m.code === 'not_authorized');
    assert.ok(denied);
    assert.equal(denied.action, 'metrics:read');
    probe.socket.close();
  });

  it('scopes a scoped ticket to its app', async () => {
    const ticket = await mintTicket('token', { appId: 'app-own' });
    const probe = openSocket(`/?ticket=${encodeURIComponent(ticket)}&appId=app-own`);
    const ready = await probe.waitFor((m) => m.type === 'ready');
    assert.ok(ready);
    assert.equal(ready.appScope, 'app-own');
    probe.send({ type: 'subscribe', appId: 'app-foreign' });
    const denied = await probe.waitFor((m) => m.type === 'error' && m.code === 'not_authorized');
    assert.ok(denied, 'scoped ticket must not reach other apps');
    probe.socket.close();
  });

  it('returns exec_result for an authorized exec (docker may be absent)', async () => {
    const ticket = await mintTicket();
    const probe = openSocket(`/?ticket=${encodeURIComponent(ticket)}`);
    assert.ok(await probe.waitFor((m) => m.type === 'ready'));
    probe.send({ type: 'exec', appId: 'app-own', command: 'echo integration' });
    const result = await probe.waitFor((m) => m.type === 'exec_result', 5000);
    assert.ok(result, 'expected an exec_result frame');
    assert.equal(result.appId, 'app-own');
    probe.socket.close();
  });

  it('rejects malformed frames without disconnecting immediately', async () => {
    const ticket = await mintTicket();
    const probe = openSocket(`/?ticket=${encodeURIComponent(ticket)}`);
    assert.ok(await probe.waitFor((m) => m.type === 'ready'));
    probe.socket.send('this is not json');
    const err = await probe.waitFor((m) => m.type === 'error' && m.code === 'bad_message');
    assert.ok(err);
    assert.equal(probe.socket.readyState, WebSocket.OPEN);
    probe.socket.close();
  });

  it('closes live sessions when all tickets are revoked', async () => {
    const ticket = await mintTicket();
    const probe = openSocket(`/?ticket=${encodeURIComponent(ticket)}`);
    assert.ok(await probe.waitFor((m) => m.type === 'ready'));
    const res = await request(httpServer, 'POST', '/api/ws-token/revoke', { all: true }, 'token');
    assert.equal(res.status, 200);
    assert.equal(res.body.sessionsClosed, 1);
    assert.equal(await probe.waitForClose(3000), 4003);
  });

  it('closes only the matching sessions when a single ticket is revoked', async () => {
    const revokedTicket = await mintTicket();
    const keptTicket = await mintTicket();
    const revoked = openSocket(`/?ticket=${encodeURIComponent(revokedTicket)}`);
    const kept = openSocket(`/?ticket=${encodeURIComponent(keptTicket)}`);
    assert.ok(await revoked.waitFor((m) => m.type === 'ready'));
    assert.ok(await kept.waitFor((m) => m.type === 'ready'));
    const res = await request(httpServer, 'POST', '/api/ws-token/revoke', { ticket: revokedTicket }, 'token');
    assert.equal(res.body.sessionsClosed, 1);
    assert.equal(await revoked.waitForClose(3000), 4003);
    assert.equal(kept.socket.readyState, WebSocket.OPEN);
    kept.socket.close();
  });

  it('enforces the per-user session cap by closing the oldest socket', async () => {
    const sockets: SocketProbe[] = [];
    for (let i = 0; i < 11; i += 1) {
      const ticket = await mintTicket();
      const probe = openSocket(`/?ticket=${encodeURIComponent(ticket)}`);
      sockets.push(probe);
      assert.ok(await probe.waitFor((m) => m.type === 'ready'), `socket ${i} should be ready`);
    }
    assert.equal(await sockets[0].waitForClose(3000), 4014);
    for (const probe of sockets.slice(1)) {
      probe.socket.close();
    }
    await Promise.all(sockets.slice(1).map((probe) => probe.waitForClose(3000)));
  });
});
