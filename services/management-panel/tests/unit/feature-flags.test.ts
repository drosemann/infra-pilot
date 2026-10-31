import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import {
  evaluateFlag,
  rolloutBucket,
  validateFlagKey,
  validateRule,
  envOverride,
  type FlagDefinition,
} from '../../server/feature-flags.ts';

// Cases mirror tests/fixtures/feature-flag-contract.yaml (single source of
// truth for cross-language consistency; the Python suite loads the YAML).
function flag(key: string, status: 'active' | 'archived' = 'active'): FlagDefinition {
  return {
    key,
    description: '',
    value_type: 'boolean',
    default_value: false,
    fail_mode: 'closed',
    status,
    expires_at: null,
    rules: {},
  };
}

function withRule(f: FlagDefinition, rule: Record<string, unknown>): FlagDefinition {
  return { ...f, rules: { production: rule as any } };
}

describe('feature-flag evaluation', () => {
  it('kill switch (enabled=false) beats an allow-list', () => {
    const f = withRule(flag('discord_service_v2'), {
      environment: 'production', enabled: false, rollout_percentage: 100,
      target_org_ids: [], target_project_ids: [], target_user_ids: ['u1'], deny_user_ids: [],
    });
    assert.equal(evaluateFlag(f, 'production', { userId: 'u1' }), false);
  });

  it('deny-list beats allow-list', () => {
    const f = withRule(flag('discord_service_v2'), {
      environment: 'production', enabled: true, rollout_percentage: 0,
      target_org_ids: [], target_project_ids: [], target_user_ids: ['u1'], deny_user_ids: ['u1'],
    });
    assert.equal(evaluateFlag(f, 'production', { userId: 'u1' }), false);
  });

  it('explicit org allow beats zero rollout', () => {
    const f = withRule(flag('living_fleet'), {
      environment: 'production', enabled: true, rollout_percentage: 0,
      target_org_ids: ['org9'], target_project_ids: [], target_user_ids: [], deny_user_ids: [],
    });
    assert.equal(evaluateFlag(f, 'production', { userId: 'u2', orgId: 'org9' }), true);
  });

  it('archived flag returns default', () => {
    const f = withRule(flag('living_fleet', 'archived'), {
      environment: 'production', enabled: true, rollout_percentage: 100,
      target_org_ids: [], target_project_ids: [], target_user_ids: [], deny_user_ids: [],
    });
    assert.equal(evaluateFlag(f, 'production', { userId: 'anyone' }), false);
  });

  it('full rollout is on for an unknown subject', () => {
    const f = withRule(flag('living_fleet'), {
      environment: 'production', enabled: true, rollout_percentage: 100,
      target_org_ids: [], target_project_ids: [], target_user_ids: [], deny_user_ids: [],
    });
    assert.equal(evaluateFlag(f, 'production', { userId: 'random-user-42' }), true);
  });

  it('zero rollout is off without an allow-list', () => {
    const f = withRule(flag('living_fleet'), {
      environment: 'production', enabled: true, rollout_percentage: 0,
      target_org_ids: [], target_project_ids: [], target_user_ids: [], deny_user_ids: [],
    });
    assert.equal(evaluateFlag(f, 'production', { userId: 'random-user-42' }), false);
  });

  it('missing environment rule falls back to default', () => {
    assert.equal(evaluateFlag(flag('living_fleet'), 'production', { userId: 'u1' }), false);
  });

  it('bucket is stable and bounded', () => {
    const b = rolloutBucket('living_fleet', 'u1');
    assert.equal(b, rolloutBucket('living_fleet', 'u1'));
    assert.ok(b >= 0 && b < 100);
  });
});

describe('feature-flag validation', () => {
  it('rejects bad slugs', () => {
    assert.equal(validateFlagKey('living_fleet'), true);
    assert.equal(validateFlagKey('Bad Key!'), false);
    assert.equal(validateFlagKey(''), false);
  });

  it('rejects out-of-range rollout', () => {
    assert.equal(validateRule({ rollout_percentage: 50 }), null);
    assert.ok(typeof validateRule({ rollout_percentage: 101 }) === 'string');
    assert.ok(typeof validateRule({ rollout_percentage: -1 }) === 'string');
  });

  it('env override parses booleans', () => {
    process.env.FEATURE_FLAG_LIVING_FLEET = 'true';
    assert.equal(envOverride('living_fleet'), true);
    process.env.FEATURE_FLAG_LIVING_FLEET = 'false';
    assert.equal(envOverride('living_fleet'), false);
    delete process.env.FEATURE_FLAG_LIVING_FLEET;
    assert.equal(envOverride('living_fleet'), null);
  });
});
