import { useEffect, useState } from 'react';
import { apiClient } from '../../lib/api';
import { toast } from 'sonner';

interface ProxyInstance { id: string; name: string; proxy_type: string; status: string; vhost_count: number; upstream_count: number; config: string }
interface VirtualHost { id: string; instance_id: string; domain: string; upstream_pool: string; ssl_enabled: boolean; ssl_cert: string; ssl_key: string }
interface UpstreamPool { id: string; instance_id: string; name: string; servers: string[]; balance_method: string; health_check: string }

export const ReverseProxyPage = () => {
  const [instances, setInstances] = useState<ProxyInstance[]>([]);
  const [vhosts, setVhosts] = useState<VirtualHost[]>([]);
  const [pools, setPools] = useState<UpstreamPool[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedInstance, setSelectedInstance] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'vhosts' | 'pools'>('vhosts');
  const [showConfig, setShowConfig] = useState<string | null>(null);

  useEffect(() => { loadData(); }, []);
  useEffect(() => { if (selectedInstance) loadDetails(); }, [selectedInstance]);

  const loadData = async () => {
    setLoading(true);
    try {
      const data = await apiClient.get('/api/networking/proxy/instances');
      setInstances(Array.isArray(data) ? data : data?.instances || []);
    } catch { toast.error('Failed to load proxies'); }
    finally { setLoading(false); }
  };

  const loadDetails = async () => {
    if (!selectedInstance) return;
    try {
      const [v, p] = await Promise.all([
        apiClient.get(`/api/networking/proxy/instances/${selectedInstance}/vhosts`),
        apiClient.get(`/api/networking/proxy/instances/${selectedInstance}/upstreams`),
      ]);
      setVhosts(Array.isArray(v) ? v : v?.vhosts || []);
      setPools(Array.isArray(p) ? p : p?.pools || []);
    } catch { toast.error('Failed to load details'); }
  };

  const handleGetConfig = async (id: string) => {
    try {
      const data = await apiClient.get(`/api/networking/proxy/instances/${id}/config`);
      setShowConfig(data?.config || 'No config');
    } catch { toast.error('Failed to get config'); }
  };

  if (loading) return <div className="text-slate-400 p-8">Loading proxies...</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Reverse Proxy Catalog</h1>
          <p className="text-slate-400">Manage reverse proxy instances, virtual hosts, and upstream pools</p>
        </div>
        <button onClick={loadData} className="px-4 py-2 bg-slate-800 border border-slate-700 text-slate-300 rounded-lg text-sm hover:bg-slate-700">Refresh</button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        <div className="lg:col-span-1 space-y-2">
          <h2 className="text-lg font-semibold text-white mb-2">Instances</h2>
          {instances.map(inst => (
            <div key={inst.id} onClick={() => setSelectedInstance(inst.id)} className={`bg-slate-900 border rounded-lg p-4 cursor-pointer transition-colors ${selectedInstance === inst.id ? 'border-blue-500' : 'border-slate-800 hover:border-slate-700'}`}>
              <div className="flex items-center gap-2">
                <div className={`w-2.5 h-2.5 rounded-full ${inst.status === 'running' ? 'bg-green-500' : 'bg-red-500'}`} />
                <span className="text-white font-medium">{inst.name}</span>
                <span className="text-xs text-slate-500">{inst.proxy_type}</span>
              </div>
              <div className="text-xs text-slate-400 mt-1">{inst.vhost_count} hosts | {inst.upstream_count} pools</div>
            </div>
          ))}
        </div>

        <div className="lg:col-span-3">
          {!selectedInstance && <p className="text-slate-500 text-center py-8">Select an instance to manage.</p>}
          {selectedInstance && (
            <>
              <div className="flex items-center justify-between mb-4">
                <div className="flex gap-2">
                  <button onClick={() => setActiveTab('vhosts')} className={`px-3 py-1.5 text-sm rounded ${activeTab === 'vhosts' ? 'bg-slate-800 text-white' : 'text-slate-400 hover:text-white'}`}>Virtual Hosts ({vhosts.length})</button>
                  <button onClick={() => setActiveTab('pools')} className={`px-3 py-1.5 text-sm rounded ${activeTab === 'pools' ? 'bg-slate-800 text-white' : 'text-slate-400 hover:text-white'}`}>Upstream Pools ({pools.length})</button>
                </div>
                <button onClick={() => handleGetConfig(selectedInstance)} className="px-3 py-1.5 bg-slate-800 border border-slate-700 text-slate-300 rounded text-xs hover:bg-slate-700">View Config</button>
              </div>

              {showConfig && (
                <div className="bg-slate-900 border border-slate-700 rounded-lg p-4 mb-4">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-sm font-semibold text-white">Configuration</h3>
                    <button onClick={() => setShowConfig(null)} className="text-slate-400 hover:text-white text-xs">Close</button>
                  </div>
                  <pre className="text-xs text-green-400 font-mono whitespace-pre-wrap max-h-60 overflow-y-auto">{showConfig}</pre>
                </div>
              )}

              {activeTab === 'vhosts' && (
                <div className="grid gap-3">
                  {vhosts.map(vh => (
                    <div key={vh.id} className="bg-slate-900 border border-slate-800 rounded-lg p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-white font-medium">{vh.domain}</span>
                        {vh.ssl_enabled && <span className="text-xs bg-green-600 text-white px-1.5 py-0.5 rounded">SSL</span>}
                      </div>
                      <div className="grid grid-cols-3 gap-3 text-sm">
                        <div><span className="text-slate-400">Upstream Pool</span><p className="text-white">{vh.upstream_pool}</p></div>
                        <div><span className="text-slate-400">SSL Cert</span><p className="text-white font-mono text-xs">{vh.ssl_cert ? `${vh.ssl_cert.slice(0, 20)}...` : 'None'}</p></div>
                      </div>
                    </div>
                  ))}
                  {vhosts.length === 0 && <p className="text-slate-500 text-center py-4">No virtual hosts.</p>}
                </div>
              )}

              {activeTab === 'pools' && (
                <div className="grid gap-3">
                  {pools.map(p => (
                    <div key={p.id} className="bg-slate-900 border border-slate-800 rounded-lg p-4">
                      <h3 className="text-white font-medium mb-2">{p.name}</h3>
                      <div className="grid grid-cols-3 gap-3 text-sm mb-2">
                        <div><span className="text-slate-400">Balance Method</span><p className="text-white">{p.balance_method}</p></div>
                        <div><span className="text-slate-400">Health Check</span><p className="text-white">{p.health_check}</p></div>
                        <div><span className="text-slate-400">Servers</span><p className="text-white">{p.servers.length}</p></div>
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {p.servers.map((s, i) => (
                          <span key={i} className="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded font-mono">{s}</span>
                        ))}
                      </div>
                    </div>
                  ))}
                  {pools.length === 0 && <p className="text-slate-500 text-center py-4">No upstream pools.</p>}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default ReverseProxyPage;
