import { useEffect, useState } from 'react';
import { FormattedMessage } from 'react-intl';
import { apiClient } from '../../lib/api';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table';

interface Opportunity { id: string; source_provider: string; target_provider: string; savings_per_hour: number; savings_percentage: number; state: string; }
interface Migration { migration_id: string; source_provider: string; target_provider: string; state: string; started_at: string; }

export const CloudArbitrage = () => {
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [migrations, setMigrations] = useState<Migration[]>([]);
  const [loading, setLoading] = useState(true);
  const [totalSavings, setTotalSavings] = useState(0);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    try {
      const [oppData, migData, savings] = await Promise.all([
        apiClient.listArbitrageOpportunities(),
        apiClient.listArbitrageMigrations(),
        apiClient.getArbitrageSavings(),
      ]);
      setOpportunities(oppData || []); setMigrations(migData || []);
      setTotalSavings(savings?.total_savings_per_month || 0);
    } catch (e) { toast.error('Failed to load arbitrage data');
    } finally { setLoading(false); }
  };

  const executeMigration = async (oppId: string) => {
    try { await apiClient.executeArbitrageMigration(oppId); toast.success('Migration started'); loadData();
    } catch (e) { toast.error('Failed to start migration'); }
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>;

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold"><FormattedMessage id="cloudArbitrage.title" defaultMessage="Cloud Arbitrage Engine" /></h1>
          <p className="text-muted-foreground mt-1"><FormattedMessage id="cloudArbitrage.description" defaultMessage="Compare spot/preemptible pricing across providers" /></p>
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card><CardHeader><CardTitle><FormattedMessage id="cloudArbitrage.opportunities" defaultMessage="Opportunities" /></CardTitle></CardHeader>
          <CardContent><p className="text-3xl font-bold">{opportunities.length}</p></CardContent></Card>
        <Card><CardHeader><CardTitle><FormattedMessage id="cloudArbitrage.migrations" defaultMessage="Migrations" /></CardTitle></CardHeader>
          <CardContent><p className="text-3xl font-bold">{migrations.length}</p></CardContent></Card>
        <Card><CardHeader><CardTitle><FormattedMessage id="cloudArbitrage.savings" defaultMessage="Monthly Savings" /></CardTitle></CardHeader>
          <CardContent><p className="text-3xl font-bold text-green-500">${totalSavings.toFixed(2)}</p></CardContent></Card>
      </div>
      <Tabs defaultValue="opportunities">
        <TabsList><TabsTrigger value="opportunities">Opportunities</TabsTrigger><TabsTrigger value="migrations">Migrations</TabsTrigger></TabsList>
        <TabsContent value="opportunities">
          <Card><CardContent className="p-0">
            <Table><TableHeader><TableRow>
              <TableHead>Source</TableHead><TableHead>Target</TableHead><TableHead>Savings/hr</TableHead><TableHead>Savings %</TableHead><TableHead>Status</TableHead><TableHead>Actions</TableHead>
            </TableRow></TableHeader>
            <TableBody>{opportunities.map((o) => (
              <TableRow key={o.id}>
                <TableCell>{o.source_provider}</TableCell>
                <TableCell>{o.target_provider}</TableCell>
                <TableCell>${o.savings_per_hour?.toFixed(4)}</TableCell>
                <TableCell><Badge variant="default">{o.savings_percentage?.toFixed(1)}%</Badge></TableCell>
                <TableCell><Badge variant={o.state === 'opportunity_found' ? 'default' : 'secondary'}>{o.state}</Badge></TableCell>
                <TableCell><Button size="sm" onClick={() => executeMigration(o.id)} disabled={o.state !== 'opportunity_found'}>Migrate</Button></TableCell>
              </TableRow>
            ))}</TableBody></Table>
          </CardContent></Card>
        </TabsContent>
        <TabsContent value="migrations">
          <Card><CardContent className="p-0">
            <Table><TableHeader><TableRow>
              <TableHead>Migration ID</TableHead><TableHead>Source</TableHead><TableHead>Target</TableHead><TableHead>Status</TableHead><TableHead>Started</TableHead>
            </TableRow></TableHeader>
            <TableBody>{migrations.map((m) => (
              <TableRow key={m.migration_id}>
                <TableCell className="font-mono text-xs">{m.migration_id}</TableCell>
                <TableCell>{m.source_provider}</TableCell><TableCell>{m.target_provider}</TableCell>
                <TableCell><Badge variant={m.state === 'completed' ? 'default' : 'secondary'}>{m.state}</Badge></TableCell>
                <TableCell>{new Date(m.started_at).toLocaleString()}</TableCell>
              </TableRow>
            ))}</TableBody></Table>
          </CardContent></Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};
  const [showCompareDialog, setShowCompareDialog] = useState(false);
  const [compareVcpu, setCompareVcpu] = useState(2);
  const [compareMemory, setCompareMemory] = useState(4);
  const [compareRegion, setCompareRegion] = useState('us-east-1');
  const [compareResults, setCompareResults] = useState<any[]>([]);
  const [alertThreshold, setAlertThreshold] = useState(0.05);
  const [alerts, setAlerts] = useState<any[]>([]);

  const runCompare = async () => {
    try {
      const data = await apiClient.compareCloudPricing(compareVcpu, compareMemory, compareRegion);
      setCompareResults(data || []);
      toast.success('Price comparison complete');
    } catch { toast.error('Failed to compare pricing'); }
  };

  const setAlert = async () => {
    try {
      const result = await apiClient.createPricingAlert('aws', alertThreshold, compareRegion);
      setAlerts([...alerts, result]);
      toast.success('Pricing alert created');
    } catch { toast.error('Failed to create alert'); }
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="grid grid-cols-3 gap-4">
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Open Opportunities</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{opportunities.filter(o => o.state === 'open').length}</p></CardContent></Card>
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Completed Migrations</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{migrations.filter(m => m.state === 'completed').length}</p></CardContent></Card>
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Active Migrations</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{migrations.filter(m => m.state === 'in_progress').length}</p></CardContent></Card>
      </div>

      <Card>
        <CardHeader><CardTitle>Price Comparison</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-4">
            <div><Label>vCPU</Label><Input type="number" value={compareVcpu} onChange={e => setCompareVcpu(parseInt(e.target.value) || 2)} className="w-24" /></div>
            <div><Label>Memory (GB)</Label><Input type="number" value={compareMemory} onChange={e => setCompareMemory(parseInt(e.target.value) || 4)} className="w-24" /></div>
            <div><Label>Region</Label><Input value={compareRegion} onChange={e => setCompareRegion(e.target.value)} className="w-32" /></div>
            <div className="flex items-end"><Button onClick={runCompare}>Compare</Button></div>
          </div>
          {compareResults.length > 0 && (
            <Table>
              <TableHeader><TableRow>
                <TableHead>Provider</TableHead><TableHead>Price/hr</TableHead><TableHead>Region</TableHead><TableHead>Savings</TableHead>
              </TableRow></TableHeader>
              <TableBody>{compareResults.map((r, i) => (
                <TableRow key={i}>
                  <TableCell className="font-medium">{r.provider?.toUpperCase()}</TableCell>
                  <TableCell>${r.hourly_price?.toFixed(4)}</TableCell>
                  <TableCell>{r.region}</TableCell>
                  <TableCell>{i === 0 ? <Badge>Best Price</Badge> : <Badge variant="secondary">{(((r.hourly_price - compareResults[0].hourly_price) / compareResults[0].hourly_price) * 100).toFixed(0)}% more</Badge>}</TableCell>
                </TableRow>
              ))}</TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Pricing Alerts</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-4">
            <div><Label>Price Threshold ($/hr)</Label><Input type="number" value={alertThreshold} onChange={e => setAlertThreshold(parseFloat(e.target.value) || 0.05)} className="w-32" step={0.01} /></div>
            <div className="flex items-end"><Button onClick={setAlert}>Set Alert</Button></div>
          </div>
          <Table>
            <TableHeader><TableRow><TableHead>Provider</TableHead><TableHead>Threshold</TableHead><TableHead>Triggered</TableHead></TableRow></TableHeader>
            <TableBody>{alerts.map((a, i) => (
              <TableRow key={i}><TableCell>{a.provider}</TableCell><TableCell>${a.threshold?.toFixed(4)}</TableCell><TableCell>{a.triggered ? 'Yes' : 'No'}</TableCell></TableRow>
            ))}</TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};

  const [showBidDialog, setShowBidDialog] = useState(false);
  const [bidProvider, setBidProvider] = useState('aws');
  const [bidInstance, setBidInstance] = useState('t3.medium');
  const [bidMaxPrice, setBidMaxPrice] = useState(0.05);
  const [showSavingsPlanDialog, setShowSavingsPlanDialog] = useState(false);
  const [spProvider, setSpProvider] = useState('aws');
  const [spCommitment, setSpCommitment] = useState('1yr');
  const [spUpfront, setSpUpfront] = useState('partial');
  const [spotBids, setSpotBids] = useState<any[]>([]);
  const [savingsPlans, setSavingsPlans] = useState<any[]>([]);

  const createBid = async () => {
    try {
      const result = await apiClient.createSpotBid(bidProvider, bidInstance, bidMaxPrice);
      setSpotBids([...spotBids, result]);
      toast.success('Spot bid created');
      setShowBidDialog(false);
    } catch { toast.error('Failed to create bid'); }
  };

  const createSavingsPlan = async () => {
    try {
      const result = await apiClient.createSavingsPlan(spProvider, spCommitment, spUpfront);
      setSavingsPlans([...savingsPlans, result]);
      toast.success('Savings plan created');
      setShowSavingsPlanDialog(false);
    } catch { toast.error('Failed to create plan'); }
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="grid grid-cols-4 gap-4">
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Open Opportunities</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{opportunities.filter(o => o.state === 'opportunity_found' || o.state === 'open').length}</p></CardContent></Card>
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Spot Bids</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{spotBids.length}</p></CardContent></Card>
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Savings Plans</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{savingsPlans.length}</p></CardContent></Card>
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Monthly Savings</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold text-green-500">${totalSavings.toFixed(2)}</p></CardContent></Card>
      </div>

      <div className="flex gap-2">
        <Dialog open={showBidDialog} onOpenChange={setShowBidDialog}>
          <DialogTrigger asChild><Button>Create Spot Bid</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>Create Spot Bid</DialogTitle></DialogHeader>
            <div className="space-y-2">
              <Select value={bidProvider} onValueChange={setBidProvider}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="aws">AWS</SelectItem>
                  <SelectItem value="azure">Azure</SelectItem>
                  <SelectItem value="gcp">GCP</SelectItem>
                  <SelectItem value="hetzner">Hetzner</SelectItem>
                </SelectContent>
              </Select>
              <Input placeholder="Instance type" value={bidInstance} onChange={e => setBidInstance(e.target.value)} />
              <Input type="number" placeholder="Max bid ($/hr)" value={bidMaxPrice} onChange={e => setBidMaxPrice(parseFloat(e.target.value) || 0.05)} step={0.01} />
            </div>
            <DialogFooter><Button onClick={createBid}>Create Bid</Button></DialogFooter>
          </DialogContent>
        </Dialog>
        <Dialog open={showSavingsPlanDialog} onOpenChange={setShowSavingsPlanDialog}>
          <DialogTrigger asChild><Button variant="outline">Savings Plan</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>Create Savings Plan</DialogTitle></DialogHeader>
            <div className="space-y-2">
              <Select value={spProvider} onValueChange={setSpProvider}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="aws">AWS</SelectItem>
                  <SelectItem value="azure">Azure</SelectItem>
                  <SelectItem value="gcp">GCP</SelectItem>
                </SelectContent>
              </Select>
              <Select value={spCommitment} onValueChange={setSpCommitment}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="1yr">1 Year</SelectItem>
                  <SelectItem value="3yr">3 Year</SelectItem>
                </SelectContent>
              </Select>
              <Select value={spUpfront} onValueChange={setSpUpfront}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="partial">Partial Upfront</SelectItem>
                  <SelectItem value="all">All Upfront</SelectItem>
                  <SelectItem value="none">No Upfront</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <DialogFooter><Button onClick={createSavingsPlan}>Create Plan</Button></DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardHeader><CardTitle>Spot Bids</CardTitle></CardHeader>
        <CardContent>
          <Table>
            <TableHeader><TableRow><TableHead>Provider</TableHead><TableHead>Instance</TableHead><TableHead>Max Bid</TableHead><TableHead>Status</TableHead></TableRow></TableHeader>
            <TableBody>{spotBids.map((b, i) => (
              <TableRow key={i}>
                <TableCell className="font-medium">{b.provider?.toUpperCase()}</TableCell>
                <TableCell>{b.instance_type}</TableCell>
                <TableCell>${b.max_bid?.toFixed(4)}</TableCell>
                <TableCell><Badge variant={b.status === 'active' ? 'default' : 'secondary'}>{b.status || 'active'}</Badge></TableCell>
              </TableRow>
            ))}</TableBody>
          </Table>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Savings Plans</CardTitle></CardHeader>
        <CardContent>
          <Table>
            <TableHeader><TableRow><TableHead>Provider</TableHead><TableHead>Commitment</TableHead><TableHead>Upfront</TableHead><TableHead>Discount</TableHead></TableRow></TableHeader>
            <TableBody>{savingsPlans.map((p, i) => (
              <TableRow key={i}>
                <TableCell className="font-medium">{p.provider?.toUpperCase()}</TableCell>
                <TableCell>{p.commitment}</TableCell>
                <TableCell>{p.upfront}</TableCell>
                <TableCell><Badge variant="default">{p.discount_pct}%</Badge></TableCell>
              </TableRow>
            ))}</TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};

function OpportunityCard({ opportunity, onExecute, onDismiss }: { opportunity: any; onExecute: (id: string) => void; onDismiss: (id: string) => void }) {
  return (
    <Card className="border-green-200"><CardHeader className="pb-2"><div className="flex items-center justify-between"><CardTitle className="text-sm">{opportunity.source_provider?.toUpperCase()} → {opportunity.target_provider?.toUpperCase()}</CardTitle><Badge variant={opportunity.state === 'opportunity_found' ? 'default' : 'secondary'}>{opportunity.state}</Badge></div></CardHeader>
    <CardContent><div className="text-sm space-y-1"><p>Savings: ${opportunity.savings_per_hour?.toFixed(4)}/h ({opportunity.savings_percentage?.toFixed(1)}%)</p><p>Region: {opportunity.region} | Resource: {opportunity.resource_id?.substring(0, 12)}</p></div>
    <div className="flex gap-2 mt-2">{opportunity.state === 'opportunity_found' && <Button size="sm" onClick={() => onExecute(opportunity.id)}>Execute</Button>}<Button variant="outline" size="sm" onClick={() => onDismiss(opportunity.id)}>Dismiss</Button></div></CardContent></Card>
  );
}

function PricingTable({ snapshots }: { snapshots: any[] }) {
  const sorted = [...snapshots].sort((a, b) => a.hourly_price - b.hourly_price);
  return (
    <Card><CardHeader><CardTitle>Pricing Comparison</CardTitle></CardHeader>
    <CardContent><Table><TableHeader><TableRow><TableHead>Provider</TableHead><TableHead>Type</TableHead><TableHead>Region</TableHead><TableHead>Price/h</TableHead><TableHead>vCPU</TableHead><TableHead>RAM</TableHead></TableRow></TableHeader>
    <TableBody>{sorted.slice(0, 20).map((s: any, i: number) => (
      <TableRow key={i}><TableCell className="font-medium">{s.provider?.toUpperCase()}</TableCell><TableCell><Badge variant="outline">{s.instance_type}</Badge></TableCell><TableCell>{s.region}</TableCell><TableCell className="font-mono">${s.hourly_price?.toFixed(4)}</TableCell><TableCell>{s.vcpu}</TableCell><TableCell>{s.memory_gb} GB</TableCell></TableRow>
    ))}</TableBody></Table></CardContent></Card>
  );
}

function SavingsSummary({ opportunities, migrations }: { opportunities: any[]; migrations: any[] }) {
  const totalSavings = migrations.filter((m: any) => m.state === 'completed').reduce((s: number, m: any) => s + (m.expected_savings_per_hour || 0), 0);
  const openOpps = opportunities.filter((o: any) => o.state === 'opportunity_found').length;
  return (
    <div className="grid grid-cols-4 gap-4 mb-6">
      <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Total Savings/h</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold text-green-600">${totalSavings.toFixed(4)}</p></CardContent></Card>
      <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Monthly Savings</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">${(totalSavings * 730).toFixed(2)}</p></CardContent></Card>
      <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Open Opportunities</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{openOpps}</p></CardContent></Card>
      <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Migrations</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{migrations.length}</p></CardContent></Card>
    </div>
  );
}

function MigrationTimeline({ migrations }: { migrations: any[] }) {
  const sorted = [...migrations].sort((a, b) => new Date(b.started_at || 0).getTime() - new Date(a.started_at || 0).getTime()).slice(0, 10);
  return (
    <Card><CardHeader><CardTitle>Migration History</CardTitle></CardHeader>
    <CardContent><Table><TableHeader><TableRow><TableHead>Source</TableHead><TableHead>Target</TableHead><TableHead>State</TableHead><TableHead>Started</TableHead></TableRow></TableHeader>
    <TableBody>{sorted.map((m: any, i: number) => (
      <TableRow key={i}><TableCell>{m.source_provider?.toUpperCase()}</TableCell><TableCell>{m.target_provider?.toUpperCase()}</TableCell><TableCell><Badge variant={m.state === 'completed' ? 'default' : m.state === 'failed' ? 'destructive' : 'secondary'}>{m.state}</Badge></TableCell><TableCell className="text-xs">{new Date(m.started_at).toLocaleString()}</TableCell></TableRow>
    ))}</TableBody></Table></CardContent></Card>
  );
}

function ProviderFilterPills({ providers, selected, onChange }: { providers: string[]; selected: string; onChange: (v: string) => void }) {
  return (
    <div className="flex flex-wrap gap-2 mb-4">{['all', ...providers].map(p => (
      <Button key={p} variant={selected === p ? 'default' : 'outline'} size="sm" onClick={() => onChange(p)}>{p === 'all' ? 'All' : p.toUpperCase()}</Button>
    ))}</div>
  );
}

export default CloudArbitrage;
