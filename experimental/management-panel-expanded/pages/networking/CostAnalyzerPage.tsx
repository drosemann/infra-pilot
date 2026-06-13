import { useEffect, useState } from 'react';
import { apiClient } from '../../lib/api';
import { toast } from 'sonner';

interface BandwidthUsage { id: string; timestamp: string; inbound_bytes: number; outbound_bytes: number; provider: string; cost: number }
interface ProviderPricing { id: string; name: string; price_per_gb: number; monthly_fee: number; included_bandwidth_gb: number; burstable: boolean }
interface CostAlert { id: string; name: string; threshold: number; current: number; severity: string; status: string; enabled: boolean }

export const CostAnalyzerPage = () => {
  const [summary, setSummary] = useState<any>(null);
  const [providers, setProviders] = useState<ProviderPricing[]>([]);
  const [alerts, setAlerts] = useState<CostAlert[]>([]);
  const [usageHistory, setUsageHistory] = useState<BandwidthUsage[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'summary' | 'providers' | 'alerts' | 'history'>('summary');

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [s, p, a, u] = await Promise.all([
        apiClient.get('/api/networking/cost/summary'),
        apiClient.get('/api/networking/cost/providers'),
        apiClient.get('/api/networking/cost/alerts'),
        apiClient.get('/api/networking/cost/usage'),
      ]);
      setSummary(s);
      setProviders(Array.isArray(p) ? p : p?.providers || []);
      setAlerts(Array.isArray(a) ? a : a?.alerts || []);
      setUsageHistory(Array.isArray(u) ? u : u?.usage || []);
    } catch { toast.error('Failed to load cost data'); }
    finally { setLoading(false); }
  };

  if (loading) return <div className="text-slate-400 p-8">Loading cost data...</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Network Cost Analyzer</h1>
          <p className="text-slate-400">Analyze bandwidth costs, provider pricing, and get cost optimization insights</p>
        </div>
        <button onClick={loadData} className="px-4 py-2 bg-slate-800 border border-slate-700 text-slate-300 rounded-lg text-sm hover:bg-slate-700">Refresh</button>
      </div>

      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-4"><div className="text-slate-400 text-xs mb-1">Current Month</div><div className="text-2xl font-bold text-white">${summary.current_month?.toFixed(2)}</div></div>
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-4"><div className="text-slate-400 text-xs mb-1">Previous Month</div><div className="text-2xl font-bold text-white">${summary.previous_month?.toFixed(2)}</div></div>
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-4"><div className="text-slate-400 text-xs mb-1">Forecast</div><div className="text-2xl font-bold text-yellow-400">${summary.forecast?.toFixed(2)}</div></div>
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-4"><div className="text-slate-400 text-xs mb-1">95th Percentile</div><div className="text-2xl font-bold text-blue-400">{summary.percentile_95?.toFixed(2)} Mbps</div></div>
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-4"><div className="text-slate-400 text-xs mb-1">Total Transfer</div><div className="text-2xl font-bold text-white">{summary.total_transfer_gb?.toFixed(2)} GB</div></div>
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-4"><div className="text-slate-400 text-xs mb-1">Trend</div><div className={`text-2xl font-bold ${summary.trend === 'up' ? 'text-red-400' : summary.trend === 'down' ? 'text-green-400' : 'text-yellow-400'}`}>{summary.trend || 'stable'}</div></div>
        </div>
      )}

      <div className="flex gap-2 border-b border-slate-800 pb-2">
        {(['summary', 'providers', 'alerts', 'history'] as const).map(t => (
          <button key={t} onClick={() => setActiveTab(t)} className={`px-4 py-2 text-sm rounded-t-lg capitalize ${activeTab === t ? 'bg-slate-800 text-white border border-slate-700 border-b-transparent' : 'text-slate-400 hover:text-white'}`}>{t}</button>
        ))}
      </div>

      {activeTab === 'summary' && summary?.provider_breakdown && (
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
          <h3 className="text-lg font-semibold text-white mb-3">Provider Breakdown</h3>
          <div className="space-y-3">
            {Object.entries(summary.provider_breakdown).map(([name, cost]) => (
              <div key={name} className="flex items-center justify-between">
                <span className="text-white">{name}</span>
                <div className="flex items-center gap-4">
                  <div className="w-48 bg-slate-800 rounded-full h-2">
                    <div className="bg-blue-600 h-2 rounded-full" style={{ width: `${Math.min(100, (cost as number) / (summary.current_month || 1) * 100)}%` }} />
                  </div>
                  <span className="text-white font-mono">${(cost as number).toFixed(2)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'providers' && (
        <div className="grid gap-4">
          {providers.map(p => (
            <div key={p.id} className="bg-slate-900 border border-slate-800 rounded-lg p-5">
              <h3 className="text-lg font-semibold text-white mb-2">{p.name}</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div><span className="text-slate-400">Price/GB</span><p className="text-white">${p.price_per_gb.toFixed(4)}</p></div>
                <div><span className="text-slate-400">Monthly Fee</span><p className="text-white">${p.monthly_fee.toFixed(2)}</p></div>
                <div><span className="text-slate-400">Included BW</span><p className="text-white">{p.included_bandwidth_gb} GB</p></div>
                <div><span className="text-slate-400">Burstable</span><p className="text-white">{p.burstable ? 'Yes' : 'No'}</p></div>
              </div>
            </div>
          ))}
        </div>
      )}

      {activeTab === 'alerts' && (
        <div className="grid gap-3">
          {alerts.map(a => (
            <div key={a.id} className="bg-slate-900 border border-slate-800 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <div className={`w-2.5 h-2.5 rounded-full ${a.severity === 'critical' ? 'bg-red-500' : a.severity === 'warning' ? 'bg-yellow-500' : 'bg-blue-500'}`} />
                  <span className="text-white font-medium">{a.name}</span>
                </div>
                <span className={`text-xs px-2 py-0.5 rounded ${a.enabled ? 'bg-green-600 text-white' : 'bg-slate-700 text-slate-400'}`}>{a.enabled ? 'Enabled' : 'Disabled'}</span>
              </div>
              <div className="flex items-center gap-4 text-sm">
                <span className="text-slate-400">Threshold: <span className="text-white">${a.threshold.toFixed(2)}</span></span>
                <span className="text-slate-400">Current: <span className={`${a.current > a.threshold ? 'text-red-400' : 'text-green-400'}`}>${a.current.toFixed(2)}</span></span>
                <span className="text-slate-400">Status: <span className="text-white capitalize">{a.status}</span></span>
              </div>
            </div>
          ))}
        </div>
      )}

      {activeTab === 'history' && (
        <div className="bg-slate-900 border border-slate-800 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead><tr className="text-slate-400 text-xs border-b border-slate-800">
              <th className="text-left px-3 py-2">Timestamp</th><th className="text-left px-3 py-2">Provider</th><th className="text-right px-3 py-2">Inbound</th><th className="text-right px-3 py-2">Outbound</th><th className="text-right px-3 py-2">Cost</th>
            </tr></thead>
            <tbody>
              {usageHistory.map(u => (
                <tr key={u.id} className="border-b border-slate-800 hover:bg-slate-800/50 text-white">
                  <td className="px-3 py-2 text-xs text-slate-400">{u.timestamp}</td>
                  <td className="px-3 py-2">{u.provider}</td>
                  <td className="px-3 py-2 text-right">{(u.inbound_bytes / 1024 / 1024 / 1024).toFixed(2)} GB</td>
                  <td className="px-3 py-2 text-right">{(u.outbound_bytes / 1024 / 1024 / 1024).toFixed(2)} GB</td>
                  <td className="px-3 py-2 text-right">${u.cost.toFixed(4)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {usageHistory.length === 0 && <p className="text-slate-500 text-center py-4">No usage data.</p>}
        </div>
      )}
    </div>
  );
};

export default CostAnalyzerPage;
