import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from "recharts";

const monitors = [
  { name: "Main Website", url: "https://example.com", type: "browser_synthetic", uptime: 99.8, status: "active", lcp: 1234, cls: 0.08 },
  { name: "API Gateway", url: "https://api.example.com/health", type: "api_check", uptime: 99.95, status: "active", lcp: 0, cls: 0 },
  { name: "Checkout Flow", url: "https://example.com/checkout", type: "multi_step", uptime: 98.5, status: "active", lcp: 2100, cls: 0.15 },
  { name: "Dashboard", url: "https://app.example.com", type: "browser_synthetic", uptime: 99.2, status: "paused", lcp: 1800, cls: 0.1 },
];

const vitalsData = [
  { day: "Mon", lcp: 1200, cls: 0.08, fid: 12 },
  { day: "Tue", lcp: 1400, cls: 0.1, fid: 15 },
  { day: "Wed", lcp: 1100, cls: 0.07, fid: 10 },
  { day: "Thu", lcp: 1600, cls: 0.12, fid: 18 },
  { day: "Fri", lcp: 1300, cls: 0.09, fid: 14 },
  { day: "Sat", lcp: 1000, cls: 0.06, fid: 8 },
  { day: "Sun", lcp: 900, cls: 0.05, fid: 7 },
];

const geoData = [
  { region: "US-East", avgLcp: 1100, avgCls: 0.08, avgUptime: 99.9 },
  { region: "US-West", avgLcp: 1200, avgCls: 0.09, avgUptime: 99.7 },
  { region: "EU-West", avgLcp: 1400, avgCls: 0.10, avgUptime: 99.5 },
  { region: "APAC", avgLcp: 1800, avgCls: 0.14, avgUptime: 98.8 },
];

const healthChecks = [
  { endpoint: "GET /api/health", status: "up", latency: 45, lastCheck: "30s ago" },
  { endpoint: "GET /api/users", status: "up", latency: 120, lastCheck: "1m ago" },
  { endpoint: "POST /api/orders", status: "degraded", latency: 450, lastCheck: "45s ago" },
  { endpoint: "GET /static/app.js", status: "up", latency: 30, lastCheck: "2m ago" },
];

function GeoPerformancePanel() {
  return (
    <Card><CardHeader><CardTitle>Performance by Region</CardTitle></CardHeader>
      <CardContent className="space-y-2">
        {geoData.map(g => (
          <div key={g.region} className="flex items-center justify-between p-2 border-b last:border-0">
            <span className="text-sm font-medium">{g.region}</span>
            <div className="flex items-center gap-3 text-xs">
              <span>LCP: {g.avgLcp}ms</span>
              <span>CLS: {g.avgCls}</span>
              <Badge variant={g.avgUptime >= 99.5 ? "default" : "destructive"}>{g.avgUptime}%</Badge>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

function HealthCheckPanel() {
  return (
    <Card><CardHeader><CardTitle>Endpoint Health Checks</CardTitle></CardHeader>
      <CardContent className="space-y-2">
        {healthChecks.map(h => (
          <div key={h.endpoint} className="flex items-center justify-between p-2 bg-muted rounded-lg text-sm">
            <div><p className="font-medium">{h.endpoint}</p><p className="text-xs text-muted-foreground">{h.lastCheck}</p></div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono">{h.latency}ms</span>
              <Badge variant={h.status === "up" ? "default" : h.status === "degraded" ? "secondary" : "destructive"}>{h.status}</Badge>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

function RegressionAlertPanel() {
  const alerts = [
    { monitor: "Checkout Flow", metric: "LCP", baseline: 1200, current: 2100, deviation: "+75%", severity: "critical" },
    { monitor: "Main Website", metric: "CLS", baseline: 0.08, current: 0.15, deviation: "+87%", severity: "warning" },
  ];
  return (
    <Card><CardHeader><CardTitle>Performance Regressions</CardTitle></CardHeader>
      <CardContent className="space-y-2">
        {alerts.map((a, i) => (
          <div key={i} className="flex items-center justify-between p-2 bg-muted rounded-lg">
            <div><p className="font-medium text-sm">{a.monitor}</p><p className="text-xs text-muted-foreground">{a.metric}: {a.baseline} → {a.current}</p></div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-red-500">{a.deviation}</span>
              <Badge variant={a.severity === "critical" ? "destructive" : "secondary"}>{a.severity}</Badge>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

export default function DigitalExperiencePage() {
  const [activeTab, setActiveTab] = useState("overview");
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Digital Experience Monitoring</h1>
          <p className="text-muted-foreground">Synthetic browser monitoring and Core Web Vitals tracking</p>
        </div>
        <Button>Add Monitor</Button>
      </div>
      <div className="grid gap-4 md:grid-cols-5">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Monitors</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">12</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Avg Uptime</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold text-green-500">99.4%</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Avg LCP</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold text-yellow-500">1.3s</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Avg CLS</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold text-green-500">0.09</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Checks Today</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">2,847</div></CardContent></Card>
      </div>
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="geo">Geo Performance</TabsTrigger>
          <TabsTrigger value="health">Health Checks</TabsTrigger>
          <TabsTrigger value="regressions">Regressions</TabsTrigger>
        </TabsList>
        <TabsContent value="overview">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader><CardTitle>Core Web Vitals Trend</CardTitle></CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={250}>
                  <LineChart data={vitalsData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="day" />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey="lcp" stroke="#3b82f6" name="LCP (ms)" />
                    <Line type="monotone" dataKey="fid" stroke="#10b981" name="FID (ms)" />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle>Monitors</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                {monitors.map(m => (
                  <div key={m.name} className="flex items-center justify-between p-2 border-b last:border-0">
                    <div>
                      <p className="font-medium">{m.name}</p>
                      <p className="text-xs text-muted-foreground">{m.url}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={m.status === "active" ? "default" : "secondary"}>{m.status}</Badge>
                      <span className="text-sm font-mono">{m.uptime}%</span>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </TabsContent>
        <TabsContent value="geo">
          <GeoPerformancePanel />
        </TabsContent>
        <TabsContent value="health">
          <HealthCheckPanel />
        </TabsContent>
        <TabsContent value="regressions">
          <RegressionAlertPanel />
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
