import { useEffect, useState } from 'react';
import { apiClient } from '../lib/api';

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
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Deployment Freeze</h1>
          <p className="text-sm opacity-70">
            Blockiert Deployments bei Freeze-Fenstern, offenen kritischen Alerts, aufgebrauchtem Error Budget
            oder fehlgeschlagenen Quality-Gates. Notfall-Override nur mit Admin-Rolle und Begründung.
          </p>
        </div>
        <select
          className="border rounded px-2 py-1 bg-transparent"
          value={environment}
          onChange={(e) => setEnvironment(e.target.value)}
        >
          {ENVIRONMENTS.map((e) => (
            <option key={e} value={e}>{e}</option>
          ))}
        </select>
      </div>

      {error && <p className="text-red-500">{error}</p>}

      {state && (
        <div className={`border rounded p-4 ${state.frozen ? 'border-red-500' : 'border-green-600'}`}>
          <p className="font-bold">{state.frozen ? 'EINGEFROREN — Deployments blockiert (423)' : 'Offen — Deployments möglich'}</p>
          {state.reasons.length > 0 && (
            <ul className="list-disc ml-5 mt-2 text-sm">
              {state.reasons.map((r, i) => (
                <li key={i}>
                  {r.message}
                  {!r.allow_emergency_override && ' (kein Notfall-Override möglich)'}
                </li>
              ))}
            </ul>
          )}
          <p className="text-xs opacity-70 mt-2">
            Offene kritische Alerts (24h): {state.signals.open_critical_alerts}
            {' · '}Error Budget: {state.signals.error_budget_remaining_percent ?? '—'}%
            {' · '}Quality-Checks fehlgeschlagen: {state.signals.failed_quality_checks ?? '—'}
          </p>
        </div>
      )}

      <div className="border rounded p-4 space-y-3">
        <h2 className="font-bold">Neues Freeze-Fenster</h2>
        <div className="flex flex-wrap gap-2">
          <input
            className="border rounded px-2 py-1 bg-transparent min-w-52"
            placeholder="Titel (z. B. Change-Freeze Black Friday)"
            value={form.title}
            onChange={(e) => setForm({ ...form, title: e.target.value })}
          />
          <select
            className="border rounded px-2 py-1 bg-transparent"
            value={form.reason}
            onChange={(e) => setForm({ ...form, reason: e.target.value })}
          >
            <option value="manual">manual</option>
            <option value="incident">incident</option>
            <option value="maintenance">maintenance</option>
          </select>
          <select
            className="border rounded px-2 py-1 bg-transparent"
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
            className="border rounded px-2 py-1 bg-transparent"
            title="Ende (leer = offen)"
            value={form.ends_at}
            onChange={(e) => setForm({ ...form, ends_at: e.target.value })}
          />
          <button
            className="px-3 py-1 rounded bg-blue-600 text-white disabled:opacity-50"
            disabled={busy}
            onClick={createWindow}
          >
            Anlegen
          </button>
        </div>
      </div>

      <div className="space-y-2">
        <h2 className="font-bold">Aktive und geplante Fenster ({state?.windows.length ?? 0})</h2>
        {(state?.windows ?? []).map((w) => (
          <div key={w.id} className="border rounded p-3 flex items-center justify-between text-sm">
            <div>
              <code className="font-mono font-bold">{w.title}</code>
              <p className="opacity-70">
                {w.reason} · {w.environment} · seit {new Date(w.starts_at).toLocaleString()}
                {w.ends_at ? ` · bis ${new Date(w.ends_at).toLocaleString()}` : ' · ohne Ende'}
                {!w.allow_emergency_override && ' · kein Override'}
              </p>
            </div>
            <button
              className="px-3 py-1 rounded bg-red-600 text-white disabled:opacity-50"
              disabled={busy}
              onClick={() => removeWindow(w.id)}
            >
              Aufheben
            </button>
          </div>
        ))}
      </div>

      {state && (
        <div className="border rounded p-4 space-y-2 text-sm">
          <h2 className="font-bold">Policy</h2>
          {(
            [
              ['enabled', 'Freeze aktiv'],
              ['freeze_on_critical_alerts', 'Bei kritischen Alerts einfrieren'],
              ['freeze_on_failed_quality_gate', 'Bei fehlgeschlagenen Quality-Gates einfrieren'],
              ['allow_emergency_override', 'Notfall-Override erlauben'],
            ] as const
          ).map(([key, label]) => (
            <label key={key} className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={state.policy[key]}
                disabled={busy}
                onChange={(e) => togglePolicy({ [key]: e.target.checked })}
              />
              {label}
            </label>
          ))}
          <label className="flex items-center gap-2">
            Error-Budget-Untergrenze (%)
            <input
              type="number"
              min={0}
              max={100}
              className="w-20 border rounded px-1 bg-transparent"
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
