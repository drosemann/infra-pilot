import { useEffect, useState } from 'react';
import { FormattedMessage } from 'react-intl';
import { apiClient } from '../../lib/api';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';

interface BCDashboard {
  overall_bc_score: { overall: number; grade: string; dr_readiness: number; backup_compliance: number; chaos_validation: number; resiliency_score: number };
  dr_readiness: { status: string; total_plans: number; ready_plans: number; percentage: number };
  backup_compliance: { total_slas: number; compliant_slas: number; percentage: number };
  rpo_rto_status: { average_rpo_minutes: number; average_rto_minutes: number; rpo_compliant_plans: number; rto_compliant_plans: number };
  compliance_status: Record<string, boolean>;
  improvement_areas: { area: string; impact: string; current_score: number; recommended_action: string }[];
}

export default function BCDashboard() {
  const [dashboard, setDashboard] = useState<BCDashboard | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadDashboard(); }, []);

  const loadDashboard = async () => {
    try { const data = await apiClient.get('/api/v1/resiliency/bc-dashboard'); setDashboard(data); }
    catch { toast.error('Failed to load BC dashboard'); }
    finally { setLoading(false); }
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>;

  if (!dashboard) return <div className="text-center py-12 text-muted-foreground">Failed to load dashboard data</div>;

  const score = dashboard.overall_bc_score;
  const gradeColor: Record<string, string> = { A: 'text-green-500', B: 'text-blue-500', C: 'text-yellow-500', D: 'text-orange-500', F: 'text-red-500' };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold"><FormattedMessage id="bcDash.title" defaultMessage="Business Continuity Dashboard" /></h1>
          <p className="text-muted-foreground mt-1">Executive view of BC readiness, compliance, and incident timeline</p>
        </div>
        <Button onClick={loadDashboard}>Refresh</Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Overall BC Score</CardTitle></CardHeader>
          <CardContent>
            <div className={`text-4xl font-bold ${gradeColor[score.grade] || ''}`}>{score.overall}<span className="text-lg ml-1">/{score.grade}</span></div>
            <p className="text-xs text-muted-foreground mt-1">Business Continuity Readiness</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm font-medium">DR Readiness</CardTitle></CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{score.dr_readiness}<span className="text-sm text-muted-foreground">/100</span></div>
            <p className="text-xs text-muted-foreground mt-1">{dashboard.dr_readiness.ready_plans}/{dashboard.dr_readiness.total_plans} plans ready</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Backup Compliance</CardTitle></CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{score.backup_compliance}<span className="text-sm text-muted-foreground">/100</span></div>
            <p className="text-xs text-muted-foreground mt-1">{dashboard.backup_compliance.compliant_slas}/{dashboard.backup_compliance.total_slas} SLAs compliant</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Chaos Validation</CardTitle></CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{score.chaos_validation}<span className="text-sm text-muted-foreground">/100</span></div>
            <p className="text-xs text-muted-foreground mt-1">Recovery validation status</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader><CardTitle>RPO/RTO Status</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div className="flex justify-between items-center">
              <span>Average RPO</span>
              <span className="font-bold">{dashboard.rpo_rto_status.average_rpo_minutes} min</span>
            </div>
            <div className="flex justify-between items-center">
              <span>Average RTO</span>
              <span className="font-bold">{dashboard.rpo_rto_status.average_rto_minutes} min</span>
            </div>
            <div className="flex justify-between items-center">
              <span>RPO Compliant</span>
              <span className="font-bold text-green-500">{dashboard.rpo_rto_status.rpo_compliant_plans} plans</span>
            </div>
            <div className="flex justify-between items-center">
              <span>RTO Compliant</span>
              <span className="font-bold text-green-500">{dashboard.rpo_rto_status.rto_compliant_plans} plans</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Compliance Status</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {Object.entries(dashboard.compliance_status).map(([framework, compliant]) => (
              <div key={framework} className="flex justify-between items-center">
                <span className="font-medium uppercase">{framework.replace(/_/g, ' ')}</span>
                <Badge variant={compliant ? 'default' : 'destructive'}>{compliant ? 'Compliant' : 'Non-Compliant'}</Badge>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader><CardTitle>Improvement Areas</CardTitle></CardHeader>
        <CardContent>
          <div className="space-y-4">
            {dashboard.improvement_areas.map((area, i) => (
              <div key={i} className="flex items-center gap-4 p-3 border rounded-lg">
                <div className="flex-1">
                  <div className="font-medium">{area.area}</div>
                  <div className="text-sm text-muted-foreground">{area.recommended_action}</div>
                </div>
                <div className="text-right">
                  <Badge variant={area.impact === 'critical' ? 'destructive' : area.impact === 'high' ? 'default' : 'secondary'}>{area.impact}</Badge>
                  <div className="text-lg font-bold mt-1">{area.current_score}<span className="text-sm text-muted-foreground">/100</span></div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function BCScoreTrend() {
  const data = [72, 75, 73, 78, 82, 81, 85];
  const maxScore = 100;
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-white font-semibold mb-3">Score Trend</h3>
      <div className="flex items-end space-x-2 h-24">
        {data.map((v, i) => (
          <div key={i} className="flex-1 flex flex-col items-center">
            <div className="w-full bg-emerald-500 rounded-t" style={{ height: `${(v / maxScore) * 100}%` }} />
            <div className="text-xs text-slate-400 mt-1">{v}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function BCFindingsPanel() {
  const [findings, setFindings] = useState<any[]>([]);
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/bc/findings').then(d => setFindings(d || [])).catch(() => {});
  }, []);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-white font-semibold mb-3">Findings</h3>
      {findings.length === 0 && <p className="text-slate-400 text-sm">No findings</p>}
      {findings.slice(0, 5).map((f, i) => (
        <div key={i} className="flex justify-between py-2 border-b border-slate-700 last:border-0 text-sm">
          <span className="text-slate-300">{f.description}</span>
          <span className={`${f.severity === 'critical' ? 'text-red-400' : f.severity === 'high' ? 'text-yellow-400' : 'text-slate-400'}`}>{f.severity}</span>
        </div>
      ))}
    </div>
  );
}

function BCMetricCard({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 text-center">
      <div className={`text-2xl font-bold ${color}`}>{value}</div>
      <div className="text-sm text-slate-400 mt-1">{label}</div>
    </div>
  );
}

function BCExportButton() {
  const handleExport = async () => {
    const data = await apiClient.get('/api/v1/resiliency/bc/export');
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = 'bc_dashboard.json'; a.click();
    toast.success('BC Dashboard exported');
  };
  return <button onClick={handleExport} className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 text-sm">Export</button>;
}

function BCScenarioPanel() {
  const [scenarios, setScenarios] = useState<any[]>([]);
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/bc/scenarios').then(d => setScenarios(d || [])).catch(() => {});
  }, []);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">BC Scenarios</h3>
      {scenarios.length === 0 && <p className="text-slate-400 text-sm">No scenarios</p>}
      {scenarios.map((s, i) => (
        <div key={i} className="flex justify-between py-2 border-b border-slate-700 last:border-0 text-sm">
          <span className="text-slate-300">{s.name}</span>
          <span className={s.severity === 'critical' ? 'text-red-400' : 'text-yellow-400'}>{s.severity}</span>
        </div>
      ))}
    </div>
  );
}

function BCScoreSimulator() {
  const [dims, setDims] = useState<string[]>(['dr_readiness', 'backup_compliance', 'recovery_capacity']);
  const [simResult, setSimResult] = useState<any>(null);
  const runSim = async (dim: string, delta: number) => {
    const data = await apiClient.get(`/api/v1/resiliency/bc/simulate?dimension=${dim}&delta=${delta}`);
    setSimResult(data);
  };
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">What-If Simulator</h3>
      <div className="flex flex-wrap gap-2 mb-3">
        {dims.map(d => (
          <div key={d} className="flex gap-1">
            <button onClick={() => runSim(d, 10)} className="bg-green-700 text-white px-2 py-1 rounded text-xs">+10 {d}</button>
            <button onClick={() => runSim(d, -10)} className="bg-red-700 text-white px-2 py-1 rounded text-xs">-10 {d}</button>
          </div>
        ))}
      </div>
      {simResult && (
        <div className="bg-slate-700/50 rounded p-2 text-sm">
          <p className="text-slate-300">Baseline: {simResult.baseline_overall} → Simulated: <span className={simResult.change >= 0 ? 'text-green-400' : 'text-red-400'}>{simResult.simulated_overall} ({simResult.change >= 0 ? '+' : ''}{simResult.change})</span></p>
        </div>
      )}
    </div>
  );
}

function BCNotificationSubscriber() {
  const [email, setEmail] = useState('');
  const handleSubscribe = async () => {
    await apiClient.post('/api/v1/resiliency/bc/notifications/subscribe', { email, events: ['score_change', 'compliance'] });
    toast.success('Subscribed');
    setEmail('');
  };
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Subscribe to Notifications</h3>
      <div className="flex gap-2">
        <input placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} className="bg-slate-700 text-white p-2 rounded text-sm flex-1" />
        <button onClick={handleSubscribe} className="bg-blue-600 text-white px-3 py-2 rounded text-sm">Subscribe</button>
      </div>
    </div>
  );
}

function BCComplianceReport() {
  const [report, setReport] = useState<any>(null);
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/bc/compliance-report').then(d => setReport(d)).catch(() => {});
  }, []);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Compliance Report</h3>
      {!report && <p className="text-slate-400 text-sm">No data</p>}
      {report && (
        <div className="text-sm">
          <p className="text-slate-300">Compliant: <span className={report.compliant ? 'text-green-400' : 'text-red-400'}>{report.compliant ? 'Yes' : 'No'}</span></p>
          <p className="text-slate-300">Risks found: {report.risks_found}</p>
        </div>
      )}
    </div>
  );
}

