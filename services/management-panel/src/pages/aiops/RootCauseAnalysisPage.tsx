import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useState } from "react";

const mockIncidents = [
  { id: "INC-001", title: "Database Connection Pool Exhaustion", severity: "critical", status: "analyzing", time: "5m ago", confidence: 0.92 },
  { id: "INC-002", title: "API Gateway Latency Spike", severity: "high", status: "analyzed", time: "15m ago", confidence: 0.85 },
  { id: "INC-003", title: "Cache Cluster Node Failure", severity: "medium", status: "analyzed", time: "1h ago", confidence: 0.78 },
  { id: "INC-004", title: "SSL Certificate Expiry", severity: "warning", status: "analyzed", time: "2h ago", confidence: 0.95 },
];

const patternsData = [
  { id: "PT-001", name: "Connection Pool Exhaustion", frequency: 8, services: ["database", "api-gateway"], avgImpact: "critical", confidence: 0.91 },
  { id: "PT-002", name: "Memory Leak Cascade", frequency: 5, services: ["cache", "web-server"], avgImpact: "high", confidence: 0.84 },
  { id: "PT-003", name: "Deploy-Induced Latency", frequency: 12, services: ["api-gateway", "web-app"], avgImpact: "medium", confidence: 0.76 },
];

const impactScores = [
  { service: "api-gateway", score: 92, events: 45, status: "critical" },
  { service: "database", score: 78, events: 23, status: "high" },
  { service: "web-server", score: 45, events: 12, status: "medium" },
  { service: "redis-cache", score: 34, events: 8, status: "low" },
];

