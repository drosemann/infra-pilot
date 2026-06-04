import { useEffect, useState } from 'react';
import { FormattedMessage } from 'react-intl';
import { apiClient } from '../../lib/api';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table';

interface ChaosExperiment {
  id: string; name: string; target: string; fault_type: string;
  status: string; approved: boolean; created_at: string; last_run: string | null;
}

export default function ChaosValidation() {
  const [experiments, setExperiments] = useState<ChaosExperiment[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: '', target: 'primary_database', fault_type: 'kill_container' });

  useEffect(() => { loadExperiments(); }, []);

  const loadExperiments = async () => {
    try { const data = await apiClient.get('/api/v1/resiliency/chaos/experiments'); setExperiments(data || []); }
    catch { toast.error('Failed to load experiments'); }
    finally { setLoading(false); }
  };

  const createExperiment = async () => {
    try { await apiClient.post('/api/v1/resiliency/chaos/experiments', form); toast.success('Experiment created'); setShowForm(false); loadExperiments(); }
    catch { toast.error('Failed to create'); }
  };

  const approveExperiment = async (expId: string) => {
    try { await apiClient.post(`/api/v1/resiliency/chaos/experiments/${expId}/approve`); toast.success('Experiment approved'); loadExperiments(); }
    catch { toast.error('Failed to approve'); }
  };

  const runExperiment = async (expId: string) => {
    try { await apiClient.post(`/api/v1/resiliency/chaos/experiments/${expId}/run`); toast.success('Experiment started'); loadExperiments(); }
    catch { toast.error('Failed to run'); }
  };

  const deleteExperiment = async (expId: string) => {
    try { await apiClient.delete(`/api/v1/resiliency/chaos/experiments/${expId}`); toast.success('Experiment deleted'); loadExperiments(); }
    catch { toast.error('Failed to delete'); }
  };

  const targets = ['primary_database', 'secondary_database', 'load_balancer', 'api_gateway', 'cache_cluster', 'message_queue', 'dns_service', 'storage_backend'];

  const statusColor: Record<string, string> = { created: 'bg-gray-500', scheduled: 'bg-blue-500', running: 'bg-orange-500', completed: 'bg-green-500', failed: 'bg-red-500', cancelled: 'bg-slate-500' };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>;

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold"><FormattedMessage id="chaosVal.title" defaultMessage="Chaos Recovery Validation" /></h1>
          <p className="text-muted-foreground mt-1">Scheduled chaos experiments validating DR procedures</p>
        </div>
        <Button onClick={() => setShowForm(!showForm)}>{showForm ? 'Cancel' : 'New Experiment'}</Button>
      </div>

      {showForm && (
        <Card>
          <CardHeader><CardTitle>Create Chaos Experiment</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div><label className="block text-sm font-medium mb-1">Name</label><input className="w-full border rounded p-2" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} /></div>
            <div><label className="block text-sm font-medium mb-1">Target</label>
              <select className="w-full border rounded p-2" value={form.target} onChange={e => setForm({ ...form, target: e.target.value })}>
                {targets.map(t => <option key={t} value={t}>{t.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</option>)}
              </select></div>
            <div><label className="block text-sm font-medium mb-1">Fault Type</label><input className="w-full border rounded p-2" value={form.fault_type} onChange={e => setForm({ ...form, fault_type: e.target.value })} /></div>
            <Button onClick={createExperiment}>Create</Button>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader><CardTitle>Chaos Experiments ({experiments.length})</CardTitle></CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow><TableHead>Name</TableHead><TableHead>Target</TableHead><TableHead>Fault</TableHead><TableHead>Status</TableHead><TableHead>Approved</TableHead><TableHead>Last Run</TableHead><TableHead>Actions</TableHead></TableRow>
            </TableHeader>
            <TableBody>
              {experiments.map(e => (
                <TableRow key={e.id}>
                  <TableCell className="font-medium">{e.name}</TableCell>
                  <TableCell><Badge variant="outline">{e.target.replace(/_/g, ' ')}</Badge></TableCell>
                  <TableCell className="text-sm">{e.fault_type}</TableCell>
                  <TableCell><Badge className={statusColor[e.status]}>{e.status}</Badge></TableCell>
                  <TableCell>{e.approved ? '✅' : '❌'}</TableCell>
                  <TableCell>{e.last_run ? new Date(e.last_run).toLocaleDateString() : 'Never'}</TableCell>
                  <TableCell>
                    <div className="flex gap-1">
                      {!e.approved && <Button size="sm" variant="outline" onClick={() => approveExperiment(e.id)}>Approve</Button>}
                      <Button size="sm" variant="default" onClick={() => runExperiment(e.id)}>Run</Button>
                      <Button size="sm" variant="destructive" onClick={() => deleteExperiment(e.id)}>Del</Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
              {experiments.length === 0 && <TableRow><TableCell colSpan={7} className="text-center text-muted-foreground">No experiments defined</TableCell></TableRow>}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}

function ChaosPassRateCard() {
  const [stats, setStats] = useState({ total: 0, passed: 0 });
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/chaos/summary').then(d => setStats(d || { total: 0, passed: 0 })).catch(() => {});
  }, []);
  const rate = stats.total > 0 ? Math.round(stats.passed / stats.total * 100) : 0;
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-white font-semibold mb-3">Pass Rate</h3>
      <div className="text-center">
        <div className={`text-3xl font-bold ${rate >= 80 ? 'text-green-400' : rate >= 50 ? 'text-yellow-400' : 'text-red-400'}`}>{rate}%</div>
        <div className="text-slate-400 text-sm">{stats.passed}/{stats.total} experiments</div>
      </div>
    </div>
  );
}

function ChaosTemplateSelector() {
  const templates = [
    { name: 'Network Latency', fault: 'network_latency', target: 'all_services' },
    { name: 'Instance Kill', fault: 'process_kill', target: 'random_instance' },
    { name: 'DNS Failure', fault: 'dns_failure', target: 'all_services' },
  ];
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-white font-semibold mb-3">Templates</h3>
      <div className="grid grid-cols-3 gap-2">
        {templates.map((t, i) => (
          <button key={i} className="bg-slate-700 hover:bg-slate-600 text-white p-2 rounded text-xs text-left">
            <div className="font-semibold">{t.name}</div>
            <div className="text-slate-400">{t.fault}</div>
          </button>
        ))}
      </div>
    </div>
  );
}

