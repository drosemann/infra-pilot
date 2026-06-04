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
import { Shield, Eye, EyeOff, Plus, Play, FileText, AlertTriangle } from 'lucide-react';

interface MaskingRule { id: string; name: string; technique: string; category: string; target: string; priority: number; enabled: boolean; }
interface MaskProfile { id: string; name: string; environment: string; rules: number; enabled: boolean; lastApplied: string; }

const mockRules: MaskingRule[] = [
  { id: 'mr-1', name: 'Mask Email', technique: 'pseudonymization', category: 'pii', target: 'users.email', priority: 10, enabled: true },
  { id: 'mr-2', name: 'Redact SSN', technique: 'redaction', category: 'pii', target: 'employees.ssn', priority: 5, enabled: true },
  { id: 'mr-3', name: 'Tokenize Card', technique: 'tokenization', category: 'financial', target: 'payments.card_number', priority: 5, enabled: true },
];

const mockProfiles: MaskProfile[] = [
  { id: 'mp-1', name: 'Staging Masking', environment: 'staging', rules: 3, enabled: true, lastApplied: '2026-05-30T08:00:00Z' },
  { id: 'mp-2', name: 'Dev Masking', environment: 'development', rules: 2, enabled: true, lastApplied: '2026-05-29T16:00:00Z' },
];

