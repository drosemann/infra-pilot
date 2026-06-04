import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

const models = [
  { id: "md-001", name: "Image Classifier", framework: "pytorch", params: "1.2M", rounds: 12, accuracy: 0.94 },
  { id: "md-002", name: "NLP Sentiment", framework: "tensorflow", params: "2.5M", rounds: 8, accuracy: 0.89 },
];

const clients = [
  { id: "cl-001", name: "Edge Node NYC", samples: 15000, rounds: 12, reliability: 0.98 },
  { id: "cl-002", name: "Edge Node LON", samples: 12000, rounds: 10, reliability: 0.95 },
  { id: "cl-003", name: "Edge Node TYO", samples: 8000, rounds: 8, reliability: 0.92 },
];

export default function FederatedLearning() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Federated Learning</h1>
        <Badge variant="outline" className="text-sm">Privacy-Preserving ML</Badge>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Models</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{models.length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Clients</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{clients.length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Rounds</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{models.reduce((s, m) => s + m.rounds, 0)}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Avg Accuracy</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-green-600">{((models.reduce((s, m) => s + m.accuracy, 0)) / models.length * 100).toFixed(0)}%</div></CardContent></Card>
      </div>

      <Tabs defaultValue="models">
        <TabsList><TabsTrigger value="models">Models</TabsTrigger><TabsTrigger value="clients">Clients</TabsTrigger><TabsTrigger value="rounds">Training Rounds</TabsTrigger></TabsList>

        <TabsContent value="models" className="mt-4">
          <div className="grid gap-4 md:grid-cols-2">
            {models.map(m => (
              <Card key={m.id}>
                <CardHeader className="pb-2"><CardTitle className="text-sm flex items-center justify-between"><span>{m.name}</span><Badge variant="outline">{m.framework}</Badge></CardTitle></CardHeader>
                <CardContent className="text-sm space-y-1">
                  <div className="flex justify-between"><span>Parameters</span><span>{m.params}</span></div>
                  <div className="flex justify-between"><span>Training Rounds</span><span>{m.rounds}</span></div>
                  <div className="flex justify-between"><span>Accuracy</span><span className="text-green-600">{(m.accuracy * 100).toFixed(1)}%</span></div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="clients">
          <div className="space-y-3">
            {clients.map(c => (
              <Card key={c.id}>
                <CardContent className="flex items-center justify-between py-3">
                  <div><div className="font-medium">{c.name}</div><div className="text-sm text-muted-foreground">{c.samples.toLocaleString()} samples | {c.rounds} rounds</div></div>
                  <div className="flex items-center gap-2"><Badge variant={c.reliability >= 0.95 ? "default" : "secondary"}>{(c.reliability * 100).toFixed(0)}% reliable</Badge></div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="rounds">
          <Card><CardHeader><CardTitle>Last Training Round</CardTitle></CardHeader><CardContent>
            <div className="space-y-2">
              <div className="flex justify-between"><span>Round #12</span><Badge>Completed</Badge></div>
              <div className="flex justify-between"><span>Clients</span><span>3</span></div>
              <div className="flex justify-between"><span>Accuracy</span><span className="text-green-600">94.2%</span></div>
              <div className="flex justify-between"><span>Loss</span><span className="text-amber-500">0.23</span></div>
              <div className="flex justify-between"><span>Duration</span><span>4.2s</span></div>
              <div className="flex justify-between"><span>Aggregation</span><span>Federated Averaging</span></div>
            </div>
          </CardContent></Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

      {/* === EXPANSION: Advanced Features Panel === */}

      {/* Activity Timeline */}
      <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
        <h3 className="text-sm font-semibold text-white mb-3">Activity Timeline</h3>
        <div className="space-y-2">
          {[
            { time: "2m ago", action: "Configuration updated", user: "admin" },
            { time: "15m ago", action: "Health check passed", user: "system" },
            { time: "1h ago", action: "Backup completed", user: "system" },
            { time: "3h ago", action: "Alert acknowledged", user: "operator" },
            { time: "6h ago", action: "Maintenance window started", user: "admin" },
          ].map((event, i) => (
            <div key={i} className="flex items-center justify-between py-1 border-b border-slate-700 last:border-0">
              <span className="text-xs text-slate-300">{event.action}</span>
              <span className="text-[10px] text-slate-500">{event.time} by {event.user}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-2 gap-2 mt-4">
        <Button variant="outline" size="sm" className="text-xs" onClick={() => alert("Running diagnostic...")}>
          Run Diagnostic
        </Button>
        <Button variant="outline" size="sm" className="text-xs" onClick={() => alert("Exporting data...")}>
          Export Data
        </Button>
        <Button variant="outline" size="sm" className="text-xs" onClick={() => alert("Creating backup...")}>
          Create Backup
        </Button>
        <Button variant="outline" size="sm" className="text-xs" onClick={() => alert("Generating report...")}>
          Generate Report
        </Button>
      </div>

      {/* Config Panel */}
      <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
        <h3 className="text-sm font-semibold text-white mb-3">Configuration</h3>
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <span className="text-xs text-slate-400">Auto-recovery</span>
            <Badge variant="outline" className="text-[10px]">Enabled</Badge>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-xs text-slate-400">Alert threshold</span>
            <span className="text-xs text-white">85%</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-xs text-slate-400">Retention period</span>
            <span className="text-xs text-white">30 days</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-xs text-slate-400">Max retries</span>
            <span className="text-xs text-white">3</span>
          </div>
        </div>
      </div>

      {/* Notifications */}
      <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mt-4">
        <h3 className="text-sm font-semibold text-white mb-3">Recent Notifications</h3>
        <div className="space-y-1">
          <p className="text-xs text-green-400">✓ Backup completed successfully</p>
          <p className="text-xs text-yellow-400">⚠ Health check warning: high memory</p>
          <p className="text-xs text-blue-400">ℹ Maintenance scheduled for 02:00 UTC</p>
        </div>
      </div>

/* Utility components and helpers */

interface MetricCardData { label: string; value: number; unit: string; }
function MetricCard({ label, value, unit }: MetricCardData) {
  return React.createElement('div', { className: 'bg-slate-800 rounded-lg p-3 border border-slate-700' },
    React.createElement('p', { className: 'text-[10px] text-slate-400 uppercase tracking-wider' }, label),
    React.createElement('p', { className: 'text-lg font-bold mt-1 text-white' }, `${value}${unit}`));
}

interface ConfigEntry { label: string; value?: string; badgeText?: string; }
function ConfigRow({ label, value, badgeText }: ConfigEntry) {
  return React.createElement('div', { className: 'flex justify-between items-center py-2 border-b border-slate-700 last:border-0' },
    React.createElement('span', { className: 'text-xs text-slate-400' }, label),
    badgeText
      ? React.createElement(Badge, { variant: 'outline', className: 'text-[10px]' }, badgeText)
      : React.createElement('span', { className: 'text-xs text-white' }, value));
}

const statusColors: Record<string, string> = { healthy: '#22c55e', warning: '#eab308', critical: '#ef4444', unknown: '#64748b' };
function StatusDot({ status }: { status: string }) {
  return React.createElement('span', { className: 'w-2 h-2 rounded-full inline-block', style: { backgroundColor: statusColors[status] || statusColors.unknown } });
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'; const k = 1024; const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

function formatDuration(s: number): string {
  if (s < 60) return `${s}s`; if (s < 3600) return `${Math.floor(s / 60)}m ${s % 60}s`;
  return `${Math.floor(s / 3600)}h ${Math.floor((s % 3600) / 60)}m`;
}

function timeAgo(d: string): string {
  const diff = Math.floor((Date.now() - new Date(d).getTime()) / 1000);
  if (diff < 60) return `${diff}s ago`; if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`; return `${Math.floor(diff / 86400)}d ago`;
}
