import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

const recentAlerts = [
  { name: "HighCPUUsage", source: "prometheus", severity: "critical", status: "firing", count: 12, time: "2m ago" },
  { name: "MemoryPressure", source: "prometheus", severity: "warning", status: "firing", count: 5, time: "5m ago" },
  { name: "APIErrorRate", source: "grafana", severity: "critical", status: "firing", count: 8, time: "10m ago" },
  { name: "DiskSpaceWarning", source: "node-exporter", severity: "warning", status: "acknowledged", count: 1, time: "15m ago" },
];

const incidents = [
  { title: "Frontend Performance Degradation", priority: "p1", alerts: 8, status: "firing", created: "10m ago" },
  { title: "Database Connection Issues", priority: "p2", alerts: 3, status: "firing", created: "25m ago" },
  { title: "Cache Cluster Instability", priority: "p2", alerts: 5, status: "resolved", created: "2h ago" },
];

const sourceBreakdown = [
  { source: "prometheus", count: 156, pct: 42 },
  { source: "grafana", count: 89, pct: 24 },
  { source: "node-exporter", count: 67, pct: 18 },
  { source: "cloudwatch", count: 45, pct: 12 },
  { source: "custom", count: 15, pct: 4 },
];

const corrRules = [
  { name: "Same Service", field: "service", window: 5, active: true },
  { name: "Same Host", field: "host", window: 3, active: true },
  { name: "Time Proximity", field: "timestamp", window: 2, active: true },
  { name: "Error Pattern", field: "message_similarity", window: 5, active: false },
];

