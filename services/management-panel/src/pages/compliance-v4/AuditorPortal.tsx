import { useState, useEffect, useCallback } from 'react';
import { toast } from 'sonner';
import { apiClient } from '../../lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Users, Search, Filter, Shield, CheckCircle, XCircle, RefreshCw, PlusCircle, Key, Clock, AlertTriangle, FileText } from 'lucide-react';

function EngagementStatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = { active: 'bg-green-600', pending: 'bg-yellow-600', completed: 'bg-blue-600', cancelled: 'bg-red-600', scheduled: 'bg-purple-600' };
  return <Badge className={colors[status] || 'bg-slate-600'}>{status}</Badge>;
}

function EngagementDetailModal({ engagementId, onClose }: { engagementId: string; onClose: () => void }) {
  const [eng, setEng] = useState<any>(null);
  useEffect(() => {
    apiClient.get(`/api/v1/compliance/auditor/engagements/${engagementId}`).then(setEng).catch(() => setEng(null));
  }, [engagementId]);
  if (!eng) return null;
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-slate-800 rounded-lg p-6 w-[600px] max-h-[80vh] overflow-y-auto border border-slate-700" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-start justify-between mb-4">
          <div><h3 className="text-lg font-bold text-white">Engagement Detail</h3><p className="text-sm text-slate-400 font-mono">{engagementId}</p></div>
          <EngagementStatusBadge status={eng.status} />
        </div>
        <div className="grid grid-cols-2 gap-3 mb-4">
          <div><p className="text-xs text-slate-400">Auditor</p><p className="text-white">{eng.auditor_name || 'N/A'}</p></div>
          <div><p className="text-xs text-slate-400">Framework</p><Badge variant="outline">{eng.framework}</Badge></div>
          <div><p className="text-xs text-slate-400">Start Date</p><p className="text-white">{eng.start_date ? new Date(eng.start_date).toLocaleDateString() : 'N/A'}</p></div>
          <div><p className="text-xs text-slate-400">End Date</p><p className="text-white">{eng.end_date ? new Date(eng.end_date).toLocaleDateString() : 'N/A'}</p></div>
          <div><p className="text-xs text-slate-400">Scope</p><p className="text-white">{eng.scope || 'Full'}</p></div>
          <div><p className="text-xs text-slate-400">Controls</p><p className="text-white">{eng.control_count || eng.controls_in_scope?.length || 0}</p></div>
        </div>
        {eng.findings?.length > 0 && (
          <div><p className="text-sm text-white mb-2">Findings</p>{eng.findings.map((f: any, i: number) => (
            <div key={i} className="p-2 bg-slate-700 rounded mb-2"><p className="text-xs text-white">{f.title}</p><p className="text-xs text-slate-400">{f.severity}</p></div>
          ))}</div>
        )}
        <Button variant="ghost" className="w-full mt-4 text-slate-400" onClick={onClose}>Close</Button>
      </div>
    </div>
  );
}

function AuditorSessionBadge({ expiresAt }: { expiresAt: string }) {
  const expiry = new Date(expiresAt);
  const now = new Date();
  const diff = expiry.getTime() - now.getTime();
  if (diff < 0) return <Badge className="bg-red-600">Expired</Badge>;
  const hours = Math.floor(diff / 3600000);
  if (hours < 24) return <Badge className="bg-yellow-600">{hours}h remaining</Badge>;
  return <Badge className="bg-green-600">{Math.floor(hours / 24)}d remaining</Badge>;
}

function CreateEngagementForm({ onCreated }: { onCreated: () => void }) {
  const [framework, setFramework] = useState('SOC_2');
  const [auditorName, setAuditorName] = useState('');
  const [scope, setScope] = useState('Full');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (!auditorName) { toast.error('Auditor name required'); return; }
    setSubmitting(true);
    try {
      await apiClient.post('/api/v1/compliance/auditor/engagements', { framework, auditor_name: auditorName, scope, status: 'scheduled', start_date: new Date().toISOString().slice(0, 10), end_date: new Date(Date.now() + 90 * 86400000).toISOString().slice(0, 10) });
      toast.success('Engagement created');
      onCreated();
    } catch { toast.error('Creation failed'); }
    setSubmitting(false);
  };

  return (
    <Card><CardHeader><CardTitle className="flex items-center gap-2"><PlusCircle className="h-4 w-4 text-green-400" /> New Engagement</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        <Input className="bg-slate-800 border-slate-700 text-white" placeholder="Auditor Name" value={auditorName} onChange={(e) => setAuditorName(e.target.value)} />
        <select className="w-full bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-sm text-white" value={framework} onChange={(e) => setFramework(e.target.value)}>
          <option value="SOC_2">SOC 2</option><option value="HIPAA">HIPAA</option><option value="PCI_DSS">PCI DSS</option><option value="GDPR">GDPR</option><option value="ISO_27001">ISO 27001</option>
        </select>
        <Input className="bg-slate-800 border-slate-700 text-white" placeholder="Scope" value={scope} onChange={(e) => setScope(e.target.value)} />
        <Button onClick={handleSubmit} disabled={submitting} className="bg-blue-600 hover:bg-blue-700 w-full">Schedule Engagement</Button>
      </CardContent></Card>
  );
}

