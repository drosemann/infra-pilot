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
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Activity, Radio, GitBranch, Plus, Trash2, Play, Pause, BarChart3, Layers } from 'lucide-react';

interface StreamCluster {
  id: string; name: string; type: string; nodes: number; status: string; brokers: string; topics: number; connectors: number; throughput: string;
}

interface StreamTopic {
  id: string; name: string; partitions: number; replication: number; retention: string; messages: number; size: string;
}

const mockClusters: StreamCluster[] = [
  { id: 'sc-1', name: 'events-cluster', type: 'kafka', nodes: 3, status: 'active', brokers: 'events-broker-0:9092,...', topics: 8, connectors: 4, throughput: '45 MB/s' },
  { id: 'sc-2', name: 'logs-pipeline', type: 'redpanda', nodes: 5, status: 'active', brokers: 'logs-broker-0:9092,...', topics: 15, connectors: 6, throughput: '120 MB/s' },
];

const mockTopics: StreamTopic[] = [
  { id: 'st-1', name: 'user-events', partitions: 6, replication: 2, retention: '7 days', messages: 45000000, size: '2.1 GB' },
  { id: 'st-2', name: 'system-logs', partitions: 3, replication: 1, retention: '30 days', messages: 120000000, size: '8.5 GB' },
];

const StreamingPipelinePage: React.FC = () => {
  const [clusters, setClusters] = useState(mockClusters);
  const [topics, setTopics] = useState(mockTopics);
  const [createOpen, setCreateOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [editCluster, setEditCluster] = useState<StreamCluster | null>(null);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [clusterToDelete, setClusterToDelete] = useState<StreamCluster | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const [selectedCluster, setSelectedCluster] = useState<StreamCluster | null>(null);
  const [topicCreateOpen, setTopicCreateOpen] = useState(false);
  const [topicDeleteOpen, setTopicDeleteOpen] = useState(false);
  const [topicToDelete, setTopicToDelete] = useState<StreamTopic | null>(null);
  const [search, setSearch] = useState('');
  const [topicSearch, setTopicSearch] = useState('');
  const [newCluster, setNewCluster] = useState({ name: '', type: 'kafka', nodes: 3, version: 'latest' });
  const [newTopic, setNewTopic] = useState({ name: '', partitions: 3, replication: 2, retention: '7 days' });

  const filteredClusters = clusters.filter(c => c.name.toLowerCase().includes(search.toLowerCase()));
  const filteredTopics = topics.filter(t => t.name.toLowerCase().includes(topicSearch.toLowerCase()));

  const handleDeploy = () => {
    const cluster: StreamCluster = {
      id: `sc-${Date.now()}`,
      name: newCluster.name,
      type: newCluster.type,
      nodes: newCluster.nodes,
      status: 'active',
      brokers: `${newCluster.name}-broker-0:9092,...`,
      topics: 0,
      connectors: 0,
      throughput: '0 MB/s',
    };
    setClusters([...clusters, cluster]);
    setCreateOpen(false);
    setNewCluster({ name: '', type: 'kafka', nodes: 3, version: 'latest' });
  };

  const handleEdit = () => {
    if (!editCluster) return;
    setClusters(clusters.map(c => c.id === editCluster.id ? editCluster : c));
    setEditOpen(false);
    setEditCluster(null);
  };

  const handleDelete = () => {
    if (!clusterToDelete) return;
    setClusters(clusters.filter(c => c.id !== clusterToDelete.id));
    setDeleteOpen(false);
    setClusterToDelete(null);
  };

  const handleCreateTopic = () => {
    const topic: StreamTopic = {
      id: `st-${Date.now()}`,
      name: newTopic.name,
      partitions: newTopic.partitions,
      replication: newTopic.replication,
      retention: newTopic.retention,
      messages: 0,
      size: '0 B',
    };
    setTopics([...topics, topic]);
    setTopicCreateOpen(false);
    setNewTopic({ name: '', partitions: 3, replication: 2, retention: '7 days' });
  };

  const handleDeleteTopic = () => {
    if (!topicToDelete) return;
    setTopics(topics.filter(t => t.id !== topicToDelete.id));
    setTopicDeleteOpen(false);
    setTopicToDelete(null);
  };

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Streaming Data Pipeline</h1>
          <p className="text-muted-foreground">Managed Kafka/Redpanda clusters with auto-scaling, schema registry, and connectors</p>
        </div>
        <Dialog open={createOpen} onOpenChange={setCreateOpen}>
          <DialogTrigger asChild><Button><Plus className="mr-2 h-4 w-4" />Deploy Cluster</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>Deploy Streaming Cluster</DialogTitle></DialogHeader>
            <div className="space-y-4">
              <div><Label>Name</Label><Input value={newCluster.name} onChange={e => setNewCluster({ ...newCluster, name: e.target.value })} placeholder="e.g. events-cluster" /></div>
              <div><Label>Type</Label>
                <RadioGroup value={newCluster.type} onValueChange={v => setNewCluster({ ...newCluster, type: v })}>
                  <div className="flex items-center gap-2"><RadioGroupItem value="kafka" id="kafka" /><Label htmlFor="kafka">Kafka</Label></div>
                  <div className="flex items-center gap-2"><RadioGroupItem value="redpanda" id="redpanda" /><Label htmlFor="redpanda">Redpanda</Label></div>
                </RadioGroup>
              </div>
              <div><Label>Nodes</Label><Input type="number" value={newCluster.nodes} onChange={e => setNewCluster({ ...newCluster, nodes: +e.target.value })} min={1} max={20} /></div>
              <div><Label>Version</Label>
                <Select value={newCluster.version} onValueChange={v => setNewCluster({ ...newCluster, version: v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent><SelectItem value="latest">Latest</SelectItem><SelectItem value="3.5">3.5</SelectItem><SelectItem value="3.4">3.4</SelectItem></SelectContent>
                </Select>
              </div>
              <Button className="w-full" onClick={handleDeploy}>Deploy</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Clusters</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{clusters.length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Total Topics</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{topics.length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Total Messages</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">165M</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Agg. Throughput</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">165 MB/s</div></CardContent></Card>
      </div>

      <Tabs defaultValue="clusters">
        <TabsList>
          <TabsTrigger value="clusters"><Radio className="mr-2 h-4 w-4" />Clusters</TabsTrigger>
          <TabsTrigger value="topics"><Layers className="mr-2 h-4 w-4" />Topics</TabsTrigger>
          <TabsTrigger value="connectors"><GitBranch className="mr-2 h-4 w-4" />Connectors</TabsTrigger>
          <TabsTrigger value="schema"><FileText className="mr-2 h-4 w-4" />Schema Registry</TabsTrigger>
          <TabsTrigger value="monitor"><Activity className="mr-2 h-4 w-4" />Monitoring</TabsTrigger>
        </TabsList>

        <TabsContent value="clusters">
          <div className="flex gap-2 mb-4">
            <Input placeholder="Search clusters..." value={search} onChange={e => setSearch(e.target.value)} className="max-w-sm" />
            <Button variant="outline" size="sm" onClick={() => setSearch('')}>Clear</Button>
          </div>
          <Table>
            <TableHeader><TableRow><TableHead>Name</TableHead><TableHead>Type</TableHead><TableHead>Nodes</TableHead><TableHead>Status</TableHead><TableHead>Topics</TableHead><TableHead>Connectors</TableHead><TableHead>Throughput</TableHead><TableHead>Actions</TableHead></TableRow></TableHeader>
            <TableBody>
              {filteredClusters.map(c => (
                <TableRow key={c.id}>
                  <TableCell className="font-medium cursor-pointer hover:text-blue-400" onClick={() => { setSelectedCluster(c); setDetailOpen(true); }}>{c.name}</TableCell>
                  <TableCell><Badge variant="outline">{c.type}</Badge></TableCell>
                  <TableCell>{c.nodes}</TableCell>
                  <TableCell><Badge variant={c.status === 'active' ? 'default' : 'secondary'}>{c.status}</Badge></TableCell>
                  <TableCell>{c.topics}</TableCell>
                  <TableCell>{c.connectors}</TableCell>
                  <TableCell className="font-mono text-xs">{c.throughput}</TableCell>
                  <TableCell>
                    <div className="flex gap-1">
                      <Button size="sm" variant="ghost"><BarChart3 className="h-4 w-4" /></Button>
                      <Button size="sm" variant="ghost" onClick={() => { setEditCluster({ ...c }); setEditOpen(true); }}>Edit</Button>
                      <Button size="sm" variant="ghost" className="text-red-400" onClick={() => { setClusterToDelete(c); setDeleteOpen(true); }}><Trash2 className="h-4 w-4" /></Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TabsContent>

        <TabsContent value="topics">
          <div className="flex gap-2 mb-4">
            <Input placeholder="Search topics..." value={topicSearch} onChange={e => setTopicSearch(e.target.value)} className="max-w-xs" />
            <Dialog open={topicCreateOpen} onOpenChange={setTopicCreateOpen}>
              <DialogTrigger asChild><Button variant="outline"><Plus className="mr-2 h-4 w-4" />Create Topic</Button></DialogTrigger>
              <DialogContent>
                <DialogHeader><DialogTitle>Create Topic</DialogTitle></DialogHeader>
                <div className="space-y-4">
                  <div><Label>Name</Label><Input value={newTopic.name} onChange={e => setNewTopic({ ...newTopic, name: e.target.value })} placeholder="e.g. clickstream" /></div>
                  <div><Label>Partitions</Label><Input type="number" value={newTopic.partitions} onChange={e => setNewTopic({ ...newTopic, partitions: +e.target.value })} /></div>
                  <div><Label>Replication Factor</Label><Input type="number" value={newTopic.replication} onChange={e => setNewTopic({ ...newTopic, replication: +e.target.value })} /></div>
                  <div><Label>Retention</Label>
                    <Select value={newTopic.retention} onValueChange={v => setNewTopic({ ...newTopic, retention: v })}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent><SelectItem value="1 day">1 day</SelectItem><SelectItem value="7 days">7 days</SelectItem><SelectItem value="30 days">30 days</SelectItem><SelectItem value="forever">Forever</SelectItem></SelectContent>
                    </Select>
                  </div>
                  <Button className="w-full" onClick={handleCreateTopic}>Create</Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>
          <Table>
            <TableHeader><TableRow><TableHead>Topic</TableHead><TableHead>Partitions</TableHead><TableHead>Replication</TableHead><TableHead>Retention</TableHead><TableHead>Messages</TableHead><TableHead>Size</TableHead><TableHead>Actions</TableHead></TableRow></TableHeader>
            <TableBody>
              {filteredTopics.map(t => (
                <TableRow key={t.id}>
                  <TableCell className="font-medium">{t.name}</TableCell>
                  <TableCell>{t.partitions}</TableCell>
                  <TableCell>{t.replication}</TableCell>
                  <TableCell>{t.retention}</TableCell>
                  <TableCell>{(t.messages / 1000000).toFixed(0)}M</TableCell>
                  <TableCell>{t.size}</TableCell>
                  <TableCell>
                    <Button size="sm" variant="ghost" className="text-red-400" onClick={() => { setTopicToDelete(t); setTopicDeleteOpen(true); }}><Trash2 className="h-4 w-4" /></Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TabsContent>

        <TabsContent value="connectors">
          <div className="flex gap-2 mb-4">
            <Dialog><DialogTrigger asChild><Button><Plus className="mr-2 h-4 w-4" />Add Connector</Button></DialogTrigger>
              <DialogContent>
                <DialogHeader><DialogTitle>Add Connector</DialogTitle></DialogHeader>
                <div className="space-y-4">
                  <div><Label>Name</Label><Input placeholder="e.g. jdbc-sink" /></div>
                  <div><Label>Type</Label>
                    <Select><SelectTrigger><SelectValue placeholder="Sink" /></SelectTrigger>
                      <SelectContent><SelectItem value="sink">Sink</SelectItem><SelectItem value="source">Source</SelectItem></SelectContent>
                    </Select>
                  </div>
                  <div><Label>Cluster</Label>
                    <Select><SelectTrigger><SelectValue placeholder="Select cluster..." /></SelectTrigger>
                      <SelectContent>{clusters.map(c => <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>)}</SelectContent>
                    </Select>
                  </div>
                  <div><Label>Connector Class</Label>
                    <Select><SelectTrigger><SelectValue placeholder="Select class..." /></SelectTrigger>
                      <SelectContent><SelectItem value="jdbc">JDBC Sink Connector</SelectItem><SelectItem value="s3">S3 Sink Connector</SelectItem><SelectItem value="elastic">Elasticsearch Sink</SelectItem></SelectContent>
                    </Select>
                  </div>
                  <Button className="w-full">Add Connector</Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>
          <Table>
            <TableHeader><TableRow><TableHead>Name</TableHead><TableHead>Type</TableHead><TableHead>Cluster</TableHead><TableHead>Class</TableHead><TableHead>Status</TableHead><TableHead>Tasks</TableHead><TableHead>Actions</TableHead></TableRow></TableHeader>
            <TableBody>
              <TableRow><TableCell>jdbc-sink-orders</TableCell><TableCell><Badge variant="outline">sink</Badge></TableCell><TableCell>events-cluster</TableCell><TableCell>JDBC Sink</TableCell><TableCell><Badge>running</Badge></TableCell><TableCell>2/2</TableCell><TableCell><div className="flex gap-1"><Button size="sm" variant="ghost"><Pause className="h-4 w-4" /></Button><Button size="sm" variant="ghost" className="text-red-400"><Trash2 className="h-4 w-4" /></Button></div></TableCell></TableRow>
              <TableRow><TableCell>s3-sink-logs</TableCell><TableCell><Badge variant="outline">sink</Badge></TableCell><TableCell>logs-pipeline</TableCell><TableCell>S3 Sink</TableCell><TableCell><Badge>running</Badge></TableCell><TableCell>4/4</TableCell><TableCell><div className="flex gap-1"><Button size="sm" variant="ghost"><Pause className="h-4 w-4" /></Button><Button size="sm" variant="ghost" className="text-red-400"><Trash2 className="h-4 w-4" /></Button></div></TableCell></TableRow>
            </TableBody>
          </Table>
        </TabsContent>

        <TabsContent value="schema">
          <Card>
            <CardHeader><CardTitle>Schema Registry</CardTitle></CardHeader>
            <CardContent>
              <div className="flex gap-2 mb-4">
                <Input placeholder="Search subjects..." className="max-w-xs" />
                <Button variant="outline"><Plus className="mr-2 h-4 w-4" />Register Schema</Button>
              </div>
              <Table>
                <TableHeader><TableRow><TableHead>Subject</TableHead><TableHead>Version</TableHead><TableHead>Type</TableHead><TableHead>Compatibility</TableHead><TableHead>ID</TableHead><TableHead>Actions</TableHead></TableRow></TableHeader>
                <TableBody>
                  <TableRow><TableCell>user-events-value</TableCell><TableCell>3</TableCell><TableCell>avro</TableCell><TableCell>backward</TableCell><TableCell>101</TableCell><TableCell><Button size="sm" variant="ghost">View</Button></TableCell></TableRow>
                  <TableRow><TableCell>system-logs-value</TableCell><TableCell>1</TableCell><TableCell>protobuf</TableCell><TableCell>forward</TableCell><TableCell>102</TableCell><TableCell><Button size="sm" variant="ghost">View</Button></TableCell></TableRow>
                  <TableRow><TableCell>orders-value</TableCell><TableCell>5</TableCell><TableCell>avro</TableCell><TableCell>backward</TableCell><TableCell>99</TableCell><TableCell><Button size="sm" variant="ghost">View</Button></TableCell></TableRow>
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="monitor">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {clusters.map(c => (
              <Card key={c.id}><CardHeader><CardTitle>{c.name} — Metrics</CardTitle></CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex justify-between"><span>Throughput</span><span className="font-mono text-xs">{c.throughput}</span></div>
                    <div className="flex justify-between"><span>Nodes</span><span className="font-mono">{c.nodes}</span></div>
                    <div className="flex justify-between"><span>Topics</span><span className="font-mono">{c.topics}</span></div>
                    <div className="flex justify-between"><span>Connectors</span><span className="font-mono">{c.connectors}</span></div>
                    <div className="pt-2 border-t border-gray-700">
                      <div className="flex justify-between"><span>Consumer Lag</span><span className="font-mono text-yellow-400">{Math.round(Math.random() * 5000)}</span></div>
                      <div className="flex justify-between"><span>Under-replicated</span><span className="font-mono text-green-400">0</span></div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>

      <Dialog open={detailOpen} onOpenChange={setDetailOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader><DialogTitle>Cluster Details — {selectedCluster?.name}</DialogTitle></DialogHeader>
          {selectedCluster && (
            <div className="space-y-3">
              <div className="flex justify-between"><span className="text-muted-foreground">Type</span><Badge variant="outline">{selectedCluster.type}</Badge></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Nodes</span><span>{selectedCluster.nodes}</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Status</span><Badge>{selectedCluster.status}</Badge></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Brokers</span><span className="font-mono text-xs max-w-[200px] truncate">{selectedCluster.brokers}</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Topics</span><span>{selectedCluster.topics}</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Connectors</span><span>{selectedCluster.connectors}</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Throughput</span><span className="font-mono">{selectedCluster.throughput}</span></div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>Edit Cluster</DialogTitle></DialogHeader>
          {editCluster && (
            <div className="space-y-4">
              <div><Label>Name</Label><Input value={editCluster.name} onChange={e => setEditCluster({ ...editCluster, name: e.target.value })} /></div>
              <div><Label>Nodes</Label><Input type="number" value={editCluster.nodes} onChange={e => setEditCluster({ ...editCluster, nodes: +e.target.value })} /></div>
              <Button className="w-full" onClick={handleEdit}>Save Changes</Button>
            </div>
          )}
        </DialogContent>
      </Dialog>

      <Dialog open={deleteOpen} onOpenChange={setDeleteOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>Delete Cluster</DialogTitle></DialogHeader>
          <p className="text-sm text-muted-foreground">Are you sure you want to delete <strong>{clusterToDelete?.name}</strong>? All topics and data will be lost.</p>
          <div className="flex gap-2 justify-end">
            <Button variant="outline" onClick={() => setDeleteOpen(false)}>Cancel</Button>
            <Button variant="destructive" onClick={handleDelete}>Delete</Button>
          </div>
        </DialogContent>
      </Dialog>

      <Dialog open={topicDeleteOpen} onOpenChange={setTopicDeleteOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>Delete Topic</DialogTitle></DialogHeader>
          <p className="text-sm text-muted-foreground">Are you sure you want to delete topic <strong>{topicToDelete?.name}</strong>?</p>
          <div className="flex gap-2 justify-end">
            <Button variant="outline" onClick={() => setTopicDeleteOpen(false)}>Cancel</Button>
            <Button variant="destructive" onClick={handleDeleteTopic}>Delete</Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

const FileText = ({ className }: { className?: string }) => React.createElement('svg', { className, width: 16, height: 16, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', strokeWidth: 2 }, React.createElement('path', { d: 'M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z' }), React.createElement('polyline', { points: '14 2 14 8 20 8' }), React.createElement('line', { x1: 16, y1: 13, x2: 8, y2: 13 }), React.createElement('line', { x1: 16, y1: 17, x2: 8, y2: 17 }), React.createElement('polyline', { points: '10 9 9 9 8 9' }));
export default StreamingPipelinePage;
