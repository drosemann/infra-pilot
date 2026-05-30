import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Thermometer, Snowflake, Flame, ArrowUpDown, Plus, Trash2, DollarSign, Activity } from 'lucide-react';

interface StorageTier {
  tier_id: string;
  name: string;
  tier_type: string;
  priority: number;
  cost_per_gb: number;
  total_capacity: number;
  used_capacity: number;
  usage_percent: number;
}

interface TieringPolicy {
  policy_id: string;
  name: string;
  source_tier: string;
  target_tier: string;
  conditions: Record<string, any>;
  enabled: boolean;
  last_run: string | null;
  bytes_moved: number;
}

const mockTiers: StorageTier[] = [
  { tier_id: 'hot', name: 'Hot Storage', tier_type: 'nvme', priority: 1, cost_per_gb: 0.10, total_capacity: 1099511627776, used_capacity: 659706976665, usage_percent: 60 },
  { tier_id: 'warm', name: 'Warm Storage', tier_type: 'ssd', priority: 2, cost_per_gb: 0.05, total_capacity: 5497558138880, used_capacity: 2199023255552, usage_percent: 40 },
  { tier_id: 'cold', name: 'Cold Storage', tier_type: 'hdd', priority: 3, cost_per_gb: 0.02, total_capacity: 10995116277760, used_capacity: 2199023255552, usage_percent: 20 },
  { tier_id: 'glacier', name: 'Glacier Archive', tier_type: 'tape', priority: 4, cost_per_gb: 0.005, total_capacity: 54975581388800, used_capacity: 2748779069440, usage_percent: 5 },
];

const mockPolicies: TieringPolicy[] = [
  { policy_id: 'pol-1', name: 'Idle Data to Cold', source_tier: 'hot', target_tier: 'cold', conditions: { last_accessed_days: 30 }, enabled: true, last_run: '2024-05-28T06:00:00Z', bytes_moved: 107374182400 },
  { policy_id: 'pol-2', name: 'Archive Old Logs', source_tier: 'warm', target_tier: 'glacier', conditions: { last_accessed_days: 90, file_types: ['.log', '.out'] }, enabled: true, last_run: '2024-05-27T06:00:00Z', bytes_moved: 53687091200 },
  { policy_id: 'pol-3', name: 'Large Files to Warm', source_tier: 'hot', target_tier: 'warm', conditions: { min_size_mb: 1024, last_accessed_days: 7 }, enabled: false, last_run: null, bytes_moved: 0 },
];

const getTierIcon = (type: string) => {
  switch (type) {
    case 'nvme': return <Flame className="h-5 w-5 text-red-500" />;
    case 'ssd': return <Activity className="h-5 w-5 text-yellow-500" />;
    case 'hdd': return <Thermometer className="h-5 w-5 text-blue-500" />;
    case 'tape': return <Snowflake className="h-5 w-5 text-cyan-500" />;
    default: return <HardDrive className="h-5 w-5" />;
  }
};

import { HardDrive } from 'lucide-react';

