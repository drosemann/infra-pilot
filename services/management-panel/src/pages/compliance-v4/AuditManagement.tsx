import { useState, useEffect, useCallback } from 'react';
import { toast } from 'sonner';
import { apiClient } from '../../lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Calendar, ClipboardList, Users, Clock, Search, ChevronDown, ChevronUp, CalendarDays, AlertTriangle, ListChecks, Workflow, ArrowUpDown, PlusCircle, FileText, Bell, RefreshCw } from 'lucide-react';

function AuditFilters({ filters, onChange }: { filters: any; onChange: (f: any) => void }) {
  return (
    <div className="flex gap-3 items-center mb-4">
      <div className="relative flex-1 max-w-xs">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
        <Input className="pl-9 bg-slate-800 border-slate-700 text-white" placeholder="Search audits..." value={filters.query || ''}
          onChange={(e) => onChange({ ...filters, query: e.target.value })} />
      </div>
      <select className="bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-sm text-white"
        value={filters.status || ''} onChange={(e) => onChange({ ...filters, status: e.target.value })}>
        <option value="">All Status</option>
        <option value="scheduled">Scheduled</option>
        <option value="in_progress">In Progress</option>
        <option value="completed">Completed</option>
      </select>
      <select className="bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-sm text-white"
        value={filters.type || ''} onChange={(e) => onChange({ ...filters, type: e.target.value })}>
        <option value="">All Types</option>
        <option value="internal">Internal</option>
        <option value="external">External</option>
        <option value="regulatory">Regulatory</option>
      </select>
    </div>
  );
}

function UpcomingAuditsCard({ audits }: { audits: any[] }) {
  const upcoming = audits.filter((a: any) => a.status === 'scheduled').slice(0, 5);
  return (
    <Card><CardHeader><CardTitle className="flex items-center gap-2"><CalendarDays className="h-4 w-4 text-blue-400" /> Upcoming Audits</CardTitle></CardHeader>
      <CardContent>{upcoming.length === 0 ? <p className="text-slate-400 text-sm">No upcoming audits</p> : (
        <div className="space-y-2">{upcoming.map((a: any) => (
          <div key={a.audit_id} className="flex items-center justify-between p-2 bg-slate-800 rounded">
            <div><p className="text-sm text-white">{a.framework}</p><p className="text-xs text-slate-400">{new Date(a.scheduled_date).toLocaleDateString()}</p></div>
            <Badge variant="outline" className="text-xs">{a.audit_type}</Badge>
          </div>
        ))}</div>
      )}</CardContent></Card>
  );
}

function AuditMetricsGrid({ stats }: { stats: any }) {
  const metrics = [
    { label: 'Scheduled', value: stats.scheduled_audits, icon: Calendar, color: 'text-blue-400' },
    { label: 'In Progress', value: stats.in_progress_audits, icon: Clock, color: 'text-yellow-400' },
    { label: 'Completed', value: stats.completed_audits, icon: ClipboardList, color: 'text-green-400' },
    { label: 'Customer Rights', value: stats.customer_rights_count, icon: Users, color: 'text-purple-400' },
  ];
  return (
    <div className="grid grid-cols-4 gap-4">
      {metrics.map((m) => (
        <Card key={m.label}><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">{m.label}</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold text-white flex items-center"><m.icon className={`mr-2 h-5 w-5 ${m.color}`} />{m.value ?? 0}</div></CardContent></Card>
      ))}
    </div>
  );
}

function AuditNotificationsPanel({ notifications }: { notifications: any[] }) {
  return (
    <Card><CardHeader><CardTitle className="flex items-center gap-2"><Bell className="h-4 w-4 text-yellow-400" /> Notifications ({notifications.length})</CardTitle></CardHeader>
      <CardContent>{notifications.length === 0 ? <p className="text-slate-400 text-sm">No notifications</p> : (
        <div className="space-y-2 max-h-60 overflow-y-auto">{notifications.map((n: any, i: number) => (
          <div key={i} className="flex items-start gap-2 p-2 bg-slate-800 rounded">
            <AlertTriangle className="h-4 w-4 text-yellow-400 mt-0.5" />
            <div><p className="text-sm text-white">{n.message}</p><p className="text-xs text-slate-400">{n.timestamp}</p></div>
          </div>
        ))}</div>
      )}</CardContent></Card>
  );
}

