import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const mockEnvs = [
  { id: "e1", name: "pr-142-feat-auth", type: "pr", project: "user-service", status: "running", branch: "feat/auth", pr: 142, createdBy: "alice", expiresIn: "22h", endpoints: { web: "https://pr-142.user-service.dev" } },
  { id: "e2", name: "staging-data-pipeline", type: "branch", project: "data-pipeline", status: "running", branch: "main", pr: 0, createdBy: "bob", expiresIn: "48h", endpoints: { api: "https://staging.data.dev" } },
  { id: "e3", name: "pr-145-fix-cache", type: "pr", project: "frontend-web", status: "provisioning", branch: "fix/cache", pr: 145, createdBy: "charlie", expiresIn: "N/A", endpoints: {} },
  { id: "e4", name: "feat-ml-training", type: "feature", project: "data-pipeline", status: "running", branch: "feat/ml-training", pr: 0, createdBy: "alice", expiresIn: "12h", endpoints: { jupyter: "https://ml-training.data.dev" } },
  { id: "e5", name: "pr-148-upgrade-deps", type: "pr", project: "payment-api", status: "terminated", branch: "upgrade/deps", pr: 148, createdBy: "bob", expiresIn: "Expired", endpoints: {} },
];

const statusColors: Record<string, string> = { running: "bg-green-100 text-green-700", provisioning: "bg-blue-100 text-blue-700", terminated: "bg-gray-100 text-gray-700", degraded: "bg-yellow-100 text-yellow-700", failed: "bg-red-100 text-red-700" };

