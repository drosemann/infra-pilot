import crypto from 'crypto';

export type FlagEnvironment = 'development' | 'staging' | 'production';
export type FlagValueType = 'boolean' | 'variant';
export type FlagStatus = 'active' | 'archived';

export interface FlagRule {
  flag_key: string;
  environment: FlagEnvironment;
  enabled: boolean;
  rollout_percentage: number;
  target_org_ids: string[];
  target_project_ids: string[];
  target_user_ids: string[];
  deny_user_ids: string[];
}

export interface FlagDefinition {
  key: string;
  description: string;
  value_type: FlagValueType;
  default_value: boolean | string;
  variants?: string[] | null;
  fail_mode: 'closed' | 'open';
  status: FlagStatus;
  expires_at: string | null;
  rules: Partial<Record<FlagEnvironment, FlagRule>>;
}

export interface FlagSubject {
  userId?: string;
  orgId?: string;
  projectId?: string;
}

const SLUG = /^[a-z][a-z0-9_.-]{1,63}$/;

export function validateFlagKey(key: string): boolean {
  return SLUG.test(key);
}

export function validateRule(rule: Partial<FlagRule>): string | null {
  const pct = rule.rollout_percentage ?? 0;
  if (!Number.isInteger(pct) || pct < 0 || pct > 100) return 'rollout_percentage must be an integer 0-100';
  for (const f of ['target_org_ids', 'target_project_ids', 'target_user_ids', 'deny_user_ids'] as const) {
    const v = (rule as any)[f];
    if (v !== undefined && (!Array.isArray(v) || !v.every((x) => typeof x === 'string'))) return `${f} must be a string array`;
  }
  return null;
}

/** Deterministic bucket 0-99 for subject+flag so rollout is stable across services. */
export function rolloutBucket(flagKey: string, subjectId: string): number {
  const hash = crypto.createHash('sha256').update(`${flagKey}:${subjectId}`).digest();
  return hash.readUInt16BE(0) % 100;
}

/** Pure evaluation — unit-tested, mirrored by the Python client contract fixture. */
export function evaluateFlag(flag: FlagDefinition, env: FlagEnvironment, subject: FlagSubject): boolean | string {
  if (flag.status === 'archived') return flag.default_value;
  if (flag.expires_at && new Date(flag.expires_at).getTime() <= Date.now()) return flag.default_value;
  const rule = flag.rules[env];
  if (!rule || !rule.enabled) return flag.value_type === 'boolean' ? false : flag.default_value;
  const sid = subject.projectId || subject.orgId || subject.userId;
  if (subject.userId && rule.deny_user_ids.includes(subject.userId)) return false;
  if (
    (subject.userId && rule.target_user_ids.includes(subject.userId)) ||
    (subject.orgId && rule.target_org_ids.includes(subject.orgId)) ||
    (subject.projectId && rule.target_project_ids.includes(subject.projectId))
  ) return true;
  if (!sid) return false;
  return rolloutBucket(flag.key, sid) < rule.rollout_percentage;
}

/** Env-var override escape hatch: FEATURE_FLAG_<KEY>=true|false|variant. */
export function envOverride(flagKey: string): string | boolean | null {
  const raw = process.env[`FEATURE_FLAG_${flagKey.toUpperCase().replace(/[^A-Z0-9]/gi, '_')}`];
  if (raw === undefined) return null;
  const v = raw.trim().toLowerCase();
  if (v === 'true') return true;
  if (v === 'false') return false;
  return raw;
}

/** Seed registry — compiled-in defaults used before DB loads and when the panel DB is down. */
export const FLAG_REGISTRY: FlagDefinition[] = [
  {
    key: 'discord_service_v2',
    description: 'New Discord command set (v2 commands in discord-service).',
    value_type: 'boolean',
    default_value: false,
    fail_mode: 'closed',
    status: 'active',
    expires_at: null,
    rules: {},
  },
  {
    key: 'living_fleet',
    description: 'Living-fleet creature UX and orchestrator mood engine.',
    value_type: 'boolean',
    default_value: false,
    fail_mode: 'closed',
    status: 'active',
    expires_at: null,
    rules: {},
  },
];
