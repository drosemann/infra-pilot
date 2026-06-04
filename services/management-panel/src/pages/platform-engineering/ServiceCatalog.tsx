import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

const mockServices = [
  { id: "s1", name: "user-service", owner: "platform", lang: "python", tier: "t1", score: 92, status: "active" },
  { id: "s2", name: "payment-api", owner: "finops", lang: "go", tier: "t1", score: 88, status: "active" },
  { id: "s3", name: "notification-svc", owner: "platform", lang: "typescript", tier: "t2", score: 65, status: "active" },
  { id: "s4", name: "data-pipeline", owner: "data", lang: "python", tier: "t2", score: 72, status: "active" },
  { id: "s5", name: "inventory-svc", owner: "platform", lang: "java", tier: "t3", score: 45, status: "in_development" },
  { id: "s6", name: "analytics-api", owner: "data", lang: "python", tier: "t2", score: 81, status: "active" },
  { id: "s7", name: "frontend-web", owner: "web", lang: "typescript", tier: "t3", score: 90, status: "active" },
  { id: "s8", name: "legacy-migrate", owner: "platform", lang: "php", tier: "t4", score: 25, status: "deprecated" },
];

const tierColors: Record<string, string> = { t1: "bg-red-100 text-red-700", t2: "bg-orange-100 text-orange-700", t3: "bg-blue-100 text-blue-700", t4: "bg-gray-100 text-gray-700", t5: "bg-green-100 text-green-700" };

