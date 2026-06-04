import { useEffect, useState } from 'react';
import { FormattedMessage, useIntl } from 'react-intl';
import { apiClient } from '../../lib/api';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table';

interface DRPlan {
  id: string; name: string; plan_type: string; status: string;
  rpo_target_minutes: number; rto_target_minutes: number;
  last_tested: string | null; created_at: string; failover_order: string[];
}

export default function DROrchestrator() {
  const intl = useIntl();
  const [plans, setPlans] = useState<DRPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: '', plan_type: 'active-passive', rpo: 60, rto: 30 });

  useEffect(() => { loadPlans(); }, []);

  const loadPlans = async () => {
    try { const data = await apiClient.get('/api/v1/resiliency/dr/plans'); setPlans(data || []); }
    catch { toast.error('Failed to load DR plans'); }
    finally { setLoading(false); }
  };

  const createPlan = async () => {
    try {
      await apiClient.post('/api/v1/resiliency/dr/plans', {
        name: form.name, plan_type: form.plan_type,
        rpo_target_minutes: form.rpo, rto_target_minutes: form.rto,
      });
      toast.success('DR plan created');
      setShowForm(false);
      setForm({ name: '', plan_type: 'active-passive', rpo: 60, rto: 30 });
      loadPlans();
    } catch { toast.error('Failed to create plan'); }
  };

  const executeFailover = async (planId: string, isDrill: boolean) => {
    try {
      await apiClient.post(`/api/v1/resiliency/dr/plans/${planId}/failover`, { is_drill: isDrill });
      toast.success(isDrill ? 'DR drill started' : 'Failover initiated');
    } catch { toast.error('Failed to execute failover'); }
  };

  const runReadiness = async (planId: string) => {
    try {
      const result = await apiClient.post(`/api/v1/resiliency/dr/plans/${planId}/readiness`);
      toast.success(result.healthy ? 'All checks passed' : 'Readiness degraded');
      loadPlans();
    } catch { toast.error('Readiness check failed'); }
  };

  const deletePlan = async (planId: string) => {
    try { await apiClient.delete(`/api/v1/resiliency/dr/plans/${planId}`); toast.success('Plan deleted'); loadPlans(); }
    catch { toast.error('Failed to delete'); }
  };

  const statusColor: Record<string, string> = { ready: 'bg-green-500', degraded: 'bg-yellow-500', draft: 'bg-gray-500', failed: 'bg-red-500', archived: 'bg-slate-500' };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>;

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold"><FormattedMessage id="dr.title" defaultMessage="Disaster Recovery Orchestrator" /></h1>
          <p className="text-muted-foreground mt-1"><FormattedMessage id="dr.description" defaultMessage="Define DR plans, RPO/RTO targets, and manage failover" /></p>
        </div>
        <Button onClick={() => setShowForm(!showForm)}>{showForm ? 'Cancel' : 'New Plan'}</Button>
      </div>

      {showForm && (
        <Card>
          <CardHeader><CardTitle>Create DR Plan</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div><label className="block text-sm font-medium mb-1">Plan Name</label><input className="w-full border rounded p-2" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} /></div>
            <div><label className="block text-sm font-medium mb-1">Plan Type</label>
              <select className="w-full border rounded p-2" value={form.plan_type} onChange={e => setForm({ ...form, plan_type: e.target.value })}>
                <option value="active-passive">Active-Passive</option><option value="pilot-light">Pilot Light</option>
                <option value="warm-standby">Warm Standby</option><option value="active-active">Active-Active</option><option value="cold-standby">Cold Standby</option>
              </select></div>
            <div className="grid grid-cols-2 gap-4">
              <div><label className="block text-sm font-medium mb-1">RPO (minutes)</label><input className="w-full border rounded p-2" type="number" value={form.rpo} onChange={e => setForm({ ...form, rpo: +e.target.value })} /></div>
              <div><label className="block text-sm font-medium mb-1">RTO (minutes)</label><input className="w-full border rounded p-2" type="number" value={form.rto} onChange={e => setForm({ ...form, rto: +e.target.value })} /></div>
            </div>
            <Button onClick={createPlan}>Create Plan</Button>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader><CardTitle>DR Plans ({plans.length})</CardTitle></CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow><TableHead>Name</TableHead><TableHead>Type</TableHead><TableHead>Status</TableHead><TableHead>RPO</TableHead><TableHead>RTO</TableHead><TableHead>Last Tested</TableHead><TableHead>Actions</TableHead></TableRow>
            </TableHeader>
            <TableBody>
              {plans.map(p => (
                <TableRow key={p.id}>
                  <TableCell className="font-medium">{p.name}</TableCell>
                  <TableCell><Badge variant="outline">{p.plan_type}</Badge></TableCell>
                  <TableCell><Badge className={statusColor[p.status] || 'bg-gray-500'}>{p.status}</Badge></TableCell>
                  <TableCell>{p.rpo_target_minutes}m</TableCell>
                  <TableCell>{p.rto_target_minutes}m</TableCell>
                  <TableCell>{p.last_tested ? new Date(p.last_tested).toLocaleDateString() : 'Never'}</TableCell>
                  <TableCell>
                    <div className="flex gap-1">
                      <Button size="sm" variant="outline" onClick={() => runReadiness(p.id)}>Check</Button>
                      <Button size="sm" variant="default" onClick={() => executeFailover(p.id, true)}>Drill</Button>
                      <Button size="sm" variant="destructive" onClick={() => executeFailover(p.id, false)}>Failover</Button>
                      <Button size="sm" variant="ghost" onClick={() => deletePlan(p.id)}>Del</Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
              {plans.length === 0 && <TableRow><TableCell colSpan={7} className="text-center text-muted-foreground">No DR plans defined</TableCell></TableRow>}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}

function DRSummaryCards() {
  const [summary, setSummary] = useState({ total_plans: 0, ready_plans: 0, tested_last_30d: 0 });
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/dr/summary').then(d => setSummary(d || { total_plans: 0, ready_plans: 0, tested_last_30d: 0 })).catch(() => {});
  }, []);
  return (
    <div className="grid grid-cols-3 gap-3 mb-4">
      <div className="bg-slate-800 rounded-lg p-3 border border-slate-700 text-center">
        <div className="text-2xl font-bold text-white">{summary.total_plans}</div>
        <div className="text-xs text-slate-400">Total Plans</div>
      </div>
      <div className="bg-slate-800 rounded-lg p-3 border border-slate-700 text-center">
        <div className="text-2xl font-bold text-green-400">{summary.ready_plans}</div>
        <div className="text-xs text-slate-400">Ready</div>
      </div>
      <div className="bg-slate-800 rounded-lg p-3 border border-slate-700 text-center">
        <div className="text-2xl font-bold text-blue-400">{summary.tested_last_30d}</div>
        <div className="text-xs text-slate-400">Tested (30d)</div>
      </div>
    </div>
  );
}

function DRPlanTemplates() {
  const templates = [
    { name: 'Pilot Light', rpo: 60, rto: 30 },
    { name: 'Warm Standby', rpo: 15, rto: 10 },
    { name: 'Active-Active', rpo: 5, rto: 2 },
  ];
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mb-4">
      <h3 className="text-white font-semibold mb-3">Plan Templates</h3>
      <div className="grid grid-cols-3 gap-2">
        {templates.map((t, i) => (
          <div key={i} className="bg-slate-700 rounded p-3 text-center">
            <div className="text-white font-semibold text-sm">{t.name}</div>
            <div className="text-xs text-slate-400 mt-1">RPO: {t.rpo}m | RTO: {t.rto}m</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function DRReadinessCheckButton({ planId }: { planId: string }) {
  const handleCheck = async () => {
    const r = await apiClient.post(`/api/v1/resiliency/dr/plans/${planId}/readiness`);
    toast.success(r.healthy ? 'All checks passed' : 'Some checks failed');
  };
  return <button onClick={handleCheck} className="bg-emerald-600 text-white px-3 py-1.5 rounded text-xs hover:bg-emerald-700">Check Readiness</button>;
}

function DRReadinessChecklist() {
  const [checklist, setChecklist] = useState<any[]>([]);
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/dr/checklist').then(d => setChecklist(d || [])).catch(() => {});
  }, []);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Readiness Checklist</h3>
      {checklist.length === 0 && <p className="text-slate-400 text-sm">No items</p>}
      {checklist.slice(0, 5).map((c: any, i: number) => (
        <div key={i} className="flex items-center justify-between py-2 border-b border-slate-700 last:border-0 text-sm">
          <span className="text-slate-300">{c.item}</span>
          <span className={c.ready ? 'text-green-400' : 'text-red-400'}>{c.ready ? 'Ready' : 'Not Ready'}</span>
        </div>
      ))}
    </div>
  );
}

function DRPlanForm({ onSuccess }: { onSuccess: () => void }) {
  const [form, setForm] = useState({ name: '', plan_type: 'pilot_light', rpo: 60, rto: 30 });
  const handleCreate = async () => {
    await apiClient.post('/api/v1/resiliency/dr/plans', form);
    toast.success('DR Plan created');
    onSuccess();
  };
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mb-4">
      <h3 className="text-white font-semibold mb-3">Quick Create Plan</h3>
      <div className="grid grid-cols-2 gap-3">
        <input placeholder="Name" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} className="bg-slate-700 text-white p-2 rounded text-sm" />
        <select value={form.plan_type} onChange={e => setForm({ ...form, plan_type: e.target.value })} className="bg-slate-700 text-white p-2 rounded text-sm">
          <option value="pilot_light">Pilot Light</option><option value="warm_standby">Warm Standby</option><option value="active_active">Active-Active</option>
        </select>
      </div>
      <button onClick={handleCreate} className="mt-3 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 text-sm">Create</button>
    </div>
  );
}

