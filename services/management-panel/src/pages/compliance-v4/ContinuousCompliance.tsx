import { useState, useEffect, useCallback } from 'react';
import { toast } from 'sonner';
import { apiClient } from '../../lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { BarChart3, Bell, Search, Filter, Shield, CheckCircle, XCircle, RefreshCw, PlusCircle, Activity, TrendingUp, TrendingDown, AlertTriangle, Clock, FileText, GitBranch, Eye, Settings } from 'lucide-react';

function DriftBadge({ score }: { score: number }) {
  if (score <= 10) return <Badge className="bg-green-600">Stable</Badge>;
  if (score <= 30) return <Badge className="bg-yellow-600">Minor Drift</Badge>;
  if (score <= 60) return <Badge className="bg-orange-600">Moderate Drift</Badge>;
  return <Badge className="bg-red-600">Critical Drift</Badge>;
}

function RemediationPlanForm({ onCreated }: { onCreated: () => void }) {
  const [findingId, setFindingId] = useState('');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState('medium');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (!findingId || !title) { toast.error('Finding ID and title required'); return; }
    setSubmitting(true);
    try {
      await apiClient.post('/api/v1/compliance/remediation/plans', { finding_id: findingId, title, description, priority, status: 'draft' });
      toast.success('Remediation plan created');
      onCreated();
    } catch { toast.error('Failed to create plan'); }
    setSubmitting(false);
  };

  return (
    <Card><CardHeader><CardTitle className="flex items-center gap-2"><PlusCircle className="h-4 w-4 text-green-400" /> Create Remediation Plan</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        <Input className="bg-slate-800 border-slate-700 text-white" placeholder="Finding ID" value={findingId} onChange={(e) => setFindingId(e.target.value)} />
        <Input className="bg-slate-800 border-slate-700 text-white" placeholder="Title" value={title} onChange={(e) => setTitle(e.target.value)} />
        <Input className="bg-slate-800 border-slate-700 text-white" placeholder="Description" value={description} onChange={(e) => setDescription(e.target.value)} />
        <select className="w-full bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-sm text-white" value={priority} onChange={(e) => setPriority(e.target.value)}>
          <option value="critical">Critical</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option>
        </select>
        <Button onClick={handleSubmit} disabled={submitting} className="bg-blue-600 hover:bg-blue-700 w-full">Create Plan</Button>
      </CardContent></Card>
  );
}

function DriftChartCard({ drift }: { drift: any }) {
  if (!drift) return null;
  return (
    <Card><CardHeader><CardTitle className="flex items-center gap-2"><Activity className="h-4 w-4 text-blue-400" /> Drift Analysis</CardTitle></CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div className="flex items-center justify-between"><span className="text-sm text-slate-400">Current Drift</span><span className="text-white font-bold">{drift.drift_percentage}%</span></div>
          <div className="flex items-center justify-between"><span className="text-sm text-slate-400">Trend</span><span className="flex items-center gap-1">{drift.trend === 'increasing' ? <TrendingUp className="h-4 w-4 text-red-400" /> : drift.trend === 'decreasing' ? <TrendingDown className="h-4 w-4 text-green-400" /> : <Activity className="h-4 w-4 text-yellow-400" />}{drift.trend || 'stable'}</span></div>
          <div className="flex items-center justify-between"><span className="text-sm text-slate-400">Checkpoints</span><span className="text-white">{drift.checkpoints_count}</span></div>
          <div className="flex items-center justify-between"><span className="text-sm text-slate-400">Last Assessment</span><span className="text-white">{drift.last_assessment ? new Date(drift.last_assessment).toLocaleDateString() : 'N/A'}</span></div>
        </div>
      </CardContent></Card>
  );
}

function ScheduleCard({ schedule }: { schedule: any }) {
  if (!schedule) return null;
  return (
    <Card><CardHeader><CardTitle className="flex items-center gap-2"><Clock className="h-4 w-4 text-purple-400" /> Scan Schedule</CardTitle></CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div className="flex items-center justify-between"><span className="text-sm text-slate-400">Interval</span><span className="text-white">{schedule.interval || 'N/A'}</span></div>
          <div className="flex items-center justify-between"><span className="text-sm text-slate-400">Last Run</span><span className="text-white">{schedule.last_run ? new Date(schedule.last_run).toLocaleString() : 'N/A'}</span></div>
          <div className="flex items-center justify-between"><span className="text-sm text-slate-400">Next Run</span><span className="text-white">{schedule.next_run ? new Date(schedule.next_run).toLocaleString() : 'N/A'}</span></div>
          <div className="flex items-center justify-between"><span className="text-sm text-slate-400">Status</span><Badge className={schedule.enabled ? 'bg-green-600' : 'bg-slate-600'}>{schedule.enabled ? 'Active' : 'Paused'}</Badge></div>
        </div>
      </CardContent></Card>
  );
}

