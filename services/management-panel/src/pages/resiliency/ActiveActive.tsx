import { useEffect, useState } from 'react';
import { FormattedMessage } from 'react-intl';
import { apiClient } from '../../lib/api';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table';

interface Region {
  id: string; name: string; endpoint: string; status: string;
  weight: number; current_load: number; replication_lag_ms: number;
}

export default function ActiveActive() {
  const [regions, setRegions] = useState<Region[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: '', endpoint: '', weight: 100 });

  useEffect(() => { loadRegions(); }, []);

  const loadRegions = async () => {
    try { const data = await apiClient.get('/api/v1/resiliency/active-active/regions'); setRegions(data || []); }
    catch { toast.error('Failed to load regions'); }
    finally { setLoading(false); }
  };

  const registerRegion = async () => {
    try { await apiClient.post('/api/v1/resiliency/active-active/regions', form); toast.success('Region registered'); setShowForm(false); setForm({ name: '', endpoint: '', weight: 100 }); loadRegions(); }
    catch { toast.error('Failed to register region'); }
  };

  const checkHealth = async (regionId: string) => {
    try { const r = await apiClient.post(`/api/v1/resiliency/active-active/regions/${regionId}/health`); toast.success(`${r.healthy ? 'Healthy' : 'Unhealthy'}`); loadRegions(); }
    catch { toast.error('Health check failed'); }
  };

  const updateWeight = async (regionId: string, weight: number) => {
    try { await apiClient.post(`/api/v1/resiliency/active-active/regions/${regionId}/weight`, { weight }); toast.success('Weight updated'); loadRegions(); }
    catch { toast.error('Failed to update weight'); }
  };

  const deleteRegion = async (regionId: string) => {
    try { await apiClient.delete(`/api/v1/resiliency/active-active/regions/${regionId}`); toast.success('Region removed'); loadRegions(); }
    catch { toast.error('Failed to delete'); }
  };

  const statusColor: Record<string, string> = { healthy: 'bg-green-500', degraded: 'bg-yellow-500', unhealthy: 'bg-red-500', offline: 'bg-gray-500' };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>;

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold"><FormattedMessage id="aa.title" defaultMessage="Multi-Region Active-Active" /></h1>
          <p className="text-muted-foreground mt-1">Active-active deployment across regions with global load balancing</p>
        </div>
        <Button onClick={() => setShowForm(!showForm)}>{showForm ? 'Cancel' : 'Add Region'}</Button>
      </div>

      {showForm && (
        <Card>
          <CardHeader><CardTitle>Register Region</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div><label className="block text-sm font-medium mb-1">Region Name</label><input className="w-full border rounded p-2" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} /></div>
            <div><label className="block text-sm font-medium mb-1">Endpoint URL</label><input className="w-full border rounded p-2" value={form.endpoint} onChange={e => setForm({ ...form, endpoint: e.target.value })} /></div>
            <div><label className="block text-sm font-medium mb-1">Traffic Weight</label><input className="w-full border rounded p-2" type="number" min={1} max={100} value={form.weight} onChange={e => setForm({ ...form, weight: +e.target.value })} /></div>
            <Button onClick={registerRegion}>Register</Button>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader><CardTitle>Regions ({regions.length})</CardTitle></CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow><TableHead>Name</TableHead><TableHead>Endpoint</TableHead><TableHead>Status</TableHead><TableHead>Weight</TableHead><TableHead>Load</TableHead><TableHead>Replication Lag</TableHead><TableHead>Actions</TableHead></TableRow>
            </TableHeader>
            <TableBody>
              {regions.map(r => (
                <TableRow key={r.id}>
                  <TableCell className="font-medium">{r.name}</TableCell>
                  <TableCell className="text-sm">{r.endpoint}</TableCell>
                  <TableCell><Badge className={statusColor[r.status]}>{r.status}</Badge></TableCell>
                  <TableCell>
                    <input className="w-16 border rounded p-1 text-sm" type="number" value={r.weight} onChange={e => updateWeight(r.id, +e.target.value)} />
                  </TableCell>
                  <TableCell>{r.current_load}</TableCell>
                  <TableCell>{r.replication_lag_ms}ms</TableCell>
                  <TableCell>
                    <div className="flex gap-1">
                      <Button size="sm" variant="outline" onClick={() => checkHealth(r.id)}>Health</Button>
                      <Button size="sm" variant="destructive" onClick={() => deleteRegion(r.id)}>Remove</Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
              {regions.length === 0 && <TableRow><TableCell colSpan={7} className="text-center text-muted-foreground">No regions configured</TableCell></TableRow>}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}

function AASummaryCard() {
  const [summary, setSummary] = useState({ totalRegions: 0, healthy: 0, rules: 0 });
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/active-active/summary').then(d => setSummary(d || { totalRegions: 0, healthy: 0, rules: 0 })).catch(() => {});
  }, []);
  return (
    <div className="grid grid-cols-3 gap-3 mb-4">
      <div className="bg-slate-800 rounded-lg p-3 border border-slate-700 text-center">
        <div className="text-2xl font-bold text-white">{summary.totalRegions}</div>
        <div className="text-xs text-slate-400">Total Regions</div>
      </div>
      <div className="bg-slate-800 rounded-lg p-3 border border-slate-700 text-center">
        <div className="text-2xl font-bold text-green-400">{summary.healthy}</div>
        <div className="text-xs text-slate-400">Healthy</div>
      </div>
      <div className="bg-slate-800 rounded-lg p-3 border border-slate-700 text-center">
        <div className="text-2xl font-bold text-blue-400">{summary.rules}</div>
        <div className="text-xs text-slate-400">Traffic Rules</div>
      </div>
    </div>
  );
}

function AARoutingRules() {
  const [rules, setRules] = useState<any[]>([]);
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/active-active/rules').then(d => setRules(d || [])).catch(() => {});
  }, []);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Routing Rules</h3>
      {rules.length === 0 && <p className="text-slate-400 text-sm">No rules configured</p>}
      {rules.map((r, i) => (
        <div key={i} className="flex justify-between text-sm py-2 border-b border-slate-700 last:border-0">
          <span className="text-slate-300">{r.source_region} → {r.destination_region}</span>
          <span className="text-slate-400">Weight: {r.weight}</span>
        </div>
      ))}
    </div>
  );
}

