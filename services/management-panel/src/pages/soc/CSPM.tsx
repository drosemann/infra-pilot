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

interface CloudAccount { id: string; name: string; provider: string; score: number; total_checks: number; failed_checks: number; last_scanned?: string; }
interface CheckResult { id: string; check_title: string; resource_name: string; resource_id: string; status: string; severity: string; benchmark: string; auto_remediated: boolean; last_checked?: string; }

export const CSPMPage = () => {
  const [accounts, setAccounts] = useState<CloudAccount[]>([]);
  const [results, setResults] = useState<CheckResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [severityFilter, setSeverityFilter] = useState('all');
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [summary, setSummary] = useState<any>({});
  const [showAccountModal, setShowAccountModal] = useState(false);
  const [accountForm, setAccountForm] = useState({ name: '', provider: 'aws', account_id: '' });
  const [showRemediateConfirm, setShowRemediateConfirm] = useState<string | null>(null);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [accts, res, sm] = await Promise.all([
        apiClient.get('/api/v1/soc/cspm/accounts'),
        apiClient.get('/api/v1/soc/cspm/results'),
        apiClient.get('/api/v1/soc/cspm/summary'),
      ]);
      setAccounts(accts?.data || []);
      setResults(res?.data?.results || []);
      setSummary(sm?.data || {});
    } catch { toast.error('Failed to load CSPM data'); }
    finally { setLoading(false); }
  };

  const runScan = async () => {
    try {
      await apiClient.post('/api/v1/soc/cspm/scan', {});
      toast.success('Scan initiated');
    } catch { toast.error('Failed to start scan'); }
  };

  const addAccount = async () => {
    try {
      await apiClient.post('/api/v1/soc/cspm/accounts', accountForm);
      toast.success('Account added');
      setShowAccountModal(false);
      setAccountForm({ name: '', provider: 'aws', account_id: '' });
      loadData();
    } catch { toast.error('Failed to add account'); }
  };

  const remediateCheck = async (checkId: string) => {
    try {
      await apiClient.post(`/api/v1/soc/cspm/results/${checkId}/remediate`);
      toast.success('Auto-remediation initiated');
      setShowRemediateConfirm(null);
      loadData();
    } catch { toast.error('Failed to remediate'); }
  };

  const filteredResults = results.filter(r => {
    if (statusFilter === 'pass' && r.status !== 'pass') return false;
    if (statusFilter === 'fail' && r.status !== 'fail') return false;
    if (severityFilter !== 'all' && r.severity !== severityFilter) return false;
    if (searchQuery && !r.check_title.toLowerCase().includes(searchQuery.toLowerCase()) && !r.resource_name.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  const paginatedResults = filteredResults.slice((page - 1) * pageSize, page * pageSize);
  const totalChecks = results.length;
  const passedChecks = results.filter(r => r.status === 'pass').length;
  const failedChecks = results.filter(r => r.status === 'fail').length;
  const overallScore = totalChecks > 0 ? Math.round((passedChecks / totalChecks) * 100) : 0;
  const autoRemediated = results.filter(r => r.auto_remediated).length;

  return (
    <div className="space-y-6 p-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Cloud Security Posture Management</h1>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setShowAccountModal(true)}>Add Account</Button>
          <Button variant="outline" onClick={loadData}>Refresh</Button>
          <Button onClick={runScan}>Run Scan</Button>
        </div>
      </div>
      <div className="grid gap-4 md:grid-cols-4">
        <Card><CardHeader><CardTitle>Overall Score</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold">{overallScore}%</p><p className="text-xs text-muted-foreground">{passedChecks}/{totalChecks} passing</p></CardContent></Card>
        <Card><CardHeader><CardTitle>Failed Checks</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold text-red-500">{failedChecks}</p></CardContent></Card>
        <Card><CardHeader><CardTitle>Auto-Remediated</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold text-green-500">{autoRemediated}</p></CardContent></Card>
        <Card><CardHeader><CardTitle>Accounts</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold">{accounts.length}</p><p className="text-xs text-muted-foreground">{accounts.filter(a => a.score < 70).length} below 70%</p></CardContent></Card>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {accounts.map(a => (
          <Card key={a.id}>
            <CardHeader><CardTitle className="flex items-center gap-2"><Badge variant="outline">{a.provider.toUpperCase()}</Badge>{a.name}</CardTitle></CardHeader>
            <CardContent>
              <p className="text-3xl font-bold">{a.score}%</p>
              <p className="text-sm text-muted-foreground">{a.total_checks - a.failed_checks}/{a.total_checks} passed</p>
              {a.last_scanned && <p className="text-xs text-muted-foreground mt-1">Last scan: {new Date(a.last_scanned).toLocaleDateString()}</p>}
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="flex gap-4 items-center">
        <Input placeholder="Search checks..." value={searchQuery} onChange={e => { setSearchQuery(e.target.value); setPage(1); }} className="max-w-xs" />
        <Select value={statusFilter} onValueChange={v => { setStatusFilter(v); setPage(1); }}>
          <option value="all">All Status</option>
          <option value="pass">Pass</option><option value="fail">Fail</option>
        </Select>
        <Select value={severityFilter} onValueChange={v => { setSeverityFilter(v); setPage(1); }}>
          <option value="all">All Severities</option>
          <option value="critical">Critical</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option>
        </Select>
      </div>

      <Tabs defaultValue="results">
        <TabsList><TabsTrigger value="results">Checks ({filteredResults.length})</TabsTrigger></TabsList>
        <TabsContent value="results">
          <Table>
            <TableHeader><TableRow><TableHead>Check</TableHead><TableHead>Resource</TableHead><TableHead>Benchmark</TableHead><TableHead>Status</TableHead><TableHead>Severity</TableHead><TableHead>Auto-Remediated</TableHead><TableHead>Actions</TableHead></TableRow></TableHeader>
            <TableBody>
              {paginatedResults.map(r => (
                <TableRow key={r.id}>
                  <TableCell className="max-w-sm truncate" title={r.check_title}>{r.check_title}</TableCell>
                  <TableCell className="font-mono text-xs max-w-xs truncate">{r.resource_name}</TableCell>
                  <TableCell><Badge variant="outline">{r.benchmark}</Badge></TableCell>
                  <TableCell><Badge variant={r.status === 'pass' ? 'default' : 'destructive'}>{r.status}</Badge></TableCell>
                  <TableCell><Badge variant={r.severity === 'critical' ? 'destructive' : r.severity === 'high' ? 'default' : 'secondary'}>{r.severity}</Badge></TableCell>
                  <TableCell>{r.auto_remediated ? <Badge variant="default">Yes</Badge> : <Badge variant="secondary">No</Badge>}</TableCell>
                  <TableCell>
                    {r.status === 'fail' && !r.auto_remediated && (
                      <Button size="sm" variant="outline" onClick={() => setShowRemediateConfirm(r.id)}>Remediate</Button>
                    )}
                  </TableCell>
                </TableRow>
              ))}
              {paginatedResults.length === 0 && <TableRow><TableCell colSpan={7} className="text-center py-4 text-muted-foreground">No results found</TableCell></TableRow>}
            </TableBody>
          </Table>
          {filteredResults.length > pageSize && (
            <Pagination page={page} totalPages={Math.ceil(filteredResults.length / pageSize)} onPageChange={setPage} />
          )}
        </TabsContent>
      </Tabs>

      <Dialog open={showAccountModal} onOpenChange={setShowAccountModal}>
        <DialogContent>
          <DialogHeader><DialogTitle>Add Cloud Account</DialogTitle></DialogHeader>
          <div className="space-y-4">
            <div><Label>Name</Label><Input value={accountForm.name} onChange={e => setAccountForm({ ...accountForm, name: e.target.value })} /></div>
            <div><Label>Provider</Label><Select value={accountForm.provider} onValueChange={v => setAccountForm({ ...accountForm, provider: v })}>
              <option value="aws">AWS</option><option value="azure">Azure</option><option value="gcp">GCP</option>
            </Select></div>
            <div><Label>Account ID</Label><Input value={accountForm.account_id} onChange={e => setAccountForm({ ...accountForm, account_id: e.target.value })} /></div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAccountModal(false)}>Cancel</Button>
            <Button onClick={addAccount}>Add</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={!!showRemediateConfirm} onOpenChange={() => setShowRemediateConfirm(null)}>
        <DialogContent>
          <DialogHeader><DialogTitle>Auto-Remediate</DialogTitle></DialogHeader>
          <p>Apply auto-remediation for this check?</p>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowRemediateConfirm(null)}>Cancel</Button>
            <Button onClick={() => remediateCheck(showRemediateConfirm!)}>Remediate</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-6">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Total Resources</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{summary.total_resources || 0}</div><p className="text-xs text-muted-foreground">across all cloud accounts</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Compliance Score</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{summary.compliance_score || 0}%</div><p className="text-xs text-muted-foreground">{summary.passed_checks || 0}/{summary.total_checks || 0} checks passing</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Critical Findings</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-red-500">{summary.critical_findings || 0}</div><p className="text-xs text-muted-foreground">require immediate action</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Auto-Remediated</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-green-500">{summary.auto_remediated || 0}</div><p className="text-xs text-muted-foreground">issues fixed automatically</p></CardContent></Card>
      </div>

      <Tabs defaultValue="compliance_trend" className="mb-6">
        <TabsList><TabsTrigger value="compliance_trend">Compliance Trend</TabsTrigger><TabsTrigger value="top_failures">Top Failures</TabsTrigger><TabsTrigger value="resource_coverage">Resource Coverage</TabsTrigger></TabsList>
        <TabsContent value="compliance_trend">
          <Card><CardHeader><CardTitle>Compliance Score Trend (Last 30 Days)</CardTitle></CardHeader><CardContent>
            <div className="space-y-2">{summary.compliance_trend?.map?.((point: any, i: number) => (<div key={i} className="flex items-center justify-between"><span className="text-sm">{point.date}</span><div className="h-2 bg-primary rounded" style={{ width: `${point.score}%` }} /><span className="text-sm font-mono">{point.score}%</span></div>))}</div>
          </CardContent></Card>
        </TabsContent>
        <TabsContent value="top_failures">
          <Card><CardHeader><CardTitle>Most Common Check Failures</CardTitle></CardHeader><CardContent>
            <Table><TableHeader><TableRow><TableHead>Check</TableHead><TableHead>Failures</TableHead><TableHead>Severity</TableHead></TableRow></TableHeader><TableBody>
              {summary.top_failures?.map?.((f: any, i: number) => (<TableRow key={i}><TableCell>{f.check}</TableCell><TableCell>{f.count}</TableCell><TableCell><Badge variant={f.severity === 'critical' ? 'destructive' : 'default'}>{f.severity}</Badge></TableCell></TableRow>))}
              {(!summary.top_failures || summary.top_failures.length === 0) && <TableRow><TableCell colSpan={3} className="text-center text-muted-foreground">No failure data available</TableCell></TableRow>}
            </TableBody></Table>
          </CardContent></Card>
        </TabsContent>
        <TabsContent value="resource_coverage">
          <Card><CardHeader><CardTitle>Resource Coverage by Provider</CardTitle></CardHeader><CardContent>
            <div className="grid gap-2">{summary.provider_coverage?.map?.((p: any, i: number) => (<div key={i} className="flex items-center justify-between p-2 border rounded"><span className="font-medium">{p.provider}</span><span className="text-sm text-muted-foreground">{p.resources} resources ({p.percentage}%)</span></div>))}</div>
          </CardContent></Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};