function WorkflowActionDialog({ scheduleId, onClose, onExecute }: { scheduleId: string; onClose: () => void; onExecute: (id: string, action: string) => void }) {
  const actions = ['start', 'complete', 'cancel', 'reschedule'];
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-slate-800 rounded-lg p-6 w-96 border border-slate-700" onClick={(e) => e.stopPropagation()}>
        <h3 className="text-lg font-bold text-white mb-4">Workflow Action</h3>
        <p className="text-sm text-slate-400 mb-4">Schedule: {scheduleId}</p>
        <div className="space-y-2">{actions.map((action) => (
          <Button key={action} variant="outline" className="w-full justify-start text-left capitalize"
            onClick={() => { onExecute(scheduleId, action); onClose(); }}>
            <Workflow className="mr-2 h-4 w-4" /> {action} audit
          </Button>
        ))}</div>
        <Button variant="ghost" className="w-full mt-4 text-slate-400" onClick={onClose}>Cancel</Button>
      </div>
    </div>
  );
}

function AuditEvidenceSection({ scheduleId, onClose }: { scheduleId: string; onClose: () => void }) {
  const [evidence, setEvidence] = useState<any[]>([]);
  useEffect(() => {
    apiClient.get(`/api/v1/compliance/audit/evidence?schedule_id=${scheduleId}`).then(setEvidence).catch(() => setEvidence([]));
  }, [scheduleId]);

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-slate-800 rounded-lg p-6 w-[600px] max-h-[80vh] overflow-y-auto border border-slate-700" onClick={(e) => e.stopPropagation()}>
        <h3 className="text-lg font-bold text-white mb-4">Audit Evidence: {scheduleId}</h3>
        {evidence.length === 0 ? <p className="text-slate-400">Loading evidence...</p> : (
          <Table><TableHeader><TableRow><TableHead className="text-slate-400">Type</TableHead><TableHead className="text-slate-400">Count</TableHead><TableHead className="text-slate-400">Status</TableHead></TableRow></TableHeader>
            <TableBody>{evidence.map((e: any, i: number) => (
              <TableRow key={i}><TableCell className="text-white">{e.type}</TableCell><TableCell className="text-white">{e.count}</TableCell><TableCell><Badge variant="outline">{e.status}</Badge></TableCell></TableRow>
            ))}</TableBody></Table>
        )}
        <Button variant="ghost" className="w-full mt-4 text-slate-400" onClick={onClose}>Close</Button>
      </div>
    </div>
  );
}

function AuditTemplatesPanel({ onSelect }: { onSelect: (t: any) => void }) {
  const [templates, setTemplates] = useState<any[]>([]);
  useEffect(() => {
    apiClient.get('/api/v1/compliance/audit/templates').then(setTemplates).catch(() => {});
  }, []);
  return (
    <Card><CardHeader><CardTitle className="flex items-center gap-2"><FileText className="h-4 w-4 text-blue-400" /> Audit Templates</CardTitle></CardHeader>
      <CardContent>
        <Table><TableHeader><TableRow><TableHead className="text-slate-400">Name</TableHead><TableHead className="text-slate-400">Framework</TableHead><TableHead className="text-slate-400">Duration</TableHead><TableHead className="text-slate-400">Actions</TableHead></TableRow></TableHeader>
          <TableBody>{templates.map((t: any) => (
            <TableRow key={t.template_id}><TableCell className="text-white">{t.name}</TableCell><TableCell><Badge variant="outline">{t.framework}</Badge></TableCell><TableCell className="text-slate-400">{t.default_duration_days}d</TableCell>
              <TableCell><Button size="sm" variant="ghost" onClick={() => onSelect(t)}><PlusCircle className="h-4 w-4" /></Button></TableCell></TableRow>
          ))}</TableBody></Table>
      </CardContent></Card>
  );
}