function DRCompliancePanel({ planId }: { planId: string }) {
  const [compliance, setCompliance] = useState<any>(null);
  useEffect(() => {
    apiClient.get(`/api/v1/resiliency/dr/plans/${planId}/compliance`).then(d => setCompliance(d)).catch(() => {});
  }, [planId]);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">RPO/RTO Compliance</h3>
      {!compliance && <p className="text-slate-400 text-sm">No data</p>}
      {compliance && (
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">RPO</span><div className={compliance.rpo_compliant ? 'text-green-400' : 'text-red-400'}>{compliance.rpo_compliant ? 'Compliant' : 'Non-compliant'}</div></div>
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">RTO</span><div className={compliance.rto_compliant ? 'text-green-400' : 'text-red-400'}>{compliance.rto_compliant ? 'Compliant' : 'Non-compliant'}</div></div>
        </div>
      )}
    </div>
  );
}

function DRScenarioList() {
  const [scenarios, setScenarios] = useState<any[]>([]);
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/dr/scenarios').then(d => setScenarios(d || [])).catch(() => {});
  }, []);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">DR Scenarios</h3>
      {scenarios.length === 0 && <p className="text-slate-400 text-sm">No scenarios configured</p>}
      {scenarios.map((s, i) => (
        <div key={i} className="flex justify-between py-2 border-b border-slate-700 last:border-0 text-sm">
          <span className="text-slate-300">{s.name}</span>
          <span className={s.severity === 'critical' ? 'text-red-400' : s.severity === 'high' ? 'text-yellow-400' : 'text-slate-400'}>{s.severity}</span>
        </div>
      ))}
    </div>
  );
}