export default function AuditorPortalPage() {
  const [engagements, setEngagements] = useState<any[]>([]);
  const [sessions, setSessions] = useState<any[]>([]);
  const [findings, setFindings] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [tab, setTab] = useState<'engagements' | 'sessions' | 'findings'>('engagements');
  const [query, setQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [selectedEngagement, setSelectedEngagement] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);

  const fetchData = useCallback(() => {
    apiClient.get('/api/v1/compliance/auditor/engagements').then(setEngagements).catch(() => {});
    apiClient.get('/api/v1/compliance/auditor/sessions').then(setSessions).catch(() => {});
    apiClient.get('/api/v1/compliance/auditor/findings').then(setFindings).catch(() => {});
    apiClient.get('/api/v1/compliance/auditor/stats').then(setStats).catch(() => {});
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const filteredEngagements = engagements.filter((e: any) => {
    if (query && !e.auditor_name?.toLowerCase().includes(query.toLowerCase()) && !e.engagement_id?.toLowerCase().includes(query.toLowerCase())) return false;
    if (filterStatus && e.status !== filterStatus) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div><h1 className="text-3xl font-bold text-white mb-2">Auditor Portal</h1><p className="text-slate-400">Manage auditor engagements, sessions, and findings for third-party audits</p></div>
        <div className="flex gap-2">
          <Button onClick={fetchData} variant="outline" className="text-slate-400"><RefreshCw className="mr-2 h-4 w-4" /> Refresh</Button>
          <Button onClick={() => setShowCreate(!showCreate)} className="bg-blue-600 hover:bg-blue-700"><PlusCircle className="mr-2 h-4 w-4" /> New Engagement</Button>
        </div>
      </div>
      {stats && (
        <div className="grid grid-cols-4 gap-4">
          <Card><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Engagements</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-white">{stats.total_engagements}</div></CardContent></Card>
          <Card><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Active</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-green-400">{stats.active_engagements}</div></CardContent></Card>
          <Card><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Open Findings</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-yellow-400">{stats.open_findings}</div></CardContent></Card>
          <Card><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Completed</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-blue-400">{stats.completed_engagements}</div></CardContent></Card>
        </div>
      )}
      <div className="flex space-x-2 border-b border-slate-700 pb-2">
        <Button variant={tab === 'engagements' ? 'default' : 'ghost'} onClick={() => setTab('engagements')}><Users className="mr-2 h-4 w-4" /> Engagements</Button>
        <Button variant={tab === 'sessions' ? 'default' : 'ghost'} onClick={() => setTab('sessions')}><Key className="mr-2 h-4 w-4" /> Sessions</Button>
        <Button variant={tab === 'findings' ? 'default' : 'ghost'} onClick={() => setTab('findings')}><FileText className="mr-2 h-4 w-4" /> Findings</Button>
      </div>
      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2">
          {tab === 'engagements' && (
            <Card><CardHeader><CardTitle>Auditor Engagements ({filteredEngagements.length})</CardTitle></CardHeader>
              <CardContent>
                <div className="flex gap-3 items-center mb-4">
                  <div className="relative flex-1"><Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                    <Input className="pl-9 bg-slate-800 border-slate-700 text-white" placeholder="Search by auditor or ID..." value={query} onChange={(e) => setQuery(e.target.value)} /></div>
                  <select className="bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-sm text-white" value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
                    <option value="">All</option><option value="active">Active</option><option value="pending">Pending</option><option value="completed">Completed</option>
                  </select>
                </div>
                <Table><TableHeader><TableRow><TableHead className="text-slate-400">ID</TableHead><TableHead className="text-slate-400">Auditor</TableHead><TableHead className="text-slate-400">Framework</TableHead><TableHead className="text-slate-400">Status</TableHead><TableHead className="text-slate-400">Scope</TableHead><TableHead className="text-slate-400">Actions</TableHead></TableRow></TableHeader>
                  <TableBody>{filteredEngagements.map((e: any) => (
                    <TableRow key={e.engagement_id}>
                      <TableCell className="font-mono text-xs text-white cursor-pointer hover:text-blue-400" onClick={() => setSelectedEngagement(e.engagement_id)}>{e.engagement_id}</TableCell>
                      <TableCell className="text-white">{e.auditor_name}</TableCell>
                      <TableCell><Badge variant="outline">{e.framework}</Badge></TableCell>
                      <TableCell><EngagementStatusBadge status={e.status} /></TableCell>
                      <TableCell className="text-slate-400 text-sm">{e.scope}</TableCell>
                      <TableCell><Button size="sm" variant="ghost" className="text-blue-400">View</Button></TableCell>
                    </TableRow>
                  ))}</TableBody></Table>
              </CardContent></Card>
          )}
          {tab === 'sessions' && (
            <Card><CardHeader><CardTitle>Auditor Sessions ({sessions.length})</CardTitle></CardHeader>
              <CardContent>
                <Table><TableHeader><TableRow><TableHead className="text-slate-400">Session ID</TableHead><TableHead className="text-slate-400">Engagement</TableHead><TableHead className="text-slate-400">Access Level</TableHead><TableHead className="text-slate-400">Expiry</TableHead><TableHead className="text-slate-400">Actions</TableHead></TableRow></TableHeader>
                  <TableBody>{sessions.map((s: any) => (
                    <TableRow key={s.session_id}>
                      <TableCell className="font-mono text-xs text-white">{s.session_id}</TableCell>
                      <TableCell className="font-mono text-xs text-slate-400">{s.engagement_id}</TableCell>
                      <TableCell className="text-white">{s.access_level}</TableCell>
                      <TableCell><AuditorSessionBadge expiresAt={s.expires_at} /></TableCell>
                      <TableCell><Button size="sm" variant="ghost" className="text-red-400">Revoke</Button></TableCell>
                    </TableRow>
                  ))}</TableBody></Table>
              </CardContent></Card>
          )}
          {tab === 'findings' && (
            <Card><CardHeader><CardTitle>Audit Findings ({findings.length})</CardTitle></CardHeader>
              <CardContent>
                <Table><TableHeader><TableRow><TableHead className="text-slate-400">ID</TableHead><TableHead className="text-slate-400">Title</TableHead><TableHead className="text-slate-400">Engagement</TableHead><TableHead className="text-slate-400">Severity</TableHead><TableHead className="text-slate-400">Status</TableHead><TableHead className="text-slate-400">Date</TableHead></TableRow></TableHeader>
                  <TableBody>{findings.map((f: any) => (
                    <TableRow key={f.finding_id || f.id}>
                      <TableCell className="font-mono text-xs text-white">{f.finding_id || f.id}</TableCell>
                      <TableCell className="text-white">{f.title}</TableCell>
                      <TableCell className="font-mono text-xs text-slate-400">{f.engagement_id}</TableCell>
                      <TableCell><Badge className={f.severity === 'critical' ? 'bg-red-600' : f.severity === 'high' ? 'bg-orange-600' : f.severity === 'medium' ? 'bg-yellow-600' : 'bg-blue-600'}>{f.severity}</Badge></TableCell>
                      <TableCell><Badge className={f.status === 'open' ? 'bg-red-600' : f.status === 'addressed' ? 'bg-green-600' : 'bg-slate-600'}>{f.status}</Badge></TableCell>
                      <TableCell className="text-slate-400 text-sm">{f.created_at ? new Date(f.created_at).toLocaleDateString() : 'N/A'}</TableCell>
                    </TableRow>
                  ))}</TableBody></Table>
              </CardContent></Card>
          )}
        </div>
        <div className="space-y-4">
          {showCreate && <CreateEngagementForm onCreated={fetchData} />}
        </div>
      </div>
      {selectedEngagement && <EngagementDetailModal engagementId={selectedEngagement} onClose={() => setSelectedEngagement(null)} />}
    </div>
  );
}
import React from "react";

interface auditor_portalAction {
  id: string;
  type: string;
  status: string;
  ts: string;
}

const auditor_portalActions: React.FC<{}> = () => {
  const [items, setItems] = React.useState<auditor_portalAction[]>([]);
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
      <h2 className="text-xl font-bold mb-4">auditor_portal Actions</h2>
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
export default auditor_portalActions;
