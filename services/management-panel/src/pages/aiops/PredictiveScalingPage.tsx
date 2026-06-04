import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from "recharts";

const forecastData = [
  { time: "Now", actual: 45, predicted: 45 },
  { time: "+5m", predicted: 48 },
  { time: "+10m", predicted: 52 },
  { time: "+15m", predicted: 58 },
  { time: "+20m", predicted: 55 },
  { time: "+25m", predicted: 50 },
  { time: "+30m", predicted: 52 },
  { time: "+35m", predicted: 56 },
  { time: "+40m", predicted: 60 },
  { time: "+45m", predicted: 58 },
  { time: "+50m", predicted: 55 },
  { time: "+55m", predicted: 52 },
  { time: "+60m", predicted: 50 },
];

const resources = [
  { name: "web-server-01", metric: "cpu", current: 45, peak: 62, confidence: 0.88, direction: "stable", policy: "moderate" },
  { name: "api-gateway", metric: "cpu", current: 72, peak: 95, confidence: 0.92, direction: "scale_up", policy: "aggressive" },
  { name: "postgres-db", metric: "memory", current: 68, peak: 85, confidence: 0.85, direction: "stable", policy: "conservative" },
  { name: "worker-queue", metric: "cpu", current: 22, peak: 35, confidence: 0.79, direction: "scale_down", policy: "moderate" },
];

const alertData = [
  { resource: "api-gateway", type: "cpu", severity: "warning", message: "Sustained high load predicted", threshold: 85, time: "12m ago" },
  { resource: "postgres-db", type: "memory", severity: "info", message: "Memory forecast trending up", threshold: 80, time: "25m ago" },
];

const historyData = [
  { day: "Mon", actions: 3, accuracy: 92 },
  { day: "Tue", actions: 5, accuracy: 88 },
  { day: "Wed", actions: 2, accuracy: 95 },
  { day: "Thu", actions: 4, accuracy: 90 },
  { day: "Fri", actions: 1, accuracy: 97 },
  { day: "Sat", actions: 0, accuracy: 100 },
  { day: "Sun", actions: 2, accuracy: 93 },
];

const recommendations = [
  { resource: "web-server-03", metric: "cpu", suggested: "scale_up", currentReplicas: 2, suggestedReplicas: 4, savings: "$120/mo", priority: "high" },
  { resource: "worker-queue", metric: "cpu", suggested: "scale_down", currentReplicas: 6, suggestedReplicas: 3, savings: "$180/mo", priority: "medium" },
  { resource: "redis-cache", metric: "memory", suggested: "resize", currentReplicas: 2, suggestedReplicas: 4, savings: "$60/mo", priority: "low" },
];

function ScalingAlertsSection() {
  const [showAll, setShowAll] = useState(false);
  const items = showAll ? alertData : alertData.slice(0, 2);
  return (
    <Card>
      <CardHeader><CardTitle>Scaling Alerts</CardTitle></CardHeader>
      <CardContent className="space-y-2">
        {items.map((a, i) => (
          <div key={i} className="flex items-center justify-between p-2 bg-muted rounded-lg">
            <div><p className="font-medium text-sm">{a.resource}</p><p className="text-xs text-muted-foreground">{a.message}</p></div>
            <Badge variant={a.severity === "warning" ? "destructive" : "secondary"}>{a.severity}</Badge>
          </div>
        ))}
        {alertData.length > 2 && <Button variant="ghost" size="sm" onClick={() => setShowAll(!showAll)}>{showAll ? "Show Less" : "Show All"}</Button>}
      </CardContent>
    </Card>
  );
}

