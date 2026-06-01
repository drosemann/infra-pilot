import { useEffect, useState } from 'react';
import { apiClient } from '../../lib/api';
import { toast } from 'sonner';

interface CellularModem { id: string; name: string; iccid: string; operator: string; status: string; signal_quality: number; data_used_mb: number; imei: string; imsi: string }
interface APNConfig { id: string; modem_id: string; apn: string; username: string; password: string; is_default: boolean }
interface FailoverConfig { id: string; modem_id: string; enabled: boolean; priority: number; trigger_condition: string; cooldown_seconds: number }

export const CellularPage = () => {
  const [modems, setModems] = useState<CellularModem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedModem, setSelectedModem] = useState<string | null>(null);
  const [apnConfig, setApnConfig] = useState<APNConfig | null>(null);
  const [failoverConfig, setFailoverConfig] = useState<FailoverConfig | null>(null);
  const [showSMS, setShowSMS] = useState(false);
  const [smsNumber, setSmsNumber] = useState('');
  const [smsMessage, setSmsMessage] = useState('');
  const [apnForm, setApnForm] = useState({ apn: '', username: '', password: '' });

  useEffect(() => { loadData(); }, []);
  useEffect(() => { if (selectedModem) loadDetails(); }, [selectedModem]);

  const loadData = async () => {
    setLoading(true);
    try {
      const d = await apiClient.get('/api/networking/cellular/modems');
      setModems(Array.isArray(d) ? d : d?.modems || []);
      if (d?.modems?.[0] && !selectedModem) setSelectedModem(d.modems[0].id);
    } catch { toast.error('Failed to load modems'); }
    finally { setLoading(false); }
  };

  const loadDetails = async () => {
    if (!selectedModem) return;
    try {
      const [a, f] = await Promise.all([
        apiClient.get(`/api/networking/cellular/modems/${selectedModem}/apn`),
        apiClient.get(`/api/networking/cellular/modems/${selectedModem}/failover`),
      ]);
      setApnConfig(a);
      setFailoverConfig(f);
      if (a) setApnForm({ apn: a.apn || '', username: a.username || '', password: '' });
    } catch { }
  };

  const handleConfigureAPN = async () => {
    if (!selectedModem) return;
    try {
      await apiClient.post(`/api/networking/cellular/modems/${selectedModem}/apn`, apnForm);
      toast.success('APN configured');
      loadDetails();
    } catch { toast.error('Failed to configure APN'); }
  };

  const handleSendSMS = async () => {
    if (!selectedModem || !smsNumber || !smsMessage) return;
    try {
      await apiClient.post(`/api/networking/cellular/modems/${selectedModem}/sms`, { number: smsNumber, message: smsMessage });
      toast.success('SMS sent');
      setSmsNumber(''); setSmsMessage(''); setShowSMS(false);
    } catch { toast.error('Failed to send SMS'); }
  };

  const handleToggleFailover = async () => {
    if (!selectedModem || !failoverConfig) return;
    try {
      await apiClient.post(`/api/networking/cellular/modems/${selectedModem}/failover`, { enabled: !failoverConfig.enabled, priority: failoverConfig.priority });
      toast.success(`Failover ${failoverConfig.enabled ? 'disabled' : 'enabled'}`);
      loadDetails();
    } catch { toast.error('Failed to update failover'); }
  };

  if (loading) return <div className="text-slate-400 p-8">Loading cellular modems...</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">5G/LTE Integration</h1>
          <p className="text-slate-400">Manage cellular modems, APN configurations, and failover</p>
        </div>
        <button onClick={loadData} className="px-4 py-2 bg-slate-800 border border-slate-700 text-slate-300 rounded-lg text-sm hover:bg-slate-700">Refresh</button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-1 space-y-2">
          <h2 className="text-lg font-semibold text-white mb-2">Modems</h2>
          {modems.map(m => (
            <div key={m.id} onClick={() => setSelectedModem(m.id)} className={`bg-slate-900 border rounded-lg p-4 cursor-pointer transition-colors ${selectedModem === m.id ? 'border-blue-500' : 'border-slate-800 hover:border-slate-700'}`}>
              <div className="flex items-center gap-2">
                <div className={`w-2.5 h-2.5 rounded-full ${m.status === 'connected' ? 'bg-green-500' : m.status === 'disconnected' ? 'bg-red-500' : 'bg-yellow-500'}`} />
                <span className="text-white font-medium">{m.name}</span>
              </div>
              <div className="text-xs text-slate-400 mt-1">
                <div>Signal: {m.signal_quality}% | Data: {m.data_used_mb} MB</div>
                <div className="font-mono">ICCID: {m.iccid?.slice(0, 14)}...</div>
              </div>
            </div>
          ))}
          {modems.length === 0 && <p className="text-slate-500 text-center py-4">No modems.</p>}
        </div>

        <div className="lg:col-span-2">
          {!selectedModem && <p className="text-slate-500 text-center py-8">Select a modem to manage.</p>}
          {selectedModem && (
            <div className="space-y-4">
              <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
                <h3 className="text-lg font-semibold text-white mb-3">Modem Details</h3>
                {(() => { const m = modems.find(x => x.id === selectedModem); if (!m) return null;
                  return (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div><span className="text-slate-400">Operator</span><p className="text-white">{m.operator}</p></div>
                      <div><span className="text-slate-400">Signal</span><p className="text-white">{m.signal_quality}%</p></div>
                      <div><span className="text-slate-400">Data Used</span><p className="text-white">{(m.data_used_mb / 1024).toFixed(2)} GB</p></div>
                      <div><span className="text-slate-400">Status</span><p className="text-white capitalize">{m.status}</p></div>
                      <div><span className="text-slate-400">IMEI</span><p className="text-white font-mono text-xs">{m.imei}</p></div>
                      <div><span className="text-slate-400">IMSI</span><p className="text-white font-mono text-xs">{m.imsi}</p></div>
                      <div><span className="text-slate-400">ICCID</span><p className="text-white font-mono text-xs">{m.iccid}</p></div>
                    </div>
                  );
                })()}
              </div>

              <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-lg font-semibold text-white">APN Configuration</h3>
                  <button onClick={handleConfigureAPN} className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded transition-colors">Save APN</button>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div><label className="block text-sm text-slate-400 mb-1">APN</label><input value={apnForm.apn} onChange={e => setApnForm({ ...apnForm, apn: e.target.value })} className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white text-sm" /></div>
                  <div><label className="block text-sm text-slate-400 mb-1">Username</label><input value={apnForm.username} onChange={e => setApnForm({ ...apnForm, username: e.target.value })} className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white text-sm" /></div>
                  <div><label className="block text-sm text-slate-400 mb-1">Password</label><input type="password" value={apnForm.password} onChange={e => setApnForm({ ...apnForm, password: e.target.value })} className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white text-sm" /></div>
                </div>
              </div>

              <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-lg font-semibold text-white">Failover Configuration</h3>
                  <button onClick={handleToggleFailover} className={`px-3 py-1.5 text-xs rounded transition-colors ${failoverConfig?.enabled ? 'bg-red-600 hover:bg-red-700 text-white' : 'bg-green-600 hover:bg-green-700 text-white'}`}>
                    {failoverConfig?.enabled ? 'Disable' : 'Enable'}
                  </button>
                </div>
                {failoverConfig && (
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div><span className="text-slate-400">Status</span><p className="text-white">{failoverConfig.enabled ? 'Enabled' : 'Disabled'}</p></div>
                    <div><span className="text-slate-400">Priority</span><p className="text-white">{failoverConfig.priority}</p></div>
                    <div><span className="text-slate-400">Trigger</span><p className="text-white">{failoverConfig.trigger_condition}</p></div>
                  </div>
                )}
              </div>

              <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-lg font-semibold text-white">SMS Messaging</h3>
                  <button onClick={() => setShowSMS(!showSMS)} className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded transition-colors">Send SMS</button>
                </div>
                {showSMS && (
                  <div className="space-y-3">
                    <div><label className="block text-sm text-slate-400 mb-1">Number</label><input value={smsNumber} onChange={e => setSmsNumber(e.target.value)} className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white text-sm" placeholder="+1234567890" /></div>
                    <div><label className="block text-sm text-slate-400 mb-1">Message</label><textarea value={smsMessage} onChange={e => setSmsMessage(e.target.value)} rows={3} className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white text-sm" /></div>
                    <button onClick={handleSendSMS} className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm">Send</button>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CellularPage;
