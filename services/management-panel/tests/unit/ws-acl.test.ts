import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import { AclService, normalizeAppId, WsAuditLogger, WS_AUDIT_ACTIONS } from '../../server/ws/index.ts';
import type { WsSession } from '../../server/ws/index.ts';

interface AuditCall {
  userId: string;
  action: string;
  entityType: string;
  entityId?: string;
  newValue?: unknown;
  ipAddress?: string;
}

function makeAudit() {
  const calls: AuditCall[] = [];
  const logger = new WsAuditLogger({
    log: (userId, action, entityType, entityId, _oldValue, newValue, ipAddress) => {
      calls.push({ userId, action, entityType, entityId, newValue, ipAddress });
    },
  });
  return { logger, calls };
}

function makeSession(overrides: Partial<WsSession> = {}): WsSession {
  return {
    id: 'session-1',
    userId: 'user-1',
    appScope: null,
    ticketJti: 'jti-1',
    ip: '127.0.0.1',
    createdAt: 0,
    lastActivityAt: 0,
    pingSentAt: null,
    awaitingPong: false,
    lastPongAt: 0,
    rooms: new Set<string>(),
    ...overrides,
  };
}

describe('normalizeAppId', () => {
  it('trims and accepts well-formed ids', () => {
    assert.equal(normalizeAppId('  app-1  '), 'app-1');
    assert.equal(normalizeAppId('a'), 'a');
  });

  it('rejects missing, oversized, and control-character ids', () => {
    assert.equal(normalizeAppId(undefined), null);
    assert.equal(normalizeAppId(123), null);
    assert.equal(normalizeAppId('   '), null);
    assert.equal(normalizeAppId('x'.repeat(129)), null);
    assert.equal(normalizeAppId('bad\u0007id'), null);
  });
});

describe('AclService.authorize', () => {
  it('allows when the resolver grants access and audits it', async () => {
    const { logger, calls } = makeAudit();
    const acl = new AclService({ resolveAppAccess: () => true, audit: logger });
    const decision = await acl.authorize({ session: makeSession(), appId: 'app-1', action: 'logs:read' });
    assert.equal(decision.allowed, true);
    assert.equal(calls[0].action, WS_AUDIT_ACTIONS.SUBSCRIBE_ALLOWED);
  });

  it('denies by default when the resolver refuses', async () => {
    const { logger, calls } = makeAudit();
    const acl = new AclService({ resolveAppAccess: () => false, audit: logger });
    const decision = await acl.authorize({ session: makeSession(), appId: 'app-1', action: 'logs:read' });
    assert.equal(decision.allowed, false);
    assert.equal(decision.reason, 'forbidden');
    assert.equal(calls[0].action, WS_AUDIT_ACTIONS.SUBSCRIBE_DENIED);
  });

  it('denies when there is no resolver at all', async () => {
    const { logger } = makeAudit();
    const acl = new AclService({ audit: logger });
    const decision = await acl.authorize({ session: makeSession(), appId: 'app-1', action: 'metrics:read' });
    assert.equal(decision.allowed, false);
    assert.equal(decision.reason, 'no_resolver');
  });

  it('refuses actions outside the ticket app scope', async () => {
    const { logger } = makeAudit();
    const acl = new AclService({ resolveAppAccess: () => true, audit: logger });
    const session = makeSession({ appScope: 'app-1' });
    const decision = await acl.authorize({ session, appId: 'app-2', action: 'terminal:exec' });
    assert.equal(decision.allowed, false);
    assert.equal(decision.reason, 'scope_mismatch');
  });

  it('allows actions inside the ticket app scope', async () => {
    const { logger } = makeAudit();
    const acl = new AclService({ resolveAppAccess: () => true, audit: logger });
    const session = makeSession({ appScope: 'app-1' });
    const decision = await acl.authorize({ session, appId: 'app-1', action: 'terminal:exec' });
    assert.equal(decision.allowed, true);
  });

  it('rejects invalid app ids before consulting the resolver', async () => {
    let called = false;
    const { logger } = makeAudit();
    const acl = new AclService({
      resolveAppAccess: () => {
        called = true;
        return true;
      },
      audit: logger,
    });
    const decision = await acl.authorize({ session: makeSession(), appId: '', action: 'logs:read' });
    assert.equal(decision.allowed, false);
    assert.equal(decision.reason, 'invalid_app_id');
    assert.equal(called, false);
  });

  it('treats a throwing resolver as a denial', async () => {
    const { logger } = makeAudit();
    const acl = new AclService({
      resolveAppAccess: () => {
        throw new Error('boom');
      },
      audit: logger,
    });
    const decision = await acl.authorize({ session: makeSession(), appId: 'app-1', action: 'logs:read' });
    assert.equal(decision.allowed, false);
    assert.equal(decision.reason, 'resolver_error');
  });

  it('awaits async resolvers', async () => {
    const { logger } = makeAudit();
    const acl = new AclService({
      resolveAppAccess: async (_u, appId) => appId === 'app-ok',
      audit: logger,
    });
    assert.equal((await acl.authorize({ session: makeSession(), appId: 'app-ok', action: 'metrics:read' })).allowed, true);
    assert.equal((await acl.authorize({ session: makeSession(), appId: 'app-no', action: 'metrics:read' })).allowed, false);
  });

  it('audits terminal denials distinctly from subscribe denials', async () => {
    const { logger, calls } = makeAudit();
    const acl = new AclService({ resolveAppAccess: () => false, audit: logger });
    await acl.authorize({ session: makeSession(), appId: 'app-1', action: 'terminal:write' });
    assert.equal(calls[0].action, WS_AUDIT_ACTIONS.TERMINAL_DENIED);
  });
});
