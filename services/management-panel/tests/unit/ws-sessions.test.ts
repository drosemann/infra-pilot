import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import { SessionRegistry } from '../../server/ws/index.ts';

function makeRegistry(overrides: Partial<ConstructorParameters<typeof SessionRegistry>[0]> = {}) {
  const state = { nowMs: 1000 };
  const registry = new SessionRegistry({
    idleTimeoutMs: 60_000,
    maxSessionsPerUser: 3,
    sessionLimitPolicy: 'kick-oldest',
    heartbeatIntervalMs: 30_000,
    clock: () => state.nowMs,
    ...overrides,
  });
  return { registry, state };
}

const DETAILS = { appScope: null, ticketJti: 'jti', ip: '127.0.0.1' };

describe('SessionRegistry.create', () => {
  it('registers a session with a unique id', () => {
    const { registry } = makeRegistry();
    const a = registry.create('user-1', DETAILS);
    const b = registry.create('user-1', DETAILS);
    assert.equal(a.ok, true);
    assert.equal(b.ok, true);
    if (a.ok && b.ok) assert.notEqual(a.session.id, b.session.id);
    assert.equal(registry.count(), 2);
    assert.equal(registry.countForUser('user-1'), 2);
  });

  it('evicts the oldest session under kick-oldest', () => {
    const { registry, state } = makeRegistry();
    registry.create('user-1', DETAILS);
    state.nowMs += 1000;
    registry.create('user-1', DETAILS);
    state.nowMs += 1000;
    registry.create('user-1', DETAILS);
    state.nowMs += 1000;
    const result = registry.create('user-1', DETAILS);
    assert.equal(result.ok, true);
    if (result.ok) {
      assert.equal(result.evicted.length, 1);
      assert.equal(result.evicted[0].createdAt, 1000);
    }
    assert.equal(registry.countForUser('user-1'), 3);
  });

  it('rejects new sessions under the reject policy', () => {
    const { registry } = makeRegistry({ sessionLimitPolicy: 'reject', maxSessionsPerUser: 1 });
    registry.create('user-1', DETAILS);
    const result = registry.create('user-1', DETAILS);
    assert.equal(result.ok, false);
    if (!result.ok) assert.equal(result.reason, 'limit');
    assert.equal(registry.countForUser('user-1'), 1);
  });

  it('tracks sessions per user independently', () => {
    const { registry } = makeRegistry({ maxSessionsPerUser: 1 });
    registry.create('user-1', DETAILS);
    const other = registry.create('user-2', DETAILS);
    assert.equal(other.ok, true);
    assert.equal(registry.countForUser('user-1'), 1);
    assert.equal(registry.countForUser('user-2'), 1);
  });
});

describe('SessionRegistry activity', () => {
  it('removes sessions and updates counts', () => {
    const { registry } = makeRegistry();
    const created = registry.create('user-1', DETAILS);
    assert.equal(created.ok, true);
    if (!created.ok) return;
    const removed = registry.remove(created.session.id);
    assert.equal(removed?.id, created.session.id);
    assert.equal(registry.remove(created.session.id), undefined);
    assert.equal(registry.count(), 0);
  });

  it('records pongs and activity', () => {
    const { registry, state } = makeRegistry();
    const created = registry.create('user-1', DETAILS);
    if (!created.ok) throw new Error('create failed');
    const { session } = created;
    state.nowMs += 5000;
    registry.touch(session.id);
    assert.equal(session.lastActivityAt, 6000);
    registry.recordPong(session.id);
    assert.equal(session.awaitingPong, false);
    assert.equal(session.lastPongAt, 6000);
  });
});

describe('SessionRegistry.heartbeatTick', () => {
  it('pings sessions once and then reports missed pongs as dead', () => {
    const { registry, state } = makeRegistry({ heartbeatIntervalMs: 30_000 });
    const created = registry.create('user-1', DETAILS);
    if (!created.ok) throw new Error('create failed');

    const first = registry.heartbeatTick();
    assert.equal(first.ping.length, 1);
    assert.equal(first.dead.length, 0);

    const early = registry.heartbeatTick();
    assert.equal(early.ping.length, 0);
    assert.equal(early.dead.length, 0);

    state.nowMs += 30_000;
    const late = registry.heartbeatTick();
    assert.equal(late.dead.length, 1);
    assert.equal(registry.count(), 0);
  });

  it('does not report a session dead after a pong arrives', () => {
    const { registry, state } = makeRegistry({ heartbeatIntervalMs: 30_000 });
    const created = registry.create('user-1', DETAILS);
    if (!created.ok) throw new Error('create failed');
    registry.heartbeatTick();
    registry.recordPong(created.session.id);
    state.nowMs += 30_000;
    const tick = registry.heartbeatTick();
    assert.equal(tick.dead.length, 0);
    assert.equal(tick.ping.length, 1);
  });
});

describe('SessionRegistry.sweepIdle', () => {
  it('removes sessions idle past the timeout', () => {
    const { registry, state } = makeRegistry({ idleTimeoutMs: 60_000 });
    const created = registry.create('user-1', DETAILS);
    if (!created.ok) throw new Error('create failed');
    state.nowMs += 59_000;
    assert.equal(registry.sweepIdle().length, 0);
    state.nowMs += 2_000;
    const idle = registry.sweepIdle();
    assert.equal(idle.length, 1);
    assert.equal(registry.count(), 0);
  });
});

describe('SessionRegistry.revokeUser', () => {
  it('returns and removes every session for the user', () => {
    const { registry } = makeRegistry();
    registry.create('user-1', DETAILS);
    registry.create('user-1', DETAILS);
    registry.create('user-2', DETAILS);
    const removed = registry.revokeUser('user-1');
    assert.equal(removed.length, 2);
    assert.equal(registry.countForUser('user-1'), 0);
    assert.equal(registry.countForUser('user-2'), 1);
  });

  it('returns an empty list for unknown users', () => {
    const { registry } = makeRegistry();
    assert.deepEqual(registry.revokeUser('nobody'), []);
  });
});
