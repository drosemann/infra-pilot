import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

const pueHistory = [
  { month: "Jan", pue: 1.45, target: 1.3 },
  { month: "Feb", pue: 1.42, target: 1.3 },
  { month: "Mar", pue: 1.38, target: 1.25 },
  { month: "Apr", pue: 1.35, target: 1.25 },
  { month: "May", pue: 1.32, target: 1.2 },
  { month: "Jun", pue: 1.28, target: 1.2 },
];

const facilities = [
  { name: "DC-1 San Jose", pue: 1.25, itLoad: 320, totalPower: 400, coolingEff: 85, score: 92 },
  { name: "DC-2 Dallas", pue: 1.35, itLoad: 280, totalPower: 378, coolingEff: 72, score: 78 },
  { name: "DC-3 Ashburn", pue: 1.18, itLoad: 450, totalPower: 531, coolingEff: 94, score: 96 },
];

export default function PUEDCIMPanel() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">PUE & DCIM Integration</h1>
        <Badge variant="secondary" className="text-sm">Power Efficiency</Badge>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Overall PUE</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">1.28</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Best PUE</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold text-green-500">1.18</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Total IT Load</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">1,050 kW</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Efficiency Score</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">89%</div></CardContent></Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader><CardTitle className="text-lg">PUE Trend</CardTitle></CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={pueHistory}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis domain={[1.0, 1.6]} />
                <Tooltip />
                <Line type="monotone" dataKey="pue" stroke="#ef4444" strokeWidth={2} dot={{ fill: "#ef4444" }} name="Actual PUE" />
                <Line type="monotone" dataKey="target" stroke="#10b981" strokeWidth={2} strokeDasharray="5 5" dot={false} name="Target PUE" />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle className="text-lg">Facility Comparison</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            {facilities.map(f => (
              <div key={f.name} className="space-y-2 p-3 border rounded-lg">
                <div className="flex items-center justify-between">
                  <span className="font-medium text-sm">{f.name}</span>
                  <Badge variant={f.score >= 90 ? "default" : f.score >= 75 ? "secondary" : "destructive"}>
                    Score: {f.score}
                  </Badge>
                </div>
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>PUE: {f.pue}</span>
                  <span>IT Load: {f.itLoad} kW</span>
                  <span>Total: {f.totalPower} kW</span>
                  <span>Cooling: {f.coolingEff}%</span>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader><CardTitle className="text-sm">Cooling Efficiency</CardTitle></CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">84%</div>
            <Progress value={84} className="h-2 mt-2" />
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle className="text-sm">Power Distribution Loss</CardTitle></CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">4.2%</div>
            <Progress value={96} className="h-2 mt-2" />
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle className="text-sm">Optimization Potential</CardTitle></CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">120 kW</div>
            <p className="text-xs text-muted-foreground">Potential savings identified</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