function DRVersionHistory({ planId }: { planId: string }) {
  const [versions, setVersions] = useState<any[]>([]);
  useEffect(() => {
    apiClient.get(`/api/v1/resiliency/dr/plans/${planId}/versions`).then(d => setVersions(d || [])).catch(() => {});
  }, [planId]);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Version History</h3>
      {versions.length === 0 && <p className="text-slate-400 text-sm">No version history</p>}
      {versions.map((v, i) => (
        <div key={i} className="flex justify-between py-2 border-b border-slate-700 last:border-0 text-sm">
          <span className="text-slate-300">v{v.version}</span>
          <span className="text-slate-400">{v.timestamp}</span>
        </div>
      ))}
    </div>
  );
}

function DRDrillSchedule() {
  const [drills, setDrills] = useState<any[]>([]);
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/dr/drills/upcoming').then(d => setDrills(d || [])).catch(() => {});
  }, []);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Upcoming Drills</h3>
      {drills.length === 0 && <p className="text-slate-400 text-sm">No scheduled drills</p>}
      {drills.map((d, i) => (
        <div key={i} className="flex justify-between py-2 border-b border-slate-700 last:border-0 text-sm">
          <span className="text-slate-300">{d.plan_name}</span>
          <span className="text-slate-400">{d.next_run}</span>
        </div>
      ))}
    </div>
  );
}

function DRResourceRequirements({ planId }: { planId: string }) {
  const [resources, setResources] = useState<any>(null);
  useEffect(() => {
    apiClient.get(`/api/v1/resiliency/dr/plans/${planId}/resources`).then(d => setResources(d)).catch(() => {});
  }, [planId]);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Resource Requirements</h3>
      {!resources && <p className="text-slate-400 text-sm">Loading...</p>}
      {resources && (
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Compute</span><div className="text-white">{resources.compute_vcpus} vCPUs</div></div>
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Memory</span><div className="text-white">{resources.memory_gb} GB</div></div>
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Storage</span><div className="text-white">{resources.storage_tb} TB</div></div>
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Bandwidth</span><div className="text-white">{resources.network_gbps} Gbps</div></div>
        </div>
      )}
    </div>
  );
}

function DRPostMortemView({ planId }: { planId: string }) {
  const [pm, setPm] = useState<any>(null);
  useEffect(() => {
    apiClient.get(`/api/v1/resiliency/dr/plans/${planId}/post-mortem`).then(d => setPm(d)).catch(() => {});
  }, [planId]);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Post-Mortem</h3>
      {!pm && <p className="text-slate-400 text-sm">No post-mortem available</p>}
      {pm && (
        <div className="text-sm text-slate-300">
          <p>Duration: {pm.duration_min}min</p>
          <p>Issues: {pm.issues_found}</p>
          <p>Action items: {pm.action_items}</p>
        </div>
      )}
    </div>
  );
}

function DRRunbookList() {
  const [runbooks, setRunbooks] = useState<any[]>([]);
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/dr/runbooks').then(d => setRunbooks(d || [])).catch(() => {});
  }, []);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">DR Runbooks</h3>
      {runbooks.length === 0 && <p className="text-slate-400 text-sm">No runbooks</p>}
      {runbooks.map((r, i) => (
        <div key={i} className="flex justify-between py-2 border-b border-slate-700 last:border-0 text-sm">
          <span className="text-slate-300">{r.name}</span>
          <span className="text-slate-400">{r.steps} steps</span>
        </div>
      ))}
    </div>
  );
}
