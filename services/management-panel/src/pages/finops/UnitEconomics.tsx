import { useState, useEffect } from 'react';
import { apiClient } from '../../lib/api';

export default function UnitEconomics() {
  const [overview, setOverview] = useState<any>(null);
  const [violations, setViolations] = useState<any[]>([]);
  const [customerId, setCustomerId] = useState('');
  const [customerData, setCustomerData] = useState<any>(null);

  useEffect(() => {
    apiClient.get('/api/v1/finops/unit/overview').then(r => setOverview(r)).catch(() => {});
    apiClient.get('/api/v1/finops/unit/violations').then(r => setViolations(r.violations || [])).catch(() => {});
  }, []);

  const loadCustomer = async () => {
    if (!customerId) return;
    const res = await apiClient.get(`/api/v1/finops/unit/customers/${customerId}`);
    setCustomerData(res);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Unit Economics Dashboard</h1>
          <p className="text-slate-400">Cost per customer, per transaction, per deployment</p>
        </div>
      </div>
      {overview?.overview && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Object.entries(overview.overview).map(([key, val]: any) => (
            <div key={key} className="bg-slate-800 rounded-lg p-4 border border-slate-700">
              <div className="text-sm text-slate-400">{key.replace(/_/g, ' ')}</div>
              <div className="text-xl font-bold text-white">${val.current}</div>
              <div className="text-xs text-slate-500">Trend: {val.trend} · 30d avg: ${val.avg_30d}</div>
            </div>
          ))}
        </div>
      )}
      <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
        <h3 className="text-white font-semibold mb-3">Customer Lookup</h3>
        <div className="flex space-x-2">
          <input value={customerId} onChange={e => setCustomerId(e.target.value)} placeholder="Enter customer ID" className="flex-1 bg-slate-700 text-white p-2 rounded" />
          <button onClick={loadCustomer} className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">Search</button>
        </div>
        {customerData && (
          <div className="mt-3 grid grid-cols-2 gap-4 text-sm">
            {Object.entries(customerData.metrics || {}).map(([key, val]: any) => (
              <div key={key} className="bg-slate-700/50 rounded p-2">
                <div className="text-slate-400">{key.replace(/_/g, ' ')}</div>
                <div className="text-white font-semibold">${val.current}</div>
                <div className="text-xs text-slate-500">Avg: ${val.avg} · {val.trend}</div>
              </div>
            ))}
          </div>
        )}
      </div>
      {violations.length > 0 && (
        <div className="bg-slate-800 rounded-lg p-4 border border-red-700">
          <h3 className="text-red-400 font-semibold mb-3">Target Violations</h3>
          {violations.map((v: any) => (
            <div key={v.target_id} className="text-sm text-slate-300 py-1 border-b border-slate-700 last:border-0">
              {v.customer_id} — {v.metric_type}: ${v.current_value} (target: ${v.target_value}, +{v.deviation_pct}%)
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function UnitMetricTrendChart() {
  const data = [
    { month: 'Jan', costPerCustomer: 165, revenuePerCustomer: 310 },
    { month: 'Feb', costPerCustomer: 158, revenuePerCustomer: 305 },
    { month: 'Mar', costPerCustomer: 152, revenuePerCustomer: 299 },
    { month: 'Apr', costPerCustomer: 149, revenuePerCustomer: 295 },
    { month: 'May', costPerCustomer: 145, revenuePerCustomer: 292 },
  ];
  const maxVal = 350;
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-white font-semibold mb-3">Metric Trends (6 Months)</h3>
      <div className="flex items-end space-x-4 h-40">
        {data.map((d, i) => {
          const cpcH = (d.costPerCustomer / maxVal) * 100;
          const rpcH = (d.revenuePerCustomer / maxVal) * 100;
          return (
            <div key={i} className="flex-1 flex flex-col items-center">
              <div className="text-xs text-green-400 mb-1">${d.revenuePerCustomer}</div>
              <div className="w-full bg-green-600 rounded-t" style={{ height: `${rpcH}%` }} />
              <div className="w-full bg-blue-500 rounded-t mt-0.5" style={{ height: `${cpcH}%` }} />
              <div className="text-xs text-slate-400 mt-1">${d.costPerCustomer}</div>
              <div className="text-xs text-slate-500 mt-1">{d.month}</div>
            </div>
          );
        })}
      </div>
      <div className="flex justify-center space-x-4 mt-2 text-xs">
        <span className="flex items-center"><span className="w-3 h-3 bg-green-600 rounded mr-1" /> Revenue</span>
        <span className="flex items-center"><span className="w-3 h-3 bg-blue-500 rounded mr-1" /> Cost</span>
      </div>
    </div>
  );
}

function UnitTargetManager({ onSet }: { onSet: (customerId: string, metric: string, target: number) => void }) {
  const [customerId, setCustomerId] = useState('');
  const [metric, setMetric] = useState('cost_per_customer');
  const [target, setTarget] = useState(150);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-white font-semibold mb-3">Set Unit Target</h3>
      <div className="space-y-3">
        <input value={customerId} onChange={e => setCustomerId(e.target.value)} placeholder="Customer ID" className="w-full bg-slate-700 text-white p-2 rounded" />
        <select value={metric} onChange={e => setMetric(e.target.value)} className="w-full bg-slate-700 text-white p-2 rounded">
          <option value="cost_per_customer">Cost/Customer</option>
          <option value="cost_per_transaction">Cost/Transaction</option>
          <option value="cost_per_deployment">Cost/Deployment</option>
          <option value="revenue_per_customer">Revenue/Customer</option>
        </select>
        <input type="number" value={target} onChange={e => setTarget(Number(e.target.value))} className="w-full bg-slate-700 text-white p-2 rounded" />
        <button onClick={() => onSet(customerId, metric, target)} className="w-full bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">Set Target</button>
      </div>
    </div>
  );
}

function UnitCustomerComparison() {
  const customers = [
    { id: 'cust-a', cpc: 145, rpc: 310, margin: 53.2 },
    { id: 'cust-b', cpc: 173, rpc: 285, margin: 39.4 },
    { id: 'cust-c', cpc: 128, rpc: 350, margin: 63.4 },
    { id: 'cust-d', cpc: 192, rpc: 270, margin: 28.9 },
  ];
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-white font-semibold mb-3">Customer Comparison</h3>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-slate-400 border-b border-slate-700">
            <th className="text-left py-2">Customer</th><th className="text-right py-2">Cost/Customer</th><th className="text-right py-2">Revenue</th><th className="text-right py-2">Margin</th>
          </tr>
        </thead>
        <tbody>
          {customers.map((c, i) => (
            <tr key={i} className="border-b border-slate-700">
              <td className="py-2 text-white">{c.id}</td><td className="py-2 text-right text-white">${c.cpc}</td><td className="py-2 text-right text-green-400">${c.rpc}</td>
              <td className={`py-2 text-right ${c.margin > 50 ? 'text-green-400' : 'text-red-400'}`}>{c.margin}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function UnitCostPerService({ services }: { services: any[] }) {
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-white font-semibold mb-3">Cost Per Service</h3>
      <table className="w-full text-sm">
        <thead><tr className="text-slate-400 border-b border-slate-700"><th className="text-left py-2">Service</th><th className="text-right py-2">Total Cost</th><th className="text-right py-2">Units</th><th className="text-right py-2">Cost/Unit</th></tr></thead>
        <tbody>{services.map((s: any, i: number) => (
          <tr key={i} className="border-b border-slate-700"><td className="py-2 text-white">{s.name}</td><td className="py-2 text-right text-white">${s.total_cost}</td><td className="py-2 text-right text-white">{s.units}</td><td className="py-2 text-right text-green-400">${s.cost_per_unit}</td></tr>
        ))}</tbody>
      </table>
    </div>
  );
}

function UnitMetricRecorder({ onRecord }: { onRecord: (customerId: string, metric: string, value: number) => void }) {
  const [customerId, setCustomerId] = useState('');
  const [metric, setMetric] = useState('cost_per_customer');
  const [value, setValue] = useState(0);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-white font-semibold mb-3">Record Metric</h3>
      <div className="grid grid-cols-3 gap-3">
        <input value={customerId} onChange={e => setCustomerId(e.target.value)} placeholder="Customer ID" className="bg-slate-700 text-white p-2 rounded" />
        <select value={metric} onChange={e => setMetric(e.target.value)} className="bg-slate-700 text-white p-2 rounded">
          <option value="cost_per_customer">Cost/Customer</option>
          <option value="cost_per_transaction">Cost/Transaction</option>
          <option value="revenue_per_customer">Revenue/Customer</option>
        </select>
        <input type="number" step="0.01" value={value} onChange={e => setValue(Number(e.target.value))} placeholder="Value" className="bg-slate-700 text-white p-2 rounded" />
      </div>
      <button onClick={() => onRecord(customerId, metric, value)} className="mt-3 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 text-sm">Record</button>
    </div>
  );
}
