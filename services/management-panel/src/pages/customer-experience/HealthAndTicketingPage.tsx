import { useState, useEffect, useCallback } from 'react';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Heart, Ticket, Search, RefreshCw, PlusCircle, Activity, AlertTriangle, TrendingUp, TrendingDown, Clock, UserCheck, BarChart3, Filter, CheckCircle, XCircle } from 'lucide-react';

function HealthRiskBadge({ risk }: { risk: string }) {
  const colors: Record<string, string> = { critical: 'bg-red-600', high: 'bg-orange-600', medium: 'bg-yellow-600', low: 'bg-green-600', healthy: 'bg-green-600' };
  return <Badge className={colors[risk] || 'bg-slate-600'}>{risk}</Badge>;
}

function TicketPriorityBadge({ priority }: { priority: string }) {
  const colors: Record<string, string> = { critical: 'bg-red-600', high: 'bg-orange-600', medium: 'bg-yellow-600', low: 'bg-green-600' };
  return <Badge className={colors[priority] || 'bg-slate-600'}>{priority}</Badge>;
}

function HealthDetailModal({ customerId, onClose }: { customerId: string; onClose: () => void }) {
  const [profile, setProfile] = useState<any>(null);
  useEffect(() => {
    fetch(`/api/v1/cx/health/${customerId}`).then(r => r.json()).then(setProfile).catch(() => setProfile(null));
  }, [customerId]);
  if (!profile) return null;
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-slate-800 rounded-lg p-6 w-[500px] border border-slate-700" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-start justify-between mb-4">
          <div><h3 className="text-lg font-bold text-white">Health Profile</h3><p className="text-sm text-slate-400">{customerId}</p></div>
          <HealthRiskBadge risk={profile.risk_level} />
        </div>
        <div className="grid grid-cols-2 gap-3 mb-4">
          <div><p className="text-xs text-slate-400">Score</p><p className="text-2xl font-bold text-white">{profile.overall_health_score || profile.composite_score || 0}</p></div>
          <div><p className="text-xs text-slate-400">Trend</p><p className="text-white flex items-center gap-1">{profile.trend === 'improving' ? <TrendingUp className="h-4 w-4 text-green-400" /> : profile.trend === 'declining' ? <TrendingDown className="h-4 w-4 text-red-400" /> : <Activity className="h-4 w-4 text-yellow-400" />}{profile.trend}</p></div>
        </div>
        {profile.recommendations?.length > 0 && (
          <div><p className="text-sm text-white mb-2">Recommendations</p>{profile.recommendations.slice(0, 5).map((r: string, i: number) => (
            <p key={i} className="text-xs text-slate-400 p-1">- {r}</p>
          ))}</div>
        )}
        <Button variant="ghost" className="w-full mt-4 text-slate-400" onClick={onClose}>Close</Button>
      </div>
    </div>
  );
}

function TicketDetailModal({ ticketId, onClose }: { ticketId: string; onClose: () => void }) {
  const [ticket, setTicket] = useState<any>(null);
  useEffect(() => {
    fetch(`/api/v1/cx/tickets/${ticketId}`).then(r => r.json()).then(setTicket).catch(() => setTicket(null));
  }, [ticketId]);
  if (!ticket) return null;
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-slate-800 rounded-lg p-6 w-[550px] border border-slate-700" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-start justify-between mb-4">
          <div><h3 className="text-lg font-bold text-white">Ticket Detail</h3><p className="text-sm text-slate-400 font-mono">{ticketId}</p></div>
          <TicketPriorityBadge priority={ticket.priority} />
        </div>
        <p className="text-lg text-white mb-2">{ticket.subject}</p>
        <p className="text-sm text-slate-400 mb-4">{ticket.description}</p>
        <div className="grid grid-cols-2 gap-3">
          <div><p className="text-xs text-slate-400">Status</p><Badge className={ticket.status === 'open' ? 'bg-blue-600' : ticket.status === 'resolved' ? 'bg-green-600' : 'bg-slate-600'}>{ticket.status}</Badge></div>
          <div><p className="text-xs text-slate-400">Assigned To</p><p className="text-white">{ticket.assigned_to || 'Unassigned'}</p></div>
          <div><p className="text-xs text-slate-400">Customer</p><p className="text-white">{ticket.customer_name || ticket.customer_id}</p></div>
          <div><p className="text-xs text-slate-400">SLA</p><p className="text-white">{ticket.sla_breached ? <Badge className="bg-red-600">Breached</Badge> : <Badge className="bg-green-600">OK</Badge>}</p></div>
        </div>
        <Button variant="ghost" className="w-full mt-4 text-slate-400" onClick={onClose}>Close</Button>
      </div>
    </div>
  );
}

