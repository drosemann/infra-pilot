import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const blueprints = [
  { id: "bp1", name: "ECS Fargate Service", type: "terraform", version: "2.1.0", owner: "platform", status: "published", usage: 42, rating: 4.5 },
  { id: "bp2", name: "GCP Cloud Run Service", type: "pulumi", version: "1.3.0", owner: "platform", status: "published", usage: 28, rating: 4.2 },
  { id: "bp3", name: "Lambda Event Processor", type: "cloudformation", version: "3.0.1", owner: "data", status: "published", usage: 35, rating: 4.8 },
  { id: "bp4", name: "Kubernetes Helm Chart", type: "helm", version: "1.0.0", owner: "platform", status: "draft", usage: 0, rating: 0 },
  { id: "bp5", name: "VPC with Subnets", type: "terraform", version: "2.0.0", owner: "networking", status: "published", usage: 55, rating: 4.6 },
  { id: "bp6", name: "RDS PostgreSQL", type: "arm", version: "1.1.0", owner: "data", status: "deprecated", usage: 12, rating: 3.9 },
];

const statusColors: Record<string, string> = { published: "bg-green-100 text-green-700", draft: "bg-gray-100 text-gray-700", deprecated: "bg-red-100 text-red-700", archived: "bg-yellow-100 text-yellow-700" };

function CreateBlueprintModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [name, setName] = useState("");
  const [type, setType] = useState("terraform");
  const [owner, setOwner] = useState("");
  const [description, setDescription] = useState("");
  const handleSubmit = () => {
    blueprints.push({ id: `bp${Date.now()}`, name, type, version: "1.0.0", owner, status: "draft", usage: 0, rating: 0 });
    onCreated();
    onClose();
  };
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={onClose}>
      <div className="bg-white dark:bg-gray-900 rounded-lg p-6 w-full max-w-md" onClick={e => e.stopPropagation()}>
        <h2 className="text-lg font-semibold mb-4">New Blueprint</h2>
        <div className="space-y-3">
          <Input placeholder="Blueprint name" value={name} onChange={e => setName(e.target.value)} />
          <select value={type} onChange={e => setType(e.target.value)} className="w-full border rounded px-3 py-2 text-sm"><option value="terraform">Terraform</option><option value="pulumi">Pulumi</option><option value="cloudformation">CloudFormation</option><option value="helm">Helm</option></select>
          <Input placeholder="Owner" value={owner} onChange={e => setOwner(e.target.value)} />
          <Input placeholder="Description" value={description} onChange={e => setDescription(e.target.value)} />
          <div className="flex gap-2 justify-end">
            <Button variant="outline" onClick={onClose}>Cancel</Button>
            <Button onClick={handleSubmit} disabled={!name || !owner}>Create</Button>
          </div>
        </div>
      </div>
    </div>
  );
}

function BlueprintDetailModal({ blueprint, onClose }: { blueprint: typeof blueprints[0]; onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={onClose}>
      <div className="bg-white dark:bg-gray-900 rounded-lg p-6 w-full max-w-lg" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">{blueprint.name}</h2>
          <Badge className={statusColors[blueprint.status] || ""}>{blueprint.status}</Badge>
        </div>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between"><span className="text-muted-foreground">Type</span><span>{blueprint.type}</span></div>
          <div className="flex justify-between"><span className="text-muted-foreground">Version</span><span>v{blueprint.version}</span></div>
          <div className="flex justify-between"><span className="text-muted-foreground">Owner</span><span>{blueprint.owner}</span></div>
          <div className="flex justify-between"><span className="text-muted-foreground">Usage</span><span>{blueprint.usage} deployments</span></div>
          <div className="flex justify-between"><span className="text-muted-foreground">Rating</span><span>{blueprint.rating > 0 ? `${blueprint.rating}/5` : "Not rated"}</span></div>
        </div>
        <div className="flex gap-2 justify-end mt-4">
          <Button variant="outline" onClick={onClose}>Close</Button>
          <Button>Deploy</Button>
        </div>
      </div>
    </div>
  );
}

