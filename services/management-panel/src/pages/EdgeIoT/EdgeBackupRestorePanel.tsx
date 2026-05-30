import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

const backupJobs = [
  { id: "b-001", device: "dev-001", type: "full", size: "2.4 GB", status: "completed", duration: "4m 12s", target: "s3://backup/" },
  { id: "b-002", device: "dev-002", type: "incremental", size: "450 MB", status: "completed", duration: "1m 08s", target: "s3://backup/" },
  { id: "b-003", device: "dev-003", type: "full", size: "1.8 GB", status: "running", duration: "2m 30s", target: "s3://backup/" },
  { id: "b-004", device: "dev-001", type: "incremental", size: "120 MB", status: "completed", duration: "45s", target: "s3://backup/" },
  { id: "b-005", device: "dev-004", type: "full", size: "3.1 GB", status: "failed", duration: "11m 00s", target: "s3://backup/" },
];

const schedules = [
  { name: "Daily Full Backup", cron: "0 2 * * *", type: "full", retention: "30 days", enabled: true },
  { name: "Hourly Incremental", cron: "0 * * * *", type: "incremental", retention: "7 days", enabled: true },
  { name: "Weekly Archive", cron: "0 3 * * 0", type: "full", retention: "90 days", enabled: false },
];

export default function EdgeBackupRestorePanel() {
  const completed = backupJobs.filter(j => j.status === "completed").length;
  const failed = backupJobs.filter(j => j.status === "failed").length;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Edge Backup & Restore</h1>
        <Badge variant="outline" className="text-sm">Last: 2m ago</Badge>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Total Backups</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">{backupJobs.length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Completed</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold text-green-500">{completed}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Failed</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold text-red-500">{failed}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Active Schedules</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">{schedules.filter(s => s.enabled).length}</div></CardContent></Card>
      </div>

      <Tabs defaultValue="jobs">
        <TabsList>
          <TabsTrigger value="jobs">Backup Jobs</TabsTrigger>
          <TabsTrigger value="schedules">Schedules</TabsTrigger>
          <TabsTrigger value="restore">Restore Points</TabsTrigger>
        </TabsList>

        <TabsContent value="jobs">
          <Card>
            <CardContent className="p-0">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-muted/50">
                    <th className="text-left p-3">Job ID</th>
                    <th className="text-left p-3">Device</th>
                    <th className="text-left p-3">Type</th>
                    <th className="text-right p-3">Size</th>
                    <th className="text-left p-3">Status</th>
                    <th className="text-right p-3">Duration</th>
                  </tr>
                </thead>
                <tbody>
                  {backupJobs.map(job => (
                    <tr key={job.id} className="border-b hover:bg-muted/50">
                      <td className="p-3 font-mono text-xs">{job.id}</td>
                      <td className="p-3">{job.device}</td>
                      <td className="p-3"><Badge variant="outline">{job.type}</Badge></td>
                      <td className="p-3 text-right">{job.size}</td>
                      <td className="p-3">
                        <Badge variant={
                          job.status === "completed" ? "default" :
                          job.status === "running" ? "secondary" : "destructive"
                        }>{job.status}</Badge>
                      </td>
                      <td className="p-3 text-right font-mono">{job.duration}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="schedules">
          <div className="space-y-3">
            {schedules.map(s => (
              <Card key={s.name}>
                <CardContent className="flex items-center justify-between p-4">
                  <div>
                    <div className="font-medium">{s.name}</div>
                    <div className="text-sm text-muted-foreground font-mono">{s.cron}</div>
                    <div className="text-xs text-muted-foreground">{s.type} · {s.retention} retention</div>
                  </div>
                  <Badge variant={s.enabled ? "default" : "secondary"}>{s.enabled ? "Enabled" : "Disabled"}</Badge>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="restore">
          <Card className="p-8 text-center text-muted-foreground">
            <p>Available restore points will appear here.</p>
            <p className="text-sm">Create a backup first to generate restore points.</p>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
