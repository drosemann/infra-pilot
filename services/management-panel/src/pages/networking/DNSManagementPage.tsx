import { useEffect, useState } from 'react';
import { apiClient } from '../../lib/api';
import { toast } from 'sonner';

interface DNSZone { id: string; zone_name: string; record_count: number; serial: number; dnssec_enabled: boolean; created_at: string }
interface DNSRecord { id: string; zone_id: string; name: string; type: string; value: string; ttl: number; priority: number }

export const DNSManagementPage = () => {
  const [zones, setZones] = useState<DNSZone[]>([]);
  const [records, setRecords] = useState<DNSRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedZone, setSelectedZone] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [showAddRecord, setShowAddRecord] = useState(false);
  const [newRecord, setNewRecord] = useState({ name: '', type: 'A', value: '', ttl: 300, priority: 0 });

  useEffect(() => { loadZones(); }, []);
  useEffect(() => { if (selectedZone) loadRecords(); }, [selectedZone]);

  const loadZones = async () => {
    setLoading(true);
    try {
      const data = await apiClient.get('/api/networking/dns/zones');
      setZones(Array.isArray(data) ? data : data?.zones || []);
    } catch { toast.error('Failed to load zones'); }
    finally { setLoading(false); }
  };

  const loadRecords = async () => {
    if (!selectedZone) return;
    try {
      const data = await apiClient.get(`/api/networking/dns/zones/${selectedZone}/records`);
      setRecords(Array.isArray(data) ? data : data?.records || []);
    } catch { toast.error('Failed to load records'); }
  };

  const handleAddRecord = async () => {
    if (!selectedZone) return;
    try {
      await apiClient.post(`/api/networking/dns/zones/${selectedZone}/records`, newRecord);
      toast.success('Record added');
      setShowAddRecord(false);
      setNewRecord({ name: '', type: 'A', value: '', ttl: 300, priority: 0 });
      loadRecords();
    } catch { toast.error('Failed to add record'); }
  };

  const handleDeleteRecord = async (recordId: string) => {
    if (!selectedZone) return;
    try {
      await apiClient.delete(`/api/networking/dns/zones/${selectedZone}/records/${recordId}`);
      toast.success('Record deleted');
      loadRecords();
    } catch { toast.error('Failed to delete record'); }
  };

  const handleExportZone = async (zoneName: string) => {
    try {
      const data = await apiClient.get(`/api/networking/dns/zones/${selectedZone}/export`);
      const zf = data?.zone_file || '';
      const blob = new Blob([zf], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a'); a.href = url; a.download = `${zoneName}.zone`; a.click();
      URL.revokeObjectURL(url);
      toast.success('Zone file downloaded');
    } catch { toast.error('Failed to export zone'); }
  };

  if (loading) return <div className="text-slate-400 p-8">Loading DNS zones...</div>;

  const filteredZones = zones.filter(z => z.zone_name.includes(search));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">DNS Management Console</h1>
          <p className="text-slate-400">Manage DNS zones, records, and DNSSEC</p>
        </div>
        <div className="flex gap-2">
          <button onClick={loadZones} className="px-4 py-2 bg-slate-800 border border-slate-700 text-slate-300 rounded-lg text-sm hover:bg-slate-700 transition-colors">Refresh</button>
        </div>
      </div>

      <div className="relative max-w-md">
        <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search zones..." className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-1 space-y-2">
          <h2 className="text-lg font-semibold text-white mb-2">Zones ({filteredZones.length})</h2>
          {filteredZones.map(z => (
            <div key={z.id} onClick={() => setSelectedZone(z.id)} className={`bg-slate-900 border rounded-lg p-4 cursor-pointer transition-colors ${selectedZone === z.id ? 'border-blue-500' : 'border-slate-800 hover:border-slate-700'}`}>
              <div className="flex items-center justify-between">
                <span className="text-white font-medium">{z.zone_name}</span>
                {z.dnssec_enabled && <span className="text-xs bg-green-600 text-white px-1.5 py-0.5 rounded">DNSSEC</span>}
              </div>
              <div className="text-xs text-slate-400 mt-1">{z.record_count} records | Serial: {z.serial}</div>
            </div>
          ))}
        </div>

        <div className="lg:col-span-2">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg font-semibold text-white">Records {selectedZone && `- ${zones.find(z => z.id === selectedZone)?.zone_name}`}</h2>
            {selectedZone && (
              <div className="flex gap-2">
                <button onClick={() => handleExportZone(zones.find(z => z.id === selectedZone)?.zone_name || 'zone')} className="px-3 py-1.5 bg-slate-800 border border-slate-700 text-slate-300 rounded text-xs hover:bg-slate-700">Export Zone</button>
                <button onClick={() => setShowAddRecord(true)} className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs transition-colors">+ Add Record</button>
              </div>
            )}
          </div>

          {!selectedZone && <p className="text-slate-500 text-center py-8">Select a zone to view records.</p>}

          {showAddRecord && (
            <div className="bg-slate-900 border border-slate-700 rounded-lg p-4 mb-4">
              <h3 className="text-sm font-semibold text-white mb-3">New Record</h3>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-3">
                <div><label className="block text-xs text-slate-400 mb-1">Name</label><input value={newRecord.name} onChange={e => setNewRecord({...newRecord, name: e.target.value})} className="w-full px-2 py-1.5 bg-slate-800 border border-slate-700 rounded text-white text-sm" placeholder="www" /></div>
                <div><label className="block text-xs text-slate-400 mb-1">Type</label><select value={newRecord.type} onChange={e => setNewRecord({...newRecord, type: e.target.value})} className="w-full px-2 py-1.5 bg-slate-800 border border-slate-700 rounded text-white text-sm"><option value="A">A</option><option value="AAAA">AAAA</option><option value="CNAME">CNAME</option><option value="MX">MX</option><option value="TXT">TXT</option><option value="NS">NS</option><option value="SRV">SRV</option></select></div>
                <div className="col-span-2"><label className="block text-xs text-slate-400 mb-1">Value</label><input value={newRecord.value} onChange={e => setNewRecord({...newRecord, value: e.target.value})} className="w-full px-2 py-1.5 bg-slate-800 border border-slate-700 rounded text-white text-sm" placeholder="192.168.1.1" /></div>
                <div><label className="block text-xs text-slate-400 mb-1">TTL</label><input type="number" value={newRecord.ttl} onChange={e => setNewRecord({...newRecord, ttl: parseInt(e.target.value) || 300})} className="w-full px-2 py-1.5 bg-slate-800 border border-slate-700 rounded text-white text-sm" /></div>
              </div>
              <div className="flex gap-2">
                <button onClick={handleAddRecord} className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs transition-colors">Add</button>
                <button onClick={() => setShowAddRecord(false)} className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-white rounded text-xs transition-colors">Cancel</button>
              </div>
            </div>
          )}

          {selectedZone && records.map(r => (
            <div key={r.id} className="bg-slate-900 border border-slate-800 rounded-lg p-3 mb-2 flex items-center justify-between">
              <div className="flex items-center gap-4">
                <span className="text-xs font-mono bg-slate-800 text-blue-400 px-2 py-0.5 rounded">{r.type}</span>
                <div>
                  <span className="text-white text-sm">{r.name}</span>
                  <span className="text-slate-400 text-sm ml-2">{r.value}</span>
                </div>
                <span className="text-xs text-slate-500">TTL: {r.ttl}s</span>
              </div>
              <button onClick={() => handleDeleteRecord(r.id)} className="text-red-400 hover:text-red-300 text-xs">Delete</button>
            </div>
          ))}
          {selectedZone && records.length === 0 && <p className="text-slate-500 text-center py-8">No records in this zone.</p>}
        </div>
      </div>
    </div>
  );
};

export default DNSManagementPage;
