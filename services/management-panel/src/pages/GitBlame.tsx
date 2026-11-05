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
  if (risk.includes('uncommitted')) return 'font-semibold text-red-400';
  if (risk.includes('stale')) return 'text-amber-300';
  if (risk.includes('many-hands')) return 'text-sky-300';
  return 'text-white/40';
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
    <div className="mx-auto max-w-5xl space-y-6 px-2 py-8">
      <h1 className="text-4xl font-semibold tracking-tight text-white">Git Blame</h1>
      <p className="mt-2 max-w-2xl text-white/55">
        Authorship per infrastructure resource. Uncommitted, stale, or widely-shared ownership is flagged as risk.
      </p>
      <div className="flex flex-wrap items-end gap-3">
        <label className="flex flex-col gap-1 text-sm text-white/55">
          Config file (repo-relative)
          <input            className="input-field w-64"
            value={filePath}
            onChange={(e) => setFilePath(e.target.value)}
          />
        </label>
        <label className="flex flex-col gap-1 text-sm text-white/55">
          Stale after (days)
          <input
            type="number"
            min={1}
            className="input-field w-24"
            value={staleDays}
            onChange={(e) => setStaleDays(Number(e.target.value) || 180)}
          />
        </label>
        <button
          className="primary-button"
          disabled={loading}
          onClick={load}
        >
          {loading ? 'Loadingâ€¦' : 'Blame'}
        </button>
      </div>
      {error && <p className="text-sm text-red-400">{error}</p>}
      {rows && rows.length === 0 && <p className="text-sm text-white/45">No servers found in this file.</p>}
      {rows && rows.length > 0 && (
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-white/10 text-left text-white/45">
              <th className="py-2 pr-3 font-medium">Resource</th>
              <th className="py-2 pr-3 font-medium">Last author</th>
              <th className="py-2 pr-3 font-medium">Commit</th>
              <th className="py-2 pr-3 font-medium">Changed</th>
              <th className="py-2 pr-3 font-medium">Authors</th>
              <th className="py-2 pr-3 font-medium">Risk</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.name} className="border-b border-white/5">
                <td className="py-2 pr-3 font-mono text-white">{r.name}</td>
                <td className="py-2 pr-3 text-white/70">{r.lastAuthor}</td>
                <td className="py-2 pr-3 font-mono text-white">{r.lastCommit}</td>
                <td className="py-2 pr-3 text-white/70">{r.lastChanged}</td>
                <td className="py-2 pr-3 text-white/70">{r.authors.join(', ') || 'â€”'}</td>
                <td className={`py-2 pr-3 ${riskStyle(r.risk)}`}>{r.risk.join(', ') || 'â€”'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
