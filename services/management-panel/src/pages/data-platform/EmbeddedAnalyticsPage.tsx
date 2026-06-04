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
import { Globe, Code, BarChart3, Plus, Trash2, Copy, RefreshCw, Users, Eye, Settings } from 'lucide-react';

interface Customer { id: string; name: string; domain: string; authMethod: string; active: boolean; embeds: number; created: string; }
interface Embed { id: string; customer: string; name: string; type: string; whiteLabel: boolean; active: boolean; lastAccess: string; }

const mockCustomers: Customer[] = [
  { id: 'ec-1', name: 'Acme Corp', domain: 'acme.com', authMethod: 'api_key', active: true, embeds: 3, created: '2026-04-01' },
  { id: 'ec-2', name: 'Globex Inc', domain: 'globex.io', authMethod: 'jwt', active: true, embeds: 2, created: '2026-04-15' },
  { id: 'ec-3', name: 'Initech', domain: 'initech.com', authMethod: 'api_key', active: false, embeds: 0, created: '2026-05-01' },
];

const mockEmbeds: Embed[] = [
  { id: 'emb-1', customer: 'Acme Corp', name: 'Usage Dashboard', type: 'dashboard', whiteLabel: true, active: true, lastAccess: '2026-05-30' },
  { id: 'emb-2', customer: 'Acme Corp', name: 'Revenue Chart', type: 'chart', whiteLabel: false, active: true, lastAccess: '2026-05-29' },
  { id: 'emb-3', customer: 'Globex Inc', name: 'Analytics Suite', type: 'full', whiteLabel: true, active: true, lastAccess: '2026-05-28' },
];

