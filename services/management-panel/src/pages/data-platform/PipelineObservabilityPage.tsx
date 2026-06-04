import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Activity, GitBranch, BarChart3, Plus, Play, Pause, Trash2, AlertTriangle, Search, Server, RefreshCw } from 'lucide-react';

interface Pipeline {
  id: string; name: string; description: string; nodes: number; status: string; throughput: string; latency: string; errorRate: string; freshness: string;
}

const mockPipelines: Pipeline[] = [
  { id: 'pl-1', name: 'User Events Pipeline', description: 'Ingest → transform → sink to lakehouse', nodes: 4, status: 'running', throughput: '2,500 r/s', latency: '45ms', errorRate: '0.3%', freshness: '< 1s' },
  { id: 'pl-2', name: 'Order Processing', description: 'Orders from API → validation → enrichment → warehouse', nodes: 5, status: 'running', throughput: '850 r/s', latency: '120ms', errorRate: '1.2%', freshness: '< 5s' },
  { id: 'pl-3', name: 'Log Aggregation', description: 'System logs → parse → index → archive', nodes: 3, status: 'paused', throughput: '0 r/s', latency: '0ms', errorRate: '0%', freshness: 'N/A' },
];

const PipelineObservabilityPage: React.FC = () => {
  const [pipelines, setPipelines] = useState(mockPipelines);
  const [search, setSearch] = useState('');
  const [createOpen, setCreateOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [editPipeline, setEditPipeline] = useState<Pipeline | null>(null);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [pipelineToDelete, setPipelineToDelete] = useState<Pipeline | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const [selectedPipeline, setSelectedPipeline] = useState<Pipeline | null>(null);
  const [newPipeline, setNewPipeline] = useState({ name: '', description: '', owner: '' });

  const filtered = pipelines.filter(p => p.name.toLowerCase().includes(search.toLowerCase()) || p.description.toLowerCase().includes(search.toLowerCase()));

  const handleCreate = () => {
    const pipeline: Pipeline = {
      id: `pl-${Date.now()}`,
      name: newPipeline.name,
      description: newPipeline.description,
      owner: newPipeline.owner,
      nodes: 2,
      status: 'running',
      throughput: '0 r/s',
      latency: '0ms',
      errorRate: '0%',
      freshness: 'N/A',
    };
    setPipelines([...pipelines, pipeline]);
    setCreateOpen(false);
    setNewPipeline({ name: '', description: '', owner: '' });
  };

  const handleEdit = () => {
    if (!editPipeline) return;
    setPipelines(pipelines.map(p => p.id === editPipeline.id ? editPipeline : p));
    setEditOpen(false);
    setEditPipeline(null);
  };

  const handleDelete = () => {
    if (!pipelineToDelete) return;
    setPipelines(pipelines.filter(p => p.id !== pipelineToDelete.id));
    setDeleteOpen(false);
    setPipelineToDelete(null);
  };

  const togglePipeline = (id: string) => {
    setPipelines(pipelines.map(p => p.id === id ? { ...p, status: p.status === 'running' ? 'paused' : 'running' } : p));
  };

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Data Pipeline Observability</h1>
          <p className="text-muted-foreground">End-to-end pipeline monitoring: throughput, latency, error rate, data freshness</p>
        </div>
        <Dialog open={createOpen} onOpenChange={setCreateOpen}>
          <DialogTrigger asChild><Button><Plus className="mr-2 h-4 w-4" />Create Pipeline</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>New Pipeline</DialogTitle></DialogHeader>
            <div className="space-y-4">
              <div><Label>Name</Label><Input value={newPipeline.name} onChange={e => setNewPipeline({ ...newPipeline, name: e.target.value })} placeholder="e.g. User Events Pipeline" /></div>
              <div><Label>Description</Label><Input value={newPipeline.description} onChange={e => setNewPipeline({ ...newPipeline, description: e.target.value })} placeholder="Brief description" /></div>
              <div><Label>Owner</Label><Input value={newPipeline.owner} onChange={e => setNewPipeline({ ...newPipeline, owner: e.target.value })} placeholder="team name" /></div>
              <div><Label>Source Type</Label>
                <select className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm">
                  <option>Kafka</option><option>API</option><option>S3 Event</option><option>Database CDC</option>
                </select>
              </div>
              <Button className="w-full" onClick={handleCreate}>Create</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Pipelines</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{pipelines.length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Running</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-green-400">{pipelines.filter(p => p.status === 'running').length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Failed/Nodes</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-red-400">0</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Alerts (24h)</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-yellow-400">2</div></CardContent></Card>
      </div>

      <Tabs defaultValue="pipelines">
        <TabsList>
          <TabsTrigger value="pipelines"><GitBranch className="mr-2 h-4 w-4" />Pipelines</TabsTrigger>
          <TabsTrigger value="metrics"><BarChart3 className="mr-2 h-4 w-4" />Metrics</TabsTrigger>
          <TabsTrigger value="lineage"><Activity className="mr-2 h-4 w-4" />Lineage View</TabsTrigger>
          <TabsTrigger value="alerts"><AlertTriangle className="mr-2 h-4 w-4" />Alerts</TabsTrigger>
          <TabsTrigger value="rca"><Search className="mr-2 h-4 w-4" />Root Cause</TabsTrigger>
        </TabsList>

        <TabsContent value="pipelines">
          <div className="flex gap-2 mb-4">
            <Input placeholder="Search pipelines..." value={search} onChange={e => setSearch(e.target.value)} className="max-w-sm" />
            <Button variant="outline" size="sm" onClick={() => setSearch('')}>Clear</Button>
          </div>
          <Table>
            <TableHeader><TableRow><TableHead>Pipeline</TableHead><TableHead>Description</TableHead><TableHead>Nodes</TableHead><TableHead>Status</TableHead><TableHead>Throughput</TableHead><TableHead>Latency</TableHead><TableHead>Error Rate</TableHead><TableHead>Freshness</TableHead><TableHead>Actions</TableHead></TableRow></TableHeader>
            <TableBody>
              {filtered.map(p => (
                <TableRow key={p.id}>
                  <TableCell className="font-medium cursor-pointer hover:text-blue-400" onClick={() => { setSelectedPipeline(p); setDetailOpen(true); }}>{p.name}</TableCell>
                  <TableCell className="text-xs text-muted-foreground max-w-[160px] truncate">{p.description}</TableCell>
                  <TableCell>{p.nodes}</TableCell>
                  <TableCell>
                    <Badge variant={p.status === 'running' ? 'default' : p.status === 'paused' ? 'secondary' : 'destructive'}>
                      {p.status === 'running' ? <><Play className="mr-1 h-3 w-3 inline" /> Running</> : p.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="font-mono text-xs">{p.throughput}</TableCell>
                  <TableCell className="font-mono text-xs">{p.latency}</TableCell>
                  <TableCell className="font-mono text-xs">{p.errorRate}</TableCell>
                  <TableCell className="font-mono text-xs">{p.freshness}</TableCell>
                  <TableCell>
                    <div className="flex gap-1">
                      <Button size="sm" variant="ghost" onClick={() => togglePipeline(p.id)}>
                        {p.status === 'running' ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                      </Button>
                      <Button size="sm" variant="ghost" onClick={() => { setEditPipeline({ ...p }); setEditOpen(true); }}>Edit</Button>
                      <Button size="sm" variant="ghost" className="text-red-400" onClick={() => { setPipelineToDelete(p); setDeleteOpen(true); }}><Trash2 className="h-4 w-4" /></Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TabsContent>

        <TabsContent value="metrics">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {pipelines.filter(p => p.status === 'running').map(p => (
              <Card key={p.id}>
                <CardHeader><CardTitle>{p.name}</CardTitle></CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div><div className="flex justify-between text-sm mb-1"><span>Throughput</span><span className="font-mono">{p.throughput}</span></div><div className="w-full bg-gray-700 rounded-full h-1.5"><div className="bg-blue-500 h-1.5 rounded-full" style={{ width: '72%' }} /></div></div>
                    <div><div className="flex justify-between text-sm mb-1"><span>Latency</span><span className="font-mono">{p.latency}</span></div><div className="w-full bg-gray-700 rounded-full h-1.5"><div className="bg-green-500 h-1.5 rounded-full" style={{ width: '45%' }} /></div></div>
                    <div><div className="flex justify-between text-sm mb-1"><span>Error Rate</span><span className="font-mono">{p.errorRate}</span></div><div className="w-full bg-gray-700 rounded-full h-1.5"><div className="bg-yellow-500 h-1.5 rounded-full" style={{ width: '8%' }} /></div></div>
                    <div><div className="flex justify-between text-sm mb-1"><span>Data Freshness</span><span className="font-mono">{p.freshness}</span></div><div className="w-full bg-gray-700 rounded-full h-1.5"><div className="bg-green-500 h-1.5 rounded-full" style={{ width: '5%' }} /></div></div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="lineage">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader><CardTitle>Pipeline Graph — User Events Pipeline</CardTitle></CardHeader>
              <CardContent>
                <div className="flex items-center justify-center gap-4 p-8">
                  <div className="flex flex-col items-center gap-2"><div className="w-20 h-10 bg-blue-600 rounded flex items-center justify-center text-xs font-medium">API</div><span className="text-xs text-muted-foreground">Source</span></div>
                  <div className="text-muted-foreground">→</div>
                  <div className="flex flex-col items-center gap-2"><div className="w-20 h-10 bg-green-600 rounded flex items-center justify-center text-xs font-medium">Transform</div><span className="text-xs text-muted-foreground">Enrich</span></div>
                  <div className="text-muted-foreground">→</div>
                  <div className="flex flex-col items-center gap-2"><div className="w-20 h-10 bg-yellow-600 rounded flex items-center justify-center text-xs font-medium">Validate</div><span className="text-xs text-muted-foreground">Quality</span></div>
                  <div className="text-muted-foreground">→</div>
                  <div className="flex flex-col items-center gap-2"><div className="w-20 h-10 bg-purple-600 rounded flex items-center justify-center text-xs font-medium">Lakehouse</div><span className="text-xs text-muted-foreground">Sink</span></div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle>Node Health</CardTitle></CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {['Ingest', 'Parse', 'Enrich', 'Validate', 'Sink'].map((node, i) => (
                    <div key={node} className="flex justify-between items-center p-2 bg-gray-800 rounded">
                      <span className="text-sm">{node}</span>
                      <div className="flex gap-2 items-center">
                        <Badge className={i === 4 ? 'bg-green-600' : 'bg-gray-600'}>{i === 4 ? 'Healthy' : 'Healthy'}</Badge>
                        <span className="text-xs text-muted-foreground">{Math.round(Math.random() * 100 + 50)}ms</span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="alerts">
          <Table>
            <TableHeader><TableRow><TableHead>Severity</TableHead><TableHead>Pipeline</TableHead><TableHead>Message</TableHead><TableHead>Metric</TableHead><TableHead>Threshold</TableHead><TableHead>Actual</TableHead><TableHead>Triggered</TableHead><TableHead>Actions</TableHead></TableRow></TableHeader>
            <TableBody>
              <TableRow><TableCell><Badge variant="destructive">Critical</Badge></TableCell><TableCell>Order Processing</TableCell><TableCell>Latency spike detected</TableCell><TableCell>latency_ms</TableCell><TableCell>500</TableCell><TableCell className="text-red-400">1,230</TableCell><TableCell>2026-05-30 09:15</TableCell><TableCell><Button size="sm" variant="ghost">Ack</Button></TableCell></TableRow>
              <TableRow><TableCell><Badge variant="secondary">Warning</Badge></TableCell><TableCell>User Events Pipeline</TableCell><TableCell>Error rate elevated</TableCell><TableCell>error_rate</TableCell><TableCell>5%</TableCell><TableCell className="text-yellow-400">7.2%</TableCell><TableCell>2026-05-30 08:45</TableCell><TableCell><Button size="sm" variant="ghost">Ack</Button></TableCell></TableRow>
              <TableRow><TableCell><Badge variant="secondary">Warning</Badge></TableCell><TableCell>Log Aggregation</TableCell><TableCell>Pipeline paused</TableCell><TableCell>status</TableCell><TableCell>running</TableCell><TableCell className="text-yellow-400">paused</TableCell><TableCell>2026-05-30 07:30</TableCell><TableCell><Button size="sm" variant="ghost">Dismiss</Button></TableCell></TableRow>
            </TableBody>
          </Table>
        </TabsContent>

        <TabsContent value="rca">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader><CardTitle>Root Cause Analysis — Order Processing</CardTitle></CardHeader>
              <CardContent className="space-y-4">
                <div className="p-4 bg-gray-800 rounded">
                  <div className="font-medium text-yellow-400">Potential Root Causes</div>
                  <div className="mt-2 space-y-2">
                    <div className="flex justify-between"><span>Database connection pool exhausted</span><Badge>85% probability</Badge></div>
                    <div className="flex justify-between"><span>Upstream API throttling</span><Badge>45% probability</Badge></div>
                    <div className="flex justify-between"><span>Transformation memory pressure</span><Badge>30% probability</Badge></div>
                    <div className="flex justify-between"><span>Network latency spike</span><Badge>15% probability</Badge></div>
                  </div>
                </div>
                <Button variant="outline"><RefreshCw className="mr-2 h-4 w-4" />Re-run Analysis</Button>
              </CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle>Recommended Actions</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                {[
                  { action: 'Scale connection pool from 20 → 50', impact: 'High' },
                  { action: 'Implement connection retry with backoff', impact: 'Medium' },
                  { action: 'Increase DB instance size', impact: 'Low' },
                ].map((rec, i) => (
                  <div key={i} className="p-3 bg-gray-800 rounded flex justify-between">
                    <span className="text-sm">{rec.action}</span>
                    <Badge variant={rec.impact === 'High' ? 'default' : 'secondary'}>{rec.impact}</Badge>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>

      <Dialog open={detailOpen} onOpenChange={setDetailOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader><DialogTitle>Pipeline Details — {selectedPipeline?.name}</DialogTitle></DialogHeader>
          {selectedPipeline && (
            <div className="space-y-3">
              <div className="flex justify-between"><span className="text-muted-foreground">Description</span><span className="text-sm max-w-xs text-right">{selectedPipeline.description}</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Nodes</span><span>{selectedPipeline.nodes}</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Status</span><Badge>{selectedPipeline.status}</Badge></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Throughput</span><span className="font-mono">{selectedPipeline.throughput}</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Latency</span><span className="font-mono">{selectedPipeline.latency}</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Error Rate</span><span className="font-mono">{selectedPipeline.errorRate}</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Freshness</span><span className="font-mono">{selectedPipeline.freshness}</span></div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>Edit Pipeline</DialogTitle></DialogHeader>
          {editPipeline && (
            <div className="space-y-4">
              <div><Label>Name</Label><Input value={editPipeline.name} onChange={e => setEditPipeline({ ...editPipeline, name: e.target.value })} /></div>
              <div><Label>Description</Label><Input value={editPipeline.description} onChange={e => setEditPipeline({ ...editPipeline, description: e.target.value })} /></div>
              <Button className="w-full" onClick={handleEdit}>Save Changes</Button>
            </div>
          )}
        </DialogContent>
      </Dialog>

      <Dialog open={deleteOpen} onOpenChange={setDeleteOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>Delete Pipeline</DialogTitle></DialogHeader>
          <p className="text-sm text-muted-foreground">Are you sure you want to delete <strong>{pipelineToDelete?.name}</strong>?</p>
          <div className="flex gap-2 justify-end">
            <Button variant="outline" onClick={() => setDeleteOpen(false)}>Cancel</Button>
            <Button variant="destructive" onClick={handleDelete}>Delete</Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default PipelineObservabilityPage;
