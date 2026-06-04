import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from "recharts";

const recommendations = [
  { resource: "web-server-cluster", type: "cpu", priority: "critical", current: 82, peak: 96, daysLeft: 12, cost: 420 },
  { resource: "postgres-db", type: "memory", priority: "high", current: 74, peak: 88, daysLeft: 45, cost: 280 },
  { resource: "redis-cache", type: "memory", priority: "medium", current: 65, peak: 78, daysLeft: 90, cost: 150 },
  { resource: "object-storage", type: "storage", priority: "low", current: 55, peak: 62, daysLeft: 180, cost: 80 },
];

const scenarios = [
  { name: "Black Friday", peak: 185, added: 3, cost: 1260 },
  { name: "Traffic Spike 2x", peak: 165, added: 2, cost: 840 },
  { name: "New Customer Wave", peak: 145, added: 2, cost: 840 },
  { name: "Feature Launch", peak: 130, added: 1, cost: 420 },
];

const historyData = [
  { month: "Jan", cpu: 52, memory: 61, storage: 38 },
  { month: "Feb", cpu: 55, memory: 63, storage: 40 },
  { month: "Mar", cpu: 58, memory: 66, storage: 43 },
  { month: "Apr", cpu: 60, memory: 68, storage: 45 },
  { month: "May", cpu: 62, memory: 71, storage: 48 },
  { month: "Jun", cpu: 65, memory: 74, storage: 50 },
];

const forecastingData = [
  { resource: "web-server-cluster", type: "cpu", trend: "growing", growthRate: 8.2, projected: 96, monthsUntilFull: 2.1 },
  { resource: "postgres-db", type: "memory", trend: "growing", growthRate: 5.7, projected: 88, monthsUntilFull: 4.3 },
  { resource: "redis-cache", type: "memory", trend: "stable", growthRate: 1.2, projected: 72, monthsUntilFull: 18.5 },
  { resource: "object-storage", type: "storage", trend: "growing", growthRate: 3.5, projected: 65, monthsUntilFull: 12.0 },
];