function BCDrillPlanner() {
  const [drills, setDrills] = useState<any[]>([]);
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/bc/drill-plans').then(d => setDrills(d || [])).catch(() => {});
  }, []);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Drill Plans</h3>
      {drills.length === 0 && <p className="text-slate-400 text-sm">No drill plans</p>}
      {drills.map((d, i) => (
        <div key={i} className="flex justify-between py-2 border-b border-slate-700 last:border-0 text-sm">
          <span className="text-slate-300">{d.scenario}</span>
          <span className="text-slate-400">{d.duration_min}min</span>
        </div>
      ))}
    </div>
  );
}

function BCResourceInventory() {
  const [resources, setResources] = useState<any>(null);
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/bc/resources').then(d => setResources(d)).catch(() => {});
  }, []);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Resource Inventory</h3>
      {!resources && <p className="text-slate-400 text-sm">Loading...</p>}
      {resources && (
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Staff</span><div className="text-white">{resources.critical_staff}</div></div>
          <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Backup Sites</span><div className="text-white">{resources.backup_sites}</div></div>
        </div>
      )}
    </div>
  );
}

function BCTrainingStatus() {
  const [training, setTraining] = useState<any>(null);
  useEffect(() => {
    apiClient.get('/api/v1/resiliency/bc/training').then(d => setTraining(d)).catch(() => {});
  }, []);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
      <h3 className="text-white font-semibold mb-3">Training Status</h3>
      {!training && <p className="text-slate-400 text-sm">No data</p>}
      {training && (
        <div className="text-sm text-slate-300">
          <p>Team trained: {training.team_trained}%</p>
          <p>Drills completed: {training.drills_completed}</p>
          <p>Next training: {training.next_training}</p>
        </div>
      )}
    </div>
  );
}