const DataMaskingPage: React.FC = () => {
  const [rules, setRules] = useState(mockRules);
  const [profiles] = useState(mockProfiles);
  const [ruleSearch, setRuleSearch] = useState('');
  const [createOpen, setCreateOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [editRule, setEditRule] = useState<MaskingRule | null>(null);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [ruleToDelete, setRuleToDelete] = useState<MaskingRule | null>(null);
  const [createProfileOpen, setCreateProfileOpen] = useState(false);
  const [newRule, setNewRule] = useState({ name: '', technique: 'redaction', category: 'pii', target: '', priority: 50 });
  const [newProfile, setNewProfile] = useState({ name: '', environment: 'staging' });

  const filteredRules = rules.filter(r => r.name.toLowerCase().includes(ruleSearch.toLowerCase()) || r.target.toLowerCase().includes(ruleSearch.toLowerCase()));

  const handleCreateRule = () => {
    const rule: MaskingRule = {
      id: `mr-${Date.now()}`,
      name: newRule.name,
      technique: newRule.technique,
      category: newRule.category,
      target: newRule.target,
      priority: newRule.priority,
      enabled: true,
    };
    setRules([...rules, rule]);
    setCreateOpen(false);
    setNewRule({ name: '', technique: 'redaction', category: 'pii', target: '', priority: 50 });
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

  const toggleRule = (id: string) => {
    setRules(rules.map(r => r.id === id ? { ...r, enabled: !r.enabled } : r));
  };

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Data Masking & Anonymization</h1>
          <p className="text-muted-foreground">Dynamic data masking for non-production environments — PII, PHI, financial data protection</p>
        </div>
        <Dialog open={createOpen} onOpenChange={setCreateOpen}>
          <DialogTrigger asChild><Button><Plus className="mr-2 h-4 w-4" />Create Rule</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>New Masking Rule</DialogTitle></DialogHeader>
            <div className="space-y-4">
              <div><Label>Name</Label><Input value={newRule.name} onChange={e => setNewRule({ ...newRule, name: e.target.value })} placeholder="e.g. Mask Email" /></div>
              <div><Label>Technique</Label>
                <Select value={newRule.technique} onValueChange={v => setNewRule({ ...newRule, technique: v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent><SelectItem value="redaction">Redaction</SelectItem><SelectItem value="tokenization">Tokenization</SelectItem><SelectItem value="pseudonymization">Pseudonymization</SelectItem><SelectItem value="generalization">Generalization</SelectItem><SelectItem value="nulling">Nulling</SelectItem></SelectContent>
                </Select>
              </div>
              <div><Label>Data Category</Label>
                <Select value={newRule.category} onValueChange={v => setNewRule({ ...newRule, category: v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent><SelectItem value="pii">PII</SelectItem><SelectItem value="phi">PHI</SelectItem><SelectItem value="financial">Financial</SelectItem><SelectItem value="credentials">Credentials</SelectItem></SelectContent>
                </Select>
              </div>
              <div><Label>Target Column</Label><Input value={newRule.target} onChange={e => setNewRule({ ...newRule, target: e.target.value })} placeholder="e.g. users.email" /></div>
              <div><Label>Priority</Label><Input type="number" value={newRule.priority} onChange={e => setNewRule({ ...newRule, priority: +e.target.value })} /></div>
              <Button className="w-full" onClick={handleCreateRule}>Create Rule</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Rules</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{rules.length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Profiles</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{profiles.length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Environments</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">2</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Rows Masked</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">12.5K</div></CardContent></Card>
      </div>

      <Tabs defaultValue="rules">
        <TabsList>
          <TabsTrigger value="rules"><EyeOff className="mr-2 h-4 w-4" />Masking Rules</TabsTrigger>
          <TabsTrigger value="profiles"><Shield className="mr-2 h-4 w-4" />Profiles</TabsTrigger>
          <TabsTrigger value="preview"><Eye className="mr-2 h-4 w-4" />Preview</TabsTrigger>
          <TabsTrigger value="audit"><FileText className="mr-2 h-4 w-4" />Audit Log</TabsTrigger>
        </TabsList>

        <TabsContent value="rules">
          <div className="flex gap-2 mb-4">
            <Input placeholder="Search rules, targets..." value={ruleSearch} onChange={e => setRuleSearch(e.target.value)} className="max-w-sm" />
            <Button variant="outline" size="sm" onClick={() => setRuleSearch('')}>Clear</Button>
          </div>
          <Table>
            <TableHeader><TableRow><TableHead>Rule</TableHead><TableHead>Technique</TableHead><TableHead>Category</TableHead><TableHead>Target</TableHead><TableHead>Priority</TableHead><TableHead>Status</TableHead><TableHead>Actions</TableHead></TableRow></TableHeader>
            <TableBody>
              {filteredRules.map(r => (
                <TableRow key={r.id}>
                  <TableCell className="font-medium">{r.name}</TableCell>
                  <TableCell><Badge variant="outline">{r.technique}</Badge></TableCell>
                  <TableCell><Badge variant={r.category === 'pii' ? 'destructive' : 'secondary'}>{r.category}</Badge></TableCell>
                  <TableCell className="font-mono text-xs">{r.target}</TableCell>
                  <TableCell>{r.priority}</TableCell>
                  <TableCell>
                    <Button size="sm" variant="ghost" onClick={() => toggleRule(r.id)}>
                      {r.enabled ? <Badge className="bg-green-600">Enabled</Badge> : <Badge variant="secondary">Disabled</Badge>}
                    </Button>
                  </TableCell>
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

        <TabsContent value="profiles">
          <div className="flex gap-2 mb-4">
            <Dialog open={createProfileOpen} onOpenChange={setCreateProfileOpen}>
              <DialogTrigger asChild><Button variant="outline"><Plus className="mr-2 h-4 w-4" />Create Profile</Button></DialogTrigger>
              <DialogContent><DialogHeader><DialogTitle>New Masking Profile</DialogTitle></DialogHeader>
                <div className="space-y-4">
                  <div><Label>Name</Label><Input value={newProfile.name} onChange={e => setNewProfile({ ...newProfile, name: e.target.value })} placeholder="e.g. Staging Masking" /></div>
                  <div><Label>Environment</Label>
                    <Select value={newProfile.environment} onValueChange={v => setNewProfile({ ...newProfile, environment: v })}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent><SelectItem value="development">Development</SelectItem><SelectItem value="staging">Staging</SelectItem><SelectItem value="testing">Testing</SelectItem></SelectContent>
                    </Select>
                  </div>
                  <Button className="w-full" onClick={() => setCreateProfileOpen(false)}>Create</Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>
          <Table>
            <TableHeader><TableRow><TableHead>Profile</TableHead><TableHead>Environment</TableHead><TableHead>Rules</TableHead><TableHead>Status</TableHead><TableHead>Last Applied</TableHead><TableHead>Actions</TableHead></TableRow></TableHeader>
            <TableBody>
              {profiles.map(p => (
                <TableRow key={p.id}>
                  <TableCell className="font-medium">{p.name}</TableCell>
                  <TableCell><Badge variant="secondary">{p.environment}</Badge></TableCell>
                  <TableCell>{p.rules}</TableCell>
                  <TableCell>{p.enabled ? <Badge className="bg-green-600">Active</Badge> : <Badge variant="secondary">Inactive</Badge>}</TableCell>
                  <TableCell className="text-sm">{new Date(p.lastApplied).toLocaleString()}</TableCell>
                  <TableCell><div className="flex gap-2"><Button size="sm"><Play className="mr-1 h-3 w-3" />Apply</Button><Button size="sm" variant="ghost">Edit</Button></div></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TabsContent>

        <TabsContent value="preview">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader><CardTitle>Sample Masking</CardTitle></CardHeader>
              <CardContent>
                <Table>
                  <TableHeader><TableRow><TableHead>Original</TableHead><TableHead>Technique</TableHead><TableHead>Masked</TableHead></TableRow></TableHeader>
                  <TableBody>
                    <TableRow><TableCell>alice@example.com</TableCell><TableCell>Pseudonymization</TableCell><TableCell className="font-mono">anon_a1b2c3d4e5f</TableCell></TableRow>
                    <TableRow><TableCell>123-45-6789</TableCell><TableCell>Redaction</TableCell><TableCell className="font-mono">***-**-****</TableCell></TableRow>
                    <TableRow><TableCell>4111-1111-1111-1111</TableCell><TableCell>Tokenization</TableCell><TableCell className="font-mono">tok_xxxxxxxxxxxxxxxx</TableCell></TableRow>
                    <TableRow><TableCell>192.168.1.1</TableCell><TableCell>Generalization</TableCell><TableCell className="font-mono">10.0.0.x</TableCell></TableRow>
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle>Data Classification Scan</CardTitle></CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {[
                    { col: 'users.email', type: 'PII', count: 15000 },
                    { col: 'employees.ssn', type: 'PII', count: 3200 },
                    { col: 'payments.card_number', type: 'Financial', count: 8500 },
                    { col: 'patients.diagnosis', type: 'PHI', count: 2200 },
                    { col: 'api_keys.value', type: 'Credentials', count: 450 },
                  ].map((item, i) => (
                    <div key={i} className="flex justify-between items-center p-2 bg-gray-800 rounded">
                      <span className="font-mono text-xs">{item.col}</span>
                      <div className="flex gap-2 items-center">
                        <Badge variant={item.type === 'PII' ? 'destructive' : 'secondary'} className="text-xs">{item.type}</Badge>
                        <span className="text-xs text-muted-foreground">{item.count.toLocaleString()} cols</span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="audit">
          <Table>
            <TableHeader><TableRow><TableHead>Timestamp</TableHead><TableHead>Profile</TableHead><TableHead>Rule</TableHead><TableHead>Table</TableHead><TableHead>Column</TableHead><TableHead>Rows</TableHead><TableHead>User</TableHead></TableRow></TableHeader>
            <TableBody>
              <TableRow><TableCell>2026-05-30 08:00</TableCell><TableCell>Staging Masking</TableCell><TableCell>Mask Email</TableCell><TableCell>users</TableCell><TableCell>email</TableCell><TableCell>5000</TableCell><TableCell>admin</TableCell></TableRow>
              <TableRow><TableCell>2026-05-30 08:00</TableCell><TableCell>Staging Masking</TableCell><TableCell>Redact SSN</TableCell><TableCell>employees</TableCell><TableCell>ssn</TableCell><TableCell>1200</TableCell><TableCell>admin</TableCell></TableRow>
              <TableRow><TableCell>2026-05-30 07:30</TableCell><TableCell>Dev Masking</TableCell><TableCell>Tokenize Card</TableCell><TableCell>payments</TableCell><TableCell>card_number</TableCell><TableCell>3400</TableCell><TableCell>devops</TableCell></TableRow>
              <TableRow><TableCell>2026-05-29 22:00</TableCell><TableCell>Dev Masking</TableCell><TableCell>Mask Email</TableCell><TableCell>users</TableCell><TableCell>email</TableCell><TableCell>2800</TableCell><TableCell>devops</TableCell></TableRow>
            </TableBody>
          </Table>
        </TabsContent>
      </Tabs>

      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>Edit Masking Rule</DialogTitle></DialogHeader>
          {editRule && (
            <div className="space-y-4">
              <div><Label>Name</Label><Input value={editRule.name} onChange={e => setEditRule({ ...editRule, name: e.target.value })} /></div>
              <div><Label>Technique</Label>
                <Select value={editRule.technique} onValueChange={v => setEditRule({ ...editRule, technique: v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent><SelectItem value="redaction">Redaction</SelectItem><SelectItem value="tokenization">Tokenization</SelectItem><SelectItem value="pseudonymization">Pseudonymization</SelectItem><SelectItem value="generalization">Generalization</SelectItem><SelectItem value="nulling">Nulling</SelectItem></SelectContent>
                </Select>
              </div>
              <div><Label>Target Column</Label><Input value={editRule.target} onChange={e => setEditRule({ ...editRule, target: e.target.value })} /></div>
              <div><Label>Priority</Label><Input type="number" value={editRule.priority} onChange={e => setEditRule({ ...editRule, priority: +e.target.value })} /></div>
              <Button className="w-full" onClick={handleEdit}>Save Changes</Button>
            </div>
          )}
        </DialogContent>
      </Dialog>

      <Dialog open={deleteOpen} onOpenChange={setDeleteOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>Delete Masking Rule</DialogTitle></DialogHeader>
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

export default DataMaskingPage;
