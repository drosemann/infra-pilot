import { useState, useEffect } from 'react';
import { apiClient } from '../lib/api';

export default function MetricsConfig() {
  const [type, setType] = useState<'netdata' | 'grafana'>('grafana');
  const [url, setUrl] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [status, setStatus] = useState<'idle' | 'connected' | 'disconnected'>('idle');

  useEffect(() => {
    apiClient.getGrafanaUrl().then((data) => {
      if (data.url) {
        setUrl(data.url);
        setStatus('connected');
      }
    }).catch(() => {});
  }, []);

  const testConnection = async () => {
    setTesting(true);
    try {
      const res = await fetch(url, { method: 'HEAD', signal: AbortSignal.timeout(5000) });
      setStatus(res.ok ? 'connected' : 'disconnected');
    } catch {
      setStatus('disconnected');
    } finally {
      setTesting(false);
    }
  };

  const save = async () => {
    setSaving(true);
    try {
      await apiClient.configureMetricsSource({ type, url, apiKey: apiKey || undefined });
      setStatus('connected');
    } catch {
      setStatus('disconnected');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="card p-6">
      <h2 className="mb-4 text-lg font-semibold text-white">Metrics Integration</h2>

      <div className="space-y-4">
        <div>
          <label className="mb-1 block text-sm text-white/45">Source Type</label>
          <div className="flex gap-3">
            {(['grafana', 'netdata'] as const).map(t => (
              <button key={t} onClick={() => setType(t)}
                className={`px-4 py-2 rounded text-sm font-medium transition-colors ${
                  type === t ? 'bg-white text-black' : 'text-white/60 hover:bg-white/10 hover:text-white'
                }`}>
                {t.charAt(0).toUpperCase() + t.slice(1)}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="mb-1 block text-sm text-white/45">URL</label>
          <input type="text" value={url} onChange={e => setUrl(e.target.value)}
            placeholder={type === 'grafana' ? 'https://grafana.example.com/d/abc/...' : 'https://netdata.example.com'}
            className="input-field w-full text-sm" />
        </div>

        {type === 'grafana' && (
          <div>
            <label className="mb-1 block text-sm text-white/45">API Key (optional)</label>
            <input type="password" value={apiKey} onChange={e => setApiKey(e.target.value)}
              placeholder="glsa_..."
              className="input-field w-full text-sm" />
          </div>
        )}

        <div className="flex items-center gap-3">
          <button onClick={testConnection} disabled={!url || testing}
            className="secondary-button">
            {testing ? 'Testing...' : 'Test Connection'}
          </button>
          <button onClick={save} disabled={!url || saving}
            className="primary-button">
            {saving ? 'Saving...' : 'Save'}
          </button>
          {status !== 'idle' && (
            <span className={`text-sm ${status === 'connected' ? 'text-green-400' : 'text-red-400'}`}>
              {status === 'connected' ? 'Connected' : 'Disconnected'}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