const StorageTieringPolicies: React.FC = () => {
  const [tiers] = useState<StorageTier[]>(mockTiers);
  const [policies, setPolicies] = useState<TieringPolicy[]>(mockPolicies);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [newPolicyName, setNewPolicyName] = useState('');
  const [newPolicySource, setNewPolicySource] = useState('hot');
  const [newPolicyTarget, setNewPolicyTarget] = useState('cold');
  const [newPolicyDays, setNewPolicyDays] = useState(30);

  const totalMonthlyCost = tiers.reduce((sum, t) => sum + (t.used_capacity / (1024**3)) * t.cost_per_gb, 0);
  const hotOnlyCost = (tiers.reduce((sum, t) => sum + t.used_capacity, 0) / (1024**3)) * 0.10;
  const monthlySavings = hotOnlyCost - totalMonthlyCost;

  const handleCreatePolicy = () => {
    const policy: TieringPolicy = {
      policy_id: `pol-${Date.now()}`,
      name: newPolicyName,
      source_tier: newPolicySource,
      target_tier: newPolicyTarget,
      conditions: { last_accessed_days: newPolicyDays },
      enabled: true,
      last_run: null,
      bytes_moved: 0,
    };
    setPolicies([...policies, policy]);
    setIsCreateOpen(false);
    setNewPolicyName('');
  };

  const togglePolicy = (policyId: string) => {
    setPolicies(policies.map(p => p.policy_id === policyId ? { ...p, enabled: !p.enabled } : p));
  };

  const deletePolicy = (policyId: string) => {
    setPolicies(policies.filter(p => p.policy_id !== policyId));
  };

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Storage Tiering Policies</h1>
          <p className="text-muted-foreground">Auto-move data between hot/warm/cold tiers based on access frequency</p>
        </div>
        <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              Create Policy
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create Tiering Policy</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label>Policy Name</Label>
                <Input value={newPolicyName} onChange={e => setNewPolicyName(e.target.value)} placeholder="Idle Data Policy" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Source Tier</Label>
                  <select className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm" value={newPolicySource} onChange={e => setNewPolicySource(e.target.value)}>
                    <option value="hot">Hot (NVMe)</option>
                    <option value="warm">Warm (SSD)</option>
                    <option value="cold">Cold (HDD)</option>
                  </select>
                </div>
                <div>
                  <Label>Target Tier</Label>
                  <select className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm" value={newPolicyTarget} onChange={e => setNewPolicyTarget(e.target.value)}>
                    <option value="warm">Warm (SSD)</option>
                    <option value="cold">Cold (HDD)</option>
                    <option value="glacier">Glacier (Tape)</option>
                  </select>
                </div>
              </div>
              <div>
                <Label>Move after N days without access</Label>
                <Input type="number" value={newPolicyDays} onChange={e => setNewPolicyDays(parseInt(e.target.value) || 30)} min={1} />
              </div>
              <Button onClick={handleCreatePolicy} className="w-full" disabled={!newPolicyName}>Create Policy</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Monthly Storage Cost</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${totalMonthlyCost.toFixed(2)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Hot-Only Cost (est.)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${hotOnlyCost.toFixed(2)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Monthly Savings</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-500">${monthlySavings.toFixed(2)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Savings %</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{((monthlySavings / hotOnlyCost) * 100).toFixed(1)}%</div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="tiers">
        <TabsList>
          <TabsTrigger value="tiers">Storage Tiers</TabsTrigger>
          <TabsTrigger value="policies">Tiering Policies</TabsTrigger>
          <TabsTrigger value="savings">Cost Savings</TabsTrigger>
        </TabsList>

        <TabsContent value="tiers">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {tiers.map(tier => (
              <Card key={tier.tier_id}>
                <CardHeader>
                  <div className="flex items-center gap-2">
                    {getTierIcon(tier.tier_type)}
                    <CardTitle className="text-lg">{tier.name}</CardTitle>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div>
                    <div className="flex justify-between mb-1">
                      <span className="text-xs text-muted-foreground">Usage</span>
                      <span className="text-xs font-medium">{tier.usage_percent}%</span>
                    </div>
                    <Progress value={tier.usage_percent} />
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>
                      <p className="text-muted-foreground">Type</p>
                      <p className="font-medium">{tier.tier_type.toUpperCase()}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Cost</p>
                      <p className="font-medium">${tier.cost_per_gb}/GB</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Used</p>
                      <p className="font-medium">{(tier.used_capacity / (1024**3)).toFixed(0)} GB</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Total</p>
                      <p className="font-medium">{(tier.total_capacity / (1024**3)).toFixed(0)} GB</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="policies">
          <Card>
            <CardHeader>
              <CardTitle>Active Policies</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Source → Target</TableHead>
                    <TableHead>Conditions</TableHead>
                    <TableHead>Data Moved</TableHead>
                    <TableHead>Enabled</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {policies.map(policy => (
                    <TableRow key={policy.policy_id}>
                      <TableCell className="font-medium">{policy.name}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{policy.source_tier}</Badge>
                        <ArrowUpDown className="h-3 w-3 mx-1 inline" />
                        <Badge variant="outline">{policy.target_tier}</Badge>
                      </TableCell>
                      <TableCell className="text-xs">
                        {Object.entries(policy.conditions).map(([k, v]) => (
                          <div key={k}>{k.replace(/_/g, ' ')}: {Array.isArray(v) ? v.join(', ') : v}</div>
                        ))}
                      </TableCell>
                      <TableCell>{(policy.bytes_moved / (1024**3)).toFixed(1)} GB</TableCell>
                      <TableCell>
                        <Switch checked={policy.enabled} onCheckedChange={() => togglePolicy(policy.policy_id)} />
                      </TableCell>
                      <TableCell>
                        <Button variant="destructive" size="sm" onClick={() => deletePolicy(policy.policy_id)}>
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="savings">
          <Card>
            <CardHeader>
              <CardTitle>Cost Savings Breakdown</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="p-4 rounded-lg bg-muted">
                    <p className="text-sm text-muted-foreground">Without Tiering</p>
                    <p className="text-3xl font-bold">${hotOnlyCost.toFixed(2)}</p>
                    <p className="text-xs text-muted-foreground">est. monthly cost if all on hot tier</p>
                  </div>
                  <div className="p-4 rounded-lg bg-muted">
                    <p className="text-sm text-muted-foreground">With Tiering</p>
                    <p className="text-3xl font-bold">${totalMonthlyCost.toFixed(2)}</p>
                    <p className="text-xs text-muted-foreground">current monthly cost with tiering</p>
                  </div>
                  <div className="p-4 rounded-lg bg-green-50 dark:bg-green-950">
                    <p className="text-sm text-green-600 dark:text-green-400">Monthly Savings</p>
                    <p className="text-3xl font-bold text-green-600 dark:text-green-400">${monthlySavings.toFixed(2)}</p>
                    <p className="text-xs text-green-600 dark:text-green-400">{((monthlySavings / hotOnlyCost) * 100).toFixed(1)}% reduction</p>
                  </div>
                </div>
                <Separator />
                <h4 className="font-medium">Per-Tier Breakdown</h4>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Tier</TableHead>
                      <TableHead>Capacity</TableHead>
                      <TableHead>Cost/GB</TableHead>
                      <TableHead>Monthly Cost</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {tiers.map(tier => (
                      <TableRow key={tier.tier_id}>
                        <TableCell>{tier.name}</TableCell>
                        <TableCell>{(tier.used_capacity / (1024**3)).toFixed(0)} GB</TableCell>
                        <TableCell>${tier.cost_per_gb}</TableCell>
                        <TableCell>${((tier.used_capacity / (1024**3)) * tier.cost_per_gb).toFixed(2)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default StorageTieringPolicies;
