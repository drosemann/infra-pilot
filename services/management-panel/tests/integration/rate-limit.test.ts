import assert from 'node:assert/strict';
import { after, before, beforeEach, describe, it } from 'node:test';
import http from 'node:http';
import { app, setSupabaseClientForTests } from '../../server/index.ts';

type Row = Record<string, any>;
type Db = Record<string, Row[]>;

function makeResponse(data: any, error: any = null) {
  return Promise.resolve({ data, error });
}

class QueryBuilder {
  private filters: Array<[string, any]> = [];
  private pendingInsert: Row | Row[] | null = null;
  private pendingUpdate: Row | null = null;
  private isDelete = false;

  constructor(private db: Db, private table: string) {}

  select(_columns = '*') { return this; }
  insert(row: Row | Row[]) { this.pendingInsert = row; return this; }
  update(row: Row) { this.pendingUpdate = row; return this; }
  delete() { this.isDelete = true; return this; }
  eq(column: string, value: any) { this.filters.push([column, value]); return this; }
  order(_column: string, _options?: any) { return this; }
  limit(_count: number) { return this; }
  range(_start: number, _end: number) { return this.execute(); }

  single() {
    if (this.pendingInsert) {
      const rows = Array.isArray(this.pendingInsert) ? this.pendingInsert : [this.pendingInsert];
      const inserted = rows.map((row) => this.insertRow(row));
      return makeResponse(inserted[0] ?? null);
    }
    if (this.pendingUpdate) {
      const row = this.rows().find((candidate) => this.matches(candidate));
      if (!row) return makeResponse(null, { code: 'PGRST116' });
      Object.assign(row, this.pendingUpdate);
      return makeResponse(row);
    }
    const row = this.rows().find((candidate) => this.matches(candidate));
    return row ? makeResponse(row) : makeResponse(null, { code: 'PGRST116' });
  }

  then(resolve: (value: any) => void, reject?: (reason?: any) => void) {
    return this.execute().then(resolve, reject);
  }

  private execute() {
    if (this.pendingInsert) {
      const rows = Array.isArray(this.pendingInsert) ? this.pendingInsert : [this.pendingInsert];
      return makeResponse(rows.map((row) => this.insertRow(row)));
    }
    if (this.isDelete) {
      this.db[this.table] = this.rows().filter((candidate) => !this.matches(candidate));
      return makeResponse(null);
    }
    return makeResponse(this.rows().filter((candidate) => this.matches(candidate)));
  }

  private insertRow(row: Row) {
    const next = { id: row.id ?? `${this.table}-${this.rows().length + 1}`, ...row };
    this.rows().push(next);
    return next;
  }

  private rows() { this.db[this.table] ??= []; return this.db[this.table]; }

  private matches(row: Row) {
    return this.filters.every(([column, value]) => row[column] === value);
  }
}

function makeSupabase(db: Db, users: Record<string, Row> = { token: { id: 'user-1', email: 'user@example.test' } }) {
  return {
    auth: {
      getUser: async (token: string) => ({ data: { user: users[token] ?? null }, error: users[token] ? null : { message: 'invalid' } }),
      signUp: async ({ email }: { email: string }) => ({ data: { user: { id: 'new-user', email } }, error: null }),
      signInWithPassword: async () => ({ data: { session: { access_token: 'token', refresh_token: 'refresh' } }, error: null }),
      admin: { deleteUser: async () => ({}) },
    },
    from: (table: string) => new QueryBuilder(db, table),
  } as any;
}

