import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Progress } from '@/components/ui/progress';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Search, Database, Tag, BookOpen, Shield, RefreshCw, Plus, GitBranch, Award, FileText } from 'lucide-react';

interface CatalogAsset {
  id: string; name: string; type: string; location: string; owner: string; domain: string; certified: boolean; quality: number; records: number; tags: string[];
}

const mockAssets: CatalogAsset[] = [
  { id: 'ca-1', name: 'user_profiles', type: 'postgresql', location: 'pg-01:5432/infrapilot', owner: 'data-team', domain: 'customer', certified: true, quality: 98, records: 150000, tags: ['pii', 'user-data'] },
  { id: 'ca-2', name: 'game_telemetry', type: 'timescaledb', location: 'ts-01:5432/telemetry', owner: 'gaming-team', domain: 'gaming', certified: true, quality: 95, records: 45000000, tags: ['telemetry', 'real-time'] },
  { id: 'ca-3', name: 'inventory_snapshots', type: 'parquet', location: 's3://data-lake/inventory/', owner: 'logistics-team', domain: 'supply-chain', certified: false, quality: 87, records: 120000000, tags: ['data-lake', 'parquet'] },
  { id: 'ca-4', name: 'support_tickets', type: 'mongodb', location: 'mongo-01:27017/support', owner: 'support-team', domain: 'customer', certified: false, quality: 76, records: 250000, tags: ['customer-data'] },
];

interface GlossaryTerm { id: string; term: string; definition: string; domain: string; linkedAssets: number; }

const mockGlossary: GlossaryTerm[] = [
  { id: 'gt-1', term: 'Customer', definition: 'A person or organization that uses the platform', domain: 'customer', linkedAssets: 2 },
  { id: 'gt-2', term: 'Active User', definition: 'User with activity in the last 30 days', domain: 'customer', linkedAssets: 1 },
  { id: 'gt-3', term: 'Net Revenue', definition: 'Gross revenue minus refunds and chargebacks', domain: 'finance', linkedAssets: 1 },
];