function ChaosScheduleList({ experiments }: { experiments: any[] }) {
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Scheduled Experiments</h3>
      {experiments.length === 0 && <p className="text-slate-400 text-sm">No scheduled experiments</p>}
      {experiments.slice(0, 5).map((e: any, i: number) => (
        <div key={i} className="flex justify-between py-2 border-b border-slate-700 last:border-0 text-sm">
          <span className="text-slate-300">{e.name}</span>
          <span className="text-slate-400">{e.schedule}</span>
        </div>
      ))}
    </div>
  );
}

function ChaosFaultTypesList() {
  const types = ['network_latency', 'process_kill', 'dns_failure', 'disk_fill', 'cpu_stress', 'memory_pressure'];
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-white font-semibold mb-3">Available Fault Types</h3>
      <div className="flex flex-wrap gap-2">
        {types.map((t, i) => <span key={i} className="bg-slate-700 text-slate-300 px-2 py-1 rounded text-xs">{t}</span>)}
      </div>
    </div>
  );
}

function ChaosBlastRadius({ experimentId }: { experimentId: string }) {
  const [radius, setRadius] = useState<any>(null);
  useEffect(() => {
    apiClient.get(`/api/v1/resiliency/chaos/experiments/${experimentId}/blast-radius`).then(d => setRadius(d)).catch(() => {});
  }, [experimentId]);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Blast Radius</h3>
      {!radius && <p className="text-slate-400 text-sm">No data</p>}
      {radius && (
        <div className="grid grid-cols-3 gap-3 text-sm">
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Targets</span><div className="text-white font-bold">{radius.unique_targets}</div></div>
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Radius</span><div className={radius.blast_radius === 'high' ? 'text-red-400' : 'text-yellow-400'}>{radius.blast_radius}</div></div>
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Runs</span><div className="text-white font-bold">{radius.total_runs}</div></div>
        </div>
      )}
    </div>
  );
}

