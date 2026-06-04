import { useEffect, useState } from 'react';
import { FormattedMessage } from 'react-intl';
import { apiClient } from '../../lib/api';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table';

interface Pipeline {
  id: string; name: string; repository: string; branch: string;
  tests: any[]; gate_strategy: string; active: boolean;
  created_at: string; last_run: string | null;
}

export default function ResiliencePipeline() {
  const [pipelines, setPipelines] = useState<Pipeline[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: '', repo: '', branch: 'main' });

  useEffect(() => { loadPipelines(); }, []);

  const loadPipelines = async () => {
    try { const data = await apiClient.get('/api/v1/resiliency/pipelines'); setPipelines(data || []); }
    catch { toast.error('Failed to load pipelines'); }
    finally { setLoading(false); }
  };

  const createPipeline = async () => {
    try { await apiClient.post('/api/v1/resiliency/pipelines', { name: form.name, repository: form.repo, branch: form.branch }); toast.success('Pipeline created'); setShowForm(false); loadPipelines(); }
    catch { toast.error('Failed to create'); }
  };

  const triggerPipeline = async (pipelineId: string) => {
    try { await apiClient.post(`/api/v1/resiliency/pipelines/${pipelineId}/trigger`, { event: 'manual' }); toast.success('Pipeline triggered'); loadPipelines(); }
    catch { toast.error('Failed to trigger'); }
  };

  const deletePipeline = async (pipelineId: string) => {
    try { await apiClient.delete(`/api/v1/resiliency/pipelines/${pipelineId}`); toast.success('Pipeline deleted'); loadPipelines(); }
    catch { toast.error('Failed to delete'); }
  };

  const testTypes = ['chaos_experiment', 'dependency_simulation', 'data_integrity', 'failover_test', 'load_test', 'circuit_breaker_test'];
  const gateStrategies = ['all_pass', 'critical_only', 'score_threshold', 'manual_review'];

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>;

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold"><FormattedMessage id="resPipe.title" defaultMessage="Resilience Testing Pipeline" /></h1>
          <p className="text-muted-foreground mt-1">CI/CD integration with chaos/resilience tests and gating</p>
        </div>
        <Button onClick={() => setShowForm(!showForm)}>{showForm ? 'Cancel' : 'New Pipeline'}</Button>
      </div>

      {showForm && (
        <Card>
          <CardHeader><CardTitle>Create Pipeline</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div><label className="block text-sm font-medium mb-1">Name</label><input className="w-full border rounded p-2" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} /></div>
            <div className="grid grid-cols-2 gap-4">
              <div><label className="block text-sm font-medium mb-1">Repository URL</label><input className="w-full border rounded p-2" value={form.repo} onChange={e => setForm({ ...form, repo: e.target.value })} /></div>
              <div><label className="block text-sm font-medium mb-1">Branch</label><input className="w-full border rounded p-2" value={form.branch} onChange={e => setForm({ ...form, branch: e.target.value })} /></div>
            </div>
            <Button onClick={createPipeline}>Create</Button>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader><CardTitle>Pipelines ({pipelines.length})</CardTitle></CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow><TableHead>Name</TableHead><TableHead>Branch</TableHead><TableHead>Tests</TableHead><TableHead>Gate Strategy</TableHead><TableHead>Active</TableHead><TableHead>Last Run</TableHead><TableHead>Actions</TableHead></TableRow>
            </TableHeader>
            <TableBody>
              {pipelines.map(p => (
                <TableRow key={p.id}>
                  <TableCell className="font-medium">{p.name}</TableCell>
                  <TableCell>{p.branch}</TableCell>
                  <TableCell>{(p.tests || []).length}</TableCell>
                  <TableCell><Badge variant="outline">{p.gate_strategy}</Badge></TableCell>
                  <TableCell>{p.active ? '✅' : '❌'}</TableCell>
                  <TableCell>{p.last_run ? new Date(p.last_run).toLocaleDateString() : 'Never'}</TableCell>
                  <TableCell>
                    <div className="flex gap-1">
                      <Button size="sm" variant="default" onClick={() => triggerPipeline(p.id)}>Trigger</Button>
                      <Button size="sm" variant="destructive" onClick={() => deletePipeline(p.id)}>Del</Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
              {pipelines.length === 0 && <TableRow><TableCell colSpan={7} className="text-center text-muted-foreground">No pipelines configured</TableCell></TableRow>}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}

function PipelineSummaryCards() {
  const [summary, setSummary] = useState({ total_pipelines: 0, active_pipelines: 0, pass_rate: 0 });
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/pipelines/summary').then(d => setSummary(d || { total_pipelines: 0, active_pipelines: 0, pass_rate: 0 })).catch(() => {});
  }, []);
  return (
    <div className="grid grid-cols-3 gap-3 mb-4">
      <div className="bg-slate-800 rounded-lg p-3 border border-slate-700 text-center">
        <div className="text-2xl font-bold text-white">{summary.total_pipelines}</div>
        <div className="text-xs text-slate-400">Total Pipelines</div>
      </div>
      <div className="bg-slate-800 rounded-lg p-3 border border-slate-700 text-center">
        <div className="text-2xl font-bold text-green-400">{summary.active_pipelines}</div>
        <div className="text-xs text-slate-400">Active</div>
      </div>
      <div className="bg-slate-800 rounded-lg p-3 border border-slate-700 text-center">
        <div className="text-2xl font-bold text-blue-400">{summary.pass_rate}%</div>
        <div className="text-xs text-slate-400">Pass Rate</div>
      </div>
    </div>
  );
}

function PipelineTemplateSelector() {
  const templates = [
    { name: 'Quick Health Check', tests: ['latency', 'availability'] },
    { name: 'Full Validation', tests: ['latency', 'availability', 'failover', 'data_integrity'] },
  ];
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mb-4">
      <h3 className="text-white font-semibold mb-3">Templates</h3>
      <div className="grid grid-cols-2 gap-2">
        {templates.map((t, i) => (
          <div key={i} className="bg-slate-700 rounded p-3">
            <div className="text-white font-semibold text-sm">{t.name}</div>
            <div className="text-xs text-slate-400 mt-1">Tests: {t.tests.join(', ')}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function PipelineRunHistory({ pipelines }: { pipelines: any[] }) {
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Recent Pipeline Runs</h3>
      <table className="w-full text-sm">
        <thead><tr className="text-slate-400 border-b border-slate-700"><th className="text-left py-2">Pipeline</th><th className="text-right py-2">Result</th><th className="text-right py-2">Duration</th></tr></thead>
        <tbody>{pipelines.slice(0, 5).map((p: any, i: number) => (
          <tr key={i} className="border-b border-slate-700"><td className="py-2 text-white">{p.name}</td><td className="py-2 text-right"><span className={p.passed ? 'text-green-400' : 'text-red-400'}>{p.passed ? 'Passed' : 'Failed'}</span></td><td className="py-2 text-right text-slate-400">{p.duration}s</td></tr>
        ))}</tbody>
      </table>
    </div>
  );
}

function PipelineQuickForm({ onSuccess }: { onSuccess: () => void }) {
  const [form, setForm] = useState({ name: '', strategy: 'all_pass', score_threshold: 75 });
  const handleCreate = async () => {
    await apiClient.post('/api/v1/resiliency/pipelines', form);
    toast.success('Pipeline created');
    onSuccess();
  };
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mb-4">
      <h3 className="text-white font-semibold mb-3">Quick Create Pipeline</h3>
      <div className="grid grid-cols-3 gap-3">
        <input placeholder="Name" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} className="bg-slate-700 text-white p-2 rounded text-sm" />
        <select value={form.strategy} onChange={e => setForm({ ...form, strategy: e.target.value })} className="bg-slate-700 text-white p-2 rounded text-sm">
          <option value="all_pass">All Pass</option><option value="weighted">Weighted</option><option value="critical_only">Critical Only</option>
        </select>
        <input type="number" value={form.score_threshold} onChange={e => setForm({ ...form, score_threshold: +e.target.value })} className="bg-slate-700 text-white p-2 rounded text-sm" />
      </div>
      <button onClick={handleCreate} className="mt-3 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 text-sm">Create</button>
    </div>
  );
}

function PipelineStepConfig({ pipelineName }: { pipelineName: string }) {
  const [steps, setSteps] = useState<any[]>([]);
  useEffect(() => {
    apiClient.get(`/api/v1/resiliency/pipelines/name/${pipelineName}/steps`).then(d => setSteps(d || [])).catch(() => {});
  }, [pipelineName]);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Pipeline Steps</h3>
      {steps.length === 0 && <p className="text-slate-400 text-sm">No steps configured</p>}
      {steps.map((s, i) => (
        <div key={i} className="flex justify-between py-2 border-b border-slate-700 last:border-0 text-sm">
          <span className="text-slate-300">{s.name} ({s.type})</span>
          <span className={s.status === 'passed' ? 'text-green-400' : 'text-slate-400'}>{s.status}</span>
        </div>
      ))}
    </div>
  );
}

function PipelineWebhookList({ pipelineName }: { pipelineName: string }) {
  const [webhooks, setWebhooks] = useState<any[]>([]);
  useEffect(() => {
    apiClient.get(`/api/v1/resiliency/pipelines/name/${pipelineName}/webhooks`).then(d => setWebhooks(d || [])).catch(() => {});
  }, [pipelineName]);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Webhooks</h3>
      {webhooks.length === 0 && <p className="text-slate-400 text-sm">No webhooks</p>}
      {webhooks.map((w, i) => (
        <div key={i} className="flex justify-between py-2 border-b border-slate-700 last:border-0 text-sm">
          <span className="text-slate-300">{w.events?.join(', ')}</span>
          <span className="text-slate-400">{w.status}</span>
        </div>
      ))}
    </div>
  );
}