export default function ContinuousCompliancePage() {
  const [findings, setFindings] = useState<any[]>([]);
  const [remediations, setRemediations] = useState<any[]>([]);
  const [reports, setReports] = useState<any[]>([]);
  const [drift, setDrift] = useState<any>(null);
  const [schedule, setSchedule] = useState<any>(null);
  const [stats, setStats] = useState<any>(null);
  const [tab, setTab] = useState<'findings' | 'remediations' | 'reports' | 'history'>('findings');
  const [query, setQuery] = useState('');
  const [filterSeverity, setFilterSeverity] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [selectedFinding, setSelectedFinding] = useState<any>(null);

  const fetchData = useCallback(() => {
    apiClient.get('/api/v1/compliance/findings').then(setFindings).catch(() => {});
    apiClient.get('/api/v1/compliance/remediation/plans').then(setRemediations).catch(() => {});
    apiClient.get('/api/v1/compliance/continuous/reports').then(setReports).catch(() => {});
    apiClient.get('/api/v1/compliance/continuous/drift').then(setDrift).catch(() => {});
    apiClient.get('/api/v1/compliance/continuous/schedule').then(setSchedule).catch(() => {});
    apiClient.get('/api/v1/compliance/continuous/stats').then(setStats).catch(() => {});
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const filteredFindings = findings.filter((f: any) => {
    if (query && !f.title?.toLowerCase().includes(query.toLowerCase()) && !f.finding_id?.toLowerCase().includes(query.toLowerCase())) return false;
    if (filterSeverity && f.severity !== filterSeverity) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div><h1 className="text-3xl font-bold text-white mb-2">Continuous Compliance</h1><p className="text-slate-400">Ongoing compliance monitoring, drift detection, and remediation tracking</p></div>
        <div className="flex gap-2">
          <Button onClick={fetchData} variant="outline" className="text-slate-400"><RefreshCw className="mr-2 h-4 w-4" /> Refresh</Button>
          <Button onClick={() => setShowCreate(!showCreate)} className="bg-blue-600 hover:bg-blue-700"><PlusCircle className="mr-2 h-4 w-4" /> Create Plan</Button>
        </div>
      </div>
      {stats && (
        <div className="grid grid-cols-4 gap-4">
          <Card><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Open Findings</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-white">{stats.open_findings}</div></CardContent></Card>
          <Card><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Remediated</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-green-400">{stats.remediated_count}</div></CardContent></Card>
          <Card><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Drift Score</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-yellow-400">{stats.drift_score}%</div></CardContent></Card>
          <Card><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Compliance %</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-blue-400">{stats.compliance_percentage}%</div></CardContent></Card>
        </div>
      )}
      <div className="flex space-x-2 border-b border-slate-700 pb-2">
        <Button variant={tab === 'findings' ? 'default' : 'ghost'} onClick={() => setTab('findings')}><AlertTriangle className="mr-2 h-4 w-4" /> Findings</Button>
        <Button variant={tab === 'remediations' ? 'default' : 'ghost'} onClick={() => setTab('remediations')}><BarChart3 className="mr-2 h-4 w-4" /> Remediation Plans</Button>
        <Button variant={tab === 'reports' ? 'default' : 'ghost'} onClick={() => setTab('reports')}><FileText className="mr-2 h-4 w-4" /> Reports</Button>
        <Button variant={tab === 'history' ? 'default' : 'ghost'} onClick={() => setTab('history')}><GitBranch className="mr-2 h-4 w-4" /> History</Button>
      </div>
      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2">
          {tab === 'findings' && (
            <Card><CardHeader><CardTitle>Compliance Findings ({filteredFindings.length})</CardTitle></CardHeader>
              <CardContent>
                <div className="flex gap-3 items-center mb-4">
                  <div className="relative flex-1"><Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                    <Input className="pl-9 bg-slate-800 border-slate-700 text-white" placeholder="Search findings..." value={query} onChange={(e) => setQuery(e.target.value)} /></div>
                  <select className="bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-sm text-white" value={filterSeverity} onChange={(e) => setFilterSeverity(e.target.value)}>
                    <option value="">All</option><option value="critical">Critical</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option>
                  </select>
                </div>
                <Table><TableHeader><TableRow><TableHead className="text-slate-400">ID</TableHead><TableHead className="text-slate-400">Title</TableHead><TableHead className="text-slate-400">Severity</TableHead><TableHead className="text-slate-400">Source</TableHead><TableHead className="text-slate-400">Status</TableHead><TableHead className="text-slate-400">Created</TableHead><TableHead className="text-slate-400">Actions</TableHead></TableRow></TableHeader>
                  <TableBody>{filteredFindings.map((f: any) => (
                    <TableRow key={f.finding_id}>
                      <TableCell className="font-mono text-xs text-white">{f.finding_id}</TableCell>
                      <TableCell className="text-white">{f.title}</TableCell>
                      <TableCell><Badge className={f.severity === 'critical' ? 'bg-red-600' : f.severity === 'high' ? 'bg-orange-600' : f.severity === 'medium' ? 'bg-yellow-600' : 'bg-green-600'}>{f.severity}</Badge></TableCell>
                      <TableCell className="text-slate-400 text-sm">{f.source}</TableCell>
                      <TableCell><Badge className={f.status === 'open' ? 'bg-red-600' : f.status === 'remediated' ? 'bg-green-600' : 'bg-blue-600'}>{f.status}</Badge></TableCell>
                      <TableCell className="text-slate-400 text-sm">{f.created_at ? new Date(f.created_at).toLocaleDateString() : 'N/A'}</TableCell>
                      <TableCell><Button size="sm" variant="ghost" onClick={() => setSelectedFinding(f)}><Eye className="h-3 w-3 text-blue-400" /></Button></TableCell>
                    </TableRow>
                  ))}</TableBody></Table>
              </CardContent></Card>
          )}
          {tab === 'remediations' && (
            <Card><CardHeader><CardTitle>Remediation Plans ({remediations.length})</CardTitle></CardHeader>
              <CardContent>
                <Table><TableHeader><TableRow><TableHead className="text-slate-400">ID</TableHead><TableHead className="text-slate-400">Title</TableHead><TableHead className="text-slate-400">Finding</TableHead><TableHead className="text-slate-400">Priority</TableHead><TableHead className="text-slate-400">Status</TableHead><TableHead className="text-slate-400">Actions</TableHead></TableRow></TableHeader>
                  <TableBody>{remediations.map((r: any) => (
                    <TableRow key={r.plan_id}>
                      <TableCell className="font-mono text-xs text-white">{r.plan_id}</TableCell>
                      <TableCell className="text-white">{r.title}</TableCell>
                      <TableCell className="font-mono text-xs text-slate-400">{r.finding_id}</TableCell>
                      <TableCell><Badge className={r.priority === 'critical' ? 'bg-red-600' : r.priority === 'high' ? 'bg-orange-600' : r.priority === 'medium' ? 'bg-yellow-600' : 'bg-blue-600'}>{r.priority}</Badge></TableCell>
                      <TableCell><Badge className={r.status === 'completed' ? 'bg-green-600' : r.status === 'in_progress' ? 'bg-blue-600' : 'bg-slate-600'}>{r.status}</Badge></TableCell>
                      <TableCell><Button size="sm" variant="ghost" className="text-blue-400">Track</Button></TableCell>
                    </TableRow>
                  ))}</TableBody></Table>
              </CardContent></Card>
          )}
          {tab === 'reports' && (
            <Card><CardHeader><CardTitle className="flex items-center gap-2"><FileText className="h-4 w-4 text-blue-400" /> Compliance Reports ({reports.length})</CardTitle></CardHeader>
              <CardContent>
                <Table><TableHeader><TableRow><TableHead className="text-slate-400">Report</TableHead><TableHead className="text-slate-400">Period</TableHead><TableHead className="text-slate-400">Score</TableHead><TableHead className="text-slate-400">Findings</TableHead><TableHead className="text-slate-400">Status</TableHead><TableHead className="text-slate-400">Actions</TableHead></TableRow></TableHeader>
                  <TableBody>{reports.map((r: any, i: number) => (
                    <TableRow key={r.report_id || i}>
                      <TableCell className="text-white text-sm">{r.title || `Compliance Report #${i + 1}`}</TableCell>
                      <TableCell className="text-xs text-slate-400">{r.period_start?.slice(0, 10)} - {r.period_end?.slice(0, 10)}</TableCell>
                      <TableCell><Badge className={r.score >= 80 ? 'bg-green-600' : r.score >= 50 ? 'bg-yellow-600' : 'bg-red-600'}>{r.score}%</Badge></TableCell>
                      <TableCell className="text-white text-sm">{r.finding_count || 0}</TableCell>
                      <TableCell><Badge className={r.status === 'generated' ? 'bg-green-600' : 'bg-blue-600'}>{r.status}</Badge></TableCell>
                      <TableCell><Button size="sm" variant="ghost" className="text-blue-400"><Eye className="mr-1 h-3 w-3" /> View</Button></TableCell>
                    </TableRow>
                  ))}</TableBody></Table>
              </CardContent></Card>
          )}
          {tab === 'history' && (
            <Card><CardHeader><CardTitle className="flex items-center gap-2"><GitBranch className="h-4 w-4 text-purple-400" /> Compliance History</CardTitle></CardHeader>
              <CardContent>
                <p className="text-sm text-slate-400 mb-4">Track changes and historical compliance events over time.</p>
                <div className="space-y-2">{drift?.history?.map((h: any, i: number) => (
                  <div key={i} className="flex items-center justify-between p-2 bg-slate-800 rounded">
                    <div><p className="text-xs text-white">{h.event || h.type}</p><p className="text-xs text-slate-400">{h.timestamp ? new Date(h.timestamp).toLocaleString() : 'N/A'}</p></div>
                    <Badge className={h.severity === 'critical' ? 'bg-red-600' : h.severity === 'high' ? 'bg-orange-600' : 'bg-yellow-600'}>{h.severity || 'info'}</Badge>
                  </div>
                )) || <p className="text-xs text-slate-500">No history entries available</p>}</div>
              </CardContent></Card>
          )}
        </div>
        <div className="space-y-4">
          {showCreate && <RemediationPlanForm onCreated={fetchData} />}
          {drift && <DriftChartCard drift={drift} />}
          {schedule && <ScheduleCard schedule={schedule} />}
          {selectedFinding && (
            <Card><CardHeader><CardTitle className="text-sm">Finding Detail</CardTitle></CardHeader>
              <CardContent className="space-y-2">
                <div className="flex justify-between"><span className="text-xs text-slate-400">ID</span><span className="text-xs font-mono text-white">{selectedFinding.finding_id}</span></div>
                <div className="flex justify-between"><span className="text-xs text-slate-400">Title</span><span className="text-xs text-white">{selectedFinding.title}</span></div>
                <div className="flex justify-between"><span className="text-xs text-slate-400">Severity</span><Badge className={selectedFinding.severity === 'critical' ? 'bg-red-600' : selectedFinding.severity === 'high' ? 'bg-orange-600' : 'bg-yellow-600'}>{selectedFinding.severity}</Badge></div>
                <div className="flex justify-between"><span className="text-xs text-slate-400">Source</span><span className="text-xs text-white">{selectedFinding.source}</span></div>
                <div className="flex justify-between"><span className="text-xs text-slate-400">Status</span><Badge className={selectedFinding.status === 'open' ? 'bg-red-600' : 'bg-green-600'}>{selectedFinding.status}</Badge></div>
                <Button size="sm" className="w-full mt-2 bg-blue-600 hover:bg-blue-700" onClick={() => setSelectedFinding(null)}><Eye className="mr-2 h-3 w-3" /> Close</Button>
              </CardContent></Card>
          )}
        </div>
      </div>
    </div>
  );
}
import React from "react";

interface continuous_complianceAction {
  id: string;
  type: string;
  status: string;
  ts: string;
}

const continuous_complianceActions: React.FC<{}> = () => {
  const [items, setItems] = React.useState<continuous_complianceAction[]>([]);
  const [loading, setLoading] = React.useState(false);
  React.useEffect(() => {
    setLoading(true);
    setItems([
      { id: "1", type: "create", status: "done", ts: new Date().toISOString() },
      { id: "2", type: "update", status: "pending", ts: new Date().toISOString() },
    ]);
    setLoading(false);
  }, []);
  if (loading) return <div>Loading...</div>;
  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-4">continuous_compliance Actions</h2>
      <div className="grid gap-4">
        {items.map((a) => (
          <div key={a.id} className="border rounded p-3 shadow-sm">
            <span className="font-medium">{a.type}</span>
            <span className={"ml-2 px-2 py-1 rounded " + (a.status === "done" ? "bg-green-100" : "bg-yellow-100")}>{a.status}</span>
          </div>
        ))}
      </div>
    </div>
  );
};
export default continuous_complianceActions;
