import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

const explorers = [
  { name: "Ethereum Mainnet", url: "https://etherscan.io", chainId: 1, status: "synced" },
  { name: "Sepolia Testnet", url: "https://sepolia.etherscan.io", chainId: 11155111, status: "synced" },
  { name: "PolygonScan", url: "https://polygonscan.com", chainId: 137, status: "synced" },
  { name: "Arbiscan", url: "https://arbiscan.io", chainId: 42161, status: "synced" },
];

export default function Web3Toolkit() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Web3 Developer Toolkit</h1>
        <Badge variant="outline" className="text-sm">Blockchain Explorer + More</Badge>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Explorers</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{explorers.length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Faucets</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">2</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Transactions</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">5</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Gas Tracker</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-blue-500">20 Gwei</div></CardContent></Card>
      </div>

      <Tabs defaultValue="explorer">
        <TabsList>
          <TabsTrigger value="explorer">Explorer</TabsTrigger>
          <TabsTrigger value="tx">Transaction Builder</TabsTrigger>
          <TabsTrigger value="faucet">Faucet</TabsTrigger>
          <TabsTrigger value="gas">Gas Tracker</TabsTrigger>
          <TabsTrigger value="verify">Contract Verifier</TabsTrigger>
        </TabsList>

        <TabsContent value="explorer" className="mt-4">
          <div className="grid gap-4 md:grid-cols-2">
            {explorers.map(e => (
              <Card key={e.name}>
                <CardHeader className="pb-2"><CardTitle className="text-sm flex items-center justify-between"><span>{e.name}</span><Badge variant="default">{e.status}</Badge></CardTitle></CardHeader>
                <CardContent className="text-sm space-y-1">
                  <div className="flex justify-between"><span>Chain ID</span><span className="font-mono">{e.chainId}</span></div>
                  <div className="flex justify-between"><span>URL</span><span className="text-blue-500 text-xs">{e.url}</span></div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="tx">
          <Card>
            <CardHeader><CardTitle>Transaction Builder</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div><label className="text-sm font-medium">Network</label><select className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2"><option>Ethereum</option><option>Polygon</option><option>Arbitrum</option></select></div>
                <div><label className="text-sm font-medium">To Address</label><input className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2" placeholder="0x..." /></div>
                <div><label className="text-sm font-medium">Value (ETH)</label><input className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2" type="number" placeholder="0.0" /></div>
                <div><label className="text-sm font-medium">Gas Limit</label><input className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2" value="21000" /></div>
              </div>
              <div className="bg-muted p-3 rounded-md text-sm">
                <div className="flex justify-between"><span>Estimated Cost</span><span className="font-mono">~$2.50</span></div>
                <div className="flex justify-between"><span>Gas Price</span><span className="font-mono">20 Gwei</span></div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="faucet">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader className="pb-2"><CardTitle className="text-sm">Sepolia ETH Faucet</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between text-sm"><span>Balance</span><span>1000 ETH</span></div>
                <div className="flex justify-between text-sm"><span>Drip Amount</span><span>0.1 ETH</span></div>
                <div className="flex justify-between text-sm"><span>Status</span><Badge>Active</Badge></div>
                <input className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2" placeholder="0x wallet address" />
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2"><CardTitle className="text-sm">Goerli ETH Faucet</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between text-sm"><span>Balance</span><span>500 ETH</span></div>
                <div className="flex justify-between text-sm"><span>Drip Amount</span><span>0.1 ETH</span></div>
                <div className="flex justify-between text-sm"><span>Status</span><Badge variant="secondary">Depleted</Badge></div>
                <input className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2" placeholder="0x wallet address" />
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="gas">
          <Card>
            <CardHeader><CardTitle>Gas Price Tracker</CardTitle></CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-5">
                <div className="text-center p-4 bg-muted rounded-lg"><div className="text-xs text-muted-foreground">Slow</div><div className="text-xl font-bold">10</div><div className="text-xs">Gwei</div></div>
                <div className="text-center p-4 bg-muted rounded-lg"><div className="text-xs text-muted-foreground">Standard</div><div className="text-xl font-bold">20</div><div className="text-xs">Gwei</div></div>
                <div className="text-center p-4 bg-muted rounded-lg"><div className="text-xs text-muted-foreground">Fast</div><div className="text-xl font-bold">50</div><div className="text-xs">Gwei</div></div>
                <div className="text-center p-4 bg-muted rounded-lg"><div className="text-xs text-muted-foreground">Instant</div><div className="text-xl font-bold">100</div><div className="text-xs">Gwei</div></div>
                <div className="text-center p-4 bg-muted rounded-lg"><div className="text-xs text-muted-foreground">Base Fee</div><div className="text-xl font-bold">15</div><div className="text-xs">Gwei</div></div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="verify">
          <Card>
            <CardHeader><CardTitle>Contract Verifier</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div><label className="text-sm font-medium">Network</label><select className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2"><option>Ethereum Mainnet</option><option>Sepolia</option></select></div>
                <div><label className="text-sm font-medium">Contract Address</label><input className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2" placeholder="0x..." /></div>
              </div>
              <div><label className="text-sm font-medium">Source Code</label><textarea className="flex h-32 w-full rounded-md border border-input bg-background px-3 py-2 font-mono text-sm" placeholder="// SPDX-License-Identifier: MIT" /></div>
              <div><label className="text-sm font-medium">Compiler Version</label><select className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2"><option>v0.8.20</option><option>v0.8.19</option></select></div>
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
