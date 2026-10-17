import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import { DEFAULT_WS_CONFIG, loadWsConfig, resolveWsTicketSecret } from '../../server/ws/index.ts';

describe('loadWsConfig', () => {
  it('returns documented defaults when no env vars are set', () => {
    const config = loadWsConfig({});
    assert.equal(config.ticketTtlSeconds, 300);
    assert.equal(config.ticketSkewSeconds, 30);
    assert.equal(config.authTimeoutMs, 5000);
    assert.equal(config.idleTimeoutMs, 1800 * 1000);
    assert.equal(config.heartbeatIntervalMs, 30 * 1000);
    assert.equal(config.maxSessionsPerUser, 10);
    assert.equal(config.sessionLimitPolicy, 'kick-oldest');
    assert.equal(config.maxMessagesPerMinute, 120);
    assert.equal(config.maxSubscribesPerMinute, 30);
    assert.equal(config.maxRateStrikes, 20);
    assert.equal(config.maxViolations, 5);
    assert.equal(config.maxMessageBytes, 65536);
  });

  it('matches DEFAULT_WS_CONFIG', () => {
    assert.deepEqual(loadWsConfig({}), DEFAULT_WS_CONFIG);
  });

  it('reads and converts second-based values to milliseconds', () => {
    const config = loadWsConfig({
      WS_TICKET_TTL_SECONDS: '60',
      WS_IDLE_TIMEOUT_SECONDS: '120',
      WS_HEARTBEAT_INTERVAL_SECONDS: '10',
    });
    assert.equal(config.ticketTtlSeconds, 60);
    assert.equal(config.idleTimeoutMs, 120000);
    assert.equal(config.heartbeatIntervalMs, 10000);
  });

  it('clamps the ticket TTL to the five minute maximum', () => {
    assert.equal(loadWsConfig({ WS_TICKET_TTL_SECONDS: '99999' }).ticketTtlSeconds, 300);
    assert.equal(loadWsConfig({ WS_TICKET_TTL_SECONDS: '1' }).ticketTtlSeconds, 30);
  });

  it('clamps out-of-range integers instead of failing', () => {
    const config = loadWsConfig({
      WS_MAX_MESSAGES_PER_MINUTE: '1',
      WS_MAX_VIOLATIONS: '100000',
      WS_AUTH_TIMEOUT_MS: '1000000',
    });
    assert.equal(config.maxMessagesPerMinute, 10);
    assert.equal(config.maxViolations, 100);
    assert.equal(config.authTimeoutMs, 60000);
  });

  it('rejects non-numeric values', () => {
    assert.throws(() => loadWsConfig({ WS_TICKET_TTL_SECONDS: 'soon' }), /must be an integer/);
    assert.throws(() => loadWsConfig({ WS_MAX_SESSIONS_PER_USER: 'ten' }), /must be an integer/);
  });

  it('rejects unknown session limit policies', () => {
    assert.throws(() => loadWsConfig({ WS_SESSION_LIMIT_POLICY: 'explode' }), /must be one of/);
  });

  it('accepts both supported session limit policies', () => {
    assert.equal(loadWsConfig({ WS_SESSION_LIMIT_POLICY: 'reject' }).sessionLimitPolicy, 'reject');
    assert.equal(loadWsConfig({ WS_SESSION_LIMIT_POLICY: 'kick-oldest' }).sessionLimitPolicy, 'kick-oldest');
  });

  it('ignores blank values as unset', () => {
    assert.equal(loadWsConfig({ WS_TICKET_TTL_SECONDS: '   ' }).ticketTtlSeconds, 300);
  });
});

describe('resolveWsTicketSecret', () => {
  it('returns a provided secret of sufficient length', () => {
    const secret = 'a'.repeat(48);
    assert.equal(resolveWsTicketSecret({ WS_TICKET_SECRET: secret }), secret);
  });

  it('rejects secrets shorter than 32 characters', () => {
    assert.throws(() => resolveWsTicketSecret({ WS_TICKET_SECRET: 'short' }), /at least 32/);
  });

  it('rejects obvious placeholders', () => {
    assert.throws(
      () => resolveWsTicketSecret({ WS_TICKET_SECRET: 'CHANGE_ME_CHANGE_ME_CHANGE_ME_1234' }),
      /placeholder/,
    );
  });

  it('generates an ephemeral secret when unset', () => {
    const first = resolveWsTicketSecret({});
    const second = resolveWsTicketSecret({});
    assert.equal(typeof first, 'string');
    assert.ok(first.length >= 32);
    assert.notEqual(first, second);
  });
});
