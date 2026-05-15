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

  select(_columns = '*') {
    return this;
  }

  insert(row: Row | Row[]) {
    this.pendingInsert = row;
    return this;
  }

  update(row: Row) {
    this.pendingUpdate = row;
    return this;
  }

  delete() {
    this.isDelete = true;
    return this;
  }

  eq(column: string, value: any) {
    this.filters.push([column, value]);
    return this;
  }

  order(_column: string, _options?: any) {
    return this;
  }

  limit(_count: number) {
    return this;
  }

  range(_start: number, _end: number) {
    return this.execute();
  }

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

  private rows() {
    this.db[this.table] ??= [];
    return this.db[this.table];
  }

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

async function request(server: http.Server, method: string, path: string, body?: any, token?: string) {
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
  return { status: response.status, body: text ? JSON.parse(text) : null };
}

describe('management-panel API integration contract', () => {
  let server: http.Server;
  let db: Db;

  before(async () => {
    server = app.listen(0);
  });

  after(async () => {
    await new Promise<void>((resolve) => server.close(() => resolve()));
  });

  beforeEach(() => {
    process.env.VITE_DEMO_FEATURE_ENABLED = 'true';
    db = {
      setup_config: [{ id: 'setup', initialized: true, mode: 'business' }],
      docker_apps: [
        { id: 'owned-app', user_id: 'user-1', name: 'Owned', image: 'nginx', status: 'stopped' },
        { id: 'other-app', user_id: 'user-2', name: 'Other', image: 'redis', status: 'stopped' },
      ],
      app_logs: [{ id: 'log-1', app_id: 'owned-app', message: 'started' }],
      customers: [{ id: 'customer-1', owner_user_id: 'user-1', name: 'Acme Co' }],
      user_profiles: [{ id: 'user-1', display_name: 'Test User', role: 'admin' }],
    };
    setSupabaseClientForTests(makeSupabase(db));
  });

  it('rejects authenticated endpoints without a bearer token', async () => {
    const response = await request(server, 'GET', '/api/apps');
    assert.equal(response.status, 401);
  });

  it('filters apps by the authenticated owner', async () => {
    const response = await request(server, 'GET', '/api/apps', undefined, 'token');
    assert.equal(response.status, 200);
    assert.deepEqual(response.body.map((app: Row) => app.id), ['owned-app']);
  });

  it('blocks business endpoints while in personal mode', async () => {
    db.setup_config[0].mode = 'personal';
    const response = await request(server, 'GET', '/api/customers', undefined, 'token');
    assert.equal(response.status, 403);
  });

  it('validates setup initialization payloads', async () => {
    const response = await request(server, 'POST', '/api/setup/init', { email: 'admin@example.test', password: 'secret', mode: 'invalid' });
    assert.equal(response.status, 400);
  });

  it('reports the demo feature flag from the environment', async () => {
    process.env.VITE_DEMO_FEATURE_ENABLED = 'false';
    const response = await request(server, 'GET', '/api/demo/flag');
    assert.equal(response.status, 200);
    assert.deepEqual(response.body, { enabled: false });
  });

  it('keeps demo seeding idempotent per owner and app name', async () => {
    let response = await request(server, 'POST', '/api/seed-demo', undefined, 'token');
    assert.equal(response.status, 200);
    assert.equal(response.body.appsSeeded, 2);

    response = await request(server, 'POST', '/api/seed-demo', undefined, 'token');
    assert.equal(response.status, 200);
    assert.equal(response.body.appsSeeded, 0);

    const demoAppsForUser = db.docker_apps.filter((row) => row.user_id === 'user-1' && ['demo-app', 'monitor'].includes(row.name));
    assert.equal(demoAppsForUser.length, 2);
  });
});
