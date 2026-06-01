import { useEffect, useState } from 'react';
import { apiClient } from '../../lib/api';
import { toast } from 'sonner';

interface FilterInstance { id: string; name: string; filter_type: string; status: string; blocked_count: number; client_count: number; upstream_dns: string }
interface BlocklistEntry { id: string; domain: string; category: string; blocked: boolean; hit_count: number; added_at: string }
interface DHCPLease { id: string; ip: string; mac: string; hostname: string; active: boolean; expires_at: string; pool: string }
interface QueryLogEntry { id: string; timestamp: string; client_ip: string; domain: string; query_type: string; blocked: boolean; response_ip: string }

export const DNSFilteringPage = () => {
  const [instances, setInstances] = useState<FilterInstance[]>([]);
  const [blocklist, setBlocklist] = useState<BlocklistEntry[]>([]);
  const [leases, setLeases] = useState<DHCPLease[]>([]);
  const [queryLogs, setQueryLogs] = useState<QueryLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeView, setActiveView] = useState<'blocklist' | 'leases' | 'queries'>('blocklist');
  const [selectedInstance, setSelectedInstance] = useState<string | null>(null);
  const [newDomain, setNewDomain] = useState('');
  const [newCategory, setNewCategory] = useState('ads');

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const i = await apiClient.get('/api/networking/dnsfilter/instances');
      setInstances(Array.isArray(i) ? i : i?.instances || []);
      if (!selectedInstance && i?.instances?.[0]) setSelectedInstance(i.instances[0].id);
      const b = await apiClient.get('/api/networking/dnsfilter/blocklist');
      setBlocklist(Array.isArray(b) ? b : b?.entries || []);
      const l = await apiClient.get('/api/networking/dhcp/leases');
      setLeases(Array.isArray(l) ? l : l?.leases || []);
      const q = await apiClient.get('/api/networking/dnsfilter/queries');
      setQueryLogs(Array.isArray(q) ? q : q?.queries || []);
    } catch { toast.error('Failed to load data'); }
    finally { setLoading(false); }
  };

  const handleBlock = async () => {
    if (!newDomain) return;
    try {
      await apiClient.post('/api/networking/dnsfilter/blocklist', { domain: newDomain, category: newCategory });
      toast.success(`${newDomain} blocked`);
      setNewDomain('');
      loadData();
    } catch { toast.error('Failed to block domain'); }
  };

  const handleUnblock = async (domain: string) => {
    try {
      await apiClient.delete(`/api/networking/dnsfilter/blocklist/${domain}`);
      toast.success(`${domain} unblocked`);
      loadData();
    } catch { toast.error('Failed to unblock'); }
  };

  if (loading) return <div className="text-slate-400 p-8">Loading DNS filter...</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">DNS Filtering & DHCP Server</h1>
          <p className="text-slate-400">DNS filtering with blocklists and DHCP lease management</p>
        </div>
        <button onClick={loadData} className="px-4 py-2 bg-slate-800 border border-slate-700 text-slate-300 rounded-lg text-sm hover:bg-slate-700">Refresh</button>
      </div>

      {instances.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {instances.map(inst => (
            <div key={inst.id} className={`bg-slate-900 border rounded-lg p-4 ${selectedInstance === inst.id ? 'border-blue-500' : 'border-slate-800'}`}>
              <div className="flex items-center gap-2 mb-1">
                <div className={`w-2.5 h-2.5 rounded-full ${inst.status === 'active' ? 'bg-green-500' : 'bg-red-500'}`} />
                <span className="text-white font-medium text-sm">{inst.name}</span>
              </div>
              <div className="text-xs text-slate-400">{inst.filter_type} | {inst.blocked_count} blocked | {inst.client_count} clients</div>
              <div className="text-xs text-slate-500 font-mono mt-1">Upstream: {inst.upstream_dns}</div>
            </div>
          ))}
        </div>
      )}

      <div className="flex gap-2 border-b border-slate-800 pb-2">
        {(['blocklist', 'leases', 'queries'] as const).map(v => (
          <button key={v} onClick={() => setActiveView(v)} className={`px-4 py-2 text-sm rounded-t-lg capitalize ${activeView === v ? 'bg-slate-800 text-white border border-slate-700 border-b-transparent' : 'text-slate-400 hover:text-white'}`}>{v} ({v === 'blocklist' ? blocklist.length : v === 'leases' ? leases.length : queryLogs.length})</button>
        ))}
      </div>

      {activeView === 'blocklist' && (
        <div className="space-y-4">
          <div className="flex gap-3">
            <input value={newDomain} onChange={e => setNewDomain(e.target.value)} className="flex-1 px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white placeholder-slate-500" placeholder="example.com" />
            <select value={newCategory} onChange={e => setNewCategory(e.target.value)} className="px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white text-sm">
              <option value="ads">Ads</option><option value="malware">Malware</option><option value="social">Social Media</option><option value="gambling">Gambling</option><option value="pornography">Pornography</option><option value="custom">Custom</option>
            </select>
            <button onClick={handleBlock} className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm transition-colors whitespace-nowrap">Block Domain</button>
          </div>
          <div className="grid gap-2">
            {blocklist.map(e => (
              <div key={e.id} className="bg-slate-900 border border-slate-800 rounded-lg p-3 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className={`text-xs px-2 py-0.5 rounded ${e.category === 'malware' ? 'bg-red-600' : e.category === 'ads' ? 'bg-yellow-600' : e.category === 'social' ? 'bg-blue-600' : 'bg-slate-600'} text-white`}>{e.category}</span>
                  <span className="text-white font-mono text-sm">{e.domain}</span>
                  <span className="text-xs text-slate-500">{e.hit_count} hits</span>
                </div>
                <button onClick={() => handleUnblock(e.domain)} className="text-green-400 hover:text-green-300 text-xs">Unblock</button>
              </div>
            ))}
            {blocklist.length === 0 && <p className="text-slate-500 text-center py-4">No blocklist entries.</p>}
          </div>
        </div>
      )}

      {activeView === 'leases' && (
        <div className="grid gap-2">
          {leases.map(l => (
            <div key={l.id} className="bg-slate-900 border border-slate-800 rounded-lg p-3 flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className={`w-2.5 h-2.5 rounded-full ${l.active ? 'bg-green-500' : 'bg-red-500'}`} />
                <span className="text-white font-medium text-sm">{l.hostname || 'Unknown'}</span>
                <span className="text-white font-mono text-sm">{l.ip}</span>
                <span className="text-slate-400 text-xs font-mono">{l.mac}</span>
              </div>
              <span className="text-xs text-slate-500">Expires: {l.expires_at?.split('T')[0] || 'N/A'}</span>
            </div>
          ))}
          {leases.length === 0 && <p className="text-slate-500 text-center py-4">No DHCP leases.</p>}
        </div>
      )}

      {activeView === 'queries' && (
        <div className="bg-slate-900 border border-slate-800 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead><tr className="text-slate-400 text-xs border-b border-slate-800">
              <th className="text-left px-3 py-2">Time</th><th className="text-left px-3 py-2">Client</th><th className="text-left px-3 py-2">Domain</th><th className="text-left px-3 py-2">Type</th><th className="text-center px-3 py-2">Blocked</th>
            </tr></thead>
            <tbody>
              {queryLogs.slice(0, 50).map(q => (
                <tr key={q.id} className="border-b border-slate-800 hover:bg-slate-800/50 text-white">
                  <td className="px-3 py-2 text-xs text-slate-400">{q.timestamp?.split('T')[1]?.split('.')[0] || q.timestamp}</td>
                  <td className="px-3 py-2 font-mono text-xs">{q.client_ip}</td>
                  <td className="px-3 py-2">{q.domain}</td>
                  <td className="px-3 py-2"><span className="text-xs bg-slate-800 text-blue-400 px-1.5 py-0.5 rounded font-mono">{q.query_type}</span></td>
                  <td className="px-3 py-2 text-center">{q.blocked ? <span className="text-red-400 text-xs">Blocked</span> : <span className="text-green-400 text-xs">Allowed</span>}</td>
                </tr>
              ))}
              {queryLogs.length === 0 && <tr><td colSpan={5} className="text-center py-4 text-slate-500">No query logs.</td></tr>}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default DNSFilteringPage;
