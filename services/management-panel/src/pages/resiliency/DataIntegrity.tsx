import { useEffect, useState } from 'react';
import { FormattedMessage } from 'react-intl';
import { apiClient } from '../../lib/api';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table';

interface Verification {
  id: string; name: string; resource_name: string;
  verification_type: string; replicas: any[]; auto_repair: boolean;
  active: boolean; last_status: string | null; last_run: string | null;
}

export default function DataIntegrity() {
  const [verifications, setVerifications] = useState<Verification[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: '', resource: '', vtype: 'checksum' });

  useEffect(() => { loadVerifications(); }, []);

  const loadVerifications = async () => {
    try { const data = await apiClient.get('/api/v1/resiliency/data-integrity/verifications'); setVerifications(data || []); }
    catch { toast.error('Failed to load verifications'); }
    finally { setLoading(false); }
  };

  const createVerification = async () => {
    try { await apiClient.post('/api/v1/resiliency/data-integrity/verifications', { name: form.name, resource_name: form.resource, verification_type: form.vtype }); toast.success('Verification created'); setShowForm(false); loadVerifications(); }
    catch { toast.error('Failed to create'); }
  };

  const runVerification = async (verId: string) => {
    try { await apiClient.post(`/api/v1/resiliency/data-integrity/verifications/${verId}/run`); toast.success('Verification completed'); loadVerifications(); }
    catch { toast.error('Failed to run'); }
  };

  const deleteVerification = async (verId: string) => {
    try { await apiClient.delete(`/api/v1/resiliency/data-integrity/verifications/${verId}`); toast.success('Verification deleted'); loadVerifications(); }
    catch { toast.error('Failed to delete'); }
  };

  const vtypes = ['checksum', 'row_count', 'schema_compare', 'sample_compare', 'replica_lag', 'backup_restore'];

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>;

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold"><FormattedMessage id="di.title" defaultMessage="Data Integrity Verification" /></h1>
          <p className="text-muted-foreground mt-1">Periodic checksum/consistency validation across replicas and backups</p>
        </div>
        <Button onClick={() => setShowForm(!showForm)}>{showForm ? 'Cancel' : 'New Verification'}</Button>
      </div>

      {showForm && (
        <Card>
          <CardHeader><CardTitle>Create Verification</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div><label className="block text-sm font-medium mb-1">Name</label><input className="w-full border rounded p-2" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} /></div>
              <div><label className="block text-sm font-medium mb-1">Resource</label><input className="w-full border rounded p-2" value={form.resource} onChange={e => setForm({ ...form, resource: e.target.value })} /></div>
            </div>
            <div><label className="block text-sm font-medium mb-1">Verification Type</label>
              <select className="w-full border rounded p-2" value={form.vtype} onChange={e => setForm({ ...form, vtype: e.target.value })}>
                {vtypes.map(t => <option key={t} value={t}>{t.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</option>)}
              </select></div>
            <Button onClick={createVerification}>Create</Button>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader><CardTitle>Verifications ({verifications.length})</CardTitle></CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow><TableHead>Name</TableHead><TableHead>Resource</TableHead><TableHead>Type</TableHead><TableHead>Replicas</TableHead><TableHead>Auto-Repair</TableHead><TableHead>Last Status</TableHead><TableHead>Actions</TableHead></TableRow>
            </TableHeader>
            <TableBody>
              {verifications.map(v => (
                <TableRow key={v.id}>
                  <TableCell className="font-medium">{v.name}</TableCell>
                  <TableCell>{v.resource_name}</TableCell>
                  <TableCell><Badge variant="outline">{v.verification_type}</Badge></TableCell>
                  <TableCell>{(v.replicas || []).length}</TableCell>
                  <TableCell>{v.auto_repair ? '✅' : '❌'}</TableCell>
                  <TableCell>{v.last_status ? <Badge variant={v.last_status === 'passed' ? 'default' : 'destructive'}>{v.last_status}</Badge> : 'Never'}</TableCell>
                  <TableCell>
                    <div className="flex gap-1">
                      <Button size="sm" variant="default" onClick={() => runVerification(v.id)}>Verify</Button>
                      <Button size="sm" variant="destructive" onClick={() => deleteVerification(v.id)}>Del</Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
              {verifications.length === 0 && <TableRow><TableCell colSpan={7} className="text-center text-muted-foreground">No verifications configured</TableCell></TableRow>}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}

function DataIntegrityStatsCard() {
  const [stats, setStats] = useState({ total: 0, active: 0, passed: 0 });
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/data-integrity/summary').then(d => setStats(d || { total: 0, active: 0, passed: 0 })).catch(() => {});
  }, []);
  return (
    <div className="grid grid-cols-3 gap-3 mb-4">
      <div className="bg-slate-800 rounded-lg p-3 border border-slate-700 text-center">
        <div className="text-2xl font-bold text-white">{stats.total}</div>
        <div className="text-xs text-slate-400">Total Checks</div>
      </div>
      <div className="bg-slate-800 rounded-lg p-3 border border-slate-700 text-center">
        <div className="text-2xl font-bold text-green-400">{stats.active}</div>
        <div className="text-xs text-slate-400">Active</div>
      </div>
      <div className="bg-slate-800 rounded-lg p-3 border border-slate-700 text-center">
        <div className="text-2xl font-bold text-blue-400">{stats.passed}</div>
        <div className="text-xs text-slate-400">Last 7d Passed</div>
      </div>
    </div>
  );
}

function DataIntegrityVerificationTypes() {
  const types = ['checksum', 'row_count', 'schema_match', 'drift_check', 'replication_lag'];
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mb-4">
      <h3 className="text-white font-semibold mb-3">Verification Types</h3>
      <div className="flex flex-wrap gap-2">
        {types.map((t, i) => <span key={i} className="bg-slate-700 text-slate-300 px-2 py-1 rounded text-xs">{t}</span>)}
      </div>
    </div>
  );
}

function DataIntegrityChecksumSummary({ verifications }: { verifications: any[] }) {
  const passed = verifications.filter((v: any) => v.status === 'passed').length;
  const total = verifications.length;
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Checksum Summary</h3>
      <div className="grid grid-cols-3 gap-3 text-sm">
        <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Total</span><div className="text-white font-bold">{total}</div></div>
        <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Passed</span><div className="text-green-400 font-bold">{passed}</div></div>
        <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Rate</span><div className="text-blue-400 font-bold">{total ? ((passed / total) * 100).toFixed(0) : 0}%</div></div>
      </div>
    </div>
  );
}

