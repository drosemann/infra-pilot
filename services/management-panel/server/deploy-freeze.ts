/**
 * Deployment freeze (idea #48 "karma-driven-deploy-freeze", sachliche Variante).
 *
 * Deployments werden blockiert, wenn mindestens eines zutrifft:
 * - ein manuell/incident-bedingtes Freeze-Fenster für die Umgebung aktiv ist,
 * - offene, unbestätigte kritische Alerts vorliegen (Policy-Schalter),
 * - das gemeldete Error Budget unter die konfigurierte Untergrenze fällt,
 * - ein gemeldetes Quality Gate fehlgeschlagen ist (Policy-Schalter).
 *
 * Die Auswertung ist rein und deterministisch (now wird übergeben), damit sie
 * unit-getestet und vom Gate wie von der UI identisch genutzt werden kann.
 * Ein Notfall-Override ist nur möglich, wenn jede aktive Begründung ihn
 * erlaubt, und wird im Aufrufer auditiert.
 */

export type FreezeEnvironment = 'development' | 'staging' | 'production' | 'all';

export interface FreezeWindow {
  id: string;
  title: string;
  reason: 'manual' | 'incident' | 'maintenance';
  environment: FreezeEnvironment;
  starts_at: string;
  ends_at: string | null;
  allow_emergency_override: boolean;
  created_by: string;
  created_at: string;
}

export interface FreezeSignals {
  /** Unbestätigte kritische Alerts (vom Server aus alert_history gezählt). */
  open_critical_alerts: number;
  /** Verbleibendes Error Budget in Prozent; null = kein SLO-Feed angebunden. */
  error_budget_remaining_percent: number | null;
  /** Anzahl fehlgeschlagener Quality-Checks; null = kein Gate-Feed angebunden. */
  failed_quality_checks: number | null;
  signals_updated_at: string | null;
}

export interface FreezePolicy {
  enabled: boolean;
  freeze_on_critical_alerts: boolean;
  /** Freeze, sobald error_budget_remaining_percent <= Wert. null = aus. */
  error_budget_floor_percent: number | null;
  freeze_on_failed_quality_gate: boolean;
  allow_emergency_override: boolean;
}

export const DEFAULT_FREEZE_POLICY: FreezePolicy = {
  enabled: true,
  freeze_on_critical_alerts: true,
  error_budget_floor_percent: 5,
  freeze_on_failed_quality_gate: true,
  allow_emergency_override: true,
};

export const EMPTY_SIGNALS: FreezeSignals = {
  open_critical_alerts: 0,
  error_budget_remaining_percent: null,
  failed_quality_checks: null,
  signals_updated_at: null,
};

export interface FreezeReason {
  kind: 'window' | 'critical_alerts' | 'error_budget' | 'quality_gate';
  message: string;
  window_id?: string;
  allow_emergency_override: boolean;
}

export interface FreezeDecision {
  frozen: boolean;
  environment: string;
  reasons: FreezeReason[];
  active_windows: FreezeWindow[];
  /** Nur true, wenn eingefroren und jede Begründung einen Override erlaubt. */
  override_allowed: boolean;
  evaluated_at: string;
}

const ENVIRONMENTS: FreezeEnvironment[] = ['development', 'staging', 'production', 'all'];
const WINDOW_REASONS = ['manual', 'incident', 'maintenance'];

export function validateFreezeWindow(input: any): string | null {
  if (!input || typeof input.title !== 'string' || input.title.trim().length < 3) {
    return 'title must be a string of at least 3 characters';
  }
  if (!WINDOW_REASONS.includes(input.reason)) return 'reason must be manual, incident or maintenance';
  if (!ENVIRONMENTS.includes(input.environment)) return 'environment must be development, staging, production or all';
  const start = new Date(input.starts_at).getTime();
  if (Number.isNaN(start)) return 'starts_at must be a valid ISO date';
  if (input.ends_at != null) {
    const end = new Date(input.ends_at).getTime();
    if (Number.isNaN(end)) return 'ends_at must be a valid ISO date or null';
    if (end <= start) return 'ends_at must be after starts_at';
  }
  if (input.allow_emergency_override !== undefined && typeof input.allow_emergency_override !== 'boolean') {
    return 'allow_emergency_override must be a boolean';
  }
  return null;
}

