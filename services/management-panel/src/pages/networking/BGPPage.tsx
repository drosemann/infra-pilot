import { useEffect, useState } from 'react';
import { apiClient } from '../../lib/api';
import { toast } from 'sonner';

interface BGPSession { id: string; peer_ip: string; remote_as: number; state: string; routes_received: number; routes_advertised: number; uptime_seconds: number; description: string }
interface BGPAnnouncement { id: string; prefix: string; next_hop: string; community: string; status: string; announced_at: string }

export const BGPPage = () => {
  const [sessions, setSessions] = useState<BGPSession[]>([]);
  const [announcements, setAnnouncements] = useState<BGPAnnouncement[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'sessions' | 'announce'>('sessions');
  const [prefix, setPrefix] = useState('');
  const [nextHop, setNextHop] = useState('');
  const [community, setCommunity] = useState('');

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [s, a] = await Promise.all([
        apiClient.get('/api/networking/bgp/sessions'),
        apiClient.get('/api/networking/bgp/announcements'),
      ]);
      setSessions(Array.isArray(s) ? s : s?.sessions || []);
      setAnnouncements(Array.isArray(a) ? a : a?.announcements || []);
    } catch { toast.error('Failed to load BGP data'); }
    finally { setLoading(false); }
  };

  const handleAnnounce = async () => {
    if (!prefix || !nextHop) { toast.error('Prefix and next hop required'); return; }
    try {
      await apiClient.post('/api/networking/bgp/announce', { prefix, next_hop: nextHop, community });
      toast.success('Route announced');
      setPrefix(''); setNextHop(''); setCommunity('');
      loadData();
    } catch { toast.error('Failed to announce route'); }
  };

  const handleWithdraw = async (p: string) => {
    try {
      await apiClient.post('/api/networking/bgp/withdraw', { prefix: p });
      toast.success('Route withdrawn');
      loadData();
    } catch { toast.error('Failed to withdraw'); }
  };

  if (loading) return <div className="text-slate-400 p-8">Loading BGP...</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">BGP Route Manager</h1>
          <p className="text-slate-400">Manage BGP sessions and route announcements</p>
        </div>
        <button onClick={loadData} className="px-4 py-2 bg-slate-800 border border-slate-700 text-slate-300 rounded-lg text-sm hover:bg-slate-700">Refresh</button>
      </div>

      <div className="flex gap-2 border-b border-slate-800 pb-2">
        <button onClick={() => setActiveTab('sessions')} className={`px-4 py-2 text-sm rounded-t-lg ${activeTab === 'sessions' ? 'bg-slate-800 text-white border border-slate-700 border-b-transparent' : 'text-slate-400 hover:text-white'}`}>Sessions ({sessions.length})</button>
        <button onClick={() => setActiveTab('announce')} className={`px-4 py-2 text-sm rounded-t-lg ${activeTab === 'announce' ? 'bg-slate-800 text-white border border-slate-700 border-b-transparent' : 'text-slate-400 hover:text-white'}`}>Announcements ({announcements.length})</button>
      </div>

      {activeTab === 'sessions' && (
        <div className="grid gap-4">
          {sessions.map(s => (
            <div key={s.id} className="bg-slate-900 border border-slate-800 rounded-lg p-5">
              <div className="flex items-center gap-3 mb-3">
                <div className={`w-3 h-3 rounded-full ${s.state === 'established' ? 'bg-green-500' : s.state === 'active' ? 'bg-yellow-500' : 'bg-red-500'}`} />
                <h3 className="text-lg font-semibold text-white">AS{s.remote_as}</h3>
                <span className="text-sm text-slate-400">{s.peer_ip}</span>
                {s.description && <span className="text-xs text-slate-500">{s.description}</span>}
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div><span className="text-slate-400">State</span><p className="text-white capitalize">{s.state}</p></div>
                <div><span className="text-slate-400">Routes Received</span><p className="text-white">{s.routes_received}</p></div>
                <div><span className="text-slate-400">Routes Advertised</span><p className="text-white">{s.routes_advertised}</p></div>
                <div><span className="text-slate-400">Uptime</span><p className="text-white">{Math.floor(s.uptime_seconds / 3600)}h {Math.floor((s.uptime_seconds % 3600) / 60)}m</p></div>
              </div>
            </div>
          ))}
          {sessions.length === 0 && <p className="text-slate-500 text-center py-8">No BGP sessions.</p>}
        </div>
      )}

      {activeTab === 'announce' && (
        <div className="space-y-4">
          <div className="bg-slate-900 border border-slate-700 rounded-lg p-5">
            <h3 className="text-lg font-semibold text-white mb-4">Announce Prefix</h3>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
              <div><label className="block text-sm text-slate-400 mb-1">Prefix</label><input value={prefix} onChange={e => setPrefix(e.target.value)} className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white text-sm font-mono" placeholder="10.0.0.0/24" /></div>
              <div><label className="block text-sm text-slate-400 mb-1">Next Hop</label><input value={nextHop} onChange={e => setNextHop(e.target.value)} className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white text-sm font-mono" placeholder="192.168.1.1" /></div>
              <div><label className="block text-sm text-slate-400 mb-1">Community</label><input value={community} onChange={e => setCommunity(e.target.value)} className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white text-sm" placeholder="64512:100" /></div>
              <div className="flex items-end">
                <button onClick={handleAnnounce} className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm w-full transition-colors">Announce</button>
              </div>
            </div>
          </div>

          <div className="grid gap-4">
            <h3 className="text-lg font-semibold text-white">Active Announcements</h3>
            {announcements.map(a => (
              <div key={a.id} className="bg-slate-900 border border-slate-800 rounded-lg p-4 flex items-center justify-between">
                <div>
                  <span className="text-white font-mono font-medium">{a.prefix}</span>
                  <span className="text-slate-400 ml-3">via {a.next_hop}</span>
                  {a.community && <span className="text-xs text-slate-500 ml-2">community: {a.community}</span>}
                  <span className={`ml-3 text-xs px-1.5 py-0.5 rounded ${a.status === 'announced' ? 'bg-green-600 text-white' : 'bg-slate-700 text-slate-300'}`}>{a.status}</span>
                </div>
                <button onClick={() => handleWithdraw(a.prefix)} className="px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white text-xs rounded transition-colors">Withdraw</button>
              </div>
            ))}
            {announcements.length === 0 && <p className="text-slate-500 text-center py-4">No announcements.</p>}
          </div>
        </div>
      )}
    </div>
  );
};

export default BGPPage;
