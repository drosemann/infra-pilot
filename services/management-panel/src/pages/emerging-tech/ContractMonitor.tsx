import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

interface SecurityAlert {
  id: string; title: string; severity: string; status: string; contract: string; tx: string;
}

const defaultAlerts: SecurityAlert[] = [
  { id: "al-001", title: "High Value Transfer", severity: "high", status: "open", contract: "USDC Token", tx: "0xabc123" },
  { id: "al-002", title: "Owner Action: transferOwnership", severity: "critical", status: "investigating", contract: "NFT Collection", tx: "0xdef456" },
  { id: "al-003", title: "Unusual Gas Usage", severity: "medium", status: "resolved", contract: "DEX Router", tx: "0x789ghi" },
];

export default function ContractMonitor() {
  const [alerts] = useState<SecurityAlert[]>(defaultAlerts);

  const severityColor = (s: string) => {
    if (s === "critical") return "destructive";
    if (s === "high") return "destructive";
    if (s === "medium") return "secondary";
    return "default";
  };

  const statusColor = (s: string) => {
    if (s === "open") return "destructive";
    if (s === "investigating") return "secondary";
    return "default";
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Smart Contract Monitor</h1>
        <Badge variant="outline" className="text-sm">{alerts.length} alerts</Badge>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Contracts</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">3</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Open Alerts</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-red-500">{alerts.filter(a => a.status === "open").length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Investigating</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-amber-500">{alerts.filter(a => a.status === "investigating").length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Resolved Today</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-green-600">{alerts.filter(a => a.status === "resolved").length}</div></CardContent></Card>
      </div>

      <Tabs defaultValue="alerts">
        <TabsList><TabsTrigger value="alerts">Alerts</TabsTrigger><TabsTrigger value="contracts">Contracts</TabsTrigger><TabsTrigger value="patterns">Anomaly Patterns</TabsTrigger></TabsList>

        <TabsContent value="alerts" className="mt-4">
          <div className="space-y-3">
            {alerts.map(alert => (
              <Card key={alert.id}>
                <CardContent className="flex items-center justify-between py-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold">{alert.title}</span>
                      <Badge variant={severityColor(alert.severity)}>{alert.severity}</Badge>
                      <Badge variant={statusColor(alert.status)}>{alert.status}</Badge>
                    </div>
                    <div className="text-sm text-muted-foreground">Contract: {alert.contract} | TX: {alert.tx.slice(0, 16)}...</div>
                  </div>
                  <Button variant="outline" size="sm">Investigate</Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="contracts">
          <Card><CardHeader><CardTitle>Registered Contracts</CardTitle></CardHeader><CardContent>
            <div className="space-y-3">
              <div className="flex justify-between items-center py-2 border-b"><div><span className="font-medium">USDC Token</span><div className="text-sm text-muted-foreground">0xa0b8...1e4 | Ethereum</div></div><Badge>ERC20</Badge></div>
              <div className="flex justify-between items-center py-2 border-b"><div><span className="font-medium">NFT Collection</span><div className="text-sm text-muted-foreground">0xbcde...2f5 | Polygon</div></div><Badge>ERC721</Badge></div>
              <div className="flex justify-between items-center py-2"><div><span className="font-medium">DEX Router</span><div className="text-sm text-muted-foreground">0xdef1...3a6 | Ethereum</div></div><Badge variant="outline">Custom</Badge></div>
            </div>
          </CardContent></Card>
        </TabsContent>

        <TabsContent value="patterns">
          <div className="grid gap-4 md:grid-cols-2">
            {["Flash Loan Attack", "Rug Pull Detection", "Suspicious Upgrade", "Large Approval", "Owner Action"].map((p, i) => (
              <Card key={i}><CardHeader className="pb-2"><CardTitle className="text-sm flex items-center justify-between"><span>{p}</span><Badge variant="default">Active</Badge></CardTitle></CardHeader>
                <CardContent className="text-sm text-muted-foreground">Anomaly detection pattern for {p.toLowerCase()} scenarios.</CardContent></Card>
            ))}
          </div>
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