function DataIntegrityRepairModal({ verificationId, onDone }: { verificationId: string; onDone: () => void }) {
  const [replica, setReplica] = useState('');
  const handleRepair = async () => {
    await apiClient.post(`/api/v1/resiliency/data-integrity/${verificationId}/repair`, { replica_name: replica });
    toast.success('Repair initiated');
    onDone();
  };
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-white font-semibold mb-3">Trigger Repair</h3>
      <input placeholder="Replica name" value={replica} onChange={e => setReplica(e.target.value)} className="bg-slate-700 text-white p-2 rounded text-sm w-full mb-3" />
      <button onClick={handleRepair} className="bg-orange-600 text-white px-4 py-2 rounded hover:bg-orange-700 text-sm">Repair</button>
      <button onClick={onDone} className="ml-2 bg-slate-600 text-white px-4 py-2 rounded text-sm">Cancel</button>
    </div>
  );
}

function IntegritySchedulePanel() {
  const [schedules, setSchedules] = useState<any[]>([]);
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/data-integrity/schedules').then(d => setSchedules(d || [])).catch(() => {});
  }, []);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Verification Schedules</h3>
      {schedules.length === 0 && <p className="text-slate-400 text-sm">No schedules</p>}
      {schedules.map((s, i) => (
        <div key={i} className="flex justify-between py-2 border-b border-slate-700 last:border-0 text-sm">
          <span className="text-slate-300">{s.type} - {s.resource_id}</span>
          <span className={s.status === 'active' ? 'text-green-400' : 'text-slate-400'}>{s.status}</span>
        </div>
      ))}
    </div>
  );
}

function IntegrityAlertList() {
  const [alerts, setAlerts] = useState<any[]>([]);
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/data-integrity/alerts/active').then(d => setAlerts(d || [])).catch(() => {});
  }, []);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Active Integrity Alerts</h3>
      {alerts.length === 0 && <p className="text-slate-400 text-sm">No active alerts</p>}
      {alerts.map((a, i) => (
        <div key={i} className="flex justify-between py-2 border-b border-slate-700 last:border-0 text-sm">
          <span className="text-slate-300">{a.type} - {a.resource}</span>
          <span className={a.severity === 'high' ? 'text-red-400' : 'text-yellow-400'}>{a.severity}</span>
        </div>
      ))}
    </div>
  );
}

