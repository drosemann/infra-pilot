import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const apis = [
  { id: "a1", name: "User Service API", type: "rest", version: "2.1.0", owner: "platform", lifecycle: "stable", endpoints: 24, consumers: 8, specUrl: "/specs/user-v2.yaml" },
  { id: "a2", name: "Payment Gateway gRPC", type: "grpc", version: "1.0.0", owner: "finops", lifecycle: "beta", endpoints: 12, consumers: 3, specUrl: "/specs/payment.proto" },
  { id: "a3", name: "Notification API", type: "rest", version: "3.0.0", owner: "platform", lifecycle: "deprecated", endpoints: 8, consumers: 5, specUrl: "/specs/notify-v3.yaml" },
  { id: "a4", name: "Analytics GraphQL", type: "graphql", version: "1.2.0", owner: "data", lifecycle: "stable", endpoints: 6, consumers: 4, specUrl: "/graphql/schema" },
  { id: "a5", name: "Inventory REST", type: "rest", version: "0.9.0", owner: "platform", lifecycle: "development", endpoints: 15, consumers: 1, specUrl: "/specs/inventory.yaml" },
  { id: "a6", name: "Data Stream WebSocket", type: "websocket", version: "1.0.0", owner: "data", lifecycle: "stable", endpoints: 3, consumers: 6, specUrl: "/specs/stream.yaml" },
];

const lifecycleColors: Record<string, string> = {
  stable: "bg-green-100 text-green-700", beta: "bg-yellow-100 text-yellow-700",
  deprecated: "bg-red-100 text-red-700", development: "bg-blue-100 text-blue-700",
  design: "bg-gray-100 text-gray-700", sunset: "bg-gray-800 text-white",
};

