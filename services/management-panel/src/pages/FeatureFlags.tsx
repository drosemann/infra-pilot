import { useEffect, useState } from 'react';
import { apiClient } from '../lib/api';

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
    <div className="p-6 space-y-4">
      <h1 className="text-2xl font-bold">Feature Flags</h1>
      {error && <p className="text-red-500">{error}</p>}
      {flags.map((f) => (
        <div key={f.key} className="border rounded p-4 space-y-2">
          <div className="flex items-center justify-between">
            <div>
              <code className="font-mono font-bold">{f.key}</code>
              <p className="text-sm opacity-70">{f.description}</p>
              {f.expires_at && new Date(f.expires_at) < new Date() && (
                <p className="text-sm text-amber-500">Expired — evaluating to default.</p>
              )}
            </div>
            <button
              className="px-3 py-1 rounded bg-red-600 text-white disabled:opacity-50"
              disabled={busy === f.key}
              onClick={() => kill(f.key)}
            >
              Kill
            </button>
          </div>
          {Object.values(f.rules || {}).map((r) => (
            <div key={r.environment} className="flex items-center gap-3 text-sm">
              <span className="w-28">{r.environment}</span>
              <label className="flex items-center gap-1">
                <input
                  type="checkbox"
                  checked={r.enabled}
                  disabled={busy === f.key}
                  onChange={(e) => patchRule(f.key, r.environment, { enabled: e.target.checked })}
                />
                enabled
              </label>
              <label className="flex items-center gap-1">
                rollout
                <input
                  type="number"
                  min={0}
                  max={100}
                  className="w-16 border rounded px-1"
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
