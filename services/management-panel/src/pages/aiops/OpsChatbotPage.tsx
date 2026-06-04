import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useState } from "react";

const quickCommands = [
  { cmd: "restart nginx", desc: "Restart a service" },
  { cmd: "logs api-gateway", desc: "View service logs" },
  { cmd: "backup postgres", desc: "Create a backup" },
  { cmd: "status web-server", desc: "Check service status" },
  { cmd: "list services", desc: "List all services" },
  { cmd: "scale api-service 5", desc: "Scale a service" },
  { cmd: "clear cache cdn", desc: "Clear service cache" },
  { cmd: "metrics gateway", desc: "Show service metrics" },
];

const userRoles = [
  { role: "Admin", users: 4, permissions: "Full access" },
  { role: "Operator", users: 12, permissions: "Execute commands, view logs" },
  { role: "Viewer", users: 28, permissions: "Read-only, status checks" },
];

const taskBreakdown = [
  { category: "Status Checks", count: 845 },
  { category: "Service Control", count: 412 },
  { category: "Log Retrieval", count: 298 },
  { category: "Deployments", count: 156 },
  { category: "Backup Jobs", count: 86 },
  { category: "Scaling", count: 50 },
];

function RBACPanel() {
  return (
    <Card><CardHeader><CardTitle>RBAC Roles</CardTitle></CardHeader>
      <CardContent className="space-y-2">
        {userRoles.map(r => (
          <div key={r.role} className="flex items-center justify-between p-2 bg-muted rounded-lg">
            <div><p className="font-medium text-sm">{r.role}</p><p className="text-xs text-muted-foreground">{r.users} users</p></div>
            <Badge variant="outline">{r.permissions}</Badge>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

function TaskBreakdownPanel() {
  return (
    <Card><CardHeader><CardTitle>Task Breakdown</CardTitle></CardHeader>
      <CardContent className="space-y-2">
        {taskBreakdown.map(t => (
          <div key={t.category} className="flex items-center justify-between">
            <span className="text-sm font-medium">{t.category}</span>
            <div className="flex items-center gap-2">
              <div className="w-24 bg-muted rounded-full h-2"><div className="bg-primary h-2 rounded-full" style={{width: `${(t.count / taskBreakdown[0].count) * 100}%`}} /></div>
              <span className="text-xs font-mono">{t.count}</span>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

function AuditLogPanel() {
  const auditEntries = [
    { user: "admin", command: "restart api-gateway", status: "success", time: "5m ago", ip: "10.0.1.42" },
    { user: "devops", command: "deploy v3.2", status: "success", time: "15m ago", ip: "10.0.1.85" },
    { user: "sre", command: "backup postgres", status: "success", time: "1h ago", ip: "10.0.2.10" },
    { user: "viewer", command: "status web-server (DENIED)", status: "allowed", time: "2h ago", ip: "10.0.3.22" },
  ];
  return (
    <Card><CardHeader><CardTitle>Audit Log</CardTitle></CardHeader>
      <CardContent className="space-y-1">
        {auditEntries.map((a, i) => (
          <div key={i} className="flex items-center justify-between p-2 text-xs border-b last:border-0">
            <div className="flex items-center gap-2">
              <span className="font-medium">{a.user}</span>
              <span className="text-muted-foreground">{a.command}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-muted-foreground">{a.time}</span>
              <Badge variant={a.status === "success" ? "default" : "secondary"}>{a.status}</Badge>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

export default function OpsChatbotPage() {
  const [messages, setMessages] = useState<Array<{role: string; content: string}>>([]);
  const [input, setInput] = useState("");
  const [activeTab, setActiveTab] = useState("chat");

  const sendMessage = () => {
    if (!input.trim()) return;
    setMessages(prev => [...prev, { role: "user", content: input }]);
    setTimeout(() => {
      setMessages(prev => [...prev, { role: "assistant", content: `✅ **${input}** — Task completed successfully!` }]);
    }, 400);
    setInput("");
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Self-Service Ops Chatbot</h1>
          <p className="text-muted-foreground">Chatbot for common operations tasks with RBAC</p>
        </div>
        <Badge variant="secondary" className="text-sm">382 Tasks Today</Badge>
      </div>
      <div className="grid gap-4 md:grid-cols-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Total Tasks</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">1,847</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Completed</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold text-green-500">1,782</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Failed</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold text-red-500">42</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Success Rate</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold text-green-500">96.5%</div></CardContent></Card>
      </div>
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="chat">Chat</TabsTrigger>
          <TabsTrigger value="tasks">Tasks</TabsTrigger>
          <TabsTrigger value="rbac">RBAC</TabsTrigger>
          <TabsTrigger value="audit">Audit Log</TabsTrigger>
        </TabsList>
        <TabsContent value="chat">
          <div className="grid gap-4 md:grid-cols-3">
            <Card className="md:col-span-2">
              <CardHeader><CardTitle>Chat</CardTitle></CardHeader>
              <CardContent>
                <div className="h-64 overflow-y-auto mb-4 space-y-3 border rounded-lg p-4 bg-muted/30">
                  {messages.length === 0 && (
                    <div className="text-center text-muted-foreground py-6">
                      <p className="text-lg mb-1">🤖 Ops Bot</p>
                      <p className="text-sm">Type a command or choose from the quick actions!</p>
                    </div>
                  )}
                  {messages.map((m, i) => (
                    <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                      <div className={`max-w-[80%] p-3 rounded-lg text-sm ${m.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted"}`}>
                        {m.content}
                      </div>
                    </div>
                  ))}
                </div>
                <div className="flex gap-2">
                  <Input placeholder="Type a command..." value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === "Enter" && sendMessage()} />
                  <Button onClick={sendMessage}>Send</Button>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle>Quick Commands</CardTitle></CardHeader>
              <CardContent className="space-y-2">
                {quickCommands.map(q => (
                  <button key={q.cmd} className="w-full text-left p-2 text-sm bg-muted rounded-lg hover:bg-primary/10 transition-colors"
                    onClick={() => { setMessages(prev => [...prev, { role: "user", content: q.cmd }]); setMessages(prev => [...prev, { role: "assistant", content: `✅ **${q.cmd}** — ${q.desc}. Task completed!` }]); }}>
                    <span className="font-medium">{q.cmd}</span>
                    <span className="block text-xs text-muted-foreground">{q.desc}</span>
                  </button>
                ))}
              </CardContent>
            </Card>
          </div>
        </TabsContent>
        <TabsContent value="tasks">
          <TaskBreakdownPanel />
        </TabsContent>
        <TabsContent value="rbac">
          <RBACPanel />
        </TabsContent>
        <TabsContent value="audit">
          <AuditLogPanel />
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