function CreateTicketForm({ onCreated }: { onCreated: () => void }) {
  const [subject, setSubject] = useState('');
  const [description, setDescription] = useState('');
  const [customerId, setCustomerId] = useState('');
  const [priority, setPriority] = useState('medium');
  const [submitting, setSubmitting] = useState(false);

  const handleCreate = async () => {
    if (!subject || !customerId) { toast.error('Subject and customer ID required'); return; }
    setSubmitting(true);
    try {
      const resp = await fetch('/api/v1/cx/tickets', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ subject, description, customer_id: customerId, priority }) });
      if (resp.ok) { toast.success('Ticket created'); onCreated(); }
    } catch { toast.error('Creation failed'); }
    setSubmitting(false);
  };

  return (
    <Card><CardHeader><CardTitle className="flex items-center gap-2"><PlusCircle className="h-4 w-4 text-green-400" /> Create Ticket</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        <Input className="bg-slate-800 border-slate-700 text-white" placeholder="Subject" value={subject} onChange={(e) => setSubject(e.target.value)} />
        <Input className="bg-slate-800 border-slate-700 text-white" placeholder="Customer ID" value={customerId} onChange={(e) => setCustomerId(e.target.value)} />
        <textarea className="w-full bg-slate-800 border border-slate-700 rounded-md p-2 text-white text-sm" rows={3} placeholder="Description" value={description} onChange={(e) => setDescription(e.target.value)} />
        <select className="w-full bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-sm text-white" value={priority} onChange={(e) => setPriority(e.target.value)}>
          <option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option><option value="critical">Critical</option>
        </select>
        <Button onClick={handleCreate} disabled={submitting} className="bg-blue-600 hover:bg-blue-700 w-full">Create</Button>
      </CardContent></Card>
  );
}

function ScoreRangeChart({ buckets }: { buckets: any }) {
  if (!buckets) return null;
  const total = Object.values(buckets).reduce((s: number, v: any) => s + (typeof v === 'number' ? v : 0), 0) || 1;
  return (
    <div className="space-y-2">{(Object.entries(buckets)).map(([range, count]: [string, any]) => {
      const pct = ((typeof count === 'number' ? count : 0) / total) * 100;
      return (
        <div key={range} className="flex items-center gap-3"><span className="text-xs text-slate-400 w-24">{range}</span>
          <div className="flex-1 h-4 bg-slate-700 rounded overflow-hidden"><div className="h-full bg-blue-500 rounded transition-all" style={{ width: `${pct}%` }} /></div>
          <span className="text-xs text-white w-10 text-right">{count}</span>
        </div>
      );
    })}</div>
  );
}

function HealthMetricsCard({ stats }: { stats: any }) {
  if (!stats) return null;
  return (
    <Card className="bg-slate-800 border-slate-700"><CardHeader><CardTitle className="flex items-center gap-2 text-sm"><BarChart3 className="h-4 w-4 text-blue-400" /> Segment Metrics</CardTitle></CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div className="flex items-center justify-between"><span className="text-sm text-slate-400">Healthy</span><span className="text-green-400 font-bold">{stats.segments?.healthy || 0}</span></div>
          <div className="flex items-center justify-between"><span className="text-sm text-slate-400">At Risk</span><span className="text-red-400 font-bold">{stats.at_risk_count || stats.segments?.at_risk || 0}</span></div>
          <div className="flex items-center justify-between"><span className="text-sm text-slate-400">Churn Risk</span><span className="text-orange-400 font-bold">{stats.churn_risk_count || 0}</span></div>
          <div className="flex items-center justify-between"><span className="text-sm text-slate-400">Avg Score</span><span className="text-white font-bold">{stats.average_score || 0}</span></div>
        </div>
      </CardContent></Card>
  );
}

