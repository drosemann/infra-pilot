import { useState } from 'react';
import { apiClient } from '../lib/api';

interface BlameAnnotation {
  name: string;
  start: number;
  end: number;
  lastAuthor: string;
  lastCommit: string;
  lastChanged: string;
  authors: string[];
  risk: string[];
}

function riskStyle(risk: string[]): string {
  if (risk.includes('uncommitted')) return 'text-red-600 font-semibold';
  if (risk.includes('stale')) return 'text-amber-600';
  if (risk.includes('many-hands')) return 'text-blue-600';
  return 'text-slate-500';
}

/** Blame-aware GitOps: who last touched each server resource, and whether that ownership looks risky. */
export function GitBlame() {
  const [filePath, setFilePath] = useState('ipilot-config.yaml');
  const [staleDays, setStaleDays] = useState(180);
  const [rows, setRows] = useState<BlameAnnotation[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await (apiClient as any).api.get('/api/gitops/blame', {
        params: { path: filePath, staleDays },
      });
      setRows(res.data.annotations || []);
    } catch (err: any) {
      setRows(null);
      setError(err?.response?.data?.error || 'Failed to load blame.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-2xl font-bold">Git Blame</h1>
      <p className="text-sm text-slate-600">
        Authorship per infrastructure resource. Uncommitted, stale, or widely-shared ownership is flagged as risk.
      </p>
      <div className="flex flex-wrap items-end gap-3">
        <label className="flex flex-col gap-1 text-sm">
          Config file (repo-relative)
          <input
            className="border rounded px-2 py-1 w-64"
            value={filePath}
            onChange={(e) => setFilePath(e.target.value)}
          />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          Stale after (days)
          <input
            type="number"
            min={1}
            className="border rounded px-2 py-1 w-24"
            value={staleDays}
            onChange={(e) => setStaleDays(Number(e.target.value) || 180)}
          />
        </label>
        <button
          className="px-3 py-1 rounded bg-slate-800 text-white disabled:opacity-50"
          disabled={loading}
          onClick={load}
        >
          {loading ? 'Loading…' : 'Blame'}
        </button>
      </div>
      {error && <p className="text-red-500">{error}</p>}
      {rows && rows.length === 0 && <p className="text-sm">No servers found in this file.</p>}
      {rows && rows.length > 0 && (
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="text-left border-b">
              <th className="py-1 pr-3">Resource</th>
              <th className="py-1 pr-3">Last author</th>
              <th className="py-1 pr-3">Commit</th>
              <th className="py-1 pr-3">Changed</th>
              <th className="py-1 pr-3">Authors</th>
              <th className="py-1 pr-3">Risk</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.name} className="border-b">
                <td className="py-1 pr-3 font-mono">{r.name}</td>
                <td className="py-1 pr-3">{r.lastAuthor}</td>
                <td className="py-1 pr-3 font-mono">{r.lastCommit}</td>
                <td className="py-1 pr-3">{r.lastChanged}</td>
                <td className="py-1 pr-3">{r.authors.join(', ') || '—'}</td>
                <td className={`py-1 pr-3 ${riskStyle(r.risk)}`}>{r.risk.join(', ') || '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
