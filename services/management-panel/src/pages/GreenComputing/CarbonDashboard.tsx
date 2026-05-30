import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell } from "recharts";

const energyData = [
  { month: "Jan", consumption: 420, renewable: 120, grid: 300, cost: 42000 },
  { month: "Feb", consumption: 380, renewable: 140, grid: 240, cost: 38000 },
  { month: "Mar", consumption: 450, renewable: 180, grid: 270, cost: 45000 },
  { month: "Apr", consumption: 410, renewable: 200, grid: 210, cost: 41000 },
  { month: "May", consumption: 470, renewable: 250, grid: 220, cost: 47000 },
  { month: "Jun", consumption: 520, renewable: 300, grid: 220, cost: 52000 },
];

const sourceData = [
  { name: "Solar", value: 35, color: "#fbbf24" },
  { name: "Wind", value: 25, color: "#3b82f6" },
  { name: "Grid", value: 30, color: "#6b7280" },
  { name: "Battery", value: 10, color: "#10b981" },
];

const weeklyEmissions = [
  { day: "Mon", co2: 1200 },
  { day: "Tue", co2: 1150 },
  { day: "Wed", co2: 1300 },
  { day: "Thu", co2: 1100 },
  { day: "Fri", co2: 1250 },
  { day: "Sat", co2: 950 },
  { day: "Sun", co2: 850 },
];

export default function CarbonDashboard() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Carbon Footprint Dashboard</h1>
        <Badge variant="secondary" className="text-sm">Scope 1 & 2</Badge>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Energy (MWh)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">2,650</div>
            <p className="text-xs text-muted-foreground">+12% vs last month</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">CO₂ Emissions (kg)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">7,800</div>
            <p className="text-xs text-green-500">-5% vs last month</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Renewable %</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">60%</div>
            <p className="text-xs text-green-500">+8% vs last month</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Carbon Intensity</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">294</div>
            <p className="text-xs text-muted-foreground">gCO₂eq/kWh</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Energy Consumption Trend</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={energyData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="renewable" fill="#10b981" name="Renewable" stackId="a" />
                <Bar dataKey="grid" fill="#6b7280" name="Grid" stackId="a" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Energy Source Mix</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie data={sourceData} cx="50%" cy="50%" innerRadius={60} outerRadius={100}
                     dataKey="value" label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
                  {sourceData.map(entry => (
                    <Cell key={entry.name} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Weekly CO₂ Emissions</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={weeklyEmissions}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="day" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="co2" stroke="#ef4444" strokeWidth={2}
                      dot={{ fill: "#ef4444" }} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Top Emitting Devices</CardTitle>
          </CardHeader>
          <CardContent>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-2 font-medium">Device</th>
                  <th className="text-right p-2 font-medium">kWh</th>
                  <th className="text-right p-2 font-medium">CO₂ (kg)</th>
                </tr>
              </thead>
              <tbody>
                {[
                  { name: "Server Rack A1", kWh: 12500, co2: 5250 },
                  { name: "GPU Cluster B2", kWh: 9800, co2: 4116 },
                  { name: "Storage Array C3", kWh: 7200, co2: 3024 },
                  { name: "Network Core D4", kWh: 4500, co2: 1890 },
                  { name: "Cooling Unit E5", kWh: 3800, co2: 1596 },
                ].map(d => (
                  <tr key={d.name} className="border-b">
                    <td className="p-2">{d.name}</td>
                    <td className="p-2 text-right">{d.kWh.toLocaleString()}</td>
                    <td className="p-2 text-right text-red-500">{d.co2.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
