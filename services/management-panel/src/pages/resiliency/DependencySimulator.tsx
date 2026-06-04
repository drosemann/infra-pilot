import { useEffect, useState } from 'react';
import { FormattedMessage } from 'react-intl';
import { apiClient } from '../../lib/api';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table';

interface Simulation {
  id: string; name: string; target_service: string;
  failure_type: string; dependency_type: string; status: string;
  created_at: string;
}

export default function DependencySimulator() {
  const [sims, setSims] = useState<Simulation[]>([]);
  const [faultTypes, setFaultTypes] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: '', target: '', failure_type: 'timeout', dep_type: 'api' });

  useEffect(() => { loadSims(); loadFaultTypes(); }, []);

  const loadSims = async () => {
    try { const data = await apiClient.get('/api/v1/resiliency/dependency/simulations'); setSims(data || []); }
    catch { toast.error('Failed to load simulations'); }
    finally { setLoading(false); }
  };

  const loadFaultTypes = async () => {
    try { const data = await apiClient.get('/api/v1/resiliency/dependency/failure-types'); setFaultTypes((data || []).map((f: any) => f.id)); }
    catch { /* ignore */ }
  };

  const createSim = async () => {
    try { await apiClient.post('/api/v1/resiliency/dependency/simulations', { name: form.name, target_service: form.target, failure_type: form.failure_type, dependency_type: form.dep_type }); toast.success('Simulation created'); setShowForm(false); loadSims(); }
    catch { toast.error('Failed to create'); }
  };

  const runSim = async (simId: string) => {
    try { await apiClient.post(`/api/v1/resiliency/dependency/simulations/${simId}/run`); toast.success('Simulation completed'); loadSims(); }
    catch { toast.error('Failed to run'); }
  };

  const deleteSim = async (simId: string) => {
    try { await apiClient.delete(`/api/v1/resiliency/dependency/simulations/${simId}`); toast.success('Simulation deleted'); loadSims(); }
    catch { toast.error('Failed to delete'); }
  };

  const failureTypes = ['timeout', 'error_response', 'slow_response', 'connection_refused', 'dns_failure', 'rate_limit', 'data_corruption', 'circuit_breaker_open'];
  const depTypes = ['database', 'api', 'queue', 'cache', 'storage', 'dns', 'auth_service', 'payment_gateway'];
  const statusColor: Record<string, string> = { created: 'bg-gray-500', running: 'bg-orange-500', completed: 'bg-green-500', failed: 'bg-red-500' };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>;

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold"><FormattedMessage id="depSim.title" defaultMessage="Dependency Failure Simulation" /></h1>
          <p className="text-muted-foreground mt-1">Simulate failure of upstream dependencies to test resilience</p>
        </div>
        <Button onClick={() => setShowForm(!showForm)}>{showForm ? 'Cancel' : 'New Simulation'}</Button>
      </div>

      {showForm && (
        <Card>
          <CardHeader><CardTitle>Create Simulation</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div><label className="block text-sm font-medium mb-1">Name</label><input className="w-full border rounded p-2" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} /></div>
              <div><label className="block text-sm font-medium mb-1">Target Service</label><input className="w-full border rounded p-2" value={form.target} onChange={e => setForm({ ...form, target: e.target.value })} /></div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div><label className="block text-sm font-medium mb-1">Failure Type</label>
                <select className="w-full border rounded p-2" value={form.failure_type} onChange={e => setForm({ ...form, failure_type: e.target.value })}>
                  {failureTypes.map(t => <option key={t} value={t}>{t.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</option>)}
                </select></div>
              <div><label className="block text-sm font-medium mb-1">Dependency Type</label>
                <select className="w-full border rounded p-2" value={form.dep_type} onChange={e => setForm({ ...form, dep_type: e.target.value })}>
                  {depTypes.map(t => <option key={t} value={t}>{t.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</option>)}
                </select></div>
            </div>
            <Button onClick={createSim}>Create</Button>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader><CardTitle>Simulations ({sims.length})</CardTitle></CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow><TableHead>Name</TableHead><TableHead>Target</TableHead><TableHead>Failure</TableHead><TableHead>Dependency</TableHead><TableHead>Status</TableHead><TableHead>Actions</TableHead></TableRow>
            </TableHeader>
            <TableBody>
              {sims.map(s => (
                <TableRow key={s.id}>
                  <TableCell className="font-medium">{s.name}</TableCell>
                  <TableCell>{s.target_service}</TableCell>
                  <TableCell><Badge variant="outline">{s.failure_type}</Badge></TableCell>
                  <TableCell>{s.dependency_type}</TableCell>
                  <TableCell><Badge className={statusColor[s.status]}>{s.status}</Badge></TableCell>
                  <TableCell>
                    <div className="flex gap-1">
                      <Button size="sm" variant="default" onClick={() => runSim(s.id)}>Run</Button>
                      <Button size="sm" variant="destructive" onClick={() => deleteSim(s.id)}>Del</Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
              {sims.length === 0 && <TableRow><TableCell colSpan={6} className="text-center text-muted-foreground">No simulations</TableCell></TableRow>}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}

function DependencySimSummary() {
  const [summary, setSummary] = useState({ total_simulations: 0, total_runs: 0, pass_rate: 0 });
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/dependency-simulator/summary').then(d => setSummary(d || { total_simulations: 0, total_runs: 0, pass_rate: 0 })).catch(() => {});
  }, []);
  return (
    <div className="grid grid-cols-3 gap-3 mb-4">
      <div className="bg-slate-800 rounded-lg p-3 border border-slate-700 text-center">
        <div className="text-2xl font-bold text-white">{summary.total_simulations}</div>
        <div className="text-xs text-slate-400">Simulations</div>
      </div>
      <div className="bg-slate-800 rounded-lg p-3 border border-slate-700 text-center">
        <div className="text-2xl font-bold text-blue-400">{summary.total_runs}</div>
        <div className="text-xs text-slate-400">Total Runs</div>
      </div>
      <div className="bg-slate-800 rounded-lg p-3 border border-slate-700 text-center">
        <div className="text-2xl font-bold text-green-400">{summary.pass_rate}%</div>
        <div className="text-xs text-slate-400">Pass Rate</div>
      </div>
    </div>
  );
}

function DependencySimImpactAnalysis() {
  const [analysis, setAnalysis] = useState<any[]>([]);
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/dependency-simulator/impact').then(d => setAnalysis(d || [])).catch(() => {});
  }, []);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Impact Analysis</h3>
      <table className="w-full text-sm">
        <thead><tr className="text-slate-400 border-b border-slate-700"><th className="text-left py-2">Service</th><th className="text-right py-2">Direct Impact</th><th className="text-right py-2">Transitive</th></tr></thead>
        <tbody>{analysis.slice(0, 5).map((a: any, i: number) => (
          <tr key={i} className="border-b border-slate-700"><td className="py-2 text-white">{a.service_name}</td><td className="py-2 text-right text-white">{a.direct_dependents}</td><td className="py-2 text-right text-slate-400">{a.transitive_dependents}</td></tr>
        ))}</tbody>
      </table>
    </div>
  );
}

