import { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { apiClient } from '../../lib/api';

const severityColors: Record<string, string> = { critical: 'text-red-400', high: 'text-orange-400', medium: 'text-yellow-400', low: 'text-blue-400' };
const bgSeverity: Record<string, string> = { critical: 'bg-red-600', high: 'bg-orange-600', medium: 'bg-yellow-600', low: 'bg-blue-600' };

export default function CostAnomalyDetection() {
  const [anomalies, setAnomalies] = useState<any[]>([]);
  const [summary, setSummary] = useState<any>(null);
  const [filter, setFilter] = useState('');

  useEffect(() => {
    apiClient.get('/api/v1/finops/anomaly/list').then(r => setAnomalies(r.anomalies || [])).catch(() => {});
    apiClient.get('/api/v1/finops/anomaly/summary').then(r => setSummary(r)).catch(() => {});
  }, []);

  const updateStatus = async (id: string, status: string) => {
    const res = await apiClient.post(`/api/v1/finops/anomaly/${id}/status`, { status });
    if (res.success) { toast.success(`Anomaly ${status}`); setAnomalies(anomalies.map(a => a.id === id ? { ...a, status } : a)); }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Cost Anomaly Detection</h1>
          <p className="text-slate-400">ML-based detection of spend anomalies</p>
        </div>
      </div>
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 text-center">
            <div className="text-2xl font-bold text-white">{summary.total_anomalies}</div>
            <div className="text-sm text-slate-400">Total</div>
          </div>
          <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 text-center">
            <div className="text-2xl font-bold text-red-400">{summary.by_severity?.critical || 0}</div>
            <div className="text-sm text-slate-400">Critical</div>
          </div>
          <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 text-center">
            <div className="text-2xl font-bold text-yellow-400">{summary.open}</div>
            <div className="text-sm text-slate-400">Open</div>
          </div>
          <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 text-center">
            <div className="text-2xl font-bold text-green-400">{summary.resolved}</div>
            <div className="text-sm text-slate-400">Resolved</div>
          </div>
        </div>
      )}
      <div className="flex space-x-2">
        {['', 'critical', 'high', 'medium', 'low'].map(s => (
          <button key={s} onClick={() => setFilter(s)} className={`px-3 py-1 rounded text-sm ${filter === s ? 'bg-slate-600 text-white' : 'bg-slate-800 text-slate-400 hover:text-white'}`}>
            {s || 'All'}
          </button>
        ))}
      </div>
      <div className="space-y-3">
        {anomalies.filter(a => !filter || a.severity === filter).map((a: any) => (
          <div key={a.id} className="bg-slate-800 rounded-lg p-4 border border-slate-700">
            <div className="flex justify-between items-start">
              <div>
                <div className="flex items-center space-x-2">
                  <h3 className="text-white font-semibold">{a.service}</h3>
                  <span className={`px-2 py-0.5 rounded text-xs text-white ${bgSeverity[a.severity] || 'bg-slate-600'}`}>{a.severity}</span>
                  <span className={`text-xs ${severityColors[a.severity]}`}>${a.amount}</span>
                </div>
                <p className="text-slate-400 text-sm mt-1">{a.root_cause_hint}</p>
              </div>
              <span className={`px-2 py-0.5 rounded text-xs ${a.status === 'open' ? 'bg-red-600' : a.status === 'investigating' ? 'bg-yellow-600' : 'bg-green-600'} text-white`}>{a.status}</span>
            </div>
            <div className="mt-2 flex space-x-2">
              {a.status === 'open' && <button onClick={() => updateStatus(a.id, 'investigating')} className="bg-yellow-600 text-white px-3 py-1 rounded text-xs hover:bg-yellow-700">Investigate</button>}
              {a.status !== 'resolved' && a.status !== 'dismissed' && (
                <button onClick={() => updateStatus(a.id, 'resolved')} className="bg-green-600 text-white px-3 py-1 rounded text-xs hover:bg-green-700">Resolve</button>
              )}
              <button onClick={() => updateStatus(a.id, 'dismissed')} className="bg-slate-600 text-white px-3 py-1 rounded text-xs hover:bg-slate-500">Dismiss</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function AnomalyTrendChart() {
  const data = [
    { day: 'Mon', count: 8 }, { day: 'Tue', count: 12 }, { day: 'Wed', count: 5 },
    { day: 'Thu', count: 7 }, { day: 'Fri', count: 10 }, { day: 'Sat', count: 3 }, { day: 'Sun', count: 2 },
  ];
  const maxCount = Math.max(...data.map(d => d.count)) * 1.3;
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-white font-semibold mb-3">Anomalies This Week</h3>
      <div className="flex items-end space-x-3 h-32">
        {data.map((d, i) => (
          <div key={i} className="flex-1 flex flex-col items-center">
            <div className="w-full bg-red-500 rounded-t" style={{ height: `${(d.count / maxCount) * 100}%` }} />
            <div className="text-xs text-slate-400 mt-1">{d.day}</div>
            <div className="text-xs text-slate-500">{d.count}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function AnomalyProfilesPanel() {
  const profiles = [
    { name: 'default-zscore', method: 'zscore', sensitivity: 2.0, active: true },
    { name: 'critical-mad', method: 'mad', sensitivity: 3.5, active: true },
    { name: 'adaptive-prod', method: 'adaptive', sensitivity: 1.5, active: true },
  ];
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-white font-semibold mb-3">Detection Profiles</h3>
      {profiles.map((p, i) => (
        <div key={i} className="flex items-center justify-between py-2 border-b border-slate-700 last:border-0">
          <div>
            <p className="text-white text-sm">{p.name}</p>
            <p className="text-slate-400 text-xs">{p.method} · sensitivity: {p.sensitivity}</p>
          </div>
          <span className={`px-2 py-0.5 rounded text-xs ${p.active ? 'bg-green-600' : 'bg-slate-600'} text-white`}>{p.active ? 'Active' : 'Inactive'}</span>
        </div>
      ))}
    </div>
  );
}

function AnomalyReportSummary() {
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-white font-semibold mb-3">Anomaly Report</h3>
      <div className="grid grid-cols-2 gap-3 text-sm">
        <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Period</span><div className="text-white">Last 30 days</div></div>
        <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Total</span><div className="text-white">47 anomalies</div></div>
        <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Open</span><div className="text-red-400">8</div></div>
        <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Excess Spend</span><div className="text-red-400">$12,450</div></div>
        <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Avg Response</span><div className="text-white">2h 15m</div></div>
        <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Auto-Resolved</span><div className="text-green-400">15 (32%)</div></div>
      </div>
    </div>
  );
}

function AnomalyPaginationTable({ anomalies, pageSize = 5 }: { anomalies: any[]; pageSize?: number }) {
  const [page, setPage] = useState(1);
  const totalPages = Math.ceil(anomalies.length / pageSize);
  const paginated = anomalies.slice((page - 1) * pageSize, page * pageSize);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-white font-semibold mb-3">Anomalies (Page {page}/{totalPages})</h3>
      <table className="w-full text-sm">
        <thead><tr className="text-slate-400 border-b border-slate-700"><th className="text-left py-2">ID</th><th className="text-left py-2">Service</th><th className="text-right py-2">Amount</th><th className="text-right py-2">Status</th></tr></thead>
        <tbody>{paginated.map((a: any) => (<tr key={a.id} className="border-b border-slate-700"><td className="py-2 text-white">{a.id}</td><td className="py-2 text-slate-300">{a.service}</td><td className="py-2 text-right text-white">${a.amount}</td><td className="py-2 text-right text-slate-300">{a.status}</td></tr>))}</tbody>
      </table>
      <div className="flex justify-between items-center mt-3 text-sm text-slate-400">
        <span>{anomalies.length} total</span>
        <div className="flex gap-2"><button disabled={page <= 1} onClick={() => setPage(p => p - 1)} className="px-3 py-1 bg-slate-700 rounded hover:bg-slate-600 disabled:opacity-50">Prev</button><button disabled={page >= totalPages} onClick={() => setPage(p => p + 1)} className="px-3 py-1 bg-slate-700 rounded hover:bg-slate-600 disabled:opacity-50">Next</button></div>
      </div>
    </div>
  );
}

function AnomalyIngestForm() {
  const [service, setService] = useState('aws-ec2');
  const [amount, setAmount] = useState(100);
  const [region, setRegion] = useState('us-east-1');
  const handleIngest = async () => {
    const res = await apiClient.post('/api/v1/finops/anomaly/ingest', { service, amount, region });
    if (res.id) toast.success('Spend record ingested');
  };
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-white font-semibold mb-3">Ingest Test Record</h3>
      <div className="grid grid-cols-3 gap-3">
        <select value={service} onChange={e => setService(e.target.value)} className="bg-slate-700 text-white p-2 rounded">
          <option value="aws-ec2">EC2</option><option value="aws-s3">S3</option><option value="data-transfer">Data Transfer</option>
        </select>
        <input type="number" value={amount} onChange={e => setAmount(Number(e.target.value))} className="bg-slate-700 text-white p-2 rounded" />
        <select value={region} onChange={e => setRegion(e.target.value)} className="bg-slate-700 text-white p-2 rounded">
          <option value="us-east-1">us-east-1</option><option value="eu-west-1">eu-west-1</option>
        </select>
      </div>
      <button onClick={handleIngest} className="mt-3 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 text-sm">Ingest</button>
    </div>
  );
}
