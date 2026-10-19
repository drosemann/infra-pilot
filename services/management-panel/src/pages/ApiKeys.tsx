import { useEffect, useState } from 'react';
import { apiClient } from '../lib/api.ts';

/**
 * Scoped API key row (key model v2) as returned by GET /api/api-keys.
 * `scopes` is null for pre-v2 legacy keys, which keep the wildcard contract.
 */
interface ScopedApiKeyRow {
  id: string;
  name: string;
  key_prefix: string;
  role?: string | null;
  scopes: string[] | null;
  key_class: 'live' | 'test' | 'legacy';
  app_id: string | null;
  expires_at: string | null;
  last_used_at: string | null;
  created_at: string;
  force_rotate?: boolean;
  needs_rotation: boolean;
}

const CLASS_CHIP: Record<ScopedApiKeyRow['key_class'], string> = {
  live: 'bg-emerald-900/60 text-emerald-200 border border-emerald-700',
  test: 'bg-amber-900/60 text-amber-200 border border-amber-700',
  legacy: 'bg-slate-800 text-slate-300 border border-slate-600',
};

const REAUTH_ERROR =
  'Fresh two-factor code required (X-2FA-Token) — sensitive key operations require re-authentication when TOTP is enabled.';

const MAX_EXPIRE_DAYS = 730;

const formatDateTime = (value: string | null): string => {
  if (!value) return '—';
  try {
    return new Date(value).toLocaleString();
  } catch {
    return value;
  }
};

const shortId = (id: string): string => (id.length > 8 ? id.slice(0, 8) : id);

const surfaceKeyError = (e: any, fallback: string): string => {
  const data = e?.response?.data;
  if (data?.code === 'reauth_required') {
    return REAUTH_ERROR;
  }
  const msg = data?.error;
  if (typeof msg === 'string' && msg.trim()) {
    return msg;
  }
  if (msg && typeof msg === 'object') {
    try {
      return JSON.stringify(msg);
    } catch {
      // fall through to the generic fallback
    }
  }
  const status = e?.response?.status;
  if (status) {
    return `HTTP ${status}`;
  }
  return fallback;
};

/**
 * Scoped API keys page. Lists key model v2 keys and lets users create, rotate,
 * and revoke them. The backend is the source of truth — the raw key is shown
 * exactly once and 403 reauth_required responses surface as errors.
 */
