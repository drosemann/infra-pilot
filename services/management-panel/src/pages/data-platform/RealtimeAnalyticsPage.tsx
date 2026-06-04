import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Activity, Radio, BarChart3, Plus, Play, Trash2, AlertTriangle, RefreshCw, Gauge, TrendingUp, Zap } from 'lucide-react';

interface Dashboard { id: string; name: string; description: string; panels: number; refresh: number; created: string; status: string; }

const mockDashboards: Dashboard[] = [
  { id: 'db-1', name: 'Service Health', description: 'Real-time health metrics for all services', panels: 6, refresh: 5, created: '2026-05-15', status: 'active' },
  { id: 'db-2', name: 'Infrastructure Ops', description: 'CPU, memory, disk, network across fleet', panels: 4, refresh: 10, created: '2026-05-20', status: 'active' },
  { id: 'db-3', name: 'Business Metrics', description: 'Revenue, users, transactions — live', panels: 3, refresh: 30, created: '2026-05-25', status: 'active' },
];

const RealtimeAnalyticsPage: React.FC = () => {
  const [dashboards, setDashboards] = useState(mockDashboards);
  const [search, setSearch] = useState('');
  const [createOpen, setCreateOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [editDashboard, setEditDashboard] = useState<Dashboard | null>(null);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [dashboardToDelete, setDashboardToDelete] = useState<Dashboard | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const [selectedDashboard, setSelectedDashboard] = useState<Dashboard | null>(null);
  const [newDashboard, setNewDashboard] = useState({ name: '', description: '', refresh: '5' });
  const [liveTab, setLiveTab] = useState('dashboards');
  const [selectedLiveDb, setSelectedLiveDb] = useState('db-1');
  const [liveValues, setLiveValues] = useState<Record<string, number>>({});

  useEffect(() => {
    const interval = setInterval(() => {
      setLiveValues({ cpu: Math.random() * 100, mem: 40 + Math.random() * 30, reqs: 500 + Math.random() * 500, latency: 20 + Math.random() * 80, disk: 50 + Math.random() * 40, net: 200 + Math.random() * 600 });
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  const filtered = dashboards.filter(d => d.name.toLowerCase().includes(search.toLowerCase()) || d.description.toLowerCase().includes(search.toLowerCase()));

  const handleCreate = () => {
    const dashboard: Dashboard = {
      id: `db-${Date.now()}`,
      name: newDashboard.name,
      description: newDashboard.description,
      panels: 3,
      refresh: +newDashboard.refresh,
      created: new Date().toISOString().slice(0, 10),
      status: 'active',
    };
    setDashboards([...dashboards, dashboard]);
    setCreateOpen(false);
    setNewDashboard({ name: '', description: '', refresh: '5' });
  };

  const handleEdit = () => {
    if (!editDashboard) return;
    setDashboards(dashboards.map(d => d.id === editDashboard.id ? editDashboard : d));
    setEditOpen(false);
    setEditDashboard(null);
  };

  const handleDelete = () => {
    if (!dashboardToDelete) return;
    setDashboards(dashboards.filter(d => d.id !== dashboardToDelete.id));
    setDeleteOpen(false);
    setDashboardToDelete(null);
  };

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Real-Time Analytics Dashboard</h1>
          <p className="text-muted-foreground">Live streaming dashboards for operational metrics with sub-second refresh and alerts</p>
        </div>
        <Dialog open={createOpen} onOpenChange={setCreateOpen}>
          <DialogTrigger asChild><Button><Plus className="mr-2 h-4 w-4" />Create Dashboard</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>New Live Dashboard</DialogTitle></DialogHeader>
            <div className="space-y-4">
              <div><Label>Name</Label><Input value={newDashboard.name} onChange={e => setNewDashboard({ ...newDashboard, name: e.target.value })} placeholder="e.g. Service Health" /></div>
              <div><Label>Description</Label><Input value={newDashboard.description} onChange={e => setNewDashboard({ ...newDashboard, description: e.target.value })} placeholder="Brief description" /></div>
              <div><Label>Refresh Interval</Label>
                <Select value={newDashboard.refresh} onValueChange={v => setNewDashboard({ ...newDashboard, refresh: v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent><SelectItem value="1">1 second</SelectItem><SelectItem value="5">5 seconds</SelectItem><SelectItem value="10">10 seconds</SelectItem><SelectItem value="30">30 seconds</SelectItem></SelectContent>
                </Select>
              </div>
              <Button className="w-full" onClick={handleCreate}>Create</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Dashboards</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{dashboards.length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Metrics Tracked</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">24</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Active Alerts</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-yellow-400">3</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Data Points/sec</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">1,200</div></CardContent></Card>
      </div>

      <Tabs defaultValue="dashboards">
        <TabsList>
          <TabsTrigger value="dashboards"><Activity className="mr-2 h-4 w-4" />Dashboards</TabsTrigger>
          <TabsTrigger value="live"><Zap className="mr-2 h-4 w-4" />Live View</TabsTrigger>
          <TabsTrigger value="alerts"><AlertTriangle className="mr-2 h-4 w-4" />Alert Rules</TabsTrigger>
          <TabsTrigger value="metrics"><BarChart3 className="mr-2 h-4 w-4" />Metrics</TabsTrigger>
        </TabsList>

        <TabsContent value="dashboards">
          <div className="flex gap-2 mb-4">
            <Input placeholder="Search dashboards..." value={search} onChange={e => setSearch(e.target.value)} className="max-w-sm" />
            <Button variant="outline" size="sm" onClick={() => setSearch('')}>Clear</Button>
          </div>
          <Table>
            <TableHeader><TableRow><TableHead>Name</TableHead><TableHead>Description</TableHead><TableHead>Panels</TableHead><TableHead>Refresh</TableHead><TableHead>Status</TableHead><TableHead>Created</TableHead><TableHead>Actions</TableHead></TableRow></TableHeader>
            <TableBody>
              {filtered.map(d => (
                <TableRow key={d.id}>
                  <TableCell className="font-medium cursor-pointer hover:text-blue-400" onClick={() => { setSelectedDashboard(d); setDetailOpen(true); }}>{d.name}</TableCell>
                  <TableCell className="text-sm text-muted-foreground max-w-xs truncate">{d.description}</TableCell>
                  <TableCell>{d.panels}</TableCell>
                  <TableCell>Every {d.refresh}s</TableCell>
                  <TableCell><Badge className="bg-green-600">{d.status}</Badge></TableCell>
                  <TableCell className="text-sm">{d.created}</TableCell>
                  <TableCell>
                    <div className="flex gap-1">
                      <Button size="sm" variant="ghost" onClick={() => { setEditDashboard({ ...d }); setEditOpen(true); }}>Edit</Button>
                      <Button size="sm" variant="ghost" className="text-red-400" onClick={() => { setDashboardToDelete(d); setDeleteOpen(true); }}><Trash2 className="h-4 w-4" /></Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TabsContent>

        <TabsContent value="live">
          <div className="flex gap-2 mb-4">
            <Select value={selectedLiveDb} onValueChange={setSelectedLiveDb}>
              <SelectTrigger className="w-64"><SelectValue /></SelectTrigger>
              <SelectContent>{dashboards.map(d => <SelectItem key={d.id} value={d.id}>{d.name}</SelectItem>)}</SelectContent>
            </Select>
            <Badge variant="outline" className="animate-pulse"><Activity className="mr-1 h-3 w-3" />Live</Badge>
            <Badge variant="outline">Every {dashboards.find(d => d.id === selectedLiveDb)?.refresh ?? 5}s</Badge>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card><CardHeader className="pb-2"><CardTitle className="text-sm">CPU Usage</CardTitle></CardHeader>
              <CardContent><div className="text-4xl font-bold font-mono">{liveValues.cpu?.toFixed(1) ?? '--'}%</div>
                <div className="mt-2 w-full bg-gray-700 rounded-full h-2"><div className="bg-blue-500 h-2 rounded-full" style={{ width: `${liveValues.cpu ?? 0}%` }} /></div>
              </CardContent>
            </Card>
            <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Memory Usage</CardTitle></CardHeader>
              <CardContent><div className="text-4xl font-bold font-mono">{liveValues.mem?.toFixed(1) ?? '--'}%</div>
                <div className="mt-2 w-full bg-gray-700 rounded-full h-2"><div className="bg-green-500 h-2 rounded-full" style={{ width: `${liveValues.mem ?? 0}%` }} /></div>
              </CardContent>
            </Card>
            <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Requests/sec</CardTitle></CardHeader>
              <CardContent><div className="text-4xl font-bold font-mono">{liveValues.reqs?.toFixed(0) ?? '--'}</div>
                <p className="text-xs text-muted-foreground mt-1">Avg latency: {liveValues.latency?.toFixed(0) ?? '--'}ms</p>
              </CardContent>
            </Card>
            <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Disk I/O</CardTitle></CardHeader>
              <CardContent><div className="text-4xl font-bold font-mono">{liveValues.disk?.toFixed(1) ?? '--'}%</div>
                <div className="mt-2 w-full bg-gray-700 rounded-full h-2"><div className="bg-purple-500 h-2 rounded-full" style={{ width: `${liveValues.disk ?? 0}%` }} /></div>
              </CardContent>
            </Card>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
            <Card><CardHeader><CardTitle>Throughput (last 5 min)</CardTitle></CardHeader>
              <CardContent>
                <div className="h-32 flex items-end justify-between gap-1 px-2">
                  {[65, 72, 58, 81, 75, 68, 70, 85, 78, 82, 74, 69, 71, 77, 80].map((v, i) => (
                    <div key={i} className="bg-blue-500 w-4 rounded-t" style={{ height: `${v}%` }} title={`${v} req/s`} />
                  ))}
                </div>
                <div className="text-xs text-muted-foreground text-center mt-2">Last 5 minutes (15 samples)</div>
              </CardContent>
            </Card>
            <Card><CardHeader><CardTitle>Error Rate</CardTitle></CardHeader>
              <CardContent>
                <div className="h-32 flex items-end justify-between gap-1 px-2">
                  {[3, 5, 2, 4, 8, 3, 2, 6, 4, 3, 5, 2, 3, 4, 3].map((v, i) => (
                    <div key={i} className="bg-red-500 w-4 rounded-t" style={{ height: `${v * 10}%` }} title={`${v}% errors`} />
                  ))}
                </div>
                <div className="text-xs text-muted-foreground text-center mt-2">Error rate over last 5 minutes</div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="alerts">
          <div className="flex gap-2 mb-4">
            <Dialog><DialogTrigger asChild><Button variant="outline"><Plus className="mr-2 h-4 w-4" />Create Alert</Button></DialogTrigger>
              <DialogContent><DialogHeader><DialogTitle>New Alert Rule</DialogTitle></DialogHeader>
                <div className="space-y-4">
                  <div><Label>Name</Label><Input placeholder="e.g. High CPU" /></div>
                  <div><Label>Metric</Label><Input placeholder="e.g. cpu_usage" /></div>
                  <div><Label>Condition</Label>
                    <Select><SelectTrigger><SelectValue placeholder="above" /></SelectTrigger><SelectContent><SelectItem value="above">Above</SelectItem><SelectItem value="below">Below</SelectItem></SelectContent></Select>
                  </div>
                  <div><Label>Threshold</Label><Input type="number" placeholder="90" /></div>
                  <div><Label>Severity</Label><Select><SelectTrigger><SelectValue placeholder="warning" /></SelectTrigger><SelectContent><SelectItem value="critical">Critical</SelectItem><SelectItem value="warning">Warning</SelectItem><SelectItem value="info">Info</SelectItem></SelectContent></Select></div>
                  <Button className="w-full">Create</Button>
                </div>
              </DialogContent>
            </Dialog>
            <Button variant="outline"><RefreshCw className="mr-2 h-4 w-4" />Evaluate All</Button>
          </div>
          <Table>
            <TableHeader><TableRow><TableHead>Alert</TableHead><TableHead>Metric</TableHead><TableHead>Condition</TableHead><TableHead>Threshold</TableHead><TableHead>Severity</TableHead><TableHead>Status</TableHead><TableHead>Last Triggered</TableHead><TableHead>Actions</TableHead></TableRow></TableHeader>
            <TableBody>
              <TableRow><TableCell>High CPU</TableCell><TableCell>cpu_usage</TableCell><TableCell>Above</TableCell><TableCell>90%</TableCell><TableCell><Badge variant="destructive">Critical</Badge></TableCell><TableCell><Badge>Active</Badge></TableCell><TableCell>2026-05-30 10:02</TableCell><TableCell><Button size="sm" variant="ghost">Mute</Button></TableCell></TableRow>
              <TableRow><TableCell>Memory Warning</TableCell><TableCell>mem_usage</TableCell><TableCell>Above</TableCell><TableCell>85%</TableCell><TableCell><Badge>Warning</Badge></TableCell><TableCell><Badge>Active</Badge></TableCell><TableCell>2026-05-30 09:45</TableCell><TableCell><Button size="sm" variant="ghost">Mute</Button></TableCell></TableRow>
              <TableRow><TableCell>Low Throughput</TableCell><TableCell>throughput</TableCell><TableCell>Below</TableCell><TableCell>100 req/s</TableCell><TableCell><Badge variant="secondary">Info</Badge></TableCell><TableCell><Badge variant="outline">Inactive</Badge></TableCell><TableCell>—</TableCell><TableCell><Button size="sm" variant="ghost">Enable</Button></TableCell></TableRow>
            </TableBody>
          </Table>
        </TabsContent>

        <TabsContent value="metrics">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <Card><CardHeader><CardTitle>Metric Explorer</CardTitle></CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div><Label>Metric</Label>
                    <Select><SelectTrigger><SelectValue placeholder="Select metric..." /></SelectTrigger>
                      <SelectContent><SelectItem value="cpu">CPU Usage</SelectItem><SelectItem value="mem">Memory Usage</SelectItem><SelectItem value="reqs">Requests/sec</SelectItem><SelectItem value="latency">Latency</SelectItem></SelectContent>
                    </Select>
                  </div>
                  <div><Label>Time Range</Label>
                    <Select><SelectTrigger><SelectValue placeholder="Last 1 hour" /></SelectTrigger>
                      <SelectContent><SelectItem value="15m">Last 15 min</SelectItem><SelectItem value="1h">Last 1 hour</SelectItem><SelectItem value="6h">Last 6 hours</SelectItem><SelectItem value="24h">Last 24 hours</SelectItem></SelectContent>
                    </Select>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card><CardHeader><CardTitle>Current Snapshot</CardTitle></CardHeader>
              <CardContent>
                <div className="space-y-1">
                  <div className="flex justify-between"><span className="text-muted-foreground">CPU</span><span className="font-mono">{liveValues.cpu?.toFixed(1) ?? '--'}%</span></div>
                  <div className="flex justify-between"><span className="text-muted-foreground">Memory</span><span className="font-mono">{liveValues.mem?.toFixed(1) ?? '--'}%</span></div>
                  <div className="flex justify-between"><span className="text-muted-foreground">Requests</span><span className="font-mono">{liveValues.reqs?.toFixed(0) ?? '--'} req/s</span></div>
                  <div className="flex justify-between"><span className="text-muted-foreground">Latency</span><span className="font-mono">{liveValues.latency?.toFixed(0) ?? '--'}ms</span></div>
                </div>
              </CardContent>
            </Card>
          </div>
          <Table>
            <TableHeader><TableRow><TableHead>Metric</TableHead><TableHead>Type</TableHead><TableHead>Unit</TableHead><TableHead>Current</TableHead><TableHead>Avg (5m)</TableHead><TableHead>Peak (5m)</TableHead><TableHead>Min (5m)</TableHead></TableRow></TableHeader>
            <TableBody>
              <TableRow><TableCell className="font-medium">cpu_usage</TableCell><TableCell>gauge</TableCell><TableCell>%</TableCell><TableCell>{liveValues.cpu?.toFixed(1) ?? '--'}</TableCell><TableCell>62.3</TableCell><TableCell>95.1</TableCell><TableCell>12.4</TableCell></TableRow>
              <TableRow><TableCell className="font-medium">mem_usage</TableCell><TableCell>gauge</TableCell><TableCell>%</TableCell><TableCell>{liveValues.mem?.toFixed(1) ?? '--'}</TableCell><TableCell>55.8</TableCell><TableCell>82.4</TableCell><TableCell>32.1</TableCell></TableRow>
              <TableRow><TableCell className="font-medium">requests_per_sec</TableCell><TableCell>rate</TableCell><TableCell>req/s</TableCell><TableCell>{liveValues.reqs?.toFixed(0) ?? '--'}</TableCell><TableCell>742</TableCell><TableCell>1,204</TableCell><TableCell>312</TableCell></TableRow>
              <TableRow><TableCell className="font-medium">latency_ms</TableCell><TableCell>histogram</TableCell><TableCell>ms</TableCell><TableCell>{liveValues.latency?.toFixed(0) ?? '--'}</TableCell><TableCell>45</TableCell><TableCell>230</TableCell><TableCell>12</TableCell></TableRow>
            </TableBody>
          </Table>
        </TabsContent>
      </Tabs>

      <Dialog open={detailOpen} onOpenChange={setDetailOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader><DialogTitle>Dashboard Details — {selectedDashboard?.name}</DialogTitle></DialogHeader>
          {selectedDashboard && (
            <div className="space-y-3">
              <div className="flex justify-between"><span className="text-muted-foreground">Description</span><span className="text-sm max-w-xs text-right">{selectedDashboard.description}</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Panels</span><span>{selectedDashboard.panels}</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Refresh</span><span>Every {selectedDashboard.refresh}s</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Created</span><span>{selectedDashboard.created}</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Status</span><Badge className="bg-green-600">{selectedDashboard.status}</Badge></div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>Edit Dashboard</DialogTitle></DialogHeader>
          {editDashboard && (
            <div className="space-y-4">
              <div><Label>Name</Label><Input value={editDashboard.name} onChange={e => setEditDashboard({ ...editDashboard, name: e.target.value })} /></div>
              <div><Label>Description</Label><Input value={editDashboard.description} onChange={e => setEditDashboard({ ...editDashboard, description: e.target.value })} /></div>
              <div><Label>Refresh (seconds)</Label><Input type="number" value={editDashboard.refresh} onChange={e => setEditDashboard({ ...editDashboard, refresh: +e.target.value })} /></div>
              <Button className="w-full" onClick={handleEdit}>Save Changes</Button>
            </div>
          )}
        </DialogContent>
      </Dialog>

      <Dialog open={deleteOpen} onOpenChange={setDeleteOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>Delete Dashboard</DialogTitle></DialogHeader>
          <p className="text-sm text-muted-foreground">Are you sure you want to delete <strong>{dashboardToDelete?.name}</strong>?</p>
          <div className="flex gap-2 justify-end">
            <Button variant="outline" onClick={() => setDeleteOpen(false)}>Cancel</Button>
            <Button variant="destructive" onClick={handleDelete}>Delete</Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default RealtimeAnalyticsPage;
