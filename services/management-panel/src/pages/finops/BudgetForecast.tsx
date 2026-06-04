import { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { apiClient } from '../../lib/api';

export default function BudgetForecast() {
  const [budgets, setBudgets] = useState<any[]>([]);
  const [summary, setSummary] = useState<any>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ name: '', amount: 50000, period: 'monthly', scope: 'project' });

  useEffect(() => {
    apiClient.get('/api/v1/finops/budgets').then(r => setBudgets(r.budgets || [])).catch(() => {});
    apiClient.get('/api/v1/finops/budgets/summary').then(r => setSummary(r)).catch(() => {});
  }, []);

  const createBudget = async () => {
    const res = await apiClient.post('/api/v1/finops/budgets', form);
    if (res.id) { toast.success('Budget created!'); setBudgets([...budgets, res]); setShowCreate(false); }
  };

  const getStatusColor = (s: string) => s === 'exceeded' ? 'text-red-400' : s === 'at_risk' ? 'text-yellow-400' : 'text-green-400';

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Budget & Forecast Engine</h1>
          <p className="text-slate-400">Hierarchical budgets, forecast vs actual, what-if modeling</p>
        </div>
        <button onClick={() => setShowCreate(!showCreate)} className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
          {showCreate ? 'Cancel' : '+ New Budget'}
        </button>
      </div>
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 text-center">
            <div className="text-2xl font-bold text-white">{summary.total_budgets}</div>
            <div className="text-sm text-slate-400">Total Budgets</div>
          </div>
          <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 text-center">
            <div className="text-2xl font-bold text-white">${summary.total_budget_amount?.toLocaleString()}</div>
            <div className="text-sm text-slate-400">Total Budgeted</div>
          </div>
          <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 text-center">
            <div className="text-2xl font-bold text-yellow-400">{summary.at_risk}</div>
            <div className="text-sm text-slate-400">At Risk</div>
          </div>
          <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 text-center">
            <div className="text-2xl font-bold text-red-400">{summary.exceeded}</div>
            <div className="text-sm text-slate-400">Exceeded</div>
          </div>
        </div>
      )}
      {showCreate && (
        <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 space-y-3">
          <input placeholder="Budget name" value={form.name} onChange={e => setForm({...form, name: e.target.value})} className="w-full bg-slate-700 text-white p-2 rounded" />
          <div className="grid grid-cols-3 gap-3">
            <input type="number" placeholder="Amount" value={form.amount} onChange={e => setForm({...form, amount: +e.target.value})} className="bg-slate-700 text-white p-2 rounded" />
            <select value={form.period} onChange={e => setForm({...form, period: e.target.value})} className="bg-slate-700 text-white p-2 rounded">
              <option value="monthly">Monthly</option><option value="quarterly">Quarterly</option><option value="annual">Annual</option>
            </select>
            <select value={form.scope} onChange={e => setForm({...form, scope: e.target.value})} className="bg-slate-700 text-white p-2 rounded">
              <option value="org">Org</option><option value="team">Team</option><option value="project">Project</option>
            </select>
          </div>
          <button onClick={createBudget} className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700">Create Budget</button>
        </div>
      )}
      <div className="grid gap-4">
        {budgets.map((b: any) => {
          const pct = b.amount > 0 ? ((b.spent / b.amount) * 100).toFixed(1) : 0;
          return (
            <div key={b.id} className="bg-slate-800 rounded-lg p-4 border border-slate-700">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="text-white font-semibold">{b.name}</h3>
                  <p className="text-slate-400 text-sm">{b.scope} · {b.period} · {b.scope_id}</p>
                </div>
                <span className={`font-semibold ${getStatusColor(b.status)}`}>{b.status}</span>
              </div>
              <div className="mt-3">
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-slate-400">${b.spent?.toLocaleString()} / ${b.amount?.toLocaleString()}</span>
                  <span className="text-white">{pct}%</span>
                </div>
                <div className="w-full bg-slate-700 rounded-full h-2">
                  <div className={`h-2 rounded-full ${+pct >= 100 ? 'bg-red-500' : +pct >= 75 ? 'bg-yellow-500' : 'bg-green-500'}`} style={{ width: `${Math.min(+pct, 100)}%` }} />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function BudgetVarianceTable({ budgets }: { budgets: any[] }) {
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-white font-semibold mb-3">Variance Analysis</h3>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-slate-400 border-b border-slate-700">
            <th className="text-left py-2">Name</th><th className="text-right py-2">Budget</th><th className="text-right py-2">Actual</th><th className="text-right py-2">Variance</th><th className="text-right py-2">%</th>
          </tr>
        </thead>
        <tbody>
          {budgets.map((b: any) => {
            const variance = (b.spent || 0) - (b.amount || 0);
            const varPct = b.amount > 0 ? ((variance / b.amount) * 100).toFixed(1) : 0;
            return (
              <tr key={b.id} className="border-b border-slate-700">
                <td className="py-2 text-white">{b.name}</td>
                <td className="py-2 text-right text-white">${b.amount?.toLocaleString()}</td>
                <td className="py-2 text-right text-white">${b.spent?.toLocaleString()}</td>
                <td className={`py-2 text-right ${variance > 0 ? 'text-red-400' : 'text-green-400'}`}>${variance.toFixed(2)}</td>
                <td className={`py-2 text-right ${Number(varPct) > 0 ? 'text-red-400' : 'text-green-400'}`}>{varPct}%</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function BudgetAlertConfig({ budgetId }: { budgetId: string }) {
  const [thresholds, setThresholds] = useState({ p50: true, p75: true, p90: true, p100: true });
  const toggle = (key: string) => setThresholds({ ...thresholds, [key]: !(thresholds as any)[key] });
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-white font-semibold mb-3">Alert Thresholds: {budgetId}</h3>
      <div className="space-y-2">
        {[{ key: 'p50', label: '50% Spent' }, { key: 'p75', label: '75% Spent' }, { key: 'p90', label: '90% Spent' }, { key: 'p100', label: '100% Spent' }].map(t => (
          <label key={t.key} className="flex items-center space-x-2 text-sm text-slate-300">
            <input type="checkbox" checked={(thresholds as any)[t.key]} onChange={() => toggle(t.key)} className="rounded bg-slate-700 border-slate-600" />
            <span>{t.label}</span>
          </label>
        ))}
      </div>
      <button className="mt-3 bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700">Save Thresholds</button>
    </div>
  );
}

function BudgetAlertPanel({ budgets }: { budgets: any[] }) {
  const atRisk = budgets.filter((b: any) => b.spent_pct > 85);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-white font-semibold mb-3">Alerts ({atRisk.length} at risk)</h3>
      {atRisk.length === 0 && <p className="text-green-400 text-sm">All budgets within threshold</p>}
      {atRisk.map((b: any, i: number) => (
        <div key={i} className="flex justify-between items-center py-2 border-b border-slate-700 last:border-0">
          <span className="text-white text-sm">{b.name}</span>
          <span className="text-red-400 text-sm font-semibold">{b.spent_pct}% used</span>
        </div>
      ))}
    </div>
  );
}

function BudgetForecastChart({ budgetId }: { budgetId: string }) {
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'];
  const forecast = [44000, 46000, 47500, 49000, 51000, 52340];
  const budget = 50000;
  const maxVal = Math.max(...forecast, budget) * 1.2;
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-white font-semibold mb-3">Forecast vs Budget: {budgetId}</h3>
      <div className="relative h-40 flex items-end space-x-3">
        {forecast.map((v, i) => {
          const h = (v / maxVal) * 100;
          const isOver = v > budget;
          return (
            <div key={i} className="flex-1 flex flex-col items-center">
              <div className="text-xs text-slate-400 mb-1">${(v / 1000).toFixed(0)}k</div>
              <div className="w-full rounded-t" style={{ height: `${h}%`, backgroundColor: isOver ? '#ef4444' : '#22c55e' }} />
              <div className="text-xs text-slate-500 mt-1">{months[i]}</div>
            </div>
          );
        })}
        <div className="absolute left-0 right-0 top-[20%] border-t border-dashed border-yellow-500/50 text-xs text-yellow-500" style={{ top: `${(budget / maxVal) * 100}%` }}>Budget</div>
      </div>
    </div>
  );
}

function BudgetWhatIfSimulator({ budgetId }: { budgetId: string }) {
  const [pctChange, setPctChange] = useState(10);
  const baseBudget = 50000;
  const adjusted = baseBudget * (1 + pctChange / 100);
  const projected = 52340;
  const wouldExceed = projected > adjusted;
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-white font-semibold mb-3">What-If Simulator: {budgetId}</h3>
      <div className="flex items-center space-x-3 mb-4">
        <span className="text-slate-400 text-sm">Adjust budget:</span>
        <input type="range" min={-50} max={50} value={pctChange} onChange={e => setPctChange(Number(e.target.value))} className="flex-1" />
        <span className={`text-sm font-semibold ${pctChange >= 0 ? 'text-red-400' : 'text-green-400'}`}>{pctChange > 0 ? '+' : ''}{pctChange}%</span>
      </div>
      <div className="grid grid-cols-2 gap-3 text-sm">
        <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Base Budget</span><div className="text-white">${baseBudget.toLocaleString()}</div></div>
        <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Adjusted</span><div className="text-white">${adjusted.toLocaleString()}</div></div>
        <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Projected</span><div className="text-white">${projected.toLocaleString()}</div></div>
        <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Result</span><div className={wouldExceed ? 'text-red-400' : 'text-green-400'}>{wouldExceed ? 'Would Exceed' : 'Within Budget'}</div></div>
      </div>
    </div>
  );
}
