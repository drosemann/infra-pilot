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
import { LayoutDashboard, BarChart3, PieChart, LineChart, Plus, Play, Download, Clock, Share2, FileText, Save, Trash2 } from 'lucide-react';

interface Report { id: string; name: string; description: string; mode: string; widgets: number; created: string; lastRun: string; }
interface Schedule { id: string; report: string; cron: string; format: string; recipients: string; enabled: boolean; lastRun: string; }

const mockReports: Report[] = [
  { id: 'r-1', name: 'Monthly Revenue Report', description: 'Revenue breakdown by product line', mode: 'hybrid', widgets: 4, created: '2026-05-01', lastRun: '2026-05-30' },
  { id: 'r-2', name: 'User Growth Dashboard', description: 'New users, active users, churn trends', mode: 'visual', widgets: 3, created: '2026-04-15', lastRun: '2026-05-29' },
  { id: 'r-3', name: 'Infrastructure Cost Analysis', description: 'Cost per service, provider, region', mode: 'sql', widgets: 2, created: '2026-05-10', lastRun: '2026-05-28' },
];

const mockSchedules: Schedule[] = [
  { id: 's-1', report: 'Monthly Revenue Report', cron: '0 0 1 * *', format: 'pdf', recipients: 'execs@company.com', enabled: true, lastRun: '2026-05-01' },
  { id: 's-2', report: 'User Growth Dashboard', cron: '0 8 * * 1', format: 'csv', recipients: 'analytics@company.com', enabled: true, lastRun: '2026-05-26' },
];

