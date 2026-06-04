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
import { Progress } from '@/components/ui/progress';
import { CheckCircle2, XCircle, AlertTriangle, Plus, Play, BarChart3, FileText, RefreshCw, Shield } from 'lucide-react';

interface QualityRule {
  id: string; name: string; type: string; target: string; column: string; severity: string; threshold: number; status: string; lastCheck: string;
}

interface Violation {
  id: string; rule: string; severity: string; message: string; actual: number; threshold: number; detected: string; status: string;
}

const mockRules: QualityRule[] = [
  { id: 'qr-1', name: 'users-email-not-null', type: 'completeness', target: 'users', column: 'email', severity: 'critical', threshold: 99.0, status: 'passing', lastCheck: '2026-05-30T10:00:00Z' },
  { id: 'qr-2', name: 'orders-amount-positive', type: 'accuracy', target: 'orders', column: 'amount', severity: 'high', threshold: 100.0, status: 'passing', lastCheck: '2026-05-30T10:00:00Z' },
  { id: 'qr-3', name: 'events-freshness', type: 'freshness', target: 'user_events', column: 'ts', severity: 'medium', threshold: 300.0, status: 'failing', lastCheck: '2026-05-30T09:55:00Z' },
  { id: 'qr-4', name: 'user-ids-unique', type: 'uniqueness', target: 'users', column: 'id', severity: 'critical', threshold: 100.0, status: 'passing', lastCheck: '2026-05-30T08:00:00Z' },
];

const mockViolations: Violation[] = [
  { id: 'v-1', rule: 'events-freshness', severity: 'medium', message: 'Data is 425s behind — exceeds threshold of 300s', actual: 425, threshold: 300, detected: '2026-05-30T09:55:00Z', status: 'open' },
];

