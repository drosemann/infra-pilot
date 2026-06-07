import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";

const candidates = [
  { resource: "worker-node-3", type: "compute", usage: 0.03, status: "identified", savings: "$2.40/hr" },
  { resource: "gpu-cluster-2", type: "gpu", usage: 0.08, status: "pending", savings: "$8.50/hr" },
  { resource: "cache-pool-1", type: "memory", usage: 0.05, status: "identified", savings: "$1.20/hr" },
  { resource: "backup-vol-5", type: "storage", usage: 0.02, status: "reclaimed", savings: "$0.80/hr" },
  { resource: "dev-sandbox-7", type: "compute", usage: 0.01, status: "identified", savings: "$1.60/hr" },
];

export default function IdleResourceReclamationPanel() {
  const totalSavings = candidates.reduce((sum, c) => {
    const hourly = parseFloat(c.savings.replace(/[^0-9.]+/g, ""));
    return sum + hourly;
  }, 0);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Idle Resource Reclamation</h1>
        <Badge variant="secondary" className="text-sm">Auto-Recover</Badge>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Idle Candidates</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">{candidates.length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Reclaimed</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold text-green-500">{candidates.filter(c => c.status === "reclaimed").length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Hourly Savings</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">${totalSavings.toFixed(2)}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Monthly Projection</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">${(totalSavings * 730).toFixed(0)}</div></CardContent></Card>
      </div>

      <Card>
        <CardContent className="p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/50">
                <th className="text-left p-3">Resource</th>
                <th className="text-left p-3">Type</th>
                <th className="text-right p-3">Usage %</th>
                <th className="text-left p-3">Status</th>
                <th className="text-right p-3">Savings</th>
                <th className="text-left p-3">Action</th>
              </tr>
            </thead>
            <tbody>
              {candidates.map(c => (
                <tr key={c.resource} className="border-b hover:bg-muted/50">
                  <td className="p-3 font-medium">{c.resource}</td>
                  <td className="p-3"><Badge variant="outline">{c.type}</Badge></td>
                  <td className="p-3 text-right">{c.usage}%</td>
                  <td className="p-3">
                    <Badge variant={
                      c.status === "reclaimed" ? "default" :
                      c.status === "pending" ? "secondary" : "outline"
                    }>{c.status}</Badge>
                  </td>
                  <td className="p-3 text-right text-green-500">{c.savings}</td>
                  <td className="p-3">
                    <Badge variant="default" className="cursor-pointer hover:bg-primary/80">Reclaim</Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader><CardTitle className="text-lg">Resource Type Breakdown</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {[
              { type: "Compute", count: 12, pct: 40 },
              { type: "Memory", count: 8, pct: 27 },
              { type: "Storage", count: 6, pct: 20 },
              { type: "GPU", count: 3, pct: 10 },
              { type: "Network", count: 1, pct: 3 },
            ].map(r => (
              <div key={r.type} className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span>{r.type}</span>
                  <span className="text-muted-foreground">{r.count} resources</span>
                </div>
                <Progress value={r.pct} className="h-2" />
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle className="text-lg">Active Policies</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {[
              { name: "Aggressive", threshold: "5%", cooldown: "5m", recovery: "on-demand" },
              { name: "Balanced", threshold: "10%", cooldown: "15m", recovery: "scheduled" },
              { name: "Conservative", threshold: "20%", cooldown: "30m", recovery: "manual" },
            ].map(p => (
              <div key={p.name} className="flex items-center justify-between p-3 border rounded-lg">
                <div>
                  <div className="font-medium text-sm">{p.name}</div>
                  <div className="text-xs text-muted-foreground">
                    Threshold: {p.threshold} · Cooldown: {p.cooldown} · Recovery: {p.recovery}
                  </div>
                </div>
                <Badge variant={p.name === "Balanced" ? "default" : "secondary"}>
                  {p.name === "Balanced" ? "Active" : "Inactive"}
                </Badge>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
