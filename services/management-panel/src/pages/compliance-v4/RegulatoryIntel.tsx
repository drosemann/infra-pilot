import { useState, useEffect, useCallback } from 'react';
import { toast } from 'sonner';
import { apiClient } from '../../lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { BookOpen, Globe, Bell, BarChart3, Search, Filter, AlertTriangle, Calendar, CheckCircle, XCircle, ExternalLink, Clock, Shield, TrendingUp, RefreshCw, PlusCircle, Eye, FileText } from 'lucide-react';

function ImpactBadge({ level }: { level: string }) {
  const colors: Record<string, string> = {
    critical: 'bg-red-600', high: 'bg-orange-600', medium: 'bg-yellow-600', low: 'bg-green-600', monitor: 'bg-blue-600',
  };
  return <Badge className={colors[level] || 'bg-slate-600'}>{level}</Badge>;
}

function ChangeDetailModal({ change, onClose }: { change: any; onClose: () => void }) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-slate-800 rounded-lg p-6 w-[600px] max-h-[80vh] overflow-y-auto border border-slate-700" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-start justify-between mb-4">
          <div><h3 className="text-lg font-bold text-white">{change.title}</h3><p className="text-sm text-slate-400">{change.regulation} - {change.jurisdiction}</p></div>
          <ImpactBadge level={change.impact_level} />
        </div>
        <div className="space-y-3">
          <div><p className="text-xs text-slate-400 mb-1">Description</p><p className="text-sm text-white">{change.description}</p></div>
          <div className="grid grid-cols-2 gap-4">
            <div><p className="text-xs text-slate-400">Type</p><p className="text-sm text-white capitalize">{change.change_type?.replace(/_/g, ' ')}</p></div>
            <div><p className="text-xs text-slate-400">Status</p><Badge variant="outline">{change.status}</Badge></div>
            <div><p className="text-xs text-slate-400">Detected</p><p className="text-sm text-white">{new Date(change.detected_at).toLocaleString()}</p></div>
            <div><p className="text-xs text-slate-400">Effective</p><p className="text-sm text-white">{change.effective_date ? new Date(change.effective_date).toLocaleDateString() : 'N/A'}</p></div>
          </div>
          {change.affected_controls?.length > 0 && (
            <div><p className="text-xs text-slate-400 mb-1">Affected Controls</p><div className="flex flex-wrap gap-1">{change.affected_controls.map((c: string) => (
              <Badge key={c} variant="outline" className="text-xs">{c}</Badge>
            ))}</div></div>
          )}
          {change.action_required && (
            <div className="p-3 bg-orange-900/20 border border-orange-800 rounded">
              <p className="text-sm text-orange-400 flex items-center gap-2"><AlertTriangle className="h-4 w-4" /> Action Required by {change.action_deadline ? new Date(change.action_deadline).toLocaleDateString() : 'N/A'}</p>
            </div>
          )}
        </div>
        <Button variant="ghost" className="w-full mt-4 text-slate-400" onClick={onClose}>Close</Button>
      </div>
    </div>
  );
}

function ImpactMatrixCard({ matrix }: { matrix: any }) {
  if (!matrix || !matrix.matrix) return null;
  return (
    <Card><CardHeader><CardTitle className="flex items-center gap-2"><BarChart3 className="h-4 w-4 text-blue-400" /> Impact Matrix</CardTitle></CardHeader>
      <CardContent>
        <Table><TableHeader><TableRow><TableHead className="text-slate-400">Framework</TableHead><TableHead className="text-slate-400">Critical</TableHead><TableHead className="text-slate-400">High</TableHead><TableHead className="text-slate-400">Action</TableHead><TableHead className="text-slate-400">Deadlines</TableHead></TableRow></TableHeader>
          <TableBody>{Object.entries(matrix.matrix).map(([fw, d]: [string, any]) => (
            <TableRow key={fw}><TableCell className="text-white font-medium">{fw}</TableCell>
              <TableCell><span className="text-red-400">{d.critical}</span></TableCell>
              <TableCell><span className="text-orange-400">{d.high}</span></TableCell>
              <TableCell><span className="text-yellow-400">{d.action_required}</span></TableCell>
              <TableCell><span className="text-blue-400">{d.upcoming_deadlines}</span></TableCell>
            </TableRow>
          ))}</TableBody></Table>
      </CardContent></Card>
  );
}

