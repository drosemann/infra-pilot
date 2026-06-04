import { useEffect, useState } from 'react';
import { FormattedMessage } from 'react-intl';
import { apiClient } from '../../lib/api';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table';

interface ServiceScore {
  id: string; service_id: string; service_name: string;
  overall_score: number; grade: string;
  dimension_scores: Record<string, number>;
  scored_at: string;
}

export default function ResiliencyScore() {
  const [scores, setScores] = useState<ServiceScore[]>([]);
  const [loading, setLoading] = useState(true);
  const [serviceName, setServiceName] = useState('');
  const [scoring, setScoring] = useState(false);

  useEffect(() => { loadScores(); }, []);

  const loadScores = async () => {
    try { const data = await apiClient.get('/api/v1/resiliency/scores'); setScores(data || []); }
    catch { toast.error('Failed to load scores'); }
    finally { setLoading(false); }
  };

  const scoreService = async () => {
    if (!serviceName) return;
    setScoring(true);
    try {
      const result = await apiClient.post(`/api/v1/resiliency/score/${serviceName.replace(/\s/g, '_')}`, { name: serviceName });
      toast.success(`Score: ${result.overall_score}/100 (${result.grade})`);
      setServiceName('');
      loadScores();
    } catch { toast.error('Failed to score service'); }
    finally { setScoring(false); }
  };

  const deleteScore = async (serviceId: string) => {
    try { await apiClient.delete(`/api/v1/resiliency/score/${serviceId}`); toast.success('Score deleted'); loadScores(); }
    catch { toast.error('Failed to delete'); }
  };

  const gradeColor: Record<string, string> = { A: 'bg-green-500', B: 'bg-blue-500', C: 'bg-yellow-500', D: 'bg-orange-500', F: 'bg-red-500' };
  const dimensions = ['redundancy', 'backup_coverage', 'dr_tested', 'circuit_breakers', 'auto_scaling', 'load_balancing', 'monitoring_coverage', 'chaos_validation'];

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>;

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold"><FormattedMessage id="resScore.title" defaultMessage="Resiliency Score & Insights" /></h1>
          <p className="text-muted-foreground mt-1">Score every service on resiliency with improvement recommendations</p>
        </div>
      </div>

      <Card>
        <CardHeader><CardTitle>Score a Service</CardTitle></CardHeader>
        <CardContent className="flex gap-4">
          <input className="flex-1 border rounded p-2" placeholder="Service name..." value={serviceName} onChange={e => setServiceName(e.target.value)} />
          <Button onClick={scoreService} disabled={scoring}>{scoring ? 'Scoring...' : 'Score'}</Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Service Scores ({scores.length})</CardTitle></CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow><TableHead>Service</TableHead><TableHead>Score</TableHead><TableHead>Grade</TableHead><TableHead>Scored At</TableHead><TableHead>Actions</TableHead></TableRow>
            </TableHeader>
            <TableBody>
              {scores.map(s => (
                <TableRow key={s.id}>
                  <TableCell className="font-medium">{s.service_name}</TableCell>
                  <TableCell><span className="text-lg font-bold">{s.overall_score}</span>/100</TableCell>
                  <TableCell><Badge className={gradeColor[s.grade]}>{s.grade}</Badge></TableCell>
                  <TableCell className="text-sm">{new Date(s.scored_at).toLocaleDateString()}</TableCell>
                  <TableCell><Button size="sm" variant="destructive" onClick={() => deleteScore(s.service_id)}>Delete</Button></TableCell>
                </TableRow>
              ))}
              {scores.length === 0 && <TableRow><TableCell colSpan={5} className="text-center text-muted-foreground">No services scored yet</TableCell></TableRow>}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {scores.length > 0 && (
        <Card>
          <CardHeader><CardTitle>Dimension Breakdown</CardTitle></CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow><TableHead>Service</TableHead>{dimensions.map(d => <TableHead key={d} className="text-xs">{d.replace(/_/g, ' ')}</TableHead>)}</TableRow>
              </TableHeader>
              <TableBody>
                {scores.slice(0, 5).map(s => (
                  <TableRow key={s.id}>
                    <TableCell className="font-medium">{s.service_name}</TableCell>
                    {dimensions.map(d => (
                      <TableCell key={d}>
                        <div className="w-full bg-gray-200 rounded h-2">
                          <div className={`h-2 rounded ${(s.dimension_scores[d] || 0) >= 70 ? 'bg-green-500' : (s.dimension_scores[d] || 0) >= 40 ? 'bg-yellow-500' : 'bg-red-500'}`}
                            style={{ width: `${s.dimension_scores[d] || 0}%` }} />
                        </div>
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function ResGradeDistribution() {
  const [grades, setGrades] = useState<Record<string, number>>({});
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/scoring/grades').then(d => setGrades(d || {})).catch(() => {});
  }, []);
  const gradeOrder = ['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'D', 'F'];
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-white font-semibold mb-3">Grade Distribution</h3>
      <div className="flex gap-2">
        {gradeOrder.filter(g => grades[g]).map(g => (
          <div key={g} className="flex-1 text-center">
            <div className="text-lg font-bold text-white">{grades[g]}</div>
            <div className="text-xs text-slate-400">{g}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function ResServiceRankings() {
  const [rankings, setRankings] = useState<any[]>([]);
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/scoring/rankings').then(d => setRankings(d || [])).catch(() => {});
  }, []);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-white font-semibold mb-3">Service Rankings</h3>
      {rankings.slice(0, 5).map((r, i) => (
        <div key={i} className="flex justify-between py-2 border-b border-slate-700 last:border-0 text-sm">
          <span className="text-slate-300">{r.service_name}</span>
          <span className="text-white">{r.overall}/100 ({r.grade})</span>
        </div>
      ))}
    </div>
  );
}

function ResScoreHistoryChart() {
  const [history, setHistory] = useState<number[]>([61, 65, 68, 72, 75, 78, 82]);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-white font-semibold mb-3">Score Trend (Monthly)</h3>
      <div className="flex items-end space-x-2 h-24">
        {history.map((v, i) => (
          <div key={i} className="flex-1 flex flex-col items-center">
            <div className="w-full bg-emerald-500 rounded-t" style={{ height: `${(v / 100) * 100}%` }} />
            <div className="text-xs text-slate-400 mt-1">{v}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function ResRecommendationsPanel() {
  const [recs, setRecs] = useState<any[]>([]);
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/scoring/recommendations').then(d => setRecs(d || [])).catch(() => {});
  }, []);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-white font-semibold mb-3">Recommendations</h3>
      {recs.length === 0 && <p className="text-slate-400 text-sm">No open recommendations</p>}
      {recs.slice(0, 5).map((r, i) => (
        <div key={i} className="flex justify-between py-2 border-b border-slate-700 last:border-0 text-sm">
          <span className="text-slate-300">{r.message}</span>
          <span className="text-green-400">+{r.potential_improvement}</span>
        </div>
      ))}
    </div>
  );
}

function ResAlertManager() {
  const [alerts, setAlerts] = useState<any[]>([]);
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/scoring/alerts/active').then(d => setAlerts(d || [])).catch(() => {});
  }, []);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Active Alerts</h3>
      {alerts.length === 0 && <p className="text-slate-400 text-sm">No active alerts</p>}
      {alerts.slice(0, 5).map((a, i) => (
        <div key={i} className="flex justify-between py-2 border-b border-slate-700 last:border-0 text-sm">
          <span className="text-slate-300">{a.dimension} - {a.service_name}</span>
          <span className={a.severity === 'critical' ? 'text-red-400' : 'text-yellow-400'}>{a.severity}</span>
        </div>
      ))}
    </div>
  );
}

function ResTrendForecast() {
  const [forecast, setForecast] = useState<any>(null);
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/scoring/forecast').then(d => setForecast(d)).catch(() => {});
  }, []);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Score Forecast</h3>
      {!forecast && <p className="text-slate-400 text-sm">Loading...</p>}
      {forecast && (
        <div className="grid grid-cols-3 gap-3 text-sm">
          {forecast.forecast?.map((v: number, i: number) => (
            <div key={i} className="bg-slate-700/50 rounded p-2 text-center">
              <div className="text-slate-400">Period {i + 1}</div>
              <div className="text-white font-bold">{v}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function ResServiceComparison() {
  const [comparison, setComparison] = useState<any>(null);
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/scoring/compare').then(d => setComparison(d)).catch(() => {});
  }, []);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Service Comparison</h3>
      {!comparison && <p className="text-slate-400 text-sm">No comparison data</p>}
      {comparison?.comparison && Object.entries(comparison.comparison).map(([sid, svc]: any) => (
        <div key={sid} className="flex justify-between py-2 border-b border-slate-700 last:border-0 text-sm">
          <span className="text-slate-300">{svc.service_name}</span>
          <span className="text-white">{svc.overall_score} ({svc.grade})</span>
        </div>
      ))}
    </div>
  );
}

function ResScoreExporter() {
  const handleExport = async (format: string) => {
    const data = await apiClient.get(`/api/v1/resiliency/scoring/export?format=${format}`);
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = `scores.${format}`; a.click();
    toast.success(`Exported as ${format}`);
  };
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Export Scores</h3>
      <div className="flex gap-2">
        <button onClick={() => handleExport('json')} className="bg-blue-600 text-white px-3 py-1.5 rounded text-xs hover:bg-blue-700">JSON</button>
        <button onClick={() => handleExport('csv')} className="bg-blue-600 text-white px-3 py-1.5 rounded text-xs hover:bg-blue-700">CSV</button>
        <button onClick={() => handleExport('prometheus')} className="bg-blue-600 text-white px-3 py-1.5 rounded text-xs hover:bg-blue-700">Prometheus</button>
      </div>
    </div>
  );
}

function ResTrendPanel() {
  const [trends, setTrends] = useState<any>(null);
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/scoring/trends').then(d => setTrends(d)).catch(() => {});
  }, []);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Score Trends</h3>
      {!trends && <p className="text-slate-400 text-sm">Loading...</p>}
      {trends && (
        <div className="grid grid-cols-3 gap-3 text-sm">
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Period</span><div className="text-white font-bold">{trends.period}</div></div>
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Change</span><div className={trends.change >= 0 ? 'text-green-400' : 'text-red-400'}>{trends.change >= 0 ? '+' : ''}{trends.change}</div></div>
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Direction</span><div className="text-white font-bold">{trends.direction}</div></div>
        </div>
      )}
    </div>
  );
}

function ResBreakdownPanel() {
  const [breakdown, setBreakdown] = useState<any>(null);
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/scoring/breakdown').then(d => setBreakdown(d)).catch(() => {});
  }, []);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Category Breakdown</h3>
      {!breakdown && <p className="text-slate-400 text-sm">No data</p>}
      {breakdown?.categories?.map((c: any, i: number) => (
        <div key={i} className="flex justify-between py-2 border-b border-slate-700 last:border-0 text-sm">
          <span className="text-slate-300">{c.name}</span>
          <span className={c.score >= 80 ? 'text-green-400' : c.score >= 60 ? 'text-yellow-400' : 'text-red-400'}>{c.score}%</span>
        </div>
      ))}
    </div>
  );
}

function ResTargetTracker() {
  const [targets, setTargets] = useState<any>(null);
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/scoring/targets').then(d => setTargets(d)).catch(() => {});
  }, []);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Targets</h3>
      {!targets && <p className="text-slate-400 text-sm">No data</p>}
      {targets && (
        <div className="text-sm text-slate-300">
          <p>Current: {targets.current}/100</p>
          <p>Q2 target: {targets.q2_target}/100</p>
          <p>On track: <span className={targets.on_track ? 'text-green-400' : 'text-red-400'}>{targets.on_track ? 'Yes' : 'No'}</span></p>
        </div>
      )}
    </div>
  );
}

function ResHistoryPanel() {
  const [history, setHistory] = useState<any>(null);
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/scoring/history').then(d => setHistory(d)).catch(() => {});
  }, []);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">History</h3>
      {!history && <p className="text-slate-400 text-sm">No data</p>}
      {history?.data_points?.slice(0, 6).map((h: any, i: number) => (
        <div key={i} className="flex justify-between py-1 border-b border-slate-700 last:border-0 text-sm">
          <span className="text-slate-300">{h.label}</span>
          <span className="text-white">{h.value}</span>
        </div>
      ))}
    </div>
  );
}
