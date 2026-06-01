import { useEffect, useState } from 'react';
import { apiClient } from '../../lib/api';
import { toast } from 'sonner';

interface VPNServer {
  id: string; name: string; vpn_type: string; port: number; status: string; active_clients: number; config: string; public_key: string; private_key: string; created_at: string
}

interface VPNClient {
  id: string; server_id: string; name: string; allowed_ips: string; public_key: string; status: string; bytes_sent: number; bytes_received: number
}

export const VPNPage = () => {
  const [servers, setServers] = useState<VPNServer[]>([]);
  const [clients, setClients] = useState<VPNClient[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState('');
  const [newType, setNewType] = useState('wireguard');
  const [newPort, setNewPort] = useState(51820);
  const [selectedServer, setSelectedServer] = useState<string | null>(null);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [s, c] = await Promise.all([
        apiClient.get('/api/networking/vpn/servers'),
        selectedServer ? apiClient.get(`/api/networking/vpn/servers/${selectedServer}/clients`) : Promise.resolve([]),
      ]);
      setServers(Array.isArray(s) ? s : s?.servers || []);
      setClients(Array.isArray(c) ? c : c?.clients || []);
    } catch { toast.error('Failed to load VPN data'); }
    finally { setLoading(false); }
  };

  useEffect(() => { if (selectedServer) loadData(); }, [selectedServer]);

  const handleCreate = async () => {
    try {
      await apiClient.post('/api/networking/vpn/servers', { name: newName, vpn_type: newType, port: newPort });
      toast.success('VPN server created');
      setShowCreate(false); setNewName(''); loadData();
    } catch { toast.error('Failed to create VPN server'); }
  };

  const handleDelete = async (id: string) => {
    try {
      await apiClient.delete(`/api/networking/vpn/servers/${id}`);
      toast.success('VPN server deleted');
      if (selectedServer === id) setSelectedServer(null);
      loadData();
    } catch { toast.error('Failed to delete'); }
  };

  const getClientConfig = async (serverId: string, clientId: string) => {
    try {
      const res = await apiClient.get(`/api/networking/vpn/servers/${serverId}/clients/${clientId}/config`);
      const cfg = res?.config || 'No config';
      navigator.clipboard.writeText(cfg);
      toast.success('Config copied to clipboard');
    } catch { toast.error('Failed to get config'); }
  };

  if (loading) return <div className="text-slate-400 p-8">Loading VPN...</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">VPN as a Service</h1>
          <p className="text-slate-400">Manage VPN servers and client configurations</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => { setShowCreate(!showCreate); setNewName(''); }} className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm transition-colors">+ New Server</button>
          <button onClick={loadData} className="px-4 py-2 bg-slate-800 border border-slate-700 text-slate-300 rounded-lg text-sm hover:bg-slate-700 transition-colors">Refresh</button>
        </div>
      </div>

      {showCreate && (
        <div className="bg-slate-900 border border-slate-700 rounded-lg p-5">
          <h3 className="text-lg font-semibold text-white mb-4">Create VPN Server</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div>
              <label className="block text-sm text-slate-400 mb-1">Name</label>
              <input value={newName} onChange={e => setNewName(e.target.value)} className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white text-sm" placeholder="My VPN" />
            </div>
            <div>
              <label className="block text-sm text-slate-400 mb-1">Type</label>
              <select value={newType} onChange={e => setNewType(e.target.value)} className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white text-sm">
                <option value="wireguard">WireGuard</option>
                <option value="openvpn">OpenVPN</option>
                <option value="ipsec">IPSec</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-slate-400 mb-1">Port</label>
              <input type="number" value={newPort} onChange={e => setNewPort(parseInt(e.target.value) || 51820)} className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white text-sm" />
            </div>
          </div>
          <div className="flex gap-2">
            <button onClick={handleCreate} className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm transition-colors">Create</button>
            <button onClick={() => setShowCreate(false)} className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded text-sm transition-colors">Cancel</button>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-1 space-y-2">
          <h2 className="text-lg font-semibold text-white mb-2">Servers</h2>
          {servers.map(s => (
            <div key={s.id} onClick={() => setSelectedServer(s.id)} className={`bg-slate-900 border rounded-lg p-4 cursor-pointer transition-colors ${selectedServer === s.id ? 'border-blue-500' : 'border-slate-800 hover:border-slate-700'}`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className={`w-2.5 h-2.5 rounded-full ${s.status === 'running' ? 'bg-green-500' : 'bg-red-500'}`} />
                  <span className="text-white font-medium">{s.name}</span>
                </div>
                <button onClick={(e) => { e.stopPropagation(); handleDelete(s.id); }} className="text-red-400 hover:text-red-300 text-xs">Delete</button>
              </div>
              <div className="text-xs text-slate-400 mt-2">{s.vpn_type} : {s.port} | Clients: {s.active_clients}</div>
            </div>
          ))}
        </div>
        <div className="lg:col-span-2">
          <h2 className="text-lg font-semibold text-white mb-2">Clients {selectedServer && `- ${servers.find(s => s.id === selectedServer)?.name}`}</h2>
          {!selectedServer && <p className="text-slate-500 text-center py-8">Select a server to view clients.</p>}
          {selectedServer && clients.length === 0 && <p className="text-slate-500 text-center py-8">No clients for this server.</p>}
          {selectedServer && clients.map(c => (
            <div key={c.id} className="bg-slate-900 border border-slate-800 rounded-lg p-4 mb-2">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <div className={`w-2.5 h-2.5 rounded-full ${c.status === 'active' ? 'bg-green-500' : 'bg-slate-500'}`} />
                  <span className="text-white font-medium">{c.name}</span>
                </div>
                <button onClick={() => getClientConfig(selectedServer, c.id)} className="px-3 py-1 bg-slate-700 hover:bg-slate-600 text-white text-xs rounded transition-colors">Copy Config</button>
              </div>
              <div className="grid grid-cols-3 gap-3 text-xs">
                <div><span className="text-slate-400">Allowed IPs</span><p className="text-white font-mono">{c.allowed_ips}</p></div>
                <div><span className="text-slate-400">Sent</span><p className="text-white">{(c.bytes_sent / 1024 / 1024).toFixed(2)} MB</p></div>
                <div><span className="text-slate-400">Received</span><p className="text-white">{(c.bytes_received / 1024 / 1024).toFixed(2)} MB</p></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default VPNPage;
