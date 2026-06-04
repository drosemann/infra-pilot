import { useEffect, useState } from 'react';
import { FormattedMessage } from 'react-intl';
import { apiClient } from '../../lib/api';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table';

interface BackupSLA {
  id: string; name: string; workload_name: string; category: string;
  backup_frequency_minutes: number; rpo_target_minutes: number; rto_target_minutes: number;
  active: boolean; created_at: string;
}

export default function BackupSLAManager() {
  const [slas, setSlas] = useState<BackupSLA[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: '', workload: '', category: 'medium', rpo: 60, rto: 120 });

  useEffect(() => { loadSlas(); }, []);

  const loadSlas = async () => {
    try { const data = await apiClient.get('/api/v1/resiliency/backup-sla'); setSlas(data || []); }
    catch { toast.error('Failed to load backup SLAs'); }
    finally { setLoading(false); }
  };

  const createSLA = async () => {
    try {
      await apiClient.post('/api/v1/resiliency/backup-sla', {
        name: form.name, workload_name: form.workload, category: form.category,
        backup_frequency_minutes: form.rpo, rpo_target_minutes: form.rpo, rto_target_minutes: form.rto,
      });
      toast.success('Backup SLA created'); setShowForm(false);
      setForm({ name: '', workload: '', category: 'medium', rpo: 60, rto: 120 }); loadSlas();
    } catch { toast.error('Failed to create SLA'); }
  };

  const runVerification = async (slaId: string) => {
    try { await apiClient.post(`/api/v1/resiliency/backup-sla/${slaId}/verify`); toast.success('Verification completed'); } catch { toast.error('Verification failed'); }
  };

  const deleteSLA = async (slaId: string) => {
    try { await apiClient.delete(`/api/v1/resiliency/backup-sla/${slaId}`); toast.success('SLA deleted'); loadSlas(); } catch { toast.error('Failed to delete'); }
  };

  const catColor: Record<string, string> = { critical: 'bg-red-500', high: 'bg-orange-500', medium: 'bg-yellow-500', low: 'bg-green-500' };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>;

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold"><FormattedMessage id="backupSla.title" defaultMessage="Backup SLA Manager" /></h1>
          <p className="text-muted-foreground mt-1">Define backup SLAs per workload with automated verification</p>
        </div>
        <Button onClick={() => setShowForm(!showForm)}>{showForm ? 'Cancel' : 'New SLA'}</Button>
      </div>

      {showForm && (
        <Card>
          <CardHeader><CardTitle>Create Backup SLA</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div><label className="block text-sm font-medium mb-1">SLA Name</label><input className="w-full border rounded p-2" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} /></div>
              <div><label className="block text-sm font-medium mb-1">Workload</label><input className="w-full border rounded p-2" value={form.workload} onChange={e => setForm({ ...form, workload: e.target.value })} /></div>
            </div>
            <div><label className="block text-sm font-medium mb-1">Category</label>
              <select className="w-full border rounded p-2" value={form.category} onChange={e => setForm({ ...form, category: e.target.value })}>
                <option value="critical">Critical</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option>
              </select></div>
            <div className="grid grid-cols-2 gap-4">
              <div><label className="block text-sm font-medium mb-1">RPO Target (min)</label><input className="w-full border rounded p-2" type="number" value={form.rpo} onChange={e => setForm({ ...form, rpo: +e.target.value })} /></div>
              <div><label className="block text-sm font-medium mb-1">RTO Target (min)</label><input className="w-full border rounded p-2" type="number" value={form.rto} onChange={e => setForm({ ...form, rto: +e.target.value })} /></div>
            </div>
            <Button onClick={createSLA}>Create SLA</Button>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader><CardTitle>Backup SLAs ({slas.length})</CardTitle></CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow><TableHead>Name</TableHead><TableHead>Workload</TableHead><TableHead>Category</TableHead><TableHead>RPO</TableHead><TableHead>RTO</TableHead><TableHead>Status</TableHead><TableHead>Actions</TableHead></TableRow>
            </TableHeader>
            <TableBody>
              {slas.map(s => (
                <TableRow key={s.id}>
                  <TableCell className="font-medium">{s.name}</TableCell>
                  <TableCell>{s.workload_name}</TableCell>
                  <TableCell><Badge className={catColor[s.category]}>{s.category}</Badge></TableCell>
                  <TableCell>{s.rpo_target_minutes}m</TableCell>
                  <TableCell>{s.rto_target_minutes}m</TableCell>
                  <TableCell><Badge variant={s.active ? 'default' : 'secondary'}>{s.active ? 'Active' : 'Inactive'}</Badge></TableCell>
                  <TableCell>
                    <div className="flex gap-1">
                      <Button size="sm" variant="outline" onClick={() => runVerification(s.id)}>Verify</Button>
                      <Button size="sm" variant="destructive" onClick={() => deleteSLA(s.id)}>Delete</Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
              {slas.length === 0 && <TableRow><TableCell colSpan={7} className="text-center text-muted-foreground">No backup SLAs defined</TableCell></TableRow>}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}

function BackupSLAFilterBar({ onFilter }: { onFilter: (filters: any) => void }) {
  const [category, setCategory] = useState('');
  const [active, setActive] = useState('');
  return (
    <div className="flex gap-3 flex-wrap items-end mb-3">
      <div>
        <label className="block text-xs text-slate-400 mb-1">Category</label>
        <select value={category} onChange={e => { setCategory(e.target.value); onFilter({ category: e.target.value, active }); }} className="bg-slate-800 text-white px-3 py-1.5 rounded border border-slate-700 text-sm">
          <option value="">All</option><option value="critical">Critical</option><option value="high">High</option><option value="medium">Medium</option>
        </select>
      </div>
      <div>
        <label className="block text-xs text-slate-400 mb-1">Status</label>
        <select value={active} onChange={e => { setActive(e.target.value); onFilter({ category, active: e.target.value }); }} className="bg-slate-800 text-white px-3 py-1.5 rounded border border-slate-700 text-sm">
          <option value="">All</option><option value="true">Active</option><option value="false">Inactive</option>
        </select>
      </div>
      <button onClick={() => { setCategory(''); setActive(''); onFilter({}); }} className="px-3 py-1.5 bg-slate-700 text-white rounded text-sm hover:bg-slate-600">Clear</button>
    </div>
  );
}

function BackupSLAComplianceGauge() {
  const [rate, setRate] = useState(78);
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/backup-sla/compliance').then(d => setRate(d?.compliance_rate ?? 78)).catch(() => {});
  }, []);
  const color = rate >= 90 ? 'text-green-400' : rate >= 70 ? 'text-yellow-400' : 'text-red-400';
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-white font-semibold mb-3">Compliance Rate</h3>
      <div className="text-center">
        <div className={`text-4xl font-bold ${color}`}>{rate}%</div>
        <div className="text-slate-400 text-sm mt-1">Last 7 days</div>
      </div>
    </div>
  );
}

