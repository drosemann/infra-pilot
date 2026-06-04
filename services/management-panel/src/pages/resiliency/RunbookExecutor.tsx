import { useEffect, useState } from 'react';
import { FormattedMessage } from 'react-intl';
import { apiClient } from '../../lib/api';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table';

interface Runbook {
  id: string; name: string; category: string; status: string;
  version: number; steps: any[]; created_at: string; last_executed: string | null;
}

export default function RunbookExecutor() {
  const [runbooks, setRunbooks] = useState<Runbook[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: '', category: 'disaster_recovery' });

  useEffect(() => { loadRunbooks(); }, []);

  const loadRunbooks = async () => {
    try { const data = await apiClient.get('/api/v1/resiliency/runbooks'); setRunbooks(data || []); }
    catch { toast.error('Failed to load runbooks'); }
    finally { setLoading(false); }
  };

  const createRunbook = async () => {
    try { await apiClient.post('/api/v1/resiliency/runbooks', form); toast.success('Runbook created'); setShowForm(false); loadRunbooks(); }
    catch { toast.error('Failed to create'); }
  };

  const executeRunbook = async (rbId: string) => {
    try { await apiClient.post(`/api/v1/resiliency/runbooks/${rbId}/execute`, {}); toast.success('Runbook execution started'); loadRunbooks(); }
    catch { toast.error('Failed to execute'); }
  };

  const deleteRunbook = async (rbId: string) => {
    try { await apiClient.delete(`/api/v1/resiliency/runbooks/${rbId}`); toast.success('Runbook deleted'); loadRunbooks(); }
    catch { toast.error('Failed to delete'); }
  };

  const categories = ['disaster_recovery', 'incident_response', 'security_incident', 'backup_restore', 'deployment', 'maintenance'];
  const statusColor: Record<string, string> = { draft: 'bg-gray-500', published: 'bg-green-500', archived: 'bg-slate-500' };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>;

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold"><FormattedMessage id="rbExec.title" defaultMessage="Automated Runbook Execution" /></h1>
          <p className="text-muted-foreground mt-1">Convert DR runbooks to executable workflows</p>
        </div>
        <Button onClick={() => setShowForm(!showForm)}>{showForm ? 'Cancel' : 'New Runbook'}</Button>
      </div>

      {showForm && (
        <Card>
          <CardHeader><CardTitle>Create Runbook</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div><label className="block text-sm font-medium mb-1">Name</label><input className="w-full border rounded p-2" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} /></div>
            <div><label className="block text-sm font-medium mb-1">Category</label>
              <select className="w-full border rounded p-2" value={form.category} onChange={e => setForm({ ...form, category: e.target.value })}>
                {categories.map(c => <option key={c} value={c}>{c.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</option>)}
              </select></div>
            <Button onClick={createRunbook}>Create Runbook</Button>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader><CardTitle>Runbooks ({runbooks.length})</CardTitle></CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow><TableHead>Name</TableHead><TableHead>Category</TableHead><TableHead>Status</TableHead><TableHead>Version</TableHead><TableHead>Steps</TableHead><TableHead>Last Executed</TableHead><TableHead>Actions</TableHead></TableRow>
            </TableHeader>
            <TableBody>
              {runbooks.map(r => (
                <TableRow key={r.id}>
                  <TableCell className="font-medium">{r.name}</TableCell>
                  <TableCell><Badge variant="outline">{r.category}</Badge></TableCell>
                  <TableCell><Badge className={statusColor[r.status]}>{r.status}</Badge></TableCell>
                  <TableCell>v{r.version}</TableCell>
                  <TableCell>{(r.steps || []).length}</TableCell>
                  <TableCell>{r.last_executed ? new Date(r.last_executed).toLocaleDateString() : 'Never'}</TableCell>
                  <TableCell>
                    <div className="flex gap-1">
                      <Button size="sm" variant="default" onClick={() => executeRunbook(r.id)}>Execute</Button>
                      <Button size="sm" variant="destructive" onClick={() => deleteRunbook(r.id)}>Delete</Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
              {runbooks.length === 0 && <TableRow><TableCell colSpan={7} className="text-center text-muted-foreground">No runbooks defined</TableCell></TableRow>}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}

function RunbookSummaryCards() {
  const [summary, setSummary] = useState({ total_runbooks: 0, completed: 0, failed: 0 });
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/runbooks/summary').then(d => setSummary(d || { total_runbooks: 0, completed: 0, failed: 0 })).catch(() => {});
  }, []);
  return (
    <div className="grid grid-cols-3 gap-3 mb-4">
      <div className="bg-slate-800 rounded-lg p-3 border border-slate-700 text-center">
        <div className="text-2xl font-bold text-white">{summary.total_runbooks}</div>
        <div className="text-xs text-slate-400">Total Runbooks</div>
      </div>
      <div className="bg-slate-800 rounded-lg p-3 border border-slate-700 text-center">
        <div className="text-2xl font-bold text-green-400">{summary.completed}</div>
        <div className="text-xs text-slate-400">Completed Executions</div>
      </div>
      <div className="bg-slate-800 rounded-lg p-3 border border-slate-700 text-center">
        <div className="text-2xl font-bold text-red-400">{summary.failed}</div>
        <div className="text-xs text-slate-400">Failed</div>
      </div>
    </div>
  );
}

function RunbookStepTypes() {
  const stepTypes = ['command', 'script', 'api_call', 'manual', 'webhook', 'notification', 'approval', 'condition'];
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mb-4">
      <h3 className="text-white font-semibold mb-3">Step Types</h3>
      <div className="flex flex-wrap gap-2">
        {stepTypes.map((t, i) => <span key={i} className="bg-slate-700 text-slate-300 px-2 py-1 rounded text-xs">{t}</span>)}
      </div>
    </div>
  );
}

function RunbookExecutionLog({ logs }: { logs: any[] }) {
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Execution Log</h3>
      <table className="w-full text-sm">
        <thead><tr className="text-slate-400 border-b border-slate-700"><th className="text-left py-2">Runbook</th><th className="text-left py-2">Status</th><th className="text-right py-2">Duration</th></tr></thead>
        <tbody>{logs.slice(0, 5).map((l: any, i: number) => (
          <tr key={i} className="border-b border-slate-700"><td className="py-2 text-white">{l.runbook_name}</td><td className="py-2"><span className={l.success ? 'text-green-400' : 'text-red-400'}>{l.success ? 'Success' : 'Failed'}</span></td><td className="py-2 text-right text-slate-400">{l.duration_seconds}s</td></tr>
        ))}</tbody>
      </table>
    </div>
  );
}