const DataQualityPage: React.FC = () => {
  const [rules, setRules] = useState(mockRules);
  const [violations, setViolations] = useState(mockViolations);
  const [tab, setTab] = useState('overview');
  const [ruleSearch, setRuleSearch] = useState('');
  const [createOpen, setCreateOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [editRule, setEditRule] = useState<QualityRule | null>(null);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [ruleToDelete, setRuleToDelete] = useState<QualityRule | null>(null);
  const [newRule, setNewRule] = useState({ name: '', type: 'freshness', target: '', column: '', threshold: 99, severity: 'medium' });

  const filteredRules = rules.filter(r => r.name.toLowerCase().includes(ruleSearch.toLowerCase()) || r.target.toLowerCase().includes(ruleSearch.toLowerCase()));

  const handleCreate = () => {
    const rule: QualityRule = {
      id: `qr-${Date.now()}`,
      name: newRule.name,
      type: newRule.type,
      target: newRule.target,
      column: newRule.column,
      severity: newRule.severity,
      threshold: newRule.threshold,
      status: 'passing',
      lastCheck: new Date().toISOString(),
    };
    setRules([...rules, rule]);
    setCreateOpen(false);
    setNewRule({ name: '', type: 'freshness', target: '', column: '', threshold: 99, severity: 'medium' });
  };

  const handleEdit = () => {
    if (!editRule) return;
    setRules(rules.map(r => r.id === editRule.id ? editRule : r));
    setEditOpen(false);
    setEditRule(null);
  };

  const handleDelete = () => {
    if (!ruleToDelete) return;
    setRules(rules.filter(r => r.id !== ruleToDelete.id));
    setDeleteOpen(false);
    setRuleToDelete(null);
  };

  const runAllChecks = () => {
    setRules(rules.map(r => ({ ...r, lastCheck: new Date().toISOString(), status: Math.random() > 0.2 ? 'passing' : 'failing' })));
    if (Math.random() > 0.7) {
      setViolations([...violations, { id: `v-${Date.now()}`, rule: 'events-freshness', severity: 'medium', message: 'New violation detected', actual: 450, threshold: 300, detected: new Date().toISOString(), status: 'open' }]);
    }
  };

  const ackViolation = (id: string) => {
    setViolations(violations.map(v => v.id === id ? { ...v, status: 'acknowledged' } : v));
  };

  const resolveViolation = (id: string) => {
    setViolations(violations.map(v => v.id === id ? { ...v, status: 'resolved' } : v));
  };

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Data Quality Framework</h1>
          <p className="text-muted-foreground">Define rules, automated monitoring, alerting, and scorecards</p>
        </div>
        <Dialog open={createOpen} onOpenChange={setCreateOpen}>
          <DialogTrigger asChild><Button><Plus className="mr-2 h-4 w-4" />Create Rule</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>New Quality Rule</DialogTitle></DialogHeader>
            <div className="space-y-4">
              <div><Label>Name</Label><Input value={newRule.name} onChange={e => setNewRule({ ...newRule, name: e.target.value })} placeholder="e.g. email-not-null" /></div>
              <div><Label>Type</Label>
                <Select value={newRule.type} onValueChange={v => setNewRule({ ...newRule, type: v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent><SelectItem value="freshness">Freshness</SelectItem><SelectItem value="completeness">Completeness</SelectItem><SelectItem value="uniqueness">Uniqueness</SelectItem><SelectItem value="accuracy">Accuracy</SelectItem><SelectItem value="volume">Volume</SelectItem></SelectContent>
                </Select>
              </div>
              <div><Label>Target Table</Label><Input value={newRule.target} onChange={e => setNewRule({ ...newRule, target: e.target.value })} placeholder="e.g. users" /></div>
              <div><Label>Column</Label><Input value={newRule.column} onChange={e => setNewRule({ ...newRule, column: e.target.value })} placeholder="e.g. email" /></div>
              <div><Label>Threshold (%)</Label><Input type="number" value={newRule.threshold} onChange={e => setNewRule({ ...newRule, threshold: +e.target.value })} /></div>
              <div><Label>Severity</Label>
                <Select value={newRule.severity} onValueChange={v => setNewRule({ ...newRule, severity: v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent><SelectItem value="critical">Critical</SelectItem><SelectItem value="high">High</SelectItem><SelectItem value="medium">Medium</SelectItem><SelectItem value="low">Low</SelectItem></SelectContent>
                </Select>
              </div>
              <Button className="w-full" onClick={handleCreate}>Create Rule</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Rules</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{rules.length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Passing</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-green-400">{rules.filter(r => r.status === 'passing').length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Failing</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-red-400">{rules.filter(r => r.status === 'failing').length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Open Violations</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-yellow-400">{violations.filter(v => v.status === 'open').length}</div></CardContent></Card>
      </div>

      <Tabs value={tab} onValueChange={setTab}>
        <TabsList>
          <TabsTrigger value="overview"><Shield className="mr-2 h-4 w-4" />Overview</TabsTrigger>
          <TabsTrigger value="rules"><FileText className="mr-2 h-4 w-4" />Rules</TabsTrigger>
          <TabsTrigger value="violations"><AlertTriangle className="mr-2 h-4 w-4" />Violations</TabsTrigger>
          <TabsTrigger value="scorecards"><BarChart3 className="mr-2 h-4 w-4" />Scorecards</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card><CardHeader><CardTitle>Quality Score — Users</CardTitle></CardHeader>
              <CardContent>
                <div className="text-4xl font-bold mb-2">98%</div>
                <Progress value={98} className="mb-2" />
                <div className="flex justify-between text-sm text-muted-foreground"><span>2 rules passing</span><span>0 rules failing</span></div>
              </CardContent>
            </Card>
            <Card><CardHeader><CardTitle>Quality Score — Orders</CardTitle></CardHeader>
              <CardContent>
                <div className="text-4xl font-bold mb-2">100%</div>
                <Progress value={100} className="mb-2" />
                <div className="flex justify-between text-sm text-muted-foreground"><span>1 rule passing</span><span>0 rules failing</span></div>
              </CardContent>
            </Card>
            <Card><CardHeader><CardTitle>Quality Score — Events</CardTitle></CardHeader>
              <CardContent>
                <div className="text-4xl font-bold mb-2">85%</div>
                <Progress value={85} className="mb-2" />
                <div className="flex justify-between text-sm text-muted-foreground"><span>0 rules passing</span><span>1 rule failing</span></div>
              </CardContent>
            </Card>
            <Card><CardHeader><CardTitle>Overall Health</CardTitle></CardHeader>
              <CardContent>
                <div className="text-4xl font-bold mb-2">94%</div>
                <Progress value={94} className="mb-2" />
                <div className="text-sm text-muted-foreground">Weighted average across all datasets</div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="rules">
          <div className="flex gap-2 mb-4">
            <Input placeholder="Search rules..." value={ruleSearch} onChange={e => setRuleSearch(e.target.value)} className="max-w-xs" />
            <Button onClick={runAllChecks}><Play className="mr-2 h-4 w-4" />Run All Checks</Button>
          </div>
          <Table>
            <TableHeader><TableRow><TableHead>Rule</TableHead><TableHead>Type</TableHead><TableHead>Target</TableHead><TableHead>Column</TableHead><TableHead>Severity</TableHead><TableHead>Threshold</TableHead><TableHead>Status</TableHead><TableHead>Last Check</TableHead><TableHead>Actions</TableHead></TableRow></TableHeader>
            <TableBody>
              {filteredRules.map(r => (
                <TableRow key={r.id}>
                  <TableCell className="font-medium">{r.name}</TableCell>
                  <TableCell><Badge variant="outline">{r.type}</Badge></TableCell>
                  <TableCell>{r.target}</TableCell>
                  <TableCell className="font-mono text-xs">{r.column}</TableCell>
                  <TableCell><Badge variant={r.severity === 'critical' ? 'destructive' : r.severity === 'high' ? 'default' : 'secondary'}>{r.severity}</Badge></TableCell>
                  <TableCell>{r.threshold}%</TableCell>
                  <TableCell>{r.status === 'passing' ? <Badge variant="default" className="bg-green-600"><CheckCircle2 className="mr-1 h-3 w-3" />Passing</Badge> : <Badge variant="destructive"><XCircle className="mr-1 h-3 w-3" />Failing</Badge>}</TableCell>
                  <TableCell className="text-sm text-muted-foreground">{new Date(r.lastCheck).toLocaleString()}</TableCell>
                  <TableCell>
                    <div className="flex gap-1">
                      <Button size="sm" variant="ghost" onClick={() => { setEditRule({ ...r }); setEditOpen(true); }}>Edit</Button>
                      <Button size="sm" variant="ghost" className="text-red-400" onClick={() => { setRuleToDelete(r); setDeleteOpen(true); }}>Delete</Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TabsContent>

        <TabsContent value="violations">
          <Table>
            <TableHeader><TableRow><TableHead>Rule</TableHead><TableHead>Severity</TableHead><TableHead>Message</TableHead><TableHead>Actual</TableHead><TableHead>Threshold</TableHead><TableHead>Detected</TableHead><TableHead>Status</TableHead><TableHead>Actions</TableHead></TableRow></TableHeader>
            <TableBody>
              {violations.map(v => (
                <TableRow key={v.id}>
                  <TableCell className="font-medium">{v.rule}</TableCell>
                  <TableCell><Badge variant="secondary">{v.severity}</Badge></TableCell>
                  <TableCell className="max-w-xs truncate">{v.message}</TableCell>
                  <TableCell className="text-red-400 font-mono">{v.actual}</TableCell>
                  <TableCell className="font-mono">{v.threshold}</TableCell>
                  <TableCell className="text-sm">{new Date(v.detected).toLocaleString()}</TableCell>
                  <TableCell><Badge variant={v.status === 'resolved' ? 'default' : 'outline'}>{v.status}</Badge></TableCell>
                  <TableCell>
                    <div className="flex gap-1">
                      {v.status === 'open' && <Button size="sm" variant="ghost" onClick={() => ackViolation(v.id)}>Ack</Button>}
                      {v.status !== 'resolved' && <Button size="sm" variant="ghost" onClick={() => resolveViolation(v.id)}>Resolve</Button>}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TabsContent>

        <TabsContent value="scorecards">
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {['users', 'orders', 'events'].map(ds => (
                <Card key={ds}><CardHeader><CardTitle className="capitalize">{ds}</CardTitle></CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold mb-2">{ds === 'events' ? '85%' : '98%'}</div>
                    <Progress value={ds === 'events' ? 85 : 98} />
                    <div className="mt-2 text-sm space-y-1">
                      <div className="flex justify-between"><span>Freshness</span><span>{Math.round(85 + Math.random() * 15)}%</span></div>
                      <div className="flex justify-between"><span>Completeness</span><span>{Math.round(90 + Math.random() * 10)}%</span></div>
                      <div className="flex justify-between"><span>Uniqueness</span><span>{Math.round(95 + Math.random() * 5)}%</span></div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
            <Card>
              <CardHeader><CardTitle>Quality Trends (Last 7 Days)</CardTitle></CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {[
                    { day: 'Mon', score: 96 }, { day: 'Tue', score: 94 }, { day: 'Wed', score: 97 },
                    { day: 'Thu', score: 95 }, { day: 'Fri', score: 93 }, { day: 'Sat', score: 94 }, { day: 'Sun', score: 94 },
                  ].map(d => (
                    <div key={d.day} className="flex items-center gap-3">
                      <span className="w-8 text-sm text-muted-foreground">{d.day}</span>
                      <Progress value={d.score} className="flex-1" />
                      <span className="w-10 text-sm text-right">{d.score}%</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>

      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>Edit Quality Rule</DialogTitle></DialogHeader>
          {editRule && (
            <div className="space-y-4">
              <div><Label>Name</Label><Input value={editRule.name} onChange={e => setEditRule({ ...editRule, name: e.target.value })} /></div>
              <div><Label>Type</Label>
                <Select value={editRule.type} onValueChange={v => setEditRule({ ...editRule, type: v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent><SelectItem value="freshness">Freshness</SelectItem><SelectItem value="completeness">Completeness</SelectItem><SelectItem value="uniqueness">Uniqueness</SelectItem><SelectItem value="accuracy">Accuracy</SelectItem></SelectContent>
                </Select>
              </div>
              <div><Label>Threshold (%)</Label><Input type="number" value={editRule.threshold} onChange={e => setEditRule({ ...editRule, threshold: +e.target.value })} /></div>
              <div><Label>Severity</Label>
                <Select value={editRule.severity} onValueChange={v => setEditRule({ ...editRule, severity: v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent><SelectItem value="critical">Critical</SelectItem><SelectItem value="high">High</SelectItem><SelectItem value="medium">Medium</SelectItem><SelectItem value="low">Low</SelectItem></SelectContent>
                </Select>
              </div>
              <Button className="w-full" onClick={handleEdit}>Save Changes</Button>
            </div>
          )}
        </DialogContent>
      </Dialog>

      <Dialog open={deleteOpen} onOpenChange={setDeleteOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>Delete Quality Rule</DialogTitle></DialogHeader>
          <p className="text-sm text-muted-foreground">Are you sure you want to delete <strong>{ruleToDelete?.name}</strong>?</p>
          <div className="flex gap-2 justify-end">
            <Button variant="outline" onClick={() => setDeleteOpen(false)}>Cancel</Button>
            <Button variant="destructive" onClick={handleDelete}>Delete</Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default DataQualityPage;