function RegisterServiceModal({ onClose }: { onClose: () => void }) {
  const [name, setName] = useState("");
  const [owner, setOwner] = useState("");
  const [language, setLanguage] = useState("python");
  const [tier, setTier] = useState("t3");
  const handleSubmit = () => {
    mockServices.push({ id: `s${Date.now()}`, name, owner, lang: language, tier, score: 0, status: "in_development" });
    onClose();
  };
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={onClose}>
      <div className="bg-white dark:bg-gray-900 rounded-lg p-6 w-full max-w-md" onClick={e => e.stopPropagation()}>
        <h2 className="text-lg font-semibold mb-4">Register Service</h2>
        <div className="space-y-3">
          <Input placeholder="Service name" value={name} onChange={e => setName(e.target.value)} />
          <Input placeholder="Owner email" value={owner} onChange={e => setOwner(e.target.value)} />
          <select value={language} onChange={e => setLanguage(e.target.value)} className="w-full border rounded px-3 py-2 text-sm"><option value="python">Python</option><option value="go">Go</option><option value="typescript">TypeScript</option><option value="java">Java</option></select>
          <select value={tier} onChange={e => setTier(e.target.value)} className="w-full border rounded px-3 py-2 text-sm"><option value="t1">Tier 1</option><option value="t2">Tier 2</option><option value="t3">Tier 3</option><option value="t4">Tier 4</option></select>
          <div className="flex gap-2 justify-end">
            <Button variant="outline" onClick={onClose}>Cancel</Button>
            <Button onClick={handleSubmit} disabled={!name || !owner}>Register</Button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ServiceCatalog() {
  const [search, setSearch] = useState("");
  const [tierFilter, setTierFilter] = useState("");
  const [showRegister, setShowRegister] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  const filtered = mockServices.filter(s => {
    if (search && !s.name.includes(search) && !s.owner.includes(search)) return false;
    if (tierFilter && s.tier !== tierFilter) return false;
    return true;
  });

  const langData = Object.entries(mockServices.reduce((acc: Record<string, number>, s) => {
    acc[s.lang] = (acc[s.lang] || 0) + 1;
    return acc;
  }, {})).map(([name, count]) => ({ name, count }));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Service Catalog</h1>
        <Badge variant="outline" className="text-sm">Auto-Scored</Badge>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Total Services</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{mockServices.length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Average Score</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{Math.round(mockServices.reduce((a, s) => a + s.score, 0) / mockServices.length)}%</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Tier 1 Services</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{mockServices.filter(s => s.tier === "t1").length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Below Threshold</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-red-500">{mockServices.filter(s => s.score < 50).length}</div></CardContent></Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>Languages</CardTitle></CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={langData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Score Distribution</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-2">
              {[{ range: "90-100%", count: 3 }, { range: "70-89%", count: 2 }, { range: "50-69%", count: 1 }, { range: "0-49%", count: 2 }].map(r => (
                <div key={r.range} className="flex items-center gap-2"><span className="text-sm w-16">{r.range}</span><div className="flex-1 h-4 bg-gray-100 rounded"><div className="h-full bg-blue-500 rounded" style={{ width: ${(r.count / mockServices.length) * 100}% }} /></div><span className="text-sm">{r.count}</span></div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader><CardTitle>All Services</CardTitle></CardHeader>
        <CardContent>
          <div className="flex gap-2 mb-4">
          <Input placeholder="Search name or owner..." value={search} onChange={e => setSearch(e.target.value)} className="max-w-xs" />
            <select value={tierFilter} onChange={e => setTierFilter(e.target.value)} className="border rounded px-2 py-1 text-sm">
              <option value="">All Tiers</option>
              <option value="t1">Tier 1</option>
              <option value="t2">Tier 2</option>
              <option value="t3">Tier 3</option>
              <option value="t4">Tier 4</option>
            </select>
            <Button variant="outline" size="sm" onClick={() => setShowRegister(true)}>Register</Button>
          </div>
          <div className="space-y-2">
            {filtered.map(s => (
              <div key={s.id} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center gap-3">
                  <div><p className="font-medium">{s.name}</p><p className="text-sm text-muted-foreground">{s.owner} &middot; {s.lang}</p></div>
                  <Badge className={tierColors[s.tier] || ""}>{s.tier.toUpperCase()}</Badge>
                </div>
                <div className="flex items-center gap-3">
                  <div className="text-lg font-bold">{s.score}%</div>
                  <Badge variant={s.status === "active" ? "default" : "secondary"}>{s.status}</Badge>
                  <Button variant="outline" size="sm">Score</Button>
                  <Button variant="ghost" size="sm">Edit</Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Service Insights</CardTitle></CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <div className="border rounded-lg p-4 text-center"><p className="text-sm text-muted-foreground">Compliance</p><p className="text-2xl font-bold">{Math.round(filtered.filter(() => true).length * 73 / 100)}%</p></div>
            <div className="border rounded-lg p-4 text-center"><p className="text-sm text-muted-foreground">Avg Score</p><p className="text-2xl font-bold">{Math.round(filtered.reduce((a, s) => a + s.score, 0) / Math.max(filtered.length, 1))}%</p></div>
            <div className="border rounded-lg p-4 text-center"><p className="text-sm text-muted-foreground">Orphan Services</p><p className="text-2xl font-bold text-orange-500">2</p></div>
            <div className="border rounded-lg p-4 text-center"><p className="text-sm text-muted-foreground">Total Monthly Cost</p><p className="text-2xl font-bold">$12,450</p></div>
          </div>
          <div className="mt-4 flex gap-2">
            <Button variant="outline" size="sm">Run Compliance Check</Button>
            <Button variant="outline" size="sm">View Dependency Graph</Button>
            <Button variant="outline" size="sm">Export Catalog</Button>
            <Button variant="outline" size="sm">Bulk Update Tier</Button>
          </div>
        </CardContent>
      </Card>

      {showRegister && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Register New Service</CardTitle>
              <Button variant="ghost" size="sm" onClick={() => setShowRegister(false)}>Close</Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2">
              <div><label className="text-sm">Name</label><Input placeholder="my-service" /></div>
              <div><label className="text-sm">Owner</label><Input placeholder="team-name" /></div>
              <div><label className="text-sm">Language</label><select className="border rounded px-2 py-1 w-full text-sm"><option>python</option><option>typescript</option><option>go</option><option>java</option></select></div>
              <div><label className="text-sm">Tier</label><select className="border rounded px-2 py-1 w-full text-sm"><option value="t1">Tier 1</option><option value="t2">Tier 2</option><option value="t3">Tier 3</option><option value="t4">Tier 4</option></select></div>
            </div>
            <div className="mt-4"><label className="text-sm">Description</label><textarea className="border rounded px-2 py-1 w-full text-sm mt-1" rows={2} /></div>
            <div className="mt-4 flex gap-2">
              <Button>Register</Button>
              <Button variant="outline" onClick={() => setShowRegister(false)}>Cancel</Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