export function validateFreezePolicy(input: any): string | null {
  if (!input || typeof input !== 'object') return 'policy must be an object';
  for (const f of ['enabled', 'freeze_on_critical_alerts', 'freeze_on_failed_quality_gate', 'allow_emergency_override'] as const) {
    if (input[f] !== undefined && typeof input[f] !== 'boolean') return `${f} must be a boolean`;
  }
  const floor = input.error_budget_floor_percent;
  if (floor !== undefined && floor !== null && (typeof floor !== 'number' || floor < 0 || floor > 100)) {
    return 'error_budget_floor_percent must be a number 0-100 or null';
  }
  return null;
}

export function validateFreezeSignals(input: any): string | null {
  if (!input || typeof input !== 'object') return 'signals must be an object';
  const budget = input.error_budget_remaining_percent;
  if (budget !== undefined && budget !== null && (typeof budget !== 'number' || budget < 0 || budget > 100)) {
    return 'error_budget_remaining_percent must be a number 0-100 or null';
  }
  const failed = input.failed_quality_checks;
  if (failed !== undefined && failed !== null && (!Number.isInteger(failed) || failed < 0)) {
    return 'failed_quality_checks must be a non-negative integer or null';
  }
  return null;
}

export function isWindowActive(w: FreezeWindow, environment: string, now: Date): boolean {
  if (w.environment !== 'all' && w.environment !== environment) return false;
  const t = now.getTime();
  if (new Date(w.starts_at).getTime() > t) return false;
  if (w.ends_at && new Date(w.ends_at).getTime() <= t) return false;
  return true;
}

/** Reine Auswertung: Fenster + Policy + Signale → eingefroren ja/nein inkl. Gründen. */
export function evaluateDeployFreeze(
  windows: FreezeWindow[],
  policy: FreezePolicy,
  signals: FreezeSignals,
  environment: string,
  now: Date = new Date(),
): FreezeDecision {
  const active = windows.filter((w) => isWindowActive(w, environment, now));
  const reasons: FreezeReason[] = active.map((w) => ({
    kind: 'window',
    window_id: w.id,
    message: `Freeze-Fenster "${w.title}" (${w.reason}) ist aktiv`,
    allow_emergency_override: w.allow_emergency_override,
  }));

  if (policy.enabled) {
    if (policy.freeze_on_critical_alerts && signals.open_critical_alerts > 0) {
      reasons.push({
        kind: 'critical_alerts',
        message: `${signals.open_critical_alerts} offene kritische Alerts`,
        allow_emergency_override: policy.allow_emergency_override,
      });
    }
    if (
      policy.error_budget_floor_percent !== null &&
      signals.error_budget_remaining_percent !== null &&
      signals.error_budget_remaining_percent <= policy.error_budget_floor_percent
    ) {
      reasons.push({
        kind: 'error_budget',
        message: `Error Budget bei ${signals.error_budget_remaining_percent}% (Untergrenze ${policy.error_budget_floor_percent}%)`,
        allow_emergency_override: policy.allow_emergency_override,
      });
    }
    if (policy.freeze_on_failed_quality_gate && (signals.failed_quality_checks ?? 0) > 0) {
      reasons.push({
        kind: 'quality_gate',
        message: `${signals.failed_quality_checks} fehlgeschlagene Quality-Checks`,
        allow_emergency_override: policy.allow_emergency_override,
      });
    }
  }

  return {
    frozen: reasons.length > 0,
    environment,
    reasons,
    active_windows: active,
    override_allowed: reasons.length > 0 && reasons.every((r) => r.allow_emergency_override),
    evaluated_at: now.toISOString(),
  };
}
