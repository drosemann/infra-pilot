import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";

const assets = [
  { id: "a-001", name: "Dell R740-01", type: "server", status: "active", age: 2.5, eol: "2028-06", warranty: "2027-01", location: "DC-1 Rack A3" },
  { id: "a-002", name: "Cisco 9300-01", type: "switch", status: "active", age: 1.2, eol: "2030-03", warranty: "2028-09", location: "DC-1 Rack B1" },
  { id: "a-003", name: "NetApp FAS8200", type: "storage", status: "active", age: 3.8, eol: "2026-12", warranty: "2025-06", location: "DC-2 Rack C2" },
  { id: "a-004", name: "NVIDIA A100-01", type: "gpu", status: "active", age: 0.8, eol: "2029-05", warranty: "2028-11", location: "DC-1 Rack A4" },
  { id: "a-005", name: "Supermicro-01", type: "server", status: "maintenance", age: 4.2, eol: "2026-03", warranty: "expired", location: "DC-2 Rack D1" },
  { id: "a-006", name: "Juniper EX4600", type: "network", status: "decommissioned", age: 6.1, eol: "2024-08", warranty: "expired", location: "DC-1 Rack B3" },
];

export default function HardwareLifecyclePanel() {
  const activeCount = assets.filter(a => a.status === "active").length;
  const nearEol = assets.filter(a => {
    if (a.eol === "expired") return false;
    const [year, month] = a.eol.split("-").map(Number);
    const eolDate = new Date(year, month - 1);
    const sixMonths = new Date();
    sixMonths.setMonth(sixMonths.getMonth() + 6);
    return eolDate <= sixMonths;
  }).length;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Hardware Lifecycle Tracker</h1>
        <Badge variant="secondary" className="text-sm">{nearEol} Near EOL</Badge>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Total Assets</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">{assets.length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Active</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold text-green-500">{activeCount}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">In Maintenance</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold text-amber-500">{assets.filter(a => a.status === "maintenance").length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Decommissioned</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold text-red-500">{assets.filter(a => a.status === "decommissioned").length}</div></CardContent></Card>
      </div>

      <Card>
        <CardContent className="p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/50">
                <th className="text-left p-3">Asset</th>
                <th className="text-left p-3">Type</th>
                <th className="text-left p-3">Status</th>
                <th className="text-right p-3">Age (yrs)</th>
                <th className="text-left p-3">EOL</th>
                <th className="text-left p-3">Warranty</th>
                <th className="text-left p-3">Location</th>
              </tr>
            </thead>
            <tbody>
              {assets.map(a => (
                <tr key={a.id} className="border-b hover:bg-muted/50">
                  <td className="p-3 font-medium">{a.name}</td>
                  <td className="p-3"><Badge variant="outline">{a.type}</Badge></td>
                  <td className="p-3">
                    <Badge variant={
                      a.status === "active" ? "default" :
                      a.status === "maintenance" ? "secondary" : "destructive"
                    }>{a.status}</Badge>
                  </td>
                  <td className="p-3 text-right">{a.age}</td>
                  <td className="p-3">
                    <span className={a.eol === "expired" ? "text-red-500" : ""}>{a.eol}</span>
                  </td>
                  <td className="p-3">
                    <span className={a.warranty === "expired" ? "text-red-500" : "text-green-500"}>
                      {a.warranty}
                    </span>
                  </td>
                  <td className="p-3 text-muted-foreground font-mono">{a.location}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader><CardTitle className="text-lg">Asset Distribution</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {[
              { type: "Server", count: 18, pct: 36 },
              { type: "Switch", count: 12, pct: 24 },
              { type: "Storage", count: 8, pct: 16 },
              { type: "GPU", count: 6, pct: 12 },
              { type: "Network", count: 6, pct: 12 },
            ].map(t => (
              <div key={t.type} className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span>{t.type}</span>
                  <span className="text-muted-foreground">{t.count} units</span>
                </div>
                <Progress value={t.pct} className="h-2" />
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle className="text-lg">Upcoming EOL (Next 6 Months)</CardTitle></CardHeader>
          <CardContent>
            {assets.filter(a => a.status === "active" || a.status === "maintenance")
              .filter(a => {
                if (a.eol === "expired") return true;
                const [year, month] = a.eol.split("-").map(Number);
                const eolDate = new Date(year, month - 1);
                const sixMonths = new Date();
                sixMonths.setMonth(sixMonths.getMonth() + 6);
                return eolDate <= sixMonths;
              }).length > 0 ? (
              <ul className="space-y-2">
                {assets.filter(a => a.status === "active" || a.status === "maintenance")
                  .filter(a => {
                    if (a.eol === "expired") return true;
                    const [year, month] = a.eol.split("-").map(Number);
                    const eolDate = new Date(year, month - 1);
                    const sixMonths = new Date();
                    sixMonths.setMonth(sixMonths.getMonth() + 6);
                    return eolDate <= sixMonths;
                  })
                  .map(a => (
                    <li key={a.id} className="flex items-center justify-between p-2 bg-muted/30 rounded">
                      <span className="text-sm">{a.name}</span>
                      <Badge variant="destructive" className="text-xs">{a.eol}</Badge>
                    </li>
                  ))}
              </ul>
            ) : (
              <p className="text-sm text-muted-foreground">No assets near end of life.</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
