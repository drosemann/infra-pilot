import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const nodes = [
  { id: "node-001", name: "gw-sjc-01", role: "gateway", ip: "10.0.1.1", status: "online", neighbors: 4, uptime: "92d", signal: -45 },
  { id: "node-002", name: "relay-a01", role: "relay", ip: "10.0.1.2", status: "online", neighbors: 3, uptime: "45d", signal: -52 },
  { id: "node-003", name: "relay-a02", role: "relay", ip: "10.0.1.3", status: "online", neighbors: 2, uptime: "12d", signal: -48 },
  { id: "node-004", name: "leaf-b01", role: "leaf", ip: "10.0.2.1", status: "online", neighbors: 1, uptime: "88d", signal: -61 },
  { id: "node-005", name: "gw-nyc-01", role: "gateway", ip: "10.0.10.1", status: "degraded", neighbors: 2, uptime: "3d", signal: -78 },
  { id: "node-006", name: "relay-b01", role: "relay", ip: "10.0.2.2", status: "offline", neighbors: 0, uptime: "0d", signal: -120 },
  { id: "node-007", name: "leaf-c01", role: "leaf", ip: "10.0.3.1", status: "online", neighbors: 1, uptime: "34d", signal: -55 },
  { id: "node-008", name: "gw-lon-01", role: "gateway", ip: "10.0.20.1", status: "online", neighbors: 5, uptime: "180d", signal: -40 },
];

const linkStats = [
  { pair: "gw-sjc-01 ↔ relay-a01", latency: 2, bandwidth: 1000, quality: 99 },
  { pair: "relay-a01 ↔ relay-a02", latency: 5, bandwidth: 500, quality: 95 },
  { pair: "relay-a02 ↔ leaf-b01", latency: 8, bandwidth: 100, quality: 88 },
  { pair: "gw-sjc-01 ↔ gw-nyc-01", latency: 15, bandwidth: 1000, quality: 92 },
  { pair: "gw-lon-01 ↔ relay-b01", latency: 45, bandwidth: 500, quality: 65 },
];

export default function MeshNetworkPanel() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Mesh Network Manager</h1>
        <Badge variant="secondary" className="text-sm">Routing Protocol: OSPF</Badge>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Total Nodes</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">{nodes.length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Online</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold text-green-500">{nodes.filter(n => n.status === "online").length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Avg Signal</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">-62 dBm</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Avg Hop Latency</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">3.2 ms</div></CardContent></Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader><CardTitle className="text-lg">Mesh Nodes</CardTitle></CardHeader>
          <CardContent className="p-0 max-h-80 overflow-y-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/50 sticky top-0">
                  <th className="text-left p-2">Node</th>
                  <th className="text-left p-2">Role</th>
                  <th className="text-left p-2">Status</th>
                  <th className="text-right p-2">Neighbors</th>
                  <th className="text-right p-2">Signal</th>
                </tr>
              </thead>
              <tbody>
                {nodes.map(n => (
                  <tr key={n.id} className="border-b hover:bg-muted/50">
                    <td className="p-2 font-medium font-mono text-xs">{n.name}</td>
                    <td className="p-2"><Badge variant="outline">{n.role}</Badge></td>
                    <td className="p-2">
                      <Badge variant={
                        n.status === "online" ? "default" :
                        n.status === "degraded" ? "secondary" : "destructive"
                      }>{n.status}</Badge>
                    </td>
                    <td className="p-2 text-right">{n.neighbors}</td>
                    <td className="p-2 text-right font-mono">{n.signal} dBm</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle className="text-lg">Link Quality</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {linkStats.map(l => (
              <div key={l.pair} className="p-2 border rounded-lg">
                <div className="flex justify-between text-sm">
                  <span className="font-mono text-xs">{l.pair}</span>
                  <Badge variant={l.quality >= 90 ? "default" : l.quality >= 75 ? "secondary" : "destructive"}>
                    {l.quality}%
                  </Badge>
                </div>
                <div className="text-xs text-muted-foreground mt-1">
                  Latency: {l.latency}ms · Bandwidth: {l.bandwidth} Mbps
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
