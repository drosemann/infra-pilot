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
import { Database, Layers, Server, Plus, Play, Trash2, RefreshCw, BarChart3, Settings, FileText } from 'lucide-react';

interface LakehouseCluster {
  id: string; name: string; format: string; engine: string; nodes: number; status: string; endpoint: string; tables: number; size: string;
}

interface LakehouseTable {
  id: string; name: string; format: string; location: string; records: number; size: string; state: string; compacted: string; vacuumed: string;
}

const mockClusters: LakehouseCluster[] = [
  { id: 'lh-1', name: 'analytics-lake', format: 'iceberg', engine: 'trino', nodes: 4, status: 'active', endpoint: 'trino://analytics-lake:8080', tables: 12, size: '2.4 TB' },
  { id: 'lh-2', name: 'logging-lake', format: 'delta', engine: 'spark', nodes: 3, status: 'active', endpoint: 'spark://logging-lake:8080', tables: 8, size: '1.1 TB' },
  { id: 'lh-3', name: 'dev-lake', format: 'hudi', engine: 'presto', nodes: 2, status: 'deploying', endpoint: 'presto://dev-lake:8080', tables: 0, size: '0 B' },
];

const mockTables: LakehouseTable[] = [
  { id: 't-1', name: 'user_events', format: 'iceberg', location: 's3://lake/analytics/user_events', records: 45000000, size: '850 GB', state: 'active', compacted: '2026-05-29T06:00:00Z', vacuumed: '2026-05-29T06:00:00Z' },
  { id: 't-2', name: 'order_snapshots', format: 'delta', location: 's3://lake/analytics/orders', records: 12000000, size: '320 GB', state: 'active', compacted: '2026-05-28T12:00:00Z', vacuumed: '2026-05-28T12:00:00Z' },
];