export function HealthScoringPage() {
  const [profiles, setProfiles] = useState<any[]>([]);
  const [stats, setStats] = useState<any>({});
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [filterRisk, setFilterRisk] = useState('');
  const [tab, setTab] = useState<'profiles' | 'distribution' | 'metrics'>('profiles');
  const [distribution, setDistribution] = useState<any>(null);

  const fetchData = useCallback(() => {
    fetch('/api/v1/cx/health/stats').then(r => r.json()).then(setStats).catch(() => {});
    fetch('/api/v1/cx/health/profile').then(r => r.json()).then(d => setProfiles(d.profiles || d || [])).catch(() => {});
    fetch('/api/v1/cx/health/distribution').then(r => r.json()).then(setDistribution).catch(() => {});
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const filteredProfiles = profiles.filter((p: any) => {
    if (search && !p.customer_id?.toLowerCase().includes(search.toLowerCase()) && !p.customer_name?.toLowerCase().includes(search.toLowerCase())) return false;
    if (filterRisk && p.risk_level !== filterRisk) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div><h1 className="text-3xl font-bold text-white mb-2">Customer Health Scoring</h1><p className="text-slate-400">Composite health scores with churn prediction and proactive outreach triggers</p></div>
        <Button onClick={fetchData} variant="outline" className="text-slate-400"><RefreshCw className="mr-2 h-4 w-4" /> Refresh</Button>
      </div>
      {stats.total_customers && (
        <div className="grid grid-cols-4 gap-4">
          <Card className="bg-slate-800 border-slate-700"><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Total Customers</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-white">{stats.total_customers}</div></CardContent></Card>
          <Card className="bg-slate-800 border-slate-700"><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Average Score</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-white">{stats.average_score}</div></CardContent></Card>
          <Card className="bg-slate-800 border-slate-700"><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">At Risk</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-red-400">{stats.at_risk_count || 0}</div></CardContent></Card>
          <Card className="bg-slate-800 border-slate-700"><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Healthy</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-green-400">{stats.segments?.healthy || 0}</div></CardContent></Card>
        </div>
      )}
      <div className="flex space-x-2 border-b border-slate-700 pb-2">
        <Button variant={tab === 'profiles' ? 'default' : 'ghost'} onClick={() => setTab('profiles')}><Heart className="mr-2 h-4 w-4" /> Profiles</Button>
        <Button variant={tab === 'distribution' ? 'default' : 'ghost'} onClick={() => setTab('distribution')}><Activity className="mr-2 h-4 w-4" /> Distribution</Button>
        <Button variant={tab === 'metrics' ? 'default' : 'ghost'} onClick={() => setTab('metrics')}><BarChart3 className="mr-2 h-4 w-4" /> Metrics</Button>
      </div>
      {tab === 'profiles' && (
        <Card className="bg-slate-800 border-slate-700"><CardHeader><CardTitle className="text-white">Health Profiles ({filteredProfiles.length})</CardTitle></CardHeader>
          <CardContent>
            <div className="flex gap-3 items-center mb-4">
              <div className="relative flex-1"><Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                <Input className="pl-9 bg-slate-700 border-slate-600 text-white" placeholder="Search by ID or name..." value={search} onChange={(e) => setSearch(e.target.value)} /></div>
              <select className="bg-slate-700 border border-slate-600 rounded-md px-3 py-2 text-sm text-white" value={filterRisk} onChange={(e) => setFilterRisk(e.target.value)}>
                <option value="">All Risk Levels</option><option value="critical">Critical</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option>
              </select>
            </div>
            <Table><TableHeader><TableRow><TableHead className="text-slate-400">ID</TableHead><TableHead className="text-slate-400">Name</TableHead><TableHead className="text-slate-400">Score</TableHead><TableHead className="text-slate-400">Risk</TableHead><TableHead className="text-slate-400">Trend</TableHead><TableHead className="text-slate-400">Actions</TableHead></TableRow></TableHeader>
              <TableBody>{filteredProfiles.slice(0, 30).map((p: any) => (
                <TableRow key={p.customer_id} className="cursor-pointer hover:bg-slate-700" onClick={() => setSelectedId(p.customer_id)}>
                  <TableCell className="text-white font-mono text-xs">{p.customer_id}</TableCell>
                  <TableCell className="text-white">{p.customer_name || p.customer_id}</TableCell>
                  <TableCell><span className={`font-bold ${(p.overall_health_score || p.composite_score || 0) >= 70 ? 'text-green-400' : (p.overall_health_score || p.composite_score || 0) >= 40 ? 'text-yellow-400' : 'text-red-400'}`}>{p.overall_health_score || p.composite_score || 0}</span></TableCell>
                  <TableCell><HealthRiskBadge risk={p.risk_level} /></TableCell>
                  <TableCell>{p.trend === 'improving' ? <TrendingUp className="h-4 w-4 text-green-400" /> : p.trend === 'declining' ? <TrendingDown className="h-4 w-4 text-red-400" /> : <Activity className="h-4 w-4 text-yellow-400" />}</TableCell>
                  <TableCell><Button size="sm" variant="ghost" className="text-blue-400" onClick={(e) => { e.stopPropagation(); setSelectedId(p.customer_id); }}>View</Button></TableCell>
                </TableRow>
              ))}</TableBody></Table>
          </CardContent></Card>
      )}
      {tab === 'distribution' && distribution && (
        <Card className="bg-slate-800 border-slate-700"><CardHeader><CardTitle className="text-white">Score Distribution</CardTitle></CardHeader>
          <CardContent><ScoreRangeChart buckets={distribution.buckets || distribution} /></CardContent></Card>
      )}
      {tab === 'metrics' && <HealthMetricsCard stats={stats} />}
      {selectedId && <HealthDetailModal customerId={selectedId} onClose={() => setSelectedId(null)} />}
    </div>
  );
}

export function TicketingPage() {
  const [tickets, setTickets] = useState<any[]>([]);
  const [stats, setStats] = useState<any>({});
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [filterPriority, setFilterPriority] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [tab, setTab] = useState<'tickets' | 'sla'>('tickets');

  const fetchData = useCallback(() => {
    fetch('/api/v1/cx/tickets').then(r => r.json()).then(d => setTickets(d.tickets || [])).catch(() => {});
    fetch('/api/v1/cx/tickets/stats').then(r => r.json()).then(setStats).catch(() => {});
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const filteredTickets = tickets.filter((t: any) => {
    if (search && !t.subject?.toLowerCase().includes(search.toLowerCase()) && !t.ticket_id?.toLowerCase().includes(search.toLowerCase())) return false;
    if (filterStatus && t.status !== filterStatus) return false;
    if (filterPriority && t.priority !== filterPriority) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div><h1 className="text-3xl font-bold text-white mb-2">Support Tickets</h1><p className="text-slate-400">Integrated ticketing with SLA management and assignment rules</p></div>
        <div className="flex gap-2">
          <Button onClick={fetchData} variant="outline" className="text-slate-400"><RefreshCw className="mr-2 h-4 w-4" /> Refresh</Button>
          <Button onClick={() => setShowCreate(!showCreate)} className="bg-blue-600 hover:bg-blue-700"><PlusCircle className="mr-2 h-4 w-4" /> Create</Button>
        </div>
      </div>
      {stats.total_tickets && (
        <div className="grid grid-cols-5 gap-4">
          <Card className="bg-slate-800 border-slate-700"><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Total</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-white">{stats.total_tickets}</div></CardContent></Card>
          <Card className="bg-slate-800 border-slate-700"><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Open</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-blue-400">{stats.open_tickets || stats.by_status?.open || 0}</div></CardContent></Card>
          <Card className="bg-slate-800 border-slate-700"><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">SLA Breaches</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-red-400">{stats.sla_breaches || 0}</div></CardContent></Card>
          <Card className="bg-slate-800 border-slate-700"><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Avg Resolution</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-white">{stats.avg_resolution_time_hours || 0}h</div></CardContent></Card>
          <Card className="bg-slate-800 border-slate-700"><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Satisfaction</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-green-400">{stats.avg_satisfaction || 0}/5</div></CardContent></Card>
        </div>
      )}
      <div className="flex space-x-2 border-b border-slate-700 pb-2">
        <Button variant={tab === 'tickets' ? 'default' : 'ghost'} onClick={() => setTab('tickets')}><Ticket className="mr-2 h-4 w-4" /> All Tickets</Button>
        <Button variant={tab === 'sla' ? 'default' : 'ghost'} onClick={() => setTab('sla')}><Clock className="mr-2 h-4 w-4" /> SLA Overview</Button>
      </div>
      {tab === 'tickets' && (
        <div className="grid grid-cols-3 gap-6">
          <div className="col-span-2">
            <Card className="bg-slate-800 border-slate-700"><CardHeader><CardTitle className="text-white">Tickets ({filteredTickets.length})</CardTitle></CardHeader>
              <CardContent>
                <div className="flex gap-3 items-center mb-4">
                  <div className="relative flex-1"><Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                    <Input className="pl-9 bg-slate-700 border-slate-600 text-white" placeholder="Search tickets..." value={search} onChange={(e) => setSearch(e.target.value)} /></div>
                  <select className="bg-slate-700 border border-slate-600 rounded-md px-3 py-2 text-sm text-white" value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
                    <option value="">All Status</option><option value="open">Open</option><option value="in_progress">In Progress</option><option value="resolved">Resolved</option><option value="closed">Closed</option>
                  </select>
                  <select className="bg-slate-700 border border-slate-600 rounded-md px-3 py-2 text-sm text-white" value={filterPriority} onChange={(e) => setFilterPriority(e.target.value)}>
                    <option value="">All Priority</option><option value="critical">Critical</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option>
                  </select>
                </div>
                <Table><TableHeader><TableRow><TableHead className="text-slate-400">ID</TableHead><TableHead className="text-slate-400">Subject</TableHead><TableHead className="text-slate-400">Status</TableHead><TableHead className="text-slate-400">Priority</TableHead><TableHead className="text-slate-400">Customer</TableHead><TableHead className="text-slate-400">SLA</TableHead></TableRow></TableHeader>
                  <TableBody>{filteredTickets.map(t => (
                    <TableRow key={t.ticket_id} className="cursor-pointer hover:bg-slate-700" onClick={() => setSelectedId(t.ticket_id)}>
                      <TableCell className="font-mono text-xs text-white">{t.ticket_id}</TableCell>
                      <TableCell className="text-white font-medium">{t.subject?.substring(0, 60)}</TableCell>
                      <TableCell><Badge className={t.status === 'open' ? 'bg-blue-600' : t.status === 'resolved' ? 'bg-green-600' : t.status === 'in_progress' ? 'bg-yellow-600' : 'bg-slate-600'}>{t.status}</Badge></TableCell>
                      <TableCell><TicketPriorityBadge priority={t.priority} /></TableCell>
                      <TableCell className="text-slate-300 text-sm">{t.customer_name || t.customer_id}</TableCell>
                      <TableCell>{t.sla_breached ? <Badge className="bg-red-600">Breached</Badge> : <Badge className="bg-green-600">OK</Badge>}</TableCell>
                    </TableRow>
                  ))}</TableBody></Table>
              </CardContent></Card>
          </div>
          <div className="space-y-4">
            {showCreate && <CreateTicketForm onCreated={fetchData} />}
          </div>
        </div>
      )}
      {tab === 'sla' && (
        <div className="space-y-4">
          <div className="grid grid-cols-3 gap-4">
            <Card className="bg-slate-800 border-slate-700"><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">SLA Met</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-green-400">{stats.sla_met || 0}</div></CardContent></Card>
            <Card className="bg-slate-800 border-slate-700"><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">SLA Breached</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-red-400">{stats.sla_breaches || 0}</div></CardContent></Card>
            <Card className="bg-slate-800 border-slate-700"><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Compliance</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-blue-400">{stats.sla_compliance_pct || 0}%</div></CardContent></Card>
          </div>
          {stats.by_priority && (
            <Card className="bg-slate-800 border-slate-700"><CardHeader><CardTitle className="text-white">SLA by Priority</CardTitle></CardHeader>
              <CardContent><div className="space-y-2">{(Object.entries(stats.by_priority)).map(([p, data]: [string, any]) => (
                <div key={p} className="flex items-center justify-between p-2 bg-slate-700 rounded">
                  <Badge className={p === 'critical' ? 'bg-red-600' : p === 'high' ? 'bg-orange-600' : p === 'medium' ? 'bg-yellow-600' : 'bg-green-600'}>{p}</Badge>
                  <span className="text-sm text-white">{data.sla_met || 0}/{data.total || 0} met</span>
                </div>
              ))}</div></CardContent></Card>
          )}
        </div>
      )}
      {selectedId && <TicketDetailModal ticketId={selectedId} onClose={() => setSelectedId(null)} />}
    </div>
  );
}