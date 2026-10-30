import assert from 'node:assert/strict';
import { after, before, beforeEach, describe, it } from 'node:test';
import { execSync } from 'node:child_process';
import fs from 'node:fs';
import http from 'node:http';
import os from 'node:os';
import path from 'node:path';
import { app, setSupabaseClientForTests } from '../../server/index.ts';
import { makeSupabase } from '../helpers/supabase-mock.ts';
import { request } from '../helpers/http-client.ts';

const USERS = {
  admintoken: { id: 'admin-1', email: 'admin@example.test' },
  usertoken: { id: 'user-1', email: 'user@example.test' },
};

const CONFIG = [
  'spec:',
  '  servers:',
  '    - name: web',
  '      type: standard',
  "    - name: 'db'",
  '      type: standard',
  '  backups: []',
  '',
].join('\n');

describe('GitOps blame API', () => {
  let server: http.Server;
  let repoDir: string = '';
  let plainDir: string = '';

  before(async () => {
    repoDir = fs.mkdtempSync(path.join(os.tmpdir(), 'git-blame-repo-'));
    execSync('git init -q', { cwd: repoDir });
    execSync('git config user.email t@example.test', { cwd: repoDir });
    execSync('git config user.name Tester', { cwd: repoDir });
    fs.writeFileSync(path.join(repoDir, 'ipilot-config.yaml'), CONFIG);
    execSync('git add .', { cwd: repoDir });
    execSync('git commit -qm init', { cwd: repoDir });

    plainDir = fs.mkdtempSync(path.join(os.tmpdir(), 'git-blame-plain-'));
    fs.writeFileSync(path.join(plainDir, 'ipilot-config.yaml'), CONFIG);

    server = app.listen(0);
  });

  after(async () => {
    delete process.env.GITOPS_REPO_DIR;
    await new Promise<void>((resolve) => server.close(() => resolve()));
    fs.rmSync(repoDir, { recursive: true, force: true });
    fs.rmSync(plainDir, { recursive: true, force: true });
  });

  beforeEach(() => {
    process.env.GITOPS_REPO_DIR = repoDir;
    const db: any = {
      user_profiles: [
        { id: 'admin-1', display_name: 'Admin', role: 'admin' },
        { id: 'user-1', display_name: 'User', role: 'user' },
      ],
    };
    setSupabaseClientForTests(makeSupabase(db, USERS));
  });

  it('GET /api/gitops/blame requires auth', async () => {
    const res = await request(server, 'GET', '/api/gitops/blame');
    assert.equal(res.status, 401);
  });

  it('annotates every server with its git author', async () => {
    const res = await request(server, 'GET', '/api/gitops/blame', undefined, 'usertoken');
    assert.equal(res.status, 200);
    assert.equal((res.body as any).file, 'ipilot-config.yaml');
    const names = ((res.body as any).annotations as any[]).map((a) => a.name);
    assert.deepEqual(names, ['web', 'db']);
    for (const annotation of (res.body as any).annotations) {
      assert.equal(annotation.lastAuthor, 'Tester');
    }
  });

  it('flags stale authorship on demand', async () => {
    const res = await request(
      server, 'GET', '/api/gitops/blame?path=ipilot-config.yaml&staleDays=0', undefined, 'usertoken',
    );
    assert.equal(res.status, 200);
    for (const annotation of (res.body as any).annotations) {
      assert.ok((annotation.risk as string[]).includes('stale'));
    }
  });

  it('rejects paths outside the repo or without yaml extension', async () => {
    const traversal = await request(server, 'GET', '/api/gitops/blame?path=../evil.yaml', undefined, 'usertoken');
    assert.equal(traversal.status, 400);
    const absolute = await request(server, 'GET', '/api/gitops/blame?path=/etc/x.yaml', undefined, 'usertoken');
    assert.equal(absolute.status, 400);
    const wrongExt = await request(server, 'GET', '/api/gitops/blame?path=notes.txt', undefined, 'usertoken');
    assert.equal(wrongExt.status, 400);
  });

  it('returns 404 for a missing config file', async () => {
    const res = await request(server, 'GET', '/api/gitops/blame?path=nope.yaml', undefined, 'usertoken');
    assert.equal(res.status, 404);
  });

  it('returns 500 when git blame fails', async () => {
    process.env.GITOPS_REPO_DIR = plainDir;
    const res = await request(server, 'GET', '/api/gitops/blame', undefined, 'usertoken');
    assert.equal(res.status, 500);
  });
});
