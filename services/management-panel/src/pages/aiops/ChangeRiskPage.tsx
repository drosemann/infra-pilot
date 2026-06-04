import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";

const changes = [
  { id: "CHG-001", title: "Update nginx config", type: "config_change", target: "nginx-proxy", risk: "low", score: 0.15, status: "completed" },
  { id: "CHG-002", title: "Scale database cluster", type: "scale_change", target: "postgres-db", risk: "high", score: 0.72, status: "pending" },
  { id: "CHG-003", title: "Deploy API v3.2", type: "deployment", target: "api-gateway", risk: "medium", score: 0.45, status: "approved" },
  { id: "CHG-004", title: "Migrate cache to Redis 7", type: "migration", target: "redis-cache", risk: "critical", score: 0.88, status: "pending" },
];

const riskFactors = [
  { name: "Change Type", score: 0.7, label: "Migration carries inherent risk" },
  { name: "Blast Radius", score: 0.6, label: "Affects 4 components" },
  { name: "Historical Failure", score: 0.3, label: "2/10 similar changes failed" },
  { name: "Time of Day", score: 0.6, label: "Scheduled during off-hours" },
  { name: "Data Integrity", score: 0.7, label: "Database migration" },
];

const changeTypes = [
  { type: "deployment", count: 98, failRate: 0.04, avgRisk: 0.32 },
  { type: "config_change", count: 210, failRate: 0.06, avgRisk: 0.28 },
  { type: "scale_change", count: 45, failRate: 0.09, avgRisk: 0.55 },
  { type: "migration", count: 24, failRate: 0.12, avgRisk: 0.68 },
  { type: "rollback", count: 15, failRate: 0.02, avgRisk: 0.15 },
];

const approvalRules = [
  { name: "High Risk Requires Approval", threshold: 0.7, approver: "SRE Lead", active: true },
  { name: "Critical Changes Freeze Window", window: "Weekend only", team: "Platform", active: true },
  { name: "Auto-Approve Low Risk", threshold: 0.2, auto: true, active: false },
];