const SelfServiceReportingPage: React.FC = () => {
  const [reports, setReports] = useState(mockReports);
  const [schedules, setSchedules] = useState(mockSchedules);
  const [search, setSearch] = useState('');
  const [createOpen, setCreateOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [editReport, setEditReport] = useState<Report | null>(null);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [reportToDelete, setReportToDelete] = useState<Report | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);
  const [newReport, setNewReport] = useState({ name: '', description: '', mode: 'visual' });
  const [scheduleCreateOpen, setScheduleCreateOpen] = useState(false);
  const [newSchedule, setNewSchedule] = useState({ report: '', cron: '0 0 1 * *', format: 'pdf', recipients: '' });

  const filtered = reports.filter(r => r.name.toLowerCase().includes(search.toLowerCase()) || r.description.toLowerCase().includes(search.toLowerCase()));

  const handleCreate = () => {
    const report: Report = {
      id: `r-${Date.now()}`,
      name: newReport.name,
      description: newReport.description,
      mode: newReport.mode,
      widgets: 1,
      created: new Date().toISOString().slice(0, 10),
      lastRun: 'Never',
    };
    setReports([...reports, report]);
    setCreateOpen(false);
    setNewReport({ name: '', description: '', mode: 'visual' });
  };

  const handleEdit = () => {
    if (!editReport) return;
    setReports(reports.map(r => r.id === editReport.id ? editReport : r));
    setEditOpen(false);
    setEditReport(null);
  };

  const handleDelete = () => {
    if (!reportToDelete) return;
    setReports(reports.filter(r => r.id !== reportToDelete.id));
    setDeleteOpen(false);
    setReportToDelete(null);
  };

  const handleCreateSchedule = () => {
    const schedule: Schedule = {
      id: `s-${Date.now()}`,
      report: newSchedule.report,
      cron: newSchedule.cron,
      format: newSchedule.format,
      recipients: newSchedule.recipients,
      enabled: true,
      lastRun: 'Never',
    };
    setSchedules([...schedules, schedule]);
    setScheduleCreateOpen(false);
    setNewSchedule({ report: '', cron: '0 0 1 * *', format: 'pdf', recipients: '' });
  };

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Self-Service Reporting</h1>
          <p className="text-muted-foreground">Drag-and-drop report builder with SQL and visual modes, scheduled delivery</p>
        </div>
        <Dialog open={createOpen} onOpenChange={setCreateOpen}>
          <DialogTrigger asChild><Button><Plus className="mr-2 h-4 w-4" />Create Report</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>New Report</DialogTitle></DialogHeader>
            <div className="space-y-4">
              <div><Label>Name</Label><Input value={newReport.name} onChange={e => setNewReport({ ...newReport, name: e.target.value })} placeholder="e.g. Monthly Revenue" /></div>
              <div><Label>Description</Label><Input value={newReport.description} onChange={e => setNewReport({ ...newReport, description: e.target.value })} placeholder="Brief description" /></div>
              <div><Label>Mode</Label>
                <Select value={newReport.mode} onValueChange={v => setNewReport({ ...newReport, mode: v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent><SelectItem value="visual">Visual (Drag & Drop)</SelectItem><SelectItem value="sql">SQL Editor</SelectItem><SelectItem value="hybrid">Hybrid</SelectItem></SelectContent>
                </Select>
              </div>
              <div><Label>Dataset</Label>
                <Select><SelectTrigger><SelectValue placeholder="Select dataset..." /></SelectTrigger>
                  <SelectContent><SelectItem value="orders">Orders</SelectItem><SelectItem value="users">Users</SelectItem><SelectItem value="events">Events</SelectItem></SelectContent>
                </Select>
              </div>
              <Button className="w-full" onClick={handleCreate}>Create</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Reports</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{reports.length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Widgets</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{reports.reduce((s, r) => s + r.widgets, 0)}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Schedules</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{schedules.length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Deliveries (30d)</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">24</div></CardContent></Card>
      </div>

      <Tabs defaultValue="reports">
        <TabsList>
          <TabsTrigger value="reports"><LayoutDashboard className="mr-2 h-4 w-4" />Reports</TabsTrigger>
          <TabsTrigger value="builder"><BarChart3 className="mr-2 h-4 w-4" />Builder</TabsTrigger>
          <TabsTrigger value="schedules"><Clock className="mr-2 h-4 w-4" />Schedules</TabsTrigger>
          <TabsTrigger value="deliveries"><Download className="mr-2 h-4 w-4" />Deliveries</TabsTrigger>
        </TabsList>

        <TabsContent value="reports">
          <div className="flex gap-2 mb-4">
            <Input placeholder="Search reports..." value={search} onChange={e => setSearch(e.target.value)} className="max-w-sm" />
            <Button variant="outline" size="sm" onClick={() => setSearch('')}>Clear</Button>
          </div>
          <Table>
            <TableHeader><TableRow><TableHead>Name</TableHead><TableHead>Description</TableHead><TableHead>Mode</TableHead><TableHead>Widgets</TableHead><TableHead>Created</TableHead><TableHead>Last Run</TableHead><TableHead>Actions</TableHead></TableRow></TableHeader>
            <TableBody>
              {filtered.map(r => (
                <TableRow key={r.id}>
                  <TableCell className="font-medium cursor-pointer hover:text-blue-400" onClick={() => { setSelectedReport(r); setDetailOpen(true); }}>{r.name}</TableCell>
                  <TableCell className="text-sm text-muted-foreground max-w-xs truncate">{r.description}</TableCell>
                  <TableCell><Badge variant="outline">{r.mode}</Badge></TableCell>
                  <TableCell>{r.widgets}</TableCell>
                  <TableCell className="text-sm">{r.created}</TableCell>
                  <TableCell className="text-sm">{r.lastRun}</TableCell>
                  <TableCell>
                    <div className="flex gap-1">
                      <Button size="sm" variant="ghost"><Play className="h-4 w-4" /></Button>
                      <Button size="sm" variant="ghost" onClick={() => { setEditReport({ ...r }); setEditOpen(true); }}>Edit</Button>
                      <Button size="sm" variant="ghost"><Share2 className="h-4 w-4" /></Button>
                      <Button size="sm" variant="ghost" className="text-red-400" onClick={() => { setReportToDelete(r); setDeleteOpen(true); }}>Delete</Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TabsContent>

        <TabsContent value="builder">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <Card className="lg:col-span-2">
              <CardHeader><CardTitle>Canvas — Monthly Revenue Report</CardTitle></CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4">
                  <div className="border-2 border-dashed border-gray-600 rounded-lg p-8 flex items-center justify-center min-h-[200px]">
                    <div className="text-center"><BarChart3 className="h-8 w-8 mx-auto mb-2 text-muted-foreground" /><span className="text-sm text-muted-foreground">Bar Chart — Revenue by Product</span></div>
                  </div>
                  <div className="border-2 border-dashed border-gray-600 rounded-lg p-8 flex items-center justify-center min-h-[200px]">
                    <div className="text-center"><LineChart className="h-8 w-8 mx-auto mb-2 text-muted-foreground" /><span className="text-sm text-muted-foreground">Line Chart — Revenue Trend</span></div>
                  </div>
                  <div className="border-2 border-dashed border-gray-600 rounded-lg p-8 flex items-center justify-center min-h-[200px]">
                    <div className="text-center"><PieChart className="h-8 w-8 mx-auto mb-2 text-muted-foreground" /><span className="text-sm text-muted-foreground">Pie Chart — By Category</span></div>
                  </div>
                  <div className="border-2 border-dashed border-gray-600 rounded-lg p-8 flex items-center justify-center min-h-[200px]">
                    <div className="text-center"><FileText className="h-8 w-8 mx-auto mb-2 text-muted-foreground" /><span className="text-sm text-muted-foreground">Table — Top Customers</span></div>
                  </div>
                </div>
                <div className="flex gap-2 mt-4">
                  <Button><Download className="mr-2 h-4 w-4" />Export PDF</Button>
                  <Button variant="outline"><Download className="mr-2 h-4 w-4" />Export CSV</Button>
                  <Button variant="outline"><Save className="mr-2 h-4 w-4" />Save Draft</Button>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle>Widget Library</CardTitle></CardHeader>
              <CardContent className="space-y-2">
                <Button variant="outline" className="w-full justify-start"><BarChart3 className="mr-2 h-4 w-4" />Bar Chart</Button>
                <Button variant="outline" className="w-full justify-start"><LineChart className="mr-2 h-4 w-4" />Line Chart</Button>
                <Button variant="outline" className="w-full justify-start"><PieChart className="mr-2 h-4 w-4" />Pie Chart</Button>
                <Button variant="outline" className="w-full justify-start"><FileText className="mr-2 h-4 w-4" />Table</Button>
                <Button variant="outline" className="w-full justify-start"><BarChart3 className="mr-2 h-4 w-4" />Area Chart</Button>
                <Button variant="outline" className="w-full justify-start"><BarChart3 className="mr-2 h-4 w-4" />Metric Card</Button>
                <div className="pt-2 border-t border-gray-700">
                  <Label className="text-xs">Data Source</Label>
                  <Select><SelectTrigger><SelectValue placeholder="Orders" /></SelectTrigger>
                    <SelectContent><SelectItem value="orders">Orders</SelectItem><SelectItem value="users">Users</SelectItem><SelectItem value="events">Events</SelectItem></SelectContent>
                  </Select>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="schedules">
          <div className="flex gap-2 mb-4">
            <Dialog open={scheduleCreateOpen} onOpenChange={setScheduleCreateOpen}>
              <DialogTrigger asChild><Button variant="outline"><Plus className="mr-2 h-4 w-4" />Add Schedule</Button></DialogTrigger>
              <DialogContent><DialogHeader><DialogTitle>New Schedule</DialogTitle></DialogHeader>
                <div className="space-y-4">
                  <div><Label>Report</Label>
                    <Select value={newSchedule.report} onValueChange={v => setNewSchedule({ ...newSchedule, report: v })}>
                      <SelectTrigger><SelectValue placeholder="Select report..." /></SelectTrigger>
                      <SelectContent>{reports.map(r => <SelectItem key={r.id} value={r.id}>{r.name}</SelectItem>)}</SelectContent>
                    </Select>
                  </div>
                  <div><Label>Cron Expression</Label><Input value={newSchedule.cron} onChange={e => setNewSchedule({ ...newSchedule, cron: e.target.value })} placeholder="0 0 1 * *" /></div>
                  <div><Label>Format</Label>
                    <Select value={newSchedule.format} onValueChange={v => setNewSchedule({ ...newSchedule, format: v })}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent><SelectItem value="pdf">PDF</SelectItem><SelectItem value="csv">CSV</SelectItem><SelectItem value="excel">Excel</SelectItem></SelectContent>
                    </Select>
                  </div>
                  <div><Label>Recipients</Label><Input value={newSchedule.recipients} onChange={e => setNewSchedule({ ...newSchedule, recipients: e.target.value })} placeholder="email@company.com" /></div>
                  <Button className="w-full" onClick={handleCreateSchedule}>Create</Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>
          <Table>
            <TableHeader><TableRow><TableHead>Report</TableHead><TableHead>Cron</TableHead><TableHead>Format</TableHead><TableHead>Recipients</TableHead><TableHead>Status</TableHead><TableHead>Last Run</TableHead><TableHead>Actions</TableHead></TableRow></TableHeader>
            <TableBody>
              {schedules.map(s => (
                <TableRow key={s.id}>
                  <TableCell className="font-medium">{s.report}</TableCell>
                  <TableCell className="font-mono text-xs">{s.cron}</TableCell>
                  <TableCell><Badge variant="outline">{s.format}</Badge></TableCell>
                  <TableCell className="text-xs">{s.recipients}</TableCell>
                  <TableCell>{s.enabled ? <Badge className="bg-green-600">Active</Badge> : <Badge variant="secondary">Disabled</Badge>}</TableCell>
                  <TableCell className="text-sm">{s.lastRun}</TableCell>
                  <TableCell>
                    <div className="flex gap-1">
                      <Button size="sm" variant="ghost"><Play className="h-4 w-4" /></Button>
                      <Button size="sm" variant="ghost">Edit</Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TabsContent>

        <TabsContent value="deliveries">
          <Table>
            <TableHeader><TableRow><TableHead>Delivery</TableHead><TableHead>Report</TableHead><TableHead>Format</TableHead><TableHead>Recipients</TableHead><TableHead>Status</TableHead><TableHead>Delivered At</TableHead><TableHead>Size</TableHead></TableRow></TableHeader>
            <TableBody>
              <TableRow><TableCell>1</TableCell><TableCell>Monthly Revenue Report</TableCell><TableCell>PDF</TableCell><TableCell>execs@company.com</TableCell><TableCell><Badge className="bg-green-600">Delivered</Badge></TableCell><TableCell>2026-05-30 06:00</TableCell><TableCell>2.4 MB</TableCell></TableRow>
              <TableRow><TableCell>2</TableCell><TableCell>User Growth Dashboard</TableCell><TableCell>CSV</TableCell><TableCell>analytics@company.com</TableCell><TableCell><Badge className="bg-green-600">Delivered</Badge></TableCell><TableCell>2026-05-26 08:00</TableCell><TableCell>1.1 MB</TableCell></TableRow>
              <TableRow><TableCell>3</TableCell><TableCell>Infrastructure Cost Analysis</TableCell><TableCell>Excel</TableCell><TableCell>finops@company.com</TableCell><TableCell><Badge variant="secondary">Pending</Badge></TableCell><TableCell>—</TableCell><TableCell>—</TableCell></TableRow>
            </TableBody>
          </Table>
        </TabsContent>
      </Tabs>

      <Dialog open={detailOpen} onOpenChange={setDetailOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader><DialogTitle>Report Details — {selectedReport?.name}</DialogTitle></DialogHeader>
          {selectedReport && (
            <div className="space-y-3">
              <div className="flex justify-between"><span className="text-muted-foreground">Description</span><span className="text-sm max-w-xs text-right">{selectedReport.description}</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Mode</span><Badge variant="outline">{selectedReport.mode}</Badge></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Widgets</span><span>{selectedReport.widgets}</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Created</span><span>{selectedReport.created}</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Last Run</span><span>{selectedReport.lastRun}</span></div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>Edit Report</DialogTitle></DialogHeader>
          {editReport && (
            <div className="space-y-4">
              <div><Label>Name</Label><Input value={editReport.name} onChange={e => setEditReport({ ...editReport, name: e.target.value })} /></div>
              <div><Label>Description</Label><Input value={editReport.description} onChange={e => setEditReport({ ...editReport, description: e.target.value })} /></div>
              <Button className="w-full" onClick={handleEdit}>Save Changes</Button>
            </div>
          )}
        </DialogContent>
      </Dialog>

      <Dialog open={deleteOpen} onOpenChange={setDeleteOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>Delete Report</DialogTitle></DialogHeader>
          <p className="text-sm text-muted-foreground">Are you sure you want to delete <strong>{reportToDelete?.name}</strong>?</p>
          <div className="flex gap-2 justify-end">
            <Button variant="outline" onClick={() => setDeleteOpen(false)}>Cancel</Button>
            <Button variant="destructive" onClick={handleDelete}>Delete</Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default SelfServiceReportingPage;
