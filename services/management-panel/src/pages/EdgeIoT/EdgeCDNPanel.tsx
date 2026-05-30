import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from "recharts";

const cacheStats = {
  totalObjects: 45230,
  totalSize: "2.4 TB",
  hitRate: 94.2,
  avgLatency: 12,
  diskUsage: 68,
};

const topContent = [
  { path: "/images/logo.png", hits: 125000, size: "2.1 MB", hitRate: 98 },
  { path: "/videos/intro.mp4", hits: 45000, size: "45 MB", hitRate: 92 },
  { path: "/js/bundle.js", hits: 38000, size: "1.8 MB", hitRate: 96 },
  { path: "/css/styles.css", hits: 22000, size: "240 KB", hitRate: 99 },
  { path: "/api/data.json", hits: 18000, size: "4.5 MB", hitRate: 85 },
];

const hourlyTraffic = [
  { hour: "00", hits: 1200 }, { hour: "02", hits: 850 }, { hour: "04", hits: 720 },
  { hour: "06", hits: 1800 }, { hour: "08", hits: 4500 }, { hour: "10", hits: 7200 },
  { hour: "12", hits: 8900 }, { hour: "14", hits: 9500 }, { hour: "16", hits: 8800 },
  { hour: "18", hits: 6200 }, { hour: "20", hits: 4100 }, { hour: "22", hits: 2400 },
];

export default function EdgeCDNPanel() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Edge CDN</h1>
        <Badge variant="secondary" className="text-sm">Edge Location: US-West</Badge>
      </div>

      <div className="grid gap-4 md:grid-cols-5">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Objects</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">{(cacheStats.totalObjects / 1000).toFixed(1)}K</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Total Size</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">{cacheStats.totalSize}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Hit Rate</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold text-green-500">{cacheStats.hitRate}%</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Avg Latency</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">{cacheStats.avgLatency}ms</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Disk Usage</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">{cacheStats.diskUsage}%</div></CardContent></Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader><CardTitle className="text-lg">Hourly Traffic</CardTitle></CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={hourlyTraffic}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="hour" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="hits" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle className="text-lg">Top Content by Hits</CardTitle></CardHeader>
          <CardContent className="p-0">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-2">Path</th>
                  <th className="text-right p-2">Hits</th>
                  <th className="text-right p-2">Size</th>
                  <th className="text-right p-2">Hit Rate</th>
                </tr>
              </thead>
              <tbody>
                {topContent.map(c => (
                  <tr key={c.path} className="border-b hover:bg-muted/50">
                    <td className="p-2 font-mono text-xs">{c.path}</td>
                    <td className="p-2 text-right">{(c.hits / 1000).toFixed(1)}K</td>
                    <td className="p-2 text-right">{c.size}</td>
                    <td className="p-2 text-right text-green-500">{c.hitRate}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="policies">
        <TabsList>
          <TabsTrigger value="policies">Cache Policies</TabsTrigger>
          <TabsTrigger value="origins">Origin Shields</TabsTrigger>
          <TabsTrigger value="invalidate">Invalidate</TabsTrigger>
        </TabsList>
        <TabsContent value="policies" className="mt-4">
          <Card>
            <CardContent className="p-4 space-y-3">
              {["images/* → 24h TTL", "videos/* → 72h TTL", "js/css/* → 7d TTL", "api/* → 5m TTL"].map(p => (
                <div key={p} className="flex items-center justify-between p-2 bg-muted/30 rounded">
                  <span className="font-mono text-sm">{p}</span>
                  <Badge variant="outline">Enabled</Badge>
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="origins" className="mt-4">
          <Card className="p-8 text-center text-muted-foreground">
            <p>Origin shield configurations</p>
            <p className="text-sm">3 origin shields active across 2 regions</p>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
