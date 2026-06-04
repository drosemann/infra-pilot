import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

interface ContentItem {
  id: string; name: string; protocol: string; cid: string;
  size: number; tier: string; pinned: boolean; gateway: string;
}

const defaultItems: ContentItem[] = [
  { id: "ds-001", name: "Website Assets", protocol: "ipfs", cid: "Qmabc123...", size: 256, tier: "hot", pinned: true, gateway: "https://ipfs.io/ipfs/Qmabc123" },
  { id: "ds-002", name: "Backup Archive", protocol: "filecoin", cid: "bafydef456...", size: 10240, tier: "cold", pinned: true, gateway: "" },
  { id: "ds-003", name: "NFT Metadata", protocol: "arweave", cid: "a-abc789...", size: 5, tier: "hot", pinned: true, gateway: "https://arweave.net/a-abc789" },
];

export default function DecentralizedStorage() {
  const [items] = useState<ContentItem[]>(defaultItems);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Decentralized Storage</h1>
        <Badge variant="outline" className="text-sm">{items.length} items</Badge>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Total Items</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{items.length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Total Size</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{(items.reduce((s, i) => s + i.size, 0) / 1024).toFixed(1)} GB</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Pinned</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-green-600">{items.filter(i => i.pinned).length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Hot Tier</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-amber-500">{items.filter(i => i.tier === "hot").length}</div></CardContent></Card>
      </div>

      <Tabs defaultValue="browse">
        <TabsList><TabsTrigger value="browse">Browse</TabsTrigger><TabsTrigger value="upload">Upload</TabsTrigger><TabsTrigger value="gateway">Gateway Config</TabsTrigger></TabsList>

        <TabsContent value="browse" className="mt-4">
          <div className="space-y-3">
            {items.map(item => (
              <Card key={item.id}>
                <CardContent className="flex items-center justify-between py-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold">{item.name}</span>
                      <Badge variant="secondary">{item.protocol}</Badge>
                      <Badge variant="outline">{item.tier}</Badge>
                    </div>
                    <div className="text-sm text-muted-foreground">CID: {item.cid} | Size: {item.size >= 1024 ? `${(item.size / 1024).toFixed(1)} GB` : `${item.size} MB`}</div>
                    {item.gateway && <div className="text-xs text-blue-500 truncate max-w-md">{item.gateway}</div>}
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={item.pinned ? "default" : "secondary"}>{item.pinned ? "Pinned" : "Unpinned"}</Badge>
                    <Button variant="outline" size="sm">Copy CID</Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="upload">
          <Card>
            <CardHeader><CardTitle>Upload Content</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div><label className="text-sm font-medium">Protocol</label><select className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2">
                  <option value="ipfs">IPFS</option><option value="arweave">Arweave</option><option value="filecoin">Filecoin</option>
                </select></div>
                <div><label className="text-sm font-medium">Storage Tier</label><select className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2">
                  <option value="hot">Hot</option><option value="warm">Warm</option><option value="cold">Cold</option><option value="archive">Archive</option>
                </select></div>
              </div>
              <Button className="w-full">Upload to Decentralized Storage</Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="gateway">
          <Card><CardHeader><CardTitle>Gateway Configuration</CardTitle></CardHeader>
            <CardContent className="space-y-3">
              <div className="flex justify-between py-2 border-b"><span>IPFS Gateway</span><span className="font-mono text-sm">https://ipfs.io</span></div>
              <div className="flex justify-between py-2 border-b"><span>Arweave Gateway</span><span className="font-mono text-sm">https://arweave.net</span></div>
              <div className="flex justify-between py-2 border-b"><span>Default Replication</span><span className="font-mono text-sm">3</span></div>
              <div className="flex justify-between py-2 border-b"><span>Hybrid Mode</span><span className="text-green-600">Enabled</span></div>
              <div className="flex justify-between py-2"><span>Cold Storage</span><span className="font-mono text-sm">S3: infrapilot-cold</span></div>
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