function IntegrityAuditView() {
  const [entries, setEntries] = useState<any[]>([]);
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/data-integrity/audit-log').then(d => setEntries(d || [])).catch(() => {});
  }, []);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Audit Log</h3>
      <table className="w-full text-sm">
        <thead><tr className="text-slate-400 border-b border-slate-700"><th className="text-left py-2">Event</th><th className="text-left py-2">Resource</th><th className="text-right py-2">Time</th></tr></thead>
        <tbody>{entries.slice(0, 5).map((e, i) => (
          <tr key={i} className="border-b border-slate-700"><td className="py-2 text-white">{e.event_type}</td><td className="py-2 text-slate-300">{e.resource_id}</td><td className="py-2 text-right text-slate-400">{e.timestamp}</td></tr>
        ))}</tbody>
      </table>
    </div>
  );
}

function IntegrityDashboard() {
  const [data, setData] = useState<any>(null);
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/data-integrity/dashboard').then(d => setData(d)).catch(() => {});
  }, []);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Dashboard</h3>
      {!data && <p className="text-slate-400 text-sm">Loading...</p>}
      {data && (
        <div className="grid grid-cols-4 gap-3 text-sm">
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Verifications</span><div className="text-white font-bold">{data.total_verifications}</div></div>
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Results</span><div className="text-white font-bold">{data.total_results}</div></div>
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Alerts</span><div className="text-red-400 font-bold">{data.alerts?.length || 0}</div></div>
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Consistency</span><div className="text-green-400 font-bold">{data.consistency?.overall_consistency || 0}%</div></div>
        </div>
      )}
    </div>
  );
}

function IntegrityRepairRunner() {
  const [repairs, setRepairs] = useState<any[]>([]);
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/data-integrity/repairs/pending').then(d => setRepairs(d || [])).catch(() => {});
  }, []);
  const runRepair = async (id: string) => {
    await apiClient.post(`/api/v1/resiliency/data-integrity/repairs/${id}/execute`, {});
    toast.success('Repair executed');
    setRepairs(prev => prev.filter(r => r.id !== id));
  };
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Pending Repairs</h3>
      {repairs.length === 0 && <p className="text-slate-400 text-sm">No pending repairs</p>}
      {repairs.slice(0, 5).map((r, i) => (
        <div key={i} className="flex items-center justify-between py-2 border-b border-slate-700 last:border-0 text-sm">
          <span className="text-slate-300">{r.dataset} ({r.type})</span>
          <button onClick={() => runRepair(r.id)} className="bg-blue-600 text-white px-2 py-1 rounded text-xs">Run</button>
        </div>
      ))}
    </div>
  );
}

function IntegrityChecksumVerifier() {
  const [checksums, setChecksums] = useState<any>(null);
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/data-integrity/checksums').then(d => setChecksums(d)).catch(() => {});
  }, []);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Checksum Status</h3>
      {!checksums && <p className="text-slate-400 text-sm">Loading...</p>}
      {checksums && (
        <div className="grid grid-cols-3 gap-3 text-sm">
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Checked</span><div className="text-white font-bold">{checksums.records_checked}</div></div>
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Mismatches</span><div className="text-green-400 font-bold">{checksums.mismatches}</div></div>
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Coverage</span><div className="text-blue-400 font-bold">{checksums.coverage}%</div></div>
        </div>
      )}
    </div>
  );
}

function IntegrityReplicationCheck() {
  const [repl, setRepl] = useState<any>(null);
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/data-integrity/replication').then(d => setRepl(d)).catch(() => {});
  }, []);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Replication Integrity</h3>
      {!repl && <p className="text-slate-400 text-sm">No data</p>}
      {repl && (
        <div className="text-sm text-slate-300">
          <p>Primary replicas: {repl.primary_healthy}/{repl.primary_total} healthy</p>
          <p>Secondary replicas: {repl.secondary_healthy}/{repl.secondary_total} healthy</p>
          <p>Consistency: <span className={repl.consistent ? 'text-green-400' : 'text-red-400'}>{repl.consistent ? 'Passed' : 'Failed'}</span></p>
        </div>
      )}
    </div>
  );
}
