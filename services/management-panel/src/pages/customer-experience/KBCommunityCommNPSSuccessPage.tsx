import { useState, useEffect, useCallback } from 'react';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Search, BookOpen, Users, MessageCircle, Megaphone, Star, Zap, RefreshCw, PlusCircle, ThumbsUp, ThumbsDown, Clock, Shield, Award, TrendingUp, Activity, CheckCircle, BarChart3, Filter, Flag, Tag, Mail, Phone, Globe, Settings } from 'lucide-react';

export function KnowledgeBasePage() {
  const [articles, setArticles] = useState<any[]>([]);
  const [categories, setCategories] = useState<any>({});
  const [searchQuery, setSearchQuery] = useState('');
  const [results, setResults] = useState<any[]>([]);

  const fetchData = useCallback(() => {
    fetch('/api/v1/cx/kb/popular').then(r => r.json()).then(d => setArticles(d.articles || [])).catch(() => {});
    fetch('/api/v1/cx/kb/categories').then(r => r.json()).then(setCategories).catch(() => {});
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const search = async () => {
    if (!searchQuery) return;
    try { const r = await fetch(`/api/v1/cx/knowledge-base/search?q=${encodeURIComponent(searchQuery)}`); const d = await r.json(); setResults(d.results || []); } catch { toast.error('Search failed'); }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div><h1 className="text-3xl font-bold text-white mb-2">Knowledge Base</h1><p className="text-slate-400">Searchable help center with articles, videos, and FAQs</p></div>
        <Button onClick={fetchData} variant="outline" className="text-slate-400"><RefreshCw className="mr-2 h-4 w-4" /> Refresh</Button>
      </div>
      <div className="flex gap-2"><Input className="bg-slate-800 border-slate-700 text-white max-w-md" placeholder="Search knowledge base..." value={searchQuery} onChange={e => setSearchQuery(e.target.value)} onKeyDown={e => e.key === 'Enter' && search()} />
        <Button onClick={search} className="bg-blue-600 hover:bg-blue-700"><Search className="mr-2 h-4 w-4" /> Search</Button></div>
      {results.length > 0 && (
        <Card className="bg-slate-800 border-slate-700">
          <CardHeader><CardTitle className="text-white">Search Results ({results.length})</CardTitle></CardHeader>
          <CardContent><div className="space-y-2">{results.map((r: any) => (
            <div key={r.article_id || r.id} className="p-3 bg-slate-700 rounded cursor-pointer hover:bg-slate-600">
              <p className="text-white font-medium">{r.title}</p>
              <p className="text-xs text-slate-400">{r.excerpt?.substring(0, 120) || r.summary?.substring(0, 120)}</p>
            </div>
          ))}</div></CardContent></Card>
      )}
      <div className="grid grid-cols-4 gap-4">
        {Object.entries(categories).map(([k, v]: [string, any]) => (
          <Card key={k} className="bg-slate-800 border-slate-700">
            <CardHeader className="pb-2"><CardTitle className="text-sm text-white capitalize">{k.replace(/_/g, ' ')}</CardTitle></CardHeader>
            <CardContent><div className="text-2xl font-bold text-white">{typeof v === 'number' ? v : v.count || v.article_count || 0}</div><p className="text-xs text-slate-400">articles</p></CardContent>
          </Card>
        ))}
      </div>
      {articles.length > 0 && (
        <Card className="bg-slate-800 border-slate-700"><CardHeader><CardTitle className="text-white">Popular Articles</CardTitle></CardHeader>
          <CardContent><Table><TableHeader><TableRow><TableHead className="text-slate-400">Title</TableHead><TableHead className="text-slate-400">Views</TableHead><TableHead className="text-slate-400">Helpful</TableHead><TableHead className="text-slate-400">Status</TableHead></TableRow></TableHeader>
            <TableBody>{articles.slice(0, 10).map((a: any) => (
              <TableRow key={a.article_id || a.id}>
                <TableCell className="text-white font-medium">{a.title}</TableCell>
                <TableCell className="text-white">{a.view_count || 0}</TableCell>
                <TableCell className="text-white">{a.helpful_votes || a.helpfulness || 0}</TableCell>
                <TableCell><Badge className={a.status === 'published' ? 'bg-green-600' : 'bg-yellow-600'}>{a.status || 'published'}</Badge></TableCell>
              </TableRow>
            ))}</TableBody></Table></CardContent></Card>
      )}
    </div>
  );
}

function CommunityCategoryCard({ categories }: { categories: any }) {
  if (!categories || Object.keys(categories).length === 0) return <p className="text-sm text-slate-400">No category data</p>;
  return (
    <div className="space-y-2">{(Object.entries(categories)).map(([cat, data]: [string, any]) => (
      <div key={cat} className="flex items-center justify-between p-2 bg-slate-700 rounded">
        <div className="flex items-center gap-2"><Tag className="h-4 w-4 text-blue-400" /><span className="text-sm text-white capitalize">{cat.replace(/_/g, ' ')}</span></div>
        <span className="text-sm text-slate-400">{typeof data === 'number' ? `${data} posts` : `${data.count || 0} posts`}</span>
      </div>
    ))}</div>
  );
}

export function CommunityPlatformPage() {
  const [posts, setPosts] = useState<any[]>([]);
  const [leaderboard, setLeaderboard] = useState<any[]>([]);
  const [categories, setCategories] = useState<any>({});
  const [tab, setTab] = useState<'posts' | 'leaderboard' | 'categories'>('posts');

  const fetchData = useCallback(() => {
    fetch('/api/v1/cx/community/posts').then(r => r.json()).then(d => setPosts(d.posts || [])).catch(() => {});
    fetch('/api/v1/cx/community/leaderboard').then(r => r.json()).then(d => setLeaderboard(d.authors || d.leaderboard || [])).catch(() => {});
    fetch('/api/v1/cx/community/categories').then(r => r.json()).then(setCategories).catch(() => {});
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div><h1 className="text-3xl font-bold text-white mb-2">Community Platform</h1><p className="text-slate-400">Forums, feature voting, Q&A, and gamification</p></div>
        <Button onClick={fetchData} variant="outline" className="text-slate-400"><RefreshCw className="mr-2 h-4 w-4" /> Refresh</Button>
      </div>
      <div className="grid grid-cols-4 gap-4">
        <Card className="bg-slate-800 border-slate-700"><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Posts</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-white">{posts.length}</div></CardContent></Card>
        <Card className="bg-slate-800 border-slate-700"><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Authors</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-white">{leaderboard.length}</div></CardContent></Card>
        <Card className="bg-slate-800 border-slate-700"><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Categories</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-white">{Object.keys(categories).length}</div></CardContent></Card>
        <Card className="bg-slate-800 border-slate-700"><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Total Likes</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-white">{posts.reduce((s, p) => s + (p.like_count || p.upvotes || 0), 0)}</div></CardContent></Card>
      </div>
      <div className="flex space-x-2 border-b border-slate-700 pb-2">
        <Button variant={tab === 'posts' ? 'default' : 'ghost'} onClick={() => setTab('posts')}><MessageCircle className="mr-2 h-4 w-4" /> Posts</Button>
        <Button variant={tab === 'leaderboard' ? 'default' : 'ghost'} onClick={() => setTab('leaderboard')}><Award className="mr-2 h-4 w-4" /> Leaderboard</Button>
        <Button variant={tab === 'categories' ? 'default' : 'ghost'} onClick={() => setTab('categories')}><Tag className="mr-2 h-4 w-4" /> Categories</Button>
      </div>
      {tab === 'posts' && (
        <Card className="bg-slate-800 border-slate-700"><CardHeader><CardTitle className="text-white">Recent Posts ({posts.length})</CardTitle></CardHeader>
          <CardContent><div className="space-y-3">{posts.map((p: any) => (
            <div key={p.post_id || p.id} className="p-3 bg-slate-700 rounded">
              <div className="flex items-start gap-3">
                <div className="text-center min-w-[50px]"><div className="text-lg font-bold text-white">{p.like_count || p.upvotes || 0}</div><div className="text-xs text-slate-400">likes</div></div>
                <div className="flex-1"><p className="text-white font-medium">{p.title}</p><p className="text-xs text-slate-400 mt-1">{p.content?.substring(0, 100)}</p>
                  <div className="flex gap-2 mt-2"><Badge variant="outline" className="text-xs">{p.post_type || 'discussion'}</Badge><span className="text-xs text-slate-400">by {p.author_name || p.author_id}</span></div></div>
              </div>
            </div>
          ))}</div></CardContent></Card>
      )}
      {tab === 'leaderboard' && (
        <Card className="bg-slate-800 border-slate-700"><CardHeader><CardTitle className="text-white">Author Leaderboard</CardTitle></CardHeader>
          <CardContent><Table><TableHeader><TableRow><TableHead className="text-slate-400">#</TableHead><TableHead className="text-slate-400">Author</TableHead><TableHead className="text-slate-400">Posts</TableHead><TableHead className="text-slate-400">Comments</TableHead><TableHead className="text-slate-400">Likes</TableHead></TableRow></TableHeader>
            <TableBody>{leaderboard.map((u: any, i: number) => (
              <TableRow key={u.author_id || u.user_id || i}>
                <TableCell className="text-white font-bold">{i + 1}</TableCell>
                <TableCell className="text-white">{u.author_name || u.username || u.author_id}</TableCell>
                <TableCell className="text-white">{u.posts || u.post_count || 0}</TableCell>
                <TableCell className="text-white">{u.comments || 0}</TableCell>
                <TableCell className="text-white">{u.likes || u.total_likes || 0}</TableCell>
              </TableRow>
            ))}</TableBody></Table></CardContent></Card>
      )}
      {tab === 'categories' && (
        <Card className="bg-slate-800 border-slate-700"><CardHeader><CardTitle className="text-white">Community Categories</CardTitle></CardHeader>
          <CardContent><CommunityCategoryCard categories={categories} /></CardContent></Card>
      )}
    </div>
  );
}

export function CommunicationHubPage() {
  const [batches, setBatches] = useState<any[]>([]);
  const [maintenance, setMaintenance] = useState<any[]>([]);
  const [templates, setTemplates] = useState<any[]>([]);
  const [tab, setTab] = useState<'batches' | 'maintenance' | 'templates'>('batches');

  const fetchData = useCallback(() => {
    fetch('/api/v1/cx/communications').then(r => r.json()).then(d => setBatches(d.notifications || d || [])).catch(() => {});
    fetch('/api/v1/cx/communications/maintenance').then(r => r.json()).then(d => setMaintenance(d.windows || d || [])).catch(() => {});
    fetch('/api/v1/cx/communications/templates').then(r => r.json()).then(d => setTemplates(d.templates || [])).catch(() => {});
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div><h1 className="text-3xl font-bold text-white mb-2">Communication Hub</h1><p className="text-slate-400">Broadcast announcements, maintenance notifications, product updates</p></div>
        <Button onClick={fetchData} variant="outline" className="text-slate-400"><RefreshCw className="mr-2 h-4 w-4" /> Refresh</Button>
      </div>
      <div className="grid grid-cols-3 gap-4">
        <Card className="bg-slate-800 border-slate-700"><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Broadcasts</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-white">{batches.length}</div></CardContent></Card>
        <Card className="bg-slate-800 border-slate-700"><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Maintenance Windows</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-white">{maintenance.length}</div></CardContent></Card>
        <Card className="bg-slate-800 border-slate-700"><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Templates</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-white">{templates.length}</div></CardContent></Card>
      </div>
      <div className="flex space-x-2 border-b border-slate-700 pb-2">
        <Button variant={tab === 'batches' ? 'default' : 'ghost'} onClick={() => setTab('batches')}><Megaphone className="mr-2 h-4 w-4" /> Broadcasts</Button>
        <Button variant={tab === 'maintenance' ? 'default' : 'ghost'} onClick={() => setTab('maintenance')}><Clock className="mr-2 h-4 w-4" /> Maintenance</Button>
        <Button variant={tab === 'templates' ? 'default' : 'ghost'} onClick={() => setTab('templates')}><Mail className="mr-2 h-4 w-4" /> Templates</Button>
      </div>
      {tab === 'batches' && (
        <Card className="bg-slate-800 border-slate-700"><CardHeader><CardTitle className="text-white">Broadcasts ({batches.length})</CardTitle></CardHeader>
          <CardContent><Table><TableHeader><TableRow><TableHead className="text-slate-400">Type</TableHead><TableHead className="text-slate-400">Subject</TableHead><TableHead className="text-slate-400">Status</TableHead><TableHead className="text-slate-400">Date</TableHead></TableRow></TableHeader>
            <TableBody>{batches.slice(0, 20).map((b: any, i: number) => (
              <TableRow key={b.notification_id || b.id || i}>
                <TableCell><Badge variant="outline" className="text-xs">{b.notification_type || b.type}</Badge></TableCell>
                <TableCell className="text-white font-medium">{b.subject?.substring(0, 60)}</TableCell>
                <TableCell><Badge className={b.status === 'sent' ? 'bg-green-600' : b.status === 'pending' ? 'bg-yellow-600' : 'bg-slate-600'}>{b.status}</Badge></TableCell>
                <TableCell className="text-slate-400 text-xs">{b.created_at?.substring(0, 10) || b.sent_at?.substring(0, 10) || 'N/A'}</TableCell>
              </TableRow>
            ))}</TableBody></Table></CardContent></Card>
      )}
      {tab === 'maintenance' && (
        <div className="grid grid-cols-2 gap-4">{maintenance.map((m: any, i: number) => (
          <Card key={m.maintenance_id || i} className="bg-slate-800 border-slate-700">
            <CardHeader><CardTitle className="text-white">{m.title}</CardTitle></CardHeader>
            <CardContent>
              <p className="text-sm text-slate-400 mb-2">{m.description}</p>
              <div className="text-xs text-slate-400 space-y-1">
                <p><Clock className="inline h-3 w-3 mr-1" />{m.start_time?.substring(0, 16)} - {m.end_time?.substring(0, 16)}</p>
                <p><Shield className="inline h-3 w-3 mr-1" />{m.affected_services?.join(', ') || 'All services'}</p>
              </div>
              <Badge className="mt-2" variant={m.status === 'scheduled' ? 'default' : 'secondary'}>{m.status}</Badge>
            </CardContent>
          </Card>
        ))}</div>
      )}
      {tab === 'templates' && (
        <Card className="bg-slate-800 border-slate-700"><CardHeader><CardTitle className="text-white">Communication Templates ({templates.length})</CardTitle></CardHeader>
          <CardContent><Table><TableHeader><TableRow><TableHead className="text-slate-400">Name</TableHead><TableHead className="text-slate-400">Type</TableHead><TableHead className="text-slate-400">Channel</TableHead><TableHead className="text-slate-400">Status</TableHead></TableRow></TableHeader>
            <TableBody>{templates.slice(0, 20).map((t: any, i: number) => (
              <TableRow key={t.template_id || i}>
                <TableCell className="text-white font-medium">{t.name}</TableCell>
                <TableCell><Badge variant="outline" className="text-xs">{t.type || t.template_type}</Badge></TableCell>
                <TableCell className="text-white">{t.channel || 'email'}</TableCell>
                <TableCell><Badge className={t.active ? 'bg-green-600' : 'bg-slate-600'}>{t.active ? 'Active' : 'Inactive'}</Badge></TableCell>
              </TableRow>
            ))}</TableBody></Table></CardContent></Card>
      )}
    </div>
  );
}

function NPSSegmentCard({ segments }: { segments: any }) {
  if (!segments || Object.keys(segments).length === 0) return <p className="text-sm text-slate-400">No segment data</p>;
  return (
    <div className="space-y-2">{(Object.entries(segments)).map(([segment, data]: [string, any]) => (
      <div key={segment} className="flex items-center justify-between p-2 bg-slate-700 rounded">
        <span className="text-sm text-white capitalize">{segment.replace(/_/g, ' ')}</span>
        <div className="flex items-center gap-3">
          <span className="text-xs text-slate-400">Score: {typeof data === 'number' ? data : data.score || data.avg_score || 0}</span>
          <Badge className={(typeof data === 'number' ? data : data.score || 0) >= 50 ? 'bg-green-600' : 'bg-yellow-600'}>{(typeof data === 'number' ? data : data.count || 0)}</Badge>
        </div>
      </div>
    ))}</div>
  );
}

export function NPSSurveysPage() {
  const [npsScore, setNpsScore] = useState<any>({});
  const [surveys, setSurveys] = useState<any[]>([]);
  const [trend, setTrend] = useState<any[]>([]);
  const [detractors, setDetractors] = useState<any[]>([]);
  const [segments, setSegments] = useState<any>({});
  const [tab, setTab] = useState<'overview' | 'segments'>('overview');

  const fetchData = useCallback(() => {
    fetch('/api/v1/cx/nps/score').then(r => r.json()).then(setNpsScore).catch(() => {});
    fetch('/api/v1/cx/nps/surveys').then(r => r.json()).then(d => setSurveys(d.surveys || [])).catch(() => {});
    fetch('/api/v1/cx/nps/trend').then(r => r.json()).then(d => setTrend(Array.isArray(d) ? d : [])).catch(() => {});
    fetch('/api/v1/cx/nps/detractors').then(r => r.json()).then(d => setDetractors(d.detractors || [])).catch(() => {});
    fetch('/api/v1/cx/nps/segments').then(r => r.json()).then(d => setSegments(d.segments || d || {})).catch(() => {});
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div><h1 className="text-3xl font-bold text-white mb-2">NPS & Surveys</h1><p className="text-slate-400">Automated NPS surveys at key lifecycle moments</p></div>
        <Button onClick={fetchData} variant="outline" className="text-slate-400"><RefreshCw className="mr-2 h-4 w-4" /> Refresh</Button>
      </div>
      <div className="grid grid-cols-4 gap-4">
        <Card className="bg-slate-800 border-slate-700" style={{ borderLeft: `4px solid ${(npsScore.nps_score ?? 0) >= 0 ? '#22c55e' : '#ef4444'}` }}>
          <CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">NPS Score</CardTitle></CardHeader><CardContent><div className="text-3xl font-bold text-white">{npsScore.nps_score ?? 0}</div></CardContent></Card>
        <Card className="bg-slate-800 border-slate-700"><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Promoters</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-green-400">{npsScore.promoters || 0}</div><div className="text-xs text-slate-400">{npsScore.promoter_pct || 0}%</div></CardContent></Card>
        <Card className="bg-slate-800 border-slate-700"><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Passives</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-yellow-400">{npsScore.passives || 0}</div></CardContent></Card>
        <Card className="bg-slate-800 border-slate-700"><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Detractors</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-red-400">{npsScore.detractors || 0}</div></CardContent></Card>
      </div>
      <div className="flex space-x-2 border-b border-slate-700 pb-2">
        <Button variant={tab === 'overview' ? 'default' : 'ghost'} onClick={() => setTab('overview')}><BarChart3 className="mr-2 h-4 w-4" /> Overview</Button>
        <Button variant={tab === 'segments' ? 'default' : 'ghost'} onClick={() => setTab('segments')}><Users className="mr-2 h-4 w-4" /> Segments</Button>
      </div>
      {tab === 'overview' && (
        <div className="space-y-4">
          {trend.length > 0 && (
            <Card className="bg-slate-800 border-slate-700"><CardHeader><CardTitle className="text-white">NPS Trend</CardTitle></CardHeader>
              <CardContent><div className="grid grid-cols-6 gap-3">{trend.map((t: any) => (
                <div key={t.month} className="text-center p-2 bg-slate-700 rounded">
                  <p className="text-xs text-slate-400">{t.month}</p>
                  <p className="text-lg font-bold text-white">{t.avg_score}</p>
                  <p className="text-xs text-slate-400">{t.responses} resp</p>
                </div>
              ))}</div></CardContent></Card>
          )}
          {detractors.length > 0 && (
            <Card className="bg-slate-800 border-slate-700 border-red-700">
              <CardHeader><CardTitle className="flex items-center gap-2 text-red-400"><ThumbsDown className="h-4 w-4" /> Detractor Feedback ({detractors.length})</CardTitle></CardHeader>
              <CardContent><div className="space-y-2">{detractors.slice(0, 5).map((d: any, i: number) => (
                <div key={i} className="p-2 bg-slate-700 rounded">
                  <p className="text-sm text-white">{d.customer_id}</p>
                  <p className="text-xs text-slate-400">Score: {d.score}</p>
                </div>
              ))}</div></CardContent></Card>
          )}
          <Card className="bg-slate-800 border-slate-700"><CardHeader><CardTitle className="text-white">Surveys ({surveys.length})</CardTitle></CardHeader>
            <CardContent><Table><TableHeader><TableRow><TableHead className="text-slate-400">Title</TableHead><TableHead className="text-slate-400">Type</TableHead><TableHead className="text-slate-400">Status</TableHead><TableHead className="text-slate-400">Responses</TableHead></TableRow></TableHeader>
              <TableBody>{surveys.map((s: any) => (
                <TableRow key={s.survey_id || s.id}>
                  <TableCell className="text-white font-medium">{s.title}</TableCell>
                  <TableCell><Badge variant="outline">{s.survey_type || 'nps'}</Badge></TableCell>
                  <TableCell><Badge className={s.active || s.status === 'active' ? 'bg-green-600' : 'bg-slate-600'}>{s.active || s.status || 'inactive'}</Badge></TableCell>
                  <TableCell className="text-white">{s.response_count || 0}</TableCell>
                </TableRow>
              ))}</TableBody></Table></CardContent></Card>
        </div>
      )}
      {tab === 'segments' && (
        <Card className="bg-slate-800 border-slate-700"><CardHeader><CardTitle className="text-white">NPS by Segment</CardTitle></CardHeader>
          <CardContent><NPSSegmentCard segments={segments} /></CardContent></Card>
      )}
    </div>
  );
}

export function SuccessAutomationPage() {
  const [plays, setPlays] = useState<any[]>([]);
  const [stats, setStats] = useState<any>({});

  const fetchData = useCallback(() => {
    fetch('/api/v1/cx/automation/plays').then(r => r.json()).then(d => setPlays(d.plays || [])).catch(() => {});
    fetch('/api/v1/cx/automation/stats').then(r => r.json()).then(setStats).catch(() => {});
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div><h1 className="text-3xl font-bold text-white mb-2">Success Automation</h1><p className="text-slate-400">Automated success plays and trigger-based workflows</p></div>
        <Button onClick={fetchData} variant="outline" className="text-slate-400"><RefreshCw className="mr-2 h-4 w-4" /> Refresh</Button>
      </div>
      <div className="grid grid-cols-4 gap-4">
        <Card className="bg-slate-800 border-slate-700"><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Total Plays</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-white">{stats.total_plays || plays.length}</div></CardContent></Card>
        <Card className="bg-slate-800 border-slate-700"><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Active</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-green-400">{stats.active_plays || 0}</div></CardContent></Card>
        <Card className="bg-slate-800 border-slate-700"><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Executions</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-white">{stats.total_executions || 0}</div></CardContent></Card>
        <Card className="bg-slate-800 border-slate-700"><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Success Rate</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-blue-400">{stats.success_rate ? `${(stats.success_rate * 100).toFixed(0)}%` : 'N/A'}</div></CardContent></Card>
      </div>
      <Card className="bg-slate-800 border-slate-700"><CardHeader><CardTitle className="text-white">Success Plays ({plays.length})</CardTitle></CardHeader>
        <CardContent><Table><TableHeader><TableRow><TableHead className="text-slate-400">Name</TableHead><TableHead className="text-slate-400">Trigger</TableHead><TableHead className="text-slate-400">Actions</TableHead><TableHead className="text-slate-400">Executions</TableHead><TableHead className="text-slate-400">Status</TableHead></TableRow></TableHeader>
          <TableBody>{plays.map((p: any) => (
            <TableRow key={p.play_id || p.id}>
              <TableCell className="text-white font-medium">{p.name}</TableCell>
              <TableCell><Badge variant="outline" className="text-xs">{p.trigger_event || p.trigger}</Badge></TableCell>
              <TableCell className="text-white">{p.actions?.length || 0}</TableCell>
              <TableCell className="text-white">{p.execution_count || 0}</TableCell>
              <TableCell><Badge className={p.active || p.status === 'active' ? 'bg-green-600' : 'bg-slate-600'}>{p.active || p.status || 'inactive'}</Badge></TableCell>
            </TableRow>
          ))}</TableBody></Table></CardContent></Card>
    </div>
  );
}