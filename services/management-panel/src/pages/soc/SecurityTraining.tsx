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

interface TrainingModule { id: string; title: string; module_type: string; category: string; duration_minutes: number; required: boolean; completions: number; avg_score: number; }
interface PhishingCampaign { id: string; name: string; simulation_type: string; status: string; emails_sent: number; links_clicked: number; reported_phishing: number; started_at?: string; }
interface TrainingAssignment { id: string; user_id: string; user_name: string; module_id: string; module_title: string; passed: boolean; score: number; completed_at: string; assigned_at?: string; }

export const SecurityTrainingPage = () => {
  const [modules, setModules] = useState<TrainingModule[]>([]);
  const [campaigns, setCampaigns] = useState<PhishingCampaign[]>([]);
  const [assignments, setAssignments] = useState<TrainingAssignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [page, setPage] = useState(1);
  const [pageSize] = useState(15);
  const [summary, setSummary] = useState<any>({});
  const [showCampaignModal, setShowCampaignModal] = useState(false);
  const [campaignForm, setCampaignForm] = useState({ name: '', description: '', simulation_type: 'phishing_email', target_departments: '', template: 'standard' });
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [assignForm, setAssignForm] = useState({ user_id: '', module_id: '', department: '' });

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [m, c, a, sm] = await Promise.all([
        apiClient.get('/api/v1/soc/training/modules'),
        apiClient.get('/api/v1/soc/training/campaigns'),
        apiClient.get('/api/v1/soc/training/assignments'),
        apiClient.get('/api/v1/soc/training/summary'),
      ]);
      setModules(m?.data || []);
      setCampaigns(c?.data || []);
      setAssignments(a?.data || []);
      setSummary(sm?.data || {});
    } catch { toast.error('Failed to load training data'); }
    finally { setLoading(false); }
  };

  const createCampaign = async () => {
    try {
      await apiClient.post('/api/v1/soc/training/campaigns', {
        ...campaignForm,
        target_departments: campaignForm.target_departments.split(',').map(t => t.trim()).filter(Boolean),
      });
      toast.success('Campaign created');
      setShowCampaignModal(false);
      setCampaignForm({ name: '', description: '', simulation_type: 'phishing_email', target_departments: '', template: 'standard' });
      loadData();
    } catch { toast.error('Failed to create campaign'); }
  };

  const launchCampaign = async (id: string) => {
    try {
      await apiClient.post(`/api/v1/soc/training/campaigns/${id}/launch`);
      toast.success('Campaign launched');
      loadData();
    } catch { toast.error('Failed to launch campaign'); }
  };

  const assignModule = async () => {
    try {
      await apiClient.post('/api/v1/soc/training/assignments', assignForm);
      toast.success('Module assigned');
      setShowAssignModal(false);
      setAssignForm({ user_id: '', module_id: '', department: '' });
      loadData();
    } catch { toast.error('Failed to assign module'); }
  };

  const filteredModules = modules.filter(m => {
    if (categoryFilter !== 'all' && m.category !== categoryFilter) return false;
    if (searchQuery && !m.title.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  const paginatedModules = filteredModules.slice((page - 1) * pageSize, page * pageSize);
  const paginatedAssignments = assignments.slice((page - 1) * pageSize, page * pageSize);
  const completedAssignments = assignments.filter(a => a.completed_at).length;
  const completionRate = assignments.length ? ((completedAssignments / assignments.length) * 100).toFixed(1) : '0';
  const passedAssignments = assignments.filter(a => a.passed).length;
  const passRate = completedAssignments ? ((passedAssignments / completedAssignments) * 100).toFixed(1) : '0';

  return (
    <div className="space-y-6 p-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Security Awareness Training</h1>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setShowCampaignModal(true)}>New Campaign</Button>
          <Button variant="outline" onClick={() => setShowAssignModal(true)}>Assign Module</Button>
          <Button onClick={loadData}>Refresh</Button>
        </div>
      </div>
      <div className="grid gap-4 md:grid-cols-4">
        <Card><CardHeader><CardTitle>Modules</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold">{modules.length}</p><p className="text-xs text-muted-foreground">{modules.filter(m => m.required).length} required</p></CardContent></Card>
        <Card><CardHeader><CardTitle>Completion Rate</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold text-green-500">{completionRate}%</p></CardContent></Card>
        <Card><CardHeader><CardTitle>Pass Rate</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold">{passRate}%</p><p className="text-xs text-muted-foreground">{passedAssignments} passed</p></CardContent></Card>
        <Card><CardHeader><CardTitle>Campaigns</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold">{campaigns.length}</p><p className="text-xs text-muted-foreground">{campaigns.filter(c => c.status === 'running').length} active</p></CardContent></Card>
      </div>
      <div className="flex gap-4 items-center">
        <Input placeholder="Search modules..." value={searchQuery} onChange={e => { setSearchQuery(e.target.value); setPage(1); }} className="max-w-xs" />
        <Select value={categoryFilter} onValueChange={v => { setCategoryFilter(v); setPage(1); }}>
          <option value="all">All Categories</option>
          <option value="phishing">Phishing</option>
          <option value="password">Password Security</option>
          <option value="social_engineering">Social Engineering</option>
          <option value="data_protection">Data Protection</option>
        </Select>
      </div>
      <Tabs defaultValue="modules">
        <TabsList><TabsTrigger value="modules">Modules ({filteredModules.length})</TabsTrigger><TabsTrigger value="campaigns">Campaigns ({campaigns.length})</TabsTrigger><TabsTrigger value="assignments">Assignments ({assignments.length})</TabsTrigger></TabsList>
        <TabsContent value="modules">
          <Table>
            <TableHeader><TableRow><TableHead>Title</TableHead><TableHead>Category</TableHead><TableHead>Type</TableHead><TableHead>Duration</TableHead><TableHead>Required</TableHead><TableHead>Completions</TableHead><TableHead>Avg Score</TableHead></TableRow></TableHeader>
            <TableBody>
              {paginatedModules.map(m => (
                <TableRow key={m.id}>
                  <TableCell className="font-medium">{m.title}</TableCell>
                  <TableCell><Badge variant="outline">{m.category}</Badge></TableCell>
                  <TableCell>{m.module_type}</TableCell>
                  <TableCell>{m.duration_minutes}min</TableCell>
                  <TableCell>{m.required ? <Badge variant="default">Required</Badge> : <Badge variant="secondary">Optional</Badge>}</TableCell>
                  <TableCell>{m.completions}</TableCell>
                  <TableCell>{m.avg_score.toFixed(1)}%</TableCell>
                </TableRow>
              ))}
              {paginatedModules.length === 0 && <TableRow><TableCell colSpan={7} className="text-center py-4 text-muted-foreground">No modules found</TableCell></TableRow>}
            </TableBody>
          </Table>
          {filteredModules.length > pageSize && (
            <Pagination page={page} totalPages={Math.ceil(filteredModules.length / pageSize)} onPageChange={setPage} />
          )}
        </TabsContent>
        <TabsContent value="campaigns">
          <Table>
            <TableHeader><TableRow><TableHead>Name</TableHead><TableHead>Type</TableHead><TableHead>Status</TableHead><TableHead>Sent</TableHead><TableHead>Clicked</TableHead><TableHead>Reported</TableHead><TableHead>Click Rate</TableHead><TableHead>Actions</TableHead></TableRow></TableHeader>
            <TableBody>
              {campaigns.map(c => (
                <TableRow key={c.id}>
                  <TableCell className="font-medium">{c.name}</TableCell>
                  <TableCell><Badge variant="outline">{c.simulation_type}</Badge></TableCell>
                  <TableCell><Badge variant={c.status === 'completed' ? 'default' : c.status === 'running' ? 'secondary' : 'outline'}>{c.status}</Badge></TableCell>
                  <TableCell>{c.emails_sent}</TableCell>
                  <TableCell>{c.links_clicked}</TableCell>
                  <TableCell>{c.reported_phishing}</TableCell>
                  <TableCell>{c.emails_sent > 0 ? ((c.links_clicked / c.emails_sent) * 100).toFixed(1) + '%' : 'N/A'}</TableCell>
                  <TableCell>{c.status === 'draft' && <Button size="sm" onClick={() => launchCampaign(c.id)}>Launch</Button>}</TableCell>
                </TableRow>
              ))}
              {campaigns.length === 0 && <TableRow><TableCell colSpan={8} className="text-center py-4 text-muted-foreground">No campaigns</TableCell></TableRow>}
            </TableBody>
          </Table>
        </TabsContent>
        <TabsContent value="assignments">
          <Table>
            <TableHeader><TableRow><TableHead>User</TableHead><TableHead>Module</TableHead><TableHead>Score</TableHead><TableHead>Passed</TableHead><TableHead>Assigned</TableHead><TableHead>Completed</TableHead></TableRow></TableHeader>
            <TableBody>
              {paginatedAssignments.map(a => (
                <TableRow key={a.id}>
                  <TableCell>{a.user_name}</TableCell>
                  <TableCell className="max-w-xs truncate">{a.module_title}</TableCell>
                  <TableCell>{a.score}%</TableCell>
                  <TableCell>{a.passed ? <Badge variant="default">Passed</Badge> : <Badge variant="destructive">Failed</Badge>}</TableCell>
                  <TableCell className="text-xs">{a.assigned_at ? new Date(a.assigned_at).toLocaleDateString() : '-'}</TableCell>
                  <TableCell className="text-xs">{a.completed_at ? new Date(a.completed_at).toLocaleDateString() : 'Incomplete'}</TableCell>
                </TableRow>
              ))}
              {paginatedAssignments.length === 0 && <TableRow><TableCell colSpan={6} className="text-center py-4 text-muted-foreground">No assignments</TableCell></TableRow>}
            </TableBody>
          </Table>
          {assignments.length > pageSize && (
            <Pagination page={page} totalPages={Math.ceil(assignments.length / pageSize)} onPageChange={setPage} />
          )}
        </TabsContent>
      </Tabs>

      <Dialog open={showCampaignModal} onOpenChange={setShowCampaignModal}>
        <DialogContent>
          <DialogHeader><DialogTitle>Create Phishing Campaign</DialogTitle></DialogHeader>
          <div className="space-y-4">
            <div><Label>Name</Label><Input value={campaignForm.name} onChange={e => setCampaignForm({ ...campaignForm, name: e.target.value })} /></div>
            <div><Label>Description</Label><Input value={campaignForm.description} onChange={e => setCampaignForm({ ...campaignForm, description: e.target.value })} /></div>
            <div><Label>Simulation Type</Label><Select value={campaignForm.simulation_type} onValueChange={v => setCampaignForm({ ...campaignForm, simulation_type: v })}>
              <option value="phishing_email">Phishing Email</option>
              <option value="spear_phishing">Spear Phishing</option>
              <option value="smishing">SMS Phishing</option>
            </Select></div>
            <div><Label>Target Departments (comma-separated)</Label><Input value={campaignForm.target_departments} onChange={e => setCampaignForm({ ...campaignForm, target_departments: e.target.value })} placeholder="engineering, finance, hr" /></div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCampaignModal(false)}>Cancel</Button>
            <Button onClick={createCampaign}>Create</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={showAssignModal} onOpenChange={setShowAssignModal}>
        <DialogContent>
          <DialogHeader><DialogTitle>Assign Training Module</DialogTitle></DialogHeader>
          <div className="space-y-4">
            <div><Label>User ID</Label><Input value={assignForm.user_id} onChange={e => setAssignForm({ ...assignForm, user_id: e.target.value })} /></div>
            <div><Label>Module</Label><Select value={assignForm.module_id} onValueChange={v => setAssignForm({ ...assignForm, module_id: v })}>
              {modules.map(m => <option key={m.id} value={m.id}>{m.title}</option>)}
            </Select></div>
            <div><Label>Department</Label><Input value={assignForm.department} onChange={e => setAssignForm({ ...assignForm, department: e.target.value })} /></div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAssignModal(false)}>Cancel</Button>
            <Button onClick={assignModule}>Assign</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-6">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Total Users Trained</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{summary.total_users || 0}</div><p className="text-xs text-muted-foreground">{summary.active_users || 0} active this quarter</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Completion Rate</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-green-500">{summary.completion_rate || 0}%</div><p className="text-xs text-muted-foreground">modules completed</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Phishing Susceptibility</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{summary.phishing_rate || 0}%</div><p className="text-xs text-muted-foreground">clicked on simulated phish</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Avg Score</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{summary.avg_score || 0}%</div><p className="text-xs text-muted-foreground">assessment average</p></CardContent></Card>
      </div>

      <Tabs defaultValue="training_trend" className="mb-6">
        <TabsList><TabsTrigger value="training_trend">Training Trend</TabsTrigger><TabsTrigger value="dept_performance">Department Performance</TabsTrigger><TabsTrigger value="campaign_results">Campaign Results</TabsTrigger></TabsList>
        <TabsContent value="training_trend">
          <Card><CardHeader><CardTitle>Training Completion Trend (Last 30 Days)</CardTitle></CardHeader><CardContent>
            <div className="space-y-2">{summary.training_trend?.map?.((p: any, i: number) => (<div key={i} className="flex items-center justify-between"><span className="text-sm">{p.date}</span><div className="h-2 bg-green-500 rounded" style={{ width: `${(p.count / (summary.training_trend?.[0]?.count || 1)) * 100}%` }} /><span className="text-sm font-mono">{p.count}</span></div>))}</div>
          </CardContent></Card>
        </TabsContent>
        <TabsContent value="dept_performance">
          <Card><CardHeader><CardTitle>Department Training Performance</CardTitle></CardHeader><CardContent>
            <Table><TableHeader><TableRow><TableHead>Department</TableHead><TableHead>Completion</TableHead><TableHead>Avg Score</TableHead><TableHead>Phishing Rate</TableHead></TableRow></TableHeader><TableBody>
              {summary.dept_performance?.map?.((d: any, i: number) => (<TableRow key={i}><TableCell className="font-medium">{d.department}</TableCell><TableCell>{d.completion}%</TableCell><TableCell>{d.avg_score}%</TableCell><TableCell><Badge variant={d.phishing_rate < 10 ? 'default' : 'destructive'}>{d.phishing_rate}%</Badge></TableCell></TableRow>))}
              {(!summary.dept_performance || summary.dept_performance.length === 0) && <TableRow><TableCell colSpan={4} className="text-center text-muted-foreground">No department data available</TableCell></TableRow>}
            </TableBody></Table>
          </CardContent></Card>
        </TabsContent>
        <TabsContent value="campaign_results">
          <Card><CardHeader><CardTitle>Phishing Campaign Results</CardTitle></CardHeader><CardContent>
            <div className="space-y-2">{summary.campaign_results?.map?.((c: any, i: number) => (<div key={i} className="flex items-center justify-between p-2 border rounded"><div><span className="font-medium">{c.name}</span><span className="text-sm text-muted-foreground ml-2">{c.date}</span></div><span>{c.sent} sent, {c.clicked} clicked ({c.rate}%)</span></div>))}</div>
          </CardContent></Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};
