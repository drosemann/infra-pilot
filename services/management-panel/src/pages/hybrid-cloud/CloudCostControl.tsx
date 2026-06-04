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

interface Budget { id: string; name: string; amount: number; spent: number; period: string; }
interface Anomaly { id: string; provider: string; service: string; amount: number; expected_amount: number; deviation: number; severity: string; }

export const CloudCostControl = () => {
  const [budgets, setBudgets] = useState<Budget[]>([]);
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);
  const [totalSpend, setTotalSpend] = useState(0);
  const [loading, setLoading] = useState(true);
  const [showBudgetDialog, setShowBudgetDialog] = useState(false);
  const [budgetName, setBudgetName] = useState('');
  const [budgetAmount, setBudgetAmount] = useState(1000);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    try {
      const [budgetData, anomalyData, spendData] = await Promise.all([
        apiClient.listCostBudgets(), apiClient.listCostAnomalies(), apiClient.getTotalCostSpend(),
      ]);
      setBudgets(budgetData || []); setAnomalies(anomalyData || []);
      setTotalSpend(spendData?.total || 0);
    } catch (e) { toast.error('Failed to load cost data');
    } finally { setLoading(false); }
  };

  const createBudget = async () => {
    try { await apiClient.createCostBudget({ name: budgetName, amount: budgetAmount }); toast.success('Budget created'); setShowBudgetDialog(false); loadData();
    } catch (e) { toast.error('Failed to create budget'); }
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>;

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex justify-between items-center">
        <div><h1 className="text-3xl font-bold"><FormattedMessage id="cloudCostControl.title" defaultMessage="Cloud Cost Control" /></h1>
          <p className="text-muted-foreground mt-1"><FormattedMessage id="cloudCostControl.description" defaultMessage="Aggregate billing, budgets, and anomaly detection" /></p></div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card><CardHeader><CardTitle>Total Spend</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold">${totalSpend.toFixed(2)}</p></CardContent></Card>
        <Card><CardHeader><CardTitle>Active Budgets</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold">{budgets.length}</p></CardContent></Card>
        <Card><CardHeader><CardTitle>Anomalies</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold">{anomalies.length}</p></CardContent></Card>
      </div>
      <Tabs defaultValue="budgets">
        <TabsList><TabsTrigger value="budgets">Budgets</TabsTrigger><TabsTrigger value="anomalies">Anomalies</TabsTrigger></TabsList>
        <TabsContent value="budgets" className="space-y-4">
          <div className="flex justify-between"><h2 className="text-xl font-semibold">Budgets</h2>
            <Button onClick={() => setShowBudgetDialog(true)}>Create Budget</Button></div>
          <Card><CardContent className="p-0">
            <Table><TableHeader><TableRow>
              <TableHead>Name</TableHead><TableHead>Amount</TableHead><TableHead>Spent</TableHead><TableHead>Utilization</TableHead><TableHead>Period</TableHead>
            </TableRow></TableHeader>
            <TableBody>{budgets.map((b) => {
              const pct = b.amount > 0 ? ((b.spent / b.amount) * 100).toFixed(1) : '0';
              return (<TableRow key={b.id}><TableCell className="font-medium">{b.name}</TableCell>
                <TableCell>${b.amount.toFixed(2)}</TableCell><TableCell>${b.spent.toFixed(2)}</TableCell>
                <TableCell><Badge variant={parseFloat(pct) > 80 ? 'destructive' : 'default'}>{pct}%</Badge></TableCell>
                <TableCell>{b.period}</TableCell></TableRow>);
            })}</TableBody></Table>
          </CardContent></Card>
          {showBudgetDialog && (<div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"><Card className="w-96">
            <CardHeader><CardTitle>Create Budget</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div><Label>Name</Label><Input value={budgetName} onChange={(e) => setBudgetName(e.target.value)} /></div>
              <div><Label>Amount ($)</Label><Input type="number" value={budgetAmount} onChange={(e) => setBudgetAmount(parseFloat(e.target.value) || 0)} /></div>
              <div className="flex gap-2"><Button onClick={createBudget}>Create</Button><Button variant="outline" onClick={() => setShowBudgetDialog(false)}>Cancel</Button></div>
            </CardContent></Card></div>))}
        </TabsContent>
        <TabsContent value="anomalies">
          <Card><CardContent className="p-0">
            <Table><TableHeader><TableRow>
              <TableHead>Provider</TableHead><TableHead>Service</TableHead><TableHead>Actual</TableHead><TableHead>Expected</TableHead><TableHead>Deviation</TableHead><TableHead>Severity</TableHead>
            </TableRow></TableHeader>
            <TableBody>{anomalies.map((a) => (
              <TableRow key={a.id}><TableCell>{a.provider}</TableCell><TableCell>{a.service}</TableCell>
                <TableCell>${a.amount.toFixed(2)}</TableCell><TableCell>${a.expected_amount.toFixed(2)}</TableCell>
                <TableCell>{(a.deviation * 100).toFixed(1)}%</TableCell>
                <TableCell><Badge variant={a.severity === 'critical' ? 'destructive' : 'default'}>{a.severity}</Badge></TableCell>
              </TableRow>
            ))}</TableBody></Table>
          </CardContent></Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};
  const [showBudgetDialog, setShowBudgetDialog] = useState(false);
  const [budgetName, setBudgetName] = useState('');
  const [budgetAmount, setBudgetAmount] = useState(1000);
  const [budgetProvider, setBudgetProvider] = useState('aws');
  const [showCostDialog, setShowCostDialog] = useState(false);
  const [costProvider, setCostProvider] = useState('aws');
  const [costAmount, setCostAmount] = useState(0);
  const [costCategory, setCostCategory] = useState('compute');
  const [costDescription, setCostDescription] = useState('');
  const [trends, setTrends] = useState<any>(null);

  useEffect(() => {
    loadTrends();
  }, []);

  const loadTrends = async () => {
    try {
      const data = await apiClient.getCostTrends();
      setTrends(data);
    } catch { /* ignore */ }
  };

  const recordCost = async () => {
    try {
      await apiClient.recordCost(costProvider, costAmount, costCategory, costDescription);
      toast.success('Cost recorded');
      setShowCostDialog(false);
    } catch { toast.error('Failed to record cost'); }
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="grid grid-cols-4 gap-4">
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Total Spend</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">${budgets.reduce((s, b) => s + (b.spent || 0), 0).toFixed(2)}</p></CardContent></Card>
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Budgets</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{budgets.length}</p></CardContent></Card>
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Anomalies</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{anomalies.filter(a => a.severity === 'critical').length}</p></CardContent></Card>
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Daily Avg</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">${(trends?.daily_avg || 0).toFixed(2)}</p></CardContent></Card>
      </div>

      <div className="flex gap-2">
        <Dialog open={showBudgetDialog} onOpenChange={setShowBudgetDialog}>
          <DialogTrigger asChild><Button>Create Budget</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>Create Budget</DialogTitle></DialogHeader>
            <div className="space-y-2">
              <Input placeholder="Budget name" value={budgetName} onChange={e => setBudgetName(e.target.value)} />
              <Input type="number" placeholder="Amount" value={budgetAmount} onChange={e => setBudgetAmount(parseFloat(e.target.value) || 0)} />
              <Input placeholder="Provider" value={budgetProvider} onChange={e => setBudgetProvider(e.target.value)} />
            </div>
            <DialogFooter><Button onClick={() => { createBudget(); }}>Create</Button></DialogFooter>
          </DialogContent>
        </Dialog>
        <Dialog open={showCostDialog} onOpenChange={setShowCostDialog}>
          <DialogTrigger asChild><Button variant="outline">Record Cost</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>Record Cost</DialogTitle></DialogHeader>
            <div className="space-y-2">
              <Input placeholder="Provider" value={costProvider} onChange={e => setCostProvider(e.target.value)} />
              <Input type="number" placeholder="Amount" value={costAmount} onChange={e => setCostAmount(parseFloat(e.target.value) || 0)} />
              <Input placeholder="Category" value={costCategory} onChange={e => setCostCategory(e.target.value)} />
              <Input placeholder="Description" value={costDescription} onChange={e => setCostDescription(e.target.value)} />
            </div>
            <DialogFooter><Button onClick={recordCost}>Record</Button></DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {trends && (
        <Card>
          <CardHeader><CardTitle>Cost Trends</CardTitle></CardHeader>
          <CardContent className="grid grid-cols-3 gap-4">
            <div><Label>Period</Label><p className="text-xl font-bold">{trends.period_days}d</p></div>
            <div><Label>Trend</Label><p className="text-xl font-bold">{trends.trend}</p></div>
            <div><Label>Confidence</Label><p className="text-xl font-bold">High</p></div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

  const [showRiDialog, setShowRiDialog] = useState(false);
  const [riProvider, setRiProvider] = useState('aws');
  const [riInstanceType, setRiInstanceType] = useState('t3.large');
  const [riTerm, setRiTerm] = useState('1yr');
  const [riCount, setRiCount] = useState(1);
  const [reservedInstances, setReservedInstances] = useState<any[]>([]);
  const [forecast, setForecast] = useState<any>(null);

  useEffect(() => {
    loadForecast();
  }, []);

  const loadForecast = async () => {
    try { const data = await apiClient.getCostForecast(); setForecast(data); } catch { /* ignore */ }
  };

  const purchaseReserved = async () => {
    try {
      const result = await apiClient.purchaseReservedInstance(riProvider, riInstanceType, riTerm, riCount);
      setReservedInstances([...reservedInstances, result]);
      toast.success('Reserved instance purchased');
      setShowRiDialog(false);
    } catch { toast.error('Failed to purchase'); }
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="grid grid-cols-4 gap-4">
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Total Spend</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">${totalSpend.toFixed(2)}</p></CardContent></Card>
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Budgets</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{budgets.length}</p></CardContent></Card>
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">RI Purchased</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{reservedInstances.length}</p></CardContent></Card>
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Forecast</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">${forecast?.forecast_amount?.toFixed(2) || '0.00'}</p></CardContent></Card>
      </div>

      <div className="flex gap-2">
        <Dialog open={showRiDialog} onOpenChange={setShowRiDialog}>
          <DialogTrigger asChild><Button>Purchase Reserved Instance</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>Purchase Reserved Instance</DialogTitle></DialogHeader>
            <div className="space-y-2">
              <Select value={riProvider} onValueChange={setRiProvider}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="aws">AWS</SelectItem>
                  <SelectItem value="azure">Azure</SelectItem>
                  <SelectItem value="gcp">GCP</SelectItem>
                </SelectContent>
              </Select>
              <Input placeholder="Instance type" value={riInstanceType} onChange={e => setRiInstanceType(e.target.value)} />
              <Select value={riTerm} onValueChange={setRiTerm}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="1yr">1 Year</SelectItem>
                  <SelectItem value="3yr">3 Year</SelectItem>
                </SelectContent>
              </Select>
              <Input type="number" placeholder="Count" value={riCount} onChange={e => setRiCount(parseInt(e.target.value) || 1)} min={1} />
            </div>
            <DialogFooter><Button onClick={purchaseReserved}>Purchase</Button></DialogFooter>
          </DialogContent>
        </Dialog>
        {budgets.length > 0 && (
          <Button variant="outline" onClick={loadData}>Refresh Data</Button>
        )}
      </div>

      {forecast && (
        <Card>
          <CardHeader><CardTitle>Forecast</CardTitle></CardHeader>
          <CardContent className="grid grid-cols-3 gap-4">
            <div><Label>Daily Average</Label><p className="text-xl font-bold">${forecast.daily_avg?.toFixed(2)}</p></div>
            <div><Label>Forecast Period</Label><p className="text-xl font-bold">{forecast.period_days || 30}d</p></div>
            <div><Label>Confidence</Label><p className="text-xl font-bold text-green-600">High</p></div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader><CardTitle>Cost by Provider</CardTitle></CardHeader>
        <CardContent>
          <Table>
            <TableHeader><TableRow><TableHead>Provider</TableHead><TableHead>Total Spend</TableHead><TableHead>Budgets</TableHead><TableHead>Anomalies</TableHead></TableRow></TableHeader>
            <TableBody>
              {['aws', 'azure', 'gcp', 'hetzner'].map(p => {
                const provAnomalies = anomalies.filter(a => a.provider === p).length;
                const provBudgets = budgets.filter(b => b.name?.toLowerCase().includes(p)).length;
                return (
                  <TableRow key={p}>
                    <TableCell className="font-medium">{p.toUpperCase()}</TableCell>
                    <TableCell>${(anomalies.filter(a => a.provider === p).reduce((s, a) => s + a.amount, 0) || 0).toFixed(2)}</TableCell>
                    <TableCell><Badge variant="outline">{provBudgets}</Badge></TableCell>
                    <TableCell><Badge variant={provAnomalies > 0 ? 'destructive' : 'default'}>{provAnomalies}</Badge></TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};

function BudgetFormDialog({ open, onOpenChange, onSubmit }: { open: boolean; onOpenChange: (v: boolean) => void; onSubmit: (data: any) => void }) {
  const [name, setName] = useState(''); const [amount, setAmount] = useState('1000'); const [provider, setProvider] = useState('all');
  return (
    <Dialog open={open} onOpenChange={onOpenChange}><DialogContent><DialogHeader><DialogTitle>Create Budget</DialogTitle></DialogHeader>
      <div className="space-y-4">
        <div><Label>Name</Label><Input value={name} onChange={e => setName(e.target.value)} /></div>
        <div><Label>Amount ($)</Label><Input type="number" value={amount} onChange={e => setAmount(e.target.value)} /></div>
        <div><Label>Provider</Label><Select value={provider} onValueChange={setProvider}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{['all','aws','azure','gcp','hetzner','ovh'].map(p => <SelectItem key={p} value={p}>{p.toUpperCase()}</SelectItem>)}</SelectContent></Select></div>
      </div>
      <DialogFooter><Button onClick={() => { onSubmit({ name, amount: parseFloat(amount), provider }); onOpenChange(false); }}>Create</Button></DialogFooter>
    </DialogContent></Dialog>
  );
}

function AnomalyAlertCard({ anomaly, onResolve }: { anomaly: any; onResolve: (id: string) => void }) {
  return (
    <Card className="border-red-200"><CardHeader className="pb-2"><div className="flex items-center justify-between"><CardTitle className="text-sm">{anomaly.provider}/{anomaly.service}</CardTitle><Badge variant="destructive">{anomaly.severity}</Badge></div></CardHeader>
    <CardContent><div className="text-sm space-y-1"><p>Actual: ${anomaly.amount?.toFixed(2)} | Expected: ${anomaly.expected_amount?.toFixed(2)}</p><p>Deviation: {(anomaly.deviation * 100).toFixed(1)}%</p></div>
    <Button variant="outline" size="sm" className="mt-2" onClick={() => onResolve(anomaly.id)}>Resolve</Button></CardContent></Card>
  );
}

function SpendTrendChart({ costs }: { costs: any[] }) {
  const byDay: Record<string, number> = {};
  costs.forEach((c: any) => { const d = c.recorded_at?.substring(0, 10); if (d) byDay[d] = (byDay[d] || 0) + (c.amount || 0); });
  const sorted = Object.entries(byDay).sort((a, b) => a[0].localeCompare(b[0])).slice(-14);
  const maxVal = Math.max(...sorted.map(s => s[1]), 1);
  return (
    <Card><CardHeader><CardTitle>Daily Spend (14d)</CardTitle></CardHeader>
    <CardContent><div className="space-y-1">{sorted.map(([d, amt]) => (
      <div key={d} className="flex items-center gap-2"><span className="text-xs w-20">{d.slice(5)}</span><div className="h-4 bg-primary rounded" style={{ width: `${(amt / maxVal) * 80 + 10}%` }} /><span className="text-xs w-16 text-right">${amt.toFixed(0)}</span></div>
    ))}</div></CardContent></Card>
  );
}

function ForecastCard({ totalSpend }: { totalSpend: number }) {
  const daily = totalSpend / 30;
  return (
    <Card><CardHeader><CardTitle>Forecast</CardTitle></CardHeader>
    <CardContent><div className="grid grid-cols-3 gap-4">
      <div><Label>Daily Avg</Label><p className="text-xl font-bold">${daily.toFixed(2)}</p></div>
      <div><Label>30-Day</Label><p className="text-xl font-bold">${(daily * 30).toFixed(2)}</p></div>
      <div><Label>Annualized</Label><p className="text-xl font-bold">${(daily * 365).toFixed(2)}</p></div>
    </div></CardContent></Card>
  );
}

function ProviderBreakdownTable({ costs }: { costs: any[] }) {
  const byP: Record<string, { total: number; count: number }> = {};
  costs.forEach((c: any) => { const p = c.provider || 'unknown'; if (!byP[p]) byP[p] = { total: 0, count: 0 }; byP[p].total += c.amount || 0; byP[p].count += 1; });
  return (
    <Card><CardHeader><CardTitle>Provider Breakdown</CardTitle></CardHeader>
    <CardContent><Table><TableHeader><TableRow><TableHead>Provider</TableHead><TableHead>Total</TableHead><TableHead>Records</TableHead><TableHead>Avg/Record</TableHead></TableRow></TableHeader>
    <TableBody>{Object.entries(byP).map(([p, d]) => (
      <TableRow key={p}><TableCell className="font-medium">{p.toUpperCase()}</TableCell><TableCell>${d.total.toFixed(2)}</TableCell><TableCell>{d.count}</TableCell><TableCell>${(d.total / d.count).toFixed(4)}</TableCell></TableRow>
    ))}</TableBody></Table></CardContent></Card>
  );
}

export default CloudCostControl;