function PipelineAnalyticsPanel() {
  const [stats, setStats] = useState<any>(null);
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/pipelines/analytics').then(d => setStats(d)).catch(() => {});
  }, []);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Pipeline Analytics</h3>
      {!stats && <p className="text-slate-400 text-sm">Loading...</p>}
      {stats && (
        <div className="grid grid-cols-4 gap-3 text-sm">
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Total</span><div className="text-white font-bold">{stats.total_pipelines}</div></div>
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Runs</span><div className="text-white font-bold">{stats.total_runs}</div></div>
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Success</span><div className="text-green-400 font-bold">{stats.success_rate}%</div></div>
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Avg Duration</span><div className="text-white font-bold">{stats.avg_duration_seconds}s</div></div>
        </div>
      )}
    </div>
  );
}

function PipelineTriggerList({ pipelineName }: { pipelineName: string }) {
  const [triggers, setTriggers] = useState<any[]>([]);
  useEffect(() => {
    apiClient.get(`/api/v1/resiliency/pipelines/name/${pipelineName}/triggers`).then(d => setTriggers(d || [])).catch(() => {});
  }, [pipelineName]);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Triggers</h3>
      {triggers.length === 0 && <p className="text-slate-400 text-sm">No triggers configured</p>}
      {triggers.map((t, i) => (
        <div key={i} className="flex justify-between py-2 border-b border-slate-700 last:border-0 text-sm">
          <span className="text-slate-300">{t.type} {t.cron || t.event_type}</span>
          <span className={t.status === 'active' ? 'text-green-400' : 'text-slate-400'}>{t.status}</span>
        </div>
      ))}
    </div>
  );
}

