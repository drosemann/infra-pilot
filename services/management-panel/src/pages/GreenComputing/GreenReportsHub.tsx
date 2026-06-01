import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line } from "recharts";

const monthlyData = [
  { month: "Jan", energy: 420, cost: 50400, co2: 123 },
  { month: "Feb", energy: 380, cost: 45600, co2: 112 },
  { month: "Mar", energy: 450, cost: 54000, co2: 132 },
  { month: "Apr", energy: 410, cost: 49200, co2: 120 },
  { month: "May", energy: 470, cost: 56400, co2: 138 },
  { month: "Jun", energy: 520, cost: 62400, co2: 153 },
];

const reports = [
  { id: "r-001", name: "Monthly Energy Summary", type: "energy", period: "Jun 2026", status: "ready", size: "2.4 MB" },
  { id: "r-002", name: "Carbon Footprint Q2 2026", type: "carbon", period: "Q2 2026", status: "ready", size: "1.8 MB" },
  { id: "r-003", name: "PUE Efficiency Report", type: "pue", period: "Jun 2026", status: "generating", size: "-" },
  { id: "r-004", name: "Hardware Lifecycle Audit", type: "hardware", period: "H1 2026", status: "ready", size: "4.2 MB" },
  { id: "r-005", name: "Sustainability Scorecard", type: "sustainability", period: "Q2 2026", status: "draft", size: "-" },
  { id: "r-006", name: "CO2 Offset Portfolio", type: "offset", period: "Jun 2026", status: "ready", size: "0.6 MB" },
];

const complianceChecks = [
  { name: "ISO 14001", status: "compliant", score: 92 },
  { name: "SOC 2 Type II", status: "compliant", score: 88 },
  { name: "Carbon Neutral", status: "in_progress", score: 65 },
  { name: "RE100", status: "compliant", score: 100 },
  { name: "EU Taxonomy", status: "compliant", score: 78 },
];

export default function GreenReportsHub() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Green Reports Hub</h1>
        <Badge variant="secondary" className="text-sm">Compliance Ready</Badge>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Total Reports</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">{reports.length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Ready to Download</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold text-green-500">{reports.filter(r => r.status === "ready").length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Compliance Score</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">85%</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Last Generated</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">2h ago</div></CardContent></Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader><CardTitle className="text-lg">Energy & Cost Trend</CardTitle></CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={monthlyData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" />
                <Tooltip />
                <Bar yAxisId="left" dataKey="energy" fill="#3b82f6" name="Energy (MWh)" radius={[4, 4, 0, 0]} />
                <Bar yAxisId="right" dataKey="co2" fill="#ef4444" name="CO₂ (tonnes)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle className="text-lg">Compliance Status</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {complianceChecks.map(c => (
              <div key={c.name} className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span>{c.name}</span>
                  <Badge variant={
                    c.status === "compliant" ? "default" :
                    c.status === "in_progress" ? "secondary" : "destructive"
                  }>{c.status}</Badge>
                </div>
                <Progress value={c.score} className="h-2" />
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader><CardTitle className="text-lg">Available Reports</CardTitle></CardHeader>
        <CardContent className="p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/50">
                <th className="text-left p-3">Report Name</th>
                <th className="text-left p-3">Type</th>
                <th className="text-left p-3">Period</th>
                <th className="text-left p-3">Status</th>
                <th className="text-right p-3">Size</th>
                <th className="text-left p-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {reports.map(r => (
                <tr key={r.id} className="border-b hover:bg-muted/50">
                  <td className="p-3 font-medium">{r.name}</td>
                  <td className="p-3"><Badge variant="outline">{r.type}</Badge></td>
                  <td className="p-3 text-muted-foreground">{r.period}</td>
                  <td className="p-3">
                    <Badge variant={
                      r.status === "ready" ? "default" :
                      r.status === "generating" ? "secondary" : "outline"
                    }>{r.status}</Badge>
                  </td>
                  <td className="p-3 text-right text-muted-foreground">{r.size}</td>
                  <td className="p-3">
                    <Badge variant="default" className="cursor-pointer hover:bg-primary/80">
                      {r.status === "ready" ? "Download" : r.status === "generating" ? "..." : "Edit"}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}
