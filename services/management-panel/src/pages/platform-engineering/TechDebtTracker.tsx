import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

const debtItems = [
  { id: "d1", service: "user-service", category: "outdated_dependencies", severity: "critical", title: "Express v3 with CVE-2024-1234", status: "open", effort: 4 },
  { id: "d2", service: "payment-api", category: "deprecated_apis", severity: "high", title: "Stripe API v2022 deprecated", status: "in_progress", effort: 8 },
  { id: "d3", service: "notification-svc", category: "test_coverage", severity: "medium", title: "Test coverage below 60%", status: "open", effort: 16 },
  { id: "d4", service: "data-pipeline", category: "security_vulnerabilities", severity: "critical", title: "Python 3.8 EOL in 30 days", status: "open", effort: 6 },
  { id: "d5", service: "frontend-web", category: "code_smells", severity: "low", title: "Unused imports in 15 files", status: "open", effort: 2 },
  { id: "d6", service: "user-service", category: "documentation_gaps", severity: "medium", title: "Missing API docs for 5 endpoints", status: "resolved", effort: 3 },
  { id: "d7", service: "payment-api", category: "architectural_debt", severity: "high", title: "Monolith needs splitting", status: "open", effort: 40 },
  { id: "d8", service: "analytics-api", category: "performance_issues", severity: "medium", title: "Slow query >5s on dashboard", status: "in_progress", effort: 6 },
];

const severityColors: Record<string, string> = { critical: "bg-red-100 text-red-700", high: "bg-orange-100 text-orange-700", medium: "bg-yellow-100 text-yellow-700", low: "bg-blue-100 text-blue-700", info: "bg-gray-100 text-gray-700" };

const categoryData = Object.entries(debtItems.reduce((acc: Record<string, number>, d) => {
  acc[d.category] = (acc[d.category] || 0) + 1;
  return acc;
}, {})).map(([name, count]) => ({ name: name.replace(/_/g, " "), count }));

