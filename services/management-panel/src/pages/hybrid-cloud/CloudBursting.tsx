import { useEffect, useState } from 'react';
import { FormattedMessage } from 'react-intl';
import { apiClient } from '../../lib/api';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table';
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '../../components/ui/dialog';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';

interface BurstWorkload {
  workload_id: string;
  name: string;
  target_capacity: number;
  current_capacity: number;
  priority: number;
  state: string;
}

interface ActiveBurst {
  burst_id: string;
  started_at: string;
  workloads: string[];
  state: string;
}

export const CloudBursting = () => {
  const [workloads, setWorkloads] = useState<BurstWorkload[]>([]);
  const [bursts, setBursts] = useState<ActiveBurst[]>([]);
  const [loading, setLoading] = useState(true);
  const [showDialog, setShowDialog] = useState(false);
  const [newName, setNewName] = useState('');
  const [newCapacity, setNewCapacity] = useState(100);
  const [newPriority, setNewPriority] = useState(5);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [wlData, burstData] = await Promise.all([
        apiClient.listBurstWorkloads(),
        apiClient.listActiveBursts(),
      ]);
      setWorkloads(wlData || []);
      setBursts(burstData || []);
    } catch (error) {
      toast.error('Failed to load burst data');
    } finally {
      setLoading(false);
    }
  };

  const registerWorkload = async () => {
    try {
      const wl = await apiClient.registerBurstWorkload({ name: newName, target_capacity: newCapacity, priority: newPriority });
      setWorkloads([...workloads, wl]);
      toast.success('Workload registered');
      setShowDialog(false);
      setNewName('');
    } catch (error) {
      toast.error('Failed to register workload');
    }
  };

  const startBurst = async () => {
    try {
      const burst = await apiClient.startCloudBurst();
      setBursts([...bursts, burst]);
      toast.success('Cloud burst initiated');
    } catch (error) {
      toast.error('Failed to start burst');
    }
  };

  const drainBurst = async (burstId: string) => {
    try {
      await apiClient.drainCloudBurst(burstId);
      setBursts(bursts.filter((b) => b.burst_id !== burstId));
      toast.success('Burst drained');
    } catch (error) {
      toast.error('Failed to drain burst');
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>;
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold"><FormattedMessage id="cloudBursting.title" defaultMessage="Cloud Bursting Gateway" /></h1>
          <p className="text-muted-foreground mt-1"><FormattedMessage id="cloudBursting.description" defaultMessage="Burst on-prem workloads to public cloud during peak" /></p>
        </div>
      </div>

      <Tabs defaultValue="workloads">
        <TabsList>
          <TabsTrigger value="workloads"><FormattedMessage id="cloudBursting.workloads" defaultMessage="Workloads" /></TabsTrigger>
          <TabsTrigger value="bursts"><FormattedMessage id="cloudBursting.activeBursts" defaultMessage="Active Bursts" /></TabsTrigger>
          <TabsTrigger value="config"><FormattedMessage id="cloudBursting.config" defaultMessage="Configuration" /></TabsTrigger>
        </TabsList>

        <TabsContent value="workloads" className="space-y-4">
          <div className="flex justify-between">
            <h2 className="text-xl font-semibold"><FormattedMessage id="cloudBursting.registeredWorkloads" defaultMessage="Registered Workloads" /></h2>
            <Dialog open={showDialog} onOpenChange={setShowDialog}>
              <DialogTrigger asChild><Button><FormattedMessage id="cloudBursting.registerWorkload" defaultMessage="Register Workload" /></Button></DialogTrigger>
              <DialogContent>
                <DialogHeader><DialogTitle><FormattedMessage id="cloudBursting.registerNew" defaultMessage="Register New Workload" /></DialogTitle></DialogHeader>
                <div className="space-y-4">
                  <div><Label><FormattedMessage id="common.name" defaultMessage="Name" /></Label><Input value={newName} onChange={(e) => setNewName(e.target.value)} placeholder="web-server" /></div>
                  <div><Label><FormattedMessage id="cloudBursting.targetCapacity" defaultMessage="Target Capacity" /></Label><Input type="number" value={newCapacity} onChange={(e) => setNewCapacity(parseInt(e.target.value) || 100)} /></div>
                  <div><Label><FormattedMessage id="cloudBursting.priority" defaultMessage="Priority (1-10)" /></Label><Input type="number" value={newPriority} onChange={(e) => setNewPriority(parseInt(e.target.value) || 5)} min={1} max={10} /></div>
                </div>
                <DialogFooter><Button onClick={registerWorkload}><FormattedMessage id="common.create" defaultMessage="Create" /></Button></DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
          <Card><CardContent className="p-0">
            <Table><TableHeader><TableRow>
              <TableHead><FormattedMessage id="common.name" defaultMessage="Name" /></TableHead>
              <TableHead><FormattedMessage id="cloudBursting.targetCapacity" defaultMessage="Target" /></TableHead>
              <TableHead><FormattedMessage id="cloudBursting.currentCapacity" defaultMessage="Current" /></TableHead>
              <TableHead><FormattedMessage id="cloudBursting.priority" defaultMessage="Priority" /></TableHead>
              <TableHead><FormattedMessage id="common.status" defaultMessage="Status" /></TableHead>
            </TableRow></TableHeader>
            <TableBody>{workloads.map((w) => (
              <TableRow key={w.workload_id}>
                <TableCell className="font-medium">{w.name}</TableCell>
                <TableCell>{w.target_capacity}</TableCell>
                <TableCell>{w.current_capacity}</TableCell>
                <TableCell>{w.priority}</TableCell>
                <TableCell><Badge variant={w.state === 'bursting' ? 'default' : 'secondary'}>{w.state}</Badge></TableCell>
              </TableRow>
            ))}</TableBody></Table>
          </CardContent></Card>
          <Button onClick={startBurst}><FormattedMessage id="cloudBursting.startBurst" defaultMessage="Start Cloud Burst" /></Button>
        </TabsContent>

        <TabsContent value="bursts" className="space-y-4">
          <Card><CardContent className="p-0">
            <Table><TableHeader><TableRow>
              <TableHead><FormattedMessage id="cloudBursting.burstId" defaultMessage="Burst ID" /></TableHead>
              <TableHead><FormattedMessage id="cloudBursting.startedAt" defaultMessage="Started At" /></TableHead>
              <TableHead><FormattedMessage id="cloudBursting.workloadCount" defaultMessage="Workloads" /></TableHead>
              <TableHead><FormattedMessage id="common.status" defaultMessage="Status" /></TableHead>
              <TableHead><FormattedMessage id="common.actions" defaultMessage="Actions" /></TableHead>
            </TableRow></TableHeader>
            <TableBody>{bursts.map((b) => (
              <TableRow key={b.burst_id}>
                <TableCell className="font-mono text-xs">{b.burst_id}</TableCell>
                <TableCell>{new Date(b.started_at).toLocaleString()}</TableCell>
                <TableCell>{b.workloads?.length || 0}</TableCell>
                <TableCell><Badge variant={b.state === 'bursting' ? 'default' : 'secondary'}>{b.state}</Badge></TableCell>
                <TableCell><Button variant="destructive" size="sm" onClick={() => drainBurst(b.burst_id)}><FormattedMessage id="cloudBursting.drain" defaultMessage="Drain" /></Button></TableCell>
              </TableRow>
            ))}</TableBody></Table>
          </CardContent></Card>
        </TabsContent>

        <TabsContent value="config" className="space-y-4">
          <Card><CardHeader><CardTitle><FormattedMessage id="cloudBursting.burstConfig" defaultMessage="Burst Configuration" /></CardTitle></CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <div><Label>Min Burst Threshold</Label><p className="text-2xl font-bold">80%</p></div>
              <div><Label>Max Burst Capacity</Label><p className="text-2xl font-bold">500</p></div>
              <div><Label>Default Strategy</Label><p className="text-2xl font-bold">Least Connections</p></div>
              <div><Label>Network Stitching</Label><p className="text-2xl font-bold">WireGuard</p></div>
              <div><Label>Burst Duration</Label><p className="text-2xl font-bold">120 min</p></div>
              <div><Label>Drain Timeout</Label><p className="text-2xl font-bold">300 sec</p></div>
            </div>
          </CardContent></Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

  const [networkStitches, setNetworkStitches] = useState<any[]>([]);
  const [costAnalysis, setCostAnalysis] = useState<any>(null);
  const [strategy, setStrategy] = useState('round_robin');

  useEffect(() => {
    loadCostAnalysis();
  }, []);

  const loadCostAnalysis = async () => {
    try {
      const data = await apiClient.getBurstCostAnalysis();
      setCostAnalysis(data);
    } catch { /* ignore */ }
  };

  const createStitch = async (onPremCidr: string, cloudCidr: string, provider: string) => {
    try {
      const result = await apiClient.createNetworkStitch(onPremCidr, cloudCidr, provider);
      setNetworkStitches([...networkStitches, result]);
      toast.success('Network stitch created');
    } catch { toast.error('Failed to create stitch'); }
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="grid grid-cols-4 gap-4">
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Workloads</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{workloads.length}</p></CardContent></Card>
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Active Bursts</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{bursts.length}</p></CardContent></Card>
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">On-Prem Cost/hr</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">${(costAnalysis?.estimated_on_prem_cost || 0).toFixed(2)}</p></CardContent></Card>
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Cloud Cost/hr</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">${(costAnalysis?.estimated_cloud_cost || 0).toFixed(2)}</p></CardContent></Card>
      </div>

      <div className="flex items-center gap-4">
        <Label>Strategy:</Label>
        <Select value={strategy} onValueChange={v => { setStrategy(v); apiClient.setBurstStrategy(v); }}>
          <SelectTrigger className="w-[200px]"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="round_robin">Round Robin</SelectItem>
            <SelectItem value="weighted">Weighted</SelectItem>
            <SelectItem value="least_loaded">Least Loaded</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <Card>
        <CardHeader><CardTitle>Network Stitches</CardTitle></CardHeader>
        <CardContent>
          <div className="space-y-2">
            {networkStitches.map(s => (
              <div key={s.id} className="flex items-center justify-between p-2 border rounded">
                <span className="font-mono text-sm">{s.on_prem_cidr} ↔ {s.cloud_cidr}</span>
                <Badge variant="outline">{s.provider}</Badge>
              </div>
            ))}
            <Dialog>
              <DialogTrigger asChild><Button variant="outline" size="sm">Add Stitch</Button></DialogTrigger>
              <DialogContent>
                <DialogHeader><DialogTitle>Add Network Stitch</DialogTitle></DialogHeader>
                <div className="space-y-2">
                  <Input placeholder="On-Prem CIDR (e.g. 10.0.0.0/16)" />
                  <Input placeholder="Cloud CIDR (e.g. 172.16.0.0/16)" />
                  <Input placeholder="Provider (e.g. aws)" />
                </div>
                <DialogFooter><Button onClick={() => createStitch('10.0.0.0/16', '172.16.0.0/16', 'aws')}>Create</Button></DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

  const [showAutoScaleDialog, setShowAutoScaleDialog] = useState(false);
  const [autoScaleWl, setAutoScaleWl] = useState('');
  const [autoScaleMin, setAutoScaleMin] = useState(1);
  const [autoScaleMax, setAutoScaleMax] = useState(50);
  const [autoScaleThreshold, setAutoScaleThreshold] = useState(80);
  const [burstPolicies, setBurstPolicies] = useState<any[]>([]);
  const [peakData, setPeakData] = useState<any>(null);

  useEffect(() => {
    loadPeakData();
  }, []);

  const loadPeakData = async () => {
    try { const data = await apiClient.getBurstPeakAnalysis(); setPeakData(data); } catch { /* ignore */ }
  };

  const configureAutoScale = async () => {
    try {
      await apiClient.configureBurstAutoScale(autoScaleWl, autoScaleMin, autoScaleMax, autoScaleThreshold);
      toast.success('Auto-scale configured');
      setShowAutoScaleDialog(false);
    } catch { toast.error('Failed to configure auto-scale'); }
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="grid grid-cols-4 gap-4">
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Workloads</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{workloads.length}</p></CardContent></Card>
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Active Bursts</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{bursts.length}</p></CardContent></Card>
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Policies</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{burstPolicies.length}</p></CardContent></Card>
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Avg Load</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{peakData?.avg_load || 0}%</p></CardContent></Card>
      </div>

      <div className="flex gap-2">
        <Dialog open={showAutoScaleDialog} onOpenChange={setShowAutoScaleDialog}>
          <DialogTrigger asChild><Button>Configure Auto-Scale</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>Auto-Scale Configuration</DialogTitle></DialogHeader>
            <div className="space-y-2">
              <Input placeholder="Workload ID" value={autoScaleWl} onChange={e => setAutoScaleWl(e.target.value)} />
              <Input type="number" placeholder="Min capacity" value={autoScaleMin} onChange={e => setAutoScaleMin(parseInt(e.target.value) || 1)} />
              <Input type="number" placeholder="Max capacity" value={autoScaleMax} onChange={e => setAutoScaleMax(parseInt(e.target.value) || 50)} />
              <Input type="number" placeholder="Threshold %" value={autoScaleThreshold} onChange={e => setAutoScaleThreshold(parseInt(e.target.value) || 80)} />
            </div>
            <DialogFooter><Button onClick={configureAutoScale}>Configure</Button></DialogFooter>
          </DialogContent>
        </Dialog>
        <Button variant="outline" onClick={loadPeakData}>Refresh Peak Data</Button>
      </div>

      {peakData && (
        <Card>
          <CardHeader><CardTitle>Peak Analysis</CardTitle></CardHeader>
          <CardContent className="grid grid-cols-3 gap-4">
            <div><Label>Average Load</Label><p className="text-xl font-bold">{peakData.avg_load}%</p></div>
            <div><Label>Peak Load</Label><p className="text-xl font-bold">{peakData.peak_load}%</p></div>
            <div><Label>Peak Time</Label><p className="text-xl font-bold">{peakData.peak_time || 'N/A'}</p></div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader><CardTitle>Burst Strategy Configuration</CardTitle></CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <Label>Strategy:</Label>
            <Select value={strategy} onValueChange={v => { setStrategy(v); apiClient.setBurstStrategy(v); }}>
              <SelectTrigger className="w-[200px]"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="round_robin">Round Robin</SelectItem>
                <SelectItem value="weighted">Weighted</SelectItem>
                <SelectItem value="least_loaded">Least Loaded</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Cost Analysis</CardTitle></CardHeader>
        <CardContent className="grid grid-cols-3 gap-4">
          <div><Label>On-Prem Cost/hr</Label><p className="text-xl font-bold">${(costAnalysis?.estimated_on_prem_cost || 0).toFixed(2)}</p></div>
          <div><Label>Cloud Cost/hr</Label><p className="text-xl font-bold">${(costAnalysis?.estimated_cloud_cost || 0).toFixed(2)}</p></div>
          <div><Label>Savings/hr</Label><p className="text-xl font-bold text-green-600">${((costAnalysis?.estimated_on_prem_cost || 0) - (costAnalysis?.estimated_cloud_cost || 0)).toFixed(2)}</p></div>
        </CardContent>
      </Card>
    </div>
  );
};

function WorkloadFormDialog({ open, onOpenChange, onSubmit }: { open: boolean; onOpenChange: (v: boolean) => void; onSubmit: (data: any) => void }) {
  const [name, setName] = useState(''); const [capacity, setCapacity] = useState('100'); const [priority, setPriority] = useState('5');
  return (
    <Dialog open={open} onOpenChange={onOpenChange}><DialogContent><DialogHeader><DialogTitle>Create Workload</DialogTitle></DialogHeader>
      <div className="space-y-4">
        <div><Label>Name</Label><Input value={name} onChange={e => setName(e.target.value)} /></div>
        <div><Label>Target Capacity</Label><Input type="number" value={capacity} onChange={e => setCapacity(e.target.value)} /></div>
        <div><Label>Priority (1-10)</Label><Input type="number" min={1} max={10} value={priority} onChange={e => setPriority(e.target.value)} /></div>
      </div>
      <DialogFooter><Button onClick={() => { onSubmit({ name, target_capacity: parseInt(capacity), priority: parseInt(priority) }); onOpenChange(false); }}>Create</Button></DialogFooter>
    </DialogContent></Dialog>
  );
}

function BurstStateBadge({ state }: { state: string }) {
  const map: Record<string, string> = { idle: 'secondary', bursting: 'default', scaling_up: 'default', scaling_down: 'outline', draining: 'secondary', completed: 'default', failed: 'destructive' };
  return <Badge variant={(map[state] || 'outline') as any}>{state}</Badge>;
}

function CapacityGauge({ current, target }: { current: number; target: number }) {
  const pct = target > 0 ? Math.round((current / target) * 100) : 0;
  const color = pct > 90 ? 'bg-red-500' : pct > 75 ? 'bg-yellow-500' : 'bg-green-500';
  return (
    <div className="space-y-1"><div className="flex justify-between text-sm"><span>Current: {current}</span><span>Target: {target}</span></div>
    <div className="h-4 bg-muted rounded"><div className={`h-full rounded ${color}`} style={{ width: `${Math.min(pct, 100)}%` }} /></div><p className="text-xs text-right text-muted-foreground">{pct}% utilized</p></div>
  );
}

function StitchCard({ stitch }: { stitch: any }) {
  return (
    <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Stitch: {stitch.stitch_id?.substring(0, 12)}</CardTitle></CardHeader>
    <CardContent><div className="text-xs space-y-1"><p>Method: {stitch.method}</p><p>On-Prem: {stitch.on_prem_subnet}</p><p>Cloud: {stitch.cloud_subnet}</p><p>Status: <Badge variant="outline">{stitch.status}</Badge></p></div></CardContent></Card>
  );
}

function BurstTimeline({ bursts }: { bursts: any[] }) {
  return (
    <Card><CardHeader><CardTitle>Recent Bursts</CardTitle></CardHeader>
    <CardContent><Table><TableHeader><TableRow><TableHead>ID</TableHead><TableHead>Workloads</TableHead><TableHead>State</TableHead><TableHead>Started</TableHead></TableRow></TableHeader>
    <TableBody>{bursts.slice(-10).reverse().map((b: any, i: number) => (
      <TableRow key={i}><TableCell className="font-mono text-xs">{b.burst_id?.substring(0, 12)}</TableCell><TableCell>{(b.workloads || []).length}</TableCell><TableCell><BurstStateBadge state={b.state} /></TableCell><TableCell className="text-xs">{new Date(b.started_at).toLocaleString()}</TableCell></TableRow>
    ))}</TableBody></Table></CardContent></Card>
  );
}

function StrategySelector({ strategies, selected, onChange }: { strategies: string[]; selected: string; onChange: (v: string) => void }) {
  return (
    <div className="flex items-center gap-2 mb-4"><Label>Strategy:</Label><Select value={selected} onValueChange={onChange}><SelectTrigger className="w-48"><SelectValue /></SelectTrigger><SelectContent>{strategies.map(s => <SelectItem key={s} value={s}>{s.replace('_', ' ')}</SelectItem>)}</SelectContent></Select></div>
  );
}

export default CloudBursting;
