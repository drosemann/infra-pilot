import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FormattedMessage, useIntl } from 'react-intl';
import { apiClient } from '../../lib/api';
import { toast } from 'sonner';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Badge } from '../../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '../../components/ui/dialog';
import { Label } from '../../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';

interface CloudResource {
  id: string;
  provider: string;
  type: string;
  name: string;
  region: string;
  status: string;
  cost_per_hour: number;
  created_at: string;
}

interface ProviderScore {
  provider: string;
  overall: number;
  cost_score: number;
  latency_score: number;
  availability_score: number;
}

export const MultiCloudBroker = () => {
  const intl = useIntl();
  const navigate = useNavigate();
  const [resources, setResources] = useState<CloudResource[]>([]);
  const [providers, setProviders] = useState<string[]>(['aws', 'azure', 'gcp', 'hetzner', 'ovh', 'digitalocean']);
  const [loading, setLoading] = useState(true);
  const [showProvisionDialog, setShowProvisionDialog] = useState(false);
  const [newProvider, setNewProvider] = useState('aws');
  const [newType, setNewType] = useState('compute');
  const [newName, setNewName] = useState('');
  const [newRegion, setNewRegion] = useState('us-east-1');
  const [newCount, setNewCount] = useState(1);
  const [scores, setScores] = useState<ProviderScore[]>([]);

  useEffect(() => {
    loadResources();
  }, []);

  const loadResources = async () => {
    try {
      const data = await apiClient.listCloudResources();
      setResources(data || []);
    } catch (error) {
      toast.error('Failed to load cloud resources');
    } finally {
      setLoading(false);
    }
  };

  const provisionResource = async () => {
    try {
      const result = await apiClient.provisionCloudResource({
        provider: newProvider,
        type: newType,
        name: newName,
        region: newRegion,
        count: newCount,
      });
      setResources([...resources, result]);
      toast.success('Resource provisioning started');
      setShowProvisionDialog(false);
      setNewName('');
    } catch (error) {
      toast.error('Failed to provision resource');
    }
  };

  const deleteResource = async (id: string) => {
    try {
      await apiClient.deleteCloudResource(id);
      setResources(resources.filter((r) => r.id !== id));
      toast.success('Resource deleted');
    } catch (error) {
      toast.error('Failed to delete resource');
    }
  };

  const scoreProviders = async () => {
    try {
      const data = await apiClient.scoreCloudProviders();
      setScores(data || []);
    } catch (error) {
      toast.error('Failed to score providers');
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>;
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold"><FormattedMessage id="multiCloudBroker.title" defaultMessage="Multi-Cloud Resource Broker" /></h1>
          <p className="text-muted-foreground mt-1"><FormattedMessage id="multiCloudBroker.description" defaultMessage="Manage cloud resources across providers" /></p>
        </div>
      </div>

      <Tabs defaultValue="resources">
        <TabsList>
          <TabsTrigger value="resources"><FormattedMessage id="multiCloudBroker.resources" defaultMessage="Resources" /></TabsTrigger>
          <TabsTrigger value="providers"><FormattedMessage id="multiCloudBroker.providers" defaultMessage="Providers" /></TabsTrigger>
          <TabsTrigger value="scores"><FormattedMessage id="multiCloudBroker.scores" defaultMessage="Provider Scores" /></TabsTrigger>
        </TabsList>

        <TabsContent value="resources" className="space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-semibold"><FormattedMessage id="multiCloudBroker.cloudResources" defaultMessage="Cloud Resources" /></h2>
            <Dialog open={showProvisionDialog} onOpenChange={setShowProvisionDialog}>
              <DialogTrigger asChild>
                <Button><FormattedMessage id="multiCloudBroker.provision" defaultMessage="Provision Resource" /></Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle><FormattedMessage id="multiCloudBroker.provisionResource" defaultMessage="Provision Resource" /></DialogTitle>
                  <DialogDescription><FormattedMessage id="multiCloudBroker.provisionDesc" defaultMessage="Provision a new cloud resource" /></DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                  <div>
                    <Label><FormattedMessage id="multiCloudBroker.provider" defaultMessage="Provider" /></Label>
                    <Select value={newProvider} onValueChange={setNewProvider}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        {providers.map((p) => (<SelectItem key={p} value={p}>{p.toUpperCase()}</SelectItem>))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label><FormattedMessage id="multiCloudBroker.type" defaultMessage="Type" /></Label>
                    <Select value={newType} onValueChange={setNewType}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="compute">Compute</SelectItem>
                        <SelectItem value="storage">Storage</SelectItem>
                        <SelectItem value="network">Network</SelectItem>
                        <SelectItem value="database">Database</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label><FormattedMessage id="common.name" defaultMessage="Name" /></Label>
                    <Input value={newName} onChange={(e) => setNewName(e.target.value)} placeholder="my-resource" />
                  </div>
                  <div>
                    <Label><FormattedMessage id="multiCloudBroker.region" defaultMessage="Region" /></Label>
                    <Input value={newRegion} onChange={(e) => setNewRegion(e.target.value)} placeholder="us-east-1" />
                  </div>
                  <div>
                    <Label><FormattedMessage id="multiCloudBroker.count" defaultMessage="Count" /></Label>
                    <Input type="number" value={newCount} onChange={(e) => setNewCount(parseInt(e.target.value) || 1)} min={1} max={100} />
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setShowProvisionDialog(false)}><FormattedMessage id="common.cancel" defaultMessage="Cancel" /></Button>
                  <Button onClick={provisionResource}><FormattedMessage id="multiCloudBroker.provision" defaultMessage="Provision" /></Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead><FormattedMessage id="common.name" defaultMessage="Name" /></TableHead>
                    <TableHead><FormattedMessage id="multiCloudBroker.provider" defaultMessage="Provider" /></TableHead>
                    <TableHead><FormattedMessage id="multiCloudBroker.type" defaultMessage="Type" /></TableHead>
                    <TableHead><FormattedMessage id="multiCloudBroker.region" defaultMessage="Region" /></TableHead>
                    <TableHead><FormattedMessage id="common.status" defaultMessage="Status" /></TableHead>
                    <TableHead><FormattedMessage id="multiCloudBroker.cost" defaultMessage="Cost/hr" /></TableHead>
                    <TableHead><FormattedMessage id="common.actions" defaultMessage="Actions" /></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {resources.map((r) => (
                    <TableRow key={r.id}>
                      <TableCell className="font-medium">{r.name}</TableCell>
                      <TableCell><Badge variant="outline">{r.provider.toUpperCase()}</Badge></TableCell>
                      <TableCell>{r.type}</TableCell>
                      <TableCell>{r.region}</TableCell>
                      <TableCell><Badge variant={r.status === 'running' ? 'default' : 'secondary'}>{r.status}</Badge></TableCell>
                      <TableCell>${r.cost_per_hour?.toFixed(4)}</TableCell>
                      <TableCell><Button variant="destructive" size="sm" onClick={() => deleteResource(r.id)}><FormattedMessage id="common.delete" defaultMessage="Delete" /></Button></TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="providers" className="space-y-4">
          <Card>
            <CardHeader><CardTitle><FormattedMessage id="multiCloudBroker.configuredProviders" defaultMessage="Configured Providers" /></CardTitle></CardHeader>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead><FormattedMessage id="common.name" defaultMessage="Provider" /></TableHead>
                    <TableHead><FormattedMessage id="common.status" defaultMessage="Status" /></TableHead>
                    <TableHead><FormattedMessage id="multiCloudBroker.region" defaultMessage="Region" /></TableHead>
                    <TableHead><FormattedMessage id="multiCloudBroker.regions" defaultMessage="Regions" /></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {providers.map((p) => (
                    <TableRow key={p}>
                      <TableCell className="font-medium">{p.toUpperCase()}</TableCell>
                      <TableCell><Badge variant="default">Connected</Badge></TableCell>
                      <TableCell>us-east-1</TableCell>
                      <TableCell>15-60</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="scores" className="space-y-4">
          <div className="flex justify-between">
            <h2 className="text-xl font-semibold"><FormattedMessage id="multiCloudBroker.providerScores" defaultMessage="Provider Scores" /></h2>
            <Button onClick={scoreProviders}><FormattedMessage id="multiCloudBroker.score" defaultMessage="Score Providers" /></Button>
          </div>
          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead><FormattedMessage id="multiCloudBroker.provider" defaultMessage="Provider" /></TableHead>
                    <TableHead><FormattedMessage id="multiCloudBroker.overall" defaultMessage="Overall" /></TableHead>
                    <TableHead><FormattedMessage id="multiCloudBroker.costScore" defaultMessage="Cost" /></TableHead>
                    <TableHead><FormattedMessage id="multiCloudBroker.latencyScore" defaultMessage="Latency" /></TableHead>
                    <TableHead><FormattedMessage id="multiCloudBroker.availabilityScore" defaultMessage="Availability" /></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {scores.map((s) => (
                    <TableRow key={s.provider}>
                      <TableCell className="font-medium">{s.provider.toUpperCase()}</TableCell>
                      <TableCell><Badge variant={s.overall >= 80 ? 'default' : 'secondary'}>{s.overall}</Badge></TableCell>
                      <TableCell>{s.cost_score}</TableCell>
                      <TableCell>{s.latency_score}</TableCell>
                      <TableCell>{s.availability_score}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

  const [filterProvider, setFilterProvider] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [pagination, setPagination] = useState({ page: 1, pageSize: 10 });
  const [showFailoverDialog, setShowFailoverDialog] = useState(false);
  const [failoverResource, setFailoverResource] = useState('');
  const [costSummary, setCostSummary] = useState({ total_cost_per_hour: 0, total_cost_per_day: 0, total_cost_per_month: 0 });
  const [searchQuery, setSearchQuery] = useState('');

  const loadCostSummary = async () => {
    try {
      const data = await apiClient.getCloudCostSummary();
      setCostSummary(data || { total_cost_per_hour: 0, total_cost_per_day: 0, total_cost_per_month: 0 });
    } catch { toast.error('Failed to load cost summary'); }
  };

  const filteredResources = resources.filter(r => {
    if (filterProvider && r.provider !== filterProvider) return false;
    if (filterStatus && r.status !== filterStatus) return false;
    if (searchQuery && !r.name.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  const paginatedResources = filteredResources.slice(
    (pagination.page - 1) * pagination.pageSize,
    pagination.page * pagination.pageSize
  );

  const executeFailover = async () => {
    try {
      await apiClient.failoverCloudResource(failoverResource);
      toast.success('Failover initiated');
      setShowFailoverDialog(false);
      await loadResources();
    } catch { toast.error('Failover failed'); }
  };

  const batchDelete = async () => {
    if (!window.confirm('Delete all filtered resources?')) return;
    try {
      await apiClient.batchDeleteCloudResources(filteredResources.map(r => r.id));
      toast.success('Batch delete initiated');
      await loadResources();
    } catch { toast.error('Batch delete failed'); }
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex items-center gap-4">
        <Input
          placeholder="Search resources..."
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
          className="max-w-sm"
        />
        <Select value={filterProvider} onValueChange={setFilterProvider}>
          <SelectTrigger className="w-[180px]"><SelectValue placeholder="All Providers" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="">All Providers</SelectItem>
            {providers.map(p => <SelectItem key={p} value={p}>{p.toUpperCase()}</SelectItem>)}
          </SelectContent>
        </Select>
        <Select value={filterStatus} onValueChange={setFilterStatus}>
          <SelectTrigger className="w-[180px]"><SelectValue placeholder="All Status" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="">All Status</SelectItem>
            <SelectItem value="running">Running</SelectItem>
            <SelectItem value="provisioning">Provisioning</SelectItem>
            <SelectItem value="stopped">Stopped</SelectItem>
            <SelectItem value="failed">Failed</SelectItem>
          </SelectContent>
        </Select>
        {filteredResources.length > 0 && (
          <Button variant="destructive" size="sm" onClick={batchDelete}>
            Delete {filteredResources.length} Resources
          </Button>
        )}
      </div>

      <div className="grid grid-cols-4 gap-4">
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Total Resources</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{resources.length}</p></CardContent></Card>
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Cost/hr</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">${costSummary.total_cost_per_hour.toFixed(4)}</p></CardContent></Card>
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Cost/day</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">${costSummary.total_cost_per_day.toFixed(2)}</p></CardContent></Card>
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Cost/month</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">${costSummary.total_cost_per_month.toFixed(2)}</p></CardContent></Card>
      </div>

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Provider</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Region</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Cost/hr</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {paginatedResources.map(r => (
                <TableRow key={r.id}>
                  <TableCell className="font-medium">{r.name}</TableCell>
                  <TableCell><Badge variant="outline">{r.provider.toUpperCase()}</Badge></TableCell>
                  <TableCell>{r.type}</TableCell>
                  <TableCell>{r.region}</TableCell>
                  <TableCell>
                    <Badge variant={
                      r.status === 'running' ? 'default' :
                      r.status === 'failed' ? 'destructive' : 'secondary'
                    }>{r.status}</Badge>
                  </TableCell>
                  <TableCell>${r.cost_per_hour?.toFixed(4)}</TableCell>
                  <TableCell className="flex gap-1">
                    <Button variant="outline" size="sm" onClick={() => navigate(`/cloud/resource/${r.id}`)}>View</Button>
                    <Button variant="destructive" size="sm" onClick={() => deleteResource(r.id)}>Delete</Button>
                    <Button variant="secondary" size="sm" onClick={() => { setFailoverResource(r.id); setShowFailoverDialog(true); }}>Failover</Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          <div className="flex items-center justify-between p-4">
            <p className="text-sm text-muted-foreground">Showing {paginatedResources.length} of {filteredResources.length}</p>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" disabled={pagination.page <= 1} onClick={() => setPagination(p => ({ ...p, page: p.page - 1 }))}>Previous</Button>
              <Button variant="outline" size="sm" disabled={pagination.page * pagination.pageSize >= filteredResources.length} onClick={() => setPagination(p => ({ ...p, page: p.page + 1 }))}>Next</Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <Dialog open={showFailoverDialog} onOpenChange={setShowFailoverDialog}>
        <DialogContent>
          <DialogHeader><DialogTitle>Failover Resource</DialogTitle><DialogDescription>Failover resource {failoverResource} to backup provider</DialogDescription></DialogHeader>
          <DialogFooter><Button variant="outline" onClick={() => setShowFailoverDialog(false)}>Cancel</Button><Button variant="destructive" onClick={executeFailover}>Execute Failover</Button></DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

  const [showSnapshotDialog, setShowSnapshotDialog] = useState(false);
  const [snapshotResourceId, setSnapshotResourceId] = useState('');
  const [snapshots, setSnapshots] = useState<any[]>([]);
  const [showTagDialog, setShowTagDialog] = useState(false);
  const [tagResourceId, setTagResourceId] = useState('');
  const [tagKey, setTagKey] = useState('');
  const [tagValue, setTagValue] = useState('');
  const [showScheduleDialog, setShowScheduleDialog] = useState(false);
  const [schedResourceId, setSchedResourceId] = useState('');
  const [schedAction, setSchedAction] = useState('stop');
  const [schedCron, setSchedCron] = useState('0 0 * * *');

  const createSnapshot = async () => {
    try {
      const result = await apiClient.snapshotCloudResource(snapshotResourceId);
      setSnapshots([...snapshots, result]);
      toast.success('Snapshot created');
      setShowSnapshotDialog(false);
    } catch { toast.error('Failed to create snapshot'); }
  };

  const addTag = async () => {
    try {
      await apiClient.tagCloudResource(tagResourceId, tagKey, tagValue);
      toast.success('Tag added');
      setShowTagDialog(false);
    } catch { toast.error('Failed to add tag'); }
  };

  const scheduleAction = async () => {
    try {
      await apiClient.scheduleCloudAction(schedResourceId, schedAction, schedCron);
      toast.success('Action scheduled');
      setShowScheduleDialog(false);
    } catch { toast.error('Failed to schedule action'); }
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="grid grid-cols-4 gap-4">
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Resources</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{resources.length}</p></CardContent></Card>
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Snapshots</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{snapshots.length}</p></CardContent></Card>
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Providers</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{providers.length}</p></CardContent></Card>
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Cost/hr</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">${resources.reduce((s, r) => s + (r.cost_per_hour || 0), 0).toFixed(4)}</p></CardContent></Card>
      </div>

      <div className="flex gap-2 flex-wrap">
        <Dialog open={showSnapshotDialog} onOpenChange={setShowSnapshotDialog}>
          <DialogTrigger asChild><Button variant="outline">Take Snapshot</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>Take Resource Snapshot</DialogTitle></DialogHeader>
            <Input placeholder="Resource ID" value={snapshotResourceId} onChange={e => setSnapshotResourceId(e.target.value)} />
            <DialogFooter><Button onClick={createSnapshot}>Snapshot</Button></DialogFooter>
          </DialogContent>
        </Dialog>
        <Dialog open={showTagDialog} onOpenChange={setShowTagDialog}>
          <DialogTrigger asChild><Button variant="outline">Tag Resource</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>Tag Resource</DialogTitle></DialogHeader>
            <div className="space-y-2">
              <Input placeholder="Resource ID" value={tagResourceId} onChange={e => setTagResourceId(e.target.value)} />
              <Input placeholder="Tag key" value={tagKey} onChange={e => setTagKey(e.target.value)} />
              <Input placeholder="Tag value" value={tagValue} onChange={e => setTagValue(e.target.value)} />
            </div>
            <DialogFooter><Button onClick={addTag}>Add Tag</Button></DialogFooter>
          </DialogContent>
        </Dialog>
        <Dialog open={showScheduleDialog} onOpenChange={setShowScheduleDialog}>
          <DialogTrigger asChild><Button variant="outline">Schedule Action</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>Schedule Resource Action</DialogTitle></DialogHeader>
            <div className="space-y-2">
              <Input placeholder="Resource ID" value={schedResourceId} onChange={e => setSchedResourceId(e.target.value)} />
              <Select value={schedAction} onValueChange={setSchedAction}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="start">Start</SelectItem>
                  <SelectItem value="stop">Stop</SelectItem>
                  <SelectItem value="restart">Restart</SelectItem>
                  <SelectItem value="snapshot">Snapshot</SelectItem>
                </SelectContent>
              </Select>
              <Input placeholder="Cron expression" value={schedCron} onChange={e => setSchedCron(e.target.value)} />
            </div>
            <DialogFooter><Button onClick={scheduleAction}>Schedule</Button></DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardHeader><CardTitle>Provider Comparison</CardTitle></CardHeader>
        <CardContent>
          <Table>
            <TableHeader><TableRow><TableHead>Provider</TableHead><TableHead>Resources</TableHead><TableHead>Avg Cost/hr</TableHead><TableHead>Status</TableHead></TableRow></TableHeader>
            <TableBody>{providers.map(p => {
              const provResources = resources.filter(r => r.provider === p);
              const avgCost = provResources.length > 0 ? provResources.reduce((s, r) => s + (r.cost_per_hour || 0), 0) / provResources.length : 0;
              return (
                <TableRow key={p}>
                  <TableCell className="font-medium">{p.toUpperCase()}</TableCell>
                  <TableCell>{provResources.length}</TableCell>
                  <TableCell>${avgCost.toFixed(4)}</TableCell>
                  <TableCell><Badge variant="default">Connected</Badge></TableCell>
                </TableRow>
              );
            })}</TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};

function ProviderChart({ resources }: { resources: CloudResource[] }) {
  const byProvider: Record<string, number> = {};
  resources.forEach(r => { byProvider[r.provider] = (byProvider[r.provider] || 0) + r.cost_per_hour; });
  const sorted = Object.entries(byProvider).sort((a, b) => b[1] - a[1]);
  return (
    <Card><CardHeader><CardTitle>Cost by Provider</CardTitle></CardHeader>
    <CardContent><div className="space-y-2">{sorted.slice(0, 5).map(([p, c]) => (
      <div key={p} className="flex items-center justify-between"><span className="font-medium">{p}</span><span>${c.toFixed(2)}/h</span><div className="w-1/2 h-2 bg-muted rounded"><div className="h-full bg-primary rounded" style={{ width: `${(c / Math.max(...sorted.map(s => s[1]))) * 100}%` }} /></div></div>
    ))}</div></CardContent></Card>
  );
}

function ResourceFormDialog({ open, onOpenChange, onSubmit }: { open: boolean; onOpenChange: (v: boolean) => void; onSubmit: (data: any) => void }) {
  const [name, setName] = useState(''); const [provider, setProvider] = useState('aws'); const [type, setType] = useState('compute'); const [region, setRegion] = useState('us-east-1');
  return (
    <Dialog open={open} onOpenChange={onOpenChange}><DialogContent><DialogHeader><DialogTitle>New Resource</DialogTitle></DialogHeader>
      <div className="space-y-4">
        <div><Label>Name</Label><Input value={name} onChange={e => setName(e.target.value)} /></div>
        <div><Label>Provider</Label><Select value={provider} onValueChange={setProvider}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{['aws','azure','gcp','hetzner','ovh'].map(p => <SelectItem key={p} value={p}>{p.toUpperCase()}</SelectItem>)}</SelectContent></Select></div>
        <div><Label>Type</Label><Select value={type} onValueChange={setType}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{['compute','storage','database','network'].map(t => <SelectItem key={t} value={t}>{t}</SelectItem>)}</SelectContent></Select></div>
        <div><Label>Region</Label><Input value={region} onChange={e => setRegion(e.target.value)} /></div>
      </div>
      <DialogFooter><Button onClick={() => { onSubmit({ name, provider, type, region }); onOpenChange(false); }}>Create</Button></DialogFooter>
    </DialogContent></Dialog>
  );
}

function FilterBar({ providers, selectedProvider, onProviderChange, searchTerm, onSearchChange }: { providers: string[]; selectedProvider: string; onProviderChange: (v: string) => void; searchTerm: string; onSearchChange: (v: string) => void }) {
  return (
    <div className="flex items-center gap-4 mb-4">
      <Input placeholder="Search resources..." value={searchTerm} onChange={e => onSearchChange(e.target.value)} className="max-w-sm" />
      <Select value={selectedProvider} onValueChange={onProviderChange}><SelectTrigger className="w-40"><SelectValue placeholder="All Providers" /></SelectTrigger><SelectContent><SelectItem value="all">All Providers</SelectItem>{providers.map(p => <SelectItem key={p} value={p}>{p.toUpperCase()}</SelectItem>)}</SelectContent></Select>
    </div>
  );
}

interface PaginationProps { page: number; totalPages: number; onPageChange: (p: number) => void; }
function PaginationBar({ page, totalPages, onPageChange }: PaginationProps) {
  return (
    <div className="flex items-center justify-center gap-2 mt-4">
      <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => onPageChange(page - 1)}>Prev</Button>
      <span className="text-sm text-muted-foreground">Page {page} of {totalPages}</span>
      <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => onPageChange(page + 1)}>Next</Button>
    </div>
  );
}

function ResourceHealthBadge({ status }: { status: string }) {
  const colorMap: Record<string, string> = { running: 'default', stopped: 'secondary', terminated: 'destructive', provisioning: 'outline' };
  return <Badge variant={(colorMap[status] || 'outline') as any}>{status}</Badge>;
}

function CostSummaryPanel({ resources }: { resources: CloudResource[] }) {
  const totalMonthly = resources.reduce((s, r) => s + (r.cost_per_hour || 0) * 730, 0);
  const avgCost = resources.length > 0 ? resources.reduce((s, r) => s + (r.cost_per_hour || 0), 0) / resources.length : 0;
  return (
    <Card><CardHeader><CardTitle>Cost Summary</CardTitle></CardHeader>
    <CardContent><div className="grid grid-cols-3 gap-4">
      <div><Label>Monthly Total</Label><p className="text-2xl font-bold">${totalMonthly.toFixed(2)}</p></div>
      <div><Label>Hourly Total</Label><p className="text-2xl font-bold">${(totalMonthly / 730).toFixed(2)}</p></div>
      <div><Label>Avg Cost/Resource</Label><p className="text-2xl font-bold">${avgCost.toFixed(4)}/h</p></div>
    </div></CardContent></Card>
  );
}

export default MultiCloudBroker;
