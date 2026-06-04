import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

const providers = [
  { id: "prov-001", name: "GPU-Pool-NA", region: "us-east", cpu: 32, gpu: 4, memory: 128, price: 0.45, reputation: 4.8, jobs: 150 },
  { id: "prov-002", name: "Compute-EU", region: "eu-west", cpu: 16, gpu: 0, memory: 64, price: 0.08, reputation: 4.5, jobs: 89 },
  { id: "prov-003", name: "Edge-Asia", region: "ap-southeast", cpu: 8, gpu: 1, memory: 32, price: 0.12, reputation: 4.2, jobs: 45 },
];

const orders = [
  { id: "ord-001", name: "ML Training Job", provider: "GPU-Pool-NA", cost: 2.25, status: "active", duration: "5h" },
  { id: "ord-002", name: "Web Scraping", provider: "Compute-EU", cost: 0.40, status: "completed", duration: "5h" },
];

export default function DecentralizedCompute() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Decentralized Compute</h1>
        <Badge variant="outline" className="text-sm">P2P Compute Marketplace</Badge>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Providers</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{providers.length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Online</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-green-600">{providers.length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Active Orders</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-amber-500">{orders.filter(o => o.status === "active").length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Available CPU</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{providers.reduce((s, p) => s + p.cpu, 0)} cores</div></CardContent></Card>
      </div>

      <Tabs defaultValue="market">
        <TabsList><TabsTrigger value="market">Market</TabsTrigger><TabsTrigger value="orders">Orders</TabsTrigger><TabsTrigger value="providers">Providers</TabsTrigger></TabsList>

        <TabsContent value="market" className="mt-4">
          <div className="grid gap-4 md:grid-cols-3">
            {providers.map(p => (
              <Card key={p.id}>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center justify-between">
                    <span>{p.name}</span>
                    <Badge variant="outline">{p.region}</Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent className="text-sm space-y-1">
                  <div className="flex justify-between"><span>CPU</span><span>{p.cpu} cores</span></div>
                  <div className="flex justify-between"><span>GPU</span><span>{p.gpu}</span></div>
                  <div className="flex justify-between"><span>Memory</span><span>{p.memory} GB</span></div>
                  <div className="flex justify-between"><span>Price/hr</span><span className="font-mono">${p.price.toFixed(2)}</span></div>
                  <div className="flex justify-between"><span>Reputation</span><span className="text-amber-500">{p.reputation}/5.0</span></div>
                  <div className="flex justify-between"><span>Jobs</span><span>{p.jobs}</span></div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="orders">
          <div className="space-y-3">
            {orders.map(o => (
              <Card key={o.id}>
                <CardContent className="flex items-center justify-between py-4">
                  <div><div className="font-medium">{o.name}</div><div className="text-sm text-muted-foreground">Provider: {o.provider} | ${o.cost.toFixed(2)} | {o.duration}</div></div>
                  <Badge variant={o.status === "active" ? "default" : "secondary"}>{o.status}</Badge>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="providers">
          <Card><CardHeader><CardTitle>Provider Registration</CardTitle></CardHeader>
            <CardContent className="text-center text-muted-foreground py-4">
              Register your compute resources and start earning. Accepts CPU, GPU, and storage contributions.
            </CardContent>
          </Card>
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
