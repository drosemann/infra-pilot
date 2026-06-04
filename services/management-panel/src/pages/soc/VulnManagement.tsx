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

interface Vulnerability { id: string; cve_id: string; title: string; severity: string; cvss_score: number; exploit_available: boolean; patch_available: boolean; status?: string; package?: string; created_at?: string; }
interface Scan { id: string; name: string; engine: string; status: string; target_assets?: string[]; vulnerabilities_found?: number; created_at?: string; }

export const VulnManagementPage = () => {
  const [vulns, setVulns] = useState<Vulnerability[]>([]);
  const [scans, setScans] = useState<Scan[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [severityFilter, setSeverityFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [summary, setSummary] = useState<any>({});
  const [showScanModal, setShowScanModal] = useState(false);
  const [scanForm, setScanForm] = useState({ name: '', targets: '', scan_type: 'full' });
  const [showVulnModal, setShowVulnModal] = useState<Vulnerability | null>(null);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [v, s, sm] = await Promise.all([
        apiClient.get('/api/v1/soc/vulnerabilities'),
        apiClient.get('/api/v1/soc/vulnerabilities/scans'),
        apiClient.get('/api/v1/soc/vulnerabilities/summary'),
      ]);
      setVulns(v?.data?.vulnerabilities || []);
      setScans(s?.data || []);
      setSummary(sm?.data || {});
    } catch { toast.error('Failed to load vulnerability data'); }
    finally { setLoading(false); }
  };

  const startScan = async () => {
    try {
      await apiClient.post('/api/v1/soc/vulnerabilities/scans', {
        ...scanForm,
        targets: scanForm.targets.split(',').map(t => t.trim()).filter(Boolean),
      });
      toast.success('Scan started');
      setShowScanModal(false);
      setScanForm({ name: '', targets: '', scan_type: 'full' });
      loadData();
    } catch { toast.error('Failed to start scan'); }
  };

  const filteredVulns = vulns.filter(v => {
    if (severityFilter !== 'all' && v.severity !== severityFilter) return false;
    if (statusFilter === 'exploitable' && !v.exploit_available) return false;
    if (statusFilter === 'patchable' && !v.patch_available) return false;
    if (searchQuery && !v.cve_id.toLowerCase().includes(searchQuery.toLowerCase()) && !v.title.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  const paginatedVulns = filteredVulns.slice((page - 1) * pageSize, page * pageSize);
  const criticalVulns = vulns.filter(v => v.severity === 'critical').length;
  const exploitableVulns = vulns.filter(v => v.exploit_available).length;
  const avgCvss = vulns.length ? (vulns.reduce((s, v) => s + v.cvss_score, 0) / vulns.length).toFixed(1) : '0';

  return (
    <div className="space-y-6 p-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Vulnerability Management</h1>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setShowScanModal(true)}>New Scan</Button>
          <Button onClick={loadData}>Refresh</Button>
        </div>
      </div>
      <div className="grid gap-4 md:grid-cols-4">
        <Card><CardHeader><CardTitle>Total Vulns</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold">{vulns.length}</p><p className="text-xs text-muted-foreground">avg CVSS {avgCvss}</p></CardContent></Card>
        <Card><CardHeader><CardTitle>Critical</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold text-red-500">{criticalVulns}</p></CardContent></Card>
        <Card><CardHeader><CardTitle>Exploit Available</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold text-orange-500">{exploitableVulns}</p></CardContent></Card>
        <Card><CardHeader><CardTitle>Scans</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold">{scans.length}</p><p className="text-xs text-muted-foreground">{scans.filter(s => s.status === 'completed').length} completed</p></CardContent></Card>
      </div>
      <div className="flex gap-4 items-center">
        <Input placeholder="Search CVE or title..." value={searchQuery} onChange={e => { setSearchQuery(e.target.value); setPage(1); }} className="max-w-xs" />
        <Select value={severityFilter} onValueChange={v => { setSeverityFilter(v); setPage(1); }}>
          <option value="all">All Severities</option>
          <option value="critical">Critical</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option>
        </Select>
        <Select value={statusFilter} onValueChange={v => { setStatusFilter(v); setPage(1); }}>
          <option value="all">All Status</option>
          <option value="exploitable">Exploitable</option><option value="patchable">Patchable</option>
        </Select>
      </div>
      <Tabs defaultValue="vulnerabilities">
        <TabsList><TabsTrigger value="vulnerabilities">Vulnerabilities ({filteredVulns.length})</TabsTrigger><TabsTrigger value="scans">Scans ({scans.length})</TabsTrigger></TabsList>
        <TabsContent value="vulnerabilities">
          <Table>
            <TableHeader><TableRow><TableHead>CVE</TableHead><TableHead>Package</TableHead><TableHead>Severity</TableHead><TableHead>CVSS</TableHead><TableHead>Exploit</TableHead><TableHead>Patch</TableHead><TableHead>Status</TableHead></TableRow></TableHeader>
            <TableBody>
              {paginatedVulns.map(v => (
                <TableRow key={v.id} className="cursor-pointer" onClick={() => setShowVulnModal(v)}>
                  <TableCell className="font-mono text-xs">{v.cve_id}</TableCell>
                  <TableCell className="text-xs">{v.package || '-'}</TableCell>
                  <TableCell><Badge variant={v.severity === 'critical' ? 'destructive' : v.severity === 'high' ? 'default' : 'secondary'}>{v.severity}</Badge></TableCell>
                  <TableCell>{v.cvss_score}</TableCell>
                  <TableCell>{v.exploit_available ? <Badge variant="destructive">Yes</Badge> : <Badge variant="secondary">No</Badge>}</TableCell>
                  <TableCell>{v.patch_available ? <Badge variant="default">Available</Badge> : <Badge variant="secondary">N/A</Badge>}</TableCell>
                  <TableCell><Badge variant="outline">{v.status || 'open'}</Badge></TableCell>
                </TableRow>
              ))}
              {paginatedVulns.length === 0 && <TableRow><TableCell colSpan={7} className="text-center py-4 text-muted-foreground">No vulnerabilities found</TableCell></TableRow>}
            </TableBody>
          </Table>
          {filteredVulns.length > pageSize && (
            <Pagination page={page} totalPages={Math.ceil(filteredVulns.length / pageSize)} onPageChange={setPage} />
          )}
        </TabsContent>
        <TabsContent value="scans">
          <Table>
            <TableHeader><TableRow><TableHead>Name</TableHead><TableHead>Engine</TableHead><TableHead>Type</TableHead><TableHead>Status</TableHead><TableHead>Targets</TableHead><TableHead>Findings</TableHead><TableHead>Created</TableHead></TableRow></TableHeader>
            <TableBody>
              {scans.map(s => (
                <TableRow key={s.id}>
                  <TableCell className="font-medium">{s.name}</TableCell>
                  <TableCell><Badge variant="outline">{s.engine}</Badge></TableCell>
                  <TableCell><Badge variant="outline">{s.scan_type || 'full'}</Badge></TableCell>
                  <TableCell><Badge variant={s.status === 'completed' ? 'default' : s.status === 'running' ? 'secondary' : 'destructive'}>{s.status}</Badge></TableCell>
                  <TableCell>{s.target_assets?.length || 0}</TableCell>
                  <TableCell>{s.vulnerabilities_found || 0}</TableCell>
                  <TableCell className="text-xs">{s.created_at ? new Date(s.created_at).toLocaleDateString() : '-'}</TableCell>
                </TableRow>
              ))}
              {scans.length === 0 && <TableRow><TableCell colSpan={7} className="text-center py-4 text-muted-foreground">No scans found</TableCell></TableRow>}
            </TableBody>
          </Table>
        </TabsContent>
      </Tabs>

      <Dialog open={showScanModal} onOpenChange={setShowScanModal}>
        <DialogContent>
          <DialogHeader><DialogTitle>New Vulnerability Scan</DialogTitle></DialogHeader>
          <div className="space-y-4">
            <div><Label>Scan Name</Label><Input value={scanForm.name} onChange={e => setScanForm({ ...scanForm, name: e.target.value })} /></div>
            <div><Label>Targets (comma-separated IPs/hosts)</Label><Input value={scanForm.targets} onChange={e => setScanForm({ ...scanForm, targets: e.target.value })} placeholder="10.0.0.1, 10.0.0.2" /></div>
            <div><Label>Scan Type</Label><Select value={scanForm.scan_type} onValueChange={v => setScanForm({ ...scanForm, scan_type: v })}>
              <option value="full">Full</option><option value="quick">Quick</option><option value="custom">Custom</option>
            </Select></div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowScanModal(false)}>Cancel</Button>
            <Button onClick={startScan}>Start Scan</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={!!showVulnModal} onOpenChange={() => setShowVulnModal(null)}>
        <DialogContent className="max-w-lg">
          <DialogHeader><DialogTitle>{showVulnModal?.cve_id}</DialogTitle></DialogHeader>
          <div className="space-y-3">
            <p><strong>Title:</strong> {showVulnModal?.title}</p>
            <p><strong>Severity:</strong> {showVulnModal?.severity} (CVSS: {showVulnModal?.cvss_score})</p>
            <p><strong>Exploit Available:</strong> {showVulnModal?.exploit_available ? 'Yes' : 'No'}</p>
            <p><strong>Patch Available:</strong> {showVulnModal?.patch_available ? 'Yes' : 'No'}</p>
            <p><strong>Package:</strong> {showVulnModal?.package || 'N/A'}</p>
          </div>
          <DialogFooter><Button variant="outline" onClick={() => setShowVulnModal(null)}>Close</Button></DialogFooter>
        </DialogContent>
      </Dialog>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-6">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Total Vulnerabilities</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{summary.total_vulns || 0}</div><p className="text-xs text-muted-foreground">{summary.critical || 0} critical, {summary.high || 0} high</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Remediation Rate</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-green-500">{summary.remediation_rate || 0}%</div><p className="text-xs text-muted-foreground">{summary.remediated || 0} resolved (30d)</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">MTTR</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{summary.mttr_days || 0}d</div><p className="text-xs text-muted-foreground">mean time to remediate</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Scans Completed</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{summary.scans || 0}</div><p className="text-xs text-muted-foreground">{summary.assets_scanned || 0} assets covered</p></CardContent></Card>
      </div>

      <Tabs defaultValue="vuln_trend" className="mb-6">
        <TabsList><TabsTrigger value="vuln_trend">Vulnerability Trend</TabsTrigger><TabsTrigger value="severity_dist">Severity Distribution</TabsTrigger><TabsTrigger value="top_assets">Top Vulnerable Assets</TabsTrigger></TabsList>
        <TabsContent value="vuln_trend">
          <Card><CardHeader><CardTitle>Vulnerability Trend (Last 30 Days)</CardTitle></CardHeader><CardContent>
            <div className="space-y-2">{summary.vuln_trend?.map?.((p: any, i: number) => (<div key={i} className="flex items-center justify-between"><span className="text-sm">{p.date}</span><div className="h-2 bg-red-500 rounded" style={{ width: `${(p.count / (summary.vuln_trend?.[0]?.count || 1)) * 100}%` }} /><span className="text-sm font-mono">{p.count}</span></div>))}</div>
          </CardContent></Card>
        </TabsContent>
        <TabsContent value="severity_dist">
          <Card><CardHeader><CardTitle>Severity Distribution</CardTitle></CardHeader><CardContent>
            <Table><TableHeader><TableRow><TableHead>Severity</TableHead><TableHead>Count</TableHead><TableHead>Percent</TableHead></TableRow></TableHeader><TableBody>
              {summary.severity_distribution?.map?.((s: any, i: number) => (<TableRow key={i}><TableCell className="font-medium">{s.severity}</TableCell><TableCell>{s.count}</TableCell><TableCell>{s.percent}%</TableCell></TableRow>))}
              {(!summary.severity_distribution || summary.severity_distribution.length === 0) && <TableRow><TableCell colSpan={3} className="text-center text-muted-foreground">No severity data available</TableCell></TableRow>}
            </TableBody></Table>
          </CardContent></Card>
        </TabsContent>
        <TabsContent value="top_assets">
          <Card><CardHeader><CardTitle>Top Vulnerable Assets</CardTitle></CardHeader><CardContent>
            <div className="space-y-2">{summary.top_assets?.map?.((a: any, i: number) => (<div key={i} className="flex items-center justify-between p-2 border rounded"><span className="font-medium">{a.name}</span><span className="text-sm">{a.critical} critical, {a.high} high, {a.total} total</span></div>))}</div>
          </CardContent></Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};
