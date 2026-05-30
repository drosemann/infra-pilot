import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const policies = [
  { name: "Night Shutdown", scope: "global", action: "hibernate", start: "22:00", end: "06:00", days: ["Mon-Fri"], enabled: true, savings: "120 kWh/day" },
  { name: "Weekend Standby", scope: "device", action: "shutdown", start: "18:00 Fri", end: "08:00 Mon", days: ["Sat", "Sun"], enabled: true, savings: "340 kWh/weekend" },
  { name: "Idle Timeout", scope: "group", action: "sleep", start: "15m idle", end: "activity", days: ["All"], enabled: true, savings: "45 kWh/day" },
  { name: "Holiday Shutdown", scope: "global", action: "shutdown", start: "holiday", end: "next business", days: ["Holidays"], enabled: false, savings: "200 kWh/day" },
];

const effectiveness = [
  { policy: "Night Shutdown", compliance: 96, saved: "3,600 kWh", cost: "$432" },
  { policy: "Weekend Standby", compliance: 88, saved: "1,360 kWh", cost: "$163" },
  { policy: "Idle Timeout", compliance: 72, saved: "1,350 kWh", cost: "$162" },
];

export default function AutoShutdownPoliciesPanel() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Auto Shutdown Policies</h1>
        <Badge variant="secondary" className="text-sm">Energy Saving</Badge>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Total Policies</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">{policies.length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Enabled</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold text-green-500">{policies.filter(p => p.enabled).length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Daily Savings</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">165 kWh</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Monthly Savings</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">$757</div></CardContent></Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader><CardTitle className="text-lg">Active Policies</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {policies.map(p => (
              <div key={p.name} className="flex items-center justify-between p-3 border rounded-lg">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-sm">{p.name}</span>
                    <Badge variant="outline" className="text-xs">{p.scope}</Badge>
                  </div>
                  <div className="text-xs text-muted-foreground mt-1">
                    {p.action} · {p.start} → {p.end} · {p.days.join(", ")}
                  </div>
                  <div className="text-xs text-green-500 mt-1">{p.savings}</div>
                </div>
                <Badge variant={p.enabled ? "default" : "secondary"}>{p.enabled ? "Active" : "Paused"}</Badge>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle className="text-lg">Policy Effectiveness</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            {effectiveness.map(e => (
              <div key={e.policy} className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="font-medium">{e.policy}</span>
                  <span className="text-muted-foreground">{e.compliance}% compliance</span>
                </div>
                <div className="w-full bg-muted rounded-full h-2">
                  <div className="bg-green-500 h-2 rounded-full" style={{ width: `${e.compliance}%` }} />
                </div>
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>Saved: {e.saved}</span>
                  <span>Cost saved: {e.cost}</span>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