async function requestWithHeaders(server: http.Server, method: string, path: string, body?: any, token?: string) {
  const address = server.address();
  assert(address && typeof address === 'object');
  const response = await fetch(`http://127.0.0.1:${address.port}${path}`, {
    method,
    headers: {
      ...(body ? { 'content-type': 'application/json' } : {}),
      ...(token ? { authorization: `Bearer ${token}` } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  const text = await response.text();
  const headers: Record<string, string> = {};
  response.headers.forEach((value, key) => { headers[key] = value; });
  return { status: response.status, body: text ? JSON.parse(text) : null, headers };
}

describe('customers rate-limiting middleware', () => {
  let server: http.Server;
  let db: Db;

  before(async () => {
    server = app.listen(0);
  });

  after(async () => {
    await new Promise<void>((resolve) => server.close(() => resolve()));
  });

  beforeEach(() => {
    db = {
      setup_config: [{ id: 'setup', initialized: true, mode: 'business' }],
      docker_apps: [],
      app_logs: [],
      customers: [{ id: 'customer-1', owner_user_id: 'user-1', name: 'Acme Co', email: 'acme@example.test' }],
      user_profiles: [{ id: 'user-1', display_name: 'Test User', role: 'admin' }],
    };
    setSupabaseClientForTests(makeSupabase(db));
  });

  it('GET /api/customers emits standard RateLimit-* response headers', async () => {
    const { headers } = await requestWithHeaders(server, 'GET', '/api/customers', undefined, 'token');
    // express-rate-limit v8 standardHeaders: true (draft-6) sends RateLimit-Limit, RateLimit-Remaining, RateLimit-Reset
    assert.ok('ratelimit-limit' in headers, 'Expected RateLimit-Limit header to be present');
    assert.ok('ratelimit-remaining' in headers, 'Expected RateLimit-Remaining header to be present');
    assert.ok('ratelimit-reset' in headers, 'Expected RateLimit-Reset header to be present');
  });

  it('GET /api/customers does not emit legacy X-RateLimit-* response headers', async () => {
    const { headers } = await requestWithHeaders(server, 'GET', '/api/customers', undefined, 'token');
    assert.ok(!('x-ratelimit-limit' in headers), 'X-RateLimit-Limit must be absent (legacyHeaders: false)');
    assert.ok(!('x-ratelimit-remaining' in headers), 'X-RateLimit-Remaining must be absent (legacyHeaders: false)');
    assert.ok(!('x-ratelimit-reset' in headers), 'X-RateLimit-Reset must be absent (legacyHeaders: false)');
  });

  it('POST /api/customers emits standard RateLimit-* response headers', async () => {
    const { headers } = await requestWithHeaders(server, 'POST', '/api/customers', { name: 'New Customer', email: 'new@example.test' }, 'token');
    assert.ok('ratelimit-limit' in headers, 'Expected RateLimit-Limit header to be present');
    assert.ok('ratelimit-remaining' in headers, 'Expected RateLimit-Remaining header to be present');
    assert.ok('ratelimit-reset' in headers, 'Expected RateLimit-Reset header to be present');
  });

  it('POST /api/customers does not emit legacy X-RateLimit-* response headers', async () => {
    const { headers } = await requestWithHeaders(server, 'POST', '/api/customers', { name: 'Another Customer' }, 'token');
    assert.ok(!('x-ratelimit-limit' in headers), 'X-RateLimit-Limit must be absent (legacyHeaders: false)');
    assert.ok(!('x-ratelimit-remaining' in headers), 'X-RateLimit-Remaining must be absent (legacyHeaders: false)');
    assert.ok(!('x-ratelimit-reset' in headers), 'X-RateLimit-Reset must be absent (legacyHeaders: false)');
  });

  it('RateLimit-Limit header reflects the configured max of 60', async () => {
    const { headers } = await requestWithHeaders(server, 'GET', '/api/customers', undefined, 'token');
    assert.equal(headers['ratelimit-limit'], '60');
  });

  it('RateLimit-Remaining decrements with each request to /api/customers', async () => {
    const first = await requestWithHeaders(server, 'GET', '/api/customers', undefined, 'token');
    const second = await requestWithHeaders(server, 'GET', '/api/customers', undefined, 'token');
    const firstRemaining = parseInt(first.headers['ratelimit-remaining'], 10);
    const secondRemaining = parseInt(second.headers['ratelimit-remaining'], 10);
    assert.equal(secondRemaining, firstRemaining - 1, 'Remaining count should decrement by 1 per request');
  });

  it('non-customer routes are not subject to the customers rate limiter', async () => {
    const { headers } = await requestWithHeaders(server, 'GET', '/api/apps', undefined, 'token');
    assert.ok(!('ratelimit-limit' in headers), 'GET /api/apps must not emit RateLimit-Limit (no rate limiter on this route)');
  });

  it('GET /api/customers returns 429 after exceeding the 60-request limit', async () => {
    // Drain the remaining allowance. Each describe-block runs in its own Node.js
    // process (node --test forks per file), so the in-memory store starts fresh.
    let remaining = -1;
    // Read remaining from the first request made in this test run (prior tests
    // in this file already consumed some quota from the same IP).
    const probe = await requestWithHeaders(server, 'GET', '/api/customers', undefined, 'token');
    remaining = parseInt(probe.headers['ratelimit-remaining'], 10);

    // Fire off exactly `remaining` more requests to exhaust the quota.
    for (let i = 0; i < remaining; i++) {
      await requestWithHeaders(server, 'GET', '/api/customers', undefined, 'token');
    }

    // The very next request must be rate-limited.
    const { status } = await requestWithHeaders(server, 'GET', '/api/customers', undefined, 'token');
    assert.equal(status, 429, 'Expected 429 Too Many Requests after exhausting the rate-limit window');
  });

  it('POST /api/customers also returns 429 once the shared limit is exhausted', async () => {
    // At this point the rate limit window is already exhausted (previous test).
    const { status } = await requestWithHeaders(server, 'POST', '/api/customers', { name: 'X' }, 'token');
    assert.equal(status, 429, 'POST /api/customers must also be blocked after the shared limit is exhausted');
  });

  it('rate-limited 429 response includes a Retry-After header', async () => {
    // The window should still be exhausted from the earlier drain test.
    const { status, headers } = await requestWithHeaders(server, 'GET', '/api/customers', undefined, 'token');
    assert.equal(status, 429);
    assert.ok('retry-after' in headers, 'Expected Retry-After header on 429 response');
  });
});
