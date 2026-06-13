import { useEffect, useState } from 'react';
import { apiClient } from '../../lib/api';
import { toast } from 'sonner';

interface SLATemplate { id: string; name: string; uptime_target: number; response_time_mins: number; credit_percent: number; max_monthly_credit_percent: number; price_monthly: number }
interface SLACredit { id: string; sla_id: string; amount: number; reason: string; status: string; issued_at: string }

export const SLAPage = () => {
  const [templates, setTemplates] = useState<SLATemplate[]>([]);
  const [credits, setCredits] = useState<SLACredit[]>([]);
  const [statusData, setStatusData] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(true);
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [newSLA, setNewSLA] = useState({ name: '', uptime_target: 99.9, response_time_mins: 15, credit_percent: 5, max_credit: 100, price_monthly: 0 });

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [t, c] = await Promise.all([
        apiClient.get('/api/marketplace/sla/templates'),
        apiClient.get('/api/marketplace/sla/credits'),
      ]);
      setTemplates(Array.isArray(t) ? t : t?.templates || []);
      setCredits(Array.isArray(c) ? c : c?.credits || []);
    } catch { toast.error('Failed to load SLA data'); }
    finally { setLoading(false); }
  };

  const handleStatus = async (id: string) => {
    try {
      const d = await apiClient.get(`/api/marketplace/sla/status/${id}`);
      setStatusData({ ...statusData, [id]: d });
    } catch { toast.error('Failed to get status'); }
  };

  const handleCreate = async () => {
    try {
      await apiClient.post('/api/marketplace/sla/templates', {
        name: newSLA.name, uptime_target: newSLA.uptime_target, response_time_mins: newSLA.response_time_mins,
        credit_percent: newSLA.credit_percent, max_monthly_credit_percent: newSLA.max_credit, price_monthly: newSLA.price_monthly,
      });
      toast.success('SLA template created');
      setShowCreate(false);
      loadData();
    } catch { toast.error('Failed to create'); }
  };

  if (loading) return <div className="text-slate-400 p-8">Loading SLA data...</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">SLA Management & Credits</h1>
          <p className="text-slate-400">Service Level Agreements with automated credit issuance</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => setShowCreate(!showCreate)} className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm transition-colors">+ New SLA</button>
          <button onClick={loadData} className="px-4 py-2 bg-slate-800 border border-slate-700 text-slate-300 rounded-lg text-sm hover:bg-slate-700">Refresh</button>
        </div>
      </div>

      {showCreate && (
        <div className="bg-slate-900 border border-slate-700 rounded-lg p-5">
          <h3 className="text-lg font-semibold text-white mb-4">New SLA Template</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-4">
            <div><label className="block text-sm text-slate-400 mb-1">Name</label><input value={newSLA.name} onChange={e => setNewSLA({...newSLA, name: e.target.value})} className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white text-sm" /></div>
            <div><label className="block text-sm text-slate-400 mb-1">Uptime %</label><input type="number" step="0.1" value={newSLA.uptime_target} onChange={e => setNewSLA({...newSLA, uptime_target: parseFloat(e.target.value) || 99.9})} className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white text-sm" /></div>
            <div><label className="block text-sm text-slate-400 mb-1">Response (min)</label><input type="number" value={newSLA.response_time_mins} onChange={e => setNewSLA({...newSLA, response_time_mins: parseInt(e.target.value) || 15})} className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white text-sm" /></div>
            <div><label className="block text-sm text-slate-400 mb-1">Credit %</label><input type="number" step="0.5" value={newSLA.credit_percent} onChange={e => setNewSLA({...newSLA, credit_percent: parseFloat(e.target.value) || 5})} className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white text-sm" /></div>
            <div><label className="block text-sm text-slate-400 mb-1">Max Credit %</label><input type="number" step="5" value={newSLA.max_credit} onChange={e => setNewSLA({...newSLA, max_credit: parseFloat(e.target.value) || 100})} className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white text-sm" /></div>
            <div><label className="block text-sm text-slate-400 mb-1">Price/mo</label><input type="number" step="0.01" value={newSLA.price_monthly} onChange={e => setNewSLA({...newSLA, price_monthly: parseFloat(e.target.value) || 0})} className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white text-sm" /></div>
          </div>
          <button onClick={handleCreate} className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm">Create SLA</button>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {templates.map(t => {
          const st = statusData[t.id];
          return (
            <div key={t.id} className="bg-slate-900 border border-slate-800 rounded-lg p-5">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-semibold text-white">{t.name}</h3>
                {t.price_monthly > 0 && <span className="text-sm text-yellow-400">${t.price_monthly}/mo</span>}
              </div>
              <div className="grid grid-cols-2 gap-3 text-sm mb-4">
                <div><span className="text-slate-400">Uptime Target</span><p className="text-white">{t.uptime_target}%</p></div>
                <div><span className="text-slate-400">Response Time</span><p className="text-white">{t.response_time_mins} min</p></div>
                <div><span className="text-slate-400">Credit/Incident</span><p className="text-white">{t.credit_percent}%</p></div>
                <div><span className="text-slate-400">Max Monthly</span><p className="text-white">{t.max_monthly_credit_percent}%</p></div>
              </div>
              {st && (
                <div className="border-t border-slate-800 pt-3 mt-3">
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div><span className="text-slate-400">Current Uptime</span><p className={`font-semibold ${st.current_uptime >= st.uptime_target ? 'text-green-400' : 'text-red-400'}`}>{st.current_uptime?.toFixed(3)}%</p></div>
                    <div><span className="text-slate-400">Credits Issued</span><p className="text-white">${st.credits_issued?.toFixed(2)}</p></div>
                  </div>
                </div>
              )}
              <button onClick={() => handleStatus(t.id)} className="mt-3 w-full px-3 py-1.5 bg-slate-800 border border-slate-700 text-slate-300 rounded text-xs hover:bg-slate-700 transition-colors">Check Status</button>
            </div>
          );
        })}
      </div>

      {credits.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold text-white mb-3">Credit History</h2>
          <div className="grid gap-2">
            {credits.map(c => (
              <div key={c.id} className="bg-slate-900 border border-slate-800 rounded-lg p-3 flex items-center justify-between">
                <div>
                  <span className="text-white font-medium">${c.amount.toFixed(2)}</span>
                  <span className="text-slate-400 ml-3 text-sm">{c.reason}</span>
                  <span className={`ml-2 text-xs px-1.5 py-0.5 rounded ${c.status === 'issued' ? 'bg-green-600' : c.status === 'pending' ? 'bg-yellow-600' : 'bg-red-600'} text-white`}>{c.status}</span>
                </div>
                <span className="text-xs text-slate-500">{c.issued_at?.split('T')[0]}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default SLAPage;