function SourceBreakdownChart() {
  return (
    <Card><CardHeader><CardTitle>Alert Source Breakdown</CardTitle></CardHeader>
      <CardContent className="space-y-2">
        {sourceBreakdown.map(s => (
          <div key={s.source} className="flex items-center justify-between">
            <span className="text-sm font-medium">{s.source}</span>
            <div className="flex items-center gap-2">
              <div className="w-32 bg-muted rounded-full h-2"><div className="bg-primary h-2 rounded-full" style={{width: `${s.pct}%`}} /></div>
              <span className="text-xs font-mono">{s.count} ({s.pct}%)</span>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

function CorrelationRulesPanel() {
  return (
    <Card><CardHeader><CardTitle>Correlation Rules</CardTitle></CardHeader>
      <CardContent className="space-y-2">
        {corrRules.map(r => (
          <div key={r.name} className="flex items-center justify-between p-2 border-b last:border-0">
            <div><p className="font-medium text-sm">{r.name}</p><p className="text-xs text-muted-foreground">Field: {r.field} ({r.window}m window)</p></div>
            <Badge variant={r.active ? "default" : "secondary"}>{r.active ? "Active" : "Disabled"}</Badge>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

function SuppressionHistoryPanel() {
  const history = [
    { rule: "HighCPU", suppressed: 45, saved: 12, lastTriggered: "5m ago" },
    { rule: "DiskCheck", suppressed: 23, saved: 6, lastTriggered: "30m ago" },
    { rule: "DeployNoise", suppressed: 67, saved: 18, lastTriggered: "2h ago" },
  ];
  return (
    <Card><CardHeader><CardTitle>Suppression History</CardTitle></CardHeader>
      <CardContent className="space-y-2">
        {history.map(h => (
          <div key={h.rule} className="flex items-center justify-between p-2 bg-muted rounded-lg">
            <div><p className="font-medium text-sm">{h.rule}</p><p className="text-xs text-muted-foreground">{h.suppressed} suppressed — {h.saved} incidents prevented</p></div>
            <span className="text-xs text-muted-foreground">{h.lastTriggered}</span>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

function TimeSeriesChart() {
  const seriesData = [
    { hour: "00:00", alerts: 12, incidents: 2 },
    { hour: "04:00", alerts: 8, incidents: 1 },
    { hour: "08:00", alerts: 23, incidents: 4 },
    { hour: "12:00", alerts: 18, incidents: 3 },
    { hour: "16:00", alerts: 15, incidents: 2 },
    { hour: "20:00", alerts: 10, incidents: 1 },
  ];
  return (
    <Card><CardHeader><CardTitle>Alert Timeline (24h)</CardTitle></CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={seriesData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="hour" />
            <YAxis />
            <Tooltip />
            <Line type="monotone" dataKey="alerts" stroke="#3b82f6" name="Alerts" />
            <Line type="monotone" dataKey="incidents" stroke="#10b981" name="Incidents" />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

export default function AlertCorrelationPage() {
  const [activeTab, setActiveTab] = useState("alerts");
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Alert Correlation</h1>
          <p className="text-muted-foreground">Intelligent grouping of related alerts into incidents</p>
        </div>
        <Badge variant="secondary" className="text-sm">Noise Reduction: 67%</Badge>
      </div>
      <div className="grid gap-4 md:grid-cols-5">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Firing</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold text-red-500">23</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Suppressed</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold text-muted-foreground">156</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Active Incidents</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold text-yellow-500">4</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Duplicates</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">89</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Suppression Rules</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">12</div></CardContent></Card>
      </div>
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="alerts">Alerts</TabsTrigger>
          <TabsTrigger value="incidents">Incidents</TabsTrigger>
          <TabsTrigger value="suppression">Suppression</TabsTrigger>
          <TabsTrigger value="sources">Sources</TabsTrigger>
          <TabsTrigger value="rules">Rules</TabsTrigger>
          <TabsTrigger value="stats">Statistics</TabsTrigger>
        </TabsList>
        <TabsContent value="alerts" className="space-y-2">
          {recentAlerts.map(a => (
            <div key={a.name} className="flex items-center justify-between p-3 bg-muted rounded-lg">
              <div className="flex items-center gap-3">
                <Badge variant={a.severity === "critical" ? "destructive" : "secondary"}>{a.severity}</Badge>
                <div>
                  <p className="font-medium">{a.name}</p>
                  <p className="text-xs text-muted-foreground">{a.source} — {a.time}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="outline">{a.status}</Badge>
                <span className="text-sm text-muted-foreground">×{a.count}</span>
                <Button size="sm" variant="ghost">Ack</Button>
              </div>
            </div>
          ))}
        </TabsContent>
        <TabsContent value="incidents" className="space-y-2">
          {incidents.map(i => (
            <div key={i.title} className="flex items-center justify-between p-3 bg-muted rounded-lg">
              <div className="flex items-center gap-3">
                <Badge variant={i.priority === "p1" ? "destructive" : "secondary"}>{i.priority}</Badge>
                <div>
                  <p className="font-medium">{i.title}</p>
                  <p className="text-xs text-muted-foreground">{i.alerts} alerts correlated — {i.created}</p>
                </div>
              </div>
              <Badge variant={i.status === "firing" ? "default" : "outline"}>{i.status}</Badge>
            </div>
          ))}
        </TabsContent>
        <TabsContent value="suppression" className="space-y-2">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              {[{name:"HighCPU",duration:60,active:true},{name:"DiskCheck",duration:120,active:false}].map(s => (
                <div key={s.name} className="flex items-center justify-between p-3 bg-muted rounded-lg">
                  <div><p className="font-medium">{s.name}</p><p className="text-xs text-muted-foreground">{s.duration}m duration</p></div>
                  <Badge variant={s.active?"default":"secondary"}>{s.active?"Active":"Inactive"}</Badge>
                </div>
              ))}
            </div>
            <SuppressionHistoryPanel />
          </div>
        </TabsContent>
        <TabsContent value="sources">
          <div className="grid gap-4 md:grid-cols-2">
            <SourceBreakdownChart />
            <TimeSeriesChart />
          </div>
        </TabsContent>
        <TabsContent value="rules">
          <CorrelationRulesPanel />
        </TabsContent>
        <TabsContent value="stats">
          <div className="grid gap-4 md:grid-cols-2">
            <Card><CardHeader><CardTitle className="text-sm">Noise Reduction</CardTitle></CardHeader><CardContent><div className="text-3xl font-bold text-green-500">67%</div></CardContent></Card>
            <Card><CardHeader><CardTitle className="text-sm">Avg Correlation Time</CardTitle></CardHeader><CardContent><div className="text-3xl font-bold">1.2s</div></CardContent></Card>
            <Card><CardHeader><CardTitle className="text-sm">Duplicate Rate</CardTitle></CardHeader><CardContent><div className="text-3xl font-bold">23%</div></CardContent></Card>
            <Card><CardHeader><CardTitle className="text-sm">Alert/Incident Ratio</CardTitle></CardHeader><CardContent><div className="text-3xl font-bold">4.7:1</div></CardContent></Card>
          </div>
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
