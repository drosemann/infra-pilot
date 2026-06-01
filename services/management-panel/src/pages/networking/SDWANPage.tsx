import { useEffect, useState } from 'react';
import { apiClient } from '../../lib/api';
import { toast } from 'sonner';

interface Uplink {
  id: string; name: string; provider: string; bandwidth: number; status: string; load_percent: number; ip_address: string; failover_priority: number; is_active: boolean
}

interface FailoverPolicy {
  id: string; name: string; condition: string; target_uplink: string; priority: number
}

interface QoSPolicy {
  id: string; name: string; direction: string; bandwidth_limit: number; priority: number; protocol: string
}

export const SDWANPage = () => {
  const [uplinks, setUplinks] = useState<Uplink[]>([]);
  const [policies, setPolicies] = useState<FailoverPolicy[]>([]);
  const [qosPolicies, setQoSPolicies] = useState<QoSPolicy[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'uplinks' | 'failover' | 'qos'>('uplinks');

  useEffect(() => { loadAll(); }, []);

  const loadAll = async () => {
    setLoading(true);
    try {
      const [u, f, q] = await Promise.all([
        apiClient.get('/api/networking/sdwan/uplinks'),
        apiClient.get('/api/networking/sdwan/failover-policies'),
        apiClient.get('/api/networking/sdwan/qos-policies'),
      ]);
      setUplinks(Array.isArray(u) ? u : u?.uplinks || []);
      setPolicies(Array.isArray(f) ? f : f?.policies || []);
      setQoSPolicies(Array.isArray(q) ? q : q?.policies || []);
    } catch { toast.error('Failed to load SD-WAN data'); }
    finally { setLoading(false); }
  };

  const handleFailover = async (uplinkId: string) => {
    try {
      await apiClient.post(`/api/networking/sdwan/uplinks/${uplinkId}/failover`, {});
      toast.success('Failover triggered');
      loadAll();
    } catch { toast.error('Failover failed'); }
  };

  if (loading) return <div className="text-slate-400 p-8">Loading SD-WAN...</div>;

  const tabs = [
    { key: 'uplinks' as const, label: 'Uplinks', count: uplinks.length },
    { key: 'failover' as const, label: 'Failover Policies', count: policies.length },
    { key: 'qos' as const, label: 'QoS Policies', count: qosPolicies.length },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">SD-WAN Controller</h1>
          <p className="text-slate-400">Manage software-defined wide area network uplinks and policies</p>
        </div>
        <button onClick={loadAll} className="px-4 py-2 bg-slate-800 border border-slate-700 text-slate-300 rounded-lg text-sm hover:bg-slate-700 transition-colors">Refresh</button>
      </div>

      <div className="flex gap-2 border-b border-slate-800 pb-2">
        {tabs.map(t => (
          <button key={t.key} onClick={() => setActiveTab(t.key)} className={`px-4 py-2 text-sm rounded-t-lg transition-colors ${activeTab === t.key ? 'bg-slate-800 text-white border border-slate-700 border-b-transparent' : 'text-slate-400 hover:text-white'}`}>{t.label} ({t.count})</button>
        ))}
      </div>

      {activeTab === 'uplinks' && (
        <div className="grid gap-4">
          {uplinks.map(u => (
            <div key={u.id} className="bg-slate-900 border border-slate-800 rounded-lg p-5">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className={`w-3 h-3 rounded-full ${u.status === 'active' ? 'bg-green-500' : u.status === 'degraded' ? 'bg-yellow-500' : 'bg-red-500'}`} />
                  <h3 className="text-lg font-semibold text-white">{u.name}</h3>
                  {u.is_active && <span className="text-xs bg-blue-600 text-white px-2 py-0.5 rounded">Active</span>}
                </div>
                <button onClick={() => handleFailover(u.id)} className="px-3 py-1.5 bg-yellow-600 hover:bg-yellow-700 text-white text-xs rounded transition-colors">Failover</button>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div><span className="text-slate-400">Provider</span><p className="text-white">{u.provider}</p></div>
                <div><span className="text-slate-400">Bandwidth</span><p className="text-white">{u.bandwidth} Mbps</p></div>
                <div><span className="text-slate-400">Load</span><p className="text-white">{u.load_percent}%</p></div>
                <div><span className="text-slate-400">IP</span><p className="text-white font-mono text-xs">{u.ip_address}</p></div>
              </div>
            </div>
          ))}
          {uplinks.length === 0 && <p className="text-slate-500 text-center py-8">No uplinks configured.</p>}
        </div>
      )}

      {activeTab === 'failover' && (
        <div className="grid gap-4">
          {policies.map(p => (
            <div key={p.id} className="bg-slate-900 border border-slate-800 rounded-lg p-5">
              <h3 className="text-lg font-semibold text-white mb-2">{p.name}</h3>
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div><span className="text-slate-400">Condition</span><p className="text-white">{p.condition}</p></div>
                <div><span className="text-slate-400">Target Uplink</span><p className="text-white">{p.target_uplink}</p></div>
                <div><span className="text-slate-400">Priority</span><p className="text-white">{p.priority}</p></div>
              </div>
            </div>
          ))}
          {policies.length === 0 && <p className="text-slate-500 text-center py-8">No failover policies configured.</p>}
        </div>
      )}

      {activeTab === 'qos' && (
        <div className="grid gap-4">
          {qosPolicies.map(q => (
            <div key={q.id} className="bg-slate-900 border border-slate-800 rounded-lg p-5">
              <h3 className="text-lg font-semibold text-white mb-2">{q.name}</h3>
              <div className="grid grid-cols-4 gap-4 text-sm">
                <div><span className="text-slate-400">Direction</span><p className="text-white">{q.direction}</p></div>
                <div><span className="text-slate-400">BW Limit</span><p className="text-white">{q.bandwidth_limit} Mbps</p></div>
                <div><span className="text-slate-400">Priority</span><p className="text-white">{q.priority}</p></div>
                <div><span className="text-slate-400">Protocol</span><p className="text-white">{q.protocol}</p></div>
              </div>
            </div>
          ))}
          {qosPolicies.length === 0 && <p className="text-slate-500 text-center py-8">No QoS policies configured.</p>}
        </div>
      )}
    </div>
  );
};

export default SDWANPage;
