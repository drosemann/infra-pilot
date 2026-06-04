import { useEffect, useState } from 'react';
import { apiClient } from '../../lib/api';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../../components/ui/dialog';
import { Select } from '../../components/ui/select';
import { Pagination } from '../../components/ui/pagination';

interface NetworkFlow { id: string; src_ip: string; dst_ip: string; protocol: string; bytes_sent: number; threat_score: number; malicious: boolean; timestamp: string; dns_query?: string; }
interface NDRAlert { id: string; title: string; severity: string; category: string; source_ip: string; destination_ip: string; detected_at: string; acknowledged: boolean; }
interface DetectionRule { id: string; name: string; description: string; severity: string; category: string; enabled: boolean; hits: number; }

export const NDRPage = () => {
  const [flows, setFlows] = useState<NetworkFlow[]>([]);
  const [alerts, setAlerts] = useState<NDRAlert[]>([]);
  const [rules, setRules] = useState<DetectionRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [severityFilter, setSeverityFilter] = useState('all');
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [summary, setSummary] = useState<any>({});
  const [showRuleModal, setShowRuleModal] = useState(false);
  const [ruleForm, setRuleForm] = useState({ name: '', description: '', signature: '', severity: 'medium', protocol: 'any', category: 'anomaly' });

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [f, a, r, sm] = await Promise.all([
        apiClient.get('/api/v1/soc/ndr/flows?malicious_only=true'),
        apiClient.get('/api/v1/soc/ndr/alerts'),
        apiClient.get('/api/v1/soc/ndr/rules'),
        apiClient.get('/api/v1/soc/ndr/summary'),
      ]);
      setFlows(f?.data || []);
      setAlerts(a?.data || []);
      setRules(r?.data || []);
      setSummary(sm?.data || {});
    } catch { toast.error('Failed to load NDR data'); }
    finally { setLoading(false); }
  };

  const acknowledgeAlert = async (id: string) => {
    try {
      await apiClient.post(`/api/v1/soc/ndr/alerts/${id}/acknowledge`);
      toast.success('Alert acknowledged');
      loadData();
    } catch { toast.error('Failed to acknowledge alert'); }
  };

  const toggleRule = async (id: string) => {
    try {
      await apiClient.put(`/api/v1/soc/ndr/rules/${id}/toggle`);
      toast.success('Rule toggled');
      loadData();
    } catch { toast.error('Failed to toggle rule'); }
  };

  const createRule = async () => {
    try {
      await apiClient.post('/api/v1/soc/ndr/rules', ruleForm);
      toast.success('Rule created');
      setShowRuleModal(false);
      setRuleForm({ name: '', description: '', signature: '', severity: 'medium', protocol: 'any', category: 'anomaly' });
      loadData();
    } catch { toast.error('Failed to create rule'); }
  };

  const filteredAlerts = alerts.filter(a => {
    if (severityFilter !== 'all' && a.severity !== severityFilter) return false;
    if (searchQuery && !a.title.toLowerCase().includes(searchQuery.toLowerCase()) && !a.source_ip.includes(searchQuery)) return false;
    return true;
  });

  const paginatedAlerts = filteredAlerts.slice((page - 1) * pageSize, page * pageSize);
  const unacknowledgedAlerts = alerts.filter(a => !a.acknowledged).length;
  const enabledRules = rules.filter(r => r.enabled).length;
  const maliciousFlows = flows.length;
  const totalFlows = summary.total_flows || 0;

  return (
    <div className="space-y-6 p-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Network Detection & Response</h1>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setShowRuleModal(true)}>Add Rule</Button>
          <Button onClick={loadData}>Refresh</Button>
        </div>
      </div>
      <div className="grid gap-4 md:grid-cols-4">
        <Card><CardHeader><CardTitle>Flows</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold">{totalFlows.toLocaleString()}</p><p className="text-xs text-muted-foreground">{maliciousFlows} malicious</p></CardContent></Card>
        <Card><CardHeader><CardTitle>Malicious %</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold text-red-500">{totalFlows > 0 ? ((maliciousFlows / totalFlows) * 100).toFixed(1) : 0}%</p></CardContent></Card>
        <Card><CardHeader><CardTitle>Alerts</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold">{alerts.length}</p><p className="text-xs text-muted-foreground">{unacknowledgedAlerts} unacknowledged</p></CardContent></Card>
        <Card><CardHeader><CardTitle>Rules Active</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold">{enabledRules}/{rules.length}</p></CardContent></Card>
      </div>
      <div className="flex gap-4 items-center">
        <Input placeholder="Search alerts..." value={searchQuery} onChange={e => { setSearchQuery(e.target.value); setPage(1); }} className="max-w-xs" />
        <Select value={severityFilter} onValueChange={v => { setSeverityFilter(v); setPage(1); }}>
          <option value="all">All Severities</option>
          <option value="critical">Critical</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option>
        </Select>
      </div>
      <Tabs defaultValue="alerts">
        <TabsList><TabsTrigger value="alerts">Alerts ({filteredAlerts.length})</TabsTrigger><TabsTrigger value="flows">Malicious Flows ({flows.length})</TabsTrigger><TabsTrigger value="rules">Rules ({rules.length})</TabsTrigger></TabsList>
        <TabsContent value="alerts">
          <Table>
            <TableHeader><TableRow><TableHead>Title</TableHead><TableHead>Severity</TableHead><TableHead>Category</TableHead><TableHead>Source</TableHead><TableHead>Destination</TableHead><TableHead>Time</TableHead><TableHead>Status</TableHead><TableHead>Actions</TableHead></TableRow></TableHeader>
            <TableBody>
              {paginatedAlerts.map(a => (
                <TableRow key={a.id}>
                  <TableCell className="max-w-xs truncate">{a.title}</TableCell>
                  <TableCell><Badge variant={a.severity === 'critical' ? 'destructive' : a.severity === 'high' ? 'default' : 'secondary'}>{a.severity}</Badge></TableCell>
                  <TableCell><Badge variant="outline">{a.category}</Badge></TableCell>
                  <TableCell className="font-mono text-xs">{a.source_ip}</TableCell>
                  <TableCell className="font-mono text-xs">{a.destination_ip}</TableCell>
                  <TableCell className="text-xs">{new Date(a.detected_at).toLocaleString()}</TableCell>
                  <TableCell>{a.acknowledged ? <Badge variant="default">Acked</Badge> : <Badge variant="secondary">New</Badge>}</TableCell>
                  <TableCell>{!a.acknowledged && <Button size="sm" onClick={() => acknowledgeAlert(a.id)}>Ack</Button>}</TableCell>
                </TableRow>
              ))}
              {paginatedAlerts.length === 0 && <TableRow><TableCell colSpan={8} className="text-center py-4 text-muted-foreground">No alerts</TableCell></TableRow>}
            </TableBody>
          </Table>
          {filteredAlerts.length > pageSize && (
            <Pagination page={page} totalPages={Math.ceil(filteredAlerts.length / pageSize)} onPageChange={setPage} />
          )}
        </TabsContent>
        <TabsContent value="flows">
          <Table>
            <TableHeader><TableRow><TableHead>Source</TableHead><TableHead>Destination</TableHead><TableHead>Protocol</TableHead><TableHead>Bytes</TableHead><TableHead>DNS Query</TableHead><TableHead>Threat Score</TableHead></TableRow></TableHeader>
            <TableBody>
              {flows.map(f => (
                <TableRow key={f.id}>
                  <TableCell className="font-mono text-xs">{f.src_ip}</TableCell>
                  <TableCell className="font-mono text-xs">{f.dst_ip}</TableCell>
                  <TableCell><Badge variant="outline">{f.protocol}</Badge></TableCell>
                  <TableCell>{(f.bytes_sent / 1024).toFixed(0)} KB</TableCell>
                  <TableCell className="text-xs max-w-xs truncate">{f.dns_query || '-'}</TableCell>
                  <TableCell><Badge variant={f.threat_score > 0.7 ? 'destructive' : 'default'}>{(f.threat_score * 100).toFixed(0)}%</Badge></TableCell>
                </TableRow>
              ))}
              {flows.length === 0 && <TableRow><TableCell colSpan={6} className="text-center py-4 text-muted-foreground">No malicious flows</TableCell></TableRow>}
            </TableBody>
          </Table>
        </TabsContent>
        <TabsContent value="rules">
          <Table>
            <TableHeader><TableRow><TableHead>Name</TableHead><TableHead>Severity</TableHead><TableHead>Category</TableHead><TableHead>Hits</TableHead><TableHead>Enabled</TableHead><TableHead>Action</TableHead></TableRow></TableHeader>
            <TableBody>
              {rules.map(r => (
                <TableRow key={r.id}>
                  <TableCell className="font-medium">{r.name}</TableCell>
                  <TableCell><Badge variant={r.severity === 'critical' ? 'destructive' : r.severity === 'high' ? 'default' : 'secondary'}>{r.severity}</Badge></TableCell>
                  <TableCell><Badge variant="outline">{r.category}</Badge></TableCell>
                  <TableCell>{r.hits}</TableCell>
                  <TableCell><Badge variant={r.enabled ? 'default' : 'secondary'}>{r.enabled ? 'Active' : 'Disabled'}</Badge></TableCell>
                  <TableCell><Button size="sm" variant="outline" onClick={() => toggleRule(r.id)}>{r.enabled ? 'Disable' : 'Enable'}</Button></TableCell>
                </TableRow>
              ))}
              {rules.length === 0 && <TableRow><TableCell colSpan={6} className="text-center py-4 text-muted-foreground">No rules configured</TableCell></TableRow>}
            </TableBody>
          </Table>
        </TabsContent>
      </Tabs>

      <Dialog open={showRuleModal} onOpenChange={setShowRuleModal}>
        <DialogContent>
          <DialogHeader><DialogTitle>Add Detection Rule</DialogTitle></DialogHeader>
          <div className="space-y-4">
            <div><Label>Name</Label><Input value={ruleForm.name} onChange={e => setRuleForm({ ...ruleForm, name: e.target.value })} /></div>
            <div><Label>Description</Label><Input value={ruleForm.description} onChange={e => setRuleForm({ ...ruleForm, description: e.target.value })} /></div>
            <div><Label>Signature (e.g. bytes_sent > 10000000)</Label><Input value={ruleForm.signature} onChange={e => setRuleForm({ ...ruleForm, signature: e.target.value })} /></div>
            <div><Label>Severity</Label><Select value={ruleForm.severity} onValueChange={v => setRuleForm({ ...ruleForm, severity: v })}>
              <option value="critical">Critical</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option>
            </Select></div>
            <div><Label>Protocol</Label><Select value={ruleForm.protocol} onValueChange={v => setRuleForm({ ...ruleForm, protocol: v })}>
              <option value="any">Any</option><option value="TCP">TCP</option><option value="UDP">UDP</option><option value="DNS">DNS</option><option value="HTTP">HTTP</option>
            </Select></div>
            <div><Label>Category</Label><Input value={ruleForm.category} onChange={e => setRuleForm({ ...ruleForm, category: e.target.value })} /></div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowRuleModal(false)}>Cancel</Button>
            <Button onClick={createRule}>Create Rule</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-6">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Total Traffic Analyzed</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{summary.total_traffic || '0 B'}</div><p className="text-xs text-muted-foreground">{summary.traffic_period || 'in last 24h'}</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Threats Detected</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-red-500">{summary.threats_detected || 0}</div><p className="text-xs text-muted-foreground">{summary.blocked || 0} blocked automatically</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Network Flows</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{summary.flows || 0}</div><p className="text-xs text-muted-foreground">{summary.flows_per_sec || 0} flows/sec avg</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Detection Engines</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{summary.active_engines || 0}</div><p className="text-xs text-muted-foreground">{summary.total_engines || 0} total engines deployed</p></CardContent></Card>
      </div>

      <Tabs defaultValue="threat_trend" className="mb-6">
        <TabsList><TabsTrigger value="threat_trend">Threat Trend</TabsTrigger><TabsTrigger value="top_threats">Top Threats</TabsTrigger><TabsTrigger value="protocol_dist">Protocol Distribution</TabsTrigger></TabsList>
        <TabsContent value="threat_trend">
          <Card><CardHeader><CardTitle>Threat Detection Trend (Last 30 Days)</CardTitle></CardHeader><CardContent>
            <div className="space-y-2">{summary.threat_trend?.map?.((p: any, i: number) => (<div key={i} className="flex items-center justify-between"><span className="text-sm">{p.date}</span><div className="h-2 bg-red-500 rounded" style={{ width: `${(p.count / (summary.threat_trend?.[0]?.count || 1)) * 100}%` }} /><span className="text-sm font-mono">{p.count}</span></div>))}</div>
          </CardContent></Card>
        </TabsContent>
        <TabsContent value="top_threats">
          <Card><CardHeader><CardTitle>Top Threat Categories</CardTitle></CardHeader><CardContent>
            <Table><TableHeader><TableRow><TableHead>Category</TableHead><TableHead>Count</TableHead><TableHead>Percent</TableHead></TableRow></TableHeader><TableBody>
              {summary.top_threats?.map?.((t: any, i: number) => (<TableRow key={i}><TableCell>{t.category}</TableCell><TableCell>{t.count}</TableCell><TableCell>{t.percent}%</TableCell></TableRow>))}
              {(!summary.top_threats || summary.top_threats.length === 0) && <TableRow><TableCell colSpan={3} className="text-center text-muted-foreground">No threat data available</TableCell></TableRow>}
            </TableBody></Table>
          </CardContent></Card>
        </TabsContent>
        <TabsContent value="protocol_dist">
          <Card><CardHeader><CardTitle>Network Protocol Distribution</CardTitle></CardHeader><CardContent>
            <div className="grid gap-2">{summary.protocols?.map?.((p: any, i: number) => (<div key={i} className="flex items-center justify-between p-2 border rounded"><span className="font-medium">{p.protocol}</span><span className="text-sm">{p.percent}% ({p.bytes})</span></div>))}</div>
          </CardContent></Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};
