import { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { apiClient } from '../../lib/api';

export default function Rightsizing() {
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [summary, setSummary] = useState<any>(null);

  useEffect(() => {
    apiClient.get('/api/v1/finops/rightsizing/recommendations').then(r => setRecommendations(r.recommendations || [])).catch(() => {});
    apiClient.get('/api/v1/finops/rightsizing/summary').then(r => setSummary(r)).catch(() => {});
  }, []);

  const action = async (id: string, action: string) => {
    const res = await apiClient.post(`/api/v1/finops/rightsizing/recommendations/${id}/${action}`, {});
    if (res.success) {
      toast.success(`Recommendation ${action}ed!`);
      setRecommendations(recommendations.map(r => r.id === id ? { ...r, status: action === 'implement' ? 'implemented' : action === 'approve' ? 'approved' : 'dismissed' } : r));
    }
  };

  const priorityColors: Record<string, string> = { critical: 'text-red-400', high: 'text-orange-400', medium: 'text-yellow-400', low: 'text-blue-400' };

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Resource Right-Sizing</h1>
          <p className="text-slate-400">Analyze utilization and recommend size changes</p>
        </div>
      </div>
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 text-center">
            <div className="text-2xl font-bold text-white">{summary.total_recommendations}</div>
            <div className="text-sm text-slate-400">Total Recommendations</div>
          </div>
          <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 text-center">
            <div className="text-2xl font-bold text-green-400">${summary.potential_monthly_savings}</div>
            <div className="text-sm text-slate-400">Potential Monthly Savings</div>
          </div>
          <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 text-center">
            <div className="text-2xl font-bold text-yellow-400">{summary.pending}</div>
            <div className="text-sm text-slate-400">Pending Review</div>
          </div>
          <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 text-center">
            <div className="text-2xl font-bold text-green-400">{summary.implemented}</div>
            <div className="text-sm text-slate-400">Implemented</div>
          </div>
        </div>
      )}
      <div className="space-y-3">
        {recommendations.map((r: any) => (
          <div key={r.id} className="bg-slate-800 rounded-lg p-4 border border-slate-700">
            <div className="flex justify-between items-start">
              <div>
                <div className="flex items-center space-x-2">
                  <h3 className="text-white font-semibold">{r.resource_name}</h3>
                  <span className={`text-xs ${priorityColors[r.priority] || 'text-slate-400'}`}>{r.priority}</span>
                </div>
                <p className="text-sm text-slate-400 mt-1">{r.reason}</p>
              </div>
              <span className={`px-2 py-0.5 rounded text-xs ${r.status === 'pending' ? 'bg-yellow-600' : r.status === 'implemented' ? 'bg-green-600' : r.status === 'approved' ? 'bg-blue-600' : 'bg-slate-600'} text-white`}>{r.status}</span>
            </div>
            <div className="mt-3 grid grid-cols-3 gap-4 text-sm">
              <div><span className="text-slate-400">Current:</span> <span className="text-white">{r.current_size} (${r.current_monthly_cost}/mo)</span></div>
              <div><span className="text-slate-400">Recommended:</span> <span className="text-green-400">{r.recommended_size} (${r.recommended_monthly_cost}/mo)</span></div>
              <div><span className="text-slate-400">Savings:</span> <span className="text-green-400">${r.monthly_savings}/mo (${r.annual_savings}/yr)</span></div>
            </div>
            <div className="mt-3 grid grid-cols-2 gap-4 text-xs text-slate-500">
              <div>Avg CPU: {r.avg_cpu_pct}% · P95 CPU: {r.p95_cpu_pct}%</div>
              <div>Avg Memory: {r.avg_memory_pct}% · P95 Memory: {r.p95_memory_pct}%</div>
            </div>
            {r.status === 'pending' && (
              <div className="mt-3 flex space-x-2">
                <button onClick={() => action(r.id, 'approve')} className="bg-blue-600 text-white px-3 py-1 rounded text-xs hover:bg-blue-700">Approve</button>
                <button onClick={() => action(r.id, 'dismiss')} className="bg-slate-600 text-white px-3 py-1 rounded text-xs hover:bg-slate-500">Dismiss</button>
              </div>
            )}
            {r.status === 'approved' && (
              <button onClick={() => action(r.id, 'implement')} className="mt-3 bg-green-600 text-white px-3 py-1 rounded text-xs hover:bg-green-700">Implement</button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function RightsizingResourceRegistration() {
  const [form, setForm] = useState({ name: '', resourceType: 'compute', size: 't3.large', monthlyCost: 100 });
  const handleRegister = async () => {
    const res = await apiClient.post('/api/v1/finops/rightsizing/resources', form);
    if (res.id) toast.success('Resource registered for analysis');
  };
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-white font-semibold mb-3">Register Resource</h3>
      <div className="grid grid-cols-2 gap-3">
        <input placeholder="Name" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} className="bg-slate-700 text-white p-2 rounded" />
        <select value={form.resourceType} onChange={e => setForm({ ...form, resourceType: e.target.value })} className="bg-slate-700 text-white p-2 rounded">
          <option value="compute">Compute</option><option value="database">Database</option><option value="storage">Storage</option>
        </select>
        <input placeholder="Size (e.g. t3.large)" value={form.size} onChange={e => setForm({ ...form, size: e.target.value })} className="bg-slate-700 text-white p-2 rounded" />
        <input type="number" placeholder="Monthly Cost" value={form.monthlyCost} onChange={e => setForm({ ...form, monthlyCost: Number(e.target.value) })} className="bg-slate-700 text-white p-2 rounded" />
      </div>
      <button onClick={handleRegister} className="mt-3 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 text-sm">Register</button>
    </div>
  );
}

function RightsizingSimulator() {
  const [currentSize, setCurrentSize] = useState('t3.large');
  const [targetSize, setTargetSize] = useState('t3.medium');
  const [monthlyCost, setMonthlyCost] = useState(68.64);
  const savingsMap: Record<string, number> = { 't3.large->t3.medium': 0.5, 't3.xlarge->t3.large': 0.5, 'm5.xlarge->m5.large': 0.5 };
  const key = `${currentSize}->${targetSize}`;
  const savingsPct = savingsMap[key] || 0.4;
  const savings = monthlyCost * savingsPct;
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-white font-semibold mb-3">Resize Simulator</h3>
      <div className="grid grid-cols-2 gap-3">
        <select value={currentSize} onChange={e => setCurrentSize(e.target.value)} className="bg-slate-700 text-white p-2 rounded">
          <option value="t3.large">t3.large</option><option value="t3.xlarge">t3.xlarge</option><option value="m5.xlarge">m5.xlarge</option>
        </select>
        <select value={targetSize} onChange={e => setTargetSize(e.target.value)} className="bg-slate-700 text-white p-2 rounded">
          <option value="t3.medium">t3.medium</option><option value="t3.large">t3.large</option><option value="m5.large">m5.large</option>
        </select>
        <input type="number" value={monthlyCost} onChange={e => setMonthlyCost(Number(e.target.value))} className="bg-slate-700 text-white p-2 rounded" />
      </div>
      <div className="mt-3 grid grid-cols-2 gap-3 text-sm bg-slate-700/50 rounded p-3">
        <div><span className="text-slate-400">Savings:</span> <span className="text-green-400">${savings.toFixed(2)}/mo</span></div>
        <div><span className="text-slate-400">Annual:</span> <span className="text-green-400">${(savings * 12).toFixed(2)}/yr</span></div>
        <div><span className="text-slate-400">New Cost:</span> <span className="text-white">${(monthlyCost - savings).toFixed(2)}/mo</span></div>
        <div><span className="text-slate-400">Reduction:</span> <span className="text-green-400">{(savingsPct * 100).toFixed(0)}%</span></div>
      </div>
    </div>
  );
}

function RightsizingSavingsSummary({ recommendations }: { recommendations: any[] }) {
  const totalSavings = recommendations.reduce((s: number, r: any) => s + (r.monthly_savings || 0), 0);
  const implemented = recommendations.filter((r: any) => r.status === 'implemented').length;
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-white font-semibold mb-3">Savings Summary</h3>
      <div className="grid grid-cols-3 gap-4 text-sm">
        <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Monthly</span><div className="text-green-400 font-bold">${totalSavings}</div></div>
        <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Annual</span><div className="text-green-400 font-bold">${totalSavings * 12}</div></div>
        <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Implemented</span><div className="text-white font-bold">{implemented}/{recommendations.length}</div></div>
      </div>
    </div>
  );
}

function RightsizingUtilizationChart({ recommendations }: { recommendations: any[] }) {
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-white font-semibold mb-3">Resource Utilization Overview</h3>
      {recommendations.slice(0, 5).map((r: any, i: number) => {
        const cpuBar = Math.min(r.avg_cpu_pct || 30, 100);
        const memBar = Math.min(r.avg_memory_pct || 40, 100);
        return (
          <div key={i} className="mb-3">
            <div className="flex justify-between text-sm mb-1">
              <span className="text-slate-300">{r.resource_name}</span>
              <span className="text-slate-400">CPU: {cpuBar}% | Mem: {memBar}%</span>
            </div>
            <div className="w-full bg-slate-700 rounded-full h-3 flex">
              <div className="bg-blue-500 h-3 rounded-l-full" style={{ width: `${cpuBar}%` }} />
              <div className="bg-purple-500 h-3 rounded-r-full" style={{ width: `${memBar}%` }} />
            </div>
          </div>
        );
      })}
    </div>
  );
}

