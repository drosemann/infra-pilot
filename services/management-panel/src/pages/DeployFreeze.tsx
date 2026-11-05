import { useEffect, useState } from 'react';
import { apiClient } from '../lib/api';
import { PageHeader } from '../components/PageHeader';

interface FreezeReason {
  kind: 'window' | 'critical_alerts' | 'error_budget' | 'quality_gate';
  message: string;
  window_id?: string;
  allow_emergency_override: boolean;
}

interface FreezeWindow {
  id: string;
  title: string;
  reason: 'manual' | 'incident' | 'maintenance';
  environment: string;
  starts_at: string;
  ends_at: string | null;
  allow_emergency_override: boolean;
}

interface FreezeState {
  frozen: boolean;
  environment: string;
  reasons: FreezeReason[];
  active_windows: FreezeWindow[];
  override_allowed: boolean;
  windows: FreezeWindow[];
  policy: {
    enabled: boolean;
    freeze_on_critical_alerts: boolean;
    error_budget_floor_percent: number | null;
    freeze_on_failed_quality_gate: boolean;
    allow_emergency_override: boolean;
  };
  signals: {
    open_critical_alerts: number;
    error_budget_remaining_percent: number | null;
    failed_quality_checks: number | null;
    signals_updated_at: string | null;
  };
}

const ENVIRONMENTS = ['production', 'staging', 'development'];
const api = (apiClient as any).api;

