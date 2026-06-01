import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

const gateways = [
  { id: "gw-001", name: "US-West Gateway", region: "us915", status: "online", packets: 125000, devices: 23, lastSeen: "1m ago" },
  { id: "gw-002", name: "EU-Central Gateway", region: "eu868", status: "online", packets: 98000, devices: 18, lastSeen: "30s ago" },
  { id: "gw-003", name: "APAC Gateway", region: "as923", status: "degraded", packets: 45000, devices: 12, lastSeen: "5m ago" },
  { id: "gw-004", name: "US-East Gateway", region: "us915", status: "offline", packets: 0, devices: 0, lastSeen: "2h ago" },
];

const provisionedDevices = [
  { id: "lor-001", eui: "A8:61:0A:FF:FE:00:00:01", devClass: "class_a", sf: "SF9", status: "active", lastActivity: "2m ago" },
  { id: "lor-002", eui: "A8:61:0A:FF:FE:00:00:02", devClass: "class_b", sf: "SF10", status: "active", lastActivity: "1h ago" },
  { id: "lor-003", eui: "A8:61:0A:FF:FE:00:00:03", devClass: "class_c", sf: "SF7", status: "inactive", lastActivity: "3d ago" },
];

export default function IoTProvisioningPanel() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">IoT Device Provisioning</h1>
        <Badge variant="secondary" className="text-sm">LoRaWAN</Badge>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Gateways</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">{gateways.length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Online</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold text-green-500">{gateways.filter(g => g.status === "online").length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Devices</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">{provisionedDevices.length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Packets Today</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">268K</div></CardContent></Card>
      </div>

      <Tabs defaultValue="gateways">
        <TabsList>
          <TabsTrigger value="gateways">Gateways</TabsTrigger>
          <TabsTrigger value="devices">Devices</TabsTrigger>
          <TabsTrigger value="claim">Claim Codes</TabsTrigger>
        </TabsList>

        <TabsContent value="gateways">
          <Card>
            <CardContent className="p-0">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-muted/50">
                    <th className="text-left p-3">Gateway</th>
                    <th className="text-left p-3">Region</th>
                    <th className="text-left p-3">Status</th>
                    <th className="text-right p-3">Packets</th>
                    <th className="text-right p-3">Devices</th>
                    <th className="text-left p-3">Last Seen</th>
                  </tr>
                </thead>
                <tbody>
                  {gateways.map(g => (
                    <tr key={g.id} className="border-b hover:bg-muted/50">
                      <td className="p-3 font-medium">{g.name}</td>
                      <td className="p-3 font-mono">{g.region}</td>
                      <td className="p-3">
                        <Badge variant={
                          g.status === "online" ? "default" :
                          g.status === "degraded" ? "secondary" : "destructive"
                        }>{g.status}</Badge>
                      </td>
                      <td className="p-3 text-right">{(g.packets / 1000).toFixed(0)}K</td>
                      <td className="p-3 text-right">{g.devices}</td>
                      <td className="p-3 text-muted-foreground">{g.lastSeen}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="devices">
          <Card>
            <CardContent className="p-0">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-muted/50">
                    <th className="text-left p-3">Device ID</th>
                    <th className="text-left p-3">DevEUI</th>
                    <th className="text-left p-3">Class</th>
                    <th className="text-left p-3">SF</th>
                    <th className="text-left p-3">Status</th>
                    <th className="text-left p-3">Last Activity</th>
                  </tr>
                </thead>
                <tbody>
                  {provisionedDevices.map(d => (
                    <tr key={d.id} className="border-b hover:bg-muted/50">
                      <td className="p-3 font-mono text-xs">{d.id}</td>
                      <td className="p-3 font-mono text-xs">{d.eui}</td>
                      <td className="p-3"><Badge variant="outline">{d.devClass}</Badge></td>
                      <td className="p-3 font-mono">{d.sf}</td>
                      <td className="p-3">
                        <Badge variant={d.status === "active" ? "default" : "secondary"}>{d.status}</Badge>
                      </td>
                      <td className="p-3 text-muted-foreground">{d.lastActivity}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="claim">
          <Card className="p-8 text-center text-muted-foreground">
            <p>Generate bulk claim codes for device onboarding.</p>
            <div className="flex gap-2 justify-center mt-4">
              <Badge variant="outline" className="text-sm p-2">IP-X7K9L-M3P2Q</Badge>
              <Badge variant="outline" className="text-sm p-2">IP-R4B6D-N8T1W</Badge>
              <Badge variant="outline" className="text-sm p-2">IP-H5J2F-C7V3G</Badge>
            </div>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
