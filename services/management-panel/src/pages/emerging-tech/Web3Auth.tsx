import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

const users = [
  { id: "u-001", wallet: "0x1234...5678", type: "metamask", ens: "vitalik.eth", verified: true, lastLogin: "2m ago" },
  { id: "u-002", wallet: "0xabcd...ef01", type: "phantom", ens: "", verified: true, lastLogin: "1h ago" },
  { id: "u-003", wallet: "0x9876...5432", type: "walletconnect", ens: "user.eth", verified: false, lastLogin: "1d ago" },
];

export default function Web3Auth() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Web3 Identity & Auth</h1>
        <Badge variant="outline" className="text-sm">SIWE + Token-Gated</Badge>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Users</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{users.length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Verified</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-green-600">{users.filter(u => u.verified).length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Active Sessions</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">5</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Gate Rules</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">2</div></CardContent></Card>
      </div>

      <Tabs defaultValue="users">
        <TabsList><TabsTrigger value="users">Users</TabsTrigger><TabsTrigger value="sessions">Sessions</TabsTrigger><TabsTrigger value="gates">Token Gates</TabsTrigger><TabsTrigger value="siwe">SIWE</TabsTrigger></TabsList>

        <TabsContent value="users" className="mt-4">
          <Card>
            <CardHeader><CardTitle>Registered Wallets</CardTitle></CardHeader>
            <CardContent><div className="space-y-3">
              {users.map(u => (
                <div key={u.id} className="flex items-center justify-between py-2 border-b last:border-0">
                  <div><div className="flex items-center gap-2"><span className="font-medium">{u.wallet}</span><Badge variant="outline">{u.type}</Badge></div>
                    <div className="text-sm text-muted-foreground">{u.ens || "No ENS"} | Last login: {u.lastLogin}</div></div>
                  <Badge variant={u.verified ? "default" : "secondary"}>{u.verified ? "Verified" : "Unverified"}</Badge>
                </div>
              ))}
            </div></CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="sessions">
          <Card><CardHeader><CardTitle>Active Sessions</CardTitle></CardHeader><CardContent className="text-center text-muted-foreground py-6">5 active sessions from registered wallets.</CardContent></Card>
        </TabsContent>

        <TabsContent value="gates">
          <div className="space-y-3">
            <Card><CardContent className="py-4 flex items-center justify-between"><div><span className="font-medium">NFT Holders Only</span><div className="text-sm text-muted-foreground">Type: NFT Holding | Network: Ethereum | Min: 1 NFT</div></div><Badge>Enabled</Badge></CardContent></Card>
            <Card><CardContent className="py-4 flex items-center justify-between"><div><span className="font-medium">Whitelist Access</span><div className="text-sm text-muted-foreground">Type: Whitelist | 5 allowed wallets</div></div><Badge>Enabled</Badge></CardContent></Card>
          </div>
        </TabsContent>

        <TabsContent value="siwe">
          <Card><CardHeader><CardTitle>Sign-In with Ethereum</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div className="bg-muted p-4 rounded-md font-mono text-sm">
                infrapilot.ai wants you to sign in with your Ethereum account:<br />
                0x1234...5678<br /><br />
                Sign in to Infra Pilot with your wallet<br />
                URI: https://infrapilot.ai<br />
                Version: 1<br />
                Chain ID: 1<br />
                Nonce: abcdef123456<br />
              </div>
              <div className="text-sm text-muted-foreground">SIWE provides secure, non-custodial authentication for dApp access.</div>
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
