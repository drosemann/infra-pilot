import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from "recharts";

const surveys = [
  { id: "s1", title: "Platform NPS Q2 2026", type: "nps", status: "active", responses: 47, target: 120, nps: 42, createdAt: "2026-04-01" },
  { id: "s2", title: "Developer Satisfaction Survey", type: "satisfaction", status: "closed", responses: 85, target: 100, nps: 58, createdAt: "2026-03-15" },
  { id: "s3", title: "Tooling Feedback", type: "tooling", status: "active", responses: 32, target: 80, nps: 35, createdAt: "2026-05-01" },
  { id: "s4", title: "Team Wellbeing Check", type: "wellbeing", status: "draft", responses: 0, target: 50, nps: 0, createdAt: "2026-05-28" },
  { id: "s5", title: "Platform Experience Q1", type: "platform", status: "closed", responses: 92, target: 100, nps: 62, createdAt: "2026-01-10" },
];

const npsTrend = [
  { month: "Jan", nps: 45 },
  { month: "Feb", nps: 52 },
  { month: "Mar", nps: 58 },
  { month: "Apr", nps: 48 },
  { month: "May", nps: 42 },
  { month: "Jun", nps: 55 },
];

const statusColors: Record<string, string> = { active: "bg-green-100 text-green-700", closed: "bg-gray-100 text-gray-700", draft: "bg-blue-100 text-blue-700", archived: "bg-yellow-100 text-yellow-700" };

function CreateSurveyModal({ onClose }: { onClose: () => void }) {
  const [title, setTitle] = useState("");
  const [surveyType, setSurveyType] = useState("nps");
  const [createdBy, setCreatedBy] = useState("current-user");
  const handleSubmit = () => {
    surveys.push({ id: `s${Date.now()}`, title, type: surveyType, status: "draft", responses: 0, target: 100, nps: 0, createdAt: new Date().toISOString().slice(0, 10) });
    onClose();
  };
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={onClose}>
      <div className="bg-white dark:bg-gray-900 rounded-lg p-6 w-full max-w-md" onClick={e => e.stopPropagation()}>
        <h2 className="text-lg font-semibold mb-4">Create Survey</h2>
        <div className="space-y-3">
          <Input placeholder="Survey title" value={title} onChange={e => setTitle(e.target.value)} />
          <select value={surveyType} onChange={e => setSurveyType(e.target.value)} className="w-full border rounded px-3 py-2 text-sm">
            <option value="nps">NPS</option>
            <option value="satisfaction">Satisfaction</option>
            <option value="wellbeing">Wellbeing</option>
            <option value="tooling">Tooling</option>
            <option value="platform">Platform</option>
          </select>
          <Input placeholder="Created by" value={createdBy} onChange={e => setCreatedBy(e.target.value)} />
          <div className="flex gap-2 justify-end">
            <Button variant="outline" onClick={onClose}>Cancel</Button>
            <Button onClick={handleSubmit} disabled={!title}>Create</Button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function DeveloperPulse() {
  const [showCreate, setShowCreate] = useState(false);
  const [typeFilter, setTypeFilter] = useState("");
  const filtered = typeFilter ? surveys.filter(s => s.type === typeFilter) : surveys;

  return (
    <div className="space-y-6">
      {showCreate && <CreateSurveyModal onClose={() => setShowCreate(false)} />}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Developer Feedback & Pulse</h1>
        <Badge variant="outline" className="text-sm">NPS + Sentiment</Badge>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Total Surveys</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{surveys.length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Active</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-green-500">{surveys.filter(s => s.status === "active").length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Total Responses</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{surveys.reduce((a, s) => a + s.responses, 0)}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Avg NPS</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{Math.round(surveys.filter(s => s.nps > 0).reduce((a, s) => a + s.nps, 0) / surveys.filter(s => s.nps > 0).length)}</div></CardContent></Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>NPS Trend</CardTitle></CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={npsTrend}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis domain={[0, 100]} />
                <Tooltip />
                <Line type="monotone" dataKey="nps" stroke="#3b82f6" strokeWidth={2} dot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Survey Responses</CardTitle></CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={surveys.filter(s => s.responses > 0)}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="title" tick={{ fontSize: 10 }} />
                <YAxis />
                <Tooltip />
                <Bar dataKey="responses" fill="#10b981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Surveys</CardTitle>
            <div className="flex gap-2">
              <select value={typeFilter} onChange={e => setTypeFilter(e.target.value)} className="border rounded px-2 py-1 text-sm"><option value="">All Types</option><option value="nps">NPS</option><option value="satisfaction">Satisfaction</option><option value="wellbeing">Wellbeing</option><option value="tooling">Tooling</option></select>
              <Button onClick={() => setShowCreate(true)}>Create Survey</Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {filtered.map(s => (
              <div key={s.id} className="flex items-center justify-between p-3 border rounded-lg">
                <div>
                  <div className="flex items-center gap-2"><p className="font-medium">{s.title}</p><Badge className={statusColors[s.status] || ""}>{s.status}</Badge></div>
                  <p className="text-sm text-muted-foreground">{s.type} &middot; {s.responses}/{s.target} responses &middot; Created {s.createdAt}</p>
                </div>
                <div className="flex items-center gap-3">
                  {s.nps > 0 && <span className="text-lg font-bold">{s.nps}</span>}
                  <Button variant="outline" size="sm">View</Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {showCreate && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Create New Survey</CardTitle>
              <Button variant="ghost" size="sm" onClick={() => setShowCreate(false)}>Close</Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <Input placeholder="Survey title" />
              <select className="border rounded px-2 py-1 w-full text-sm"><option value="nps">NPS</option><option value="satisfaction">Satisfaction</option><option value="wellbeing">Wellbeing</option><option value="tooling">Tooling</option></select>
              <textarea className="border rounded px-2 py-1 w-full text-sm" rows={3} placeholder="Questions (one per line)" />
              <Input placeholder="Target audience (comma-separated)" />
              <div className="flex gap-2">
                <Button>Create Survey</Button>
                <Button variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader><CardTitle>Sentiment & Insights</CardTitle></CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="border rounded-lg p-4">
              <p className="font-medium text-sm">NPS Score</p>
              <p className="text-3xl font-bold mt-2">{surveys.length > 0 ? Math.round(surveys.reduce((a, s) => a + (s.nps || 0), 0) / surveys.length) : 0}</p>
              <p className="text-xs text-muted-foreground">Average across all surveys</p>
            </div>
            <div className="border rounded-lg p-4">
              <p className="font-medium text-sm">Response Rate</p>
              <p className="text-3xl font-bold mt-2">{surveys.length > 0 ? Math.round(surveys.reduce((a, s) => a + (s.responses / Math.max(s.target, 1)), 0) / surveys.length * 100) : 0}%</p>
              <p className="text-xs text-muted-foreground">Average response rate</p>
            </div>
          </div>
          <div className="mt-4 flex gap-2">
            <Button variant="outline" size="sm">Aggregate Results</Button>
            <Button variant="outline" size="sm">Sentiment Trend</Button>
            <Button variant="outline" size="sm">Export Survey Data</Button>
            <Button variant="outline" size="sm">Schedule Recurring</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
