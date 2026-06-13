import { useState, useEffect } from 'react';
import { apiClient } from '../../lib/api';

const reportTypes = ['executive_summary', 'cost_breakdown', 'savings_opportunity', 'budget_vs_actual', 'showback', 'chargeback', 'commitment_utilization', 'waste_analysis', 'forecast', 'compliance', 'kpi_dashboard'];

export default function FinopsReporting() {
  const [reports, setReports] = useState<any[]>([]);
  const [summary, setSummary] = useState<any>(null);
  const [selectedReport, setSelectedReport] = useState<any>(null);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    apiClient.get('/api/v1/finops/reports/summary').then(r => setSummary(r)).catch(() => {});
    apiClient.get('/api/v1/finops/reports').then(r => setReports(r.reports || [])).catch(() => {});
  }, []);

  const generate = async (type: string) => {
    setGenerating(true);
    const res = await apiClient.post('/api/v1/finops/reports/generate', { report_type: type, period: 'monthly' });
    if (res.id) {
      setReports([res, ...reports]);
      setSelectedReport(res);
    }
    setGenerating(false);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">FinOps Reporting & Compliance</h1>
          <p className="text-slate-400">Pre-built FinOps dashboards and audit-ready reports</p>
        </div>
      </div>
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 text-center">
            <div className="text-2xl font-bold text-white">{summary.total_reports}</div>
            <div className="text-sm text-slate-400">Reports Generated</div>
          </div>
          <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 text-center">
            <div className="text-2xl font-bold text-white">{summary.kpi_count}</div>
            <div className="text-sm text-slate-400">KPIs Tracked</div>
          </div>
          <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 text-center">
            <div className="text-2xl font-bold text-green-400">{summary.kpis_on_track}</div>
            <div className="text-sm text-slate-400">KPIs On Track</div>
          </div>
          <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 text-center">
            <div className="text-2xl font-bold text-blue-400">{summary.total_allocations}</div>
            <div className="text-sm text-slate-400">Allocation Tags</div>
          </div>
        </div>
      )}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
        {reportTypes.map((type) => (
          <button key={type} onClick={() => generate(type)} disabled={generating}
            className="bg-slate-800 hover:bg-slate-700 text-white p-3 rounded-lg border border-slate-700 text-sm transition disabled:opacity-50">
            {type.replace(/_/g, ' ')}
          </button>
        ))}
      </div>
      {selectedReport && selectedReport.data && (
        <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-white font-semibold">{selectedReport.type.replace(/_/g, ' ').toUpperCase()} Report</h3>
            <span className="text-xs text-slate-400">{selectedReport.period} · {selectedReport.format}</span>
          </div>
          <pre className="text-xs text-slate-300 overflow-auto max-h-96">{JSON.stringify(selectedReport.data, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

function FinopsReportFilterBar({ onFilter }: { onFilter: (filters: any) => void }) {
  const [bucket, setBucket] = useState('');
  const [account, setAccount] = useState('');
  return (
    <div className="flex gap-3 flex-wrap items-end">
      <div>
        <label className="block text-xs text-slate-400 mb-1">Cost Bucket</label>
        <select value={bucket} onChange={e => { setBucket(e.target.value); onFilter({ bucket: e.target.value, account }); }} className="bg-slate-800 text-white px-3 py-1.5 rounded border border-slate-700 text-sm">
          <option value="">All</option><option value="compute">Compute</option><option value="storage">Storage</option><option value="network">Network</option><option value="database">Database</option>
        </select>
      </div>
      <div>
        <label className="block text-xs text-slate-400 mb-1">Account</label>
        <select value={account} onChange={e => { setAccount(e.target.value); onFilter({ bucket, account: e.target.value }); }} className="bg-slate-800 text-white px-3 py-1.5 rounded border border-slate-700 text-sm">
          <option value="">All</option><option value="prod">Production</option><option value="staging">Staging</option><option value="dev">Development</option>
        </select>
      </div>
      <button onClick={() => { setBucket(''); setAccount(''); onFilter({}); }} className="px-3 py-1.5 bg-slate-700 text-white rounded text-sm hover:bg-slate-600">Clear</button>
    </div>
  );
}

function FinopsComplianceCard() {
  const checks = [
    { name: 'Budget Alerts Configured', pass: true },
    { name: 'Anomaly Detection Active', pass: true },
    { name: 'Tagging Policy Enforced', pass: false },
    { name: 'Rightsizing Recommendations Enabled', pass: true },
    { name: 'Cost Allocation Tags Present', pass: true },
    { name: 'Scheduled Reports Configured', pass: false },
  ];
  const passed = checks.filter(c => c.pass).length;
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-white font-semibold mb-3">FinOps Compliance</h3>
      <div className="text-center mb-4">
        <span className="text-3xl font-bold text-emerald-400">{passed}/{checks.length}</span>
        <span className="text-slate-400 ml-2">checks passed</span>
      </div>
      {checks.map((c, i) => (
        <div key={i} className="flex items-center justify-between py-1.5 border-b border-slate-700 last:border-0">
          <span className="text-sm text-slate-300">{c.name}</span>
          <span className={`text-xs ${c.pass ? 'text-green-400' : 'text-red-400'}`}>{c.pass ? '✅' : '❌'}</span>
        </div>
      ))}
    </div>
  );
}

function FinopsChargebackTable() {
  const teams = [
    { team: 'Platform Engineering', cost: 18450, percentage: 37 },
    { team: 'Data Science', cost: 12200, percentage: 24 },
    { team: 'Web Team', cost: 9800, percentage: 20 },
    { team: 'Mobile Team', cost: 6700, percentage: 13 },
    { team: 'DevTools', cost: 3100, percentage: 6 },
  ];
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-white font-semibold mb-3">Chargeback Summary</h3>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-slate-400 border-b border-slate-700">
            <th className="text-left py-2">Team</th><th className="text-right py-2">Monthly Cost</th><th className="text-right py-2">Share</th>
          </tr>
        </thead>
        <tbody>
          {teams.map((t, i) => (
            <tr key={i} className="border-b border-slate-700">
              <td className="py-2 text-white">{t.team}</td>
              <td className="py-2 text-right text-white">${t.cost.toLocaleString()}</td>
              <td className="py-2 text-right text-slate-300">{t.percentage}%</td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="mt-3 pt-3 border-t border-slate-700 text-right text-sm">
        <span className="text-slate-400">Total: </span><span className="text-white font-semibold">${teams.reduce((s, t) => s + t.cost, 0).toLocaleString()}</span>
      </div>
    </div>
  );
}

function FinopsBudgetVsActualChart({ budgets }: { budgets: any[] }) {
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-white font-semibold mb-3">Budget vs Actual</h3>
      <table className="w-full text-sm">
        <thead><tr className="text-slate-400 border-b border-slate-700"><th className="text-left py-2">Team</th><th className="text-right py-2">Budget</th><th className="text-right py-2">Actual</th><th className="text-right py-2">Variance</th></tr></thead>
        <tbody>{budgets.map((b: any, i: number) => {
          const variance = b.budget - b.actual; const isOver = variance < 0;
          return (<tr key={i} className="border-b border-slate-700"><td className="py-2 text-white">{b.team}</td><td className="py-2 text-right text-white">${b.budget.toLocaleString()}</td><td className="py-2 text-right text-white">${b.actual.toLocaleString()}</td><td className={`py-2 text-right ${isOver ? 'text-red-400' : 'text-green-400'}`}>{isOver ? '+' : ''}{variance.toLocaleString()}</td></tr>);
        })}</tbody>
      </table>
    </div>
  );
}

function FinopsForecastExport() {
  const handleExportCSV = () => {
    const csv = 'month,cost,forecast\nJan,45000,46000\nFeb,44000,45500\nMar,46500,47000';
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = 'finops_forecast.csv'; a.click();
    toast.success('Forecast CSV downloaded');
  };
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-white font-semibold mb-3">Export Forecast</h3>
      <p className="text-slate-400 text-sm mb-3">Download forecast data as CSV for external analysis.</p>
      <button onClick={handleExportCSV} className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 text-sm">Download CSV</button>
    </div>
  );
}