function ChaosMetricCollector({ experimentId }: { experimentId: string }) {
  const [metrics, setMetrics] = useState<any>(null);
  useEffect(() => {
    apiClient.get(`/api/v1/resiliency/chaos/experiments/${experimentId}/metrics`).then(d => setMetrics(d)).catch(() => {});
  }, [experimentId]);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Experiment Metrics</h3>
      {!metrics && <p className="text-slate-400 text-sm">No metrics</p>}
      {metrics && (
        <div className="grid grid-cols-4 gap-2 text-sm">
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Avg Duration</span><div className="text-white">{metrics.avg_duration}s</div></div>
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Pass Rate</span><div className="text-green-400">{metrics.total_runs ? Math.round(metrics.passed / metrics.total_runs * 100) : 0}%</div></div>
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Median RTO</span><div className="text-white">{metrics.median_rto}s</div></div>
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Median RPO</span><div className="text-white">{metrics.median_rpo}s</div></div>
        </div>
      )}
    </div>
  );
}

function ChaosNotificationConfig({ experimentId }: { experimentId: string }) {
  const [configs, setConfigs] = useState<any[]>([]);
  useEffect(() => {
    apiClient.get(`/api/v1/resiliency/chaos/experiments/${experimentId}/notifications`).then(d => setConfigs(d || [])).catch(() => {});
  }, [experimentId]);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Notification Configs</h3>
      {configs.length === 0 && <p className="text-slate-400 text-sm">No notification configs</p>}
      {configs.map((c, i) => (
        <div key={i} className="flex justify-between py-2 border-b border-slate-700 last:border-0 text-sm">
          <span className="text-slate-300">{c.channels?.join(', ')}</span>
          <span className={c.status === 'active' ? 'text-green-400' : 'text-slate-400'}>{c.status}</span>
        </div>
      ))}
    </div>
  );
}

function ChaosFailureTrend() {
  const [trend, setTrend] = useState<any>(null);
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/chaos/failure-trend').then(d => setTrend(d)).catch(() => {});
  }, []);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Failure Rate Trend</h3>
      {!trend && <p className="text-slate-400 text-sm">No data</p>}
      {trend?.trend?.slice(0, 7).map((t: any, i: number) => (
        <div key={i} className="flex justify-between py-1 border-b border-slate-700 last:border-0 text-sm">
          <span className="text-slate-300">{t.date}</span>
          <span className={t.failure_rate > 10 ? 'text-red-400' : 'text-green-400'}>{t.failure_rate}%</span>
        </div>
      ))}
    </div>
  );
}

function ChaosTemplateLibrary() {
  const [templates, setTemplates] = useState<any[]>([]);
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/chaos/templates').then(d => setTemplates(d || [])).catch(() => {});
  }, []);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Template Library</h3>
      {templates.length === 0 && <p className="text-slate-400 text-sm">No templates</p>}
      {templates.map((t, i) => (
        <div key={i} className="flex justify-between py-2 border-b border-slate-700 last:border-0 text-sm">
          <span className="text-slate-300">{t.category}</span>
          <span className="text-slate-400">{t.scenarios?.slice(0, 3).join(', ')}</span>
        </div>
      ))}
    </div>
  );
}

function ChaosBenchmarkPanel() {
  const [benchmark, setBenchmark] = useState<any>(null);
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/chaos/benchmark').then(d => setBenchmark(d)).catch(() => {});
  }, []);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Benchmark</h3>
      {!benchmark && <p className="text-slate-400 text-sm">Loading...</p>}
      {benchmark && (
        <div className="grid grid-cols-3 gap-3 text-sm">
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Avg Recovery</span><div className="text-white">{benchmark.avg_recovery_time}s</div></div>
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Success Rate</span><div className="text-green-400">{benchmark.success_rate}%</div></div>
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Maturity</span><div className="text-white">{benchmark.maturity_level}</div></div>
        </div>
      )}
    </div>
  );
}

function ChaosConfigViewer() {
  const [config, setConfig] = useState<any>(null);
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/chaos/config').then(d => setConfig(d)).catch(() => {});
  }, []);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Chaos Config</h3>
      {!config && <p className="text-slate-400 text-sm">No data</p>}
      {config && (
        <div className="text-sm text-slate-300">
          <p>Kill switch: <span className={config.kill_switch ? 'text-green-400' : 'text-red-400'}>{config.kill_switch ? 'Enabled' : 'Disabled'}</span></p>
          <p>Max blast radius: {config.max_blast_radius}</p>
          <p>Blacklisted: {config.blacklisted_services?.join(', ')}</p>
        </div>
      )}
    </div>
  );
}