export default function TemplateRegistry() {
  const [search, setSearch] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [selectedBlueprint, setSelectedBlueprint] = useState<typeof blueprints[0] | null>(null);
  const [refresh, setRefresh] = useState(0);
  const filtered = blueprints.filter(b => search ? b.name.toLowerCase().includes(search.toLowerCase()) || b.type.includes(search) : true);

  const handleRefresh = () => setRefresh(prev => prev + 1);

  return (
    <div className="space-y-6">
      {showCreate && <CreateBlueprintModal onClose={() => setShowCreate(false)} onCreated={handleRefresh} />}
      {selectedBlueprint && <BlueprintDetailModal blueprint={selectedBlueprint} onClose={() => setSelectedBlueprint(null)} />}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Template & Blueprint Registry</h1>
        <Badge variant="outline" className="text-sm">Infra Blueprints</Badge>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Total Blueprints</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{blueprints.length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Published</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{blueprints.filter(b => b.status === "published").length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Total Usage</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{blueprints.reduce((a, b) => a + b.usage, 0)}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Avg Rating</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{blueprints.filter(b => b.rating > 0).reduce((a, b) => a + b.rating, 0).toFixed(1)}</div></CardContent></Card>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Blueprint Library</CardTitle>
            <Button onClick={() => setShowCreate(true)}>New Blueprint</Button>
          </div>
        </CardHeader>
        <CardContent>
          <Input placeholder="Search blueprints..." value={search} onChange={e => setSearch(e.target.value)} className="mb-4 max-w-sm" />
          <div className="space-y-2">
            {filtered.map(bp => (
              <div key={bp.id} className="flex items-center justify-between p-3 border rounded-lg">
                <div className="flex items-center gap-3">
                  <div><p className="font-medium">{bp.name}</p><p className="text-sm text-muted-foreground">{bp.type} &middot; v{bp.version} &middot; {bp.owner}</p></div>
                  <Badge className={statusColors[bp.status] || ""}>{bp.status}</Badge>
                </div>
                <div className="flex items-center gap-4">
                  <span className="text-sm">{bp.usage} uses</span>
                  {bp.rating > 0 && <span className="text-sm">{"★".repeat(Math.round(bp.rating))} {bp.rating}</span>}
                  <Button variant="outline" size="sm" onClick={() => setSelectedBlueprint(bp)}>Details</Button>
                  <Button variant="ghost" size="sm">Deploy</Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader><CardTitle>Blueprint Categories</CardTitle></CardHeader>
        <CardContent>
          <div className="grid gap-3 md:grid-cols-3">
            {[{ name: "Compute", count: 3 }, { name: "Network", count: 1 }, { name: "Database", count: 1 }, { name: "Security", count: 0 }, { name: "Storage", count: 1 }, { name: "Monitoring", count: 0 }].map(cat => (
              <div key={cat.name} className="border rounded-lg p-3 text-center">
                <p className="font-medium">{cat.name}</p>
                <p className="text-2xl font-bold text-blue-500">{cat.count}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {selectedBlueprint && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Blueprint Details: {selectedBlueprint.name}</CardTitle>
              <Button variant="ghost" size="sm" onClick={() => setSelectedBlueprint(null)}>Close</Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2">
              <div><label className="text-sm text-muted-foreground">ID</label><p>{selectedBlueprint.id}</p></div>
              <div><label className="text-sm text-muted-foreground">Type</label><p>{selectedBlueprint.type}</p></div>
              <div><label className="text-sm text-muted-foreground">Version</label><p>v{selectedBlueprint.version}</p></div>
              <div><label className="text-sm text-muted-foreground">Owner</label><p>{selectedBlueprint.owner}</p></div>
              <div><label className="text-sm text-muted-foreground">Status</label><Badge className={statusColors[selectedBlueprint.status] || ""}>{selectedBlueprint.status}</Badge></div>
              <div><label className="text-sm text-muted-foreground">Rating</label><p>{selectedBlueprint.rating > 0 ? "★".repeat(Math.round(selectedBlueprint.rating)) : "No ratings"}</p></div>
              <div><label className="text-sm text-muted-foreground">Usage</label><p>{selectedBlueprint.usage} deployments</p></div>
              <div><label className="text-sm text-muted-foreground">Created</label><p>{selectedBlueprint.createdAt}</p></div>
            </div>
            {selectedBlueprint.description && <div className="mt-4"><label className="text-sm text-muted-foreground">Description</label><p className="mt-1">{selectedBlueprint.description}</p></div>}
            <div className="mt-4 flex gap-2">
              <Button size="sm">Deploy Blueprint</Button>
              <Button variant="outline" size="sm">Create New Version</Button>
              <Button variant="outline" size="sm">View Version History</Button>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader><CardTitle>Version Management</CardTitle></CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex gap-2">
              <Input placeholder="Blueprint ID..." className="max-w-xs" />
              <Button variant="outline" size="sm">Archive Old Versions</Button>
              <Button variant="outline" size="sm">Merge Versions</Button>
            </div>
            <div className="border rounded-lg p-4">
              <p className="text-sm font-medium mb-2">Bulk Operations</p>
              <div className="flex gap-2">
                <Button variant="outline" size="sm">Import Blueprints from JSON</Button>
                <Button variant="outline" size="sm">Export Selected</Button>
                <Button variant="outline" size="sm">Run Health Check</Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
