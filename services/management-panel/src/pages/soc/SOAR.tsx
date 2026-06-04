import { useEffect, useState } from 'react';
import { FormattedMessage, useIntl } from 'react-intl';
import { apiClient } from '../../lib/api';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Input } from '../../components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../../components/ui/dialog';
import { Label } from '../../components/ui/label';
import { Select } from '../../components/ui/select';
import { Switch } from '../../components/ui/switch';
import { Pagination } from '../../components/ui/pagination';

interface Playbook { id: string; name: string; description: string; trigger: string; enabled: boolean; total_runs: number; success_rate: number; last_run?: string; }
interface CaseItem { id: string; title: string; description?: string; priority: string; status: string; assignee: string; created_at?: string; }
interface Connector { id: string; name: string; connector_type: string; healthy: boolean; last_heartbeat?: string; }

export const SOARPage = () => {
  const intl = useIntl();
  const [playbooks, setPlaybooks] = useState<Playbook[]>([]);
  const [cases, setCases] = useState<CaseItem[]>([]);
  const [connectors, setConnectors] = useState<Connector[]>([]);
  const [loading, setLoading] = useState(true);
  
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [priorityFilter, setPriorityFilter] = useState<string>('all');
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  
  const [selectedPlaybook, setSelectedPlaybook] = useState<Playbook | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [formData, setFormData] = useState({ name: '', description: '', trigger: 'webhook' });
  
  const [summary, setSummary] = useState<any>({});

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [pb, cs, cn, sm] = await Promise.all([
        apiClient.get('/api/v1/soc/soar/playbooks'),
        apiClient.get('/api/v1/soc/soar/cases'),
        apiClient.get('/api/v1/soc/soar/connectors'),
        apiClient.get('/api/v1/soc/soar/summary'),
      ]);
      setPlaybooks(pb?.data || []);
      setCases(cs?.data || []);
      setConnectors(cn?.data || []);
      setSummary(sm?.data || {});
    } catch { toast.error('Failed to load SOAR data'); }
    finally { setLoading(false); }
  };

  const togglePlaybook = async (id: string, enabled: boolean) => {
    try {
      await apiClient.put(`/api/v1/soc/soar/playbooks/${id}`, { enabled: !enabled });
      toast.success(`Playbook ${enabled ? 'disabled' : 'enabled'}`);
      loadData();
    } catch { toast.error('Failed to toggle playbook'); }
  };

  const executePlaybook = async (id: string) => {
    try {
      await apiClient.post(`/api/v1/soc/soar/playbooks/${id}/execute`);
      toast.success('Playbook execution started');
    } catch { toast.error('Failed to execute playbook'); }
  };

  const createPlaybook = async () => {
    try {
      await apiClient.post('/api/v1/soc/soar/playbooks', formData);
      toast.success('Playbook created');
      setShowCreateModal(false);
      setFormData({ name: '', description: '', trigger: 'webhook' });
      loadData();
    } catch { toast.error('Failed to create playbook'); }
  };

  const deletePlaybook = async () => {
    if (!selectedPlaybook) return;
    try {
      await apiClient.delete(`/api/v1/soc/soar/playbooks/${selectedPlaybook.id}`);
      toast.success('Playbook deleted');
      setShowDeleteConfirm(false);
      setSelectedPlaybook(null);
      loadData();
    } catch { toast.error('Failed to delete playbook'); }
  };

  const filteredPlaybooks = playbooks.filter(pb => {
    if (statusFilter !== 'all') return pb.enabled === (statusFilter === 'enabled');
    if (searchQuery) return pb.name.toLowerCase().includes(searchQuery.toLowerCase());
    return true;
  });

  const filteredCases = cases.filter(c => {
    if (priorityFilter !== 'all') return c.priority === priorityFilter;
    if (searchQuery) return c.title.toLowerCase().includes(searchQuery.toLowerCase());
    return true;
  });

  const paginatedPlaybooks = filteredPlaybooks.slice((page - 1) * pageSize, page * pageSize);
  const paginatedCases = filteredCases.slice((page - 1) * pageSize, page * pageSize);

  const totalRuns = playbooks.reduce((s, p) => s + p.total_runs, 0);
  const avgSuccess = playbooks.length ? playbooks.reduce((s, p) => s + p.success_rate, 0) / playbooks.length * 100 : 0;
  const openCases = cases.filter(c => c.status !== 'closed').length;

  return (
    <div className="space-y-6 p-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">SOAR Platform</h1>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setShowCreateModal(true)}>New Playbook</Button>
          <Button onClick={() => loadData()}>Refresh</Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card><CardHeader><CardTitle>Playbooks</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold">{playbooks.length}</p><p className="text-xs text-muted-foreground">{playbooks.filter(p => p.enabled).length} active</p></CardContent></Card>
        <Card><CardHeader><CardTitle>Open Cases</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold">{openCases}</p><p className="text-xs text-muted-foreground">{cases.length} total</p></CardContent></Card>
        <Card><CardHeader><CardTitle>Connectors</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold">{connectors.filter(c => c.healthy).length}/{connectors.length}</p><p className="text-xs text-muted-foreground">healthy</p></CardContent></Card>
        <Card><CardHeader><CardTitle>Avg Success Rate</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold">{avgSuccess.toFixed(0)}%</p><p className="text-xs text-muted-foreground">{totalRuns} total runs</p></CardContent></Card>
      </div>

      <div className="flex gap-4 items-center">
        <Input placeholder="Search..." value={searchQuery} onChange={e => { setSearchQuery(e.target.value); setPage(1); }} className="max-w-xs" />
        <Select value={statusFilter} onValueChange={v => { setStatusFilter(v); setPage(1); }}>
          <option value="all">All Status</option>
          <option value="enabled">Enabled</option>
          <option value="disabled">Disabled</option>
        </Select>
        <Select value={priorityFilter} onValueChange={v => { setPriorityFilter(v); setPage(1); }}>
          <option value="all">All Priorities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </Select>
      </div>

      <Tabs defaultValue="playbooks">
        <TabsList><TabsTrigger value="playbooks">Playbooks ({filteredPlaybooks.length})</TabsTrigger><TabsTrigger value="cases">Cases ({filteredCases.length})</TabsTrigger><TabsTrigger value="connectors">Connectors ({connectors.length})</TabsTrigger></TabsList>
        
        <TabsContent value="playbooks">
          <Table>
            <TableHeader>
              <TableRow><TableHead>Name</TableHead><TableHead>Description</TableHead><TableHead>Trigger</TableHead><TableHead>Status</TableHead><TableHead>Runs</TableHead><TableHead>Success</TableHead><TableHead>Actions</TableHead></TableRow>
            </TableHeader>
            <TableBody>
              {paginatedPlaybooks.map(pb => (
                <TableRow key={pb.id}>
                  <TableCell className="font-medium">{pb.name}</TableCell>
                  <TableCell className="max-w-xs truncate">{pb.description}</TableCell>
                  <TableCell><Badge variant="outline">{pb.trigger}</Badge></TableCell>
                  <TableCell>
                    <Switch checked={pb.enabled} onCheckedChange={() => togglePlaybook(pb.id, pb.enabled)} />
                  </TableCell>
                  <TableCell>{pb.total_runs}</TableCell>
                  <TableCell>{(pb.success_rate * 100).toFixed(0)}%</TableCell>
                  <TableCell>
                    <div className="flex gap-1">
                      <Button size="sm" variant="outline" onClick={() => executePlaybook(pb.id)}>Run</Button>
                      <Button size="sm" variant="outline" onClick={() => { setSelectedPlaybook(pb); setShowEditModal(true); }}>Edit</Button>
                      <Button size="sm" variant="destructive" onClick={() => { setSelectedPlaybook(pb); setShowDeleteConfirm(true); }}>Delete</Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
              {paginatedPlaybooks.length === 0 && (
                <TableRow><TableCell colSpan={7} className="text-center py-4 text-muted-foreground">No playbooks found</TableCell></TableRow>
              )}
            </TableBody>
          </Table>
          {filteredPlaybooks.length > pageSize && (
            <Pagination page={page} totalPages={Math.ceil(filteredPlaybooks.length / pageSize)} onPageChange={setPage} />
          )}
        </TabsContent>

        <TabsContent value="cases">
          <Table>
            <TableHeader>
              <TableRow><TableHead>Title</TableHead><TableHead>Description</TableHead><TableHead>Priority</TableHead><TableHead>Status</TableHead><TableHead>Assignee</TableHead><TableHead>Created</TableHead></TableRow>
            </TableHeader>
            <TableBody>
              {paginatedCases.map(c => (
                <TableRow key={c.id}>
                  <TableCell className="font-medium">{c.title}</TableCell>
                  <TableCell className="max-w-xs truncate">{c.description || '-'}</TableCell>
                  <TableCell><Badge variant={c.priority === 'critical' ? 'destructive' : c.priority === 'high' ? 'default' : 'secondary'}>{c.priority}</Badge></TableCell>
                  <TableCell>{c.status}</TableCell>
                  <TableCell>{c.assignee || 'Unassigned'}</TableCell>
                  <TableCell>{c.created_at ? new Date(c.created_at).toLocaleDateString() : '-'}</TableCell>
                </TableRow>
              ))}
              {paginatedCases.length === 0 && (
                <TableRow><TableCell colSpan={6} className="text-center py-4 text-muted-foreground">No cases found</TableCell></TableRow>
              )}
            </TableBody>
          </Table>
          {filteredCases.length > pageSize && (
            <Pagination page={page} totalPages={Math.ceil(filteredCases.length / pageSize)} onPageChange={setPage} />
          )}
        </TabsContent>

        <TabsContent value="connectors">
          <Table>
            <TableHeader>
              <TableRow><TableHead>Name</TableHead><TableHead>Type</TableHead><TableHead>Health</TableHead><TableHead>Last Heartbeat</TableHead></TableRow>
            </TableHeader>
            <TableBody>
              {connectors.map(c => (
                <TableRow key={c.id}>
                  <TableCell>{c.name}</TableCell>
                  <TableCell><Badge variant="outline">{c.connector_type}</Badge></TableCell>
                  <TableCell><Badge variant={c.healthy ? 'default' : 'destructive'}>{c.healthy ? 'Healthy' : 'Unhealthy'}</Badge></TableCell>
                  <TableCell>{c.last_heartbeat ? new Date(c.last_heartbeat).toLocaleString() : '-'}</TableCell>
                </TableRow>
              ))}
              {connectors.length === 0 && (
                <TableRow><TableCell colSpan={4} className="text-center py-4 text-muted-foreground">No connectors found</TableCell></TableRow>
              )}
            </TableBody>
          </Table>
        </TabsContent>
      </Tabs>

      <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
        <DialogContent>
          <DialogHeader><DialogTitle>Create Playbook</DialogTitle></DialogHeader>
          <div className="space-y-4">
            <div><Label>Name</Label><Input value={formData.name} onChange={e => setFormData({ ...formData, name: e.target.value })} /></div>
            <div><Label>Description</Label><Input value={formData.description} onChange={e => setFormData({ ...formData, description: e.target.value })} /></div>
            <div><Label>Trigger Type</Label>
              <Select value={formData.trigger} onValueChange={v => setFormData({ ...formData, trigger: v })}>
                <option value="webhook">Webhook</option>
                <option value="scheduled">Scheduled</option>
                <option value="event">Event</option>
                <option value="manual">Manual</option>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateModal(false)}>Cancel</Button>
            <Button onClick={createPlaybook}>Create</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={showDeleteConfirm} onOpenChange={setShowDeleteConfirm}>
        <DialogContent>
          <DialogHeader><DialogTitle>Delete Playbook</DialogTitle></DialogHeader>
          <p>Are you sure you want to delete "{selectedPlaybook?.name}"? This action cannot be undone.</p>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDeleteConfirm(false)}>Cancel</Button>
            <Button variant="destructive" onClick={deletePlaybook}>Delete</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-6">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Total Playbooks</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{summary.total_playbooks || 0}</div><p className="text-xs text-muted-foreground">{summary.active_playbooks || 0} active</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Executions (30d)</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{summary.total_executions || 0}</div><p className="text-xs text-muted-foreground">{summary.success_rate || 0}% success rate</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Open Cases</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-orange-500">{summary.open_cases || 0}</div><p className="text-xs text-muted-foreground">{summary.cases_resolved || 0} resolved</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Auto-Resolution</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-green-500">{summary.auto_resolution_rate || 0}%</div><p className="text-xs text-muted-foreground">cases auto-resolved</p></CardContent></Card>
      </div>

      <Tabs defaultValue="execution_trend" className="mb-6">
        <TabsList><TabsTrigger value="execution_trend">Execution Trend</TabsTrigger><TabsTrigger value="playbook_perf">Playbook Performance</TabsTrigger><TabsTrigger value="connector_health">Connector Health</TabsTrigger></TabsList>
        <TabsContent value="execution_trend">
          <Card><CardHeader><CardTitle>Playbook Execution Trend (Last 30 Days)</CardTitle></CardHeader><CardContent>
            <div className="space-y-2">{summary.execution_trend?.map?.((p: any, i: number) => (<div key={i} className="flex items-center justify-between"><span className="text-sm">{p.date}</span><div className="h-2 bg-blue-500 rounded" style={{ width: `${(p.count / (summary.execution_trend?.[0]?.count || 1)) * 100}%` }} /><span className="text-sm font-mono">{p.count}</span></div>))}</div>
          </CardContent></Card>
        </TabsContent>
        <TabsContent value="playbook_perf">
          <Card><CardHeader><CardTitle>Playbook Performance Metrics</CardTitle></CardHeader><CardContent>
            <Table><TableHeader><TableRow><TableHead>Playbook</TableHead><TableHead>Runs</TableHead><TableHead>Success Rate</TableHead><TableHead>Avg Duration</TableHead></TableRow></TableHeader><TableBody>
              {summary.playbook_metrics?.map?.((p: any, i: number) => (<TableRow key={i}><TableCell className="font-medium">{p.name}</TableCell><TableCell>{p.runs}</TableCell><TableCell><Badge variant={p.success_rate > 90 ? 'default' : 'destructive'}>{p.success_rate}%</Badge></TableCell><TableCell>{p.avg_duration}</TableCell></TableRow>))}
              {(!summary.playbook_metrics || summary.playbook_metrics.length === 0) && <TableRow><TableCell colSpan={4} className="text-center text-muted-foreground">No playbook metrics available</TableCell></TableRow>}
            </TableBody></Table>
          </CardContent></Card>
        </TabsContent>
        <TabsContent value="connector_health">
          <Card><CardHeader><CardTitle>Connector Health Status</CardTitle></CardHeader><CardContent>
            <div className="space-y-2">{summary.connector_health?.map?.((c: any, i: number) => (<div key={i} className="flex items-center justify-between p-2 border rounded"><div><span className="font-medium">{c.name}</span><span className="text-sm text-muted-foreground ml-2">{c.type}</span></div><div className="flex items-center gap-2"><Badge variant={c.healthy ? 'default' : 'destructive'}>{c.healthy ? 'Healthy' : 'Unhealthy'}</Badge><span className="text-xs text-muted-foreground">{c.last_heartbeat || 'N/A'}</span></div></div>))}</div>
          </CardContent></Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};