function PipelineRetryConfig({ pipelineName }: { pipelineName: string }) {
  const [config, setConfig] = useState<any>(null);
  useEffect(() => {
    apiClient.get(`/api/v1/resiliency/pipelines/name/${pipelineName}/retry-config`).then(d => setConfig(d)).catch(() => {});
  }, [pipelineName]);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Retry Configuration</h3>
      {!config && <p className="text-slate-400 text-sm">No config</p>}
      {config && (
        <div className="grid grid-cols-3 gap-3 text-sm">
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Max Retries</span><div className="text-white font-bold">{config.max_retries}</div></div>
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Backoff</span><div className="text-white">{config.backoff_seconds}s</div></div>
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Exponential</span><div className={config.exponential_backoff ? 'text-green-400' : 'text-slate-400'}>{config.exponential_backoff ? 'Yes' : 'No'}</div></div>
        </div>
      )}
    </div>
  );
}

function PipelineArtifactList({ runId }: { runId: string }) {
  const [artifacts, setArtifacts] = useState<any[]>([]);
  useEffect(() => {
    apiClient.get(`/api/v1/resiliency/pipelines/runs/${runId}/artifacts`).then(d => setArtifacts(d || [])).catch(() => {});
  }, [runId]);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Artifacts</h3>
      {artifacts.length === 0 && <p className="text-slate-400 text-sm">No artifacts</p>}
      {artifacts.map((a, i) => (
        <div key={i} className="flex justify-between py-2 border-b border-slate-700 last:border-0 text-sm">
          <span className="text-slate-300">{a.type}</span>
          <span className="text-slate-400">{a.size}</span>
        </div>
      ))}
    </div>
  );
}

function PipelineDependencyList({ pipelineName }: { pipelineName: string }) {
  const [deps, setDeps] = useState<any>(null);
  useEffect(() => {
    apiClient.get(`/api/v1/resiliency/pipelines/name/${pipelineName}/dependencies`).then(d => setDeps(d)).catch(() => {});
  }, [pipelineName]);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Dependencies</h3>
      {!deps && <p className="text-slate-400 text-sm">No data</p>}
      {deps && (
        <div className="text-sm text-slate-300">
          <p>Upstream: {deps.upstream_pipelines?.join(', ')}</p>
          <p>Downstream: {deps.downstream_pipelines?.join(', ')}</p>
          <p>External: {deps.external_services?.join(', ')}</p>
        </div>
      )}
    </div>
  );
}
