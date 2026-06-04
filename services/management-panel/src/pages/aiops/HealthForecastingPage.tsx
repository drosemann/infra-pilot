import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from "recharts";

const forecastScores = [
  { hour: "Now", score: 0.92 },
  { hour: "+4h", score: 0.88 },
  { hour: "+8h", score: 0.85 },
  { hour: "+12h", score: 0.82 },
  { hour: "+16h", score: 0.78 },
  { hour: "+20h", score: 0.74 },
  { hour: "+24h", score: 0.71 },
];

const services = [
  { name: "Web Server", score: 0.92, health: "healthy", trend: "stable", forecast: 0.88 },
  { name: "API Gateway", score: 0.78, health: "degraded", trend: "degrading", forecast: 0.65 },
  { name: "Database", score: 0.95, health: "healthy", trend: "improving", forecast: 0.97 },
  { name: "Cache Cluster", score: 0.72, health: "degraded", trend: "degrading", forecast: 0.58 },
  { name: "Worker Queue", score: 0.88, health: "healthy", trend: "stable", forecast: 0.85 },
];

const anomalyData = [
  { service: "API Gateway", metric: "latency", observed: 450, expected: 120, deviation: "+275%", severity: "high", detected: "10m ago" },
  { service: "Cache Cluster", metric: "hit_rate", observed: 0.72, expected: 0.92, deviation: "-22%", severity: "medium", detected: "25m ago" },
  { service: "Database", metric: "connection_pool", observed: 88, expected: 45, deviation: "+95%", severity: "high", detected: "1h ago" },
];

const forecastHistory = [
  { week: "W1", predicted: 0.88, actual: 0.91 },
  { week: "W2", predicted: 0.85, actual: 0.82 },
  { week: "W3", predicted: 0.82, actual: 0.86 },
  { week: "W4", predicted: 0.79, actual: 0.81 },
  { week: "W5", predicted: 0.76, actual: 0.74 },
  { week: "W6", predicted: 0.74, actual: 0.77 },
];

function AnomalyPanel() {
  return (
    <Card><CardHeader><CardTitle>Recent Anomalies</CardTitle></CardHeader>
      <CardContent className="space-y-2">
        {anomalyData.map((a, i) => (
          <div key={i} className="flex items-center justify-between p-2 bg-muted rounded-lg">
            <div><p className="font-medium text-sm">{a.service} — {a.metric}</p><p className="text-xs text-muted-foreground">Expected: {a.expected} → Observed: {a.observed}</p></div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-red-500">{a.deviation}</span>
              <Badge variant={a.severity === "high" ? "destructive" : "secondary"}>{a.severity}</Badge>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

function ForecastAccuracy() {
  return (
    <Card><CardHeader><CardTitle>Forecast Accuracy (6 Weeks)</CardTitle></CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={forecastHistory}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="week" />
            <YAxis domain={[0, 1]} />
            <Tooltip />
            <Line type="monotone" dataKey="predicted" stroke="#3b82f6" name="Predicted" strokeDasharray="5 5" />
            <Line type="monotone" dataKey="actual" stroke="#10b981" name="Actual" />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

function DeterioratingServices() {
  const deteriorating = [
    { name: "API Gateway", currentScore: 0.72, score30dAgo: 0.88, decline: "-18%", estimatedFailure: "5-7 days" },
    { name: "Cache Cluster", currentScore: 0.78, score30dAgo: 0.91, decline: "-14%", estimatedFailure: "8-12 days" },
  ];
  return (
    <Card><CardHeader><CardTitle>Deteriorating Services</CardTitle></CardHeader>
      <CardContent className="space-y-2">
        {deteriorating.map(d => (
          <div key={d.name} className="flex items-center justify-between p-2 border-b last:border-0">
            <div><p className="font-medium text-sm">{d.name}</p><p className="text-xs text-muted-foreground">{d.score30dAgo} → {d.currentScore}</p></div>
            <div className="text-right"><Badge variant="destructive">{d.decline}</Badge><p className="text-xs text-muted-foreground mt-1">{d.estimatedFailure}</p></div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

export default function HealthForecastingPage() {
  const [activeTab, setActiveTab] = useState("overview");
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Service Health Forecasting</h1>
          <p className="text-muted-foreground">Predict future service health based on current trends</p>
        </div>
        <Badge variant="secondary" className="text-sm">3 Services At Risk</Badge>
      </div>
      <div className="grid gap-4 md:grid-cols-5">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Services</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">15</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Healthy</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold text-green-500">10</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Degraded</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold text-yellow-500">3</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Critical</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold text-red-500">2</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Avg Score</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold text-yellow-500">84%</div></CardContent></Card>
      </div>
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="anomalies">Anomalies</TabsTrigger>
          <TabsTrigger value="accuracy">Accuracy</TabsTrigger>
          <TabsTrigger value="deteriorating">Deteriorating</TabsTrigger>
        </TabsList>
        <TabsContent value="overview">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader><CardTitle>24h Health Forecast</CardTitle></CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={250}>
                  <AreaChart data={forecastScores}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="hour" />
                    <YAxis domain={[0, 1]} />
                    <Tooltip />
                    <Area type="monotone" dataKey="score" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.1} />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle>Service Health Status</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                {services.map(s => (
                  <div key={s.name} className="flex items-center justify-between p-2 border-b last:border-0">
                    <div className="flex items-center gap-3">
                      <div className={`w-2 h-2 rounded-full ${s.health === "healthy" ? "bg-green-500" : "bg-yellow-500"}`} />
                      <div>
                        <p className="font-medium">{s.name}</p>
                        <p className="text-xs text-muted-foreground">Trend: {s.trend}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-mono">{(s.score * 100).toFixed(0)}%</span>
                      <Badge variant={s.health === "healthy" ? "default" : "destructive"}>{s.health}</Badge>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </TabsContent>
        <TabsContent value="anomalies">
          <AnomalyPanel />
        </TabsContent>
        <TabsContent value="accuracy">
          <ForecastAccuracy />
        </TabsContent>
        <TabsContent value="deteriorating">
          <DeterioratingServices />
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