const DataCatalogPage: React.FC = () => {
  const [assets, setAssets] = useState(mockAssets);
  const [glossary] = useState(mockGlossary);
  const [search, setSearch] = useState('');
  const [glossarySearch, setGlossarySearch] = useState('');
  const [selectedAsset, setSelectedAsset] = useState<CatalogAsset | null>(null);
  const [registerOpen, setRegisterOpen] = useState(false);
  const [detailOpen, setDetailOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [newAsset, setNewAsset] = useState({ name: '', type: 'database', location: '', owner: '', domain: '' });
  const [editAsset, setEditAsset] = useState<CatalogAsset | null>(null);

  const filtered = assets.filter(a => a.name.toLowerCase().includes(search.toLowerCase()) || a.tags.some(t => t.includes(search.toLowerCase())));
  const filteredGlossary = glossary.filter(g => g.term.toLowerCase().includes(glossarySearch.toLowerCase()) || g.definition.toLowerCase().includes(glossarySearch.toLowerCase()));

  const handleRegister = () => {
    const asset: CatalogAsset = {
      id: `ca-${Date.now()}`,
      name: newAsset.name,
      type: newAsset.type,
      location: newAsset.location,
      owner: newAsset.owner,
      domain: newAsset.domain,
      certified: false,
      quality: 100,
      records: 0,
      tags: [],
    };
    setAssets([...assets, asset]);
    setRegisterOpen(false);
    setNewAsset({ name: '', type: 'database', location: '', owner: '', domain: '' });
  };

  const handleEdit = () => {
    if (!editAsset) return;
    setAssets(assets.map(a => a.id === editAsset.id ? editAsset : a));
    setEditOpen(false);
    setEditAsset(null);
  };

  const handleDelete = () => {
    if (!selectedAsset) return;
    setAssets(assets.filter(a => a.id !== selectedAsset.id));
    setDeleteOpen(false);
    setSelectedAsset(null);
  };

  const toggleCertify = (asset: CatalogAsset) => {
    setAssets(assets.map(a => a.id === asset.id ? { ...a, certified: !a.certified } : a));
  };

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Data Catalog & Governance</h1>
          <p className="text-muted-foreground">Automated metadata harvesting, column-level lineage, glossary, and PII/PHI tagging</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline"><RefreshCw className="mr-2 h-4 w-4" />Run Discovery</Button>
          <Dialog open={registerOpen} onOpenChange={setRegisterOpen}>
            <DialogTrigger asChild><Button><Plus className="mr-2 h-4 w-4" />Register Asset</Button></DialogTrigger>
            <DialogContent>
              <DialogHeader><DialogTitle>Register Data Asset</DialogTitle></DialogHeader>
              <div className="space-y-4">
                <div><Input placeholder="Asset name" value={newAsset.name} onChange={e => setNewAsset({ ...newAsset, name: e.target.value })} /></div>
                <div><Input placeholder="Description" /></div>
                <div><Input placeholder="Location" value={newAsset.location} onChange={e => setNewAsset({ ...newAsset, location: e.target.value })} /></div>
                <div><Label>Source Type</Label>
                  <select className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm" value={newAsset.type} onChange={e => setNewAsset({ ...newAsset, type: e.target.value })}>
                    <option value="database">Database</option><option value="data_lake">Data Lake</option><option value="stream">Stream</option><option value="file">File</option><option value="api">API</option>
                  </select>
                </div>
                <div><Input placeholder="Owner" value={newAsset.owner} onChange={e => setNewAsset({ ...newAsset, owner: e.target.value })} /></div>
                <div><Input placeholder="Domain" value={newAsset.domain} onChange={e => setNewAsset({ ...newAsset, domain: e.target.value })} /></div>
                <Button className="w-full" onClick={handleRegister}>Register</Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Total Assets</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{assets.length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Certified</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{assets.filter(a => a.certified).length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Records</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">165.4M</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Avg Quality</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">89%</div></CardContent></Card>
      </div>

      <Tabs defaultValue="assets">
        <TabsList>
          <TabsTrigger value="assets"><Database className="mr-2 h-4 w-4" />Assets</TabsTrigger>
          <TabsTrigger value="lineage"><GitBranch className="mr-2 h-4 w-4" />Lineage</TabsTrigger>
          <TabsTrigger value="glossary"><BookOpen className="mr-2 h-4 w-4" />Glossary</TabsTrigger>
          <TabsTrigger value="classification"><Shield className="mr-2 h-4 w-4" />Classification</TabsTrigger>
        </TabsList>

        <TabsContent value="assets">
          <div className="flex gap-2 mb-4">
            <Input placeholder="Search assets, tags..." value={search} onChange={e => setSearch(e.target.value)} className="max-w-sm" />
            <Button variant="outline" size="sm" onClick={() => setSearch('')}>Clear</Button>
          </div>
          <Table>
            <TableHeader><TableRow><TableHead>Name</TableHead><TableHead>Type</TableHead><TableHead>Location</TableHead><TableHead>Owner</TableHead><TableHead>Domain</TableHead><TableHead>Certified</TableHead><TableHead>Quality</TableHead><TableHead>Records</TableHead><TableHead>Tags</TableHead><TableHead>Actions</TableHead></TableRow></TableHeader>
            <TableBody>
              {filtered.map(a => (
                <TableRow key={a.id}>
                  <TableCell className="font-medium cursor-pointer hover:text-blue-400" onClick={() => { setSelectedAsset(a); setDetailOpen(true); }}>{a.name}</TableCell>
                  <TableCell><Badge variant="outline">{a.type}</Badge></TableCell>
                  <TableCell className="text-xs font-mono max-w-[200px] truncate">{a.location}</TableCell>
                  <TableCell>{a.owner}</TableCell>
                  <TableCell><Badge variant="secondary">{a.domain}</Badge></TableCell>
                  <TableCell>
                    <Button size="sm" variant="ghost" onClick={() => toggleCertify(a)}>
                      {a.certified ? <Badge className="bg-green-600"><Award className="mr-1 h-3 w-3" />Certified</Badge> : <Badge variant="outline">Uncertified</Badge>}
                    </Button>
                  </TableCell>
                  <TableCell><div className="flex items-center gap-2"><Progress value={a.quality} className="w-16" /><span>{a.quality}%</span></div></TableCell>
                  <TableCell>{(a.records / 1000000).toFixed(1)}M</TableCell>
                  <TableCell><div className="flex gap-1">{a.tags.map(t => <Badge key={t} variant="outline" className="text-xs">{t}</Badge>)}</div></TableCell>
                  <TableCell>
                    <div className="flex gap-1">
                      <Button size="sm" variant="ghost" onClick={() => { setEditAsset({ ...a }); setEditOpen(true); }}>Edit</Button>
                      <Button size="sm" variant="ghost" className="text-red-400" onClick={() => { setSelectedAsset(a); setDeleteOpen(true); }}><Trash2 className="h-4 w-4" /></Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TabsContent>

        <TabsContent value="lineage">
          <Card>
            <CardHeader><CardTitle>Column-Level Lineage</CardTitle></CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="p-3 bg-gray-800 rounded">
                  <div className="font-medium">user_profiles.email</div>
                  <div className="text-sm text-muted-foreground flex gap-2 items-center mt-1"><Badge variant="outline" className="text-xs">source</Badge> → <Badge variant="outline" className="text-xs">transform</Badge> → <Badge variant="outline" className="text-xs">sink</Badge></div>
                  <div className="text-xs text-muted-foreground mt-1">api-gateway → user-service → analytics-pipeline → users_analytics.email</div>
                </div>
                <div className="p-3 bg-gray-800 rounded">
                  <div className="font-medium">transactions.amount</div>
                  <div className="text-sm text-muted-foreground flex gap-2 items-center mt-1"><Badge variant="outline" className="text-xs">source</Badge> → <Badge variant="outline" className="text-xs">transform</Badge> → <Badge variant="outline" className="text-xs">sink</Badge></div>
                  <div className="text-xs text-muted-foreground mt-1">payment-gateway → billing-service → ledger → finance_reports.amount</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="glossary">
          <div className="flex gap-2 mb-4">
            <Input placeholder="Search glossary..." value={glossarySearch} onChange={e => setGlossarySearch(e.target.value)} className="max-w-sm" />
            <Dialog><DialogTrigger asChild><Button variant="outline"><Plus className="mr-2 h-4 w-4" />Add Term</Button></DialogTrigger>
              <DialogContent><DialogHeader><DialogTitle>Add Glossary Term</DialogTitle></DialogHeader>
                <div className="space-y-4">
                  <div><Label>Term</Label><Input placeholder="e.g. Monthly Active User" /></div>
                  <div><Label>Definition</Label><textarea className="w-full h-24 bg-gray-900 text-gray-100 p-3 rounded border border-gray-700 text-sm" placeholder="Define the term..." /></div>
                  <div><Label>Domain</Label><Input placeholder="e.g. customer" /></div>
                  <Button className="w-full">Add Term</Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>
          <Table>
            <TableHeader><TableRow><TableHead>Term</TableHead><TableHead>Definition</TableHead><TableHead>Domain</TableHead><TableHead>Linked Assets</TableHead></TableRow></TableHeader>
            <TableBody>
              {filteredGlossary.map(g => (
                <TableRow key={g.id}>
                  <TableCell className="font-medium">{g.term}</TableCell>
                  <TableCell className="text-sm max-w-md">{g.definition}</TableCell>
                  <TableCell><Badge variant="secondary">{g.domain}</Badge></TableCell>
                  <TableCell>{g.linkedAssets}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TabsContent>

        <TabsContent value="classification">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card><CardHeader><CardTitle>PII/PHI Discovery</CardTitle></CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex justify-between"><span>Email addresses</span><Badge variant="destructive">PII</Badge></div>
                  <div className="flex justify-between"><span>Phone numbers</span><Badge variant="destructive">PII</Badge></div>
                  <div className="flex justify-between"><span>IP addresses</span><Badge variant="destructive">PII</Badge></div>
                  <div className="flex justify-between"><span>Medical records</span><Badge variant="destructive">PHI</Badge></div>
                  <div className="flex justify-between"><span>Credit card numbers</span><Badge variant="destructive">PCI</Badge></div>
                </div>
              </CardContent>
            </Card>
            <Card><CardHeader><CardTitle>Policy Enforcement</CardTitle></CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between items-center"><span>PII columns masked in dev</span><Badge className="bg-green-600">Enforced</Badge></div>
                  <div className="flex justify-between items-center"><span>Data retention enforced</span><Badge className="bg-green-600">Enforced</Badge></div>
                  <div className="flex justify-between items-center"><span>Cross-border restriction</span><Badge variant="secondary">Warning</Badge></div>
                  <div className="flex justify-between items-center"><span>Encryption at rest</span><Badge className="bg-green-600">Active</Badge></div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>

      <Dialog open={detailOpen} onOpenChange={setDetailOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader><DialogTitle>Asset Details — {selectedAsset?.name}</DialogTitle></DialogHeader>
          {selectedAsset && (
            <div className="space-y-3">
              <div className="flex justify-between"><span className="text-muted-foreground">Type</span><Badge variant="outline">{selectedAsset.type}</Badge></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Location</span><span className="font-mono text-xs">{selectedAsset.location}</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Owner</span><span>{selectedAsset.owner}</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Domain</span><Badge variant="secondary">{selectedAsset.domain}</Badge></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Records</span><span>{(selectedAsset.records / 1000000).toFixed(1)}M</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Quality</span><span>{selectedAsset.quality}%</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Tags</span><div className="flex gap-1">{selectedAsset.tags.map(t => <Badge key={t} variant="outline" className="text-xs">{t}</Badge>)}</div></div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>Edit Asset</DialogTitle></DialogHeader>
          {editAsset && (
            <div className="space-y-4">
              <div><Label>Name</Label><Input value={editAsset.name} onChange={e => setEditAsset({ ...editAsset, name: e.target.value })} /></div>
              <div><Label>Location</Label><Input value={editAsset.location} onChange={e => setEditAsset({ ...editAsset, location: e.target.value })} /></div>
              <div><Label>Owner</Label><Input value={editAsset.owner} onChange={e => setEditAsset({ ...editAsset, owner: e.target.value })} /></div>
              <div><Label>Domain</Label><Input value={editAsset.domain} onChange={e => setEditAsset({ ...editAsset, domain: e.target.value })} /></div>
              <Button className="w-full" onClick={handleEdit}>Save Changes</Button>
            </div>
          )}
        </DialogContent>
      </Dialog>

      <Dialog open={deleteOpen} onOpenChange={setDeleteOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>Confirm Delete</DialogTitle></DialogHeader>
          <p className="text-sm text-muted-foreground">Are you sure you want to delete <strong>{selectedAsset?.name}</strong>? This action cannot be undone.</p>
          <div className="flex gap-2 justify-end">
            <Button variant="outline" onClick={() => setDeleteOpen(false)}>Cancel</Button>
            <Button variant="destructive" onClick={handleDelete}>Delete</Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

const Select = ({ children, ...props }: any) => {
  const [open, setOpen] = useState(false);
  return React.createElement('div', { className: 'relative' },
    React.createElement('button', { onClick: () => setOpen(!open), className: 'flex items-center justify-between w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm' },
      React.createElement('span', null, props.value || props.placeholder),
      React.createElement('svg', { width: 16, height: 16, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor' }, React.createElement('polyline', { points: '6 9 12 15 18 9' }))
    ),
    open && React.createElement('div', { className: 'absolute z-50 w-full mt-1 bg-gray-800 border border-gray-700 rounded shadow-lg' }, children)
  );
};

export default DataCatalogPage;