function DependencySimFailureTypes() {
function DependencyGraphView() {
  const [graph, setGraph] = useState<any>(null);
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/dependency-simulator/graph').then(d => setGraph(d)).catch(() => {});
  }, []);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Dependency Graph</h3>
      {!graph && <p className="text-slate-400 text-sm">Loading...</p>}
      {graph && (
        <div className="grid grid-cols-3 gap-3 text-sm">
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Nodes</span><div className="text-white font-bold">{graph.total_nodes}</div></div>
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Edges</span><div className="text-white font-bold">{graph.total_edges}</div></div>
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Critical Nodes</span><div className="text-red-400 font-bold">{graph.critical_nodes}</div></div>
        </div>
      )}
    </div>
  );
}

function DependencyRecommendations() {
  const [recs, setRecs] = useState<any[]>([]);
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/dependency-simulator/recommendations').then(d => setRecs(d || [])).catch(() => {});
  }, []);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Recommendations</h3>
      {recs.length === 0 && <p className="text-slate-400 text-sm">No recommendations</p>}
      {recs.map((r, i) => (
        <div key={i} className="flex justify-between py-2 border-b border-slate-700 last:border-0 text-sm">
          <span className="text-slate-300">{r.suggestion}</span>
          <span className="text-slate-400">{r.target_service}</span>
        </div>
      ))}
    </div>
  );
}

function DependencySimConfig() {
  const [config, setConfig] = useState<any>(null);
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/dependency-simulator/config').then(d => setConfig(d)).catch(() => {});
  }, []);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Simulation Config</h3>
      {!config && <p className="text-slate-400 text-sm">No data</p>}
      {config && (
        <div className="text-sm text-slate-300">
          <p>Timeout: {config.timeout}s</p>
          <p>Max depth: {config.max_depth}</p>
          <p>Auto remediate: <span className={config.auto_remediate ? 'text-green-400' : 'text-slate-400'}>{config.auto_remediate ? 'Enabled' : 'Disabled'}</span></p>
        </div>
      )}
    </div>
  );
}

