import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from "recharts";

const COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899"];

const mockComponents = [
  { id: "c1", name: "user-service", type: "service", owner: "platform-team", health: 92, maturity: "level_4", deps: 3, depBy: 5 },
  { id: "c2", name: "payment-api", type: "api", owner: "finops-team", health: 88, maturity: "level_3", deps: 2, depBy: 8 },
  { id: "c3", name: "auth-lib", type: "library", owner: "security-team", health: 95, maturity: "level_5", deps: 0, depBy: 12 },
  { id: "c4", name: "notification-svc", type: "service", owner: "platform-team", health: 78, maturity: "level_2", deps: 4, depBy: 3 },
  { id: "c5", name: "data-pipeline", type: "service", owner: "data-team", health: 85, maturity: "level_3", deps: 5, depBy: 2 },
  { id: "c6", name: "frontend-web", type: "service", owner: "web-team", health: 90, maturity: "level_3", deps: 6, depBy: 1 },
];

const maturityData = [
  { name: "Level 1", count: 1, fill: "#3b82f6" },
  { name: "Level 2", count: 1, fill: "#10b981" },
  { name: "Level 3", count: 3, fill: "#f59e0b" },
  { name: "Level 4", count: 1, fill: "#8b5cf6" },
  { name: "Level 5", count: 1, fill: "#ec4899" },
];

function RegisterComponentModal({ onClose }: { onClose: () => void }) {
  const [name, setName] = useState("");
  const [compType, setCompType] = useState("service");
  const [owner, setOwner] = useState("");
  const handleSubmit = () => {
    mockComponents.push({ id: `c${Date.now()}`, name, type: compType, owner, health: 100, maturity: "level_1", deps: 0, depBy: 0 });
    onClose();
  };
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={onClose}>
      <div className="bg-white dark:bg-gray-900 rounded-lg p-6 w-full max-w-md" onClick={e => e.stopPropagation()}>
        <h2 className="text-lg font-semibold mb-4">Register Component</h2>
        <div className="space-y-3">
          <Input placeholder="Component name" value={name} onChange={e => setName(e.target.value)} />
          <select value={compType} onChange={e => setCompType(e.target.value)} className="w-full border rounded px-3 py-2 text-sm"><option value="service">Service</option><option value="api">API</option><option value="library">Library</option></select>
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

export default function DeveloperPortal() {
  const [search, setSearch] = useState("");
  const [filtered, setFiltered] = useState(mockComponents);
  const [showRegister, setShowRegister] = useState(false);
  const [typeFilter, setTypeFilter] = useState("");

  useEffect(() => {
    let result = mockComponents;
    if (search) result = result.filter(c => c.name.includes(search) || c.owner.includes(search));
    if (typeFilter) result = result.filter(c => c.type === typeFilter);
    setFiltered(result);
  }, [search, typeFilter]);

  const getHealthColor = (h: number) => h >= 90 ? "text-green-500" : h >= 75 ? "text-yellow-500" : "text-red-500";

  return (
    <div className="space-y-6">
          <div className="flex items-center justify-between">
            <CardTitle>Software Catalog</CardTitle>
            <div className="flex gap-2">
              <select value={typeFilter} onChange={e => setTypeFilter(e.target.value)} className="border rounded px-2 py-1 text-sm"><option value="">All Types</option><option value="service">Service</option><option value="api">API</option><option value="library">Library</option></select>
              <Button size="sm" onClick={() => setShowRegister(true)}>Register</Button>
            </div>
          </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Components</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{mockComponents.length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Systems</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">4</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Avg Health</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">88%</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Maturity Level 4+</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">2</div></CardContent></Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>Maturity Distribution</CardTitle></CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={maturityData}>
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
          <CardHeader><CardTitle>By Type</CardTitle></CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie data={[{ name: "Services", value: 4 }, { name: "APIs", value: 1 }, { name: "Libraries", value: 1 }]} cx="50%" cy="50%" outerRadius={80} label dataKey="value">
                  {[{ name: "S", value: 4 }, { name: "A", value: 1 }, { name: "L", value: 1 }].map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader><CardTitle>Software Catalog</CardTitle></CardHeader>
        <CardContent>
          <Input placeholder="Search by name or owner..." value={search} onChange={e => setSearch(e.target.value)} className="max-w-sm" />
          <div className="mt-4 space-y-2">
            {showRegister && <RegisterComponentModal onClose={() => setShowRegister(false)} />}
            {filtered.map(c => (
              <div key={c.id} className="flex items-center justify-between p-3 rounded-lg border">
                <div className="flex items-center gap-3">
                  <div><p className="font-medium">{c.name}</p><p className="text-sm text-muted-foreground">{c.type} &middot; {c.owner}</p></div>
                </div>
                <div className="flex items-center gap-4">
                  <span className={getHealthColor(c.health)}>{c.health}%</span>
                  <Badge>{c.maturity}</Badge>
                  <span className="text-sm text-muted-foreground">Deps: {c.deps} &middot; Used by: {c.depBy}</span>
                  <Button variant="outline" size="sm">View</Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {showRegister && <RegisterComponentModal onClose={() => setShowRegister(false)} />}

      <Card>
        <CardHeader><CardTitle>Portal Insights</CardTitle></CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <div className="border rounded-lg p-4 text-center"><p className="text-sm text-muted-foreground">Avg Maturity</p><p className="text-2xl font-bold">67%</p></div>
            <div className="border rounded-lg p-4 text-center"><p className="text-sm text-muted-foreground">Healthy</p><p className="text-2xl font-bold text-green-500">4</p></div>
            <div className="border rounded-lg p-4 text-center"><p className="text-sm text-muted-foreground">Needs Attention</p><p className="text-2xl font-bold text-orange-500">2</p></div>
            <div className="border rounded-lg p-4 text-center"><p className="text-sm text-muted-foreground">Critical</p><p className="text-2xl font-bold text-red-500">1</p></div>
          </div>
          <div className="mt-4 flex gap-2">
            <Button variant="outline" size="sm">Dependency Visualization</Button>
            <Button variant="outline" size="sm">Portal Scorecard</Button>
            <Button variant="outline" size="sm">Search Portal</Button>
            <Button variant="outline" size="sm">Bulk Update Owner</Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>System Maturity</CardTitle></CardHeader>
        <CardContent>
          <div className="space-y-2">
            {[{ name: "Payment System", score: 82, level: "gold" }, { name: "User Management", score: 65, level: "silver" }, { name: "Data Pipeline", score: 45, level: "bronze" }].map(sys => (
              <div key={sys.name} className="flex items-center justify-between p-3 border rounded-lg">
                <p className="font-medium">{sys.name}</p>
                <div className="flex items-center gap-3">
                  <div className="h-2 w-32 bg-gray-100 rounded"><div className="h-full bg-blue-500 rounded" style={{ width: `${sys.score}%` }} /></div>
                  <span className="text-sm font-bold">{sys.score}%</span>
                  <Badge>{sys.level}</Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
