import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

const devices = [
  { id: "dev-001", name: "Temp Sensor A1", type: "sensor", status: "online", battery: 87, lastSeen: "2m ago", firmware: "2.1.3" },
  { id: "dev-002", name: "Gateway NYC-1", type: "gateway", status: "online", battery: 100, lastSeen: "1m ago", firmware: "3.0.1" },
  { id: "dev-003", name: "Camera B2", type: "camera", status: "offline", battery: 12, lastSeen: "2h ago", firmware: "1.9.8" },
  { id: "dev-004", name: "Actuator C1", type: "actuator", status: "online", battery: 94, lastSeen: "30s ago", firmware: "1.2.0" },
  { id: "dev-005", name: "Humidity Sensor D3", type: "sensor", status: "degraded", battery: 45, lastSeen: "10m ago", firmware: "2.1.1" },
];

export default function DigitalTwinViewer() {
  const onlineCount = devices.filter(d => d.status === "online").length;
  const offlineCount = devices.filter(d => d.status === "offline").length;
  const degradedCount = devices.filter(d => d.status === "degraded").length;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Digital Twin Viewer</h1>
        <Badge variant="outline" className="text-sm">
          {devices.length} Devices
        </Badge>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Online</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{onlineCount}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Degraded</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-amber-500">{degradedCount}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Offline</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-500">{offlineCount}</div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="grid">
        <TabsList>
          <TabsTrigger value="grid">Grid View</TabsTrigger>
          <TabsTrigger value="list">List View</TabsTrigger>
          <TabsTrigger value="map">Map View</TabsTrigger>
        </TabsList>

        <TabsContent value="grid" className="mt-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {devices.map(device => (
              <Card key={device.id} className="cursor-pointer hover:shadow-lg transition-shadow">
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm font-medium">{device.name}</CardTitle>
                    <Badge variant={
                      device.status === "online" ? "default" :
                      device.status === "degraded" ? "secondary" : "destructive"
                    }>
                      {device.status}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="text-sm text-muted-foreground space-y-1">
                  <div className="flex justify-between">
                    <span>ID</span>
                    <span className="font-mono">{device.id}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Type</span>
                    <span>{device.type}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Battery</span>
                    <span className={device.battery < 20 ? "text-red-500 font-bold" : ""}>
                      {device.battery}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Firmware</span>
                    <span className="font-mono">{device.firmware}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Last Seen</span>
                    <span>{device.lastSeen}</span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="list" className="mt-4">
          <Card>
            <CardContent className="p-0">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-3 font-medium">Device</th>
                    <th className="text-left p-3 font-medium">Type</th>
                    <th className="text-left p-3 font-medium">Status</th>
                    <th className="text-left p-3 font-medium">Battery</th>
                    <th className="text-left p-3 font-medium">Firmware</th>
                    <th className="text-left p-3 font-medium">Last Seen</th>
                  </tr>
                </thead>
                <tbody>
                  {devices.map(device => (
                    <tr key={device.id} className="border-b hover:bg-muted/50">
                      <td className="p-3 font-medium">{device.name}</td>
                      <td className="p-3">{device.type}</td>
                      <td className="p-3">
                        <Badge variant={
                          device.status === "online" ? "default" :
                          device.status === "degraded" ? "secondary" : "destructive"
                        }>
                          {device.status}
                        </Badge>
                      </td>
                      <td className="p-3">
                        <span className={device.battery < 20 ? "text-red-500 font-bold" : ""}>
                          {device.battery}%
                        </span>
                      </td>
                      <td className="p-3 font-mono">{device.firmware}</td>
                      <td className="p-3 text-muted-foreground">{device.lastSeen}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="map" className="mt-4">
          <Card className="p-12 text-center text-muted-foreground">
            <div className="text-4xl mb-4">🗺️</div>
            <p>Map view requires geolocation data.</p>
            <p className="text-sm">Configure device locations to enable this view.</p>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
