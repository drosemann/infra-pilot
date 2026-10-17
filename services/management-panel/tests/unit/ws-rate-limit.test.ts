import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import { WsRateLimiter } from '../../server/ws/index.ts';

/** Build a rate limiter with a controllable clock. */
function makeLimiter(overrides: Partial<ConstructorParameters<typeof WsRateLimiter>[0]> = {}) {
  const state = { nowMs: 1000 };
  const limiter = new WsRateLimiter({
    capacity: 5,
    perMinute: 60,
    maxStrikes: 3,
    clock: () => state.nowMs,
    ...overrides,
  });
  return { limiter, state };
}

describe('WsRateLimiter construction', () => {
  it('rejects non-positive capacity or perMinute', () => {
    assert.throws(() => new WsRateLimiter({ capacity: 0, perMinute: 60, maxStrikes: 1 }), /positive/);
    assert.throws(() => new WsRateLimiter({ capacity: 5, perMinute: 0, maxStrikes: 1 }), /positive/);
    assert.throws(() => new WsRateLimiter({ capacity: -1, perMinute: -1, maxStrikes: 1 }), /positive/);
  });
});

describe('WsRateLimiter.tryConsume', () => {
  it('allows up to capacity immediately (burst)', () => {
    const { limiter } = makeLimiter({ capacity: 3, perMinute: 60 });
    assert.equal(limiter.tryConsume('conn-1').allowed, true);
    assert.equal(limiter.tryConsume('conn-1').allowed, true);
    assert.equal(limiter.tryConsume('conn-1').allowed, true);
  });

  it('denies once the bucket is empty and reports a retry delay', () => {
    const { limiter } = makeLimiter({ capacity: 2, perMinute: 60 });
    limiter.tryConsume('conn-1');
    limiter.tryConsume('conn-1');
    const denied = limiter.tryConsume('conn-1');
    assert.equal(denied.allowed, false);
    assert.ok(denied.retryAfterMs > 0);
  });

  it('refills continuously as time passes', () => {
    const { limiter, state } = makeLimiter({ capacity: 2, perMinute: 60 });
    limiter.tryConsume('conn-1');
    limiter.tryConsume('conn-1');
    assert.equal(limiter.tryConsume('conn-1').allowed, false);
    // 60 tokens per minute = 1 per second.
    state.nowMs += 1100;
    assert.equal(limiter.tryConsume('conn-1').allowed, true);
  });

  it('never refills beyond capacity', () => {
    const { limiter, state } = makeLimiter({ capacity: 2, perMinute: 60 });
    limiter.tryConsume('conn-1');
    state.nowMs += 60 * 60 * 1000;
    assert.equal(limiter.tryConsume('conn-1').allowed, true);
    assert.equal(limiter.tryConsume('conn-1').allowed, true);
    assert.equal(limiter.tryConsume('conn-1').allowed, false);
  });

  it('tracks keys independently', () => {
    const { limiter } = makeLimiter({ capacity: 1, perMinute: 60 });
    assert.equal(limiter.tryConsume('conn-1').allowed, true);
    assert.equal(limiter.tryConsume('conn-1').allowed, false);
    assert.equal(limiter.tryConsume('conn-2').allowed, true);
  });

  it('computes retryAfterMs from the token deficit', () => {
    const { limiter } = makeLimiter({ capacity: 1, perMinute: 60 });
    limiter.tryConsume('conn-1');
    const denied = limiter.tryConsume('conn-1');
    // One full token at 60/min takes one second.
    assert.ok(denied.retryAfterMs >= 900 && denied.retryAfterMs <= 1100);
  });

  it('treats a backwards clock jump as no elapsed time', () => {
    const { limiter, state } = makeLimiter({ capacity: 1, perMinute: 60 });
    limiter.tryConsume('conn-1');
    state.nowMs -= 10_000;
    assert.equal(limiter.tryConsume('conn-1').allowed, false);
  });
});

describe('WsRateLimiter strikes', () => {
  it('increments a strike per denial and exposes the count', () => {
    const { limiter } = makeLimiter({ capacity: 1, perMinute: 60, maxStrikes: 3 });
    limiter.tryConsume('conn-1');
    assert.equal(limiter.strikesFor('conn-1'), 0);
    limiter.tryConsume('conn-1');
    assert.equal(limiter.strikesFor('conn-1'), 1);
    limiter.tryConsume('conn-1');
    assert.equal(limiter.strikesFor('conn-1'), 2);
    assert.equal(limiter.isExhausted('conn-1'), false);
    limiter.tryConsume('conn-1');
    assert.equal(limiter.strikesFor('conn-1'), 3);
    assert.equal(limiter.isExhausted('conn-1'), true);
  });

  it('reports zero strikes for unknown keys', () => {
    const { limiter } = makeLimiter();
    assert.equal(limiter.strikesFor('nobody'), 0);
    assert.equal(limiter.isExhausted('nobody'), false);
  });

  it('forgets buckets and strikes on demand', () => {
    const { limiter } = makeLimiter({ capacity: 1, perMinute: 60, maxStrikes: 1 });
    limiter.tryConsume('conn-1');
    limiter.tryConsume('conn-1');
    assert.equal(limiter.isExhausted('conn-1'), true);
    limiter.forget('conn-1');
    assert.equal(limiter.strikesFor('conn-1'), 0);
    assert.equal(limiter.tryConsume('conn-1').allowed, true);
  });
});

describe('WsRateLimiter.sweep', () => {
  it('drops buckets and strikes idle past the refill window', () => {
    const { limiter, state } = makeLimiter({ capacity: 2, perMinute: 60, maxStrikes: 1 });
    limiter.tryConsume('conn-1');
    limiter.tryConsume('conn-1');
    limiter.tryConsume('conn-1');
    assert.deepEqual(limiter.size(), { buckets: 1, strikes: 1 });
    // Full refill for capacity 2 at 60/min is two seconds; the sweep window
    // adds a one second grace period on top.
    state.nowMs += 3500;
    const removed = limiter.sweep();
    assert.equal(removed, 2);
    assert.deepEqual(limiter.size(), { buckets: 0, strikes: 0 });
  });

  it('keeps recently used buckets', () => {
    const { limiter, state } = makeLimiter({ capacity: 2, perMinute: 60 });
    limiter.tryConsume('conn-1');
    state.nowMs += 1000;
    limiter.tryConsume('conn-1');
    limiter.sweep();
    assert.equal(limiter.size().buckets, 1);
  });
});