function CalendarView({ changes }: { changes: any[] }) {
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const currentMonth = new Date().getMonth();
  const upcoming = changes.filter((c: any) => c.effective_date && new Date(c.effective_date) >= new Date()).slice(0, 6);
  return (
    <Card><CardHeader><CardTitle className="flex items-center gap-2"><Calendar className="h-4 w-4 text-blue-400" /> Upcoming Calendar</CardTitle></CardHeader>
      <CardContent>
        <div className="grid grid-cols-3 gap-2 mb-3">
          {months.slice(currentMonth, currentMonth + 3).map((m, i) => (
            <div key={m} className="text-center p-2 bg-slate-800 rounded">
              <p className="text-xs text-slate-400">{m}</p>
              <p className="text-lg font-bold text-white">{currentMonth + i + 1}</p>
            </div>
          ))}
        </div>
        <div className="space-y-2">{upcoming.length === 0 ? <p className="text-slate-400 text-sm">No upcoming changes</p> : upcoming.map((c: any, i: number) => (
          <div key={i} className="flex items-center justify-between p-2 bg-slate-800 rounded">
            <div><p className="text-sm text-white truncate max-w-[200px]">{c.title}</p><p className="text-xs text-slate-400">{new Date(c.effective_date).toLocaleDateString()}</p></div>
            <ImpactBadge level={c.impact_level} />
          </div>
        ))}</div>
      </CardContent></Card>
  );
}

function SourceHealthCard({ sources }: { sources: any[] }) {
  return (
    <Card><CardHeader><CardTitle className="flex items-center gap-2"><Globe className="h-4 w-4 text-blue-400" /> Source Health</CardTitle></CardHeader>
      <CardContent><div className="grid grid-cols-2 gap-3">
        {sources.slice(0, 6).map((s: any) => (
          <div key={s.source_id || s.id} className="p-3 bg-slate-800 rounded border border-slate-700">
            <div className="flex items-center gap-2 mb-1">
              {s.status === 'healthy' ? <CheckCircle className="h-3 w-3 text-green-400" /> : <XCircle className="h-3 w-3 text-red-400" />}
              <span className="text-sm text-white">{s.name}</span>
            </div>
            <p className="text-xs text-slate-400">{s.jurisdiction || s.jurisdiction}</p>
            <Badge variant="outline" className="mt-1 text-xs">{s.changes_detected_30d || 0} changes</Badge>
          </div>
        ))}
      </div></CardContent></Card>
  );
}

function DetectChangeForm({ onCreated }: { onCreated: () => void }) {
  const [title, setTitle] = useState('');
  const [regulation, setRegulation] = useState('');
  const [jurisdiction, setJurisdiction] = useState('');
  const [impact, setImpact] = useState('medium');
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (!title || !regulation) { toast.error('Title and regulation are required'); return; }
    setSubmitting(true);
    try {
      await apiClient.post('/api/v1/compliance/regulatory/detect', { title, regulation, jurisdiction, impact_level: impact, description, action_required: true });
      toast.success('Regulatory change detected');
      onCreated();
      setTitle(''); setRegulation(''); setJurisdiction(''); setDescription('');
    } catch { toast.error('Failed to detect change'); }
    setSubmitting(false);
  };

  return (
    <Card><CardHeader><CardTitle className="flex items-center gap-2"><PlusCircle className="h-4 w-4 text-green-400" /> Detect Change</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        <Input className="bg-slate-800 border-slate-700 text-white" placeholder="Change title" value={title} onChange={(e) => setTitle(e.target.value)} />
        <div className="grid grid-cols-3 gap-2">
          <Input className="bg-slate-800 border-slate-700 text-white" placeholder="Regulation" value={regulation} onChange={(e) => setRegulation(e.target.value)} />
          <Input className="bg-slate-800 border-slate-700 text-white" placeholder="Jurisdiction" value={jurisdiction} onChange={(e) => setJurisdiction(e.target.value)} />
          <select className="bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-sm text-white" value={impact} onChange={(e) => setImpact(e.target.value)}>
            <option value="critical">Critical</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option>
          </select>
        </div>
        <Textarea className="bg-slate-800 border-slate-700 text-white" placeholder="Description" value={description} onChange={(e) => setDescription(e.target.value)} />
        <Button onClick={handleSubmit} disabled={submitting} className="bg-blue-600 hover:bg-blue-700 w-full">Submit</Button>
      </CardContent></Card>
  );
}

