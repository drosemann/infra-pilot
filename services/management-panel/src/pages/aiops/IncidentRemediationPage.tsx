import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";

const mockRemediations = [
  { id: "REM-001", action: "restart_service", target: "nginx-proxy", confidence: 0.94, status: "approved", mode: "auto" },
  { id: "REM-002", action: "scale_up", target: "api-gateway", confidence: 0.82, status: "pending", mode: "semi" },
  { id: "REM-003", action: "rollback_deploy", target: "web-server", confidence: 0.96, status: "completed", mode: "auto" },
  { id: "REM-004", action: "clear_cache", target: "redis-cache", confidence: 0.71, status: "pending", mode: "manual" },
];

const runbookStats = [
  { name: "Service Restart", runs: 45, avgDuration: 85, successRate: 98 },
  { name: "Cache Clear", runs: 32, avgDuration: 45, successRate: 100 },
  { name: "Rollback Deploy", runs: 18, avgDuration: 120, successRate: 94 },
  { name: "Scale Up", runs: 27, avgDuration: 65, successRate: 96 },
];

const autoRemediationHistory = [
  { incident: "CPU Spike on api-gateway", action: "scale_up", triggered: "auto", result: "resolved", duration: "45s", time: "10m ago" },
  { incident: "nginx service down", action: "restart_service", triggered: "auto", result: "resolved", duration: "12s", time: "25m ago" },
  { incident: "Memory leak on cache", action: "restart_service", triggered: "manual", result: "resolved", duration: "30s", time: "1h ago" },
];

function RunbookStatsPanel() {
  return (
    <Card><CardHeader><CardTitle>Runbook Execution Stats</CardTitle></CardHeader>
      <CardContent className="space-y-2">
        {runbookStats.map(r => (
          <div key={r.name} className="flex items-center justify-between p-2 border-b last:border-0">
            <span className="text-sm font-medium">{r.name}</span>
            <div className="flex items-center gap-3 text-xs">
              <span>{r.runs} runs</span>
              <span>{r.avgDuration}s avg</span>
              <Badge variant={r.successRate >= 96 ? "default" : "secondary"}>{r.successRate}% success</Badge>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

function AutoRemediationHistory() {
  return (
    <Card><CardHeader><CardTitle>Auto-Remediation History</CardTitle></CardHeader>
      <CardContent className="space-y-2">
        {autoRemediationHistory.map((h, i) => (
          <div key={i} className="flex items-center justify-between p-2 bg-muted rounded-lg text-sm">
            <div><p className="font-medium">{h.incident}</p><p className="text-xs text-muted-foreground">{h.action} ({h.duration})</p></div>
            <div className="flex items-center gap-2">
              <Badge variant={h.triggered === "auto" ? "default" : "secondary"}>{h.triggered}</Badge>
              <Badge variant={h.result === "resolved" ? "default" : "destructive"}>{h.result}</Badge>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

function MTTRChart() {
  const mttrData = [
    { severity: "P1", mttr: 12 },
    { severity: "P2", mttr: 28 },
    { severity: "P3", mttr: 45 },
    { severity: "P4", mttr: 120 },
  ];
  return (
    <Card><CardHeader><CardTitle>MTTR by Severity (min)</CardTitle></CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={mttrData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="severity" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="mttr" fill="#3b82f6" name="MTTR (min)" />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

export default function IncidentRemediationPage() {
  const [activeTab, setActiveTab] = useState("active");
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Incident Remediation</h1>
          <p className="text-muted-foreground">AI-suggested and auto-approved remediation actions</p>
        </div>
        <Badge variant="secondary" className="text-sm">Auto-Approval Active</Badge>
      </div>
      <div className="grid gap-4 md:grid-cols-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Active</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold text-yellow-500">2</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Completed</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold text-green-500">147</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Failed</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold text-red-500">12</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Success Rate</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold text-green-500">92.4%</div></CardContent></Card>
      </div>
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="active">Pending Approval</TabsTrigger>
          <TabsTrigger value="runbooks">Runbook Stats</TabsTrigger>
          <TabsTrigger value="history">Auto History</TabsTrigger>
          <TabsTrigger value="mttr">MTTR</TabsTrigger>
          <TabsTrigger value="patterns">Pattern Library</TabsTrigger>
        </TabsList>
        <TabsContent value="active" className="space-y-3">
          {mockRemediations.filter(r => r.status === "pending").map(r => (
            <div key={r.id} className="flex items-center justify-between p-3 bg-muted rounded-lg">
              <div>
                <p className="font-medium">{r.action.replace(/_/g, " ")}</p>
                <p className="text-sm text-muted-foreground">{r.target}</p>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant={r.mode === "auto" ? "default" : r.mode === "semi" ? "secondary" : "outline"}>{r.mode}</Badge>
                <span className="text-sm font-mono">{(r.confidence * 100).toFixed(0)}%</span>
                <Button size="sm" variant="default">Approve</Button>
                <Button size="sm" variant="destructive">Reject</Button>
              </div>
            </div>
          ))}
        </TabsContent>
        <TabsContent value="runbooks">
          <RunbookStatsPanel />
        </TabsContent>
        <TabsContent value="history">
          <AutoRemediationHistory />
        </TabsContent>
        <TabsContent value="mttr">
          <MTTRChart />
        </TabsContent>
        <TabsContent value="patterns">
          <Card><CardHeader><CardTitle>Pattern Library</CardTitle></CardHeader>
            <CardContent className="space-y-3">
              {["high_cpu", "memory_leak", "service_down", "deploy_failure", "latency_spike"].map(p => (
                <div key={p} className="flex items-center justify-between p-2 border-b last:border-0">
                  <span className="text-sm font-medium">{p.replace(/_/g, " ")}</span>
                  <Badge variant="outline">Learned</Badge>
                </div>
              ))}
            </CardContent>
          </Card>
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
