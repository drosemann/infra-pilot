import { useState, useEffect, useCallback } from 'react';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { MessageCircle, TrendingUp, Activity, Search, RefreshCw, AlertTriangle, ThumbsUp, ThumbsDown, PlusCircle, Award, CheckCircle, Clock, Users, BarChart3, BookOpen, Eye, Star, Target, Flag, Settings } from 'lucide-react';

function SentimentBadge({ sentiment }: { sentiment: string }) {
  const colors: Record<string, string> = { positive: 'bg-green-600', neutral: 'bg-yellow-600', negative: 'bg-red-600', mixed: 'bg-blue-600' };
  return <Badge className={colors[sentiment] || 'bg-slate-600'}>{sentiment}</Badge>;
}

function SentimentProfileModal({ customerId, onClose }: { customerId: string; onClose: () => void }) {
  const [profile, setProfile] = useState<any>(null);
  useEffect(() => {
    fetch(`/api/v1/cx/sentiment/${customerId}`).then(r => r.json()).then(setProfile).catch(() => setProfile(null));
  }, [customerId]);
  if (!profile) return null;
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-slate-800 rounded-lg p-6 w-[500px] border border-slate-700" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-start justify-between mb-4">
          <div><h3 className="text-lg font-bold text-white">Sentiment Profile</h3><p className="text-sm text-slate-400">{customerId}</p></div>
          <SentimentBadge sentiment={profile.overall_sentiment || 'neutral'} />
        </div>
        <div className="grid grid-cols-2 gap-3 mb-4">
          <div><p className="text-xs text-slate-400">Score</p><p className="text-2xl font-bold text-white">{profile.overall_score ? (profile.overall_score * 100).toFixed(0) : 0}%</p></div>
          <div><p className="text-xs text-slate-400">Trend</p><p className="text-white">{profile.trend || 'stable'}</p></div>
          <div><p className="text-xs text-slate-400">Risk Level</p><HealthBadge risk={profile.risk_level} /></div>
          <div><p className="text-xs text-slate-400">Interactions</p><p className="text-white">{profile.interaction_count || profile.recent_interactions?.length || 0}</p></div>
        </div>
        <Button variant="ghost" className="w-full mt-4 text-slate-400" onClick={onClose}>Close</Button>
      </div>
    </div>
  );
}

function HealthBadge({ risk }: { risk: string }) {
  const colors: Record<string, string> = { critical: 'bg-red-600', high: 'bg-orange-600', medium: 'bg-yellow-600', low: 'bg-green-600' };
  return <Badge className={colors[risk] || 'bg-slate-600'}>{risk}</Badge>;
}