function AAFailoverHistory() {
  const [history, setHistory] = useState<any[]>([]);
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/active-active/history').then(d => setHistory(d || [])).catch(() => {});
  }, []);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Failover History</h3>
      {history.length === 0 && <p className="text-slate-400 text-sm">No failover events</p>}
      {history.slice(0, 5).map((h, i) => (
        <div key={i} className="flex justify-between py-2 border-b border-slate-700 last:border-0 text-sm">
          <span className="text-slate-300">{h.from_region} &rarr; {h.to_region}</span>
          <span className="text-slate-400">{h.completed_at}</span>
        </div>
      ))}
    </div>
  );
}

function AARegionForm({ onRefresh }: { onRefresh: () => void }) {
  const [form, setForm] = useState({ name: '', endpoint: '', weight: 100 });
  const handleAdd = async () => {
    await apiClient.post('/api/v1/resiliency/active-active/regions', form);
    toast.success('Region added');
    setForm({ name: '', endpoint: '', weight: 100 });
    onRefresh();
  };
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mb-4">
      <h3 className="text-white font-semibold mb-3">Quick Add Region</h3>
      <div className="grid grid-cols-3 gap-3">
        <input placeholder="Name" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} className="bg-slate-700 text-white p-2 rounded text-sm" />
        <input placeholder="Endpoint" value={form.endpoint} onChange={e => setForm({ ...form, endpoint: e.target.value })} className="bg-slate-700 text-white p-2 rounded text-sm" />
        <input type="number" placeholder="Weight" value={form.weight} onChange={e => setForm({ ...form, weight: +e.target.value })} className="bg-slate-700 text-white p-2 rounded text-sm" />
      </div>
      <button onClick={handleAdd} className="mt-3 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 text-sm">Add Region</button>
    </div>
  );
}

function AAReplicationStatus() {
  const [status, setStatus] = useState<any>(null);
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/active-active/replication').then(d => setStatus(d)).catch(() => {});
  }, []);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Replication Status</h3>
      {!status && <p className="text-slate-400 text-sm">Loading...</p>}
      {status && (
        <div className="grid grid-cols-3 gap-3 text-sm">
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Avg Lag</span><div className="text-white font-bold">{status.average_lag_ms}ms</div></div>
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Max Lag</span><div className={status.max_lag_ms < 100 ? 'text-green-400' : 'text-red-400'}>{status.max_lag_ms}ms</div></div>
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Healthy</span><div className="text-green-400 font-bold">{status.healthy_replicas}/{status.total_regions}</div></div>
        </div>
      )}
    </div>
  );
}

