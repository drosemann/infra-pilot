import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";

const functions = [
  { id: "fn-001", name: "temperature-aggregator", runtime: "wasm", status: "active", invocations: 45230, lastError: null, memory: "8 MB", version: "1.2.0" },
  { id: "fn-002", name: "alert-threshold-check", runtime: "lua", status: "active", invocations: 18200, lastError: null, memory: "4 MB", version: "2.0.1" },
  { id: "fn-003", name: "data-normalizer", runtime: "javascript", status: "active", invocations: 89100, lastError: "timeout", memory: "16 MB", version: "1.1.0" },
  { id: "fn-004", name: "image-processor", runtime: "python", status: "degraded", invocations: 3200, lastError: "oom", memory: "128 MB", version: "0.9.0" },
  { id: "fn-005", name: "telemetry-forwarder", runtime: "wasm", status: "active", invocations: 124500, lastError: null, memory: "2 MB", version: "3.0.0" },
  { id: "fn-006", name: "ml-inference-preprocessor", runtime: "python", status: "inactive", invocations: 0, lastError: null, memory: "64 MB", version: "1.0.0" },
];

const runtimes = [
  { name: "WASM", count: 2, pct: 33 },
  { name: "Lua", count: 1, pct: 17 },
  { name: "JavaScript", count: 1, pct: 17 },
  { name: "Python", count: 2, pct: 33 },
];

export default function EdgeFunctionRuntimePanel() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Edge Function Runtime</h1>
        <Badge variant="secondary" className="text-sm">{functions.filter(f => f.status === "active").length} Active</Badge>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Total Functions</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">{functions.length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Invocations</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">280K</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Avg Memory</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">37 MB</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Error Rate</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold text-amber-500">0.8%</div></CardContent></Card>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card className="md:col-span-2">
          <CardHeader><CardTitle className="text-lg">Deployed Functions</CardTitle></CardHeader>
          <CardContent className="p-0">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/50">
                  <th className="text-left p-3">Function</th>
                  <th className="text-left p-3">Runtime</th>
                  <th className="text-left p-3">Status</th>
                  <th className="text-right p-3">Invocations</th>
                  <th className="text-right p-3">Memory</th>
                  <th className="text-left p-3">Version</th>
                </tr>
              </thead>
              <tbody>
                {functions.map(fn => (
                  <tr key={fn.id} className="border-b hover:bg-muted/50">
                    <td className="p-3 font-medium font-mono text-xs">{fn.name}</td>
                    <td className="p-3"><Badge variant="outline">{fn.runtime}</Badge></td>
                    <td className="p-3">
                      <Badge variant={
                        fn.status === "active" ? "default" :
                        fn.status === "degraded" ? "secondary" : "outline"
                      }>{fn.status}</Badge>
                    </td>
                    <td className="p-3 text-right">{(fn.invocations / 1000).toFixed(1)}K</td>
                    <td className="p-3 text-right font-mono">{fn.memory}</td>
                    <td className="p-3 font-mono">{fn.version}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle className="text-lg">Runtime Distribution</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {runtimes.map(r => (
              <div key={r.name} className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span>{r.name}</span>
                  <span className="text-muted-foreground">{r.count} functions</span>
                </div>
                <Progress value={r.pct} className="h-2" />
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