const types = ['network_partition', 'latency_spike', 'timeout', 'circuit_breaker', 'database_failover', 'region_outage'];
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mb-4">
      <h3 className="text-white font-semibold mb-3">Failure Types</h3>
      <div className="flex flex-wrap gap-2">
        {types.map((t, i) => <span key={i} className="bg-slate-700 text-slate-300 px-2 py-1 rounded text-xs">{t}</span>)}
      </div>
    </div>
  );
}

function DependencySimQuickForm({ onSuccess }: { onSuccess: () => void }) {
  const [form, setForm] = useState({ name: '', target_service: '', failure_type: 'network_partition', dependency_type: 'internal' });
  const handleCreate = async () => {
    await apiClient.post('/api/v1/resiliency/dependency-simulator/simulations', form);
    toast.success('Simulation created');
    onSuccess();
  };
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mb-4">
      <h3 className="text-white font-semibold mb-3">Quick Create Simulation</h3>
      <div className="grid grid-cols-2 gap-3">
        <input placeholder="Name" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} className="bg-slate-700 text-white p-2 rounded text-sm" />
        <select value={form.failure_type} onChange={e => setForm({ ...form, failure_type: e.target.value })} className="bg-slate-700 text-white p-2 rounded text-sm">
          {types.map(t => <option key={t} value={t}>{t}</option>)}
        </select>
      </div>
      <button onClick={handleCreate} className="mt-3 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 text-sm">Create</button>
    </div>
  );
}

function DependencyHealthScore() {
  const [health, setHealth] = useState<any>(null);
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/dependency-simulator/health').then(d => setHealth(d)).catch(() => {});
  }, []);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Dependency Health</h3>
      {!health && <p className="text-slate-400 text-sm">Loading...</p>}
      {health && (
        <div className="grid grid-cols-3 gap-3 text-sm">
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Health</span><div className={health.overall_health >= 80 ? 'text-green-400' : 'text-yellow-400'}>{health.overall_health}%</div></div>
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Level</span><div className="text-white font-bold">{health.level}</div></div>
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Simulations</span><div className="text-white font-bold">{health.total_simulations}</div></div>
        </div>
      )}
    </div>
  );
}

function DependencyBlastRadius() {
  const [radius, setRadius] = useState<any>(null);
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/dependency-simulator/blast-radius').then(d => setRadius(d)).catch(() => {});
  }, []);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Blast Radius Analysis</h3>
      {!radius && <p className="text-slate-400 text-sm">No data</p>}
      {radius && (
        <div className="text-sm text-slate-300">
          <p>Root service: {radius.root_service}</p>
          <p>Total affected: {radius.total_affected}</p>
          <p>Criticality: {radius.criticality}</p>
        </div>
      )}
    </div>
  );
}

function DependencyReportExport() {
  const handleExport = async (format: string) => {
    const data = await apiClient.get(`/api/v1/resiliency/dependency-simulator/report?format=${format}`);
    const blob = new Blob([typeof data === 'string' ? data : JSON.stringify(data, null, 2)], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = `dependency-report.${format}`; a.click();
    toast.success(`Report exported as ${format}`);
  };
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Export Report</h3>
      <div className="flex gap-2">
        <button onClick={() => handleExport('json')} className="bg-blue-600 text-white px-3 py-1.5 rounded text-xs">JSON</button>
        <button onClick={() => handleExport('md')} className="bg-blue-600 text-white px-3 py-1.5 rounded text-xs">Markdown</button>
      </div>
    </div>
  );
}

function DependencyVulnerabilityScore() {
  const [vuln, setVuln] = useState<any>(null);
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/dependency-simulator/vulnerability').then(d => setVuln(d)).catch(() => {});
  }, []);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Vulnerability Score</h3>
      {!vuln && <p className="text-slate-400 text-sm">No data</p>}
      {vuln && (
        <div className="grid grid-cols-3 gap-3 text-sm">
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Score</span><div className={vuln.vulnerability_score < 20 ? 'text-green-400' : 'text-red-400'}>{vuln.vulnerability_score}%</div></div>
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Level</span><div className="text-white font-bold">{vuln.level}</div></div>
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Failed</span><div className="text-red-400">{vuln.failed_simulations}</div></div>
        </div>
      )}
    </div>
  );
}

const types = ['network_partition', 'latency_spike', 'timeout', 'circuit_breaker', 'database_failover', 'region_outage'];
