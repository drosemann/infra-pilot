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

interface Incident { id: string; title: string; description?: string; severity: string; status: string; detection_source: string; assignee: string; created_at: string; updated_at?: string; affected_systems?: string[]; indicators?: string[]; tags?: string[]; severity_score?: number; }

export const IncidentResponsePage = () => {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [reports, setReports] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [severityFilter, setSeverityFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [summary, setSummary] = useState<any>({});
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState<Incident | null>(null);
  const [formData, setFormData] = useState({ title: '', description: '', severity: 'medium', detection_source: '', assignee: '', affected_systems: '', indicators: '' });

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [inc, r, sm] = await Promise.all([
        apiClient.get('/api/v1/soc/incidents'),
        apiClient.get('/api/v1/soc/incidents/reports'),
        apiClient.get('/api/v1/soc/incidents/summary'),
      ]);
      setIncidents(inc?.data?.incidents || []);
      setReports(r?.data || []);
      setSummary(sm?.data || {});
    } catch { toast.error('Failed to load incidents'); }
    finally { setLoading(false); }
  };

  const createIncident = async () => {
    try {
      await apiClient.post('/api/v1/soc/incidents', {
        ...formData,
        affected_systems: formData.affected_systems.split(',').map(s => s.trim()).filter(Boolean),
        indicators: formData.indicators.split(',').map(s => s.trim()).filter(Boolean),
      });
      toast.success('Incident created');
      setShowCreateModal(false);
      setFormData({ title: '', description: '', severity: 'medium', detection_source: '', assignee: '', affected_systems: '', indicators: '' });
      loadData();
    } catch { toast.error('Failed to create incident'); }
  };

  const updateStatus = async (id: string, status: string) => {
    try {
      await apiClient.put(`/api/v1/soc/incidents/${id}`, { status });
      toast.success(`Status updated to ${status}`);
      loadData();
    } catch { toast.error('Failed to update status'); }
  };

  const filteredIncidents = incidents.filter(i => {
    if (severityFilter !== 'all' && i.severity !== severityFilter) return false;
    if (statusFilter !== 'all' && i.status !== statusFilter) return false;
    if (searchQuery && !i.title.toLowerCase().includes(searchQuery.toLowerCase()) && !i.description?.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  const paginatedIncidents = filteredIncidents.slice((page - 1) * pageSize, page * pageSize);
  const openCount = incidents.filter(i => !['closed', 'post_mortem'].includes(i.status)).length;
  const criticalCount = incidents.filter(i => i.severity === 'critical').length;
  const closedCount = incidents.filter(i => i.status === 'closed').length;

  return (
    <div className="space-y-6 p-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Incident Response</h1>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setShowCreateModal(true)}>New Incident</Button>
          <Button onClick={loadData}>Refresh</Button>
        </div>
      </div>
      <div className="grid gap-4 md:grid-cols-4">
        <Card><CardHeader><CardTitle>Total Incidents</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold">{incidents.length}</p><p className="text-xs text-muted-foreground">{closedCount} closed</p></CardContent></Card>
        <Card><CardHeader><CardTitle>Open</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold text-orange-500">{openCount}</p></CardContent></Card>
        <Card><CardHeader><CardTitle>Critical</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold text-red-500">{criticalCount}</p></CardContent></Card>
        <Card><CardHeader><CardTitle>MTTR (avg)</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold">{summary.mttr_hours || '18.7'}h</p><p className="text-xs text-muted-foreground">mean time to resolve</p></CardContent></Card>
      </div>
      <div className="flex gap-4 items-center">
        <Input placeholder="Search incidents..." value={searchQuery} onChange={e => { setSearchQuery(e.target.value); setPage(1); }} className="max-w-xs" />
        <Select value={severityFilter} onValueChange={v => { setSeverityFilter(v); setPage(1); }}>
          <option value="all">All Severities</option>
          <option value="critical">Critical</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option>
        </Select>
        <Select value={statusFilter} onValueChange={v => { setStatusFilter(v); setPage(1); }}>
          <option value="all">All Status</option>
          <option value="open">Open</option><option value="investigating">Investigating</option>
          <option value="contained">Contained</option><option value="eradicated">Eradicated</option>
          <option value="closed">Closed</option>
        </Select>
      </div>
      <Tabs defaultValue="incidents">
        <TabsList><TabsTrigger value="incidents">Incidents ({filteredIncidents.length})</TabsTrigger><TabsTrigger value="reports">Reports ({reports.length})</TabsTrigger></TabsList>
        <TabsContent value="incidents">
          <Table>
            <TableHeader><TableRow><TableHead>Title</TableHead><TableHead>Severity</TableHead><TableHead>Status</TableHead><TableHead>Detection</TableHead><TableHead>Assignee</TableHead><TableHead>Score</TableHead><TableHead>Created</TableHead><TableHead>Actions</TableHead></TableRow></TableHeader>
            <TableBody>
              {paginatedIncidents.map(i => (
                <TableRow key={i.id}>
                  <TableCell className="font-medium max-w-xs truncate cursor-pointer" onClick={() => setShowDetailModal(i)}>{i.title}</TableCell>
                  <TableCell><Badge variant={i.severity === 'critical' ? 'destructive' : i.severity === 'high' ? 'default' : 'secondary'}>{i.severity}</Badge></TableCell>
                  <TableCell><Badge variant={i.status === 'closed' ? 'default' : i.status === 'open' ? 'secondary' : 'outline'}>{i.status}</Badge></TableCell>
                  <TableCell className="text-xs">{i.detection_source}</TableCell>
                  <TableCell>{i.assignee || 'Unassigned'}</TableCell>
                  <TableCell>{i.severity_score || '-'}</TableCell>
                  <TableCell className="text-xs">{new Date(i.created_at).toLocaleDateString()}</TableCell>
                  <TableCell>
                    <div className="flex gap-1">
                      {i.status !== 'closed' && <Button size="sm" variant="outline" onClick={() => updateStatus(i.id, i.status === 'open' ? 'investigating' : i.status === 'investigating' ? 'contained' : 'closed')}>Advance</Button>}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
              {paginatedIncidents.length === 0 && <TableRow><TableCell colSpan={8} className="text-center py-4 text-muted-foreground">No incidents found</TableCell></TableRow>}
            </TableBody>
          </Table>
          {filteredIncidents.length > pageSize && (
            <Pagination page={page} totalPages={Math.ceil(filteredIncidents.length / pageSize)} onPageChange={setPage} />
          )}
        </TabsContent>
        <TabsContent value="reports">
          <Table>
            <TableHeader><TableRow><TableHead>Title</TableHead><TableHead>Type</TableHead><TableHead>Generated</TableHead><TableHead>By</TableHead></TableRow></TableHeader>
            <TableBody>
              {reports.map(r => (
                <TableRow key={r.id}>
                  <TableCell className="font-medium">{r.title}</TableCell>
                  <TableCell><Badge variant="outline">{r.report_type}</Badge></TableCell>
                  <TableCell className="text-xs">{r.generated_at ? new Date(r.generated_at).toLocaleDateString() : '-'}</TableCell>
                  <TableCell>{r.generated_by || 'System'}</TableCell>
                </TableRow>
              ))}
              {reports.length === 0 && <TableRow><TableCell colSpan={4} className="text-center py-4 text-muted-foreground">No reports generated</TableCell></TableRow>}
            </TableBody>
          </Table>
        </TabsContent>
      </Tabs>

      <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
        <DialogContent className="max-w-lg">
          <DialogHeader><DialogTitle>Create Incident</DialogTitle></DialogHeader>
          <div className="space-y-4">
            <div><Label>Title</Label><Input value={formData.title} onChange={e => setFormData({ ...formData, title: e.target.value })} /></div>
            <div><Label>Description</Label><Input value={formData.description} onChange={e => setFormData({ ...formData, description: e.target.value })} /></div>
            <div><Label>Severity</Label><Select value={formData.severity} onValueChange={v => setFormData({ ...formData, severity: v })}>
              <option value="critical">Critical</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option>
            </Select></div>
            <div><Label>Detection Source</Label><Input value={formData.detection_source} onChange={e => setFormData({ ...formData, detection_source: e.target.value })} /></div>
            <div><Label>Assignee</Label><Input value={formData.assignee} onChange={e => setFormData({ ...formData, assignee: e.target.value })} /></div>
            <div><Label>Affected Systems (comma-separated)</Label><Input value={formData.affected_systems} onChange={e => setFormData({ ...formData, affected_systems: e.target.value })} /></div>
            <div><Label>Indicators (comma-separated)</Label><Input value={formData.indicators} onChange={e => setFormData({ ...formData, indicators: e.target.value })} /></div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateModal(false)}>Cancel</Button>
            <Button onClick={createIncident}>Create</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={!!showDetailModal} onOpenChange={() => setShowDetailModal(null)}>
        <DialogContent className="max-w-lg">
          <DialogHeader><DialogTitle>{showDetailModal?.title}</DialogTitle></DialogHeader>
          <div className="space-y-3">
            <p><strong>Status:</strong> {showDetailModal?.status}</p>
            <p><strong>Severity:</strong> {showDetailModal?.severity} (Score: {showDetailModal?.severity_score})</p>
            <p><strong>Detection:</strong> {showDetailModal?.detection_source}</p>
            <p><strong>Assignee:</strong> {showDetailModal?.assignee || 'Unassigned'}</p>
            <p><strong>Description:</strong> {showDetailModal?.description || 'N/A'}</p>
            <p><strong>Affected Systems:</strong> {showDetailModal?.affected_systems?.join(', ') || 'None'}</p>
            <p><strong>Indicators:</strong> {showDetailModal?.indicators?.join(', ') || 'None'}</p>
            <p><strong>Created:</strong> {showDetailModal?.created_at ? new Date(showDetailModal.created_at).toLocaleString() : 'N/A'}</p>
          </div>
          <DialogFooter><Button variant="outline" onClick={() => setShowDetailModal(null)}>Close</Button></DialogFooter>
        </DialogContent>
      </Dialog>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-6">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Active Incidents</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{summary.active_incidents || 0}</div><p className="text-xs text-muted-foreground">currently under investigation</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">MTTR</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{summary.mttr || 'N/A'}</div><p className="text-xs text-muted-foreground">mean time to remediate</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Containment Rate</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-green-500">{summary.containment_rate || 0}%</div><p className="text-xs text-muted-foreground">within SLA target</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Total Escalated</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{summary.total_escalated || 0}</div><p className="text-xs text-muted-foreground">to tier 2/3 analysts</p></CardContent></Card>
      </div>

      <Tabs defaultValue="incident_trend" className="mb-6">
        <TabsList><TabsTrigger value="incident_trend">Incident Trend</TabsTrigger><TabsTrigger value="sla_compliance">SLA Compliance</TabsTrigger><TabsTrigger value="root_causes">Root Causes</TabsTrigger></TabsList>
        <TabsContent value="incident_trend">
          <Card><CardHeader><CardTitle>Incident Trend (Last 30 Days)</CardTitle></CardHeader><CardContent>
            <div className="space-y-2">{summary.incident_trend?.map?.((p: any, i: number) => (<div key={i} className="flex items-center justify-between"><span className="text-sm">{p.date}</span><div className="h-2 bg-orange-500 rounded" style={{ width: `${(p.count / (summary.incident_trend?.[0]?.count || 1)) * 100}%` }} /><span className="text-sm font-mono">{p.count}</span></div>))}</div>
          </CardContent></Card>
        </TabsContent>
        <TabsContent value="sla_compliance">
          <Card><CardHeader><CardTitle>SLA Compliance by Severity</CardTitle></CardHeader><CardContent>
            <Table><TableHeader><TableRow><TableHead>Severity</TableHead><TableHead>SLA Target</TableHead><TableHead>Met</TableHead><TableHead>Missed</TableHead><TableHead>Compliance</TableHead></TableRow></TableHeader><TableBody>
              {summary.sla_data?.map?.((s: any, i: number) => (<TableRow key={i}><TableCell className="font-medium">{s.severity}</TableCell><TableCell>{s.target}</TableCell><TableCell>{s.met}</TableCell><TableCell>{s.missed}</TableCell><TableCell><Badge variant={s.compliance > 95 ? 'default' : 'destructive'}>{s.compliance}%</Badge></TableCell></TableRow>))}
              {(!summary.sla_data || summary.sla_data.length === 0) && <TableRow><TableCell colSpan={5} className="text-center text-muted-foreground">No SLA data available</TableCell></TableRow>}
            </TableBody></Table>
          </CardContent></Card>
        </TabsContent>
        <TabsContent value="root_causes">
          <Card><CardHeader><CardTitle>Top Root Causes</CardTitle></CardHeader><CardContent>
            <div className="space-y-2">{summary.root_causes?.map?.((r: any, i: number) => (<div key={i} className="flex items-center justify-between p-2 border rounded"><span>{r.cause}</span><span className="text-sm font-mono">{r.count} incidents ({r.percent}%)</span></div>))}</div>
          </CardContent></Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};
