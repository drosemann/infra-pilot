import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

const algorithms = [
  { name: "Kyber-512", type: "KEM", security: "AES-128" },
  { name: "Kyber-768", type: "KEM", security: "AES-192" },
  { name: "Kyber-1024", type: "KEM", security: "AES-256" },
  { name: "Dilithium-2", type: "Signature", security: "SL2-DSA" },
  { name: "Dilithium-3", type: "Signature", security: "SL3-DSA" },
  { name: "Dilithium-5", type: "Signature", security: "SL5-DSA" },
];

export default function QuantumCrypto() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Quantum-Safe Cryptography</h1>
        <Badge variant="outline" className="text-sm">NIST PQC Standardized</Badge>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">PQ Keys</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">3</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Active</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-green-600">2</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Assessments</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">1</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Migrated</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-blue-500">0</div></CardContent></Card>
      </div>

      <Tabs defaultValue="keys">
        <TabsList><TabsTrigger value="keys">Key Management</TabsTrigger><TabsTrigger value="algorithms">Algorithms</TabsTrigger><TabsTrigger value="assessment">Migration</TabsTrigger></TabsList>

        <TabsContent value="keys" className="mt-4">
          <div className="space-y-3">
            <Card><CardContent className="py-4 flex items-center justify-between">
              <div><span className="font-semibold">TLS Hybrid Cert</span><div className="text-sm text-muted-foreground">Kyber-768 + X25519 | TLS | Active</div></div>
              <Badge>Active</Badge>
            </CardContent></Card>
            <Card><CardContent className="py-4 flex items-center justify-between">
              <div><span className="font-semibold">Code Signing Key</span><div className="text-sm text-muted-foreground">Dilithium-3 | Code Signing | Active</div></div>
              <Badge>Active</Badge>
            </CardContent></Card>
            <Card><CardContent className="py-4 flex items-center justify-between">
              <div><span className="font-semibold">Legacy RSA Key</span><div className="text-sm text-muted-foreground">RSA-4096 | TLS | Expired</div></div>
              <Badge variant="secondary">Expired</Badge>
            </CardContent></Card>
          </div>
        </TabsContent>

        <TabsContent value="algorithms">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {algorithms.map(algo => (
              <Card key={algo.name}>
                <CardHeader className="pb-2"><CardTitle className="text-sm">{algo.name}</CardTitle></CardHeader>
                <CardContent className="text-sm space-y-1">
                  <div className="flex justify-between"><span>Type</span><Badge variant="outline">{algo.type}</Badge></div>
                  <div className="flex justify-between"><span>Security</span><span>{algo.security}</span></div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="assessment">
          <Card><CardHeader><CardTitle>PQ Migration Assessment</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-4">
                <div className="text-center"><div className="text-2xl font-bold">50</div><div className="text-xs text-muted-foreground">Total Endpoints</div></div>
                <div className="text-center"><div className="text-2xl font-bold text-green-600">35</div><div className="text-xs text-muted-foreground">PQ Compatible</div></div>
                <div className="text-center"><div className="text-2xl font-bold text-amber-500">10</div><div className="text-xs text-muted-foreground">Hybrid Mode</div></div>
                <div className="text-center"><div className="text-2xl font-bold text-red-500">5</div><div className="text-xs text-muted-foreground">Incompatible</div></div>
              </div>
              <div className="w-full bg-secondary h-2 rounded-full overflow-hidden flex">
                <div className="bg-green-600 h-full" style={{ width: "70%" }} />
                <div className="bg-amber-500 h-full" style={{ width: "20%" }} />
                <div className="bg-red-500 h-full" style={{ width: "10%" }} />
              </div>
              <div className="space-y-2">
                <div className="flex justify-between text-sm"><span>Step 1: Inventory TLS endpoints</span><Badge>Done</Badge></div>
                <div className="flex justify-between text-sm"><span>Step 2: Deploy hybrid certificates</span><Badge variant="secondary">In Progress</Badge></div>
                <div className="flex justify-between text-sm"><span>Step 3: Enable PQ cipher suites</span><Badge variant="outline">Pending</Badge></div>
              </div>
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
