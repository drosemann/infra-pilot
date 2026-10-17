import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import { TicketService } from '../../server/ws/index.ts';

const SECRET = 'test-secret-that-is-definitely-long-enough';

/** Build a controllable clock and a matching ticket service. */
function makeService(ttlSeconds = 300, skewSeconds = 30) {
  const state = { nowMs: 1_000_000 };
  const clock = () => state.nowMs;
  const service = new TicketService({ secret: SECRET, ttlSeconds, skewSeconds, clock });
  return { service, state };
}

describe('TicketService.mint', () => {
  it('produces a wst1 ticket with three segments', () => {
    const { service } = makeService();
    const minted = service.mint('user-1');
    assert.equal(minted.ticket.split('.').length, 3);
    assert.ok(minted.ticket.startsWith('wst1.'));
    assert.equal(minted.claims.uid, 'user-1');
    assert.equal(minted.claims.aid, undefined);
    assert.ok(minted.claims.exp > minted.claims.nbf);
  });

  it('scopes the ticket when an app id is supplied', () => {
    const { service } = makeService();
    const minted = service.mint('user-1', { appId: 'app-1' });
    assert.equal(minted.claims.aid, 'app-1');
  });

  it('rejects empty user ids and blank app scopes', () => {
    const { service } = makeService();
    assert.throws(() => service.mint(''), /without a user id/);
    assert.throws(() => service.mint('user-1', { appId: '   ' }), /non-empty string/);
  });

  it('rejects oversized app scopes', () => {
    const { service } = makeService();
    assert.throws(() => service.mint('user-1', { appId: 'x'.repeat(129) }), /at most 128/);
  });
});

describe('TicketService.verify', () => {
  it('accepts a freshly minted ticket', () => {
    const { service } = makeService();
    const minted = service.mint('user-1');
    const result = service.verify(minted.ticket);
    assert.equal(result.ok, true);
    if (result.ok) assert.equal(result.claims.uid, 'user-1');
  });

  it('is single-use (replay is rejected)', () => {
    const { service } = makeService();
    const minted = service.mint('user-1');
    assert.equal(service.verify(minted.ticket).ok, true);
    const second = service.verify(minted.ticket);
    assert.equal(second.ok, false);
    if (!second.ok) assert.equal(second.reason, 'replayed');
  });

  it('rejects malformed input', () => {
    const { service } = makeService();
    assert.equal(service.verify(undefined).ok, false);
    const empty = service.verify('');
    assert.equal(empty.ok, false);
    if (!empty.ok) assert.equal(empty.reason, 'malformed');
    const res = service.verify('not-a-ticket');
    assert.equal(res.ok, false);
    if (!res.ok) assert.equal(res.reason, 'malformed');
  });

  it('rejects a tampered signature', () => {
    const { service } = makeService();
    const minted = service.mint('user-1');
    const [version, payload] = minted.ticket.split('.');
    const forged = `${version}.${payload}.${'A'.repeat(43)}`;
    const result = service.verify(forged);
    assert.equal(result.ok, false);
    if (!result.ok) assert.ok(['bad_signature', 'malformed'].includes(result.reason));
  });

  it('rejects tickets signed with a different secret', () => {
    const { service } = makeService();
    const other = new TicketService({ secret: 'a-completely-different-secret-value' });
    const minted = other.mint('user-1');
    const result = service.verify(minted.ticket);
    assert.equal(result.ok, false);
    if (!result.ok) assert.equal(result.reason, 'bad_signature');
  });

  it('rejects expired tickets', () => {
    const { service, state } = makeService(60, 5);
    const minted = service.mint('user-1');
    state.nowMs += (60 + 6) * 1000;
    const result = service.verify(minted.ticket);
    assert.equal(result.ok, false);
    if (!result.ok) assert.equal(result.reason, 'expired');
  });

  it('rejects tickets that are not yet valid', () => {
    const { service, state } = makeService(300, 5);
    state.nowMs = 10_000_000;
    const minted = service.mint('user-1');
    state.nowMs = 9_000_000;
    const result = service.verify(minted.ticket);
    assert.equal(result.ok, false);
    if (!result.ok) assert.equal(result.reason, 'not_yet_valid');
  });

  it('respects clock skew', () => {
    const { service, state } = makeService(60, 30);
    const minted = service.mint('user-1');
    state.nowMs += (60 + 25) * 1000;
    assert.equal(service.verify(minted.ticket).ok, true);
  });
});

describe('TicketService revocation', () => {
  it('revokes a single ticket by jti', () => {
    const { service } = makeService();
    const minted = service.mint('user-1');
    service.revoke(minted.claims.jti, minted.claims.exp * 1000);
    const result = service.verify(minted.ticket);
    assert.equal(result.ok, false);
    if (!result.ok) assert.equal(result.reason, 'revoked');
  });

  it('revokes every prior ticket for a user', () => {
    const { service, state } = makeService();
    const first = service.mint('user-1');
    state.nowMs += 1000;
    service.revokeAllForUser('user-1');
    const result = service.verify(first.ticket);
    assert.equal(result.ok, false);
    if (!result.ok) assert.equal(result.reason, 'revoked');
  });

  it('still accepts tickets minted after a bulk revocation', () => {
    const { service, state } = makeService();
    state.nowMs += 10_000;
    service.revokeAllForUser('user-1');
    state.nowMs += 1000;
    const fresh = service.mint('user-1');
    assert.equal(service.verify(fresh.ticket).ok, true);
  });

  it('does not revoke other users', () => {
    const { service } = makeService();
    const other = service.mint('user-2');
    service.revokeAllForUser('user-1');
    assert.equal(service.verify(other.ticket).ok, true);
  });
});

describe('TicketService.inspect', () => {
  it('does not consume the nonce', () => {
    const { service } = makeService();
    const minted = service.mint('user-1');
    assert.equal(service.inspect(minted.ticket).ok, true);
    assert.equal(service.verify(minted.ticket).ok, true);
  });

  it('still rejects bad signatures', () => {
    const { service } = makeService();
    const result = service.inspect('wst1.YWJj.YWJj');
    assert.equal(result.ok, false);
  });
});

describe('TicketService.sweep', () => {
  it('prunes expired nonces and revocations', () => {
    const { service, state } = makeService(30, 0);
    service.mint('user-1');
    service.verify(service.mint('user-2').ticket);
    service.revokeAllForUser('user-3');
    assert.ok(service.stateSizes().nonces > 0);
    state.nowMs += 10 * 60 * 1000;
    service.sweep();
    assert.equal(service.stateSizes().nonces, 0);
    assert.equal(service.stateSizes().revokedUsers, 0);
  });

  it('enforces a minimum secret length', () => {
    assert.throws(() => new TicketService({ secret: 'tiny' }), /at least 16/);
  });
});