export default function AuditManagementPage() {
  const [audits, setAudits] = useState<any[]>([]);
  const [rights, setRights] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [filters, setFilters] = useState<any>({});
  const [sortBy, setSortBy] = useState<string>('scheduled_date');
  const [sortAsc, setSortAsc] = useState(false);
  const [workflowTarget, setWorkflowTarget] = useState<string | null>(null);
  const [evidenceTarget, setEvidenceTarget] = useState<string | null>(null);
  const [tab, setTab] = useState<'schedule' | 'rights' | 'templates'>('schedule');

  const fetchData = useCallback(() => {
    apiClient.get('/api/v1/compliance/audit/schedules').then(setAudits).catch(() => {});
    apiClient.get('/api/v1/compliance/audit/rights').then(setRights).catch(() => {});
    apiClient.get('/api/v1/compliance/audit/stats').then(setStats).catch(() => {});
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const filteredAudits = audits.filter((a: any) => {
    if (filters.query && !a.framework?.toLowerCase().includes(filters.query.toLowerCase()) && !a.assignee?.toLowerCase().includes(filters.query.toLowerCase())) return false;
    if (filters.status && a.status !== filters.status) return false;
    if (filters.type && a.audit_type !== filters.type) return false;
    return true;
  }).sort((a: any, b: any) => {
    const dir = sortAsc ? 1 : -1;
    if (a[sortBy] < b[sortBy]) return -1 * dir;
    if (a[sortBy] > b[sortBy]) return 1 * dir;
    return 0;
  });

  const handleWorkflowAction = async (scheduleId: string, action: string) => {
    try {
      await apiClient.post(`/api/v1/compliance/audit/schedules/${scheduleId}/workflow`, { action });
      toast.success(`Audit ${action} executed`);
      fetchData();
    } catch { toast.error('Workflow action failed'); }
  };

  const handleEvidenceCollect = async (scheduleId: string) => {
    try {
      await apiClient.post(`/api/v1/compliance/audit/evidence/collect`, { schedule_id: scheduleId });
      toast.success('Evidence collected');
      fetchData();
    } catch { toast.error('Evidence collection failed'); }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div><h1 className="text-3xl font-bold text-white mb-2">Audit Management</h1><p className="text-slate-400">Schedule and manage compliance audits with customer audit rights</p></div>
        <div className="flex gap-2">
          <Button onClick={fetchData} variant="outline" className="text-slate-400"><RefreshCw className="mr-2 h-4 w-4" /> Refresh</Button>
          <Button className="bg-blue-600 hover:bg-blue-700" onClick={() => setTab('schedule')}><PlusCircle className="mr-2 h-4 w-4" /> New Audit</Button>
        </div>
      </div>
      {stats && <AuditMetricsGrid stats={stats} />}
      <div className="flex space-x-2 border-b border-slate-700 pb-2">
        <Button variant={tab === 'schedule' ? 'default' : 'ghost'} onClick={() => setTab('schedule')}><Calendar className="mr-2 h-4 w-4" /> Schedule</Button>
        <Button variant={tab === 'rights' ? 'default' : 'ghost'} onClick={() => setTab('rights')}><Users className="mr-2 h-4 w-4" /> Customer Rights</Button>
        <Button variant={tab === 'templates' ? 'default' : 'ghost'} onClick={() => setTab('templates')}><FileText className="mr-2 h-4 w-4" /> Templates</Button>
      </div>
      {tab === 'schedule' && (
        <div className="grid grid-cols-3 gap-6">
          <div className="col-span-2 space-y-4">
            <Card><CardHeader><CardTitle>Audit Schedule ({filteredAudits.length})</CardTitle></CardHeader>
              <CardContent>
                <AuditFilters filters={filters} onChange={setFilters} />
                <Table><TableHeader><TableRow>
                  {['Type', 'Framework', 'Scheduled', 'Status', 'Assignee', 'Actions'].map((h) => (
                    <TableHead key={h} className="text-slate-400 cursor-pointer" onClick={() => { const key = h.toLowerCase(); if (key === 'actions') return; setSortBy(key); setSortAsc(!sortAsc); }}>
                      <span className="flex items-center gap-1">{h} <ArrowUpDown className="h-3 w-3" /></span>
                    </TableHead>
                  ))}
                </TableRow></TableHeader>
                <TableBody>{filteredAudits.map((a: any) => (
                  <TableRow key={a.audit_id}>
                    <TableCell><Badge variant="outline">{a.audit_type}</Badge></TableCell>
                    <TableCell className="text-white">{a.framework}</TableCell>
                    <TableCell className="text-slate-400">{new Date(a.scheduled_date).toLocaleDateString()}</TableCell>
                    <TableCell><Badge className={a.status === 'completed' ? 'bg-green-600' : a.status === 'in_progress' ? 'bg-yellow-600' : 'bg-blue-600'}>{a.status}</Badge></TableCell>
                    <TableCell className="text-white">{a.assignee}</TableCell>
                    <TableCell><div className="flex gap-1">
                      <Button size="sm" variant="ghost" onClick={() => setWorkflowTarget(a.audit_id)}><Workflow className="h-4 w-4" /></Button>
                      <Button size="sm" variant="ghost" onClick={() => setEvidenceTarget(a.audit_id)}><FileText className="h-4 w-4" /></Button>
                      <Button size="sm" variant="ghost" onClick={() => handleEvidenceCollect(a.audit_id)}><ClipboardList className="h-4 w-4" /></Button>
                    </div></TableCell>
                  </TableRow>
                ))}</TableBody></Table>
              </CardContent></Card>
          </div>
          <div className="space-y-4">
            <UpcomingAuditsCard audits={audits} />
            <AuditNotificationsPanel notifications={[]} />
          </div>
        </div>
      )}
      {tab === 'rights' && (
        <Card><CardHeader><CardTitle>Customer Audit Rights</CardTitle></CardHeader>
          <CardContent>
            <Table><TableHeader><TableRow><TableHead className="text-slate-400">Customer</TableHead><TableHead className="text-slate-400">Framework</TableHead><TableHead className="text-slate-400">Frequency</TableHead><TableHead className="text-slate-400">Next Audit</TableHead><TableHead className="text-slate-400">Status</TableHead></TableRow></TableHeader>
              <TableBody>{rights.map((r: any) => (
                <TableRow key={r.right_id}>
                  <TableCell className="text-white">{r.customer_name}</TableCell>
                  <TableCell><Badge variant="outline">{r.framework}</Badge></TableCell>
                  <TableCell className="text-slate-400">Every {r.audit_frequency_days}d</TableCell>
                  <TableCell className="text-slate-400">{new Date(r.next_audit_date).toLocaleDateString()}</TableCell>
                  <TableCell><Badge className={r.status === 'active' ? 'bg-green-600' : 'bg-yellow-600'}>{r.status}</Badge></TableCell>
                </TableRow>
              ))}</TableBody></Table>
          </CardContent></Card>
      )}
      {tab === 'templates' && <AuditTemplatesPanel onSelect={(t) => toast.info(`Selected template: ${t.name}`)} />}
      {workflowTarget && <WorkflowActionDialog scheduleId={workflowTarget} onClose={() => setWorkflowTarget(null)} onExecute={handleWorkflowAction} />}
      {evidenceTarget && <AuditEvidenceSection scheduleId={evidenceTarget} onClose={() => setEvidenceTarget(null)} />}
    </div>
  );
}

import React from "react";

interface audit_managementAction {
  id: string;
  type: string;
  status: string;
  ts: string;
}

const audit_managementActions: React.FC<{}> = () => {
  const [items, setItems] = React.useState<audit_managementAction[]>([]);
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
      <h2 className="text-xl font-bold mb-4">audit_management Actions</h2>
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
export default audit_managementActions;
