import { useState, useEffect } from 'react';
import { Routes, Route, Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { RefreshCw, Activity, Heart, Ticket, MessageCircle, TrendingUp, BookOpen, Users, Megaphone, Star, Zap, Globe, AlertTriangle, CheckCircle, Clock, BarChart3 } from 'lucide-react';
import { HealthScoringPage, TicketingPage } from './HealthAndTicketingPage';
import { SentimentAnalysisPage, AdoptionAnalyticsPage, OnboardingWizardPage } from './SentimentAdoptionOnboardingPage';
import { KnowledgeBasePage, CommunityPlatformPage, CommunicationHubPage, NPSSurveysPage, SuccessAutomationPage } from './KBCommunityCommNPSSuccessPage';

export function CustomerExperienceRoutes() {
  return (
    <Routes>
      <Route path="health" element={<HealthScoringPage />} />
      <Route path="tickets" element={<TicketingPage />} />
      <Route path="sentiment" element={<SentimentAnalysisPage />} />
      <Route path="adoption" element={<AdoptionAnalyticsPage />} />
      <Route path="onboarding" element={<OnboardingWizardPage />} />
      <Route path="knowledge-base" element={<KnowledgeBasePage />} />
      <Route path="community" element={<CommunityPlatformPage />} />
      <Route path="communication" element={<CommunicationHubPage />} />
      <Route path="nps" element={<NPSSurveysPage />} />
      <Route path="success" element={<SuccessAutomationPage />} />
      <Route index element={<CustomerExperienceDashboard />} />
    </Routes>
  );
}

const icons: Record<string, any> = { health: Heart, tickets: Ticket, sentiment: MessageCircle, adoption: TrendingUp, onboarding: Activity, 'knowledge-base': BookOpen, community: Users, communication: Megaphone, nps: Star, success: Zap };

function CustomerExperienceDashboard() {
  const [stats, setStats] = useState<any>({});
  const [recentActivity, setRecentActivity] = useState<any[]>([]);

  useEffect(() => {
    Promise.all([
      fetch('/api/v1/cx/health/stats').then(r => r.json()).catch(() => ({})),
      fetch('/api/v1/cx/tickets/stats').then(r => r.json()).catch(() => ({})),
      fetch('/api/v1/cx/sentiment/alerts').then(r => r.json()).catch(() => ({})),
      fetch('/api/v1/cx/nps/score').then(r => r.json()).catch(() => ({})),
      fetch('/api/v1/cx/success/stats').then(r => r.json()).catch(() => ({})),
      fetch('/api/v1/cx/activity').then(r => r.json()).catch(() => ({})),
    ]).then(([health, tickets, sentiment, nps, success, activity]) => {
      setStats({ health, tickets, sentiment, nps, success });
      setRecentActivity(activity.recent || activity.events || []);
    });
  }, []);

  const cards = [
    { label: 'Health Profiles', value: stats.health?.total_customers ?? 0, path: 'health', desc: `${stats.health?.at_risk_count ?? 0} at risk` },
    { label: 'Support Tickets', value: stats.tickets?.total_tickets ?? 0, path: 'tickets', desc: `${stats.tickets?.open_tickets ?? 0} open` },
    { label: 'Sentiment Alerts', value: stats.sentiment?.alerts?.length ?? 0, path: 'sentiment', desc: 'active alerts' },
    { label: 'Adoption Rate', value: 'N/A', path: 'adoption', desc: 'feature usage' },
    { label: 'Onboarding', value: 'N/A', path: 'onboarding', desc: 'session tracking' },
    { label: 'KB Articles', value: 'N/A', path: 'knowledge-base', desc: 'help center' },
    { label: 'Community Posts', value: 'N/A', path: 'community', desc: 'discussions' },
    { label: 'Broadcasts', value: 'N/A', path: 'communication', desc: 'notifications' },
    { label: 'NPS Score', value: stats.nps?.nps_score ?? 0, path: 'nps', desc: `${stats.nps?.total_responses ?? 0} responses` },
    { label: 'Success Plays', value: stats.success?.total_plays ?? 0, path: 'success', desc: `${stats.success?.active_plays ?? 0} active` },
  ];

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Globe className="h-8 w-8 text-blue-500" />
          <div><h1 className="text-3xl font-bold tracking-tight text-white">Customer Experience</h1><p className="text-slate-400">Customer health, support, sentiment, adoption, and success automation</p></div>
        </div>
        <Button variant="outline" className="text-slate-400" onClick={() => window.location.reload()}><RefreshCw className="mr-2 h-4 w-4" /> Refresh</Button>
      </div>
      {stats.health?.average_score && (
        <div className="grid grid-cols-5 gap-4 mb-6">
          <Card className="bg-slate-800 border-slate-700"><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Avg Health Score</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-white">{stats.health?.average_score ?? 0}</div></CardContent></Card>
          <Card className="bg-slate-800 border-slate-700"><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Open Tickets</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-yellow-400">{stats.tickets?.open_tickets ?? 0}</div></CardContent></Card>
          <Card className="bg-slate-800 border-slate-700"><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Sentiment Alerts</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-red-400">{stats.sentiment?.alerts?.length ?? 0}</div></CardContent></Card>
          <Card className="bg-slate-800 border-slate-700"><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">NPS Score</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-blue-400">{stats.nps?.nps_score ?? 0}</div></CardContent></Card>
          <Card className="bg-slate-800 border-slate-700"><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">SLA Breaches</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-red-400">{stats.tickets?.sla_breaches ?? 0}</div></CardContent></Card>
        </div>
      )}
      <div className="grid grid-cols-5 gap-4">
        {cards.map(c => {
          const Icon = icons[c.path] || Activity;
          return (
            <Link key={c.path} to={`/customer-experience/${c.path}`} className="block">
              <Card className="bg-slate-800 border-slate-700 hover:border-blue-500 cursor-pointer transition-colors">
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm text-slate-300">{c.label}</CardTitle>
                    <Icon className="h-5 w-5 text-blue-400" />
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-white">{c.value}</div>
                  <p className="text-xs text-slate-400 mt-1">{c.desc}</p>
                </CardContent>
              </Card>
            </Link>
          );
        })}
      </div>
      <Card className="bg-slate-800 border-slate-700">
        <CardHeader><CardTitle className="text-white">Quick Actions</CardTitle></CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          <Link to="/customer-experience/tickets"><Button className="bg-blue-600 hover:bg-blue-700"><Ticket className="mr-2 h-4 w-4" /> View Tickets</Button></Link>
          <Link to="/customer-experience/health"><Button className="bg-green-600 hover:bg-green-700"><Heart className="mr-2 h-4 w-4" /> Health Check</Button></Link>
          <Link to="/customer-experience/nps"><Button className="bg-purple-600 hover:bg-purple-700"><Star className="mr-2 h-4 w-4" /> NPS Dashboard</Button></Link>
          <Link to="/customer-experience/communication"><Button className="bg-orange-600 hover:bg-orange-700"><Megaphone className="mr-2 h-4 w-4" /> Send Broadcast</Button></Link>
          <Link to="/customer-experience/success"><Button className="bg-indigo-600 hover:bg-indigo-700"><Zap className="mr-2 h-4 w-4" /> Success Plays</Button></Link>
        </CardContent>
      </Card>
      {recentActivity.length > 0 && (
        <Card className="bg-slate-800 border-slate-700">
          <CardHeader><CardTitle className="flex items-center gap-2 text-white"><Clock className="h-4 w-4 text-blue-400" /> Recent Activity</CardTitle></CardHeader>
          <CardContent>
            <Table><TableHeader><TableRow><TableHead className="text-slate-400">Time</TableHead><TableHead className="text-slate-400">Type</TableHead><TableHead className="text-slate-400">Description</TableHead><TableHead className="text-slate-400">Status</TableHead></TableRow></TableHeader>
              <TableBody>{recentActivity.slice(0, 10).map((a: any, i: number) => (
                <TableRow key={i}>
                  <TableCell className="text-xs text-slate-400">{a.timestamp ? new Date(a.timestamp).toLocaleString() : 'N/A'}</TableCell>
                  <TableCell><Badge variant="outline" className="text-xs">{a.type || a.event_type}</Badge></TableCell>
                  <TableCell className="text-sm text-white">{a.description || a.message}</TableCell>
                  <TableCell>{a.status === 'success' || a.status === 'completed' ? <CheckCircle className="h-4 w-4 text-green-400" /> : a.status === 'failed' ? <AlertTriangle className="h-4 w-4 text-red-400" /> : <Clock className="h-4 w-4 text-yellow-400" />}</TableCell>
                </TableRow>
              ))}</TableBody></Table>
          </CardContent></Card>
      )}
      <div className="grid grid-cols-2 gap-4">
        <Card className="bg-slate-800 border-slate-700">
          <CardHeader><CardTitle className="flex items-center gap-2 text-sm text-white"><BarChart3 className="h-4 w-4 text-green-400" /> SLA Compliance</CardTitle></CardHeader>
          <CardContent>
            <div className="flex items-center justify-between mb-2"><span className="text-sm text-slate-400">Met</span><span className="text-white font-bold">{stats.tickets?.sla_met ?? 0}</span></div>
            <div className="flex items-center justify-between mb-2"><span className="text-sm text-slate-400">Breached</span><span className="text-red-400 font-bold">{stats.tickets?.sla_breaches ?? 0}</span></div>
            <div className="flex items-center justify-between"><span className="text-sm text-slate-400">Compliance Rate</span><span className="text-green-400 font-bold">{stats.tickets?.sla_compliance_pct ?? 0}%</span></div>
          </CardContent></Card>
        <Card className="bg-slate-800 border-slate-700">
          <CardHeader><CardTitle className="flex items-center gap-2 text-sm text-white"><Activity className="h-4 w-4 text-blue-400" /> Category Distribution</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-2">{(Object.entries(stats.tickets?.by_category || {})).map(([cat, count]: [string, any]) => (
              <div key={cat} className="flex items-center justify-between"><span className="text-sm text-slate-400 capitalize">{cat}</span><Badge>{count}</Badge></div>
            )) || <p className="text-sm text-slate-400">No data</p>}</div>
          </CardContent></Card>
      </div>
      <Card className="bg-slate-800 border-slate-700">
        <CardHeader><CardTitle className="flex items-center gap-2 text-white"><BarChart3 className="h-4 w-4 text-blue-400" /> Key Performance Indicators</CardTitle></CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-slate-900 rounded-lg p-4 border border-slate-700">
              <p className="text-xs text-slate-400 mb-1">First Response Time</p>
              <p className="text-2xl font-bold text-white">{stats.tickets?.avg_first_response_minutes ?? 0} <span className="text-sm text-slate-400">min</span></p>
              <p className="text-xs text-slate-500 mt-1">Average time to first response</p>
            </div>
            <div className="bg-slate-900 rounded-lg p-4 border border-slate-700">
              <p className="text-xs text-slate-400 mb-1">Resolution Time</p>
              <p className="text-2xl font-bold text-white">{stats.tickets?.avg_resolution_hours ?? 0} <span className="text-sm text-slate-400">hrs</span></p>
              <p className="text-xs text-slate-500 mt-1">Average time to resolution</p>
            </div>
            <div className="bg-slate-900 rounded-lg p-4 border border-slate-700">
              <p className="text-xs text-slate-400 mb-1">Churn Risk</p>
              <p className="text-2xl font-bold text-red-400">{stats.health?.at_risk_count ?? 0}</p>
              <p className="text-xs text-slate-500 mt-1">Customers with high churn risk</p>
            </div>
          </div>
        </CardContent>
      </Card>
      <Card className="bg-slate-800 border-slate-700">
        <CardHeader><CardTitle className="flex items-center gap-2 text-white"><Activity className="h-4 w-4 text-green-400" /> System Status</CardTitle></CardHeader>
        <CardContent>
          <div className="grid grid-cols-4 gap-4 text-center">
            <div className="bg-slate-900 rounded-lg p-3 border border-slate-700">
              <p className="text-xs text-slate-400 mb-2">Health Scoring</p>
              <Badge className="bg-green-600">Online</Badge>
            </div>
            <div className="bg-slate-900 rounded-lg p-3 border border-slate-700">
              <p className="text-xs text-slate-400 mb-2">Ticketing</p>
              <Badge className="bg-green-600">Online</Badge>
            </div>
            <div className="bg-slate-900 rounded-lg p-3 border border-slate-700">
              <p className="text-xs text-slate-400 mb-2">Sentiment</p>
              <Badge className="bg-green-600">Online</Badge>
            </div>
            <div className="bg-slate-900 rounded-lg p-3 border border-slate-700">
              <p className="text-xs text-slate-400 mb-2">NPS Surveys</p>
              <Badge className="bg-green-600">Online</Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}