function RunbookQuickForm({ onSuccess }: { onSuccess: () => void }) {
  const [form, setForm] = useState({ name: '', category: 'general', severity: 'medium' });
  const handleCreate = async () => {
    await apiClient.post('/api/v1/resiliency/runbooks', { ...form, steps: [] });
    toast.success('Runbook created');
    onSuccess();
  };
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mb-4">
      <h3 className="text-white font-semibold mb-3">Quick Create Runbook</h3>
      <div className="grid grid-cols-3 gap-3">
        <input placeholder="Name" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} className="bg-slate-700 text-white p-2 rounded text-sm" />
        <select value={form.category} onChange={e => setForm({ ...form, category: e.target.value })} className="bg-slate-700 text-white p-2 rounded text-sm">
          <option value="general">General</option><option value="networking">Networking</option><option value="database">Database</option>
        </select>
        <select value={form.severity} onChange={e => setForm({ ...form, severity: e.target.value })} className="bg-slate-700 text-white p-2 rounded text-sm">
          <option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option><option value="critical">Critical</option>
        </select>
      </div>
      <button onClick={handleCreate} className="mt-3 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 text-sm">Create</button>
    </div>
  );
}

function RunbookVersionHistory() {
  const [versions, setVersions] = useState<any[]>([]);
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/runbooks/version-history').then(d => setVersions(d || [])).catch(() => {});
  }, []);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Version History</h3>
      {versions.length === 0 && <p className="text-slate-400 text-sm">No version history</p>}
      {versions.slice(0, 5).map((v, i) => (
        <div key={i} className="flex justify-between py-2 border-b border-slate-700 last:border-0 text-sm">
          <span className="text-slate-300">v{v.version}</span>
          <span className="text-slate-400">{v.updated_at}</span>
        </div>
      ))}
    </div>
  );
}