const EmbeddedAnalyticsPage: React.FC = () => {
  const [customers, setCustomers] = useState(mockCustomers);
  const [embeds, setEmbeds] = useState(mockEmbeds);
  const [embedCode, setEmbedCode] = useState('');
  const [customerSearch, setCustomerSearch] = useState('');
  const [createOpen, setCreateOpen] = useState(false);
  const [newCustomer, setNewCustomer] = useState({ name: '', domain: '', authMethod: 'api_key' });
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [customerToDelete, setCustomerToDelete] = useState<Customer | null>(null);
  const [createEmbedOpen, setCreateEmbedOpen] = useState(false);
  const [newEmbed, setNewEmbed] = useState({ customer: '', name: '', type: 'dashboard', whiteLabel: 'false' });

  const filteredCustomers = customers.filter(c => c.name.toLowerCase().includes(customerSearch.toLowerCase()) || c.domain.toLowerCase().includes(customerSearch.toLowerCase()));

  const handleAddCustomer = () => {
    const customer: Customer = {
      id: `ec-${Date.now()}`,
      name: newCustomer.name,
      domain: newCustomer.domain,
      authMethod: newCustomer.authMethod,
      active: true,
      embeds: 0,
      created: new Date().toISOString().slice(0, 10),
    };
    setCustomers([...customers, customer]);
    setCreateOpen(false);
    setNewCustomer({ name: '', domain: '', authMethod: 'api_key' });
  };

  const handleDeleteCustomer = () => {
    if (!customerToDelete) return;
    setCustomers(customers.filter(c => c.id !== customerToDelete.id));
    setDeleteOpen(false);
    setCustomerToDelete(null);
  };

  const handleCreateEmbed = () => {
    const embed: Embed = {
      id: `emb-${Date.now()}`,
      customer: customers.find(c => c.id === newEmbed.customer)?.name || '',
      name: newEmbed.name,
      type: newEmbed.type,
      whiteLabel: newEmbed.whiteLabel === 'true',
      active: true,
      lastAccess: new Date().toISOString().slice(0, 10),
    };
    setEmbeds([...embeds, embed]);
    setCreateEmbedOpen(false);
    setNewEmbed({ customer: '', name: '', type: 'dashboard', whiteLabel: 'false' });
  };

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Embedded Analytics SDK</h1>
          <p className="text-muted-foreground">Embeddable charts and dashboards for external customers, white-label ready</p>
        </div>
        <Dialog open={createOpen} onOpenChange={setCreateOpen}>
          <DialogTrigger asChild><Button><Plus className="mr-2 h-4 w-4" />Add Customer</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>Register Customer</DialogTitle></DialogHeader>
            <div className="space-y-4">
              <div><Label>Company Name</Label><Input value={newCustomer.name} onChange={e => setNewCustomer({ ...newCustomer, name: e.target.value })} placeholder="e.g. Acme Corp" /></div>
              <div><Label>Domain</Label><Input value={newCustomer.domain} onChange={e => setNewCustomer({ ...newCustomer, domain: e.target.value })} placeholder="e.g. acme.com" /></div>
              <div><Label>Auth Method</Label>
                <Select value={newCustomer.authMethod} onValueChange={v => setNewCustomer({ ...newCustomer, authMethod: v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent><SelectItem value="api_key">API Key</SelectItem><SelectItem value="jwt">JWT</SelectItem><SelectItem value="sso">SSO</SelectItem></SelectContent>
                </Select>
              </div>
              <div><Label>Rate Limit</Label><Input type="number" defaultValue={1000} placeholder="Requests per hour" /></div>
              <Button className="w-full" onClick={handleAddCustomer}>Register</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Customers</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{customers.length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Embeds</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{embeds.length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Requests (24h)</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">2,450</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Active Customers</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{customers.filter(c => c.active).length}</div></CardContent></Card>
      </div>

      <Tabs defaultValue="customers">
        <TabsList>
          <TabsTrigger value="customers"><Users className="mr-2 h-4 w-4" />Customers</TabsTrigger>
          <TabsTrigger value="embeds"><Globe className="mr-2 h-4 w-4" />Embeds</TabsTrigger>
          <TabsTrigger value="code"><Code className="mr-2 h-4 w-4" />Embed Code</TabsTrigger>
          <TabsTrigger value="usage"><Eye className="mr-2 h-4 w-4" />Usage</TabsTrigger>
        </TabsList>

        <TabsContent value="customers">
          <div className="flex gap-2 mb-4">
            <Input placeholder="Search customers..." value={customerSearch} onChange={e => setCustomerSearch(e.target.value)} className="max-w-sm" />
            <Button variant="outline" size="sm" onClick={() => setCustomerSearch('')}>Clear</Button>
          </div>
          <Table>
            <TableHeader><TableRow><TableHead>Company</TableHead><TableHead>Domain</TableHead><TableHead>Auth</TableHead><TableHead>Status</TableHead><TableHead>Embeds</TableHead><TableHead>Created</TableHead><TableHead>Actions</TableHead></TableRow></TableHeader>
            <TableBody>
              {filteredCustomers.map(c => (
                <TableRow key={c.id}>
                  <TableCell className="font-medium">{c.name}</TableCell>
                  <TableCell className="text-xs font-mono">{c.domain}</TableCell>
                  <TableCell><Badge variant="outline">{c.authMethod}</Badge></TableCell>
                  <TableCell>{c.active ? <Badge className="bg-green-600">Active</Badge> : <Badge variant="secondary">Inactive</Badge>}</TableCell>
                  <TableCell>{c.embeds}</TableCell>
                  <TableCell className="text-sm">{c.created}</TableCell>
                  <TableCell>
                    <div className="flex gap-1">
                      <Button size="sm" variant="ghost"><Settings className="h-4 w-4" /></Button>
                      <Button size="sm" variant="ghost" className="text-red-400" onClick={() => { setCustomerToDelete(c); setDeleteOpen(true); }}><Trash2 className="h-4 w-4" /></Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TabsContent>

        <TabsContent value="embeds">
          <div className="flex gap-2 mb-4">
            <Dialog open={createEmbedOpen} onOpenChange={setCreateEmbedOpen}>
              <DialogTrigger asChild><Button variant="outline"><Plus className="mr-2 h-4 w-4" />Create Embed</Button></DialogTrigger>
              <DialogContent>
                <DialogHeader><DialogTitle>New Embed</DialogTitle></DialogHeader>
                <div className="space-y-4">
                  <div><Label>Customer</Label>
                    <Select value={newEmbed.customer} onValueChange={v => setNewEmbed({ ...newEmbed, customer: v })}>
                      <SelectTrigger><SelectValue placeholder="Select customer..." /></SelectTrigger>
                      <SelectContent>{customers.filter(c => c.active).map(c => <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>)}</SelectContent>
                    </Select>
                  </div>
                  <div><Label>Name</Label><Input value={newEmbed.name} onChange={e => setNewEmbed({ ...newEmbed, name: e.target.value })} placeholder="e.g. Usage Dashboard" /></div>
                  <div><Label>Embed Type</Label>
                    <Select value={newEmbed.type} onValueChange={v => setNewEmbed({ ...newEmbed, type: v })}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent><SelectItem value="chart">Chart</SelectItem><SelectItem value="dashboard">Dashboard</SelectItem><SelectItem value="full">Full Analytics</SelectItem></SelectContent>
                    </Select>
                  </div>
                  <div><Label>White Label</Label>
                    <Select value={newEmbed.whiteLabel} onValueChange={v => setNewEmbed({ ...newEmbed, whiteLabel: v })}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent><SelectItem value="true">Yes</SelectItem><SelectItem value="false">No</SelectItem></SelectContent>
                    </Select>
                  </div>
                  <Button className="w-full" onClick={handleCreateEmbed}>Create</Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>
          <Table>
            <TableHeader><TableRow><TableHead>Name</TableHead><TableHead>Customer</TableHead><TableHead>Type</TableHead><TableHead>White Label</TableHead><TableHead>Status</TableHead><TableHead>Last Access</TableHead><TableHead>Actions</TableHead></TableRow></TableHeader>
            <TableBody>
              {embeds.map(e => (
                <TableRow key={e.id}>
                  <TableCell className="font-medium">{e.name}</TableCell>
                  <TableCell>{e.customer}</TableCell>
                  <TableCell><Badge variant="outline">{e.type}</Badge></TableCell>
                  <TableCell>{e.whiteLabel ? <Badge className="bg-green-600">Yes</Badge> : <Badge variant="secondary">No</Badge>}</TableCell>
                  <TableCell>{e.active ? <Badge>Active</Badge> : <Badge variant="secondary">Inactive</Badge>}</TableCell>
                  <TableCell className="text-sm">{e.lastAccess}</TableCell>
                  <TableCell>
                    <div className="flex gap-1">
                      <Button size="sm" variant="ghost" onClick={() => setEmbedCode(`<iframe src="https://analytics.infrapilot.io/embed/${e.id}" width="100%" height="600"></iframe>`)}><Code className="h-4 w-4" /></Button>
                      <Button size="sm" variant="ghost" className="text-red-400"><Trash2 className="h-4 w-4" /></Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TabsContent>

        <TabsContent value="code">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader><CardTitle>Embed Code Generator</CardTitle></CardHeader>
              <CardContent className="space-y-4">
                <div><Label>Select Embed</Label>
                  <Select onValueChange={(v) => setEmbedCode(`<iframe src="https://analytics.infrapilot.io/embed/${v}" width="100%" height="600" frameborder="0"></iframe>`)}>
                    <SelectTrigger><SelectValue placeholder="Choose an embed..." /></SelectTrigger>
                    <SelectContent>{embeds.filter(e => e.active).map(e => <SelectItem key={e.id} value={e.id}>{e.name} ({e.customer})</SelectItem>)}</SelectContent>
                  </Select>
                </div>
                {embedCode && (
                  <div>
                    <div className="flex justify-between mb-2"><Label>Embed Code</Label><Button size="sm" variant="ghost" onClick={() => navigator.clipboard.writeText(embedCode)}><Copy className="mr-1 h-3 w-3" />Copy</Button></div>
                    <pre className="bg-gray-900 text-gray-100 p-4 rounded text-xs overflow-x-auto whitespace-pre-wrap">{embedCode}</pre>
                  </div>
                )}
              </CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle>Configuration Options</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                <div className="p-2 bg-gray-800 rounded text-sm">
                  <div className="font-medium mb-1">Theme</div>
                  <select className="w-full bg-gray-700 border border-gray-600 rounded px-2 py-1 text-sm">
                    <option>Light</option><option>Dark</option><option>Auto (follow host)</option>
                  </select>
                </div>
                <div className="p-2 bg-gray-800 rounded text-sm">
                  <div className="font-medium mb-1">Locale</div>
                  <select className="w-full bg-gray-700 border border-gray-600 rounded px-2 py-1 text-sm">
                    <option>en-US</option><option>de-DE</option><option>ja-JP</option>
                  </select>
                </div>
                <div className="p-2 bg-gray-800 rounded text-sm">
                  <div className="font-medium mb-1">Permissions</div>
                  <label className="flex items-center gap-2 mt-1"><input type="checkbox" defaultChecked /> Allow export</label>
                  <label className="flex items-center gap-2"><input type="checkbox" defaultChecked /> Allow drill-down</label>
                  <label className="flex items-center gap-2"><input type="checkbox" /> Allow date range picker</label>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="usage">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {customers.filter(c => c.active).map(c => (
              <Card key={c.id}>
                <CardHeader><CardTitle>{c.name}</CardTitle></CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex justify-between"><span>API Requests (24h)</span><span className="font-mono">{Math.round(Math.random() * 1000 + 100)}</span></div>
                    <div className="flex justify-between"><span>Dashboard Views</span><span className="font-mono">{Math.round(Math.random() * 200 + 20)}</span></div>
                    <div className="flex justify-between"><span>Active Embeds</span><span className="font-mono">{c.embeds}</span></div>
                    <div className="flex justify-between"><span>Rate Limit</span><span className="font-mono">{1000}/hr</span></div>
                    <div className="flex justify-between"><span>Usage</span>
                      <div className="w-32 bg-gray-700 rounded-full h-2 mt-1"><div className="bg-blue-500 h-2 rounded-full" style={{ width: `${Math.min(100, Math.round(Math.random() * 60 + 10))}%` }} /></div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>

      <Dialog open={deleteOpen} onOpenChange={setDeleteOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>Delete Customer</DialogTitle></DialogHeader>
          <p className="text-sm text-muted-foreground">Are you sure you want to delete <strong>{customerToDelete?.name}</strong>? All associated embeds will be removed.</p>
          <div className="flex gap-2 justify-end">
            <Button variant="outline" onClick={() => setDeleteOpen(false)}>Cancel</Button>
            <Button variant="destructive" onClick={handleDeleteCustomer}>Delete</Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default EmbeddedAnalyticsPage;