function DebtEditModal({ item, onClose }: { item: typeof debtItems[0]; onClose: () => void }) {
  const [status, setStatus] = useState(item.status);
  const [assignee, setAssignee] = useState("");
  const handleSave = () => {
    item.status = status;
    onClose();
  };
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={onClose}>
      <div className="bg-white dark:bg-gray-900 rounded-lg p-6 w-full max-w-md" onClick={e => e.stopPropagation()}>
        <h2 className="text-lg font-semibold mb-4">Edit: {item.title}</h2>
        <div className="space-y-3">
          <div className="text-sm"><span className="text-muted-foreground">Service:</span> {item.service}</div>
          <div className="text-sm"><span className="text-muted-foreground">Category:</span> {item.category.replace(/_/g, " ")}</div>
          <div className="text-sm"><span className="text-muted-foreground">Effort:</span> {item.effort}h</div>
          <select value={status} onChange={e => setStatus(e.target.value)} className="w-full border rounded px-3 py-2 text-sm">
            <option value="open">Open</option>
            <option value="in_progress">In Progress</option>
            <option value="resolved">Resolved</option>
            <option value="wont_fix">Won't Fix</option>
          </select>
          <Input placeholder="Assign to..." value={assignee} onChange={e => setAssignee(e.target.value)} />
          <div className="flex gap-2 justify-end">
            <Button variant="outline" onClick={onClose}>Cancel</Button>
            <Button onClick={handleSave}>Save</Button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function TechDebtTracker() {
  const [filter, setFilter] = useState("");
  const [editItem, setEditItem] = useState<typeof debtItems[0] | null>(null);
  const [statusFilter, setStatusFilter] = useState("");
  const filtered = debtItems.filter(d => {
    if (filter && d.severity !== filter) return false;
    if (statusFilter && d.status !== statusFilter) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      {editItem && <DebtEditModal item={editItem} onClose={() => setEditItem(null)} />}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Technical Debt Tracker</h1>
        <Badge variant="outline" className="text-sm">Auto-Detected</Badge>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Total Items</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{debtItems.length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Open</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-red-500">{debtItems.filter(d => d.status === "open").length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Critical</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-red-600">{debtItems.filter(d => d.severity === "critical").length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Est. Effort</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{debtItems.reduce((a, d) => a + d.effort, 0)}h</div></CardContent></Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>By Category</CardTitle></CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={categoryData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis type="category" dataKey="name" width={140} tick={{ fontSize: 10 }} />
                <Tooltip />
                <Bar dataKey="count" fill="#ef4444" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Severity Breakdown</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-3">
              {["critical", "high", "medium", "low"].map(sev => {
                const count = debtItems.filter(d => d.severity === sev).length;
                return <div key={sev} className="flex items-center gap-2"><span className="text-sm w-16 capitalize">{sev}</span><div className="flex-1 h-5 bg-gray-100 rounded"><div className={h-full rounded } style={{ width: ${(count / debtItems.length) * 100}% }} /></div><span className="text-sm w-6">{count}</span></div>;
              })}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Debt Items</CardTitle>
              <div className="flex items-center gap-2">
                <select value={filter} onChange={e => setFilter(e.target.value)} className="border rounded px-2 py-1 text-sm"><option value="">All Severities</option><option value="critical">Critical</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option></select>
                <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className="border rounded px-2 py-1 text-sm"><option value="">All Statuses</option><option value="open">Open</option><option value="in_progress">In Progress</option><option value="resolved">Resolved</option></select>
                <Button>Run Auto-Scan</Button>
              </div>
            </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {filtered.map(d => (
              <div key={d.id} className="flex items-center justify-between p-3 border rounded-lg">
                <div className="flex-1">
                  <div className="flex items-center gap-2"><p className="font-medium">{d.title}</p><Badge className={severityColors[d.severity] || ""} variant="outline">{d.severity}</Badge></div>
                  <p className="text-sm text-muted-foreground">{d.service} &middot; {d.category.replace(/_/g, " ")} &middot; {d.effort}h effort</p>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={d.status === "resolved" ? "default" : d.status === "in_progress" ? "secondary" : "outline"}>{d.status}</Badge>
                  <Button variant="ghost" size="sm" onClick={() => setEditItem(d)}>Edit</Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {editItem && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Edit Debt Item: {editItem.title}</CardTitle>
              <Button variant="ghost" size="sm" onClick={() => setEditItem(null)}>Close</Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2">
              <div><label className="text-sm text-muted-foreground">Severity</label><select defaultValue={editItem.severity} className="border rounded px-2 py-1 w-full text-sm"><option value="critical">Critical</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option></select></div>
              <div><label className="text-sm text-muted-foreground">Status</label><select defaultValue={editItem.status} className="border rounded px-2 py-1 w-full text-sm"><option value="open">Open</option><option value="in_progress">In Progress</option><option value="resolved">Resolved</option></select></div>
              <div><label className="text-sm text-muted-foreground">Effort Hours</label><input type="number" defaultValue={editItem.effort} className="border rounded px-2 py-1 w-full text-sm" /></div>
              <div><label className="text-sm text-muted-foreground">Assignee</label><input defaultValue={editItem.assignee || ""} className="border rounded px-2 py-1 w-full text-sm" /></div>
            </div>
            <div className="mt-4"><label className="text-sm text-muted-foreground">Resolution Notes</label><textarea className="border rounded px-2 py-1 w-full text-sm mt-1" rows={3} /></div>
            <div className="mt-4 flex gap-2">
              <Button size="sm">Save Changes</Button>
              <Button variant="outline" size="sm">Auto-Remediate</Button>
              <Button variant="outline" size="sm" onClick={() => setEditItem(null)}>Cancel</Button>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader><CardTitle>Debt Analytics & Reports</CardTitle></CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="border rounded-lg p-4">
              <p className="font-medium text-sm">Trend Analysis</p>
              <p className="text-2xl font-bold mt-2">{debtItems.filter(d => d.status === "open").length - debtItems.filter(d => d.status === "resolved").length}</p>
              <p className="text-xs text-muted-foreground">Net open items (last 90 days)</p>
            </div>
            <div className="border rounded-lg p-4">
              <p className="font-medium text-sm">Resolution Rate</p>
              <p className="text-2xl font-bold mt-2">{debtItems.length > 0 ? Math.round(debtItems.filter(d => d.status === "resolved").length / debtItems.length * 100) : 0}%</p>
              <p className="text-xs text-muted-foreground">Overall resolution rate</p>
            </div>
          </div>
          <div className="mt-4 flex gap-2">
            <Button variant="outline" size="sm">Generate Report</Button>
            <Button variant="outline" size="sm">Export CSV</Button>
            <Button variant="outline" size="sm">Schedule Auto-Scan</Button>
            <Button variant="outline" size="sm">View Service Rankings</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