function PatternsPanel() {
  return (
    <Card><CardHeader><CardTitle>Detected Correlation Patterns</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        {patternsData.map(p => (
          <div key={p.id} className="flex items-center justify-between p-3 bg-muted rounded-lg">
            <div><p className="font-medium text-sm">{p.name}</p><p className="text-xs text-muted-foreground">Observed {p.frequency}x — Services: {p.services.join(", ")}</p></div>
            <div className="flex items-center gap-2">
              <Badge variant={p.avgImpact === "critical" ? "destructive" : "secondary"}>{p.avgImpact}</Badge>
              <span className="text-xs font-mono">{(p.confidence * 100).toFixed(0)}%</span>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

function ImpactChart() {
  return (
    <Card><CardHeader><CardTitle>Service Impact Scores</CardTitle></CardHeader>
      <CardContent className="space-y-2">
        {impactScores.map(s => (
          <div key={s.service} className="flex items-center justify-between">
            <span className="text-sm font-medium">{s.service}</span>
            <div className="flex items-center gap-2">
              <div className="w-24 bg-muted rounded-full h-2"><div className="bg-primary h-2 rounded-full" style={{width: `${s.score}%`}} /></div>
              <span className="text-xs font-mono">{s.score}</span>
              <Badge variant={s.status === "critical" ? "destructive" : "secondary"} className="text-xs">{s.status}</Badge>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

function SuggestedRemediations() {
  const suggestions = [
    { pattern: "Connection Pool Exhaustion", action: "Increase max_connections", confidence: 0.92 },
    { pattern: "Memory Leak Cascade", action: "Restart cache service", confidence: 0.87 },
    { pattern: "Deploy-Induced Latency", action: "Rollback to previous deploy", confidence: 0.78 },
  ];
  return (
    <Card><CardHeader><CardTitle>AI-Suggested Remediations</CardTitle></CardHeader>
      <CardContent className="space-y-2">
        {suggestions.map(s => (
          <div key={s.pattern} className="flex items-center justify-between p-2 border-b last:border-0">
            <div><p className="font-medium text-sm">{s.action}</p><p className="text-xs text-muted-foreground">For: {s.pattern}</p></div>
            <span className="text-xs font-mono">{(s.confidence * 100).toFixed(0)}% confidence</span>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

export default function RootCauseAnalysisPage() {
  const [selected, setSelected] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("incidents");
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Root Cause Analysis</h1>
          <p className="text-muted-foreground">ML-powered incident correlation and root cause identification</p>
        </div>
        <Badge variant="secondary" className="text-sm">3 Active Incidents</Badge>
      </div>
      <div className="grid gap-4 md:grid-cols-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Active Incidents</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold text-red-500">4</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Avg RCA Time</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">2.3s</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Avg Confidence</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold text-green-500">87.5%</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Events Processed</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">12,847</div></CardContent></Card>
      </div>
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="incidents">Incidents</TabsTrigger>
          <TabsTrigger value="events">Event Stream</TabsTrigger>
          <TabsTrigger value="patterns">Patterns</TabsTrigger>
          <TabsTrigger value="impact">Impact</TabsTrigger>
          <TabsTrigger value="dependencies">Dependency Graph</TabsTrigger>
          <TabsTrigger value="remediations">Remediations</TabsTrigger>
        </TabsList>
        <TabsContent value="incidents" className="space-y-4">
          {mockIncidents.map((inc) => (
            <Card key={inc.id} className={`cursor-pointer transition-colors ${selected === inc.id ? 'ring-2 ring-blue-500' : ''}`} onClick={() => setSelected(inc.id)}>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Badge variant={inc.severity === "critical" ? "destructive" : inc.severity === "high" ? "default" : "secondary"}>
                      {inc.severity}
                    </Badge>
                    <div>
                      <p className="font-medium">{inc.title}</p>
                      <p className="text-sm text-muted-foreground">{inc.id} — {inc.time}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <Badge variant="outline">{inc.status}</Badge>
                    <span className="text-sm font-mono">{(inc.confidence * 100).toFixed(0)}%</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>
        <TabsContent value="events" className="space-y-2">
          {[{type:"error",source:"api-gateway",title:"Timeout",severity:"high",time:"1m ago"},{type:"metric",source:"prometheus",title:"CPU>90%",severity:"critical",time:"3m ago"},{type:"log",source:"database",title:"Connection refused",severity:"warning",time:"5m ago"}].map((e,i) => (
            <div key={i} className="flex items-center justify-between p-3 bg-muted rounded-lg">
              <div className="flex items-center gap-3">
                <Badge variant={e.severity==="critical"?"destructive":"secondary"}>{e.severity}</Badge>
                <div><p className="font-medium">{e.title}</p><p className="text-xs text-muted-foreground">{e.source} — {e.time}</p></div>
              </div>
              <Badge variant="outline">{e.type}</Badge>
            </div>
          ))}
        </TabsContent>
        <TabsContent value="patterns">
          <PatternsPanel />
        </TabsContent>
        <TabsContent value="impact">
          <div className="grid gap-4 md:grid-cols-2">
            <ImpactChart />
            <Card><CardHeader><CardTitle>Impact Summary</CardTitle></CardHeader>
              <CardContent><div className="text-4xl font-bold text-red-500">4</div><p className="text-sm text-muted-foreground">Services currently impacted</p>
                <div className="mt-4 space-y-2">{impactScores.filter(s => s.status === "critical" || s.status === "high").map(s => (
                  <div key={s.service} className="flex items-center justify-between p-2 bg-muted rounded-lg">
                    <span className="text-sm font-medium">{s.service}</span><Badge variant="destructive">{s.status}</Badge>
                  </div>
                ))}</div></CardContent></Card>
          </div>
        </TabsContent>
        <TabsContent value="dependencies">
          <div className="grid gap-4 md:grid-cols-2">
            {[{svc:"api-gateway",deps:["auth","redis"]},{svc:"web-app",deps:["api-gateway"]},{svc:"database",deps:["storage"]},{svc:"auth",deps:["database"]}].map(d => (
              <Card key={d.svc}><CardContent className="p-4">
                <p className="font-medium">{d.svc}</p>
                <p className="text-sm text-muted-foreground">Depends on: {d.deps.join(", ") || "None"}</p>
              </CardContent></Card>
            ))}
          </div>
        </TabsContent>
        <TabsContent value="remediations">
          <SuggestedRemediations />
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
