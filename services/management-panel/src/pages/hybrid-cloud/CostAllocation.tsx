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

interface Allocation { id: string; name: string; amount: number; team: string; project: string; source: string; }
interface Chargeback { id: string; team: string; project: string; amount: number; period: string; }

export const CostAllocation = () => {
  const [allocations, setAllocations] = useState<Allocation[]>([]);
  const [chargebacks, setChargebacks] = useState<Chargeback[]>([]);
  const [loading, setLoading] = useState(true);
  const [showDialog, setShowDialog] = useState(false);
  const [allocName, setAllocName] = useState(''); const [allocAmount, setAllocAmount] = useState(0);
  const [allocTeam, setAllocTeam] = useState(''); const [allocProject, setAllocProject] = useState('');
  const [allocSource, setAllocSource] = useState('cloud');

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    try { const [a, c] = await Promise.all([apiClient.listCostAllocations(), apiClient.listChargebacks()]);
      setAllocations(a || []); setChargebacks(c || []);
    } catch (e) { toast.error('Failed to load allocation data');
    } finally { setLoading(false); }
  };

  const createAllocation = async () => {
    try { await apiClient.createCostAllocation({ name: allocName, amount: allocAmount, team: allocTeam, project: allocProject, source: allocSource });
      toast.success('Allocation created'); setShowDialog(false); loadData();
    } catch (e) { toast.error('Failed to create allocation'); }
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>;

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex justify-between items-center">
        <div><h1 className="text-3xl font-bold"><FormattedMessage id="costAllocation.title" defaultMessage="Cost Allocation" /></h1>
          <p className="text-muted-foreground mt-1"><FormattedMessage id="costAllocation.description" defaultMessage="Tag and allocate costs across on-prem, edge, and multi-cloud" /></p></div>
      </div>
      <Tabs defaultValue="allocations">
        <TabsList><TabsTrigger value="allocations">Allocations</TabsTrigger><TabsTrigger value="chargebacks">Chargebacks</TabsTrigger><TabsTrigger value="teams">Teams</TabsTrigger></TabsList>
        <TabsContent value="allocations" className="space-y-4">
          <div className="flex justify-between"><h2 className="text-xl font-semibold">Cost Allocations</h2>
            <Button onClick={() => setShowDialog(true)}>Allocate Cost</Button></div>
          <Card><CardContent className="p-0">
            <Table><TableHeader><TableRow>
              <TableHead>Name</TableHead><TableHead>Amount</TableHead><TableHead>Team</TableHead><TableHead>Project</TableHead><TableHead>Source</TableHead>
            </TableRow></TableHeader>
            <TableBody>{allocations.map((a) => (
              <TableRow key={a.id}><TableCell className="font-medium">{a.name}</TableCell>
                <TableCell>${a.amount.toFixed(2)}</TableCell><TableCell>{a.team}</TableCell><TableCell>{a.project}</TableCell>
                <TableCell><Badge variant="outline">{a.source}</Badge></TableCell>
              </TableRow>
            ))}</TableBody></Table>
          </CardContent></Card>
          {showDialog && (<div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"><Card className="w-96">
            <CardHeader><CardTitle>Allocate Cost</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div><Label>Name</Label><Input value={allocName} onChange={(e) => setAllocName(e.target.value)} /></div>
              <div><Label>Amount ($)</Label><Input type="number" value={allocAmount} onChange={(e) => setAllocAmount(parseFloat(e.target.value) || 0)} /></div>
              <div><Label>Team</Label><Input value={allocTeam} onChange={(e) => setAllocTeam(e.target.value)} /></div>
              <div><Label>Project</Label><Input value={allocProject} onChange={(e) => setAllocProject(e.target.value)} /></div>
              <div><Label>Source</Label><Input value={allocSource} onChange={(e) => setAllocSource(e.target.value)} /></div>
              <div className="flex gap-2"><Button onClick={createAllocation}>Allocate</Button><Button variant="outline" onClick={() => setShowDialog(false)}>Cancel</Button></div>
            </CardContent></Card></div>)}
        </TabsContent>
        <TabsContent value="chargebacks">
          <Card><CardContent className="p-0">
            <Table><TableHeader><TableRow>
              <TableHead>Team</TableHead><TableHead>Project</TableHead><TableHead>Amount</TableHead><TableHead>Period</TableHead><TableHead>Invoiced</TableHead>
            </TableRow></TableHeader>
            <TableBody>{chargebacks.map((c) => (
              <TableRow key={c.id}><TableCell>{c.team}</TableCell><TableCell>{c.project}</TableCell>
                <TableCell>${c.amount.toFixed(2)}</TableCell><TableCell>{c.period}</TableCell>
                <TableCell><Badge variant="secondary">Pending</Badge></TableCell>
              </TableRow>
            ))}</TableBody></Table>
          </CardContent></Card>
        </TabsContent>
        <TabsContent value="teams">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card><CardHeader><CardTitle>Platform</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">$2,450</p><p className="text-sm text-muted-foreground">Budget: $5,000</p></CardContent></Card>
            <Card><CardHeader><CardTitle>Backend</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">$1,800</p><p className="text-sm text-muted-foreground">Budget: $4,000</p></CardContent></Card>
            <Card><CardHeader><CardTitle>SRE</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">$950</p><p className="text-sm text-muted-foreground">Budget: $2,500</p></CardContent></Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};
  const [allocations, setAllocations] = useState<any[]>([]);
  const [showAllocDialog, setShowAllocDialog] = useState(false);
  const [allocTeam, setAllocTeam] = useState('');
  const [allocProject, setAllocProject] = useState('');
  const [allocAmount, setAllocAmount] = useState(0);
  const [allocSource, setAllocSource] = useState('cloud');
  const [showBudgetDialog, setShowBudgetDialog] = useState(false);
  const [budgetTeam, setBudgetTeam] = useState('');
  const [budgetValue, setBudgetValue] = useState(5000);
  const [exportData, setExportData] = useState<any>(null);

  const exportReport = async () => {
    try { const data = await apiClient.exportCostReport('monthly'); setExportData(data); toast.success('Report exported'); } catch { toast.error('Export failed'); }
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="grid grid-cols-4 gap-4">
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Allocations</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{allocations.length}</p></CardContent></Card>
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Chargebacks</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{chargebacks.length}</p></CardContent></Card>
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Teams</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{teams.length}</p></CardContent></Card>
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Budgets</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{teams.filter(t => t.budget).length}</p></CardContent></Card>
      </div>

      <div className="flex gap-2">
        <Dialog open={showAllocDialog} onOpenChange={setShowAllocDialog}>
          <DialogTrigger asChild><Button>Add Allocation</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>Add Cost Allocation</DialogTitle></DialogHeader>
            <div className="space-y-2">
              <Input placeholder="Team" value={allocTeam} onChange={e => setAllocTeam(e.target.value)} />
              <Input placeholder="Project" value={allocProject} onChange={e => setAllocProject(e.target.value)} />
              <Input type="number" placeholder="Amount" value={allocAmount} onChange={e => setAllocAmount(parseFloat(e.target.value) || 0)} />
              <Select value={allocSource} onValueChange={setAllocSource}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="cloud">Cloud</SelectItem>
                  <SelectItem value="on_prem">On-Prem</SelectItem>
                  <SelectItem value="edge">Edge</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <DialogFooter><Button onClick={() => { apiClient.allocateCost(allocAmount, allocTeam, allocProject, allocSource); toast.success('Allocation added'); setShowAllocDialog(false); }}>Add</Button></DialogFooter>
          </DialogContent>
        </Dialog>
        <Dialog open={showBudgetDialog} onOpenChange={setShowBudgetDialog}>
          <DialogTrigger asChild><Button variant="outline">Set Budget</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>Set Team Budget</DialogTitle></DialogHeader>
            <div className="space-y-2">
              <Input placeholder="Team" value={budgetTeam} onChange={e => setBudgetTeam(e.target.value)} />
              <Input type="number" placeholder="Budget amount" value={budgetValue} onChange={e => setBudgetValue(parseFloat(e.target.value) || 0)} />
            </div>
            <DialogFooter><Button onClick={() => { apiClient.setTeamBudget(budgetTeam, budgetValue); toast.success('Budget set'); setShowBudgetDialog(false); }}>Set</Button></DialogFooter>
          </DialogContent>
        </Dialog>
        <Button variant="outline" onClick={exportReport}>Export Report</Button>
      </div>

      <Card>
        <CardHeader><CardTitle>Cost Allocations</CardTitle></CardHeader>
        <CardContent>
          <Table>
            <TableHeader><TableRow><TableHead>Team</TableHead><TableHead>Project</TableHead><TableHead>Amount</TableHead><TableHead>Source</TableHead><TableHead>Allocated</TableHead></TableRow></TableHeader>
            <TableBody>{allocations.map(a => (
              <TableRow key={a.id}>
                <TableCell className="font-medium">{a.team}</TableCell>
                <TableCell>{a.project}</TableCell>
                <TableCell>${a.amount?.toFixed(2)}</TableCell>
                <TableCell><Badge variant="outline">{a.source}</Badge></TableCell>
                <TableCell>{a.allocated ? <Badge>Yes</Badge> : <Badge variant="secondary">No</Badge>}</TableCell>
              </TableRow>
            ))}</TableBody>
          </Table>
        </CardContent>
      </Card>

      {exportData && (
        <Card>
          <CardHeader><CardTitle>Export: {exportData.period}</CardTitle></CardHeader>
          <CardContent className="grid grid-cols-3 gap-4">
            <div><Label>Total Allocated</Label><p className="text-lg font-bold">${exportData.total_allocations}</p></div>
            <div><Label>Generated At</Label><p className="text-sm">{new Date(exportData.generated_at).toLocaleString()}</p></div>
            <div><Label>Entry Count</Label><p className="text-lg font-bold">{exportData.entries?.length || 0}</p></div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

  const [teams, setTeams] = useState<any[]>([]);
  const [showChargebackDialog, setShowChargebackDialog] = useState(false);
  const [cbTeam, setCbTeam] = useState('');
  const [cbProject, setCbProject] = useState('');
  const [cbAmount, setCbAmount] = useState(0);
  const [showSplitDialog, setShowSplitDialog] = useState(false);
  const [splitTotal, setSplitTotal] = useState(10000);
  const [splitTeams, setSplitTeams] = useState('');

  useEffect(() => {
    loadTeams();
  }, []);

  const loadTeams = async () => {
    try { const data = await apiClient.listAllocationTeams(); setTeams(data || []); } catch { /* ignore */ }
  };

  const createChargeback = async () => {
    try {
      await apiClient.createChargeback(cbTeam, cbProject, cbAmount);
      toast.success('Chargeback created');
      setShowChargebackDialog(false);
      loadData();
    } catch { toast.error('Failed to create chargeback'); }
  };

  const splitCost = async () => {
    const teamList = splitTeams.split(',').map(t => t.trim());
    const share = (splitTotal / teamList.length).toFixed(2);
    toast.success(`Cost split: ${teamList.length} teams @ $${share} each`);
    setShowSplitDialog(false);
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="grid grid-cols-4 gap-4">
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Allocations</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{allocations.length}</p></CardContent></Card>
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Chargebacks</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{chargebacks.length}</p></CardContent></Card>
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Teams</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{teams.length}</p></CardContent></Card>
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Total Allocated</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">${allocations.reduce((s, a) => s + (a.amount || 0), 0).toFixed(2)}</p></CardContent></Card>
      </div>

      <div className="flex gap-2">
        <Dialog open={showChargebackDialog} onOpenChange={setShowChargebackDialog}>
          <DialogTrigger asChild><Button>Create Chargeback</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>Create Chargeback</DialogTitle></DialogHeader>
            <div className="space-y-2">
              <Input placeholder="Team" value={cbTeam} onChange={e => setCbTeam(e.target.value)} />
              <Input placeholder="Project" value={cbProject} onChange={e => setCbProject(e.target.value)} />
              <Input type="number" placeholder="Amount" value={cbAmount} onChange={e => setCbAmount(parseFloat(e.target.value) || 0)} />
            </div>
            <DialogFooter><Button onClick={createChargeback}>Create</Button></DialogFooter>
          </DialogContent>
        </Dialog>
        <Dialog open={showSplitDialog} onOpenChange={setShowSplitDialog}>
          <DialogTrigger asChild><Button variant="outline">Split Cost</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>Split Cost Across Teams</DialogTitle></DialogHeader>
            <div className="space-y-2">
              <Input type="number" placeholder="Total amount" value={splitTotal} onChange={e => setSplitTotal(parseFloat(e.target.value) || 0)} />
              <Input placeholder="Teams (comma-separated)" value={splitTeams} onChange={e => setSplitTeams(e.target.value)} />
            </div>
            <DialogFooter><Button onClick={splitCost}>Split</Button></DialogFooter>
          </DialogContent>
        </Dialog>
        <Button variant="outline" onClick={exportReport}>Export Report</Button>
      </div>

      <Card>
        <CardHeader><CardTitle>Team Budgets</CardTitle></CardHeader>
        <CardContent>
          <Table>
            <TableHeader><TableRow><TableHead>Team</TableHead><TableHead>Spent</TableHead><TableHead>Budget</TableHead><TableHead>Utilization</TableHead></TableRow></TableHeader>
            <TableBody>{teams.slice(0, 10).map((t, i) => (
              <TableRow key={i}>
                <TableCell className="font-medium">{t.name || t.team}</TableCell>
                <TableCell>${(t.spent || 0).toFixed(2)}</TableCell>
                <TableCell>${(t.budget || 0).toFixed(2)}</TableCell>
                <TableCell>
                  <Badge variant={((t.spent || 0) / (t.budget || 1) * 100) > 80 ? 'destructive' : 'default'}>
                    {((t.spent || 0) / (t.budget || 1) * 100).toFixed(1)}%
                  </Badge>
                </TableCell>
              </TableRow>
            ))}</TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};

function AllocationFormDialog({ open, onOpenChange, onSubmit }: { open: boolean; onOpenChange: (v: boolean) => void; onSubmit: (data: any) => void }) {
  const [team, setTeam] = useState(''); const [project, setProject] = useState(''); const [amount, setAmount] = useState('0'); const [category, setCategory] = useState('compute');
  return (
    <Dialog open={open} onOpenChange={onOpenChange}><DialogContent><DialogHeader><DialogTitle>Allocate Cost</DialogTitle></DialogHeader>
      <div className="space-y-4">
        <div><Label>Team</Label><Input value={team} onChange={e => setTeam(e.target.value)} /></div>
        <div><Label>Project</Label><Input value={project} onChange={e => setProject(e.target.value)} /></div>
        <div><Label>Amount ($)</Label><Input type="number" value={amount} onChange={e => setAmount(e.target.value)} /></div>
        <div><Label>Category</Label><Select value={category} onValueChange={setCategory}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{['compute','storage','network','database','gpu','license','support','other'].map(c => <SelectItem key={c} value={c}>{c}</SelectItem>)}</SelectContent></Select></div>
      </div>
      <DialogFooter><Button onClick={() => { onSubmit({ team, project, amount: parseFloat(amount), category }); onOpenChange(false); }}>Allocate</Button></DialogFooter>
    </DialogContent></Dialog>
  );
}

function BudgetGauge({ spent, budget }: { spent: number; budget: number }) {
  const pct = budget > 0 ? Math.round((spent / budget) * 100) : 0;
  const color = pct > 90 ? 'bg-red-500' : pct > 75 ? 'bg-yellow-500' : 'bg-green-500';
  return (
    <div className="space-y-1"><div className="flex justify-between text-sm"><span>${spent.toFixed(2)}</span><span>${budget.toFixed(2)}</span></div>
    <div className="h-3 bg-muted rounded"><div className={`h-full rounded ${color}`} style={{ width: `${Math.min(pct, 100)}%` }} /></div>
    <p className="text-xs text-right text-muted-foreground">{pct}% utilized</p></div>
  );
}

function CostByCategoryChart({ allocations }: { allocations: any[] }) {
  const byCat: Record<string, number> = {};
  allocations.forEach((a: any) => { const c = a.category || 'other'; byCat[c] = (byCat[c] || 0) + (a.amount || 0); });
  const sorted = Object.entries(byCat).sort((a, b) => b[1] - a[1]);
  const total = sorted.reduce((s, [, v]) => s + v, 0);
  return (
    <Card><CardHeader><CardTitle>Cost by Category</CardTitle></CardHeader>
    <CardContent><div className="space-y-2">{sorted.map(([cat, amt]) => (
      <div key={cat} className="flex items-center gap-2"><span className="text-sm w-24 capitalize">{cat}</span><div className="h-4 bg-muted rounded flex-1"><div className="h-full bg-primary rounded" style={{ width: `${(amt / total) * 100}%` }} /></div><span className="text-sm w-20 text-right">${amt.toFixed(2)}</span></div>
    ))}</div></CardContent></Card>
  );
}

function ChargebackTable({ chargebacks }: { chargebacks: any[] }) {
  return (
    <Card><CardHeader><CardTitle>Chargebacks</CardTitle></CardHeader>
    <CardContent><Table><TableHeader><TableRow><TableHead>Team</TableHead><TableHead>Project</TableHead><TableHead>Amount</TableHead><TableHead>Period</TableHead><TableHead>Status</TableHead></TableRow></TableHeader>
    <TableBody>{chargebacks.slice(0, 20).map((c: any, i: number) => (
      <TableRow key={i}><TableCell>{c.team}</TableCell><TableCell>{c.project}</TableCell><TableCell>${c.amount?.toFixed(2)}</TableCell><TableCell>{c.period}</TableCell><TableCell><Badge variant={c.invoiced ? 'default' : 'secondary'}>{c.invoiced ? 'Invoiced' : 'Pending'}</Badge></TableCell></TableRow>
    ))}</TableBody></Table></CardContent></Card>
  );
}

function TeamSpendBar({ teams }: { teams: any[] }) {
  const maxSpend = Math.max(...teams.map(t => t.total_spend || 0), 1);
  return (
    <Card><CardHeader><CardTitle>Team Spend</CardTitle></CardHeader>
    <CardContent><div className="space-y-2">{teams.slice(0, 10).map((t: any, i: number) => (
      <div key={i} className="flex items-center gap-2"><span className="text-sm w-24 truncate">{t.team}</span><div className="h-5 bg-muted rounded flex-1"><div className="h-full bg-primary rounded" style={{ width: `${((t.total_spend || 0) / maxSpend) * 100}%` }} /></div><span className="text-sm w-20 text-right">${(t.total_spend || 0).toFixed(2)}</span></div>
    ))}</div></CardContent></Card>
  );
}

export default CostAllocation;