function BackupSLAHistoryPanel() {
  const [history, setHistory] = useState<any[]>([]);
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/backup-sla/history').then(d => setHistory(d || [])).catch(() => {});
  }, []);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Verification History</h3>
      <table className="w-full text-sm">
        <thead><tr className="text-slate-400 border-b border-slate-700"><th className="text-left py-2">SLA</th><th className="text-left py-2">Result</th><th className="text-right py-2">Time</th></tr></thead>
        <tbody>{history.slice(0, 6).map((h: any, i: number) => (
          <tr key={i} className="border-b border-slate-700"><td className="py-2 text-white">{h.sla_name}</td><td className="py-2"><span className={h.passed ? 'text-green-400' : 'text-red-400'}>{h.passed ? 'Passed' : 'Failed'}</span></td><td className="py-2 text-right text-slate-400">{h.verified_at}</td></tr>
        ))}</tbody>
      </table>
    </div>
  );
}

function BackupSLAQuickForm({ onSuccess }: { onSuccess: () => void }) {
  const [form, setForm] = useState({ name: '', workload_name: '', category: 'medium', rpo: 60, rto: 120 });
  const handleCreate = async () => {
    await apiClient.post('/api/v1/resiliency/backup-sla', form);
    toast.success('SLA created');
    onSuccess();
  };
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mb-4">
      <h3 className="text-white font-semibold mb-3">Quick Create SLA</h3>
      <div className="grid grid-cols-3 gap-3">
        <input placeholder="Name" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} className="bg-slate-700 text-white p-2 rounded text-sm" />
        <input placeholder="Workload" value={form.workload_name} onChange={e => setForm({ ...form, workload_name: e.target.value })} className="bg-slate-700 text-white p-2 rounded text-sm" />
        <select value={form.category} onChange={e => setForm({ ...form, category: e.target.value })} className="bg-slate-700 text-white p-2 rounded text-sm">
          <option value="critical">Critical</option><option value="high">High</option><option value="medium">Medium</option>
        </select>
      </div>
      <button onClick={handleCreate} className="mt-3 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 text-sm">Create SLA</button>
    </div>
  );
}

function BackupPolicyList() {
  const [policies, setPolicies] = useState<any[]>([]);
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/backup-sla/policies').then(d => setPolicies(d || [])).catch(() => {});
  }, []);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Backup Policies</h3>
      {policies.length === 0 && <p className="text-slate-400 text-sm">No policies configured</p>}
      {policies.map((p, i) => (
        <div key={i} className="flex justify-between py-2 border-b border-slate-700 last:border-0 text-sm">
          <span className="text-slate-300">{p.name} ({p.backup_type})</span>
          <span className="text-slate-400">{p.retention_days}d</span>
        </div>
      ))}
    </div>
  );
}

