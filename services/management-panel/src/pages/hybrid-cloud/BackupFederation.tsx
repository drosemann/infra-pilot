import { useEffect, useState } from 'react';
import { FormattedMessage } from 'react-intl';
import { apiClient } from '../../lib/api';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table';

interface Backup { id: string; name: string; workload_id: string; target: string; size_gb: number; state: string; }
interface RestoreJob { id: string; backup_id: string; target_provider: string; state: string; }

export const BackupFederation = () => {
  const [backups, setBackups] = useState<Backup[]>([]);
  const [restores, setRestores] = useState<RestoreJob[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    try { const [b, r] = await Promise.all([apiClient.listFederatedBackups(), apiClient.listRestoreJobs()]);
      setBackups(b || []); setRestores(r || []);
    } catch (e) { toast.error('Failed to load backup data');
    } finally { setLoading(false); }
  };

  const executeBackup = async (backupId: string) => {
    try { await apiClient.executeFederatedBackup(backupId); toast.success('Backup completed'); loadData();
    } catch (e) { toast.error('Backup failed'); }
  };

  const restoreBackup = async (backupId: string, targetProvider?: string) => {
    try { await apiClient.restoreFederatedBackup(backupId, targetProvider); toast.success('Restore started'); loadData();
    } catch (e) { toast.error('Restore failed'); }
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>;

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex justify-between items-center">
        <div><h1 className="text-3xl font-bold"><FormattedMessage id="backupFederation.title" defaultMessage="Backup Federation" /></h1>
          <p className="text-muted-foreground mt-1"><FormattedMessage id="backupFederation.description" defaultMessage="Cross-cloud backup and restore management" /></p></div>
      </div>
      <Tabs defaultValue="backups">
        <TabsList><TabsTrigger value="backups">Backups</TabsTrigger><TabsTrigger value="restores">Restores</TabsTrigger><TabsTrigger value="vaults">Vaults</TabsTrigger></TabsList>
        <TabsContent value="backups" className="space-y-4">
          <div className="flex justify-between"><h2 className="text-xl font-semibold">Backups</h2></div>
          <Card><CardContent className="p-0">
            <Table><TableHeader><TableRow>
              <TableHead>Name</TableHead><TableHead>Workload</TableHead><TableHead>Target</TableHead><TableHead>Size</TableHead><TableHead>Status</TableHead><TableHead>Actions</TableHead>
            </TableRow></TableHeader>
            <TableBody>{backups.map((b) => (
              <TableRow key={b.id}><TableCell className="font-medium">{b.name}</TableCell>
                <TableCell className="font-mono text-xs">{b.workload_id?.substring(0, 12)}..</TableCell>
                <TableCell><Badge variant="outline">{b.target}</Badge></TableCell>
                <TableCell>{b.size_gb}GB</TableCell>
                <TableCell><Badge variant={b.state === 'completed' ? 'default' : 'secondary'}>{b.state}</Badge></TableCell>
                <TableCell className="flex gap-1"><Button size="sm" onClick={() => executeBackup(b.id)}>Run</Button><Button size="sm" variant="outline" onClick={() => restoreBackup(b.id)}>Restore</Button></TableCell>
              </TableRow>
            ))}</TableBody></Table>
          </CardContent></Card>
        </TabsContent>
        <TabsContent value="restores">
          <Card><CardContent className="p-0">
            <Table><TableHeader><TableRow>
              <TableHead>Job ID</TableHead><TableHead>Backup</TableHead><TableHead>Target</TableHead><TableHead>Status</TableHead>
            </TableRow></TableHeader>
            <TableBody>{restores.map((r) => (
              <TableRow key={r.id}><TableCell className="font-mono text-xs">{r.id}</TableCell>
                <TableCell className="font-mono text-xs">{r.backup_id?.substring(0, 12)}..</TableCell>
                <TableCell>{r.target_provider}</TableCell>
                <TableCell><Badge variant={r.state === 'completed' ? 'default' : 'secondary'}>{r.state}</Badge></TableCell>
              </TableRow>
            ))}</TableBody></Table>
          </CardContent></Card>
        </TabsContent>
        <TabsContent value="vaults">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card><CardHeader><CardTitle>AWS S3</CardTitle></CardHeader><CardContent><p>Region: us-east-1<br/>Geo: Cross-Cloud</p></CardContent></Card>
            <Card><CardHeader><CardTitle>Azure Blob</CardTitle></CardHeader><CardContent><p>Region: eastus<br/>Geo: Same-Region</p></CardContent></Card>
            <Card><CardHeader><CardTitle>GCP Storage</CardTitle></CardHeader><CardContent><p>Region: us-central1<br/>Geo: Cross-Region</p></CardContent></Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};
  const [showBackupDialog, setShowBackupDialog] = useState(false);
  const [backupWorkloadId, setBackupWorkloadId] = useState('');
  const [backupProvider, setBackupProvider] = useState('aws');
  const [backupSize, setBackupSize] = useState(10);
  const [schedules, setSchedules] = useState<any[]>([]);
  const [showScheduleDialog, setShowScheduleDialog] = useState(false);
  const [scheduleCron, setScheduleCron] = useState('0 0 * * *');
  const [scheduleRetention, setScheduleRetention] = useState(30);

  useEffect(() => {
    loadSchedules();
  }, []);

  const loadSchedules = async () => {
    try { const data = await apiClient.getBackupSchedules(); setSchedules(data || []); } catch { /* ignore */ }
  };

  const verifyIntegrity = async (backupId: string) => {
    try { const result = await apiClient.verifyBackupIntegrity(backupId); toast.success(result.integrity_ok ? 'Integrity OK' : 'Integrity FAILED'); } catch { toast.error('Verification failed'); }
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="grid grid-cols-4 gap-4">
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Backups</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{backups.length}</p></CardContent></Card>
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Restores</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{restores.length}</p></CardContent></Card>
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Schedules</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{schedules.length}</p></CardContent></Card>
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Total Size</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{backups.reduce((s, b) => s + (b.size_gb || 0), 0).toFixed(1)} GB</p></CardContent></Card>
      </div>

      <div className="flex gap-2">
        <Dialog open={showBackupDialog} onOpenChange={setShowBackupDialog}>
          <DialogTrigger asChild><Button>Create Backup</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>Create Backup</DialogTitle></DialogHeader>
            <div className="space-y-2">
              <Input placeholder="Workload ID" value={backupWorkloadId} onChange={e => setBackupWorkloadId(e.target.value)} />
              <Input placeholder="Provider" value={backupProvider} onChange={e => setBackupProvider(e.target.value)} />
              <Input type="number" placeholder="Size (GB)" value={backupSize} onChange={e => setBackupSize(parseFloat(e.target.value) || 10)} />
            </div>
            <DialogFooter><Button onClick={() => { apiClient.createBackup(backupWorkloadId, backupProvider, backupSize); toast.success('Backup created'); setShowBackupDialog(false); }}>Create</Button></DialogFooter>
          </DialogContent>
        </Dialog>
        <Dialog open={showScheduleDialog} onOpenChange={setShowScheduleDialog}>
          <DialogTrigger asChild><Button variant="outline">Add Schedule</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>Add Backup Schedule</DialogTitle></DialogHeader>
            <div className="space-y-2">
              <Input placeholder="Cron expression" value={scheduleCron} onChange={e => setScheduleCron(e.target.value)} />
              <Input type="number" placeholder="Retention (days)" value={scheduleRetention} onChange={e => setScheduleRetention(parseInt(e.target.value) || 30)} />
            </div>
            <DialogFooter><Button onClick={() => { apiClient.createBackupSchedule(backupWorkloadId || 'default', scheduleCron, scheduleRetention); toast.success('Schedule added'); setShowScheduleDialog(false); }}>Add</Button></DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardHeader><CardTitle>Backup Schedules</CardTitle></CardHeader>
        <CardContent>
          <Table>
            <TableHeader><TableRow><TableHead>ID</TableHead><TableHead>Cron</TableHead><TableHead>Retention</TableHead><TableHead>Status</TableHead></TableRow></TableHeader>
            <TableBody>{schedules.map((s, i) => (
              <TableRow key={i}>
                <TableCell className="font-mono text-xs">{s.id}</TableCell>
                <TableCell className="font-mono">{s.cron}</TableCell>
                <TableCell>{s.retention_days}d</TableCell>
                <TableCell><Badge variant={s.active ? 'default' : 'secondary'}>{s.active ? 'Active' : 'Inactive'}</Badge></TableCell>
              </TableRow>
            ))}</TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};

  const [showIntegrityDialog, setShowIntegrityDialog] = useState(false);
  const [integrityBackupId, setIntegrityBackupId] = useState('');
  const [integrityResult, setIntegrityResult] = useState<any>(null);
  const [showRestoreDialog, setShowRestoreDialog] = useState(false);
  const [restoreBackupId, setRestoreBackupId] = useState('');
  const [restoreTarget, setRestoreTarget] = useState('');
  const [vaults] = useState([
    { name: 'AWS S3', region: 'us-east-1', geo: 'Cross-Cloud', provider: 'aws' },
    { name: 'Azure Blob', region: 'eastus', geo: 'Same-Region', provider: 'azure' },
    { name: 'GCP Storage', region: 'us-central1', geo: 'Cross-Region', provider: 'gcp' },
  ]);

  const runIntegrityCheck = async () => {
    try {
      const result = await apiClient.verifyBackupIntegrity(integrityBackupId);
      setIntegrityResult(result);
      toast.success(result.integrity_ok ? 'Integrity OK' : 'Integrity FAILED');
      setShowIntegrityDialog(false);
    } catch { toast.error('Verification failed'); }
  };

  const executeRestore = async () => {
    try {
      await apiClient.restoreFederatedBackup(restoreBackupId, restoreTarget || undefined);
      toast.success('Restore started');
      setShowRestoreDialog(false);
      loadData();
    } catch { toast.error('Restore failed'); }
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="grid grid-cols-4 gap-4">
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Vaults</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{vaults.length}</p></CardContent></Card>
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Schedules</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{schedules.length}</p></CardContent></Card>
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Total Backups</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{backups.length}</p></CardContent></Card>
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Total Size</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{backups.reduce((s, b) => s + (b.size_gb || 0), 0).toFixed(1)} GB</p></CardContent></Card>
      </div>

      <div className="flex gap-2">
        <Dialog open={showIntegrityDialog} onOpenChange={setShowIntegrityDialog}>
          <DialogTrigger asChild><Button variant="outline">Verify Integrity</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>Verify Backup Integrity</DialogTitle></DialogHeader>
            <Input placeholder="Backup ID" value={integrityBackupId} onChange={e => setIntegrityBackupId(e.target.value)} />
            <DialogFooter><Button onClick={runIntegrityCheck}>Verify</Button></DialogFooter>
          </DialogContent>
        </Dialog>
        <Dialog open={showRestoreDialog} onOpenChange={setShowRestoreDialog}>
          <DialogTrigger asChild><Button variant="secondary">Restore Backup</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>Restore Backup</DialogTitle></DialogHeader>
            <div className="space-y-2">
              <Input placeholder="Backup ID" value={restoreBackupId} onChange={e => setRestoreBackupId(e.target.value)} />
              <Input placeholder="Target provider (optional)" value={restoreTarget} onChange={e => setRestoreTarget(e.target.value)} />
            </div>
            <DialogFooter><Button onClick={executeRestore}>Restore</Button></DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {integrityResult && (
        <Card>
          <CardHeader><CardTitle>Last Integrity Check</CardTitle></CardHeader>
          <CardContent className="flex gap-4">
            <div><Label>Status</Label><p className={integrityResult.integrity_ok ? 'text-green-600 font-bold' : 'text-red-600 font-bold'}>{integrityResult.integrity_ok ? 'PASSED' : 'FAILED'}</p></div>
            <div><Label>Verified At</Label><p className="text-sm">{new Date(integrityResult.verified_at).toLocaleString()}</p></div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader><CardTitle>Backup Vaults</CardTitle></CardHeader>
        <CardContent>
          <Table>
            <TableHeader><TableRow><TableHead>Name</TableHead><TableHead>Provider</TableHead><TableHead>Region</TableHead><TableHead>Geo</TableHead></TableRow></TableHeader>
            <TableBody>{vaults.map((v, i) => (
              <TableRow key={i}>
                <TableCell className="font-medium">{v.name}</TableCell>
                <TableCell><Badge variant="outline">{v.provider}</Badge></TableCell>
                <TableCell>{v.region}</TableCell>
                <TableCell>{v.geo}</TableCell>
              </TableRow>
            ))}</TableBody>
          </Table>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Backup Schedules</CardTitle></CardHeader>
        <CardContent>
          <Table>
            <TableHeader><TableRow><TableHead>ID</TableHead><TableHead>Cron</TableHead><TableHead>Retention</TableHead><TableHead>Active</TableHead></TableRow></TableHeader>
            <TableBody>{schedules.map((s, i) => (
              <TableRow key={i}>
                <TableCell className="font-mono text-xs">{s.id}</TableCell>
                <TableCell className="font-mono">{s.cron}</TableCell>
                <TableCell>{s.retention_days}d</TableCell>
                <TableCell><Badge variant={s.active ? 'default' : 'secondary'}>{s.active ? 'Active' : 'Inactive'}</Badge></TableCell>
              </TableRow>
            ))}</TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};

function BackupFormDialog({ open, onOpenChange, onSubmit }: { open: boolean; onOpenChange: (v: boolean) => void; onSubmit: (data: any) => void }) {
  const [name, setName] = useState(''); const [workloadId, setWorkloadId] = useState(''); const [target, setTarget] = useState('aws_s3'); const [retention, setRetention] = useState('30');
  return (
    <Dialog open={open} onOpenChange={onOpenChange}><DialogContent><DialogHeader><DialogTitle>Create Backup</DialogTitle></DialogHeader>
      <div className="space-y-4">
        <div><Label>Name</Label><Input value={name} onChange={e => setName(e.target.value)} /></div>
        <div><Label>Workload ID</Label><Input value={workloadId} onChange={e => setWorkloadId(e.target.value)} /></div>
        <div><Label>Target</Label><Select value={target} onValueChange={setTarget}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{['aws_s3','azure_blob','gcp_storage','local'].map(t => <SelectItem key={t} value={t}>{t}</SelectItem>)}</SelectContent></Select></div>
        <div><Label>Retention (days)</Label><Input type="number" value={retention} onChange={e => setRetention(e.target.value)} /></div>
      </div>
      <DialogFooter><Button onClick={() => { onSubmit({ name, workload_id: workloadId, target, retention_days: parseInt(retention) }); onOpenChange(false); }}>Create</Button></DialogFooter>
    </DialogContent></Dialog>
  );
}

function BackupStateBadge({ state }: { state: string }) {
  const map: Record<string, string> = { pending: 'secondary', running: 'default', completed: 'default', failed: 'destructive', expired: 'outline' };
  return <Badge variant={(map[state] || 'outline') as any}>{state}</Badge>;
}

function StorageUsageChart({ backups }: { backups: any[] }) {
  const byTarget: Record<string, number> = {};
  backups.forEach((b: any) => { const t = b.target || 'unknown'; byTarget[t] = (byTarget[t] || 0) + (b.size_gb || 0); });
  const total = Object.values(byTarget).reduce((s, v) => s + v, 0);
  const sorted = Object.entries(byTarget).sort((a, b) => b[1] - a[1]);
  return (
    <Card><CardHeader><CardTitle>Storage by Target</CardTitle></CardHeader>
    <CardContent><div className="space-y-2">{sorted.map(([t, gb]) => (
      <div key={t} className="flex items-center gap-2"><span className="text-sm w-24">{t}</span><div className="h-4 bg-muted rounded flex-1"><div className="h-full bg-blue-500 rounded" style={{ width: `${(gb / total) * 100}%` }} /></div><span className="text-sm w-16 text-right">{gb.toFixed(1)} GB</span></div>
    ))}</div></CardContent></Card>
  );
}

function RestoreJobCard({ job, onExecute }: { job: any; onExecute: (id: string) => void }) {
  return (
    <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Restore: {job.id?.substring(0, 12)}</CardTitle></CardHeader>
    <CardContent><div className="text-xs space-y-1"><p>Backup: {job.backup_id?.substring(0, 12)}</p><p>Target: {job.target_provider}/{job.target_region}</p><p>State: <BackupStateBadge state={job.state} /></p></div>
    {job.state === 'pending' && <Button size="sm" className="mt-2" onClick={() => onExecute(job.id)}>Execute</Button>}</CardContent></Card>
  );
}

function ComplianceSummary({ backups }: { backups: any[] }) {
  const total = backups.length;
  const encrypted = backups.filter((b: any) => b.encrypted).length;
  const completed = backups.filter((b: any) => b.state === 'completed').length;
  return (
    <div className="grid grid-cols-4 gap-4 mb-6">
      <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Total Backups</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{total}</p></CardContent></Card>
      <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Encrypted</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{encrypted}</p></CardContent></Card>
      <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Completed</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{completed}</p></CardContent></Card>
      <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Success Rate</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{total > 0 ? `${Math.round((completed / total) * 100)}%` : 'N/A'}</p></CardContent></Card>
    </div>
  );
}

export default BackupFederation;