export default function RegulatoryIntelPage() {
  const [changes, setChanges] = useState<any[]>([]);
  const [sources, setSources] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [matrix, setMatrix] = useState<any>(null);
  const [selectedChange, setSelectedChange] = useState<any>(null);
  const [query, setQuery] = useState('');
  const [filterImpact, setFilterImpact] = useState('');
  const [filterStatus, setFilterStatus] = useState('');

  const fetchData = useCallback(() => {
    apiClient.get('/api/v1/compliance/regulatory/changes').then(r => setChanges(r.changes || [])).catch(() => {});
    apiClient.get('/api/v1/compliance/regulatory/sources').then(setSources).catch(() => {});
    apiClient.get('/api/v1/compliance/regulatory/stats').then(setStats).catch(() => {});
    apiClient.get('/api/v1/compliance/regulatory/matrix').then(setMatrix).catch(() => {});
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const filtered = changes.filter((c: any) => {
    if (query && !c.title?.toLowerCase().includes(query.toLowerCase()) && !c.regulation?.toLowerCase().includes(query.toLowerCase())) return false;
    if (filterImpact && c.impact_level !== filterImpact) return false;
    if (filterStatus && c.status !== filterStatus) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div><h1 className="text-3xl font-bold text-white mb-2">Regulatory Intelligence Engine</h1><p className="text-slate-400">Automated regulatory change monitoring and impact analysis</p></div>
        <div className="flex gap-2">
          <Button onClick={fetchData} variant="outline" className="text-slate-400"><RefreshCw className="mr-2 h-4 w-4" /> Refresh</Button>
        </div>
      </div>
      {stats && (
        <div className="grid grid-cols-4 gap-4">
          <Card><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Total Changes</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-white">{stats.total_changes}</div></CardContent></Card>
          <Card><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Action Required</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-yellow-400">{stats.action_required}</div></CardContent></Card>
          <Card><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Sources</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-white">{stats.sources_monitored}</div></CardContent></Card>
          <Card><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">By Impact</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-white">{Object.entries(stats.by_impact || {}).map(([k, v]: [string, any]) => `${k}: ${v}`).join(', ')}</div></CardContent></Card>
        </div>
      )}
      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2 space-y-4">
          <Card><CardHeader><CardTitle className="flex items-center gap-2"><BookOpen className="h-4 w-4 text-blue-400" /> Regulatory Changes ({filtered.length})</CardTitle></CardHeader>
            <CardContent>
              <div className="flex gap-3 items-center mb-4">
                <div className="relative flex-1"><Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                  <Input className="pl-9 bg-slate-800 border-slate-700 text-white" placeholder="Search changes..." value={query} onChange={(e) => setQuery(e.target.value)} /></div>
                <select className="bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-sm text-white" value={filterImpact} onChange={(e) => setFilterImpact(e.target.value)}>
                  <option value="">All Impacts</option><option value="critical">Critical</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option>
                </select>
                <select className="bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-sm text-white" value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
                  <option value="">All Status</option><option value="new">New</option><option value="reviewing">Reviewing</option><option value="reviewed">Reviewed</option>
                </select>
              </div>
              <Table><TableHeader><TableRow><TableHead className="text-slate-400">Title</TableHead><TableHead className="text-slate-400">Regulation</TableHead><TableHead className="text-slate-400">Impact</TableHead><TableHead className="text-slate-400">Status</TableHead><TableHead className="text-slate-400">Detected</TableHead><TableHead className="text-slate-400">Actions</TableHead></TableRow></TableHeader>
                <TableBody>{filtered.slice(0, 50).map((c: any, i: number) => (
                  <TableRow key={i}>
                    <TableCell className="font-medium text-white max-w-[200px] truncate">{c.title}</TableCell>
                    <TableCell><Badge variant="outline">{c.regulation}</Badge></TableCell>
                    <TableCell><ImpactBadge level={c.impact_level} /></TableCell>
                    <TableCell><Badge variant="outline">{c.status}</Badge></TableCell>
                    <TableCell className="text-slate-400 text-sm">{new Date(c.detected_at).toLocaleDateString()}</TableCell>
                    <TableCell><Button size="sm" variant="ghost" onClick={() => setSelectedChange(c)}><Eye className="h-4 w-4" /></Button></TableCell>
                  </TableRow>
                ))}</TableBody></Table>
            </CardContent></Card>
          <DetectChangeForm onCreated={fetchData} />
        </div>
        <div className="space-y-4">
          <CalendarView changes={changes} />
          <SourceHealthCard sources={sources} />
        </div>
      </div>
      {matrix && <ImpactMatrixCard matrix={matrix} />}
      {selectedChange && <ChangeDetailModal change={selectedChange} onClose={() => setSelectedChange(null)} />}
    </div>
  );
}
import React from "react";

interface regulatory_intelAction {
  id: string;
  type: string;
  status: string;
  ts: string;
}

const regulatory_intelActions: React.FC<{}> = () => {
  const [items, setItems] = React.useState<regulatory_intelAction[]>([]);
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
      <h2 className="text-xl font-bold mb-4">regulatory_intel Actions</h2>
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
export default regulatory_intelActions;
