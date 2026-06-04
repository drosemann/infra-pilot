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

interface Decoy { id: string; name: string; decoy_type: string; status: string; network_zone: string; engagement_count: number; ip_address: string; tags?: string[]; }
interface DeceptionEvent { id: string; decoy_id: string; decoy_name: string; event_type: string; severity: string; source_ip: string; timestamp: string; }
interface HoneyToken { id: string; name: string; token_type: string; deployment_location: string; status: string; }

export const DeceptionTechPage = () => {
  const [decoys, setDecoys] = useState<Decoy[]>([]);
  const [events, setEvents] = useState<DeceptionEvent[]>([]);
  const [tokens, setTokens] = useState<HoneyToken[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [summary, setSummary] = useState<any>({});
  const [showDecoyModal, setShowDecoyModal] = useState(false);
  const [showTokenModal, setShowTokenModal] = useState(false);
  const [decoyForm, setDecoyForm] = useState({ name: '', decoy_type: 'honeypot', network_zone: 'dmz', ip_address: '10.0.0.1', services: '', tags: '' });
  const [tokenForm, setTokenForm] = useState({ name: '', token_type: 'credential', deployment_location: 'github', trigger_conditions: '' });

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [d, e, t, sm] = await Promise.all([
        apiClient.get('/api/v1/soc/deception/decoys'),
        apiClient.get('/api/v1/soc/deception/events'),
        apiClient.get('/api/v1/soc/deception/tokens'),
        apiClient.get('/api/v1/soc/deception/summary'),
      ]);
      setDecoys(d?.data || []);
      setEvents(e?.data || []);
      setTokens(t?.data || []);
      setSummary(sm?.data || {});
    } catch { toast.error('Failed to load deception data'); }
    finally { setLoading(false); }
  };

  const deployDecoy = async () => {
    try {
      await apiClient.post('/api/v1/soc/deception/decoys', {
        ...decoyForm,
        services: decoyForm.services.split(',').map(s => s.trim()).filter(Boolean),
        tags: decoyForm.tags.split(',').map(t => t.trim()).filter(Boolean),
      });
      toast.success('Decoy deployed');
      setShowDecoyModal(false);
      setDecoyForm({ name: '', decoy_type: 'honeypot', network_zone: 'dmz', ip_address: '10.0.0.1', services: '', tags: '' });
      loadData();
    } catch { toast.error('Failed to deploy decoy'); }
  };

  const createToken = async () => {
    try {
      await apiClient.post('/api/v1/soc/deception/tokens', tokenForm);
      toast.success('Honey token created');
      setShowTokenModal(false);
      setTokenForm({ name: '', token_type: 'credential', deployment_location: 'github', trigger_conditions: '' });
      loadData();
    } catch { toast.error('Failed to create token'); }
  };

  const filteredDecoys = decoys.filter(d => {
    if (statusFilter !== 'all' && d.status !== statusFilter) return false;
    if (searchQuery && !d.name.toLowerCase().includes(searchQuery.toLowerCase()) && !d.network_zone.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  const paginatedDecoys = filteredDecoys.slice((page - 1) * pageSize, page * pageSize);
  const engagedDecoys = decoys.filter(d => d.status === 'engaged').length;
  const compromisedDecoys = decoys.filter(d => d.status === 'compromised').length;
  const criticalEvents = events.filter(e => e.severity === 'critical').length;

  return (
    <div className="space-y-6 p-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Deception Technology</h1>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setShowDecoyModal(true)}>Deploy Decoy</Button>
          <Button variant="outline" onClick={() => setShowTokenModal(true)}>Create Token</Button>
          <Button onClick={loadData}>Refresh</Button>
        </div>
      </div>
      <div className="grid gap-4 md:grid-cols-4">
        <Card><CardHeader><CardTitle>Decoys</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold">{decoys.length}</p><p className="text-xs text-muted-foreground">{decoys.filter(d => d.status === 'deployed').length} deployed</p></CardContent></Card>
        <Card><CardHeader><CardTitle>Engaged</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold text-orange-500">{engagedDecoys}</p></CardContent></Card>
        <Card><CardHeader><CardTitle>Compromised</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold text-red-500">{compromisedDecoys}</p></CardContent></Card>
        <Card><CardHeader><CardTitle>Tokens / Events</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold">{tokens.length} / {events.length}</p><p className="text-xs text-muted-foreground">{criticalEvents} critical</p></CardContent></Card>
      </div>
      <div className="flex gap-4 items-center">
        <Input placeholder="Search decoys..." value={searchQuery} onChange={e => { setSearchQuery(e.target.value); setPage(1); }} className="max-w-xs" />
        <Select value={statusFilter} onValueChange={v => { setStatusFilter(v); setPage(1); }}>
          <option value="all">All Status</option>
          <option value="deployed">Deployed</option><option value="engaged">Engaged</option>
          <option value="compromised">Compromised</option><option value="inactive">Inactive</option>
        </Select>
      </div>
      <Tabs defaultValue="decoys">
        <TabsList><TabsTrigger value="decoys">Decoys ({filteredDecoys.length})</TabsTrigger><TabsTrigger value="events">Events ({events.length})</TabsTrigger><TabsTrigger value="tokens">Honey Tokens ({tokens.length})</TabsTrigger></TabsList>
        <TabsContent value="decoys">
          <Table>
            <TableHeader><TableRow><TableHead>Name</TableHead><TableHead>Type</TableHead><TableHead>IP</TableHead><TableHead>Zone</TableHead><TableHead>Status</TableHead><TableHead>Engagements</TableHead></TableRow></TableHeader>
            <TableBody>
              {paginatedDecoys.map(d => (
                <TableRow key={d.id}>
                  <TableCell className="font-medium">{d.name}</TableCell>
                  <TableCell><Badge variant="outline">{d.decoy_type}</Badge></TableCell>
                  <TableCell className="font-mono text-xs">{d.ip_address}</TableCell>
                  <TableCell>{d.network_zone}</TableCell>
                  <TableCell><Badge variant={d.status === 'engaged' ? 'destructive' : d.status === 'deployed' ? 'default' : 'secondary'}>{d.status}</Badge></TableCell>
                  <TableCell>{d.engagement_count}</TableCell>
                </TableRow>
              ))}
              {paginatedDecoys.length === 0 && <TableRow><TableCell colSpan={6} className="text-center py-4 text-muted-foreground">No decoys deployed</TableCell></TableRow>}
            </TableBody>
          </Table>
          {filteredDecoys.length > pageSize && (
            <Pagination page={page} totalPages={Math.ceil(filteredDecoys.length / pageSize)} onPageChange={setPage} />
          )}
        </TabsContent>
        <TabsContent value="events">
          <Table>
            <TableHeader><TableRow><TableHead>Time</TableHead><TableHead>Decoy</TableHead><TableHead>Event Type</TableHead><TableHead>Severity</TableHead><TableHead>Source IP</TableHead></TableRow></TableHeader>
            <TableBody>
              {events.map(e => (
                <TableRow key={e.id}>
                  <TableCell className="text-xs">{new Date(e.timestamp).toLocaleString()}</TableCell>
                  <TableCell>{e.decoy_name}</TableCell>
                  <TableCell><Badge variant="outline">{e.event_type}</Badge></TableCell>
                  <TableCell><Badge variant={e.severity === 'critical' ? 'destructive' : e.severity === 'high' ? 'default' : 'secondary'}>{e.severity}</Badge></TableCell>
                  <TableCell className="font-mono text-xs">{e.source_ip}</TableCell>
                </TableRow>
              ))}
              {events.length === 0 && <TableRow><TableCell colSpan={5} className="text-center py-4 text-muted-foreground">No events</TableCell></TableRow>}
            </TableBody>
          </Table>
        </TabsContent>
        <TabsContent value="tokens">
          <Table>
            <TableHeader><TableRow><TableHead>Name</TableHead><TableHead>Type</TableHead><TableHead>Location</TableHead><TableHead>Status</TableHead></TableRow></TableHeader>
            <TableBody>
              {tokens.map(t => (
                <TableRow key={t.id}>
                  <TableCell className="font-medium">{t.name}</TableCell>
                  <TableCell><Badge variant="outline">{t.token_type}</Badge></TableCell>
                  <TableCell className="font-mono text-xs">{t.deployment_location}</TableCell>
                  <TableCell><Badge variant={t.status === 'triggered' ? 'destructive' : 'default'}>{t.status}</Badge></TableCell>
                </TableRow>
              ))}
              {tokens.length === 0 && <TableRow><TableCell colSpan={4} className="text-center py-4 text-muted-foreground">No honey tokens created</TableCell></TableRow>}
            </TableBody>
          </Table>
        </TabsContent>
      </Tabs>

      <Dialog open={showDecoyModal} onOpenChange={setShowDecoyModal}>
        <DialogContent>
          <DialogHeader><DialogTitle>Deploy Decoy</DialogTitle></DialogHeader>
          <div className="space-y-4">
            <div><Label>Name</Label><Input value={decoyForm.name} onChange={e => setDecoyForm({ ...decoyForm, name: e.target.value })} /></div>
            <div><Label>Decoy Type</Label><Select value={decoyForm.decoy_type} onValueChange={v => setDecoyForm({ ...decoyForm, decoy_type: v })}>
              <option value="honeypot">Honeypot</option><option value="honeynet">Honeynet</option><option value="fake_db">Fake Database</option><option value="fake_file">Fake File</option>
            </Select></div>
            <div><Label>Network Zone</Label><Input value={decoyForm.network_zone} onChange={e => setDecoyForm({ ...decoyForm, network_zone: e.target.value })} /></div>
            <div><Label>IP Address</Label><Input value={decoyForm.ip_address} onChange={e => setDecoyForm({ ...decoyForm, ip_address: e.target.value })} /></div>
            <div><Label>Services (comma-separated)</Label><Input value={decoyForm.services} onChange={e => setDecoyForm({ ...decoyForm, services: e.target.value })} placeholder="ssh, http, mysql" /></div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDecoyModal(false)}>Cancel</Button>
            <Button onClick={deployDecoy}>Deploy</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={showTokenModal} onOpenChange={setShowTokenModal}>
        <DialogContent>
          <DialogHeader><DialogTitle>Create Honey Token</DialogTitle></DialogHeader>
          <div className="space-y-4">
            <div><Label>Name</Label><Input value={tokenForm.name} onChange={e => setTokenForm({ ...tokenForm, name: e.target.value })} /></div>
            <div><Label>Token Type</Label><Select value={tokenForm.token_type} onValueChange={v => setTokenForm({ ...tokenForm, token_type: v })}>
              <option value="credential">Credential</option><option value="api_key">API Key</option><option value="database">Database Credential</option><option value="ssh_key">SSH Key</option>
            </Select></div>
            <div><Label>Deployment Location</Label><Input value={tokenForm.deployment_location} onChange={e => setTokenForm({ ...tokenForm, deployment_location: e.target.value })} placeholder="github, confluence, file share" /></div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowTokenModal(false)}>Cancel</Button>
            <Button onClick={createToken}>Create</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-6">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Active Deceptions</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{summary.active_deceptions || 0}</div><p className="text-xs text-muted-foreground">decoys + honey tokens deployed</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Triggered (24h)</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-red-500">{summary.triggered_24h || 0}</div><p className="text-xs text-muted-foreground">interactions detected</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Threat Intel Gathered</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{summary.threat_intel || 0}</div><p className="text-xs text-muted-foreground">IOCs from deception events</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Deception Coverage</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{summary.coverage_percent || 0}%</div><p className="text-xs text-muted-foreground">network zones covered</p></CardContent></Card>
      </div>

      <Tabs defaultValue="trigger_analysis" className="mb-6">
        <TabsList><TabsTrigger value="trigger_analysis">Trigger Analysis</TabsTrigger><TabsTrigger value="attacker_profiles">Attacker Profiles</TabsTrigger><TabsTrigger value="deployment_map">Deployment Map</TabsTrigger></TabsList>
        <TabsContent value="trigger_analysis">
          <Card><CardHeader><CardTitle>Deception Trigger Analysis (Last 30 Days)</CardTitle></CardHeader><CardContent>
            <Table><TableHeader><TableRow><TableHead>Date</TableHead><TableHead>Decoy</TableHead><TableHead>Source IP</TableHead><TableHead>Technique</TableHead><TableHead>Severity</TableHead></TableRow></TableHeader><TableBody>
              {summary.triggers?.map?.((t: any, i: number) => (<TableRow key={i}><TableCell>{t.date}</TableCell><TableCell>{t.decoy_name}</TableCell><TableCell className="font-mono text-xs">{t.source_ip}</TableCell><TableCell>{t.technique}</TableCell><TableCell><Badge variant={t.severity === 'critical' ? 'destructive' : 'default'}>{t.severity}</Badge></TableCell></TableRow>))}
              {(!summary.triggers || summary.triggers.length === 0) && <TableRow><TableCell colSpan={5} className="text-center text-muted-foreground">No trigger data available</TableCell></TableRow>}
            </TableBody></Table>
          </CardContent></Card>
        </TabsContent>
        <TabsContent value="attacker_profiles">
          <Card><CardHeader><CardTitle>Attacker Behavior Profiles</CardTitle></CardHeader><CardContent>
            <div className="space-y-3">{summary.attacker_profiles?.map?.((p: any, i: number) => (<div key={i} className="p-3 border rounded"><div className="font-medium">{p.ip}</div><div className="text-sm text-muted-foreground">Techniques: {p.techniques?.join(', ')}</div><div className="text-sm text-muted-foreground">Targets: {p.targets} | Sessions: {p.sessions}</div></div>))}</div>
          </CardContent></Card>
        </TabsContent>
        <TabsContent value="deployment_map">
          <Card><CardHeader><CardTitle>Deception Deployment Map</CardTitle></CardHeader><CardContent>
            <div className="grid gap-2">{summary.deployment_zones?.map?.((z: any, i: number) => (<div key={i} className="flex items-center justify-between p-2 border rounded"><span className="font-medium">{z.zone}</span><span className="text-sm">{z.decoys} decoys, {z.tokens} tokens</span></div>))}</div>
          </CardContent></Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};
