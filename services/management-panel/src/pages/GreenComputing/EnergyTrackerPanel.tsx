import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from "recharts";

const dailyUsage = [
  { day: "Mon", grid: 320, solar: 120, wind: 80, total: 520 },
  { day: "Tue", grid: 300, solar: 140, wind: 70, total: 510 },
  { day: "Wed", grid: 340, solar: 130, wind: 90, total: 560 },
  { day: "Thu", grid: 310, solar: 160, wind: 85, total: 555 },
  { day: "Fri", grid: 350, solar: 150, wind: 95, total: 595 },
  { day: "Sat", grid: 280, solar: 180, wind: 100, total: 560 },
  { day: "Sun", grid: 260, solar: 200, wind: 90, total: 550 },
];

const topDevices = [
  { name: "Server Rack A1", watts: 2450, daily: 58.8, pct: 18 },
  { name: "GPU Cluster B2", watts: 3800, daily: 91.2, pct: 28 },
  { name: "Storage Array C3", watts: 1800, daily: 43.2, pct: 13 },
  { name: "Network Core D4", watts: 1200, daily: 28.8, pct: 9 },
  { name: "Cooling Unit E5", watts: 2200, daily: 52.8, pct: 16 },
];

export default function EnergyTrackerPanel() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Energy Consumption Tracker</h1>
        <Badge variant="secondary" className="text-sm">Real-time Monitoring</Badge>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Current Draw</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">14.6 kW</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Today's Usage</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">350 kWh</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Peak Power</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">18.2 kW</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">This Month</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">10,850 kWh</div></CardContent></Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader><CardTitle className="text-lg">Daily Consumption (kWh)</CardTitle></CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={dailyUsage}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="day" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="grid" stackId="a" fill="#6b7280" name="Grid" />
                <Bar dataKey="solar" stackId="a" fill="#fbbf24" name="Solar" />
                <Bar dataKey="wind" stackId="a" fill="#3b82f6" name="Wind" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle className="text-lg">Top Energy Consumers</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {topDevices.map(d => (
              <div key={d.name} className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span>{d.name}</span>
                  <span className="font-mono">{d.watts}W</span>
                </div>
                <Progress value={d.pct} className="h-2" />
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>{d.daily} kWh/day</span>
                  <span>{d.pct}% of total</span>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader><CardTitle className="text-lg">Source Mix</CardTitle></CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4 text-center">
            {[
              { source: "Grid", pct: 55, color: "#6b7280" },
              { source: "Solar", pct: 28, color: "#fbbf24" },
              { source: "Wind", pct: 17, color: "#3b82f6" },
            ].map(s => (
              <div key={s.source} className="p-4 bg-muted/30 rounded-lg">
                <div className="text-3xl font-bold" style={{ color: s.color }}>{s.pct}%</div>
                <div className="text-sm text-muted-foreground mt-1">{s.source}</div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