const DataLakehousePage: React.FC = () => {
  const [clusters, setClusters] = useState(mockClusters);
  const [tables, setTables] = useState(mockTables);
  const [selectedCluster, setSelectedCluster] = useState<LakehouseCluster | null>(null);
  const [clusterSearch, setClusterSearch] = useState('');
  const [tableSearch, setTableSearch] = useState('');
  const [createOpen, setCreateOpen] = useState(false);
  const [detailOpen, setDetailOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [clusterToDelete, setClusterToDelete] = useState<LakehouseCluster | null>(null);
  const [editOpen, setEditOpen] = useState(false);
  const [editCluster, setEditCluster] = useState<LakehouseCluster | null>(null);
  const [tableCreateOpen, setTableCreateOpen] = useState(false);
  const [newCluster, setNewCluster] = useState({ name: '', format: 'iceberg', engine: 'trino', nodes: 3, description: '' });
  const [newTable, setNewTable] = useState({ name: '', format: 'iceberg', location: '' });
  const [queryText, setQueryText] = useState('');
  const [selectedQueryCluster, setSelectedQueryCluster] = useState('');

  const filteredClusters = clusters.filter(c => c.name.toLowerCase().includes(clusterSearch.toLowerCase()));
  const filteredTables = tables.filter(t => t.name.toLowerCase().includes(tableSearch.toLowerCase()) || t.format.toLowerCase().includes(tableSearch.toLowerCase()));

  const handleDeploy = () => {
    const cluster: LakehouseCluster = {
      id: `lh-${Date.now()}`,
      name: newCluster.name,
      format: newCluster.format,
      engine: newCluster.engine,
      nodes: newCluster.nodes,
      status: 'deploying',
      endpoint: `${newCluster.name}:8080`,
      tables: 0,
      size: '0 B',
    };
    setClusters([...clusters, cluster]);
    setCreateOpen(false);
    setNewCluster({ name: '', format: 'iceberg', engine: 'trino', nodes: 3, description: '' });
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

  const handleCreateTable = () => {
    const table: LakehouseTable = {
      id: `t-${Date.now()}`,
      name: newTable.name,
      format: newTable.format,
      location: newTable.location,
      records: 0,
      size: '0 B',
      state: 'active',
      compacted: new Date().toISOString(),
      vacuumed: new Date().toISOString(),
    };
    setTables([...tables, table]);
    setTableCreateOpen(false);
    setNewTable({ name: '', format: 'iceberg', location: '' });
  };

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Managed Data Lakehouse</h1>
          <p className="text-muted-foreground">Deploy and manage Iceberg/Hudi/Delta Lake on object storage with SQL analytics</p>
        </div>
        <Dialog open={createOpen} onOpenChange={setCreateOpen}>
          <DialogTrigger asChild><Button><Plus className="mr-2 h-4 w-4" />Deploy Lakehouse</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>Deploy Lakehouse Cluster</DialogTitle></DialogHeader>
            <div className="space-y-4">
              <div><Label>Name</Label><Input value={newCluster.name} onChange={e => setNewCluster({ ...newCluster, name: e.target.value })} placeholder="e.g. analytics-lake" /></div>
              <div><Label>Description</Label><Input value={newCluster.description} onChange={e => setNewCluster({ ...newCluster, description: e.target.value })} placeholder="Production analytics cluster" /></div>
              <div><Label>Table Format</Label>
                <Select value={newCluster.format} onValueChange={v => setNewCluster({ ...newCluster, format: v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent><SelectItem value="iceberg">Iceberg</SelectItem><SelectItem value="hudi">Hudi</SelectItem><SelectItem value="delta">Delta Lake</SelectItem></SelectContent>
                </Select>
              </div>
              <div><Label>Query Engine</Label>
                <Select value={newCluster.engine} onValueChange={v => setNewCluster({ ...newCluster, engine: v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent><SelectItem value="trino">Trino</SelectItem><SelectItem value="presto">Presto</SelectItem><SelectItem value="spark">Spark SQL</SelectItem></SelectContent>
                </Select>
              </div>
              <div><Label>Nodes</Label><Input type="number" value={newCluster.nodes} onChange={e => setNewCluster({ ...newCluster, nodes: +e.target.value })} /></div>
              <Button className="w-full" onClick={handleDeploy}>Deploy</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Clusters</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{clusters.length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Total Tables</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{tables.length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Total Records</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">57M</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Storage Used</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">3.5 TB</div></CardContent></Card>
      </div>

      <Tabs defaultValue="clusters">
        <TabsList>
          <TabsTrigger value="clusters"><Server className="mr-2 h-4 w-4" />Clusters</TabsTrigger>
          <TabsTrigger value="tables"><Database className="mr-2 h-4 w-4" />Tables</TabsTrigger>
          <TabsTrigger value="query"><FileText className="mr-2 h-4 w-4" />SQL Query</TabsTrigger>
          <TabsTrigger value="optimize"><Settings className="mr-2 h-4 w-4" />Optimization</TabsTrigger>
        </TabsList>

        <TabsContent value="clusters" className="space-y-4">
          <div className="flex gap-2">
            <Input placeholder="Search clusters..." value={clusterSearch} onChange={e => setClusterSearch(e.target.value)} className="max-w-xs" />
            <Button variant="outline" size="sm" onClick={() => setClusterSearch('')}>Clear</Button>
          </div>
          <Table>
            <TableHeader>
              <TableRow><TableHead>Name</TableHead><TableHead>Format</TableHead><TableHead>Engine</TableHead><TableHead>Nodes</TableHead><TableHead>Status</TableHead><TableHead>Tables</TableHead><TableHead>Size</TableHead><TableHead>Endpoint</TableHead><TableHead>Actions</TableHead></TableRow>
            </TableHeader>
            <TableBody>
              {filteredClusters.map(c => (
                <TableRow key={c.id}>
                  <TableCell className="font-medium cursor-pointer hover:text-blue-400" onClick={() => { setSelectedCluster(c); setDetailOpen(true); }}>{c.name}</TableCell>
                  <TableCell><Badge variant="outline">{c.format}</Badge></TableCell>
                  <TableCell>{c.engine}</TableCell>
                  <TableCell>{c.nodes}</TableCell>
                  <TableCell><Badge variant={c.status === 'active' ? 'default' : 'secondary'}>{c.status}</Badge></TableCell>
                  <TableCell>{c.tables}</TableCell>
                  <TableCell>{c.size}</TableCell>
                  <TableCell className="text-xs font-mono max-w-[160px] truncate">{c.endpoint}</TableCell>
                  <TableCell>
                    <div className="flex gap-1">
                      <Button size="sm" variant="ghost" onClick={() => { setEditCluster({ ...c }); setEditOpen(true); }}>Edit</Button>
                      <Button size="sm" variant="ghost"><RefreshCw className="h-4 w-4" /></Button>
                      <Button size="sm" variant="ghost" className="text-red-400" onClick={() => { setClusterToDelete(c); setDeleteOpen(true); }}><Trash2 className="h-4 w-4" /></Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TabsContent>

        <TabsContent value="tables" className="space-y-4">
          <div className="flex gap-2">
            <Input placeholder="Search tables..." value={tableSearch} onChange={e => setTableSearch(e.target.value)} className="max-w-xs" />
            <Dialog open={tableCreateOpen} onOpenChange={setTableCreateOpen}>
              <DialogTrigger asChild><Button variant="outline"><Plus className="mr-2 h-4 w-4" />Create Table</Button></DialogTrigger>
              <DialogContent>
                <DialogHeader><DialogTitle>Create Table</DialogTitle></DialogHeader>
                <div className="space-y-4">
                  <div><Label>Table Name</Label><Input value={newTable.name} onChange={e => setNewTable({ ...newTable, name: e.target.value })} placeholder="e.g. clickstream_events" /></div>
                  <div><Label>Format</Label>
                    <Select value={newTable.format} onValueChange={v => setNewTable({ ...newTable, format: v })}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent><SelectItem value="iceberg">Iceberg</SelectItem><SelectItem value="hudi">Hudi</SelectItem><SelectItem value="delta">Delta Lake</SelectItem></SelectContent>
                    </Select>
                  </div>
                  <div><Label>Location</Label><Input value={newTable.location} onChange={e => setNewTable({ ...newTable, location: e.target.value })} placeholder="s3://lake/analytics/table" /></div>
                  <Button className="w-full" onClick={handleCreateTable}>Create</Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>
          <Table>
            <TableHeader>
              <TableRow><TableHead>Table</TableHead><TableHead>Format</TableHead><TableHead>Location</TableHead><TableHead>Records</TableHead><TableHead>Size</TableHead><TableHead>State</TableHead><TableHead>Last Compacted</TableHead><TableHead>Actions</TableHead></TableRow>
            </TableHeader>
            <TableBody>
              {filteredTables.map(t => (
                <TableRow key={t.id}>
                  <TableCell className="font-medium">{t.name}</TableCell>
                  <TableCell><Badge variant="outline">{t.format}</Badge></TableCell>
                  <TableCell className="text-xs font-mono max-w-[200px] truncate">{t.location}</TableCell>
                  <TableCell>{(t.records / 1000000).toFixed(0)}M</TableCell>
                  <TableCell>{t.size}</TableCell>
                  <TableCell><Badge variant="default">{t.state}</Badge></TableCell>
                  <TableCell>{new Date(t.compacted).toLocaleDateString()}</TableCell>
                  <TableCell>
                    <div className="flex gap-1">
                      <Button size="sm" variant="ghost"><BarChart3 className="h-4 w-4" /></Button>
                      <Button size="sm" variant="ghost"><RefreshCw className="h-4 w-4" /></Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TabsContent>

        <TabsContent value="query">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader><CardTitle>Run SQL Query</CardTitle></CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div><Label>Cluster</Label>
                    <Select value={selectedQueryCluster} onValueChange={setSelectedQueryCluster}>
                      <SelectTrigger><SelectValue placeholder="Select cluster..." /></SelectTrigger>
                      <SelectContent>{clusters.filter(c => c.status === 'active').map(c => <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>)}</SelectContent>
                    </Select>
                  </div>
                  <div><Label>Query</Label>
                    <textarea className="w-full h-32 bg-gray-900 text-gray-100 p-4 rounded border border-gray-700 font-mono text-sm" value={queryText} onChange={e => setQueryText(e.target.value)} placeholder="SELECT * FROM user_events LIMIT 10" />
                  </div>
                  <div className="flex gap-2"><Button disabled={!selectedQueryCluster || !queryText}><Play className="mr-2 h-4 w-4" />Execute</Button><Button variant="outline"><FileText className="mr-2 h-4 w-4" />Save As</Button></div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle>Query History</CardTitle></CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {['SELECT COUNT(*) FROM user_events', 'SELECT * FROM order_snapshots LIMIT 50', 'SHOW TABLES'].map((q, i) => (
                    <div key={i} className="p-2 bg-gray-800 rounded text-sm font-mono cursor-pointer hover:bg-gray-700" onClick={() => setQueryText(q)}>
                      <div className="truncate">{q}</div>
                      <div className="text-xs text-muted-foreground">{`${i + 1}h ago`}</div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="optimize">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card><CardHeader><CardTitle>Compaction</CardTitle></CardHeader>
              <CardContent><p className="text-sm text-muted-foreground mb-4">Merge small files into larger ones for better query performance</p>
                <div className="space-y-3">
                  <div><Label>Table</Label>
                    <Select><SelectTrigger><SelectValue placeholder="Select table..." /></SelectTrigger>
                      <SelectContent>{tables.map(t => <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>)}</SelectContent>
                    </Select>
                  </div>
                  <div className="flex items-center gap-2"><Label>Target file size (MB):</Label><Input type="number" defaultValue={256} className="w-24" /></div>
                  <Button className="w-full"><RefreshCw className="mr-2 h-4 w-4" />Run Compaction</Button>
                </div>
              </CardContent>
            </Card>
            <Card><CardHeader><CardTitle>Vacuum</CardTitle></CardHeader>
              <CardContent><p className="text-sm text-muted-foreground mb-4">Remove old snapshots and orphaned files</p>
                <div className="space-y-3">
                  <div><Label>Table</Label>
                    <Select><SelectTrigger><SelectValue placeholder="Select table..." /></SelectTrigger>
                      <SelectContent>{tables.map(t => <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>)}</SelectContent>
                    </Select>
                  </div>
                  <div className="flex items-center gap-2"><Label>Retention (hours):</Label><Input type="number" defaultValue={168} className="w-24" /></div>
                  <Button className="w-full"><Trash2 className="mr-2 h-4 w-4" />Run Vacuum</Button>
                </div>
              </CardContent>
            </Card>
            <Card className="md:col-span-2">
              <CardHeader><CardTitle>Job History</CardTitle></CardHeader>
              <CardContent>
                <Table>
                  <TableHeader><TableRow><TableHead>Job</TableHead><TableHead>Table</TableHead><TableHead>Type</TableHead><TableHead>Status</TableHead><TableHead>Duration</TableHead><TableHead>Ran At</TableHead></TableRow></TableHeader>
                  <TableBody>
                    <TableRow><TableCell>compact-lake-1</TableCell><TableCell>user_events</TableCell><TableCell>Compaction</TableCell><TableCell><Badge className="bg-green-600">Success</Badge></TableCell><TableCell>4m 32s</TableCell><TableCell>2026-05-29 06:00</TableCell></TableRow>
                    <TableRow><TableCell>vacuum-lake-1</TableCell><TableCell>user_events</TableCell><TableCell>Vacuum</TableCell><TableCell><Badge className="bg-green-600">Success</Badge></TableCell><TableCell>2m 10s</TableCell><TableCell>2026-05-29 06:00</TableCell></TableRow>
                    <TableRow><TableCell>compact-log-1</TableCell><TableCell>order_snapshots</TableCell><TableCell>Compaction</TableCell><TableCell><Badge variant="secondary">Running</Badge></TableCell><TableCell>--</TableCell><TableCell>2026-05-29 12:00</TableCell></TableRow>
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>

      <Dialog open={detailOpen} onOpenChange={setDetailOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader><DialogTitle>Cluster Details — {selectedCluster?.name}</DialogTitle></DialogHeader>
          {selectedCluster && (
            <div className="space-y-3">
              <div className="flex justify-between"><span className="text-muted-foreground">Format</span><Badge variant="outline">{selectedCluster.format}</Badge></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Engine</span><span>{selectedCluster.engine}</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Nodes</span><span>{selectedCluster.nodes}</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Status</span><Badge variant={selectedCluster.status === 'active' ? 'default' : 'secondary'}>{selectedCluster.status}</Badge></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Endpoint</span><span className="font-mono text-xs">{selectedCluster.endpoint}</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Tables</span><span>{selectedCluster.tables}</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Size</span><span>{selectedCluster.size}</span></div>
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
              <div><Label>Engine</Label>
                <Select value={editCluster.engine} onValueChange={v => setEditCluster({ ...editCluster, engine: v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent><SelectItem value="trino">Trino</SelectItem><SelectItem value="presto">Presto</SelectItem><SelectItem value="spark">Spark SQL</SelectItem></SelectContent>
                </Select>
              </div>
              <div><Label>Nodes</Label><Input type="number" value={editCluster.nodes} onChange={e => setEditCluster({ ...editCluster, nodes: +e.target.value })} /></div>
              <div><Label>Format</Label><Input value={editCluster.format} disabled className="text-muted-foreground" /></div>
              <Button className="w-full" onClick={handleEdit}>Save Changes</Button>
            </div>
          )}
        </DialogContent>
      </Dialog>

      <Dialog open={deleteOpen} onOpenChange={setDeleteOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>Delete Cluster</DialogTitle></DialogHeader>
          <p className="text-sm text-muted-foreground">Are you sure you want to delete <strong>{clusterToDelete?.name}</strong>? All tables and data will be removed.</p>
          <div className="flex gap-2 justify-end">
            <Button variant="outline" onClick={() => setDeleteOpen(false)}>Cancel</Button>
            <Button variant="destructive" onClick={handleDelete}>Delete</Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

const Save = ({ className }: { className?: string }) => React.createElement('svg', { className, width: 16, height: 16, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', strokeWidth: 2 }, React.createElement('path', { d: 'M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z' }), React.createElement('polyline', { points: '17 21 17 13 7 13 7 21' }), React.createElement('polyline', { points: '7 3 7 8 15 8' }));
export default DataLakehousePage;