function AccuracyTrendSection() {
  return (
    <Card>
      <CardHeader><CardTitle>Prediction Accuracy Trend (7d)</CardTitle></CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={historyData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="day" />
            <YAxis domain={[0, 100]} />
            <Tooltip />
            <Bar dataKey="accuracy" fill="#10b981" name="Accuracy %" />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

function SchedulingPanel() {
  const schedules = [
    { resource: "api-gateway", schedule: "M-F 8am-8pm", min: 4, max: 12, active: true },
    { resource: "batch-workers", schedule: "Daily 2am-6am", min: 1, max: 8, active: true },
    { resource: "web-frontend", schedule: "Always", min: 3, max: 10, active: false },
  ];
  return (
    <Card>
      <CardHeader><CardTitle>Scheduled Scaling Policies</CardTitle></CardHeader>
      <CardContent className="space-y-2">
        {schedules.map(s => (
          <div key={s.resource} className="flex items-center justify-between p-2 border-b last:border-0">
            <div><p className="font-medium text-sm">{s.resource}</p><p className="text-xs text-muted-foreground">{s.schedule} ({s.min}-{s.max})</p></div>
            <Badge variant={s.active ? "default" : "secondary"}>{s.active ? "Active" : "Paused"}</Badge>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

function ResourceComparisonChart() {
  const compData = [
    { name: "cpu", predicted: 72, actual: 68 },
    { name: "memory", predicted: 81, actual: 76 },
    { name: "network", predicted: 45, actual: 42 },
    { name: "disk", predicted: 34, actual: 31 },
  ];
  return (
    <Card><CardHeader><CardTitle>Predicted vs Actual</CardTitle></CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={compData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="predicted" fill="#3b82f6" name="Predicted" />
            <Bar dataKey="actual" fill="#10b981" name="Actual" />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

export default function PredictiveScalingPage() {
  const [activeTab, setActiveTab] = useState("overview");
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Predictive Auto-Scaling</h1>
          <p className="text-muted-foreground">ML-based workload prediction and proactive resource scaling</p>
        </div>
        <Badge variant="secondary" className="text-sm">Auto-Scale Enabled</Badge>
      </div>
      <div className="grid gap-4 md:grid-cols-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Resources</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">24</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Predictions Today</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">1,247</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Scaling Actions</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold text-yellow-500">3</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Cost Saved</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold text-green-500">$342</div></CardContent></Card>
      </div>
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="alerts">Alerts</TabsTrigger>
          <TabsTrigger value="schedules">Schedules</TabsTrigger>
          <TabsTrigger value="recommendations">Recommendations</TabsTrigger>
        </TabsList>
        <TabsContent value="overview">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader><CardTitle>CPU Forecast: api-gateway</CardTitle></CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={250}>
                  <LineChart data={forecastData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" />
                    <YAxis domain={[0, 100]} />
                    <Tooltip />
                    <Line type="monotone" dataKey="actual" stroke="#3b82f6" name="Actual" strokeWidth={2} />
                    <Line type="monotone" dataKey="predicted" stroke="#10b981" name="Predicted" strokeDasharray="5 5" />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle>Resource Overview</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                {resources.map(r => (
                  <div key={r.name} className="flex items-center justify-between p-2 border-b last:border-0">
                    <div>
                      <p className="font-medium">{r.name}</p>
                      <p className="text-xs text-muted-foreground">{r.metric} — Policy: {r.policy}</p>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-sm">{r.current}%</span>
                      <Badge variant={r.direction === "scale_up" ? "destructive" : r.direction === "scale_down" ? "default" : "secondary"}>
                        {r.direction}
                      </Badge>
                      <span className="text-xs text-muted-foreground">{(r.confidence * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
            <AccuracyTrendSection />
            <ResourceComparisonChart />
          </div>
        </TabsContent>
        <TabsContent value="alerts">
          <ScalingAlertsSection />
        </TabsContent>
        <TabsContent value="schedules">
          <SchedulingPanel />
        </TabsContent>
        <TabsContent value="recommendations">
          <Card>
            <CardHeader><CardTitle>Optimization Recommendations</CardTitle></CardHeader>
            <CardContent className="space-y-3">
              {recommendations.map(r => (
                <div key={r.resource} className="flex items-center justify-between p-3 bg-muted rounded-lg">
                  <div><p className="font-medium">{r.resource}</p><p className="text-xs text-muted-foreground">{r.metric} — {r.currentReplicas} → {r.suggestedReplicas} replicas</p></div>
                  <div className="flex items-center gap-2">
                    <Badge variant={r.priority === "high" ? "destructive" : "secondary"}>{r.priority}</Badge>
                    <span className="text-xs text-green-500">{r.savings}</span>
                    <Button size="sm" variant="outline">Apply</Button>
                  </div>
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