function TrendChart() {
  return (
    <Card><CardHeader><CardTitle>Monthly Utilization Trends</CardTitle></CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={historyData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis />
            <Tooltip />
            <Line type="monotone" dataKey="cpu" stroke="#3b82f6" name="CPU" />
            <Line type="monotone" dataKey="memory" stroke="#10b981" name="Memory" />
            <Line type="monotone" dataKey="storage" stroke="#f59e0b" name="Storage" />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

function ForecastSection() {
  return (
    <Card><CardHeader><CardTitle>Growth Forecast</CardTitle></CardHeader>
      <CardContent className="space-y-2">
        {forecastingData.map(f => (
          <div key={f.resource} className="flex items-center justify-between p-2 border-b last:border-0">
            <div><p className="font-medium text-sm">{f.resource}</p><p className="text-xs text-muted-foreground">{f.type.toUpperCase()} — {f.growthRate}%/mo</p></div>
            <div className="flex items-center gap-3">
              <span className="text-xs text-muted-foreground">Full in {f.monthsUntilFull}mo</span>
              <Badge variant={f.monthsUntilFull < 3 ? "destructive" : f.monthsUntilFull < 6 ? "default" : "secondary"}>{f.trend}</Badge>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

function BudgetSection() {
  const budgetData = [
    { category: "Compute", current: 3400, projected: 4200, variance: "+$800" },
    { category: "Storage", current: 1800, projected: 2100, variance: "+$300" },
    { category: "Network", current: 900, projected: 1100, variance: "+$200" },
    { category: "Database", current: 2800, projected: 3600, variance: "+$800" },
  ];
  return (
    <Card><CardHeader><CardTitle>Budget Projection</CardTitle></CardHeader>
      <CardContent className="space-y-2">
        {budgetData.map(b => (
          <div key={b.category} className="flex items-center justify-between p-2 bg-muted rounded-lg">
            <span className="text-sm font-medium">{b.category}</span>
            <div className="flex items-center gap-2">
              <span className="text-xs">${b.current} → ${b.projected}</span>
              <Badge variant="destructive" className="text-xs">{b.variance}</Badge>
            </div>
          </div>
        ))}
        <div className="pt-2 border-t"><div className="flex items-center justify-between"><span className="font-medium">Total</span><span className="font-mono">$8,900 → $11,000</span></div></div>
      </CardContent>
    </Card>
  );
}

export default function CapacityPlanningPage() {
  const [activeTab, setActiveTab] = useState("recommendations");
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">AI-Driven Capacity Planning</h1>
          <p className="text-muted-foreground">Capacity recommendations with what-if simulation</p>
        </div>
        <Badge variant="secondary" className="text-sm">3 Pending Recommendations</Badge>
      </div>
      <div className="grid gap-4 md:grid-cols-5">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Resources Tracked</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">32</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Critical</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold text-red-500">1</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">High</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold text-orange-500">1</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Applied</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold text-green-500">8</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Est. Monthly Savings</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold text-green-500">$1,240</div></CardContent></Card>
      </div>
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="recommendations">Recommendations</TabsTrigger>
          <TabsTrigger value="simulations">What-If</TabsTrigger>
          <TabsTrigger value="forecast">Forecast</TabsTrigger>
          <TabsTrigger value="budget">Budget</TabsTrigger>
          <TabsTrigger value="usage">Usage</TabsTrigger>
        </TabsList>
        <TabsContent value="recommendations" className="space-y-3">
          {recommendations.map(r => (
            <div key={r.resource} className="flex items-center justify-between p-3 bg-muted rounded-lg">
              <div>
                <p className="font-medium">{r.resource}</p>
                <p className="text-xs text-muted-foreground">{r.type.toUpperCase()} — {r.daysLeft} days until threshold</p>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-sm">{r.current}% → {r.peak}%</span>
                <Badge variant={r.priority === "critical" ? "destructive" : r.priority === "high" ? "default" : r.priority === "medium" ? "secondary" : "outline"}>{r.priority}</Badge>
                <span className="text-sm font-mono text-green-500">+${r.cost}/mo</span>
                <Button size="sm" variant="outline">Apply</Button>
              </div>
            </div>
          ))}
        </TabsContent>
        <TabsContent value="simulations" className="space-y-3">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-3">
              {scenarios.map(s => (
                <div key={s.name} className="flex items-center justify-between p-3 bg-muted rounded-lg">
                  <p className="font-medium">{s.name}</p>
                  <div className="flex items-center gap-3">
                    <span className="text-sm">Peak: {s.peak}%</span>
                    <span className="text-sm">+{s.added} nodes</span>
                    <span className="text-sm font-mono text-green-500">+${s.cost}/mo</span>
                    <Button size="sm" variant="outline">Run</Button>
                  </div>
                </div>
              ))}
            </div>
            <Card><CardHeader><CardTitle>Simulation Parameters</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                <div><label className="text-sm font-medium">Traffic Multiplier</label><div className="text-lg font-bold">1.0x-2.0x</div></div>
                <div><label className="text-sm font-medium">Duration</label><div className="text-lg font-bold">4 hours peak</div></div>
                <div><label className="text-sm font-medium">Auto-Scale</label><Badge>Enabled</Badge></div>
              </CardContent></Card>
          </div>
        </TabsContent>
        <TabsContent value="forecast">
          <div className="grid gap-4 md:grid-cols-2">
            <TrendChart />
            <ForecastSection />
          </div>
        </TabsContent>
        <TabsContent value="budget">
          <BudgetSection />
        </TabsContent>
        <TabsContent value="usage">
          <div className="grid gap-4 md:grid-cols-2">
            <Card><CardHeader><CardTitle>Utilization by Type</CardTitle></CardHeader>
            <CardContent className="space-y-3">
              {[{type:"CPU",avg:62,peak:89},{type:"Memory",avg:71,peak:94},{type:"Storage",avg:48,peak:72},{type:"Network",avg:35,peak:58}].map(u => (
                <div key={u.type} className="flex items-center justify-between">
                  <span className="text-sm font-medium">{u.type}</span>
                  <div className="flex items-center gap-2">
                    <div className="w-32 bg-muted rounded-full h-2"><div className="bg-primary h-2 rounded-full" style={{width:`${u.avg}%`}} /></div>
                    <span className="text-xs font-mono">{u.avg}% avg / {u.peak}% peak</span>
                  </div>
                </div>
              ))}
            </CardContent></Card>
            <Card><CardHeader><CardTitle>Top Consumers</CardTitle></CardHeader>
            <CardContent className="space-y-2">
              {[{resource:"api-gateway",usage:88},{resource:"postgres-db",usage:82},{resource:"web-server",usage:76},{resource:"redis-cache",usage:65}].map(c => (
                <div key={c.resource} className="flex items-center justify-between p-2 bg-muted rounded-lg">
                  <span className="text-sm font-medium">{c.resource}</span>
                  <span className="text-sm font-mono">{c.usage}%</span>
                </div>
              ))}
            </CardContent></Card>
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
