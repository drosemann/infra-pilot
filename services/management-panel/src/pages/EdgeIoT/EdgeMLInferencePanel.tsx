import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from "recharts";

const models = [
  { id: "m-001", name: "temp-anomaly-detector", format: "tflite", status: "active", accuracy: 94.2, latency: 8, device: "dev-001", version: "2.1.0" },
  { id: "m-002", name: "object-detector-lite", format: "onnx", status: "active", accuracy: 89.5, latency: 45, device: "dev-002", version: "1.0.0" },
  { id: "m-003", name: "predictive-maintenance", format: "openvino", status: "active", accuracy: 92.8, latency: 12, device: "dev-003", version: "3.0.0" },
  { id: "m-004", name: "audio-classifier", format: "tflite", status: "inactive", accuracy: 87.1, latency: 22, device: "dev-004", version: "0.9.0" },
  { id: "m-005", name: "power-forecaster", format: "onnx", status: "active", accuracy: 91.3, latency: 6, device: "dev-001", version: "1.2.0" },
];

const dailyInferences = [
  { day: "Mon", count: 12500, avgLatency: 12 },
  { day: "Tue", count: 11800, avgLatency: 11 },
  { day: "Wed", count: 14200, avgLatency: 13 },
  { day: "Thu", count: 13800, avgLatency: 10 },
  { day: "Fri", count: 15200, avgLatency: 14 },
  { day: "Sat", count: 8900, avgLatency: 9 },
  { day: "Sun", count: 7600, avgLatency: 8 },
];

export default function EdgeMLInferencePanel() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Edge ML Inference</h1>
        <Badge variant="secondary" className="text-sm">{models.filter(m => m.status === "active").length} Models Active</Badge>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Models</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">{models.length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Avg Accuracy</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold text-green-500">91.6%</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Avg Latency</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">16 ms</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Today's Inferences</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">83.6K</div></CardContent></Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader><CardTitle className="text-lg">Daily Inference Volume</CardTitle></CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={dailyInferences}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="day" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#8b5cf6" radius={[4, 4, 0, 0]} name="Inferences" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle className="text-lg">Model Details</CardTitle></CardHeader>
          <CardContent className="p-0">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/50">
                  <th className="text-left p-2">Model</th>
                  <th className="text-left p-2">Format</th>
                  <th className="text-left p-2">Status</th>
                  <th className="text-right p-2">Accuracy</th>
                  <th className="text-right p-2">Latency</th>
                </tr>
              </thead>
              <tbody>
                {models.map(m => (
                  <tr key={m.id} className="border-b hover:bg-muted/50">
                    <td className="p-2 font-mono text-xs">{m.name}</td>
                    <td className="p-2"><Badge variant="outline">{m.format}</Badge></td>
                    <td className="p-2">
                      <Badge variant={m.status === "active" ? "default" : "secondary"}>{m.status}</Badge>
                    </td>
                    <td className="p-2 text-right">{m.accuracy}%</td>
                    <td className="p-2 text-right font-mono">{m.latency}ms</td>
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