function AACapacityAnalysis() {
  const [capacity, setCapacity] = useState<any>(null);
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/active-active/capacity').then(d => setCapacity(d)).catch(() => {});
  }, []);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Capacity Analysis</h3>
      {!capacity && <p className="text-slate-400 text-sm">No data</p>}
      {capacity && (
        <div className="text-sm">
          <p className="text-slate-300">Utilization: {capacity.utilization}%</p>
          <p className="text-slate-300">Overloaded: {capacity.overloaded_count} regions ({capacity.overloaded_regions?.join(', ')})</p>
          <p className="text-slate-300">Underutilized: {capacity.underutilized_count} regions ({capacity.underutilized_regions?.join(', ')})</p>
        </div>
      )}
    </div>
  );
}

function AAFailoverStrategy() {
  const [strategy, setStrategy] = useState<any>(null);
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/active-active/failover-strategy').then(d => setStrategy(d)).catch(() => {});
  }, []);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Failover Strategy</h3>
      {!strategy && <p className="text-slate-400 text-sm">No data</p>}
      {strategy && (
        <div className="text-sm">
          <p className="text-slate-300">Strategy: <span className="text-white font-bold">{strategy.strategy}</span></p>
          <p className="text-slate-300">Healthy regions: {strategy.healthy_regions}</p>
          <p className="text-slate-300">Recommendation: {strategy.recommendation}</p>
        </div>
      )}
    </div>
  );
}

function AADataLossRisk() {
  const [risk, setRisk] = useState<any>(null);
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/active-active/data-loss-risk').then(d => setRisk(d)).catch(() => {});
  }, []);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Data Loss Risk</h3>
      {!risk && <p className="text-slate-400 text-sm">Loading...</p>}
      {risk && (
        <div className="grid grid-cols-3 gap-3 text-sm">
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Risk</span><div className={risk.risk_level === 'low' ? 'text-green-400' : 'text-red-400'}>{risk.risk_level}</div></div>
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Sync Regions</span><div className="text-white">{risk.sync_regions}</div></div>
            <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Async Avg Lag</span><div className="text-white">{risk.avg_async_lag_ms}ms</div></div>
        </div>
      )}
    </div>
  );
}

function AATrafficRouting() {
  const [routes, setRoutes] = useState<any>(null);
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/active-active/traffic-routing').then(d => setRoutes(d)).catch(() => {});
  }, []);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Traffic Routing</h3>
      {!routes && <p className="text-slate-400 text-sm">Loading...</p>}
      {routes && (
        <div className="grid grid-cols-3 gap-3 text-sm">
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Strategy</span><div className="text-white font-bold">{routes.strategy}</div></div>
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Sticky Sessions</span><div className={routes.sticky_sessions ? 'text-green-400' : 'text-slate-400'}>{routes.sticky_sessions ? 'Enabled' : 'Disabled'}</div></div>
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">DNS TTL</span><div className="text-white">{routes.dns_ttl}s</div></div>
        </div>
      )}
    </div>
  );
}

function AAFailoverConfig() {
  const [config, setConfig] = useState<any>(null);
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/active-active/failover-config').then(d => setConfig(d)).catch(() => {});
  }, []);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Failover Config</h3>
      {!config && <p className="text-slate-400 text-sm">No data</p>}
      {config && (
        <div className="text-sm text-slate-300">
          <p>Auto: <span className={config.auto_failover ? 'text-green-400' : 'text-slate-400'}>{config.auto_failover ? 'Enabled' : 'Disabled'}</span></p>
          <p>Threshold: {config.failure_threshold}</p>
          <p>Warm standby: {config.warm_standby_regions}</p>
        </div>
      )}
    </div>
  );
}

function AALatencyMap() {
  const [latency, setLatency] = useState<any>(null);
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/active-active/latency-map').then(d => setLatency(d)).catch(() => {});
  }, []);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Latency Map</h3>
      {!latency && <p className="text-slate-400 text-sm">No data</p>}
      {latency?.pairs?.slice(0, 6).map((p: any, i: number) => (
        <div key={i} className="flex justify-between py-1 border-b border-slate-700 last:border-0 text-sm">
          <span className="text-slate-300">{p.from} → {p.to}</span>
          <span className={p.latency_ms > 100 ? 'text-red-400' : 'text-green-400'}>{p.latency_ms}ms</span>
        </div>
      ))}
    </div>
  );
}
