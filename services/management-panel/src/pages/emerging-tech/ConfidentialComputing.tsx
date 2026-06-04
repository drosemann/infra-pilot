import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

const enclaves = [
  { id: "enc-001", name: "Secure Model Inference", tech: "intel_sgx", status: "running", attestation: "verified", memory: 512, cores: 4 },
  { id: "enc-002", name: "Encrypted DB", tech: "amd_sev", status: "running", attestation: "verified", memory: 1024, cores: 8 },
  { id: "enc-003", name: "Trusted Execution", tech: "arm_trustzone", status: "stopped", attestation: "pending", memory: 64, cores: 2 },
];

const techInfo: Record<string, { name: string, color: string }> = {
  intel_sgx: { name: "Intel SGX", color: "blue" },
  amd_sev: { name: "AMD SEV", color: "red" },
  arm_trustzone: { name: "ARM TrustZone", color: "purple" },
};

export default function ConfidentialComputing() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Confidential Computing</h1>
        <Badge variant="outline" className="text-sm">{enclaves.length} enclaves</Badge>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Total Enclaves</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{enclaves.length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Running</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-green-600">{enclaves.filter(e => e.status === "running").length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Verified Attestations</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{enclaves.filter(e => e.attestation === "verified").length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Total Memory</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{enclaves.reduce((s, e) => s + e.memory, 0)} MB</div></CardContent></Card>
      </div>

      <Tabs defaultValue="enclaves">
        <TabsList><TabsTrigger value="enclaves">Enclaves</TabsTrigger><TabsTrigger value="attestations">Attestations</TabsTrigger><TabsTrigger value="platforms">Platforms</TabsTrigger></TabsList>

        <TabsContent value="enclaves" className="mt-4">
          <div className="space-y-3">
            {enclaves.map(e => (
              <Card key={e.id}>
                <CardContent className="flex items-center justify-between py-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold">{e.name}</span>
                      <Badge style={{ backgroundColor: techInfo[e.tech]?.color || "gray" }}>{techInfo[e.tech]?.name || e.tech}</Badge>
                    </div>
                    <div className="text-sm text-muted-foreground">{e.memory} MB / {e.cores} cores | Attestation: {e.attestation}</div>
                  </div>
                  <Badge variant={e.status === "running" ? "default" : "secondary"}>{e.status}</Badge>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="attestations">
          <Card><CardHeader><CardTitle>Attestation Evidence</CardTitle></CardHeader><CardContent className="text-center text-muted-foreground py-6">
            All running enclaves have verified attestations. Remote attestation confirms TCB integrity and measurement hash.
          </CardContent></Card>
        </TabsContent>

        <TabsContent value="platforms">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {Object.entries(techInfo).map(([key, val]) => (
              <Card key={key}><CardHeader className="pb-2"><CardTitle className="text-sm">{val.name}</CardTitle></CardHeader>
                <CardContent className="text-xs space-y-1">
                  <div>Max Memory: {key === "intel_sgx" ? "512 MB" : key === "amd_sev" ? "80 GB" : "32 MB"}</div>
                  <div>OS: {key === "arm_trustzone" ? "OP-TEE" : "Linux"}</div>
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
