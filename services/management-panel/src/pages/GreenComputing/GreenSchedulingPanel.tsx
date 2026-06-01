import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

const hourlyData = [
  { hour: "00", intensity: 180, jobs: 2 }, { hour: "02", intensity: 150, jobs: 1 },
  { hour: "04", intensity: 130, jobs: 0 }, { hour: "06", intensity: 200, jobs: 3 },
  { hour: "08", intensity: 320, jobs: 8 }, { hour: "10", intensity: 380, jobs: 12 },
  { hour: "12", intensity: 410, jobs: 15 }, { hour: "14", intensity: 390, jobs: 14 },
  { hour: "16", intensity: 350, jobs: 10 }, { hour: "18", intensity: 300, jobs: 7 },
  { hour: "20", intensity: 250, jobs: 4 }, { hour: "22", intensity: 200, jobs: 2 },
];

const recommendations = [
  { job: "Backup Task", currentTime: "14:00", suggestedTime: "02:00", savings: "0.8 kg CO₂" },
  { job: "Data Sync", currentTime: "10:00", suggestedTime: "04:00", savings: "1.2 kg CO₂" },
  { job: "Batch Processing", currentTime: "16:00", suggestedTime: "06:00", savings: "2.1 kg CO₂" },
];

export default function GreenSchedulingPanel() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Green Scheduling</h1>
        <Badge variant="secondary" className="text-sm">Carbon-Aware</Badge>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Scheduled Jobs</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">47</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Carbon Saved</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold text-green-500">12.4 kg</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Avg Delay</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">3.2h</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Optimization</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">94%</div></CardContent></Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader><CardTitle className="text-lg">Carbon Intensity by Hour</CardTitle></CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={hourlyData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="hour" />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" />
                <Tooltip />
                <Bar yAxisId="left" dataKey="intensity" fill="#ef4444" name="Intensity (gCO₂/kWh)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle className="text-lg">Optimization Recommendations</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {recommendations.map(r => (
              <div key={r.job} className="flex items-center justify-between p-3 bg-muted/30 rounded-lg">
                <div>
                  <div className="font-medium text-sm">{r.job}</div>
                  <div className="text-xs text-muted-foreground">
                    {r.currentTime} → <span className="text-green-500">{r.suggestedTime}</span>
                  </div>
                </div>
                <Badge variant="outline" className="text-green-500">{r.savings}</Badge>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader><CardTitle className="text-lg">Active Scheduling Policies</CardTitle></CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[
              { name: "Low Carbon Hours", desc: "Schedule non-urgent jobs between 00:00-06:00", enabled: true, threshold: "200 gCO₂/kWh" },
              { name: "Renewable Priority", desc: "Prefer scheduling when renewable > 50%", enabled: true, threshold: "50% renewable" },
              { name: "Cost Optimization", desc: "Balance carbon and cost based on spot pricing", enabled: false, threshold: "N/A" },
            ].map(p => (
              <div key={p.name} className="flex items-center justify-between p-3 border rounded-lg">
                <div>
                  <div className="font-medium text-sm">{p.name}</div>
                  <div className="text-xs text-muted-foreground">{p.desc}</div>
                  <Badge variant="outline" className="text-xs mt-1">{p.threshold}</Badge>
                </div>
                <Badge variant={p.enabled ? "default" : "secondary"}>{p.enabled ? "Active" : "Paused"}</Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
