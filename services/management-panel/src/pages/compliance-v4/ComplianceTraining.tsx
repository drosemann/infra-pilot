import { useState, useEffect, useCallback } from 'react';
import { toast } from 'sonner';
import { apiClient } from '../../lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { GraduationCap, Search, Filter, Shield, CheckCircle, XCircle, RefreshCw, PlusCircle, BookOpen, Award, Clock, Users, BarChart3, FileText, Trophy, Star, Trash2, Edit } from 'lucide-react';

function ProgressBar({ value, max, label }: { value: number; max: number; label: string }) {
  const pct = max > 0 ? (value / max) * 100 : 0;
  const color = pct >= 80 ? 'bg-green-500' : pct >= 50 ? 'bg-yellow-500' : 'bg-red-500';
  return (
    <div><div className="flex items-center justify-between text-xs mb-1"><span className="text-slate-400">{label}</span><span className="text-white">{value}/{max}</span></div>
      <div className="w-full h-2 bg-slate-700 rounded"><div className={`${color} h-2 rounded transition-all`} style={{ width: `${pct}%` }} /></div></div>
  );
}

function AssignTrainingForm({ onCreated }: { onCreated: () => void }) {
  const [moduleId, setModuleId] = useState('');
  const [userIds, setUserIds] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (!moduleId || !userIds) { toast.error('Module ID and user IDs required'); return; }
    setSubmitting(true);
    try {
      const ids = userIds.split(',').map((s: string) => s.trim());
      await apiClient.post('/api/v1/compliance/training/assign', { module_id: moduleId, user_ids: ids });
      toast.success(`Assigned to ${ids.length} users`);
      onCreated();
    } catch { toast.error('Assignment failed'); }
    setSubmitting(false);
  };

  return (
    <Card><CardHeader><CardTitle className="flex items-center gap-2"><PlusCircle className="h-4 w-4 text-green-400" /> Assign Training</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        <Input className="bg-slate-800 border-slate-700 text-white" placeholder="Module ID" value={moduleId} onChange={(e) => setModuleId(e.target.value)} />
        <Input className="bg-slate-800 border-slate-700 text-white" placeholder="User IDs (comma-separated)" value={userIds} onChange={(e) => setUserIds(e.target.value)} />
        <Button onClick={handleSubmit} disabled={submitting} className="bg-blue-600 hover:bg-blue-700 w-full">Assign</Button>
      </CardContent></Card>
  );
}

function ModuleDetailCard({ module }: { module: any }) {
  if (!module) return null;
  return (
    <Card><CardHeader><CardTitle className="text-sm">{module.title || module.name}</CardTitle></CardHeader>
      <CardContent className="space-y-2">
        <div className="flex items-center justify-between"><span className="text-xs text-slate-400">Category</span><Badge variant="outline" className="text-xs">{module.category}</Badge></div>
        <div className="flex items-center justify-between"><span className="text-xs text-slate-400">Duration</span><span className="text-white text-sm">{module.duration_minutes || module.duration}</span></div>
        <ProgressBar value={module.completed_count || 0} max={module.total_enrolled || 1} label="Completion" />
      </CardContent></Card>
  );
}

function CertificateCard({ certs }: { certs: any[] }) {
  if (!certs?.length) return <p className="text-sm text-slate-400">No certificates issued yet</p>;
  return (
    <div className="space-y-2">{certs.map((c: any, i: number) => (
      <div key={i} className="flex items-center justify-between p-3 bg-slate-800 rounded border border-slate-700">
        <div><p className="text-sm text-white font-medium">{c.module_name || c.title}</p><p className="text-xs text-slate-400">Issued: {c.issued_at ? new Date(c.issued_at).toLocaleDateString() : 'N/A'} | Expires: {c.expires_at ? new Date(c.expires_at).toLocaleDateString() : 'N/A'}</p></div>
        <div className="flex items-center gap-2"><Trophy className={`h-4 w-4 ${c.status === 'active' ? 'text-yellow-400' : 'text-slate-500'}`} /><Badge className={c.status === 'active' ? 'bg-green-600' : 'bg-slate-600'}>{c.status}</Badge></div>
      </div>
    ))}</div>
  );
}