function ProvisionModal({ onClose }: { onClose: () => void }) {
  const [name, setName] = useState("");
  const [project, setProject] = useState("user-service");
  const [template, setTemplate] = useState("default");
  const [ttl, setTtl] = useState("24");
  const [envType, setEnvType] = useState("pr");
  const [branch, setBranch] = useState("");
  const handleSubmit = () => {
    mockEnvs.push({ id: `e${Date.now()}`, name, type: envType, project, status: "provisioning", branch: branch || "main", pr: 0, createdBy: "current-user", expiresIn: `${ttl}h`, endpoints: {} });
    onClose();
  };
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={onClose}>
      <div className="bg-white dark:bg-gray-900 rounded-lg p-6 w-full max-w-md" onClick={e => e.stopPropagation()}>
        <h2 className="text-lg font-semibold mb-4">Provision Environment</h2>
        <div className="space-y-3">
          <Input placeholder="Environment name" value={name} onChange={e => setName(e.target.value)} />
          <select value={project} onChange={e => setProject(e.target.value)} className="w-full border rounded px-3 py-2 text-sm"><option value="user-service">user-service</option><option value="payment-api">payment-api</option><option value="data-pipeline">data-pipeline</option><option value="frontend-web">frontend-web</option></select>
          <select value={template} onChange={e => setTemplate(e.target.value)} className="w-full border rounded px-3 py-2 text-sm"><option value="default">Default (1 CPU, 1GB RAM)</option><option value="large">Large (2 CPU, 4GB RAM)</option></select>
          <select value={envType} onChange={e => setEnvType(e.target.value)} className="w-full border rounded px-3 py-2 text-sm"><option value="pr">PR</option><option value="branch">Branch</option><option value="feature">Feature</option><option value="ephemeral">Ephemeral</option></select>
          <Input type="number" placeholder="TTL (hours)" value={ttl} onChange={e => setTtl(e.target.value)} />
          <Input placeholder="Branch name" value={branch} onChange={e => setBranch(e.target.value)} />
          <div className="flex gap-2 justify-end">
            <Button variant="outline" onClick={onClose}>Cancel</Button>
            <Button onClick={handleSubmit} disabled={!name}>Provision</Button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function EnvironmentOrchestrator() {
  const [showProvision, setShowProvision] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);
  return (
    <div className="space-y-6">
      {showProvision && <ProvisionModal onClose={() => setShowProvision(false)} />}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Environment Orchestrator</h1>
        <Badge variant="outline" className="text-sm">Self-Service Ephemeral</Badge>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Active Envs</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{mockEnvs.filter(e => e.status === "running").length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Provisioning</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-blue-500">{mockEnvs.filter(e => e.status === "provisioning").length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">PR Environments</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{mockEnvs.filter(e => e.type === "pr").length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Expiring Soon</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-yellow-500">2</div></CardContent></Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>Provision New Environment</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <div className="grid gap-3 md:grid-cols-2">
              <div><label className="text-sm">Environment Name</label><Input placeholder="pr-150-feat-xyz" /></div>
              <div><label className="text-sm">Project</label><Select><SelectTrigger><SelectValue placeholder="Select project..." /></SelectTrigger><SelectContent><SelectItem value="user-service">user-service</SelectItem><SelectItem value="payment-api">payment-api</SelectItem><SelectItem value="data-pipeline">data-pipeline</SelectItem></SelectContent></Select></div>
              <div><label className="text-sm">Template</label><Select><SelectTrigger><SelectValue placeholder="Select template..." /></SelectTrigger><SelectContent><SelectItem value="default">Default (1 CPU, 1GB RAM)</SelectItem><SelectItem value="large">Large (2 CPU, 4GB RAM)</SelectItem></SelectContent></Select></div>
              <div><label className="text-sm">TTL (hours)</label><Input type="number" defaultValue={24} /></div>
            </div>
            <Button onClick={() => setShowProvision(true)}>Provision</Button>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Quick Stats</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            {[{ label: "Avg TTL", value: "26h" }, { label: "Avg Provision Time", value: "1m 32s" }, { label: "PR Auto-Cleanup", value: "Enabled" }, { label: "Active Templates", value: "2" }].map(s => (
              <div key={s.label} className="flex justify-between p-2 border-b text-sm"><span>{s.label}</span><span className="font-medium">{s.value}</span></div>
            ))}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader><CardTitle>All Environments</CardTitle></CardHeader>
        <CardContent>
          <div className="space-y-2">
            {mockEnvs.map(e => (
              <div key={e.id} className="flex items-center justify-between p-3 border rounded-lg">
                <div>
                  <div className="flex items-center gap-2"><p className="font-medium">{e.name}</p>                  <Badge variant="outline">{e.type === "pr" ? `PR #${e.pr}` : e.type}</Badge></div>
                  <p className="text-sm text-muted-foreground">{e.project} &middot; Branch: {e.branch} &middot; By: {e.createdBy}</p>
                </div>
                <div className="flex items-center gap-3">
                  <Badge className={statusColors[e.status] || ""}>{e.status}</Badge>
                  <span className="text-sm text-muted-foreground">{e.expiresIn}</span>
                  {e.status === "running" && <Button variant="outline" size="sm">Open</Button>}
                  <Button variant="ghost" size="sm">Terminate</Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Cleanup & Quotas</CardTitle></CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="border rounded-lg p-4">
              <p className="font-medium text-sm">Cleanup Policy</p>
              <div className="mt-2 space-y-2">
                <Input placeholder="Project name" />
                <div className="flex gap-2">
                  <Input placeholder="Max age (hours)" type="number" defaultValue={72} />
                  <Button variant="outline" size="sm">Set Policy</Button>
                </div>
              </div>
            </div>
            <div className="border rounded-lg p-4">
              <p className="font-medium text-sm">Resource Quota</p>
              <div className="mt-2 space-y-2">
                <Input placeholder="Project name" />
                <div className="flex gap-2">
                  <Input placeholder="Max CPU" type="number" defaultValue={8} className="w-20" />
                  <Input placeholder="Max Memory GB" type="number" defaultValue={32} className="w-24" />
                  <Button variant="outline" size="sm">Set Quota</Button>
                </div>
              </div>
            </div>
          </div>
          <div className="mt-4 flex gap-2">
            <Button variant="outline" size="sm">Apply Cleanup</Button>
            <Button variant="outline" size="sm">Check Quota Usage</Button>
            <Button variant="outline" size="sm">Delete Expired</Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Backup & Restore</CardTitle></CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="border rounded-lg p-4">
              <p className="text-sm font-medium">Backup Environment</p>
              <div className="mt-2 flex gap-2">
                <Input placeholder="Environment ID" />
                <Button variant="outline" size="sm">Backup</Button>
              </div>
            </div>
            <div className="border rounded-lg p-4">
              <p className="text-sm font-medium">Restore from Backup</p>
              <div className="mt-2 flex gap-2">
                <Input placeholder="Backup ID" />
                <Button variant="outline" size="sm">Restore</Button>
              </div>
            </div>
          </div>
          <div className="mt-4 flex gap-2">
            <Button variant="outline" size="sm">List Backups</Button>
            <Button variant="outline" size="sm">Extend TTL</Button>
            <Button variant="outline" size="sm">Health Check</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