function ChangeTypeAnalysis() {
  return (
    <Card><CardHeader><CardTitle>Change Type Risk Analysis</CardTitle></CardHeader>
      <CardContent className="space-y-2">
        {changeTypes.map(ct => (
          <div key={ct.type} className="flex items-center justify-between p-2 border-b last:border-0">
            <div><p className="font-medium text-sm">{ct.type.replace(/_/g, " ")}</p><p className="text-xs text-muted-foreground">{ct.count} changes</p></div>
            <div className="flex items-center gap-3">
              <span className="text-xs text-muted-foreground">Fail: {(ct.failRate * 100).toFixed(0)}%</span>
              <Badge variant={ct.avgRisk > 0.5 ? "destructive" : ct.avgRisk > 0.3 ? "default" : "secondary"}>Risk: {(ct.avgRisk * 100).toFixed(0)}%</Badge>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

function ApprovalRulesPanel() {
  return (
    <Card><CardHeader><CardTitle>Approval Rules</CardTitle></CardHeader>
      <CardContent className="space-y-2">
        {approvalRules.map(r => (
          <div key={r.name} className="flex items-center justify-between p-2 bg-muted rounded-lg">
            <div><p className="font-medium text-sm">{r.name}</p><p className="text-xs text-muted-foreground">{r.threshold ? `${(r.threshold * 100).toFixed(0)}% threshold` : r.window}</p></div>
            <Badge variant={r.active ? "default" : "secondary"}>{r.active ? "Active" : "Disabled"}</Badge>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

function HistoricalTrend() {
  const trendData = [
    { month: "Jan", successRate: 94, avgRisk: 0.35 },
    { month: "Feb", successRate: 91, avgRisk: 0.42 },
    { month: "Mar", successRate: 93, avgRisk: 0.38 },
    { month: "Apr", successRate: 89, avgRisk: 0.45 },
    { month: "May", successRate: 92, avgRisk: 0.40 },
    { month: "Jun", successRate: 95, avgRisk: 0.32 },
  ];
  return (
    <Card><CardHeader><CardTitle>Historical Trend</CardTitle></CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={trendData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis yAxisId="left" />
            <YAxis yAxisId="right" orientation="right" domain={[0, 1]} />
            <Tooltip />
            <Line yAxisId="left" type="monotone" dataKey="successRate" stroke="#10b981" name="Success %" />
            <Line yAxisId="right" type="monotone" dataKey="avgRisk" stroke="#ef4444" name="Avg Risk" />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

export default function ChangeRiskPage() {
  const [activeTab, setActiveTab] = useState("changes");
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Change Risk Analysis</h1>
          <p className="text-muted-foreground">Analyze planned changes against historical data</p>
        </div>
        <Button>Plan New Change</Button>
      </div>
      <div className="grid gap-4 md:grid-cols-5">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Total Changes</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">247</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Success Rate</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold text-green-500">92%</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Pending</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold text-yellow-500">2</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">High Risk</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold text-red-500">1</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Historical Records</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">1,892</div></CardContent></Card>
      </div>
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="changes">Planned Changes</TabsTrigger>
          <TabsTrigger value="risk">Risk Factors</TabsTrigger>
          <TabsTrigger value="types">By Type</TabsTrigger>
          <TabsTrigger value="trend">Trend</TabsTrigger>
          <TabsTrigger value="rules">Approval Rules</TabsTrigger>
        </TabsList>
        <TabsContent value="changes" className="space-y-3">
          {changes.map(c => (
            <div key={c.id} className="flex items-center justify-between p-3 bg-muted rounded-lg">
              <div>
                <p className="font-medium">{c.title}</p>
                <p className="text-xs text-muted-foreground">{c.id} — {c.target}</p>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant={c.risk === "critical" ? "destructive" : c.risk === "high" ? "default" : c.risk === "medium" ? "secondary" : "outline"}>{c.risk}</Badge>
                <span className="text-sm font-mono">{(c.score * 100).toFixed(0)}%</span>
                <Badge variant="outline">{c.status}</Badge>
              </div>
            </div>
          ))}
        </TabsContent>
        <TabsContent value="risk">
          <Card>
            <CardHeader><CardTitle>Risk Factor Breakdown</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              {riskFactors.map(f => (
                <div key={f.name}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium">{f.label}</span>
                    <span className="text-sm font-mono">{(f.score * 100).toFixed(0)}%</span>
                  </div>
                  <Progress value={f.score * 100} className="h-2" />
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="types">
          <ChangeTypeAnalysis />
        </TabsContent>
        <TabsContent value="trend">
          <HistoricalTrend />
        </TabsContent>
        <TabsContent value="rules">
          <ApprovalRulesPanel />
        </TabsContent>
      </Tabs>
    </div>
  );
}

// -- Extended Types ---------------------------------------------------

interface AiopsMetricData {
  timestamp: string;
  value: number;
  label: string;
  severity?: 'low' | 'medium' | 'high' | 'critical';
}

interface AnomalyResult {
  id: string;
  metric: string;
  score: number;
  baseline: number;
  detectedAt: string;
  status: 'open' | 'investigating' | 'resolved';
}

interface PredictionResult {
  metric: string;
  predictedValue: number;
  confidence: number;
  validUntil: string;
  factors: string[];
}

// -- Utility Hooks ----------------------------------------------------

function useMetricHistory(metricName: string, days: number = 30): AiopsMetricData[] {
  const [data] = React.useState<AiopsMetricData[]>(() =>
    Array.from({ length: days }, (_, i) => ({
      timestamp: new Date(Date.now() - (days - i) * 86400000).toISOString(),
      value: Math.round(Math.random() * 100 * 100) / 100,
      label: metricName,
      severity: (['low', 'medium', 'high', 'critical'] as const)[Math.floor(Math.random() * 4)],
    }))
  );
  return data;
}

function useAnomalyDetection(threshold: number = 0.7): AnomalyResult[] {
  const [anomalies] = React.useState<AnomalyResult[]>(() =>
    Array.from({ length: 5 }, (_, i) => ({
      id: `anomaly-${i}`,
      metric: ['cpu', 'memory', 'latency', 'error_rate', 'throughput'][i],
      score: Math.round(Math.random() * 100) / 100,
      baseline: Math.round(Math.random() * 50 * 100) / 100,
      detectedAt: new Date(Date.now() - Math.random() * 86400000 * 7).toISOString(),
      status: (['open', 'investigating', 'resolved'] as const)[Math.floor(Math.random() * 3)],
    })).filter(a => a.score > threshold)
  );
  return anomalies;
}

function usePredictions(metricName: string): PredictionResult {
  const [prediction] = React.useState<PredictionResult>(() => ({
    metric: metricName,
    predictedValue: Math.round(Math.random() * 100 * 100) / 100,
    confidence: Math.round(Math.random() * 30 + 70 * 100) / 100,
    validUntil: new Date(Date.now() + 86400000 * 7).toISOString(),
    factors: ['seasonal_trend', 'recent_growth', 'cyclical_pattern'],
  }));
  return prediction;
}

// -- Shared Components ------------------------------------------------

const MetricCard: React.FC<{ title: string; value: number; unit: string; trend?: 'up' | 'down' | 'stable'; color?: string }> = ({
  title, value, unit, trend = 'stable', color = '#6366f1',
}) => (
  <div className="metric-card" style={{ borderLeft: `4px solid ${color}`, padding: '16px', background: '#1e1e2e', borderRadius: '8px', margin: '8px' }}>
    <div style={{ fontSize: '12px', color: '#888', textTransform: 'uppercase', letterSpacing: '1px' }}>{title}</div>
    <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#fff', marginTop: '8px' }}>
      {value.toLocaleString()} <span style={{ fontSize: '14px', color: '#888' }}>{unit}</span>
    </div>
    <div style={{ fontSize: '12px', marginTop: '4px', color: trend === 'up' ? '#4ade80' : trend === 'down' ? '#f87171' : '#888' }}>
      {trend === 'up' ? '?' : trend === 'down' ? '?' : '?'} {trend === 'up' ? 'Increasing' : trend === 'down' ? 'Decreasing' : 'Stable'}
    </div>
  </div>
);

const AnomalyBadge: React.FC<{ severity: string }> = ({ severity }) => {
  const colors: Record<string, string> = { low: '#4ade80', medium: '#fbbf24', high: '#fb923c', critical: '#f87171' };
  return <span style={{ background: colors[severity] || '#888', color: '#000', padding: '2px 8px', borderRadius: '12px', fontSize: '11px', fontWeight: 600 }}>{severity}</span>;
};

const StatusIndicator: React.FC<{ status: string }> = ({ status }) => {
  const colors: Record<string, string> = { healthy: '#4ade80', warning: '#fbbf24', critical: '#f87171', unknown: '#888' };
  return <span style={{ display: 'inline-block', width: '10px', height: '10px', borderRadius: '50%', background: colors[status] || '#888', marginRight: '6px' }} />;
};

// -- Data Table -------------------------------------------------------

interface DataTableProps {
  columns: { key: string; label: string }[];
  data: Record<string, any>[];
  onRowClick?: (row: Record<string, any>) => void;
}

const DataTable: React.FC<DataTableProps> = ({ columns, data, onRowClick }) => (
  <div style={{ overflowX: 'auto', marginTop: '16px' }}>
    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
      <thead>
        <tr style={{ borderBottom: '2px solid #333' }}>
          {columns.map(col => <th key={col.key} style={{ padding: '10px 12px', textAlign: 'left', color: '#888', fontWeight: 600 }}>{col.label}</th>)}
        </tr>
      </thead>
      <tbody>
        {data.map((row, i) => (
          <tr key={i} style={{ borderBottom: '1px solid #2a2a2a', cursor: onRowClick ? 'pointer' : 'default' }}
              onClick={() => onRowClick?.(row)}>
            {columns.map(col => <td key={col.key} style={{ padding: '10px 12px' }}>{row[col.key]}</td>)}
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);

// -- Filter Bar -------------------------------------------------------

interface FilterOption { label: string; value: string; }

const FilterBar: React.FC<{
  options: FilterOption[];
  selected: string;
  onChange: (value: string) => void;
  label?: string;
}> = ({ options, selected, onChange, label = 'Filter' }) => (
  <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
    <span style={{ color: '#888', fontSize: '13px' }}>{label}:</span>
    <div style={{ display: 'flex', gap: '4px' }}>
      {options.map(opt => (
        <button key={opt.value} onClick={() => onChange(opt.value)}
                style={{ padding: '6px 14px', borderRadius: '6px', border: 'none',
                        background: selected === opt.value ? '#6366f1' : '#2a2a2a',
                        color: selected === opt.value ? '#fff' : '#888', cursor: 'pointer', fontSize: '13px' }}>
          {opt.label}
        </button>
      ))}
    </div>
  </div>
);

// -- Time Range Selector ----------------------------------------------

type TimeRange = '1h' | '6h' | '24h' | '7d' | '30d';

const TimeRangeSelector: React.FC<{ value: TimeRange; onChange: (range: TimeRange) => void }> = ({ value, onChange }) => {
  const ranges: { label: string; value: TimeRange }[] = [
    { label: '1H', value: '1h' }, { label: '6H', value: '6h' }, { label: '24H', value: '24h' },
    { label: '7D', value: '7d' }, { label: '30D', value: '30d' },
  ];
  return (
    <div style={{ display: 'flex', gap: '4px' }}>
      {ranges.map(r => (
        <button key={r.value} onClick={() => onChange(r.value)}
                style={{ padding: '4px 10px', borderRadius: '4px', border: 'none',
                        background: value === r.value ? '#6366f1' : '#2a2a2a',
                        color: value === r.value ? '#fff' : '#888', cursor: 'pointer', fontSize: '12px' }}>
          {r.label}
        </button>
      ))}
    </div>
  );
};

// -- Export Helpers ---------------------------------------------------

const exportToCsv = (data: Record<string, any>[], filename: string = 'export.csv') => {
  if (data.length === 0) return;
  const headers = Object.keys(data[0]);
  const csv = [headers.join(','), ...data.map(row => headers.map(h => row[h]).join(','))].join('\n');
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
};

const exportToJson = (data: any, filename: string = 'export.json') => {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
};
