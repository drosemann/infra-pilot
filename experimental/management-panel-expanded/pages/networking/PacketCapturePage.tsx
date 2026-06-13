import { useEffect, useState } from 'react';
import { apiClient } from '../../lib/api';
import { toast } from 'sonner';

interface CaptureSession { id: string; name: string; interface: string; filter: string; status: string; packet_count: number; duration: number; started_at: string; file_size_bytes: number }
interface CapturedPacket { id: string; session_id: string; timestamp: string; src_ip: string; dst_ip: string; protocol: string; length: number; src_port: number; dst_port: number; flags: string }

export const PacketCapturePage = () => {
  const [sessions, setSessions] = useState<CaptureSession[]>([]);
  const [packets, setPackets] = useState<CapturedPacket[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedSession, setSelectedSession] = useState<string | null>(null);
  const [showNew, setShowNew] = useState(false);
  const [newCapture, setNewCapture] = useState({ name: '', interface: 'eth0', filter: '', duration: 60 });
  const [protocolFilter, setProtocolFilter] = useState('');

  useEffect(() => { loadSessions(); }, []);
  useEffect(() => { if (selectedSession) loadPackets(); }, [selectedSession]);

  const loadSessions = async () => {
    setLoading(true);
    try {
      const data = await apiClient.get('/api/networking/capture/sessions');
      setSessions(Array.isArray(data) ? data : data?.sessions || []);
    } catch { toast.error('Failed to load sessions'); }
    finally { setLoading(false); }
  };

  const loadPackets = async () => {
    if (!selectedSession) return;
    try {
      const data = await apiClient.get(`/api/networking/capture/sessions/${selectedSession}/packets`);
      setPackets(Array.isArray(data) ? data : data?.packets || []);
    } catch { toast.error('Failed to load packets'); }
  };

  const handleStart = async () => {
    try {
      await apiClient.post('/api/networking/capture/sessions', newCapture);
      toast.success('Capture started');
      setShowNew(false);
      loadSessions();
    } catch { toast.error('Failed to start capture'); }
  };

  const handleStop = async (id: string) => {
    try {
      await apiClient.post(`/api/networking/capture/sessions/${id}/stop`, {});
      toast.success('Capture stopped');
      loadSessions();
    } catch { toast.error('Failed to stop'); }
  };

  const handleAnalyze = async (id: string) => {
    try {
      const data = await apiClient.get(`/api/networking/capture/sessions/${id}/analysis`);
      const analysis = data?.analysis || data;
      const msg = [`Packets: ${analysis.total_packets}`, `Protocols: ${analysis.protocol_summary || 'N/A'}`, `Top Talkers: ${analysis.top_talkers || 'N/A'}`].join('\n');
      toast.success(msg, { duration: 5000 });
    } catch { toast.error('Analysis failed'); }
  };

  if (loading) return <div className="text-slate-400 p-8">Loading captures...</div>;

  const filteredPackets = protocolFilter ? packets.filter(p => p.protocol === protocolFilter) : packets;
  const protocols = [...new Set(packets.map(p => p.protocol))];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Packet Capture Studio</h1>
          <p className="text-slate-400">Capture and analyze network traffic</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => setShowNew(!showNew)} className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm transition-colors">+ New Capture</button>
          <button onClick={loadSessions} className="px-4 py-2 bg-slate-800 border border-slate-700 text-slate-300 rounded-lg text-sm hover:bg-slate-700">Refresh</button>
        </div>
      </div>

      {showNew && (
        <div className="bg-slate-900 border border-slate-700 rounded-lg p-5">
          <h3 className="text-lg font-semibold text-white mb-4">Start New Capture</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
            <div><label className="block text-sm text-slate-400 mb-1">Name</label><input value={newCapture.name} onChange={e => setNewCapture({ ...newCapture, name: e.target.value })} className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white text-sm" placeholder="capture-1" /></div>
            <div><label className="block text-sm text-slate-400 mb-1">Interface</label><input value={newCapture.interface} onChange={e => setNewCapture({ ...newCapture, interface: e.target.value })} className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white text-sm font-mono" /></div>
            <div><label className="block text-sm text-slate-400 mb-1">BPF Filter</label><input value={newCapture.filter} onChange={e => setNewCapture({ ...newCapture, filter: e.target.value })} className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white text-sm font-mono" placeholder="port 80" /></div>
            <div><label className="block text-sm text-slate-400 mb-1">Duration (s)</label><input type="number" value={newCapture.duration} onChange={e => setNewCapture({ ...newCapture, duration: parseInt(e.target.value) || 60 })} className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white text-sm" /></div>
          </div>
          <button onClick={handleStart} className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded text-sm transition-colors">Start Capture</button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        <div className="lg:col-span-1 space-y-2">
          <h2 className="text-lg font-semibold text-white mb-2">Sessions</h2>
          {sessions.map(s => (
            <div key={s.id} onClick={() => setSelectedSession(s.id)} className={`bg-slate-900 border rounded-lg p-3 cursor-pointer transition-colors ${selectedSession === s.id ? 'border-blue-500' : 'border-slate-800 hover:border-slate-700'}`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className={`w-2.5 h-2.5 rounded-full ${s.status === 'active' ? 'bg-green-500' : s.status === 'completed' ? 'bg-blue-500' : 'bg-red-500'}`} />
                  <span className="text-white text-sm font-medium">{s.name}</span>
                </div>
                {s.status === 'active' && <button onClick={(e) => { e.stopPropagation(); handleStop(s.id); }} className="text-red-400 text-xs hover:text-red-300">Stop</button>}
              </div>
              <div className="text-xs text-slate-400 mt-1">{s.interface} | {s.packet_count} packets | {(s.file_size_bytes / 1024).toFixed(1)} KB</div>
            </div>
          ))}
        </div>

        <div className="lg:col-span-3">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg font-semibold text-white">
              Packets {selectedSession && sessions.find(s => s.id === selectedSession) ? `- ${sessions.find(s => s.id === selectedSession)?.name}` : ''}
            </h2>
            <div className="flex gap-2 items-center">
              {protocols.map(p => (
                <button key={p} onClick={() => setProtocolFilter(protocolFilter === p ? '' : p)} className={`px-2 py-1 text-xs rounded ${protocolFilter === p ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-400'}`}>{p}</button>
              ))}
              {selectedSession && <button onClick={() => handleAnalyze(selectedSession)} className="px-3 py-1.5 bg-slate-800 border border-slate-700 text-slate-300 rounded text-xs hover:bg-slate-700">Analyze</button>}
            </div>
          </div>

          {!selectedSession && <p className="text-slate-500 text-center py-8">Select a session to view packets.</p>}
          {selectedSession && (
            <div className="bg-slate-900 border border-slate-800 rounded-lg overflow-hidden">
              <table className="w-full text-sm">
                <thead><tr className="text-slate-400 text-xs border-b border-slate-800">
                  <th className="text-left px-3 py-2">Time</th><th className="text-left px-3 py-2">Source</th><th className="text-left px-3 py-2">Dest</th><th className="text-left px-3 py-2">Proto</th><th className="text-right px-3 py-2">Length</th><th className="text-left px-3 py-2">Flags</th>
                </tr></thead>
                <tbody>
                  {filteredPackets.slice(0, 100).map(p => (
                    <tr key={p.id} className="border-b border-slate-800 hover:bg-slate-800/50 text-white">
                      <td className="px-3 py-2 text-xs text-slate-400 font-mono">{p.timestamp?.split('T')[1]?.split('.')[0] || p.timestamp}</td>
                      <td className="px-3 py-2 font-mono text-xs">{p.src_ip}:{p.src_port}</td>
                      <td className="px-3 py-2 font-mono text-xs">{p.dst_ip}:{p.dst_port}</td>
                      <td className="px-3 py-2"><span className="text-xs bg-slate-800 text-blue-400 px-1.5 py-0.5 rounded font-mono">{p.protocol}</span></td>
                      <td className="px-3 py-2 text-right">{p.length} B</td>
                      <td className="px-3 py-2 text-xs text-slate-400">{p.flags || '-'}</td>
                    </tr>
                  ))}
                  {filteredPackets.length === 0 && <tr><td colSpan={6} className="text-center py-4 text-slate-500">No packets captured yet.</td></tr>}
                </tbody>
              </table>
              {filteredPackets.length > 100 && <p className="text-xs text-slate-500 text-center py-2">Showing 100 of {filteredPackets.length} packets</p>}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PacketCapturePage;
