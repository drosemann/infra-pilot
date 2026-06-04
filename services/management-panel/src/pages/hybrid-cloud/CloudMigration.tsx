import { useEffect, useState } from 'react';
import { FormattedMessage } from 'react-intl';
import { apiClient } from '../../lib/api';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';

interface Workload { id: string; name: string; hostname: string; os_type: string; vcpu: number; memory_gb: number; state: string; }
interface Wave { id: string; name: string; workload_ids: string[]; target_provider: string; state: string; }

export const CloudMigration = () => {
  const [workloads, setWorkloads] = useState<Workload[]>([]);
  const [waves, setWaves] = useState<Wave[]>([]);
  const [loading, setLoading] = useState(true);
  const [showDiscover, setShowDiscover] = useState(false);
  const [discName, setDiscName] = useState('');
  const [discHost, setDiscHost] = useState('');
  const [discOS, setDiscOS] = useState('linux');
  const [discCPU, setDiscCPU] = useState(2);
  const [discMem, setDiscMem] = useState(4);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    try { const [wl, wv] = await Promise.all([apiClient.listMigrationWorkloads(), apiClient.listMigrationWaves()]);
      setWorkloads(wl || []); setWaves(wv || []);
    } catch (e) { toast.error('Failed to load migration data');
    } finally { setLoading(false); }
  };

  const discoverWorkload = async () => {
    try { await apiClient.discoverWorkload({ name: discName, hostname: discHost, os_type: discOS, vcpu: discCPU, memory_gb: discMem });
      toast.success('Workload discovered'); setShowDiscover(false); loadData();
    } catch (e) { toast.error('Failed to discover workload'); }
  };

  const executeWave = async (waveId: string) => {
    try { await apiClient.executeMigrationWave(waveId); toast.success('Wave executed'); loadData();
    } catch (e) { toast.error('Failed to execute wave'); }
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>;

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex justify-between items-center">
        <div><h1 className="text-3xl font-bold"><FormattedMessage id="cloudMigration.title" defaultMessage="Cloud Migration Toolkit" /></h1>
          <p className="text-muted-foreground mt-1"><FormattedMessage id="cloudMigration.description" defaultMessage="Agentless discovery, dependency mapping, wave planning" /></p></div>
      </div>
      <Tabs defaultValue="workloads">
        <TabsList><TabsTrigger value="workloads">Workloads</TabsTrigger><TabsTrigger value="waves">Migration Waves</TabsTrigger></TabsList>
        <TabsContent value="workloads" className="space-y-4">
          <div className="flex justify-between"><h2 className="text-xl font-semibold">Discovered Workloads</h2>
            <Button onClick={() => setShowDiscover(true)}>Discover Workload</Button></div>
          <Card><CardContent className="p-0">
            <Table><TableHeader><TableRow>
              <TableHead>Name</TableHead><TableHead>Hostname</TableHead><TableHead>OS</TableHead><TableHead>vCPU</TableHead><TableHead>Memory</TableHead><TableHead>Status</TableHead>
            </TableRow></TableHeader>
            <TableBody>{workloads.map((w) => (
              <TableRow key={w.id}><TableCell className="font-medium">{w.name}</TableCell>
                <TableCell className="font-mono text-xs">{w.hostname}</TableCell>
                <TableCell>{w.os_type}</TableCell><TableCell>{w.vcpu}</TableCell><TableCell>{w.memory_gb}GB</TableCell>
                <TableCell><Badge variant={w.state === 'completed' ? 'default' : 'secondary'}>{w.state}</Badge></TableCell>
              </TableRow>
            ))}</TableBody></Table>
          </CardContent></Card>
          {showDiscover && (<div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"><Card className="w-96">
            <CardHeader><CardTitle>Discover Workload</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div><Label>Name</Label><Input value={discName} onChange={(e) => setDiscName(e.target.value)} /></div>
              <div><Label>Hostname</Label><Input value={discHost} onChange={(e) => setDiscHost(e.target.value)} /></div>
              <div><Label>OS Type</Label><Input value={discOS} onChange={(e) => setDiscOS(e.target.value)} /></div>
              <div><Label>vCPU</Label><Input type="number" value={discCPU} onChange={(e) => setDiscCPU(parseInt(e.target.value) || 2)} /></div>
              <div><Label>Memory (GB)</Label><Input type="number" value={discMem} onChange={(e) => setDiscMem(parseInt(e.target.value) || 4)} /></div>
              <div className="flex gap-2"><Button onClick={discoverWorkload}>Discover</Button><Button variant="outline" onClick={() => setShowDiscover(false)}>Cancel</Button></div>
            </CardContent></Card></div>)}
        </TabsContent>
        <TabsContent value="waves" className="space-y-4">
          <Card><CardContent className="p-0">
            <Table><TableHeader><TableRow>
              <TableHead>Name</TableHead><TableHead>Target Provider</TableHead><TableHead>Workloads</TableHead><TableHead>Status</TableHead><TableHead>Actions</TableHead>
            </TableRow></TableHeader>
            <TableBody>{waves.map((w) => (
              <TableRow key={w.id}><TableCell className="font-medium">{w.name}</TableCell>
                <TableCell><Badge variant="outline">{w.target_provider}</Badge></TableCell>
                <TableCell>{w.workload_ids?.length || 0}</TableCell>
                <TableCell><Badge variant={w.state === 'completed' ? 'default' : 'secondary'}>{w.state}</Badge></TableCell>
                <TableCell><Button size="sm" onClick={() => executeWave(w.id)} disabled={w.state === 'completed' || w.state === 'migrating'}>Execute</Button></TableCell>
              </TableRow>
            ))}</TableBody></Table>
          </CardContent></Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};
  const [showWaveDialog, setShowWaveDialog] = useState(false);
  const [waveName, setWaveName] = useState('');
  const [workloadIds, setWorkloadIds] = useState('');
  const [targetProvider, setTargetProvider] = useState('aws');
  const [migrationLog, setMigrationLog] = useState<any[]>([]);
  const [dependencies, setDependencies] = useState<any>(null);
  const [showAssessDialog, setShowAssessDialog] = useState(false);
  const [assessWorkloadId, setAssessWorkloadId] = useState('');

  useEffect(() => {
    loadDependencies();
  }, []);

  const loadDependencies = async () => {
    try {
      const data = await apiClient.getMigrationDependencyMap();
      setDependencies(data);
    } catch { /* ignore */ }
  };

  const assessWorkload = async () => {
    try {
      const result = await apiClient.assessWorkload(assessWorkloadId);
      toast.success(`Assessment: ${result.compatibility ? 'Compatible' : 'Incompatible'}`);
      setShowAssessDialog(false);
    } catch { toast.error('Assessment failed'); }
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="grid grid-cols-4 gap-4">
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Workloads</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{workloads.length}</p></CardContent></Card>
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Waves</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{waves.length}</p></CardContent></Card>
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Completed</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{waves.filter(w => w.state === 'completed').length}</p></CardContent></Card>
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Target</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{targetProvider.toUpperCase()}</p></CardContent></Card>
      </div>

      <div className="flex gap-2">
        <Dialog open={showWaveDialog} onOpenChange={setShowWaveDialog}>
          <DialogTrigger asChild><Button>Create Wave</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>Create Migration Wave</DialogTitle></DialogHeader>
            <div className="space-y-2">
              <Input placeholder="Wave name" value={waveName} onChange={e => setWaveName(e.target.value)} />
              <Input placeholder="Workload IDs (comma-separated)" value={workloadIds} onChange={e => setWorkloadIds(e.target.value)} />
              <Input placeholder="Target provider" value={targetProvider} onChange={e => setTargetProvider(e.target.value)} />
            </div>
            <DialogFooter><Button onClick={() => { apiClient.createWave(waveName, workloadIds.split(','), targetProvider); setShowWaveDialog(false); }}>Create</Button></DialogFooter>
          </DialogContent>
        </Dialog>
        <Dialog open={showAssessDialog} onOpenChange={setShowAssessDialog}>
          <DialogTrigger asChild><Button variant="outline">Assess Workload</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>Assess Workload</DialogTitle></DialogHeader>
            <Input placeholder="Workload ID" value={assessWorkloadId} onChange={e => setAssessWorkloadId(e.target.value)} />
            <DialogFooter><Button onClick={assessWorkload}>Assess</Button></DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {dependencies && (
        <Card>
          <CardHeader><CardTitle>Dependency Map</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-2">
              {Object.entries(dependencies.workloads || {}).slice(0, 5).map(([id, wl]: [string, any]) => (
                <div key={id} className="flex items-center justify-between p-2 border rounded">
                  <span className="font-medium">{wl.name}</span>
                  <span className="text-sm text-muted-foreground">{wl.dependencies?.length || 0} dependencies</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

  const [showCutoverDialog, setShowCutoverDialog] = useState(false);
  const [cutoverWaveId, setCutoverWaveId] = useState('');
  const [showReplicationDialog, setShowReplicationDialog] = useState(false);
  const [repWorkloadId, setRepWorkloadId] = useState('');
  const [replicationStatus, setReplicationStatus] = useState<any>(null);
  const [showRollbackDialog, setShowRollbackDialog] = useState(false);
  const [rollbackWaveId, setRollbackWaveId] = useState('');

  const initiateCutover = async () => {
    try {
      await apiClient.cutoverMigrationWave(cutoverWaveId);
      toast.success('Cutover initiated');
      setShowCutoverDialog(false);
      loadData();
    } catch { toast.error('Cutover failed'); }
  };

  const checkReplication = async () => {
    try {
      const result = await apiClient.checkReplicationStatus(repWorkloadId);
      setReplicationStatus(result);
      toast.success(`Replication: ${result.progress}%`);
    } catch { toast.error('Failed to check replication'); }
  };

  const rollbackWave = async () => {
    try {
      await apiClient.rollbackMigrationWave(rollbackWaveId);
      toast.success('Wave rolled back');
      setShowRollbackDialog(false);
      loadData();
    } catch { toast.error('Rollback failed'); }
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="grid grid-cols-4 gap-4">
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Workloads</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{workloads.length}</p></CardContent></Card>
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Waves</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{waves.length}</p></CardContent></Card>
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Completed</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{waves.filter(w => w.state === 'completed').length}</p></CardContent></Card>
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Dependencies</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{dependencies ? Object.keys(dependencies.workloads || {}).length : 0}</p></CardContent></Card>
      </div>

      <div className="flex gap-2 flex-wrap">
        <Dialog open={showCutoverDialog} onOpenChange={setShowCutoverDialog}>
          <DialogTrigger asChild><Button>Initiate Cutover</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>Initiate Cutover</DialogTitle></DialogHeader>
            <Input placeholder="Wave ID" value={cutoverWaveId} onChange={e => setCutoverWaveId(e.target.value)} />
            <DialogFooter><Button onClick={initiateCutover}>Cutover</Button></DialogFooter>
          </DialogContent>
        </Dialog>
        <Dialog open={showReplicationDialog} onOpenChange={setShowReplicationDialog}>
          <DialogTrigger asChild><Button variant="outline">Check Replication</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>Check Replication Status</DialogTitle></DialogHeader>
            <div className="space-y-2">
              <Input placeholder="Workload ID" value={repWorkloadId} onChange={e => setRepWorkloadId(e.target.value)} />
            </div>
            <DialogFooter><Button onClick={checkReplication}>Check</Button></DialogFooter>
          </DialogContent>
        </Dialog>
        <Dialog open={showRollbackDialog} onOpenChange={setShowRollbackDialog}>
          <DialogTrigger asChild><Button variant="destructive">Rollback Wave</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>Rollback Migration Wave</DialogTitle></DialogHeader>
            <Input placeholder="Wave ID" value={rollbackWaveId} onChange={e => setRollbackWaveId(e.target.value)} />
            <DialogFooter><Button variant="destructive" onClick={rollbackWave}>Rollback</Button></DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {replicationStatus && (
        <Card>
          <CardHeader><CardTitle>Replication Status</CardTitle></CardHeader>
          <CardContent className="grid grid-cols-3 gap-4">
            <div><Label>Progress</Label><p className="text-xl font-bold">{replicationStatus.progress}%</p></div>
            <div><Label>State</Label><p className="text-xl font-bold">{replicationStatus.state}</p></div>
            <div><Label>RPO</Label><p className="text-xl font-bold">{replicationStatus.rpo || '15 min'}</p></div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader><CardTitle>Migration Log</CardTitle></CardHeader>
        <CardContent>
          <Table>
            <TableHeader><TableRow><TableHead>Action</TableHead><TableHead>Workload</TableHead><TableHead>Status</TableHead><TableHead>Time</TableHead></TableRow></TableHeader>
            <TableBody>
              {(migrationLog || []).slice(-5).reverse().map((entry: any, i: number) => (
                <TableRow key={i}>
                  <TableCell className="font-medium">{entry.action}</TableCell>
                  <TableCell className="font-mono text-xs">{entry.workload_id?.substring(0, 12)}</TableCell>
                  <TableCell><Badge variant={entry.status === 'success' ? 'default' : 'secondary'}>{entry.status}</Badge></TableCell>
                  <TableCell className="text-xs">{new Date(entry.timestamp || Date.now()).toLocaleString()}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};

function WorkloadFormDialog({ open, onOpenChange, onSubmit }: { open: boolean; onOpenChange: (v: boolean) => void; onSubmit: (data: any) => void }) {
  const [name, setName] = useState(''); const [vcpu, setVcpu] = useState('2'); const [memory, setMemory] = useState('4'); const [storage, setStorage] = useState('50'); const [os, setOs] = useState('linux');
  return (
    <Dialog open={open} onOpenChange={onOpenChange}><DialogContent><DialogHeader><DialogTitle>Add Workload</DialogTitle></DialogHeader>
      <div className="space-y-4">
        <div><Label>Name</Label><Input value={name} onChange={e => setName(e.target.value)} /></div>
        <div className="grid grid-cols-3 gap-2"><div><Label>vCPU</Label><Input type="number" value={vcpu} onChange={e => setVcpu(e.target.value)} /></div><div><Label>RAM (GB)</Label><Input type="number" value={memory} onChange={e => setMemory(e.target.value)} /></div><div><Label>Storage (GB)</Label><Input type="number" value={storage} onChange={e => setStorage(e.target.value)} /></div></div>
        <div><Label>OS</Label><Select value={os} onValueChange={setOs}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{['linux','windows','ubuntu','centos','rhel'].map(o => <SelectItem key={o} value={o}>{o}</SelectItem>)}</SelectContent></Select></div>
      </div>
      <DialogFooter><Button onClick={() => { onSubmit({ name, vcpu: parseInt(vcpu), memory_gb: parseInt(memory), storage_gb: parseInt(storage), os_type: os }); onOpenChange(false); }}>Add</Button></DialogFooter>
    </DialogContent></Dialog>
  );
}

function WaveProgressCard({ wave }: { wave: any }) {
  const total = wave.workload_ids?.length || 0;
  const assessed = 0;
  return (
    <Card><CardHeader className="pb-2"><CardTitle className="text-sm">{wave.name}</CardTitle></CardHeader>
    <CardContent><div className="space-y-1"><div className="flex justify-between text-xs"><span>Wave {wave.id?.substring(0, 8)}</span><Badge variant="outline">{wave.state}</Badge></div>
    <div className="h-2 bg-muted rounded"><div className="h-full bg-blue-500 rounded" style={{ width: `${(assessed / Math.max(total, 1)) * 100}%` }} /></div>
    <p className="text-xs text-muted-foreground">{assessed}/{total} workloads</p></div></CardContent></Card>
  );
}

function WorkflowStatusBadge({ state }: { state: string }) {
  const map: Record<string, string> = { discovered: 'outline', assessed: 'secondary', planned: 'default', migrating: 'default', completed: 'default', failed: 'destructive', rolled_back: 'secondary' };
  return <Badge variant={(map[state] || 'outline') as any}>{state}</Badge>;
}

function MigrationStats({ workloads, waves }: { workloads: any[]; waves: any[] }) {
  const assessed = workloads.filter(w => w.state === 'assessed').length;
  const migrated = workloads.filter(w => w.state === 'completed').length;
  return (
    <div className="grid grid-cols-4 gap-4 mb-6">
      <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Workloads</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{workloads.length}</p></CardContent></Card>
      <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Assessed</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{assessed}</p></CardContent></Card>
      <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Migrated</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{migrated}</p></CardContent></Card>
      <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Waves</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{waves.length}</p></CardContent></Card>
    </div>
  );
}

function ReadinessGauge({ pct }: { pct: number }) {
  const color = pct >= 100 ? 'bg-green-500' : pct >= 50 ? 'bg-yellow-500' : 'bg-red-500';
  return (
    <div className="space-y-1"><div className="flex justify-between text-sm"><span>Readiness</span><span>{pct}%</span></div>
    <div className="h-3 bg-muted rounded"><div className={`h-full rounded ${color}`} style={{ width: `${Math.min(pct, 100)}%` }} /></div></div>
  );
}

export default CloudMigration;
