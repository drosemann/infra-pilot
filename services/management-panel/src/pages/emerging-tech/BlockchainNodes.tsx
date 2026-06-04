import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

interface BlockchainNode {
  id: string; name: string; network: string; role: string; status: string;
  peers: number; block: number; progress: number; staked: number; rewards: number;
}

const defaultNodes: BlockchainNode[] = [
  { id: "bc-001", name: "Eth Main Validator", network: "ethereum", role: "validator", status: "synced", peers: 24, block: 19500000, progress: 100, staked: 32, rewards: 1.45 },
  { id: "bc-002", name: "Solana RPC Node", network: "solana", role: "rpc", status: "running", peers: 18, block: 240000000, progress: 100, staked: 0, rewards: 0 },
  { id: "bc-003", name: "Polygon Archive", network: "polygon", role: "archive", status: "syncing", peers: 12, block: 45000000, progress: 72, staked: 0, rewards: 0 },
];

const networkDefaults: Record<string, { color: string; symbol: string }> = {
  ethereum: { color: "blue", symbol: "ETH" },
  solana: { color: "purple", symbol: "SOL" },
  polygon: { color: "violet", symbol: "MATIC" },
  avalanche: { color: "red", symbol: "AVAX" },
};

export default function BlockchainNodes() {
  const [nodes] = useState<BlockchainNode[]>(defaultNodes);
  const [name, setName] = useState("");
  const [network, setNetwork] = useState("ethereum");
  const [role, setRole] = useState("full");

  const statusColor = (s: string) => {
    if (s === "synced" || s === "running") return "default";
    if (s === "syncing") return "secondary";
    return "destructive";
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Blockchain Nodes</h1>
        <Badge variant="outline" className="text-sm">{nodes.length} nodes</Badge>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Total Nodes</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{nodes.length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Synced</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-green-600">{nodes.filter(n => n.status === "synced" || n.status === "running").length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Validators</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-amber-500">{nodes.filter(n => n.role === "validator").length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Total Staked</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{nodes.reduce((s, n) => s + n.staked, 0)} ETH</div></CardContent></Card>
      </div>

      <Card>
        <CardHeader><CardTitle>Deploy Node</CardTitle></CardHeader>
        <CardContent className="flex gap-4 items-end">
          <div><label className="text-sm font-medium">Name</label><Input value={name} onChange={e => setName(e.target.value)} placeholder="my-node" /></div>
          <div><label className="text-sm font-medium">Network</label><select className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2" value={network} onChange={e => setNetwork(e.target.value)}>
            <option value="ethereum">Ethereum</option><option value="solana">Solana</option><option value="polygon">Polygon</option><option value="avalanche">Avalanche</option>
          </select></div>
          <div><label className="text-sm font-medium">Role</label><select className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2" value={role} onChange={e => setRole(e.target.value)}>
            <option value="full">Full</option><option value="archive">Archive</option><option value="validator">Validator</option><option value="rpc">RPC</option><option value="light">Light</option>
          </select></div>
          <Button>Deploy</Button>
        </CardContent>
      </Card>

      <Tabs defaultValue="list">
        <TabsList><TabsTrigger value="list">List</TabsTrigger><TabsTrigger value="validators">Validators</TabsTrigger><TabsTrigger value="networks">Networks</TabsTrigger></TabsList>
        <TabsContent value="list" className="mt-4">
          <div className="space-y-3">
            {nodes.map(node => {
              const net = networkDefaults[node.network] || { color: "gray", symbol: "" };
              return (
                <Card key={node.id} className="hover:shadow-md transition-shadow">
                  <CardContent className="flex items-center justify-between py-4">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold">{node.name}</span>
                        <Badge style={{ backgroundColor: net.color }}>{node.network}</Badge>
                        <Badge variant="outline">{node.role}</Badge>
                      </div>
                      <div className="text-sm text-muted-foreground">Peers: {node.peers} | Block: {node.block.toLocaleString()} | Progress: {node.progress}%</div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={statusColor(node.status)}>{node.status}</Badge>
                      {node.role === "validator" && node.staked > 0 && (
                        <Badge variant="outline" className="text-amber-500">{node.staked} {net.symbol} | {node.rewards} rewards</Badge>
                      )}
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </TabsContent>
        <TabsContent value="validators">
          <Card><CardContent className="py-6 text-center text-muted-foreground">Validator management dashboard â€” view attestation rates, proposal history, and rewards.</CardContent></Card>
        </TabsContent>
        <TabsContent value="networks">
          <div className="grid gap-4 md:grid-cols-2">
            {Object.entries(networkDefaults).map(([key, val]) => (
              <Card key={key}><CardHeader><CardTitle className="capitalize">{key}</CardTitle></CardHeader>
                <CardContent>
                  <div className="space-y-1 text-sm">
                    <div className="flex justify-between"><span>Symbol</span><span className="font-mono">{val.symbol}</span></div>
                    <div className="flex justify-between"><span>Nodes</span><span>{nodes.filter(n => n.network === key).length}</span></div>
                    <div className="flex justify-between"><span>P2P Port</span><span className="font-mono">{key === "solana" ? "8000" : key === "avalanche" ? "9651" : "30303"}</span></div>
                    <div className="flex justify-between"><span>RPC Port</span><span className="font-mono">{key === "solana" ? "8899" : key === "avalanche" ? "9650" : "8545"}</span></div>
                  </div>
                </CardContent>
              </Card>
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



// test

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