/** Admin page: deployment freeze windows, policy, and live freeze decision. */
export function DeployFreeze() {
  const [state, setState] = useState<FreezeState | null>(null);
  const [environment, setEnvironment] = useState('production');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState({ title: '', reason: 'manual', environment: 'production', ends_at: '' });

  const load = async (env = environment) => {
    try {
      const res = await api.get('/api/deploy-freeze', { params: { environment: env } });
      setState(res.data);
      setError(null);
    } catch (err: any) {
      setError(err?.response?.data?.error || 'Failed to load freeze status.');
    }
  };

  useEffect(() => {
    load(environment);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [environment]);

  const createWindow = async () => {
    if (form.title.trim().length < 3) {
      setError('Title needs at least 3 characters.');
      return;
    }
    setBusy(true);
    try {
      await api.post('/api/deploy-freeze/windows', {
        title: form.title.trim(),
        reason: form.reason,
        environment: form.environment,
        starts_at: new Date().toISOString(),
        ends_at: form.ends_at ? new Date(form.ends_at).toISOString() : null,
      });
      setForm({ title: '', reason: 'manual', environment: 'production', ends_at: '' });
      await load();
    } catch (err: any) {
      setError(err?.response?.data?.error || 'Creating the window failed.');
    } finally {
      setBusy(false);
    }
  };

  const removeWindow = async (id: string) => {
    if (!window.confirm('Freeze-Fenster wirklich aufheben?')) return;
    setBusy(true);
    try {
      await api.delete(`/api/deploy-freeze/windows/${id}`);
      await load();
    } catch (err: any) {
      setError(err?.response?.data?.error || 'Deleting the window failed.');
    } finally {
      setBusy(false);
    }
  };

  const togglePolicy = async (patch: Record<string, unknown>) => {
    setBusy(true);
    try {
      await api.put('/api/deploy-freeze/policy', patch);
      await load();
    } catch (err: any) {
      setError(err?.response?.data?.error || 'Updating the policy failed.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="mx-auto max-w-5xl space-y-8 px-2 py-8">
      <PageHeader
        eyebrow="Ship"
        actions={
          <select
            className="input-field w-auto text-sm"
            aria-label="Environment"
            value={environment}
            onChange={(e) => setEnvironment(e.target.value)}
          >
            {ENVIRONMENTS.map((e) => (
              <option key={e} value={e}>{e}</option>
            ))}
          </select>
        }
      >
        <h1 className="text-4xl font-semibold tracking-tight text-white">Deployment Freeze</h1>
        <p className="mt-2 max-w-2xl text-white/55">
          Blocks deployments during freeze windows, open critical alerts, depleted error budget
          or failed quality gates. Emergency override requires the admin role and a reason.
        </p>
      </PageHeader>

      {error && <p className="text-sm text-red-400">{error}</p>}

      {state && (
        <div className={`card p-5 ${state.frozen ? 'border-red-500/40' : 'border-emerald-500/30'}`}>
          <p className="font-semibold text-white">
            {state.frozen ? 'Frozen — deployments blocked' : 'Open — deployments allowed'}
          </p>
          {state.reasons.length > 0 && (
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-white/60">
              {state.reasons.map((r, i) => (
                <li key={i}>
                  {r.message}
                  {!r.allow_emergency_override && ' (no emergency override available)'}
                </li>
              ))}
            </ul>
          )}
          <p className="mt-3 text-xs text-white/40">
            Open critical alerts (24h): {state.signals.open_critical_alerts}
            {' · '}Error budget: {state.signals.error_budget_remaining_percent ?? '—'}%
            {' · '}Failed quality checks: {state.signals.failed_quality_checks ?? '—'}
          </p>
        </div>
      )}

      <div className="card space-y-3 p-5">
        <h2 className="text-lg font-semibold text-white">New freeze window</h2>
        <div className="flex flex-wrap gap-2">
          <input
            className="input-field min-w-52 flex-1"
            placeholder="Title (e.g. Black Friday change freeze)"
            value={form.title}
            onChange={(e) => setForm({ ...form, title: e.target.value })}
          />
          <select
            className="input-field w-auto"
            value={form.reason}
            onChange={(e) => setForm({ ...form, reason: e.target.value })}
          >
            <option value="manual">manual</option>
            <option value="incident">incident</option>
            <option value="maintenance">maintenance</option>
          </select>
          <select
            className="input-field w-auto"
            value={form.environment}
            onChange={(e) => setForm({ ...form, environment: e.target.value })}
          >
            <option value="all">all</option>
            {ENVIRONMENTS.map((e) => (
              <option key={e} value={e}>{e}</option>
            ))}
          </select>
          <input
            type="datetime-local"
            className="input-field w-auto"
            title="Ends at (empty = open-ended)"
            value={form.ends_at}
            onChange={(e) => setForm({ ...form, ends_at: e.target.value })}
          />
          <button
            className="primary-button"
            disabled={busy}
            onClick={createWindow}
          >
            Create
          </button>
        </div>
      </div>

      <div className="space-y-2">
        <h2 className="text-lg font-semibold text-white">Active and scheduled windows ({state?.windows.length ?? 0})</h2>
        {(state?.windows ?? []).map((w) => (
          <div key={w.id} className="card flex items-center justify-between p-4 text-sm">
            <div>
              <p className="font-semibold text-white">{w.title}</p>
              <p className="mt-1 text-white/45">
                {w.reason} · {w.environment} · since {new Date(w.starts_at).toLocaleString()}
                {w.ends_at ? ` · until ${new Date(w.ends_at).toLocaleString()}` : ' · open-ended'}
                {!w.allow_emergency_override && ' · no override'}
              </p>
            </div>
            <button
              className="secondary-button"
              disabled={busy}
              onClick={() => removeWindow(w.id)}
            >
              Lift
            </button>
          </div>
        ))}
      </div>

      {state && (
        <div className="card space-y-3 p-5 text-sm">
          <h2 className="text-lg font-semibold text-white">Policy</h2>
          {(
            [
              ['enabled', 'Freeze enabled'],
              ['freeze_on_critical_alerts', 'Freeze on critical alerts'],
              ['freeze_on_failed_quality_gate', 'Freeze on failed quality gates'],
              ['allow_emergency_override', 'Allow emergency override'],
            ] as const
          ).map(([key, label]) => (
            <label key={key} className="flex items-center gap-2 text-white/70">
              <input
                type="checkbox"
                checked={state.policy[key]}
                disabled={busy}
                onChange={(e) => togglePolicy({ [key]: e.target.checked })}
              />
              {label}
            </label>
          ))}
          <label className="flex items-center gap-2 text-white/70">
            Error budget floor (%)
            <input
              type="number"
              min={0}
              max={100}
              className="input-field w-20"
              defaultValue={state.policy.error_budget_floor_percent ?? 5}
              key={String(state.policy.error_budget_floor_percent)}
              onBlur={(e) => togglePolicy({ error_budget_floor_percent: Number(e.target.value) })}
            />
          </label>
        </div>
      )}
    </div>
  );
}