function RightsizingFilterBar({ onFilter }: { onFilter: (filters: any) => void }) {
  const [priority, setPriority] = useState('');
  const [status, setStatus] = useState('');
  return (
    <div className="flex gap-3 flex-wrap items-end">
      <div>
        <label className="block text-xs text-slate-400 mb-1">Priority</label>
        <select value={priority} onChange={e => { setPriority(e.target.value); onFilter({ priority: e.target.value, status }); }} className="bg-slate-800 text-white px-3 py-1.5 rounded border border-slate-700 text-sm">
          <option value="">All</option><option value="critical">Critical</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option>
        </select>
      </div>
      <div>
        <label className="block text-xs text-slate-400 mb-1">Status</label>
        <select value={status} onChange={e => { setStatus(e.target.value); onFilter({ priority, status: e.target.value }); }} className="bg-slate-800 text-white px-3 py-1.5 rounded border border-slate-700 text-sm">
          <option value="">All</option><option value="pending">Pending</option><option value="approved">Approved</option><option value="implemented">Implemented</option>
        </select>
      </div>
      <button onClick={() => { setPriority(''); setStatus(''); onFilter({}); }} className="px-3 py-1.5 bg-slate-700 text-white rounded text-sm hover:bg-slate-600">Clear</button>
    </div>
  );
}
