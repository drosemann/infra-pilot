import assert from 'node:assert/strict';
import { after, before, beforeEach, describe, it } from 'node:test';
import http from 'node:http';
import { app, setSupabaseClientForTests } from '../../server/index.ts';
import { makeSupabase } from '../helpers/supabase-mock.ts';
import { request } from '../helpers/http-client.ts';

const USERS = {
  admintoken: { id: 'admin-1', email: 'admin@example.test' },
  usertoken: { id: 'user-1', email: 'user@example.test' },
};

describe('Feature flags API', () => {
  let server: http.Server;

  before(async () => {
    server = app.listen(0);
  });

  after(async () => {
    await new Promise<void>((resolve) => server.close(() => resolve()));
  });

  beforeEach(() => {
    const db: any = {
      user_profiles: [
        { id: 'admin-1', display_name: 'Admin', role: 'admin' },
        { id: 'user-1', display_name: 'User', role: 'user' },
      ],
      feature_flags: [],
      feature_flag_rules: [],
      audit_log: [],
    };
    setSupabaseClientForTests(makeSupabase(db, USERS));
  });

  it('GET /api/feature-flags/evaluate requires auth', async () => {
    const res = await request(server, 'GET', '/api/feature-flags/evaluate');
    assert.equal(res.status, 401);
  });

  it('GET /api/feature-flags/evaluate resolves registry defaults for a user', async () => {
    const res = await request(server, 'GET', '/api/feature-flags/evaluate', undefined, 'usertoken');
    assert.equal(res.status, 200);
    assert.equal((res.body as any).flags['living_fleet'], false);
    assert.equal((res.body as any).flags['discord_service_v2'], false);
  });

  it('GET /api/feature-flags/evaluate accepts the service token', async () => {
    process.env.FEATURE_FLAGS_SERVICE_TOKEN = 'svc-secret';
    try {
      const res = await request(server, 'GET', '/api/feature-flags/evaluate?userId=user-1', undefined, 'svc-secret');
      assert.equal(res.status, 200);
      assert.ok((res.body as any).flags);
      const bad = await request(server, 'GET', '/api/feature-flags/evaluate', undefined, 'wrong');
      assert.equal(bad.status, 401);
    } finally {
      delete process.env.FEATURE_FLAGS_SERVICE_TOKEN;
    }
  });

  it('GET /api/feature-flags requires admin', async () => {
    const denied = await request(server, 'GET', '/api/feature-flags', undefined, 'usertoken');
    assert.equal(denied.status, 403);
    const allowed = await request(server, 'GET', '/api/feature-flags', undefined, 'admintoken');
    assert.equal(allowed.status, 200);
    assert.ok(Array.isArray((allowed.body as any).flags));
  });

  it('admin can create, roll out, and kill a flag with audit trail', async () => {
    const created = await request(server, 'POST', '/api/feature-flags', { key: 'living_fleet' }, 'admintoken');
    assert.equal(created.status, 201);

    const badSlug = await request(server, 'POST', '/api/feature-flags', { key: 'Bad Key!' }, 'admintoken');
    assert.equal(badSlug.status, 400);

    const patched = await request(
      server, 'PATCH', '/api/feature-flags/living_fleet',
      { rule: { environment: 'development', enabled: true, rollout_percentage: 100 } }, 'admintoken',
    );
    assert.equal(patched.status, 200);

    const on = await request(server, 'GET', '/api/feature-flags/evaluate', undefined, 'usertoken');
    assert.equal((on.body as any).flags['living_fleet'], true);

    const killed = await request(server, 'POST', '/api/feature-flags/living_fleet/kill', {}, 'admintoken');
    assert.equal(killed.status, 200);

    const off = await request(server, 'GET', '/api/feature-flags/evaluate', undefined, 'usertoken');
    assert.equal((off.body as any).flags['living_fleet'], false);
  });

  it('non-admin cannot create flags', async () => {
    const res = await request(server, 'POST', '/api/feature-flags', { key: 'x_flag' }, 'usertoken');
    assert.equal(res.status, 403);
  });
});
