import { useState, useEffect } from 'react';
import { apiClient } from '../../lib/api';

export default function ArbitrageSavingsGoal({ opportunities }: { opportunities: any[] }) {
  const totalSavings = opportunities.reduce((s: number, o: any) => s + o.savings, 0);
  const goal = 5000;
  const pct = Math.min(totalSavings / goal * 100, 100);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-white font-semibold mb-3">Savings Goal Progress</h3>
      <div className="flex justify-between text-sm mb-2"><span className="text-slate-400">Current</span><span className="text-green-400">${totalSavings}/mo</span></div>
      <div className="flex justify-between text-sm mb-3"><span className="text-slate-400">Target</span><span className="text-white">${goal}/mo</span></div>
      <div className="w-full bg-slate-700 rounded-full h-4"><div className="bg-green-500 h-4 rounded-full" style={{ width: `${pct}%` }} /></div>
      <p className="text-xs text-slate-400 mt-2">{pct.toFixed(0)}% of target achieved</p>
    </div>
  );
}

function DiscountArbitrage() {
  const [workloads, setWorkloads] = useState<any[]>([]);
  const [comparisons, setComparisons] = useState<any[]>([]);
  const [savings, setSavings] = useState<any>(null);

  useEffect(() => {
    apiClient.get('/api/v1/finops/arbitrage/workloads').then(r => setWorkloads(r.workloads || [])).catch(() => {});
    apiClient.get('/api/v1/finops/arbitrage/comparisons').then(r => setComparisons(r.comparisons || [])).catch(() => {});
    apiClient.get('/api/v1/finops/arbitrage/savings').then(r => setSavings(r)).catch(() => {});
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Multi-Cloud Discount Arbitrage</h1>
          <p className="text-slate-400">Compare effective pricing across providers after committed discounts</p>
        </div>
      </div>
      {savings && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 text-center">
            <div className="text-2xl font-bold text-white">{savings.total_workloads}</div>
            <div className="text-sm text-slate-400">Workloads</div>
          </div>
          <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 text-center">
            <div className="text-2xl font-bold text-red-400">${savings.total_current_monthly?.toLocaleString()}</div>
            <div className="text-sm text-slate-400">Current Spend</div>
          </div>
          <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 text-center">
            <div className="text-2xl font-bold text-green-400">${savings.total_potential_monthly_savings?.toLocaleString()}</div>
            <div className="text-sm text-slate-400">Potential Savings</div>
          </div>
          <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 text-center">
            <div className="text-2xl font-bold text-green-400">{savings.savings_pct}%</div>
            <div className="text-sm text-slate-400">Savings %</div>
          </div>
        </div>
      )}
      <div className="grid gap-4">
        {comparisons.map((c: any) => c.best_option && (
          <div key={c.workload_id} className="bg-slate-800 rounded-lg p-4 border border-slate-700">
            <h3 className="text-white font-semibold">{c.workload_name}</h3>
            <p className="text-sm text-slate-400">Current: {c.current_provider} — ${c.current_monthly_cost}/mo</p>
            <div className="mt-2 bg-slate-700/50 rounded p-3">
              <div className="flex justify-between items-center">
                <div>
                  <span className="text-green-400 font-bold">{c.best_option.provider_name}</span>
                  <span className="text-slate-400 text-sm ml-2">({c.best_option.discount_type})</span>
                </div>
                <div className="text-right">
                  <div className="text-white font-semibold">${c.best_option.effective_monthly_cost}/mo</div>
                  <div className="text-green-400 text-sm">Save ${c.potential_monthly_savings}/mo ({c.potential_savings_pct}%)</div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function SpotVsOnDemandTable() {
  const comparisons = [
    { instance: 'm5.large', spot: 0.034, od: 0.096, savings: 64 },
    { instance: 'm5.xlarge', spot: 0.076, od: 0.192, savings: 60 },
    { instance: 'c5.2xlarge', spot: 0.175, od: 0.340, savings: 49 },
    { instance: 'r5.large', spot: 0.049, od: 0.126, savings: 61 },
  ];
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-white font-semibold mb-3">Spot vs On-Demand Pricing</h3>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-slate-400 border-b border-slate-700">
            <th className="text-left py-2">Instance</th><th className="text-right py-2">Spot ($/hr)</th><th className="text-right py-2">On-Demand ($/hr)</th><th className="text-right py-2">Savings</th>
          </tr>
        </thead>
        <tbody>
          {comparisons.map((c, i) => (
            <tr key={i} className="border-b border-slate-700">
              <td className="py-2 text-white">{c.instance}</td>
              <td className="py-2 text-right text-emerald-400">${c.spot.toFixed(3)}</td>
              <td className="py-2 text-right text-white">${c.od.toFixed(3)}</td>
              <td className="py-2 text-right text-green-400">{c.savings}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ArbitrageBuyingGuide() {
  const purchaseOptions = [
    { term: '1-Year Standard', savings: 30, flexibility: 'Very Low', risk: 'Low' },
    { term: '1-Year Convertible', savings: 22, flexibility: 'Medium', risk: 'Low' },
    { term: '3-Year Standard', savings: 50, flexibility: 'Very Low', risk: 'Medium' },
    { term: '3-Year Convertible', savings: 40, flexibility: 'Medium', risk: 'Medium' },
    { term: 'Spot (No Commitment)', savings: 65, flexibility: 'Very High', risk: 'High' },
    { term: 'On-Demand (No Commitment)', savings: 0, flexibility: 'Highest', risk: 'None' },
  ];
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-white font-semibold mb-3">Purchase Option Matrix</h3>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-slate-400 border-b border-slate-700">
            <th className="text-left py-2">Term</th><th className="text-right py-2">Savings</th><th className="text-right py-2">Flexibility</th><th className="text-right py-2">Risk</th>
          </tr>
        </thead>
        <tbody>
          {purchaseOptions.map((o, i) => (
            <tr key={i} className="border-b border-slate-700">
              <td className="py-2 text-white">{o.term}</td>
              <td className="py-2 text-right text-green-400">{o.savings}%</td>
              <td className="py-2 text-right text-slate-300">{o.flexibility}</td>
              <td className={`py-2 text-right ${o.risk === 'High' ? 'text-red-400' : o.risk === 'Medium' ? 'text-yellow-400' : 'text-green-400'}`}>{o.risk}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ArbitrageOpportunityAlert() {
  const opportunities = [
    { description: 'Convert 3-year RIs to convertible in region us-east-1', savings: 1200, risk: 'low', id: '1' },
    { description: 'Replace high-cost RDS instances with Compute Savings Plan', savings: 3500, risk: 'medium', id: '2' },
    { description: 'Use spot for stateless data pipeline workers', savings: 4800, risk: 'high', id: '3' },
  ];
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-white font-semibold mb-3">Arbitrage Opportunities</h3>
      {opportunities.map((o, i) => (
        <div key={i} className="flex items-center justify-between py-2 border-b border-slate-700 last:border-0">
          <div className="flex-1">
            <p className="text-white text-sm">{o.description}</p>
            <span className={`text-xs ${o.risk === 'low' ? 'text-green-400' : o.risk === 'medium' ? 'text-yellow-400' : 'text-red-400'}`}>{o.risk} risk</span>
          </div>
          <span className="text-green-400 text-sm font-semibold ml-3">${o.savings}/mo</span>
        </div>
      ))}
    </div>
  );
}

function ArbitrageFilterBar({ onFilter }: { onFilter: (filters: any) => void }) {
  const [type, setType] = useState('');
  const [region, setRegion] = useState('');
  return (
    <div className="flex gap-3 flex-wrap items-end">
      <div>
        <label className="block text-xs text-slate-400 mb-1">Discount Type</label>
        <select value={type} onChange={e => { setType(e.target.value); onFilter({ type: e.target.value, region }); }} className="bg-slate-800 text-white px-3 py-1.5 rounded border border-slate-700 text-sm">
          <option value="">All</option><option value="ri">Reserved Instances</option><option value="savings_plan">Savings Plan</option><option value="spot">Spot</option>
        </select>
      </div>
      <div>
        <label className="block text-xs text-slate-400 mb-1">Region</label>
        <select value={region} onChange={e => { setRegion(e.target.value); onFilter({ type, region: e.target.value }); }} className="bg-slate-800 text-white px-3 py-1.5 rounded border border-slate-700 text-sm">
          <option value="">All</option><option value="us-east-1">us-east-1</option><option value="eu-west-1">eu-west-1</option><option value="ap-south-1">ap-south-1</option>
        </select>
      </div>
      <button onClick={() => { setType(''); setRegion(''); onFilter({}); }} className="px-3 py-1.5 bg-slate-700 text-white rounded text-sm hover:bg-slate-600">Clear</button>
    </div>
  );
}