function BackupStorageEstimator() {
  const [slaId, setSlaId] = useState('');
  const [sizeGb, setSizeGb] = useState(100);
  const [estimate, setEstimate] = useState<any>(null);
  const handleEstimate = async () => {
    const data = await apiClient.get(`/api/v1/resiliency/backup-sla/${slaId}/storage-cost?data_size_gb=${sizeGb}`);
    setEstimate(data);
  };
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Storage Cost Estimator</h3>
      <div className="flex gap-2 mb-3">
        <input placeholder="SLA ID" value={slaId} onChange={e => setSlaId(e.target.value)} className="bg-slate-700 text-white p-2 rounded text-sm flex-1" />
        <input type="number" placeholder="GB" value={sizeGb} onChange={e => setSizeGb(+e.target.value)} className="bg-slate-700 text-white p-2 rounded text-sm w-20" />
        <button onClick={handleEstimate} className="bg-blue-600 text-white px-3 py-2 rounded text-sm">Estimate</button>
      </div>
      {estimate?.tier_estimates?.map((t: any, i: number) => (
        <div key={i} className="flex justify-between py-1 text-sm"><span className="text-slate-300">{t.tier}</span><span className="text-white">${t.total_retention_cost}</span></div>
      ))}
    </div>
  );
}

function BackupJobTracker() {
  const [jobs, setJobs] = useState<any[]>([]);
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/backup-sla/jobs/active').then(d => setJobs(d || [])).catch(() => {});
  }, []);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Active Backup Jobs</h3>
      {jobs.length === 0 && <p className="text-slate-400 text-sm">No active jobs</p>}
      {jobs.map((j, i) => (
        <div key={i} className="flex justify-between py-2 border-b border-slate-700 last:border-0 text-sm">
          <span className="text-slate-300">{j.sla_name}</span>
          <div className="flex items-center gap-2">
            <div className="w-24 bg-slate-700 rounded h-2"><div className="bg-blue-500 rounded h-2" style={{ width: `${j.progress_pct}%` }} /></div>
            <span className="text-slate-400">{j.progress_pct}%</span>
          </div>
        </div>
      ))}
    </div>
  );
}

function BackupSLAComplianceSummary() {
  const [summary, setSummary] = useState<any>(null);
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/backup-sla/compliance-summary').then(d => setSummary(d)).catch(() => {});
  }, []);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Compliance Summary</h3>
      {!summary && <p className="text-slate-400 text-sm">Loading...</p>}
      {summary && (
        <div className="grid grid-cols-3 gap-3 text-sm">
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Audited</span><div className="text-white font-bold">{summary.audited_slas}</div></div>
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Compliant</span><div className="text-green-400 font-bold">{summary.compliant}</div></div>
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Rate</span><div className="text-blue-400 font-bold">{summary.compliance_rate}%</div></div>
        </div>
      )}
    </div>
  );
}

function BackupSLAObjectiveManager() {
  const [objectives, setObjectives] = useState<any[]>([]);
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/backup-sla/objectives').then(d => setObjectives(d || [])).catch(() => {});
  }, []);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">SLA Objectives</h3>
      {objectives.length === 0 && <p className="text-slate-400 text-sm">No objectives</p>}
      {objectives.map((o, i) => (
        <div key={i} className="flex justify-between py-2 border-b border-slate-700 last:border-0 text-sm">
          <span className="text-slate-300">{o.name}</span>
          <span className="text-slate-400">{o.target}</span>
        </div>
      ))}
    </div>
  );
}

function BackupSLAPenaltyTracker() {
  const [penalties, setPenalties] = useState<any>(null);
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/backup-sla/penalties').then(d => setPenalties(d)).catch(() => {});
  }, []);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Penalty Assessment</h3>
      {!penalties && <p className="text-slate-400 text-sm">Loading...</p>}
      {penalties && (
        <div className="text-sm text-slate-300">
          <p>YTD Penalty: <span className="text-white">{penalties.ytd_penalty}</span></p>
          <p>Breaches: {penalties.breaches}</p>
          <p>Allowable: {penalties.allowable_breaches}</p>
        </div>
      )}
    </div>
  );
}

function BackupSLATierAnalysis() {
  const [tiers, setTiers] = useState<any>(null);
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/backup-sla/tier-analysis').then(d => setTiers(d)).catch(() => {});
  }, []);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Tier Distribution</h3>
      {!tiers && <p className="text-slate-400 text-sm">No data</p>}
      {tiers?.tiers?.map((t: any, i: number) => (
        <div key={i} className="flex justify-between py-2 border-b border-slate-700 last:border-0 text-sm">
          <span className="text-slate-300">{t.name}</span>
          <span className="text-white">{t.count} ({t.percentage}%)</span>
        </div>
      ))}
    </div>
  );
}
