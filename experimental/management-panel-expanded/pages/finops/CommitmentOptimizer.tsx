import { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { apiClient } from '../../lib/api';

function CommitmentAnalysisTab() {
  const [coverage, setCoverage] = useState<any[]>([]);
  const [analysis, setAnalysis] = useState<any>(null);

  useEffect(() => {
    apiClient.get('/api/v1/finops/commitment/coverage-gaps').then(d => setCoverage(d.gaps || d)).catch(() => {});
    apiClient.post('/api/v1/finops/commitment/analyze').then(d => setAnalysis(d)).catch(() => {});
  }, []);

  return (
    <div className="space-y-6">
      {analysis && (
        <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
          <h3 className="text-white font-semibold mb-3">Analysis Results</h3>
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div><span className="text-slate-400">Current Coverage:</span> <span className="text-white">{analysis.current_coverage}%</span></div>
            <div><span className="text-slate-400">Recommended Coverage:</span> <span className="text-green-400">{analysis.recommended_coverage}%</span></div>
            <div><span className="text-slate-400">Potential Savings:</span> <span className="text-green-400">${analysis.potential_savings}/mo</span></div>
          </div>
          <p className="text-slate-300 mt-2">{analysis.recommendation}</p>
        </div>
      )}
      <h3 className="text-white font-semibold">Coverage Gaps</h3>
      <div className="grid gap-3">
        {coverage.map((g: any, i: number) => (
          <div key={i} className="bg-slate-800 rounded-lg p-3 border border-slate-700">
            <div className="flex justify-between">
              <span className="text-white font-medium">{g.service}</span>
              <span className="text-red-400">{g.gap_pct}% gap</span>
            </div>
            <div className="mt-2 w-full bg-slate-700 rounded-full h-2">
              <div className="bg-green-500 h-2 rounded-full" style={{ width: `${g.coverage_pct}%` }} />
            </div>
            <div className="flex justify-between mt-1 text-sm text-slate-400">
              <span>{g.coverage_pct}% covered</span>
              <span>${g.potential_savings}/mo potential savings</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function CommitmentHistoryTab() {
  const [history] = useState<any[]>([
    { action: 'Implemented 1yr RI for EC2', date: '2026-05-15', savings: 450 },
    { action: 'Expired 3yr RI for RDS', date: '2026-05-10', savings: -320 },
    { action: 'Purchased Savings Plan', date: '2026-05-01', savings: 280 },
    { action: 'Modified commitment scope', date: '2026-04-20', savings: 0 },
  ]);

  return (
    <div className="space-y-3">
      <h3 className="text-white font-semibold">Commitment History</h3>
      {history.map((h: any, i: number) => (
        <div key={i} className="bg-slate-800 rounded-lg p-3 border border-slate-700 flex justify-between items-center">
          <div>
            <p className="text-white">{h.action}</p>
            <p className="text-slate-400 text-sm">{h.date}</p>
          </div>
          <span className={h.savings >= 0 ? 'text-green-400' : 'text-red-400'}>
            {h.savings >= 0 ? '+' : ''}${h.savings}/mo
          </span>
        </div>
      ))}
    </div>
  );
}

function CommitmentCoverageChart() {
  const services = [
    { name: 'EC2', covered: 72, total: 100 },
    { name: 'RDS', covered: 55, total: 100 },
    { name: 'Lambda', covered: 0, total: 100 },
    { name: 'ElastiCache', covered: 40, total: 100 },
    { name: 'S3', covered: 30, total: 100 },
  ];
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-white font-semibold mb-3">Service Coverage Breakdown</h3>
      {services.map((s, i) => (
        <div key={i} className="mb-3">
          <div className="flex justify-between text-sm mb-1">
            <span className="text-slate-300">{s.name}</span>
            <span className="text-slate-400">{s.covered}% covered</span>
          </div>
          <div className="w-full bg-slate-700 rounded-full h-3">
            <div className="bg-blue-500 h-3 rounded-full" style={{ width: `${s.covered}%` }} />
          </div>
        </div>
      ))}
    </div>
  );
}

function ProviderComparisonTable() {
  const providers = [
    { name: 'AWS', monthly: 5200, coverage: 72, savings: 1800, utilization: 85 },
    { name: 'Azure', monthly: 3800, coverage: 65, savings: 1200, utilization: 78 },
    { name: 'GCP', monthly: 2100, coverage: 58, savings: 900, utilization: 92 },
  ];
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-white font-semibold mb-3">Provider Comparison</h3>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-slate-400 border-b border-slate-700">
            <th className="text-left py-2">Provider</th>
            <th className="text-right py-2">Monthly</th>
            <th className="text-right py-2">Coverage</th>
            <th className="text-right py-2">Savings</th>
            <th className="text-right py-2">Utilization</th>
          </tr>
        </thead>
        <tbody>
          {providers.map((p, i) => (
            <tr key={i} className="border-b border-slate-700">
              <td className="py-2 text-white">{p.name}</td>
              <td className="py-2 text-right text-white">${p.monthly}</td>
              <td className="py-2 text-right text-blue-400">{p.coverage}%</td>
              <td className="py-2 text-right text-green-400">${p.savings}</td>
              <td className="py-2 text-right text-yellow-400">{p.utilization}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function CommitmentOptimizer() {
  const [activeTab, setActiveTab] = useState('recommendations');
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [commitments, setCommitments] = useState<any[]>([]);
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      apiClient.get('/api/v1/finops/commitment/recommendations').catch(() => ({ recommendations: [] })),
      apiClient.get('/api/v1/finops/commitment/active').catch(() => ({ commitments: [] })),
      apiClient.get('/api/v1/finops/commitment/summary').catch(() => ({})),
    ]).then(([recRes, comRes, sumRes]) => {
      setRecommendations(recRes.recommendations || []);
      setCommitments(comRes.commitments || []);
      setSummary(sumRes);
    }).finally(() => setLoading(false));
  }, []);

  const implement = async (id: string) => {
    const res = await apiClient.post('/api/v1/finops/commitment/recommendations/implement', { recommendation_id: id });
    if (res.success) { toast.success('Commitment purchased!'); setActiveTab('commitments'); }
  };

  const tabs = ['recommendations', 'commitments', 'summary', 'analysis', 'history', 'coverage', 'providers'];

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Commitment Discount Optimizer</h1>
          <p className="text-slate-400">Analyze usage and recommend reserved instances / savings plans</p>
        </div>
      </div>
      <div className="flex space-x-2 border-b border-slate-700 pb-2 overflow-x-auto">
        {tabs.map(tab => (
          <button key={tab} onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 rounded-t text-sm whitespace-nowrap ${activeTab === tab ? 'bg-slate-700 text-white' : 'text-slate-400 hover:text-white'}`}>
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>
      {loading ? <p className="text-slate-400">Loading...</p> : (
        <>
          {activeTab === 'recommendations' && (
            <div className="grid gap-4">
              <div className="flex gap-2 mb-2">
                <input placeholder="Search..." className="bg-slate-800 text-white px-3 py-1.5 rounded border border-slate-700 text-sm w-64" />
                <select className="bg-slate-800 text-white px-3 py-1.5 rounded border border-slate-700 text-sm">
                  <option>All Status</option><option>Pending</option><option>Implemented</option><option>Dismissed</option>
                </select>
                <select className="bg-slate-800 text-white px-3 py-1.5 rounded border border-slate-700 text-sm">
                  <option>All Providers</option><option>AWS</option><option>Azure</option><option>GCP</option>
                </select>
              </div>
              {recommendations.length === 0 && <p className="text-slate-500">Generate recommendations first.</p>}
              {recommendations.map((r: any) => (
                <div key={r.id} className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="text-white font-semibold">{r.service} — {r.type}</h3>
                      <p className="text-slate-400 text-sm">{r.term} · {r.payment} · {r.confidence} confidence</p>
                    </div>
                    <span className={`px-2 py-1 rounded text-xs ${r.status === 'pending' ? 'bg-yellow-600' : 'bg-green-600'} text-white`}>{r.status}</span>
                  </div>
                  <div className="mt-3 grid grid-cols-3 gap-4 text-sm">
                    <div><span className="text-slate-400">On-Demand:</span> <span className="text-white">${r.on_demand_monthly}/mo</span></div>
                    <div><span className="text-slate-400">Commitment:</span> <span className="text-white">${r.monthly_cost}/mo</span></div>
                    <div><span className="text-slate-400">Savings:</span> <span className="text-green-400">${r.monthly_savings}/mo ({r.savings_pct}%)</span></div>
                  </div>
                  {r.status === 'pending' && (
                    <button onClick={() => implement(r.id)} className="mt-3 bg-green-600 text-white px-4 py-1.5 rounded text-sm hover:bg-green-700">Implement</button>
                  )}
                </div>
              ))}
              <div className="flex justify-between items-center text-sm text-slate-400 mt-4">
                <span>Showing {recommendations.length} recommendations</span>
                <div className="flex gap-2">
                  <button className="px-3 py-1 bg-slate-700 rounded hover:bg-slate-600">Previous</button>
                  <button className="px-3 py-1 bg-slate-700 rounded hover:bg-slate-600">Next</button>
                </div>
              </div>
            </div>
          )}
          {activeTab === 'commitments' && (
            <div className="grid gap-4">
              {commitments.map((c: any) => (
                <div key={c.id} className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                  <div className="flex justify-between">
                    <h3 className="text-white font-semibold">{c.service} · {c.type}</h3>
                    <span className="text-green-400">{c.utilization_pct}% utilized</span>
                  </div>
                  <div className="mt-2 grid grid-cols-3 gap-4 text-sm">
                    <div><span className="text-slate-400">Term:</span> <span className="text-white">{c.term}</span></div>
                    <div><span className="text-slate-400">Monthly:</span> <span className="text-white">${c.monthly_cost}</span></div>
                    <div><span className="text-slate-400">Savings:</span> <span className="text-green-400">${c.estimated_monthly_savings}/mo</span></div>
                  </div>
                </div>
              ))}
            </div>
          )}
          {activeTab === 'summary' && summary && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[{ label: 'Active Commitments', value: summary.active_commitments, color: 'text-blue-400' },
                { label: 'Monthly Savings', value: `$${summary.total_monthly_savings}`, color: 'text-green-400' },
                { label: 'Annual Savings', value: `$${summary.projected_annual_savings}`, color: 'text-green-400' },
                { label: 'Avg Utilization', value: `${summary.avg_utilization}%`, color: 'text-yellow-400' },
              ].map((stat, i) => (
                <div key={i} className="bg-slate-800 rounded-lg p-4 border border-slate-700 text-center">
                  <div className={`text-2xl font-bold ${stat.color}`}>{stat.value}</div>
                  <div className="text-sm text-slate-400 mt-1">{stat.label}</div>
                </div>
              ))}
            </div>
          )}
          {activeTab === 'analysis' && <CommitmentAnalysisTab />}
          {activeTab === 'history' && <CommitmentHistoryTab />}
          {activeTab === 'coverage' && <CommitmentCoverageChart />}
          {activeTab === 'providers' && <ProviderComparisonTable />}
        </>
      )}
    </div>
  );
}

function CommitmentRenewalModal({ commitment, onClose, onRenew }: { commitment: any; onClose: () => void; onRenew: (id: string, term: string) => void }) {
  const [term, setTerm] = useState('1yr');
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-slate-800 rounded-lg p-6 border border-slate-700 w-96" onClick={e => e.stopPropagation()}>
        <h3 className="text-white font-semibold mb-4">Renew Commitment</h3>
        <p className="text-slate-300 text-sm mb-4">{commitment?.service} — {commitment?.type}</p>
        <label className="block text-sm text-slate-400 mb-1">Term</label>
        <select value={term} onChange={e => setTerm(e.target.value)} className="w-full bg-slate-700 text-white px-3 py-2 rounded border border-slate-600 mb-4">
          <option value="1yr">1 Year</option>
          <option value="3yr">3 Years</option>
          <option value="monthly">Monthly</option>
        </select>
        <div className="bg-slate-700 rounded p-3 mb-4 text-sm">
          <div className="flex justify-between text-slate-300"><span>Current savings</span><span>$180/mo</span></div>
          <div className="flex justify-between text-slate-300"><span>Renewal savings</span><span>$165/mo</span></div>
          <div className="flex justify-between text-green-400 font-medium"><span>Net difference</span><span>-$15/mo</span></div>
        </div>
        <div className="flex justify-end gap-2">
          <button onClick={onClose} className="px-4 py-2 bg-slate-700 text-white rounded hover:bg-slate-600 text-sm">Cancel</button>
          <button onClick={() => { onRenew(commitment?.id, term); onClose(); }} className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 text-sm">Renew</button>
        </div>
      </div>
    </div>
  );
}

function CommitmentFilterBar({ onFilter }: { onFilter: (filters: any) => void }) {
  const [provider, setProvider] = useState('');
  const [status, setStatus] = useState('');
  const [minSavings, setMinSavings] = useState('');
  return (
    <div className="flex gap-3 flex-wrap items-end">
      <div>
        <label className="block text-xs text-slate-400 mb-1">Provider</label>
        <select value={provider} onChange={e => { setProvider(e.target.value); onFilter({ provider: e.target.value, status, minSavings }); }} className="bg-slate-800 text-white px-3 py-1.5 rounded border border-slate-700 text-sm">
          <option value="">All</option><option value="aws">AWS</option><option value="azure">Azure</option><option value="gcp">GCP</option>
        </select>
      </div>
      <div>
        <label className="block text-xs text-slate-400 mb-1">Status</label>
        <select value={status} onChange={e => { setStatus(e.target.value); onFilter({ provider, status: e.target.value, minSavings }); }} className="bg-slate-800 text-white px-3 py-1.5 rounded border border-slate-700 text-sm">
          <option value="">All</option><option value="active">Active</option><option value="pending">Pending</option><option value="expired">Expired</option>
        </select>
      </div>
      <div>
        <label className="block text-xs text-slate-400 mb-1">Min Savings ($)</label>
        <input type="number" value={minSavings} onChange={e => { setMinSavings(e.target.value); onFilter({ provider, status, minSavings: e.target.value }); }} className="bg-slate-800 text-white px-3 py-1.5 rounded border border-slate-700 text-sm w-24" />
      </div>
      <button onClick={() => { setProvider(''); setStatus(''); setMinSavings(''); onFilter({}); }} className="px-3 py-1.5 bg-slate-700 text-white rounded text-sm hover:bg-slate-600">Clear</button>
    </div>
  );
}

function CommitmentExportButton({ data, filename }: { data: any[]; filename: string }) {
  const handleExport = () => {
    const json = JSON.stringify(data, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${filename}.json`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('Commitment data exported');
  };
  return (
    <button onClick={handleExport} className="px-4 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 flex items-center gap-2">
      Export JSON
    </button>
  );
}

function CommitmentUtilizationGauge({ pct }: { pct: number }) {
  const color = pct >= 80 ? 'text-green-400' : pct >= 60 ? 'text-yellow-400' : 'text-red-400';
  const strokeColor = pct >= 80 ? '#4ade80' : pct >= 60 ? '#facc15' : '#f87171';
  return (
    <div className="flex flex-col items-center bg-slate-800 rounded-lg p-4 border border-slate-700">
      <svg width="80" height="80" viewBox="0 0 120 120">
        <circle cx="60" cy="60" r="54" fill="none" stroke="#334155" strokeWidth="8" />
        <circle cx="60" cy="60" r="54" fill="none" stroke={strokeColor} strokeWidth="8" strokeDasharray={`${(pct / 100) * 339.292} 339.292`} transform="rotate(-90 60 60)" />
        <text x="60" y="60" textAnchor="middle" dominantBaseline="central" fill="white" fontSize="20" fontWeight="bold">{pct}%</text>
      </svg>
      <span className={`text-sm mt-2 ${color}`}>Utilization</span>
    </div>
  );
}