function RunbookApprovalQueue() {
  const [requests, setRequests] = useState<any[]>([]);
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/runbooks/approvals/pending').then(d => setRequests(d || [])).catch(() => {});
  }, []);
  const handleApprove = async (id: string) => {
    await apiClient.post(`/api/v1/resiliency/runbooks/approvals/${id}/approve`, { user: 'current-user' });
    toast.success('Approved');
    setRequests(prev => prev.filter(r => r.id !== id));
  };
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Pending Approvals</h3>
      {requests.length === 0 && <p className="text-slate-400 text-sm">No pending approvals</p>}
      {requests.slice(0, 5).map((r, i) => (
        <div key={i} className="flex items-center justify-between py-2 border-b border-slate-700 last:border-0 text-sm">
          <span className="text-slate-300">{r.runbook_name}</span>
          <button onClick={() => handleApprove(r.id)} className="bg-green-600 text-white px-2 py-1 rounded text-xs">Approve</button>
        </div>
      ))}
    </div>
  );
}

function RunbookAuditLog() {
  const [logs, setLogs] = useState<any[]>([]);
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/runbooks/audit-log').then(d => setLogs(d || [])).catch(() => {});
  }, []);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Audit Log</h3>
      <table className="w-full text-sm">
        <thead><tr className="text-slate-400 border-b border-slate-700"><th className="text-left py-2">Action</th><th className="text-left py-2">User</th><th className="text-right py-2">Time</th></tr></thead>
        <tbody>{logs.slice(0, 5).map((l, i) => (
          <tr key={i} className="border-b border-slate-700"><td className="py-2 text-white">{l.action}</td><td className="py-2 text-slate-300">{l.user}</td><td className="py-2 text-right text-slate-400">{l.timestamp}</td></tr>
        ))}</tbody>
      </table>
    </div>
  );
}

function RunbookStepViewer({ runbookId }: { runbookId: string }) {
  const [steps, setSteps] = useState<any[]>([]);
  useEffect(() => {
    apiClient.get(`/api/v1/resiliency/runbooks/${runbookId}/steps`).then(d => setSteps(d || [])).catch(() => {});
  }, [runbookId]);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Execution Steps</h3>
      {steps.length === 0 && <p className="text-slate-400 text-sm">No steps</p>}
      {steps.map((s, i) => (
        <div key={i} className="flex justify-between py-2 border-b border-slate-700 last:border-0 text-sm">
          <span className="text-slate-300">{s.name}</span>
          <span className={s.status === 'completed' ? 'text-green-400' : s.status === 'running' ? 'text-yellow-400' : 'text-slate-400'}>{s.status}</span>
        </div>
      ))}
    </div>
  );
}

function RunbookTimeoutConfig({ runbookId }: { runbookId: string }) {
  const [timeouts, setTimeouts] = useState<any>(null);
  useEffect(() => {
    apiClient.get(`/api/v1/resiliency/runbooks/${runbookId}/timeouts`).then(d => setTimeouts(d)).catch(() => {});
  }, [runbookId]);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Timeout Settings</h3>
      {!timeouts && <p className="text-slate-400 text-sm">No data</p>}
      {timeouts && (
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Step</span><div className="text-white">{timeouts.step_timeout}s</div></div>
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Total</span><div className="text-white">{timeouts.total_timeout}s</div></div>
        </div>
      )}
    </div>
  );
}

function RunbookMetricsPanel() {
  const [metrics, setMetrics] = useState<any>(null);
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/runbooks/metrics').then(d => setMetrics(d)).catch(() => {});
  }, []);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Runbook Metrics</h3>
      {!metrics && <p className="text-slate-400 text-sm">Loading...</p>}
      {metrics && (
        <div className="grid grid-cols-3 gap-3 text-sm">
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Executions</span><div className="text-white font-bold">{metrics.executions_30d}</div></div>
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Success Rate</span><div className="text-green-400 font-bold">{metrics.success_rate}%</div></div>
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Avg Duration</span><div className="text-white font-bold">{metrics.avg_duration}</div></div>
        </div>
      )}
    </div>
  );
}