function RegisterApiModal({ onClose }: { onClose: () => void }) {
  const [name, setName] = useState("");
  const [apiType, setApiType] = useState("rest");
  const [version, setVersion] = useState("1.0.0");
  const [owner, setOwner] = useState("");
  const handleSubmit = () => {
    apis.push({ id: `a${Date.now()}`, name, type: apiType, version, owner, lifecycle: "development", endpoints: 0, consumers: 0, specUrl: "" });
    onClose();
  };
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={onClose}>
      <div className="bg-white dark:bg-gray-900 rounded-lg p-6 w-full max-w-md" onClick={e => e.stopPropagation()}>
        <h2 className="text-lg font-semibold mb-4">Register API</h2>
        <div className="space-y-3">
          <Input placeholder="API name" value={name} onChange={e => setName(e.target.value)} />
          <select value={apiType} onChange={e => setApiType(e.target.value)} className="w-full border rounded px-3 py-2 text-sm"><option value="rest">REST</option><option value="grpc">gRPC</option><option value="graphql">GraphQL</option><option value="websocket">WebSocket</option></select>
          <Input placeholder="Version" value={version} onChange={e => setVersion(e.target.value)} />
          <Input placeholder="Owner" value={owner} onChange={e => setOwner(e.target.value)} />
          <div className="flex gap-2 justify-end">
            <Button variant="outline" onClick={onClose}>Cancel</Button>
            <Button onClick={handleSubmit} disabled={!name || !owner}>Register</Button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ApiCatalog() {
  const [search, setSearch] = useState("");
  const [showRegister, setShowRegister] = useState(false);
  const [lifecycleFilter, setLifecycleFilter] = useState("");
  const filtered = apis.filter(a => {
    if (search && !a.name.toLowerCase().includes(search.toLowerCase()) && !a.type.includes(search)) return false;
    if (lifecycleFilter && a.lifecycle !== lifecycleFilter) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      {showRegister && <RegisterApiModal onClose={() => setShowRegister(false)} />}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">API Catalog & Governance</h1>
        <Badge variant="outline" className="text-sm">Auto-Discovered</Badge>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Total APIs</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{apis.length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Total Endpoints</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{apis.reduce((a, api) => a + api.endpoints, 0)}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Stable</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-green-500">{apis.filter(a => a.lifecycle === "stable").length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Deprecated</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-red-500">{apis.filter(a => a.lifecycle === "deprecated").length}</div></CardContent></Card>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>API Registry</CardTitle>
            <div className="flex gap-2">
              <select value={lifecycleFilter} onChange={e => setLifecycleFilter(e.target.value)} className="border rounded px-2 py-1 text-sm"><option value="">All Lifecycles</option><option value="stable">Stable</option><option value="beta">Beta</option><option value="deprecated">Deprecated</option><option value="development">Development</option></select>
              <Button variant="outline">Import OpenAPI</Button>
              <Button onClick={() => setShowRegister(true)}>Register API</Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Input placeholder="Search APIs..." value={search} onChange={e => setSearch(e.target.value)} className="mb-4 max-w-sm" />
          <div className="space-y-2">
            {filtered.map(api => (
              <div key={api.id} className="flex items-center justify-between p-3 border rounded-lg">
                <div className="flex items-center gap-3">
                  <div><p className="font-medium">{api.name}</p><p className="text-sm text-muted-foreground">{api.type.toUpperCase()} &middot; v{api.version} &middot; {api.owner}</p></div>
                  <Badge className={lifecycleColors[api.lifecycle] || ""}>{api.lifecycle}</Badge>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-sm">{api.endpoints} endpoints</span>
                  <span className="text-sm">{api.consumers} consumers</span>
                  <Button variant="outline" size="sm">View</Button>
                  <Button variant="ghost" size="sm">Spec</Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader><CardTitle>Lifecycle Distribution</CardTitle></CardHeader>
        <CardContent>
          <div className="grid gap-3 md:grid-cols-6">
            {["design", "development", "beta", "stable", "deprecated", "sunset"].map(lc => {
              const count = apis.filter(a => a.lifecycle === lc).length;
              return <div key={lc} className="border rounded-lg p-3 text-center"><p className={`text-sm capitalize ${lifecycleColors[lc] || ""}`}>{lc}</p><p className="text-xl font-bold">{count}</p></div>;
            })}
          </div>
        </CardContent>
      </Card>

      {showRegister && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Register New API</CardTitle>
              <Button variant="ghost" size="sm" onClick={() => setShowRegister(false)}>Close</Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2">
              <div><label className="text-sm">Name</label><Input placeholder="my-api" /></div>
              <div><label className="text-sm">Version</label><Input placeholder="1.0.0" /></div>
              <div><label className="text-sm">Owner</label><Input placeholder="team-name" /></div>
              <div><label className="text-sm">Protocol</label><select className="border rounded px-2 py-1 w-full text-sm"><option>REST</option><option>gRPC</option><option>GraphQL</option></select></div>
            </div>
            <div className="mt-4"><label className="text-sm">Spec URL</label><Input placeholder="https://spec.example.com/openapi.yaml" /></div>
            <div className="mt-4 flex gap-2">
              <Button>Register</Button>
              <Button variant="outline" onClick={() => setShowRegister(false)}>Cancel</Button>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader><CardTitle>API Governance</CardTitle></CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="border rounded-lg p-4">
              <p className="font-medium text-sm">Compliance Report</p>
              <p className="text-2xl font-bold mt-2">{apis.length > 0 ? Math.round(apis.filter(a => a.owner && a.version).length / apis.length * 100) : 0}%</p>
              <p className="text-xs text-muted-foreground">APIs with owner + versioning</p>
            </div>
            <div className="border rounded-lg p-4">
              <p className="font-medium text-sm">Deprecation Schedule</p>
              <p className="text-2xl font-bold mt-2 text-orange-500">{apis.filter(a => a.lifecycle === "deprecated").length}</p>
              <p className="text-xs text-muted-foreground">APIs scheduled for sunset</p>
            </div>
          </div>
          <div className="mt-4 flex gap-2">
            <Button variant="outline" size="sm">Schedule Deprecation</Button>
            <Button variant="outline" size="sm">Usage Statistics</Button>
            <Button variant="outline" size="sm">Find Duplicates</Button>
            <Button variant="outline" size="sm">Notify Consumers</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
