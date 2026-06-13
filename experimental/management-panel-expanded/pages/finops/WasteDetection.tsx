import { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { apiClient } from '../../lib/api';

export default function WasteDetection() {
  const [findings, setFindings] = useState<any[]>([]);
  const [summary, setSummary] = useState<any>(null);
  const [scanning, setScanning] = useState(false);

  useEffect(() => {
    apiClient.get('/api/v1/finops/waste/summary').then(r => setSummary(r)).catch(() => {});
    apiClient.get('/api/v1/finops/waste/findings').then(r => setFindings(r.findings || [])).catch(() => {});
  }, []);

  const scan = async () => {
    setScanning(true);
    const res = await apiClient.post('/api/v1/finops/waste/scan', {});
    if (res.findings !== undefined) {
      toast.success(`Scan complete: ${res.findings} waste items found`);
      const fRes = await apiClient.get('/api/v1/finops/waste/findings');
      setFindings(fRes.findings || []);
      const sRes = await apiClient.get('/api/v1/finops/waste/summary');
      setSummary(sRes);
    }
    setScanning(false);
  };

  const action = async (id: string, action: string) => {
    const res = await apiClient.post(`/api/v1/finops/waste/findings/${id}/${action}`, {});
    if (res.success) {
      toast.success(`Finding ${action}ed!`);
      setFindings(findings.map(f => f.id === id ? { ...f, status: action === 'cleanup' ? 'cleaned_up' : action === 'approve' ? 'approved_for_cleanup' : 'dismissed' } : f));
    }
  };

  const severityColors: Record<string, string> = { critical: 'text-red-400', high: 'text-orange-400', medium: 'text-yellow-400', low: 'text-blue-400' };

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Cloud Waste Detection</h1>
          <p className="text-slate-400">Detect unattached volumes, idle instances, orphaned resources</p>
        </div>
        <button onClick={scan} disabled={scanning} className="bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700 disabled:opacity-50">
          {scanning ? 'Scanning...' : 'Scan Now'}
        </button>
      </div>
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 text-center">
            <div className="text-2xl font-bold text-white">{summary.total_findings}</div>
            <div className="text-sm text-slate-400">Total Findings</div>
          </div>
          <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 text-center">
            <div className="text-2xl font-bold text-red-400">${summary.total_monthly_waste}</div>
            <div className="text-sm text-slate-400">Monthly Waste</div>
          </div>
          <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 text-center">
            <div className="text-2xl font-bold text-yellow-400">{summary.open}</div>
            <div className="text-sm text-slate-400">Open</div>
          </div>
          <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 text-center">
            <div className="text-2xl font-bold text-green-400">{summary.cleaned_up}</div>
            <div className="text-sm text-slate-400">Cleaned Up</div>
          </div>
        </div>
      )}
      <div className="space-y-3">
        {findings.filter(f => f.status !== 'cleaned_up').map((f: any) => (
          <div key={f.id} className="bg-slate-800 rounded-lg p-4 border border-slate-700">
            <div className="flex justify-between items-start">
              <div>
                <div className="flex items-center space-x-2">
                  <h3 className="text-white font-semibold">{f.resource_name}</h3>
                  <span className={`text-xs ${severityColors[f.severity] || 'text-slate-400'}`}>{f.severity}</span>
                  <span className="text-xs text-slate-500">{f.category}</span>
                </div>
                <p className="text-sm text-slate-400 mt-1">{f.reason}</p>
              </div>
              <div className="text-right">
                <div className="text-red-400 font-semibold">${f.monthly_waste}/mo</div>
                <span className={`px-2 py-0.5 rounded text-xs ${f.status === 'detected' ? 'bg-red-600' : f.status === 'approved_for_cleanup' ? 'bg-yellow-600' : 'bg-slate-600'} text-white`}>{f.status}</span>
              </div>
            </div>
            {f.status === 'detected' && (
              <div className="mt-3 flex space-x-2">
                {f.auto_cleanup_eligible && <button onClick={() => action(f.id, 'approve')} className="bg-yellow-600 text-white px-3 py-1 rounded text-xs hover:bg-yellow-700">Approve Cleanup</button>}
                <button onClick={() => action(f.id, 'dismiss')} className="bg-slate-600 text-white px-3 py-1 rounded text-xs hover:bg-slate-500">Dismiss</button>
              </div>
            )}
            {f.status === 'approved_for_cleanup' && (
              <button onClick={() => action(f.id, 'cleanup')} className="mt-3 bg-green-600 text-white px-3 py-1 rounded text-xs hover:bg-green-700">Execute Cleanup</button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function WasteCategoryBreakdown() {
  const categories = [
    { name: 'Idle Instances', amount: 560, count: 3, color: 'bg-red-500' },
    { name: 'Unattached Volumes', amount: 320, count: 4, color: 'bg-orange-500' },
    { name: 'Orphaned Snapshots', amount: 210, count: 7, color: 'bg-yellow-500' },
    { name: 'Underutilized DBs', amount: 450, count: 2, color: 'bg-blue-500' },
    { name: 'Orphaned LBs', amount: 307, count: 2, color: 'bg-purple-500' },
  ];
  const total = categories.reduce((s, c) => s + c.amount, 0);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-white font-semibold mb-3">Waste by Category</h3>
      {categories.map((c, i) => (
        <div key={i} className="mb-2">
          <div className="flex justify-between text-sm mb-1">
            <span className="text-slate-300">{c.name}</span>
            <span className="text-red-400">${c.amount}/mo ({c.count} items)</span>
          </div>
          <div className="w-full bg-slate-700 rounded-full h-2">
            <div className={`${c.color} h-2 rounded-full`} style={{ width: `${(c.amount / total) * 100}%` }} />
          </div>
        </div>
      ))}
      <div className="mt-3 pt-3 border-t border-slate-700 flex justify-between text-sm">
        <span className="text-white font-semibold">Total</span>
        <span className="text-red-400 font-semibold">${total}/mo</span>
      </div>
    </div>
  );
}

function WasteTrendChart() {
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'];
  const values = [2800, 2500, 2150, 1850, 1700, 1550];
  const maxVal = Math.max(...values) * 1.2;
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-white font-semibold mb-3">Waste Trend (6 Months)</h3>
      <div className="flex items-end space-x-3 h-32">
        {values.map((v, i) => (
          <div key={i} className="flex-1 flex flex-col items-center">
            <div className="w-full bg-emerald-500 rounded-t" style={{ height: `${(v / maxVal) * 100}%` }} />
            <div className="text-xs text-slate-400 mt-1">${v}</div>
            <div className="text-xs text-slate-500">{months[i]}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function WasteSummaryCards({ findings }: { findings: any[] }) {
  const totalWaste = findings.reduce((s: number, f: any) => s + (f.monthly_waste || 0), 0);
  const recoverable = totalWaste * 0.8;
  const itemCount = findings.length;
  return (
    <div className="grid grid-cols-3 gap-4">
      <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 text-center">
        <div className="text-2xl font-bold text-red-400">${totalWaste.toLocaleString()}</div><div className="text-sm text-slate-400 mt-1">Total Waste/mo</div>
      </div>
      <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 text-center">
        <div className="text-2xl font-bold text-green-400">${recoverable.toLocaleString()}</div><div className="text-sm text-slate-400 mt-1">Recoverable/mo</div>
      </div>
      <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 text-center">
        <div className="text-2xl font-bold text-white">{itemCount}</div><div className="text-sm text-slate-400 mt-1">Findings</div>
      </div>
    </div>
  );
}

function WasteRecommendations() {
  const actions = [
    { resource: 'i-0abc (EC2)', action: 'Stop instance', savings: 450, effort: 'Low', id: '1' },
    { resource: 'vol-0def (EBS)', action: 'Delete volume', savings: 120, effort: 'Low', id: '2' },
    { resource: 'rds-prod (RDS)', action: 'Resize instance', savings: 280, effort: 'Medium', id: '3' },
  ];
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-white font-semibold mb-3">Recommended Actions</h3>
      {actions.map((a, i) => (
        <div key={i} className="flex items-center justify-between py-2 border-b border-slate-700 last:border-0">
          <div>
            <p className="text-white text-sm">{a.resource}</p>
            <p className="text-slate-400 text-xs">{a.action} · {a.effort} effort</p>
          </div>
          <div className="text-right">
            <span className="text-green-400 text-sm font-semibold">${a.savings}/mo</span>
          </div>
        </div>
      ))}
    </div>
  );
}

function WasteFilterBar({ onFilter }: { onFilter: (filters: any) => void }) {
  const [category, setCategory] = useState('');
  const [severity, setSeverity] = useState('');
  return (
    <div className="flex gap-3 flex-wrap items-end">
      <div>
        <label className="block text-xs text-slate-400 mb-1">Category</label>
        <select value={category} onChange={e => { setCategory(e.target.value); onFilter({ category: e.target.value, severity }); }} className="bg-slate-800 text-white px-3 py-1.5 rounded border border-slate-700 text-sm">
          <option value="">All</option><option value="idle_instance">Idle</option><option value="unattached_volume">Unattached</option><option value="orphaned_snapshot">Orphaned</option>
        </select>
      </div>
      <div>
        <label className="block text-xs text-slate-400 mb-1">Severity</label>
        <select value={severity} onChange={e => { setSeverity(e.target.value); onFilter({ category, severity: e.target.value }); }} className="bg-slate-800 text-white px-3 py-1.5 rounded border border-slate-700 text-sm">
          <option value="">All</option><option value="critical">Critical</option><option value="high">High</option><option value="medium">Medium</option>
        </select>
      </div>
      <button onClick={() => { setCategory(''); setSeverity(''); onFilter({}); }} className="px-3 py-1.5 bg-slate-700 text-white rounded text-sm hover:bg-slate-600">Clear</button>
    </div>
  );
}
