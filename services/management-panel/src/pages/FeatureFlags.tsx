import { useEffect, useState } from 'react';
import { apiClient } from '../lib/api';
import { PageHeader } from '../components/PageHeader';

interface FlagRow {
  key: string;
  description: string;
  value_type: string;
  default_value: boolean | string;
  status: string;
  expires_at: string | null;
  rules: Record<string, { environment: string; enabled: boolean; rollout_percentage: number }>;
}

/** Admin page: list, toggle, roll out, and kill feature flags. Non-admins never get the route (see App.tsx). */
export function FeatureFlags() {
  const [flags, setFlags] = useState<FlagRow[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  const load = async () => {
    try {
      const res = await (apiClient as any).api.get('/api/feature-flags');
      setFlags(res.data.flags || []);
    } catch (err: any) {
      setError(err?.response?.data?.error || 'Failed to load flags (admin only).');
    }
  };

  useEffect(() => {
    load();
  }, []);

  const patchRule = async (key: string, environment: string, patch: Record<string, unknown>) => {
    setBusy(key);
    try {
      await (apiClient as any).api.patch(`/api/feature-flags/${key}`, {
        rule: { environment, enabled: false, rollout_percentage: 0, ...patch },
      });
      await load();
    } catch (err: any) {
      setError(err?.response?.data?.error || 'Update failed.');
    } finally {
      setBusy(null);
    }
  };

  const kill = async (key: string) => {
    if (!window.confirm(`Kill switch: disable "${key}" in ALL environments now?`)) return;
    setBusy(key);
    try {
      await (apiClient as any).api.post(`/api/feature-flags/${key}/kill`);
      await load();
    } catch (err: any) {
      setError(err?.response?.data?.error || 'Kill failed.');
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className="mx-auto max-w-5xl space-y-6 px-2 py-8">
      <PageHeader eyebrow="Ship">
        <h1 className="text-4xl font-semibold tracking-tight text-white">Feature Flags</h1>
        <p className="mt-2 text-white/55">Roll out gradually. Kill instantly.</p>
      </PageHeader>

      {error && <p className="text-sm text-red-400">{error}</p>}
      {flags.length === 0 && !error && (
        <div className="card p-12 text-center">
          <p className="text-white/55">No feature flags yet.</p>
        </div>
      )}
      {flags.map((f) => (
        <div key={f.key} className="card space-y-3 p-5">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="font-mono font-semibold text-white">{f.key}</p>
              <p className="mt-1 text-sm text-white/50">{f.description}</p>
              {f.expires_at && new Date(f.expires_at) < new Date() && (
                <p className="mt-1 text-sm text-amber-400/90">Expired — evaluating to default.</p>
              )}
            </div>
            <button
              className="secondary-button"
              disabled={busy === f.key}
              onClick={() => kill(f.key)}
            >
              Kill
            </button>
          </div>
          {Object.values(f.rules || {}).map((r) => (
            <div key={r.environment} className="flex flex-wrap items-center gap-4 text-sm text-white/70">
              <span className="w-28 text-white/45">{r.environment}</span>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={r.enabled}
                  disabled={busy === f.key}
                  onChange={(e) => patchRule(f.key, r.environment, { enabled: e.target.checked })}
                />
                Enabled
              </label>
              <label className="flex items-center gap-2">
                Rollout
                <input
                  type="number"
                  min={0}
                  max={100}
                  className="input-field w-20"
                  defaultValue={r.rollout_percentage}
                  onBlur={(e) => patchRule(f.key, r.environment, { rollout_percentage: Number(e.target.value) })}
                />
                %
              </label>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}
