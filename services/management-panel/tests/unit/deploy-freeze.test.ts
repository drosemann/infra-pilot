import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import {
  evaluateDeployFreeze,
  isWindowActive,
  validateFreezePolicy,
  validateFreezeSignals,
  validateFreezeWindow,
  DEFAULT_FREEZE_POLICY,
  EMPTY_SIGNALS,
  type FreezeSignals,
  type FreezeWindow,
} from '../../server/deploy-freeze.ts';

const NOW = new Date('2026-06-01T12:00:00.000Z');

function window(over: Partial<FreezeWindow> = {}): FreezeWindow {
  return {
    id: 'w-1',
    title: 'Change freeze',
    reason: 'manual',
    environment: 'production',
    starts_at: new Date(NOW.getTime() - 3600_000).toISOString(),
    ends_at: new Date(NOW.getTime() + 3600_000).toISOString(),
    allow_emergency_override: true,
    created_by: 'admin-1',
    created_at: NOW.toISOString(),
    ...over,
  };
}

const signals: FreezeSignals = { ...EMPTY_SIGNALS };

describe('deployment freeze evaluation', () => {
  it('is open when nothing is active', () => {
    const d = evaluateDeployFreeze([], DEFAULT_FREEZE_POLICY, signals, 'production', NOW);
    assert.equal(d.frozen, false);
    assert.deepEqual(d.reasons, []);
  });

  it('freezes on an active window and allows override', () => {
    const d = evaluateDeployFreeze([window()], DEFAULT_FREEZE_POLICY, signals, 'production', NOW);
    assert.equal(d.frozen, true);
    assert.equal(d.reasons[0].kind, 'window');
    assert.equal(d.override_allowed, true);
  });

  it('ignores windows of other environments and expired windows', () => {
    const other = window({ environment: 'staging' });
    const expired = window({ id: 'w-2', starts_at: '2026-05-01T00:00:00.000Z', ends_at: '2026-05-02T00:00:00.000Z' });
    const d = evaluateDeployFreeze([other, expired], DEFAULT_FREEZE_POLICY, signals, 'production', NOW);
    assert.equal(d.frozen, false);
  });

  it('an "all" window freezes every environment', () => {
    const d = evaluateDeployFreeze([window({ environment: 'all' })], DEFAULT_FREEZE_POLICY, signals, 'staging', NOW);
    assert.equal(d.frozen, true);
  });

  it('a window without override denies the emergency path', () => {
    const d = evaluateDeployFreeze(
      [window({ allow_emergency_override: false })],
      DEFAULT_FREEZE_POLICY,
      signals,
      'production',
      NOW,
    );
    assert.equal(d.frozen, true);
    assert.equal(d.override_allowed, false);
  });

  it('freezes on unacknowledged critical alerts', () => {
    const d = evaluateDeployFreeze([], DEFAULT_FREEZE_POLICY, { ...signals, open_critical_alerts: 2 }, 'production', NOW);
    assert.equal(d.frozen, true);
    assert.equal(d.reasons[0].kind, 'critical_alerts');
  });

  it('freezes when the error budget hits the floor', () => {
    const d = evaluateDeployFreeze(
      [],
      DEFAULT_FREEZE_POLICY,
      { ...signals, error_budget_remaining_percent: 5 },
      'production',
      NOW,
    );
    assert.equal(d.frozen, true);
    assert.equal(d.reasons[0].kind, 'error_budget');
  });

  it('ignores missing signal feeds and a disabled policy', () => {
    const d = evaluateDeployFreeze(
      [],
      { ...DEFAULT_FREEZE_POLICY, enabled: false },
      { ...signals, open_critical_alerts: 9 },
      'production',
      NOW,
    );
    assert.equal(d.frozen, false);
  });

  it('freezes on failed quality gates', () => {
    const d = evaluateDeployFreeze(
      [],
      DEFAULT_FREEZE_POLICY,
      { ...signals, failed_quality_checks: 1 },
      'production',
      NOW,
    );
    assert.equal(d.frozen, true);
    assert.equal(d.reasons[0].kind, 'quality_gate');
  });

  it('isWindowActive respects start, end, and environment', () => {
    assert.equal(isWindowActive(window(), 'production', NOW), true);
    assert.equal(isWindowActive(window(), 'staging', NOW), false);
    assert.equal(isWindowActive(window({ starts_at: '2026-07-01T00:00:00.000Z' }), 'production', NOW), false);
  });

  it('rejects invalid windows, policies, and signals', () => {
    assert.match(validateFreezeWindow({ title: 'x' }) as string, /reason/);
    assert.match(validateFreezeWindow({ title: 'valid title', reason: 'manual', environment: 'prod', starts_at: NOW.toISOString() }) as string, /environment/);
    assert.equal(validateFreezeWindow({ title: 'valid title', reason: 'incident', environment: 'all', starts_at: NOW.toISOString() }), null);
    assert.match(validateFreezePolicy({ enabled: 'yes' }) as string, /boolean/);
    assert.match(validateFreezeSignals({ error_budget_remaining_percent: 101 }) as string, /0-100/);
    assert.equal(validateFreezeSignals({ failed_quality_checks: 0 }), null);
  });
});