function UserProgressCard({ progress }: { progress: any }) {
  if (!progress) return null;
  return (
    <Card><CardHeader><CardTitle className="flex items-center gap-2 text-sm"><BarChart3 className="h-4 w-4 text-blue-400" /> User Progress Overview</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-center justify-between"><span className="text-xs text-slate-400">Total Users</span><span className="text-white text-sm font-bold">{progress.total_users || 0}</span></div>
        <div className="flex items-center justify-between"><span className="text-xs text-slate-400">Active Learners</span><span className="text-white text-sm font-bold">{progress.active_users || 0}</span></div>
        <div className="flex items-center justify-between"><span className="text-xs text-slate-400">Certified</span><span className="text-white text-sm font-bold">{progress.certified_users || 0}</span></div>
        <div className="flex items-center justify-between"><span className="text-xs text-slate-400">Avg Completion</span><span className="text-white text-sm font-bold">{progress.avg_completion_pct || 0}%</span></div>
        <div className="w-full h-2 bg-slate-700 rounded overflow-hidden"><div className="h-full bg-blue-500 rounded transition-all" style={{ width: `${progress.avg_completion_pct || 0}%` }} /></div>
      </CardContent></Card>
  );
}

export default function ComplianceTrainingPage() {
  const [modules, setModules] = useState<any[]>([]);
  const [assignments, setAssignments] = useState<any[]>([]);
  const [certificates, setCertificates] = useState<any[]>([]);
  const [userProgress, setUserProgress] = useState<any>(null);
  const [stats, setStats] = useState<any>(null);
  const [tab, setTab] = useState<'modules' | 'assignments' | 'certificates' | 'progress'>('modules');
  const [query, setQuery] = useState('');
  const [filterCategory, setFilterCategory] = useState('');
  const [showAssign, setShowAssign] = useState(false);
  const [selectedModule, setSelectedModule] = useState<any>(null);

  const fetchData = useCallback(() => {
    apiClient.get('/api/v1/compliance/training/modules').then(setModules).catch(() => {});
    apiClient.get('/api/v1/compliance/training/assignments').then(setAssignments).catch(() => {});
    apiClient.get('/api/v1/compliance/training/certificates').then(setCertificates).catch(() => {});
    apiClient.get('/api/v1/compliance/training/progress').then(setUserProgress).catch(() => {});
    apiClient.get('/api/v1/compliance/training/stats').then(setStats).catch(() => {});
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const filteredModules = modules.filter((m: any) => {
    if (query && !m.title?.toLowerCase().includes(query.toLowerCase()) && !m.module_id?.toLowerCase().includes(query.toLowerCase())) return false;
    if (filterCategory && m.category !== filterCategory) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div><h1 className="text-3xl font-bold text-white mb-2">Compliance Training</h1><p className="text-slate-400">Manage compliance training modules, track certifications, and assign courses</p></div>
        <div className="flex gap-2">
          <Button onClick={fetchData} variant="outline" className="text-slate-400"><RefreshCw className="mr-2 h-4 w-4" /> Refresh</Button>
          <Button onClick={() => setShowAssign(!showAssign)} className="bg-blue-600 hover:bg-blue-700"><PlusCircle className="mr-2 h-4 w-4" /> Assign</Button>
        </div>
      </div>
      {stats && (
        <div className="grid grid-cols-4 gap-4">
          <Card><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Modules</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-white">{stats.total_modules}</div></CardContent></Card>
          <Card><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Enrolled</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-white">{stats.total_enrolled}</div></CardContent></Card>
          <Card><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Completed</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-green-400">{stats.completed_count}</div></CardContent></Card>
          <Card><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Avg Score</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-blue-400">{stats.average_score}%</div></CardContent></Card>
        </div>
      )}
      <div className="flex space-x-2 border-b border-slate-700 pb-2">
        <Button variant={tab === 'modules' ? 'default' : 'ghost'} onClick={() => setTab('modules')}><BookOpen className="mr-2 h-4 w-4" /> Modules</Button>
        <Button variant={tab === 'assignments' ? 'default' : 'ghost'} onClick={() => setTab('assignments')}><Users className="mr-2 h-4 w-4" /> Assignments</Button>
        <Button variant={tab === 'certificates' ? 'default' : 'ghost'} onClick={() => setTab('certificates')}><Award className="mr-2 h-4 w-4" /> Certificates</Button>
        <Button variant={tab === 'progress' ? 'default' : 'ghost'} onClick={() => setTab('progress')}><BarChart3 className="mr-2 h-4 w-4" /> Progress</Button>
      </div>
      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2">
          {tab === 'modules' && (
            <Card><CardHeader><CardTitle>Training Modules ({filteredModules.length})</CardTitle></CardHeader>
              <CardContent>
                <div className="flex gap-3 items-center mb-4">
                  <div className="relative flex-1"><Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                    <Input className="pl-9 bg-slate-800 border-slate-700 text-white" placeholder="Search modules..." value={query} onChange={(e) => setQuery(e.target.value)} /></div>
                  <select className="bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-sm text-white" value={filterCategory} onChange={(e) => setFilterCategory(e.target.value)}>
                    <option value="">All</option><option value="security_awareness">Security Awareness</option><option value="compliance">Compliance</option><option value="data_protection">Data Protection</option><option value="incident_response">Incident Response</option>
                  </select>
                </div>
                <Table><TableHeader><TableRow><TableHead className="text-slate-400">ID</TableHead><TableHead className="text-slate-400">Title</TableHead><TableHead className="text-slate-400">Category</TableHead><TableHead className="text-slate-400">Duration</TableHead><TableHead className="text-slate-400">Enrolled</TableHead><TableHead className="text-slate-400">Completed</TableHead></TableRow></TableHeader>
                  <TableBody>{filteredModules.map((m: any) => (
                    <TableRow key={m.module_id || m.id}>
                      <TableCell className="font-mono text-xs text-white cursor-pointer hover:text-blue-400" onClick={() => setSelectedModule(m)}>{m.module_id || m.id}</TableCell>
                      <TableCell className="text-white">{m.title || m.name}</TableCell>
                      <TableCell><Badge variant="outline" className="text-xs">{m.category}</Badge></TableCell>
                      <TableCell className="text-white text-sm">{m.duration_minutes || m.duration}</TableCell>
                      <TableCell className="text-white text-sm">{m.total_enrolled || 0}</TableCell>
                      <TableCell className="text-white text-sm">{m.completed_count || 0}</TableCell>
                    </TableRow>
                  ))}</TableBody></Table>
              </CardContent></Card>
          )}
          {tab === 'assignments' && (
            <Card><CardHeader><CardTitle>User Assignments ({assignments.length})</CardTitle></CardHeader>
              <CardContent>
                <Table><TableHeader><TableRow><TableHead className="text-slate-400">ID</TableHead><TableHead className="text-slate-400">Module</TableHead><TableHead className="text-slate-400">User</TableHead><TableHead className="text-slate-400">Status</TableHead><TableHead className="text-slate-400">Score</TableHead><TableHead className="text-slate-400">Due Date</TableHead></TableRow></TableHeader>
                  <TableBody>{assignments.map((a: any) => (
                    <TableRow key={a.assignment_id || a.id}>
                      <TableCell className="font-mono text-xs text-white">{a.assignment_id || a.id}</TableCell>
                      <TableCell className="font-mono text-xs text-slate-400">{a.module_id}</TableCell>
                      <TableCell className="text-white text-sm">{a.user_id}</TableCell>
                      <TableCell><Badge className={a.status === 'completed' ? 'bg-green-600' : a.status === 'in_progress' ? 'bg-yellow-600' : 'bg-slate-600'}>{a.status}</Badge></TableCell>
                      <TableCell className="text-white text-sm">{a.score ?? '-'}</TableCell>
                      <TableCell className="text-slate-400 text-sm">{a.due_date ? new Date(a.due_date).toLocaleDateString() : 'N/A'}</TableCell>
                    </TableRow>
                  ))}</TableBody></Table>
              </CardContent></Card>
          )}
          {tab === 'certificates' && (
            <Card><CardHeader><CardTitle className="flex items-center gap-2"><Award className="h-4 w-4 text-yellow-400" /> Active Certificates ({certificates.length})</CardTitle></CardHeader>
              <CardContent><CertificateCard certs={certificates} /></CardContent></Card>
          )}
          {tab === 'progress' && (
            <Card><CardHeader><CardTitle className="flex items-center gap-2"><BarChart3 className="h-4 w-4 text-blue-400" /> Training Effectiveness</CardTitle></CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div className="p-3 bg-slate-800 rounded text-center"><BarChart3 className="h-5 w-5 text-green-400 mx-auto mb-1" /><p className="text-xs text-slate-400">Completion Rate</p><p className="text-lg font-bold text-white">{stats?.completion_rate || 0}%</p></div>
                  <div className="p-3 bg-slate-800 rounded text-center"><Star className="h-5 w-5 text-yellow-400 mx-auto mb-1" /><p className="text-xs text-slate-400">Avg Score</p><p className="text-lg font-bold text-white">{stats?.average_score || 0}%</p></div>
                </div>
                {stats?.category_breakdown && Object.entries(stats.category_breakdown).map(([cat, data]: [string, any]) => (
                  <div key={cat} className="mb-2"><ProgressBar value={data.completed || 0} max={data.total || 1} label={cat} /></div>
                ))}
              </CardContent></Card>
          )}
        </div>
        <div className="space-y-4">
          {showAssign && <AssignTrainingForm onCreated={fetchData} />}
          {selectedModule && <ModuleDetailCard module={selectedModule} />}
        </div>
      </div>
    </div>
  );
}
import React from "react";

interface compliance_trainingAction {
  id: string;
  type: string;
  status: string;
  ts: string;
}

const compliance_trainingActions: React.FC<{}> = () => {
  const [items, setItems] = React.useState<compliance_trainingAction[]>([]);
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
      <h2 className="text-xl font-bold mb-4">compliance_training Actions</h2>
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
export default compliance_trainingActions;
