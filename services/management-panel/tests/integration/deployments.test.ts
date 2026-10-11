import assert from 'node:assert/strict';
import { after, before, beforeEach, describe, it } from 'node:test';
import http from 'node:http';
import { app, setSupabaseClientForTests } from '../../server/index.ts';
import { makeSupabase } from '../helpers/supabase-mock.ts';
import type { Db } from '../helpers/supabase-mock.ts';
import { request } from '../helpers/http-client.ts';

const USERS = {
  token: { id: 'user-1', email: 'user1@example.test' },
  'other-token': { id: 'user-2', email: 'user2@example.test' },
};

function makeDeploySupabase(db: Db) {
  const supabase: any = makeSupabase(db, USERS);
  const origFrom = supabase.from.bind(supabase);
  supabase.from = (table: string) => {
    const qb: any = origFrom(table);
    if (table === 'shared_config' && typeof qb.upsert !== 'function') {
      qb.upsert = (row: Record<string, any>) => ({
        then: (resolve: (v: any) => void, reject?: (r?: any) => void) => {
          db.shared_config ??= [];
          const idx = db.shared_config.findIndex((r) => r.key === row.key);
          if (idx >= 0) db.shared_config[idx] = { ...db.shared_config[idx], ...row };
          else db.shared_config.push({ ...row });
          return Promise.resolve({ data: row, error: null }).then(resolve, reject);
        },
      });
    }
    return qb;
  };
  return supabase;
}

describe('deployments API contract', () => {
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
      setup_config: [{ id: 'setup', initialized: true, mode: 'personal' }],
      shared_config: [],
      audit_log: [],
    };
    setSupabaseClientForTests(makeDeploySupabase(db));
  });

  it('requires auth to list deployments', async () => {
    const response = await request(server, 'GET', '/api/deployments');
    assert.equal(response.status, 401);
  });

  it('validates required fields on create', async () => {
    for (const body of [{}, { name: 'only-name' }, { repoUrl: 'https://github.com/a/b.git' }]) {
      const response = await request(server, 'POST', '/api/deployments', body, 'token');
      assert.equal(response.status, 400, `should reject ${JSON.stringify(body)}`);
    }
  });

  it('creates, lists, and isolates deployments by owner', async () => {
    const created = await request(
      server,
      'POST',
      '/api/deployments',
      { name: 'web', repoUrl: 'https://github.com/acme/web.git', branch: 'main' },
      'token',
    );
    assert.equal(created.status, 201);
    assert.equal(created.body.name, 'web');
    assert.equal(created.body.repo, 'acme/web');
    assert.equal(created.body.enabled, true);
    assert.ok(created.body.id);

    const listed = await request(server, 'GET', '/api/deployments', undefined, 'token');
    assert.equal(listed.status, 200);
    assert.equal(listed.body.length, 1);

    const other = await request(server, 'GET', '/api/deployments', undefined, 'other-token');
    assert.equal(other.status, 200);
    assert.deepEqual(other.body, []);
  });

  it('toggles, reads history, and deletes owned deployments', async () => {
    const created = await request(
      server,
      'POST',
      '/api/deployments',
      { name: 'api', repoUrl: 'https://github.com/acme/api.git' },
      'token',
    );
    const id = created.body.id as string;

    const toggled = await request(server, 'PATCH', `/api/deployments/${id}/toggle`, {}, 'token');
    assert.equal(toggled.status, 200);
    assert.equal(toggled.body.enabled, false);

    const history = await request(server, 'GET', `/api/deployments/${id}/history`, undefined, 'token');
    assert.equal(history.status, 200);
    assert.deepEqual(history.body, { history: [] });

    const otherToggle = await request(server, 'PATCH', `/api/deployments/${id}/toggle`, {}, 'other-token');
    assert.equal(otherToggle.status, 404);

    const deleted = await request(server, 'DELETE', `/api/deployments/${id}`, undefined, 'token');
    assert.equal(deleted.status, 200);

    const listed = await request(server, 'GET', '/api/deployments', undefined, 'token');
    assert.deepEqual(listed.body, []);
  });

  it('returns 404 for unknown deployment ids', async () => {
    const history = await request(server, 'GET', '/api/deployments/missing/history', undefined, 'token');
    assert.equal(history.status, 404);
    const deleted = await request(server, 'DELETE', '/api/deployments/missing', undefined, 'token');
    assert.equal(deleted.status, 404);
  });
});
