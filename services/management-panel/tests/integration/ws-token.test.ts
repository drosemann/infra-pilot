import assert from 'node:assert/strict';
import { after, before, beforeEach, describe, it } from 'node:test';
import { WebSocket } from 'ws';
import { httpServer, setSupabaseClientForTests } from '../../server/index.ts';
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

/** Listen on an ephemeral port once per describe block. */
async function ensureListening(): Promise<void> {
  await new Promise<void>((resolve) => {
    if (httpServer.listening) {
      resolve();
      return;
    }
    httpServer.listen(0, () => resolve());
  });
}

function wsUrl(ticket: string): string {
  const address = httpServer.address();
  assert(address && typeof address === 'object');
  return `ws://127.0.0.1:${address.port}/?ticket=${encodeURIComponent(ticket)}`;
}

/** Open a socket and wait for the close code. */
function closeCodeOf(socket: WebSocket): Promise<number> {
  return new Promise((resolve) => {
    socket.on('close', (code: number) => resolve(code));
    socket.on('error', () => {});
  });
}

describe('POST /api/ws-token', () => {
  let db: Db;

  before(async () => {
    await ensureListening();
  });

  after(async () => {
    await new Promise<void>((resolve) => httpServer.close(() => resolve()));
  });

  beforeEach(() => {
    db = seedDb();
    setSupabaseClientForTests(makeSupabase(db, USERS));
  });

  it('requires authentication', async () => {
    const res = await request(httpServer, 'POST', '/api/ws-token', {});
    assert.equal(res.status, 401);
  });

  it('rejects invalid bearer tokens', async () => {
    const res = await request(httpServer, 'POST', '/api/ws-token', {}, 'not-a-real-token');
    assert.equal(res.status, 401);
  });

  it('mints an unscoped ticket for an authenticated caller', async () => {
    const res = await request(httpServer, 'POST', '/api/ws-token', {}, 'token');
    assert.equal(res.status, 200);
    assert.ok(String(res.body.ticket).startsWith('wst1.'));
    assert.equal(typeof res.body.expiresIn, 'number');
    assert.ok(res.body.expiresIn > 0);
    assert.ok(res.body.expiresIn <= 300);
    assert.equal(res.body.appScope, null);
  });

  it('records a ticket-issued audit event without ticket material', async () => {
    await request(httpServer, 'POST', '/api/ws-token', {}, 'token');
    const issued = db.audit_log!.filter((row) => row.action === 'ws:ticket:issue');
    assert.equal(issued.length, 1);
    assert.equal(issued[0].user_id, 'user-1');
    assert.ok(!JSON.stringify(issued[0]).includes('wst1.'));
  });

  it('scopes a ticket to an owned app', async () => {
    const res = await request(httpServer, 'POST', '/api/ws-token', { appId: 'app-own' }, 'token');
    assert.equal(res.status, 200);
    assert.equal(res.body.appScope, 'app-own');
  });

  it('refuses a ticket scoped to an app the caller does not own', async () => {
    const res = await request(httpServer, 'POST', '/api/ws-token', { appId: 'app-foreign' }, 'token');
    assert.equal(res.status, 403);
    const rejected = db.audit_log!.filter((row) => row.action === 'ws:ticket:reject');
    assert.equal(rejected.length, 1);
  });

  it('rejects a non-string appId', async () => {
    const res = await request(httpServer, 'POST', '/api/ws-token', { appId: 123 }, 'token');
    assert.equal(res.status, 400);
  });

  it('rejects an oversized appId', async () => {
    const res = await request(httpServer, 'POST', '/api/ws-token', { appId: 'a'.repeat(200) }, 'token');
    assert.equal(res.status, 400);
  });

  it('treats a blank appId as unscoped', async () => {
    const res = await request(httpServer, 'POST', '/api/ws-token', { appId: '' }, 'token');
    assert.equal(res.status, 200);
    assert.equal(res.body.appScope, null);
  });
});

describe('POST /api/ws-token/revoke', () => {
  let db: Db;

  before(async () => {
    await ensureListening();
  });

  after(async () => {
    await new Promise<void>((resolve) => httpServer.close(() => resolve()));
  });

  beforeEach(() => {
    db = seedDb();
    setSupabaseClientForTests(makeSupabase(db, USERS));
  });

  /** Mint a ticket through the real route. */
  async function mint(token = 'token', body: Record<string, unknown> = {}) {
    const res = await request(httpServer, 'POST', '/api/ws-token', body, token);
    assert.equal(res.status, 200);
    return res.body.ticket as string;
  }

  it('requires authentication', async () => {
    const res = await request(httpServer, 'POST', '/api/ws-token/revoke', {});
    assert.equal(res.status, 401);
  });

  it('rejects an empty body', async () => {
    const res = await request(httpServer, 'POST', '/api/ws-token/revoke', {}, 'token');
    assert.equal(res.status, 400);
  });

  it('revokes a ticket owned by the caller', async () => {
    const ticket = await mint();
    const res = await request(httpServer, 'POST', '/api/ws-token/revoke', { ticket }, 'token');
    assert.equal(res.status, 200);
    assert.equal(res.body.revoked, true);
    assert.equal(res.body.scope, 'ticket');
    assert.equal(res.body.sessionsClosed, 0);
    const audits = db.audit_log!.filter((row) => row.action === 'ws:ticket:revoke');
    assert.equal(audits.length, 1);
    assert.ok(!JSON.stringify(audits[0]).includes('wst1.'));
  });

  it('refuses to revoke a ticket that belongs to another user', async () => {
    const ticket = await mint('token');
    const res = await request(httpServer, 'POST', '/api/ws-token/revoke', { ticket }, 'other-token');
    assert.equal(res.status, 403);
    const rejected = db.audit_log!.filter((row) => row.action === 'ws:ticket:reject');
    assert.ok(rejected.some((row) => String(row.new_value).includes('not_owner')));
  });

  it('rejects a garbage ticket', async () => {
    const res = await request(httpServer, 'POST', '/api/ws-token/revoke', { ticket: 'not-a-ticket' }, 'token');
    assert.equal(res.status, 400);
    assert.equal(res.body.reason, 'malformed');
  });

  it('revokes every ticket for the caller when all is true', async () => {
    await mint();
    await mint();
    const res = await request(httpServer, 'POST', '/api/ws-token/revoke', { all: true }, 'token');
    assert.equal(res.status, 200);
    assert.equal(res.body.scope, 'all');
  });

  it('a revoked ticket can no longer open a WebSocket', async () => {
    const ticket = await mint();
    await request(httpServer, 'POST', '/api/ws-token/revoke', { ticket }, 'token');
    const socket = new WebSocket(wsUrl(ticket));
    assert.equal(await closeCodeOf(socket), 4003);
  });
});