export function SentimentAnalysisPage() {
  const [alerts, setAlerts] = useState<any[]>([]);
  const [distribution, setDistribution] = useState<any>({});
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [search, setSearch] = useState('');

  const fetchData = useCallback(() => {
    fetch('/api/v1/cx/sentiment/alerts').then(r => r.json()).then(d => setAlerts(d.alerts || [])).catch(() => {});
    fetch('/api/v1/cx/sentiment/distribution').then(r => r.json()).then(setDistribution).catch(() => {});
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const filteredAlerts = alerts.filter((a: any) => {
    if (search && !a.customer_id?.toLowerCase().includes(search.toLowerCase()) && !a.customer_name?.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div><h1 className="text-3xl font-bold text-white mb-2">Sentiment Analysis</h1><p className="text-slate-400">NLP sentiment analysis on support conversations and feedback</p></div>
        <Button onClick={fetchData} variant="outline" className="text-slate-400"><RefreshCw className="mr-2 h-4 w-4" /> Refresh</Button>
      </div>
      <div className="grid grid-cols-4 gap-4">
        <Card className="bg-slate-800 border-slate-700"><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">At Risk</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-red-400">{alerts.length}</div></CardContent></Card>
        <Card className="bg-slate-800 border-slate-700"><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Positive</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-green-400">{distribution.positive || 0}</div></CardContent></Card>
        <Card className="bg-slate-800 border-slate-700"><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Neutral</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-yellow-400">{distribution.neutral || 0}</div></CardContent></Card>
        <Card className="bg-slate-800 border-slate-700"><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Negative</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-red-400">{distribution.negative || 0}</div></CardContent></Card>
      </div>
      <Card className="bg-slate-800 border-slate-700"><CardHeader><CardTitle className="text-white">Sentiment Alerts ({filteredAlerts.length})</CardTitle></CardHeader>
        <CardContent>
          <div className="flex gap-3 items-center mb-4">
            <div className="relative flex-1"><Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <Input className="pl-9 bg-slate-700 border-slate-600 text-white" placeholder="Search by customer..." value={search} onChange={(e) => setSearch(e.target.value)} /></div>
          </div>
          <Table><TableHeader><TableRow><TableHead className="text-slate-400">Customer</TableHead><TableHead className="text-slate-400">Sentiment</TableHead><TableHead className="text-slate-400">Risk</TableHead><TableHead className="text-slate-400">Trend</TableHead><TableHead className="text-slate-400">Message</TableHead><TableHead className="text-slate-400">Actions</TableHead></TableRow></TableHeader>
            <TableBody>{filteredAlerts.length === 0 ? <TableRow><TableCell colSpan={6} className="text-slate-400 text-center">No alerts</TableCell></TableRow> : filteredAlerts.slice(0, 20).map((a: any, i: number) => (
              <TableRow key={i} className="hover:bg-slate-700">
                <TableCell className="text-white cursor-pointer hover:text-blue-400" onClick={() => setSelectedId(a.customer_id)}>{a.customer_name || a.customer_id}</TableCell>
                <TableCell><SentimentBadge sentiment={a.overall_sentiment || 'neutral'} /></TableCell>
                <TableCell><HealthBadge risk={a.risk_level} /></TableCell>
                <TableCell className="text-slate-300">{a.trend}</TableCell>
                <TableCell className="text-slate-400 text-sm">{a.message}</TableCell>
                <TableCell><Button size="sm" variant="ghost" className="text-blue-400" onClick={() => setSelectedId(a.customer_id)}>Profile</Button></TableCell>
              </TableRow>
            ))}</TableBody></Table>
        </CardContent></Card>
      {selectedId && <SentimentProfileModal customerId={selectedId} onClose={() => setSelectedId(null)} />}
    </div>
  );
}

function FeatureTrendCard({ trend }: { trend: any }) {
  if (!trend?.length) return <p className="text-sm text-slate-400">No feature trend data available</p>;
  return (
    <div className="space-y-2">{trend.map((f: any, i: number) => (
      <div key={i} className="flex items-center justify-between p-2 bg-slate-800 rounded">
        <div className="flex items-center gap-2"><Star className="h-4 w-4 text-yellow-400" /><span className="text-sm text-white">{f.feature_name || f.name}</span></div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-slate-400">{f.usage_count || f.count} uses</span>
          <Badge className={f.trend === 'up' ? 'bg-green-600' : f.trend === 'down' ? 'bg-red-600' : 'bg-yellow-600'}>{f.trend || 'stable'}</Badge>
        </div>
      </div>
    ))}</div>
  );
}

export function AdoptionAnalyticsPage() {
  const [summary, setSummary] = useState<any>({});
  const [features, setFeatures] = useState<any[]>([]);
  const [funnel, setFunnel] = useState<any[]>([]);
  const [tab, setTab] = useState<'segments' | 'features' | 'funnel'>('segments');

  const fetchData = useCallback(() => {
    fetch('/api/v1/cx/adoption/segments').then(r => r.json()).then(setSummary).catch(() => {});
    fetch('/api/v1/cx/adoption/features').then(r => r.json()).then(d => setFeatures(d.features || d)).catch(() => {});
    fetch('/api/v1/cx/adoption/funnel').then(r => r.json()).then(d => setFunnel(d.funnel || d)).catch(() => {});
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div><h1 className="text-3xl font-bold text-white mb-2">Adoption Analytics</h1><p className="text-slate-400">Feature usage tracking, onboarding funnel analysis, and time-to-value metrics</p></div>
        <Button onClick={fetchData} variant="outline" className="text-slate-400"><RefreshCw className="mr-2 h-4 w-4" /> Refresh</Button>
      </div>
      <div className="flex space-x-2 border-b border-slate-700 pb-2">
        <Button variant={tab === 'segments' ? 'default' : 'ghost'} onClick={() => setTab('segments')}><Users className="mr-2 h-4 w-4" /> Segments</Button>
        <Button variant={tab === 'features' ? 'default' : 'ghost'} onClick={() => setTab('features')}><Star className="mr-2 h-4 w-4" /> Feature Usage</Button>
        <Button variant={tab === 'funnel' ? 'default' : 'ghost'} onClick={() => setTab('funnel')}><Target className="mr-2 h-4 w-4" /> Funnel</Button>
      </div>
      {tab === 'segments' && (
        <div className="space-y-4">
          <div className="grid grid-cols-3 gap-4">
            {Object.entries(summary).map(([k, v]: [string, any]) => (
              <Card key={k} className="bg-slate-800 border-slate-700">
                <CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400 capitalize">{k.replace(/_/g, ' ')}</CardTitle></CardHeader>
                <CardContent><div className="text-2xl font-bold text-white">{v.count ?? v.pct ?? v ?? 0}</div>{v.pct ? <p className="text-xs text-slate-400">{v.pct}%</p> : null}</CardContent>
              </Card>
            ))}
          </div>
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader><CardTitle className="text-white">Segment Breakdown</CardTitle></CardHeader>
            <CardContent><p className="text-sm text-slate-400">Customer segments by adoption level. Power users drive highest engagement while dormant users need re-engagement campaigns.</p></CardContent>
          </Card>
        </div>
      )}
      {tab === 'features' && (
        <Card className="bg-slate-800 border-slate-700"><CardHeader><CardTitle className="flex items-center gap-2 text-white"><BarChart3 className="h-4 w-4 text-blue-400" /> Feature Usage Trends ({features.length})</CardTitle></CardHeader>
          <CardContent><FeatureTrendCard trend={features} /></CardContent></Card>
      )}
      {tab === 'funnel' && (
        <Card className="bg-slate-800 border-slate-700"><CardHeader><CardTitle className="flex items-center gap-2 text-white"><Target className="h-4 w-4 text-green-400" /> Adoption Funnel</CardTitle></CardHeader>
          <CardContent><div className="space-y-3">{funnel.length === 0 ? <p className="text-sm text-slate-400">No funnel data available</p> : funnel.map((s: any, i: number) => (
            <div key={i}>
              <div className="flex items-center justify-between mb-1"><span className="text-sm text-white">{s.stage_name || s.stage}</span><span className="text-xs text-slate-400">{s.count || 0} ({s.conversion_rate || 0}%)</span></div>
              <div className="w-full h-3 bg-slate-700 rounded overflow-hidden"><div className="h-full bg-blue-500 rounded transition-all" style={{ width: `${s.conversion_rate || 0}%` }} /></div>
            </div>
          ))}</div></CardContent></Card>
      )}
    </div>
  );
}

function MilestoneCard({ milestones }: { milestones: any[] }) {
  if (!milestones?.length) return <p className="text-sm text-slate-400">No milestones defined</p>;
  return (
    <div className="space-y-2">{milestones.map((m: any, i: number) => (
      <div key={i} className="flex items-center justify-between p-2 bg-slate-800 rounded border border-slate-700">
        <div className="flex items-center gap-2">{m.achieved ? <CheckCircle className="h-4 w-4 text-green-400" /> : <Clock className="h-4 w-4 text-slate-400" />}
          <span className="text-sm text-white">{m.name || m.title}</span></div>
        <Badge className={m.achieved ? 'bg-green-600' : 'bg-slate-600'}>{m.achieved ? 'Achieved' : 'Pending'}</Badge>
      </div>
    ))}</div>
  );
}

function StepBreakdownTable({ steps }: { steps: any[] }) {
  if (!steps?.length) return <p className="text-sm text-slate-400">No step data</p>;
  return (
    <Table><TableHeader><TableRow><TableHead className="text-slate-400">Step</TableHead><TableHead className="text-slate-400">Completions</TableHead><TableHead className="text-slate-400">Drop-off</TableHead><TableHead className="text-slate-400">Avg Time</TableHead></TableRow></TableHeader>
      <TableBody>{steps.map((s: any, i: number) => (
        <TableRow key={i}>
          <TableCell className="text-white">{s.step_name || `Step ${i + 1}`}</TableCell>
          <TableCell className="text-white">{s.completion_count || 0}</TableCell>
          <TableCell className="text-red-400">{s.drop_off_rate || 0}%</TableCell>
          <TableCell className="text-slate-400">{s.avg_time_seconds ? `${s.avg_time_seconds}s` : '-'}</TableCell>
        </TableRow>
      ))}</TableBody></Table>
  );
}

export function OnboardingWizardPage() {
  const [stats, setStats] = useState<any>({});
  const [sessions, setSessions] = useState<any[]>([]);
  const [stuck, setStuck] = useState<any[]>([]);
  const [milestones, setMilestones] = useState<any[]>([]);
  const [stepBreakdown, setStepBreakdown] = useState<any[]>([]);
  const [tab, setTab] = useState<'sessions' | 'steps' | 'milestones'>('sessions');
  const [search, setSearch] = useState('');

  const fetchData = useCallback(() => {
    fetch('/api/v1/cx/onboarding/stats').then(r => r.json()).then(setStats).catch(() => {});
    fetch('/api/v1/cx/onboarding/sessions').then(r => r.json()).then(d => setSessions(d.sessions || [])).catch(() => {});
    fetch('/api/v1/cx/onboarding/sessions/stuck').then(r => r.json()).then(d => setStuck(d.sessions || [])).catch(() => {});
    fetch('/api/v1/cx/onboarding/milestones').then(r => r.json()).then(d => setMilestones(d.milestones || d)).catch(() => {});
    fetch('/api/v1/cx/onboarding/steps').then(r => r.json()).then(d => setStepBreakdown(d.steps || d)).catch(() => {});
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const filteredSessions = sessions.filter((s: any) => {
    if (search && !s.customer_id?.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div><h1 className="text-3xl font-bold text-white mb-2">Onboarding Wizard</h1><p className="text-slate-400">Step-by-step guided onboarding with progress tracking and milestone celebrations</p></div>
        <Button onClick={fetchData} variant="outline" className="text-slate-400"><RefreshCw className="mr-2 h-4 w-4" /> Refresh</Button>
      </div>
      {stats.total_sessions > 0 && (
        <div className="grid grid-cols-4 gap-4">
          <Card className="bg-slate-800 border-slate-700"><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Total Sessions</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-white">{stats.total_sessions}</div></CardContent></Card>
          <Card className="bg-slate-800 border-slate-700"><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Completed</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-green-400">{stats.completed || 0}</div></CardContent></Card>
          <Card className="bg-slate-800 border-slate-700"><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Completion Rate</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-blue-400">{stats.completion_rate || 0}%</div></CardContent></Card>
          <Card className="bg-slate-800 border-slate-700"><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Avg TTV</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-white">{stats.avg_time_to_value_days || '-'} days</div></CardContent></Card>
        </div>
      )}
      <div className="flex space-x-2 border-b border-slate-700 pb-2">
        <Button variant={tab === 'sessions' ? 'default' : 'ghost'} onClick={() => setTab('sessions')}><Users className="mr-2 h-4 w-4" /> Sessions</Button>
        <Button variant={tab === 'steps' ? 'default' : 'ghost'} onClick={() => setTab('steps')}><Flag className="mr-2 h-4 w-4" /> Steps</Button>
        <Button variant={tab === 'milestones' ? 'default' : 'ghost'} onClick={() => setTab('milestones')}><Award className="mr-2 h-4 w-4" /> Milestones</Button>
      </div>
      {tab === 'milestones' && (
        <Card className="bg-slate-800 border-slate-700"><CardHeader><CardTitle className="flex items-center gap-2 text-white"><Award className="h-4 w-4 text-yellow-400" /> Onboarding Milestones</CardTitle></CardHeader>
          <CardContent><MilestoneCard milestones={milestones} /></CardContent></Card>
      )}
      {tab === 'steps' && (
        <Card className="bg-slate-800 border-slate-700"><CardHeader><CardTitle className="flex items-center gap-2 text-white"><Flag className="h-4 w-4 text-blue-400" /> Step Completion Breakdown</CardTitle></CardHeader>
          <CardContent><StepBreakdownTable steps={stepBreakdown} /></CardContent></Card>
      )}
      {stuck.length > 0 && (
        <Card className="bg-slate-800 border-slate-700 border-orange-700">
          <CardHeader><CardTitle className="flex items-center gap-2 text-orange-400"><AlertTriangle className="h-4 w-4" /> Stuck Sessions ({stuck.length})</CardTitle></CardHeader>
          <CardContent><div className="space-y-2">{stuck.slice(0, 5).map((s: any, i: number) => (
            <div key={i} className="flex items-center justify-between p-2 bg-slate-700 rounded">
              <span className="text-white text-sm">{s.customer_id}</span>
              <span className="text-slate-400 text-xs">{s.overall_progress}% complete - last activity: {s.last_activity ? new Date(s.last_activity).toLocaleDateString() : 'N/A'}</span>
            </div>
          ))}</div></CardContent></Card>
      )}
      {tab === 'sessions' && (
        <Card className="bg-slate-800 border-slate-700"><CardHeader><CardTitle className="text-white">Sessions ({filteredSessions.length})</CardTitle></CardHeader>
          <CardContent>
            <div className="flex gap-3 items-center mb-4">
              <div className="relative flex-1"><Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                <Input className="pl-9 bg-slate-700 border-slate-600 text-white" placeholder="Search by customer ID..." value={search} onChange={(e) => setSearch(e.target.value)} /></div>
            </div>
            <Table><TableHeader><TableRow><TableHead className="text-slate-400">Customer</TableHead><TableHead className="text-slate-400">Status</TableHead><TableHead className="text-slate-400">Progress</TableHead><TableHead className="text-slate-400">Steps</TableHead><TableHead className="text-slate-400">Last Activity</TableHead></TableRow></TableHeader>
              <TableBody>{filteredSessions.map((s: any) => (
                <TableRow key={s.session_id || s.customer_id}>
                  <TableCell className="text-white">{s.customer_id}</TableCell>
                  <TableCell><Badge className={s.status === 'completed' ? 'bg-green-600' : s.status === 'in_progress' ? 'bg-blue-600' : 'bg-yellow-600'}>{s.status}</Badge></TableCell>
                  <TableCell className="text-white">{s.overall_progress || 0}%</TableCell>
                  <TableCell className="text-white">{s.completed_steps || 0}/{s.total_steps || 0}</TableCell>
                  <TableCell className="text-slate-400 text-sm">{s.last_activity ? new Date(s.last_activity).toLocaleDateString() : 'N/A'}</TableCell>
                </TableRow>
              ))}</TableBody></Table>
          </CardContent></Card>
      )}
    </div>
  );
}