export function ApiKeys() {
  const [keys, setKeys] = useState<ScopedApiKeyRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [rawKey, setRawKey] = useState<{ name: string; key: string } | null>(null);
  const [copied, setCopied] = useState(false);

  const [newName, setNewName] = useState('');
  const [newKeyClass, setNewKeyClass] = useState<'live' | 'test'>('live');
  const [newScopes, setNewScopes] = useState('');
  const [newExpireDays, setNewExpireDays] = useState('');
  const [newAppId, setNewAppId] = useState('');

  const fetchKeys = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.listApiKeys();
      setKeys(Array.isArray(data?.api_keys) ? data.api_keys : []);
    } catch (e: any) {
      setError(surfaceKeyError(e, 'Failed to load API keys'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchKeys();
  }, []);

  const copyRawKey = async (key: string) => {
    try {
      await navigator.clipboard.writeText(key);
      setCopied(true);
    } catch {
      setCopied(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    const name = newName.trim();
    if (!name || busy) return;

    const scopes = newScopes
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean);

    let expireDays: number | undefined;
    if (newExpireDays.trim()) {
      const days = Number(newExpireDays);
      if (!Number.isInteger(days) || days < 1 || days > MAX_EXPIRE_DAYS) {
        setError(`Expire days must be a whole number between 1 and ${MAX_EXPIRE_DAYS}.`);
        return;
      }
      expireDays = days;
    }

    setBusy(true);
    setError(null);
    setCopied(false);
    try {
      const created = await apiClient.createApiKey({
        name,
        key_class: newKeyClass,
        ...(scopes.length ? { scopes } : {}),
        ...(expireDays !== undefined ? { expire_days: expireDays } : {}),
        ...(newAppId.trim() ? { app_id: newAppId.trim() } : {}),
      });
      if (created?.key) {
        setRawKey({ name: created.name || name, key: created.key });
      }
      setNewName('');
      setNewScopes('');
      setNewExpireDays('');
      setNewAppId('');
      await fetchKeys();
    } catch (e2: any) {
      setError(surfaceKeyError(e2, 'Failed to create API key'));
    } finally {
      setBusy(false);
    }
  };

  const handleRotate = async (row: ScopedApiKeyRow) => {
    if (busy) return;
    setBusy(true);
    setError(null);
    setCopied(false);
    try {
      const rotated = await apiClient.rotateApiKey(row.id);
      if (rotated?.key) {
        setRawKey({ name: rotated.name || row.name, key: rotated.key });
      }
      await fetchKeys();
    } catch (e: any) {
      setError(surfaceKeyError(e, 'Failed to rotate API key'));
    } finally {
      setBusy(false);
    }
  };

  const handleRevoke = async (row: ScopedApiKeyRow) => {
    if (busy) return;
    setBusy(true);
    setError(null);
    try {
      await apiClient.revokeApiKey(row.id);
      await fetchKeys();
    } catch (e: any) {
      setError(surfaceKeyError(e, 'Failed to revoke API key'));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="p-6 space-y-6" aria-labelledby="api-keys-heading">
      <div>
        <h1 id="api-keys-heading" className="text-2xl font-bold text-slate-100">API Keys</h1>
        <p className="text-slate-400 mt-1">
          Scoped API keys (key model v2). The raw key is shown once at creation or rotation —
          save it in a secret manager. Test keys are for non-production integrations.
        </p>
      </div>

      {error && (
        <div role="alert" className="px-4 py-3 rounded bg-red-900/40 border border-red-700 text-red-200">
          {error}
        </div>
      )}

      {rawKey && (
        <div role="status" className="px-4 py-3 rounded bg-amber-900/40 border border-amber-600">
          <p className="font-semibold text-amber-100">
            Save this key now — it will not be shown again
          </p>
          <p className="text-sm text-amber-200/90 mt-0.5">Key for {rawKey.name}</p>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <code className="px-3 py-2 rounded bg-slate-900 border border-slate-700 text-slate-100 font-mono break-all">
              {rawKey.key}
            </code>
            <button
              type="button"
              onClick={() => copyRawKey(rawKey.key)}
              className="px-3 py-2 rounded bg-amber-600 hover:bg-amber-500 text-slate-900 font-semibold"
            >
              {copied ? 'Copied' : 'Copy'}
            </button>
            <button
              type="button"
              onClick={() => setRawKey(null)}
              className="px-3 py-2 rounded border border-amber-700 hover:bg-amber-900/60 text-amber-100"
            >
              Done
            </button>
          </div>
        </div>
      )}

      <div>
        <h2 className="text-lg font-semibold text-slate-200">Create API key</h2>
        <form onSubmit={handleCreate} className="mt-2 flex flex-wrap gap-3 items-end">
          <div className="flex flex-col gap-1">
            <label htmlFor="apikey-name" className="text-sm text-slate-300">Name</label>
            <input
              id="apikey-name"
              aria-label="API key name"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="e.g. CI pipeline"
              className="px-3 py-2 rounded bg-slate-800 border border-slate-700 text-slate-100 w-64"
            />
          </div>
          <div className="flex flex-col gap-1">
            <label htmlFor="apikey-class" className="text-sm text-slate-300">Class</label>
            <select
              id="apikey-class"
              aria-label="API key class"
              value={newKeyClass}
              onChange={(e) => setNewKeyClass(e.target.value as 'live' | 'test')}
              className="px-3 py-2 rounded bg-slate-800 border border-slate-700 text-slate-100"
            >
              <option value="live">live</option>
              <option value="test">test</option>
            </select>
          </div>
          <div className="flex flex-col gap-1">
            <label htmlFor="apikey-scopes" className="text-sm text-slate-300">Scopes</label>
            <input
              id="apikey-scopes"
              aria-label="Scopes, comma separated"
              value={newScopes}
              onChange={(e) => setNewScopes(e.target.value)}
              placeholder="apps:read, metrics:*"
              className="px-3 py-2 rounded bg-slate-800 border border-slate-700 text-slate-100 w-96 font-mono"
            />
            <p className="text-xs text-slate-500">apps:read, metrics:* — omit for wildcard *</p>
          </div>
          <div className="flex flex-col gap-1">
            <label htmlFor="apikey-expire-days" className="text-sm text-slate-300">Expires in (days)</label>
            <input
              id="apikey-expire-days"
              aria-label="Expiration in days, max 730"
              type="number"
              min={1}
              max={MAX_EXPIRE_DAYS}
              value={newExpireDays}
              onChange={(e) => setNewExpireDays(e.target.value)}
              placeholder="e.g. 90"
              className="px-3 py-2 rounded bg-slate-800 border border-slate-700 text-slate-100 w-36"
            />
          </div>
          <div className="flex flex-col gap-1">
            <label htmlFor="apikey-app-id" className="text-sm text-slate-300">App ID (optional)</label>
            <input
              id="apikey-app-id"
              aria-label="App ID, optional"
              value={newAppId}
              onChange={(e) => setNewAppId(e.target.value)}
              placeholder="Bind key to an app"
              className="px-3 py-2 rounded bg-slate-800 border border-slate-700 text-slate-100 w-64 font-mono"
            />
          </div>
          <button
            type="submit"
            disabled={busy || !newName.trim()}
            className="px-4 py-2 rounded bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white"
          >
            Create Key
          </button>
        </form>
      </div>

      {loading ? (
        <p className="text-slate-400">Loading...</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left text-slate-400 border-b border-slate-700">
                <th scope="col" className="py-2 pr-4">Name</th>
                <th scope="col" className="py-2 pr-4">Prefix</th>
                <th scope="col" className="py-2 pr-4">Class</th>
                <th scope="col" className="py-2 pr-4">Scopes</th>
                <th scope="col" className="py-2 pr-4">Expires</th>
                <th scope="col" className="py-2 pr-4">Last used</th>
                <th scope="col" className="py-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {keys.map((row) => (
                <tr key={row.id} className="border-b border-slate-800">
                  <td className="py-2 pr-4 text-slate-200">{row.name}</td>
                  <td className="py-2 pr-4 font-mono text-slate-200">{row.key_prefix}</td>
                  <td className="py-2 pr-4">
                    <span
                      className={`px-2 py-0.5 rounded text-xs ${CLASS_CHIP[row.key_class] || CLASS_CHIP.legacy}`}
                    >
                      {row.key_class}
                    </span>
                  </td>
                  <td className="py-2 pr-4">
                    <div className="flex flex-wrap items-center gap-1">
                      {row.scopes ? (
                        row.scopes.map((scope) => (
                          <span
                            key={scope}
                            className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700 font-mono text-xs text-slate-200"
                          >
                            {scope}
                          </span>
                        ))
                      ) : (
                        <>
                          <span className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700 font-mono text-xs text-slate-400">
                            legacy *
                          </span>
                          {row.needs_rotation && (
                            <span className="px-2 py-0.5 rounded bg-red-900/60 border border-red-700 font-mono text-xs text-red-200">
                              rotate
                            </span>
                          )}
                        </>
                      )}
                      {row.app_id && (
                        <span
                          className="px-2 py-0.5 rounded bg-slate-900 border border-slate-700 font-mono text-xs text-slate-400"
                          title={`App ${row.app_id}`}
                        >
                          app:{shortId(row.app_id)}
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="py-2 pr-4 text-slate-400">
                    {row.expires_at ? formatDateTime(row.expires_at) : 'Never'}
                  </td>
                  <td className="py-2 pr-4 text-slate-400">
                    {row.last_used_at ? formatDateTime(row.last_used_at) : '—'}
                  </td>
                  <td className="py-2">
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleRotate(row)}
                        disabled={busy}
                        className="px-3 py-1 rounded bg-blue-900/60 hover:bg-blue-800 disabled:opacity-50 text-blue-100"
                      >
                        Rotate
                      </button>
                      <button
                        onClick={() => handleRevoke(row)}
                        disabled={busy}
                        className="px-3 py-1 rounded bg-red-900/60 hover:bg-red-800 disabled:opacity-50 text-red-100"
                      >
                        Revoke
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {keys.length === 0 && (
                <tr>
                  <td colSpan={7} className="py-4 text-slate-400">
                    No API keys yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default ApiKeys;
