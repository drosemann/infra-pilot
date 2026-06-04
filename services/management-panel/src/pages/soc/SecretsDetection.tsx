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

interface SecretFinding { id: string; secret_type: string; severity: string; file_path: string; line_number: number; repository: string; remediation_status: string; auto_rotated: boolean; discovered_at?: string; snippet?: string; }
interface ScanTarget { id: string; name: string; source_type: string; location: string; last_scan: string; findings_count: number; }

export const SecretsDetectionPage = () => {
  const [findings, setFindings] = useState<SecretFinding[]>([]);
  const [targets, setTargets] = useState<ScanTarget[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [severityFilter, setSeverityFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [summary, setSummary] = useState<any>({});
  const [showTargetModal, setShowTargetModal] = useState(false);
  const [targetForm, setTargetForm] = useState({ name: '', source_type: 'repository', location: '' });
  const [showDismissConfirm, setShowDismissConfirm] = useState<string | null>(null);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [f, t, sm] = await Promise.all([
        apiClient.get('/api/v1/soc/secrets/findings'),
        apiClient.get('/api/v1/soc/secrets/targets'),
        apiClient.get('/api/v1/soc/secrets/summary'),
      ]);
      setFindings(f?.data?.findings || []);
      setTargets(t?.data || []);
      setSummary(sm?.data || {});
    } catch { toast.error('Failed to load secrets data'); }
    finally { setLoading(false); }
  };

  const rotateSecret = async (id: string) => {
    try {
      await apiClient.post(`/api/v1/soc/secrets/findings/${id}/rotate`);
      toast.success('Secret rotation initiated');
      loadData();
    } catch { toast.error('Failed to rotate secret'); }
  };

  const dismissFinding = async () => {
    if (!showDismissConfirm) return;
    try {
      await apiClient.post(`/api/v1/soc/secrets/findings/${showDismissConfirm}/dismiss`);
      toast.success('Finding dismissed');
      setShowDismissConfirm(null);
      loadData();
    } catch { toast.error('Failed to dismiss finding'); }
  };

  const addTarget = async () => {
    try {
      await apiClient.post('/api/v1/soc/secrets/targets', targetForm);
      toast.success('Target added');
      setShowTargetModal(false);
      setTargetForm({ name: '', source_type: 'repository', location: '' });
      loadData();
    } catch { toast.error('Failed to add target'); }
  };

  const filteredFindings = findings.filter(f => {
    if (severityFilter !== 'all' && f.severity !== severityFilter) return false;
    if (statusFilter === 'open' && f.remediation_status !== 'open') return false;
    if (statusFilter === 'rotated' && f.remediation_status !== 'rotated') return false;
    if (searchQuery && !f.file_path.toLowerCase().includes(searchQuery.toLowerCase()) && !f.secret_type.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  const paginatedFindings = filteredFindings.slice((page - 1) * pageSize, page * pageSize);
  const openCount = findings.filter(f => f.remediation_status === 'open').length;
  const rotatedCount = findings.filter(f => f.auto_rotated).length;
  const criticalCount = findings.filter(f => f.severity === 'critical').length;

  return (
    <div className="space-y-6 p-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Secrets Detection & Remediation</h1>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setShowTargetModal(true)}>Add Target</Button>
          <Button onClick={loadData}>Refresh</Button>
        </div>
      </div>
      <div className="grid gap-4 md:grid-cols-4">
        <Card><CardHeader><CardTitle>Findings</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold">{findings.length}</p><p className="text-xs text-muted-foreground">{openCount} open</p></CardContent></Card>
        <Card><CardHeader><CardTitle>Critical</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold text-red-500">{criticalCount}</p></CardContent></Card>
        <Card><CardHeader><CardTitle>Auto-Rotated</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold text-green-500">{rotatedCount}</p></CardContent></Card>
        <Card><CardHeader><CardTitle>Targets</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold">{targets.length}</p><p className="text-xs text-muted-foreground">repositories scanned</p></CardContent></Card>
      </div>
      <div className="flex gap-4 items-center">
        <Input placeholder="Search files, types..." value={searchQuery} onChange={e => { setSearchQuery(e.target.value); setPage(1); }} className="max-w-xs" />
        <Select value={severityFilter} onValueChange={v => { setSeverityFilter(v); setPage(1); }}>
          <option value="all">All Severities</option>
          <option value="critical">Critical</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option>
        </Select>
        <Select value={statusFilter} onValueChange={v => { setStatusFilter(v); setPage(1); }}>
          <option value="all">All Status</option>
          <option value="open">Open</option><option value="rotated">Rotated</option>
        </Select>
      </div>
      <Tabs defaultValue="findings">
        <TabsList><TabsTrigger value="findings">Findings ({filteredFindings.length})</TabsTrigger><TabsTrigger value="targets">Targets ({targets.length})</TabsTrigger></TabsList>
        <TabsContent value="findings">
          <Table>
            <TableHeader><TableRow><TableHead>Type</TableHead><TableHead>File</TableHead><TableHead>Line</TableHead><TableHead>Severity</TableHead><TableHead>Status</TableHead><TableHead>Repository</TableHead><TableHead>Discovered</TableHead><TableHead>Actions</TableHead></TableRow></TableHeader>
            <TableBody>
              {paginatedFindings.map(f => (
                <TableRow key={f.id}>
                  <TableCell><Badge variant="outline">{f.secret_type}</Badge></TableCell>
                  <TableCell className="font-mono text-xs max-w-xs truncate" title={f.file_path}>{f.file_path}</TableCell>
                  <TableCell>{f.line_number}</TableCell>
                  <TableCell><Badge variant={f.severity === 'critical' ? 'destructive' : f.severity === 'high' ? 'default' : 'secondary'}>{f.severity}</Badge></TableCell>
                  <TableCell><Badge variant={f.remediation_status === 'rotated' ? 'default' : f.remediation_status === 'open' ? 'destructive' : 'secondary'}>{f.remediation_status}</Badge></TableCell>
                  <TableCell className="text-xs">{f.repository || 'N/A'}</TableCell>
                  <TableCell className="text-xs">{f.discovered_at ? new Date(f.discovered_at).toLocaleDateString() : '-'}</TableCell>
                  <TableCell>
                    <div className="flex gap-1">
                      {f.remediation_status === 'open' && <Button size="sm" onClick={() => rotateSecret(f.id)}>Rotate</Button>}
                      {f.remediation_status === 'open' && <Button size="sm" variant="outline" onClick={() => setShowDismissConfirm(f.id)}>Dismiss</Button>}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
              {paginatedFindings.length === 0 && <TableRow><TableCell colSpan={8} className="text-center py-4 text-muted-foreground">No findings</TableCell></TableRow>}
            </TableBody>
          </Table>
          {filteredFindings.length > pageSize && (
            <Pagination page={page} totalPages={Math.ceil(filteredFindings.length / pageSize)} onPageChange={setPage} />
          )}
        </TabsContent>
        <TabsContent value="targets">
          <Table>
            <TableHeader><TableRow><TableHead>Name</TableHead><TableHead>Source</TableHead><TableHead>Location</TableHead><TableHead>Findings</TableHead><TableHead>Last Scan</TableHead></TableRow></TableHeader>
            <TableBody>
              {targets.map(t => (
                <TableRow key={t.id}>
                  <TableCell className="font-medium">{t.name}</TableCell>
                  <TableCell><Badge variant="outline">{t.source_type}</Badge></TableCell>
                  <TableCell className="font-mono text-xs max-w-xs truncate">{t.location}</TableCell>
                  <TableCell>{t.findings_count}</TableCell>
                  <TableCell className="text-xs">{t.last_scan ? new Date(t.last_scan).toLocaleDateString() : 'Never'}</TableCell>
                </TableRow>
              ))}
              {targets.length === 0 && <TableRow><TableCell colSpan={5} className="text-center py-4 text-muted-foreground">No targets added</TableCell></TableRow>}
            </TableBody>
          </Table>
        </TabsContent>
      </Tabs>

      <Dialog open={showTargetModal} onOpenChange={setShowTargetModal}>
        <DialogContent>
          <DialogHeader><DialogTitle>Add Scan Target</DialogTitle></DialogHeader>
          <div className="space-y-4">
            <div><Label>Name</Label><Input value={targetForm.name} onChange={e => setTargetForm({ ...targetForm, name: e.target.value })} /></div>
            <div><Label>Source Type</Label><Select value={targetForm.source_type} onValueChange={v => setTargetForm({ ...targetForm, source_type: v })}>
              <option value="repository">Repository</option><option value="s3">S3 Bucket</option><option value="gcs">GCS Bucket</option><option value="filesystem">Filesystem</option>
            </Select></div>
            <div><Label>Location (URL/path)</Label><Input value={targetForm.location} onChange={e => setTargetForm({ ...targetForm, location: e.target.value })} /></div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowTargetModal(false)}>Cancel</Button>
            <Button onClick={addTarget}>Add</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={!!showDismissConfirm} onOpenChange={() => setShowDismissConfirm(null)}>
        <DialogContent>
          <DialogHeader><DialogTitle>Dismiss Finding</DialogTitle></DialogHeader>
          <p>Dismiss this finding as false positive?</p>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDismissConfirm(null)}>Cancel</Button>
            <Button variant="secondary" onClick={dismissFinding}>Dismiss</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-6">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Total Findings</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{summary.total_findings || 0}</div><p className="text-xs text-muted-foreground">{summary.new_findings_24h || 0} new in 24h</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Critical Secrets</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-red-500">{summary.critical_findings || 0}</div><p className="text-xs text-muted-foreground">exposed credentials/keys</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Sources Scanned</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{summary.sources_scanned || 0}</div><p className="text-xs text-muted-foreground">{summary.repos_scanned || 0} repositories</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Remediation Rate</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-green-500">{summary.remediation_rate || 0}%</div><p className="text-xs text-muted-foreground">{summary.remediated || 0} resolved</p></CardContent></Card>
      </div>

      <Tabs defaultValue="finding_trend" className="mb-6">
        <TabsList><TabsTrigger value="finding_trend">Finding Trend</TabsTrigger><TabsTrigger value="top_locations">Top Locations</TabsTrigger><TabsTrigger value="secret_types">Secret Types</TabsTrigger></TabsList>
        <TabsContent value="finding_trend">
          <Card><CardHeader><CardTitle>Secrets Finding Trend (Last 30 Days)</CardTitle></CardHeader><CardContent>
            <div className="space-y-2">{summary.finding_trend?.map?.((p: any, i: number) => (<div key={i} className="flex items-center justify-between"><span className="text-sm">{p.date}</span><div className="h-2 bg-red-500 rounded" style={{ width: `${(p.count / (summary.finding_trend?.[0]?.count || 1)) * 100}%` }} /><span className="text-sm font-mono">{p.count}</span></div>))}</div>
          </CardContent></Card>
        </TabsContent>
        <TabsContent value="top_locations">
          <Card><CardHeader><CardTitle>Top Secret Locations</CardTitle></CardHeader><CardContent>
            <Table><TableHeader><TableRow><TableHead>Location</TableHead><TableHead>Findings</TableHead><TableHead>Percent</TableHead></TableRow></TableHeader><TableBody>
              {summary.top_locations?.map?.((l: any, i: number) => (<TableRow key={i}><TableCell className="font-mono text-xs">{l.location}</TableCell><TableCell>{l.count}</TableCell><TableCell>{l.percent}%</TableCell></TableRow>))}
              {(!summary.top_locations || summary.top_locations.length === 0) && <TableRow><TableCell colSpan={3} className="text-center text-muted-foreground">No location data available</TableCell></TableRow>}
            </TableBody></Table>
          </CardContent></Card>
        </TabsContent>
        <TabsContent value="secret_types">
          <Card><CardHeader><CardTitle>Secret Types Distribution</CardTitle></CardHeader><CardContent>
            <div className="grid gap-2">{summary.secret_types?.map?.((t: any, i: number) => (<div key={i} className="flex items-center justify-between p-2 border rounded"><span className="font-medium">{t.type}</span><span className="text-sm">{t.count} ({t.percent}%)</span></div>))}</div>
          </CardContent></Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};
