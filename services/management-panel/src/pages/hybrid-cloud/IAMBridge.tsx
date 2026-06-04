import { useEffect, useState } from 'react';
import { FormattedMessage } from 'react-intl';
import { apiClient } from '../../lib/api';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';

interface Mapping { id: string; source_role: string; source_provider: string; target_role: string; target_provider: string; active: boolean; }
interface Policy { id: string; name: string; statements: any[]; }

export const IAMBridge = () => {
  const [mappings, setMappings] = useState<Mapping[]>([]);
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [loading, setLoading] = useState(true);
  const [showDialog, setShowDialog] = useState(false);
  const [srcRole, setSrcRole] = useState(''); const [srcProv, setSrcProv] = useState('aws');
  const [tgtRole, setTgtRole] = useState(''); const [tgtProv, setTgtProv] = useState('azure');

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    try { const [m, p] = await Promise.all([apiClient.listIAMMappings(), apiClient.listIAMPolicies()]);
      setMappings(m || []); setPolicies(p || []);
    } catch (e) { toast.error('Failed to load IAM data');
    } finally { setLoading(false); }
  };

  const createMapping = async () => {
    try { await apiClient.createIAMMapping({ source_role: srcRole, source_provider: srcProv, target_role: tgtRole, target_provider: tgtProv });
      toast.success('Mapping created'); setShowDialog(false); loadData();
    } catch (e) { toast.error('Failed to create mapping'); }
  };

  const syncAll = async () => {
    try { await apiClient.syncIAMMappings(); toast.success('All mappings synced'); loadData();
    } catch (e) { toast.error('Failed to sync'); }
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>;

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex justify-between items-center">
        <div><h1 className="text-3xl font-bold"><FormattedMessage id="iamBridge.title" defaultMessage="Multi-Cloud IAM Bridge" /></h1>
          <p className="text-muted-foreground mt-1"><FormattedMessage id="iamBridge.description" defaultMessage="Synchronize roles and policies across cloud providers" /></p></div>
      </div>
      <Tabs defaultValue="mappings">
        <TabsList><TabsTrigger value="mappings">Mappings</TabsTrigger><TabsTrigger value="policies">Policies</TabsTrigger></TabsList>
        <TabsContent value="mappings" className="space-y-4">
          <div className="flex justify-between"><h2 className="text-xl font-semibold">Role Mappings</h2>
            <div className="flex gap-2"><Button onClick={() => setShowDialog(true)}>Create Mapping</Button><Button onClick={syncAll}>Sync All</Button></div></div>
          <Card><CardContent className="p-0">
            <Table><TableHeader><TableRow>
              <TableHead>Source Role</TableHead><TableHead>Source Provider</TableHead><TableHead>Target Role</TableHead><TableHead>Target Provider</TableHead><TableHead>Status</TableHead>
            </TableRow></TableHeader>
            <TableBody>{mappings.map((m) => (
              <TableRow key={m.id}><TableCell className="font-medium">{m.source_role}</TableCell>
                <TableCell><Badge variant="outline">{m.source_provider}</Badge></TableCell>
                <TableCell>{m.target_role}</TableCell>
                <TableCell><Badge variant="outline">{m.target_provider}</Badge></TableCell>
                <TableCell><Badge variant={m.active ? 'default' : 'secondary'}>{m.active ? 'Active' : 'Inactive'}</Badge></TableCell>
              </TableRow>
            ))}</TableBody></Table>
          </CardContent></Card>
          {showDialog && (<div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"><Card className="w-96">
            <CardHeader><CardTitle>Create Mapping</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div><Label>Source Role</Label><Input value={srcRole} onChange={(e) => setSrcRole(e.target.value)} placeholder="Admin" /></div>
              <div><Label>Source Provider</Label><Input value={srcProv} onChange={(e) => setSrcProv(e.target.value)} placeholder="aws" /></div>
              <div><Label>Target Role</Label><Input value={tgtRole} onChange={(e) => setTgtRole(e.target.value)} placeholder="Contributor" /></div>
              <div><Label>Target Provider</Label><Input value={tgtProv} onChange={(e) => setTgtProv(e.target.value)} placeholder="azure" /></div>
              <div className="flex gap-2"><Button onClick={createMapping}>Create</Button><Button variant="outline" onClick={() => setShowDialog(false)}>Cancel</Button></div>
            </CardContent></Card></div>)}
        </TabsContent>
        <TabsContent value="policies">
          <Card><CardContent className="p-0">
            <Table><TableHeader><TableRow>
              <TableHead>Name</TableHead><TableHead>Statements</TableHead><TableHead>Version</TableHead>
            </TableRow></TableHeader>
            <TableBody>{policies.map((p) => (
              <TableRow key={p.id}><TableCell className="font-medium">{p.name}</TableCell>
                <TableCell>{p.statements?.length || 0}</TableCell>
                <TableCell>2012-10-17</TableCell>
              </TableRow>
            ))}</TableBody></Table>
          </CardContent></Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};
  const [roles, setRoles] = useState<any[]>([]);
  const [showRoleDialog, setShowRoleDialog] = useState(false);
  const [roleName, setRoleName] = useState('');
  const [roleProvider, setRoleProvider] = useState('aws');
  const [syncHistory, setSyncHistory] = useState<any[]>([]);
  const [showMappingDialog, setShowMappingDialog] = useState(false);
  const [srcRole, setSrcRole] = useState('');
  const [srcProv, setSrcProv] = useState('aws');
  const [targetRole, setTargetRole] = useState('');
  const [tgtProv, setTgtProv] = useState('azure');

  useEffect(() => {
    loadSyncHistory();
  }, []);

  const loadSyncHistory = async () => {
    try { const data = await apiClient.getSyncHistory(); setSyncHistory(data || []); } catch { /* ignore */ }
  };

  const syncAll = async () => {
    try { await apiClient.syncAllMappings(); toast.success('All mappings synced'); await loadSyncHistory(); } catch { toast.error('Sync failed'); }
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="grid grid-cols-4 gap-4">
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Roles</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{roles.length}</p></CardContent></Card>
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Policies</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{policies.length}</p></CardContent></Card>
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Mappings</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{mappings.length}</p></CardContent></Card>
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Last Sync</CardTitle></CardHeader><CardContent><p className="text-sm">{syncHistory[0]?.synced_at ? new Date(syncHistory[0].synced_at).toLocaleString() : 'Never'}</p></CardContent></Card>
      </div>

      <div className="flex gap-2">
        <Button onClick={syncAll}>Sync All</Button>
        <Dialog open={showRoleDialog} onOpenChange={setShowRoleDialog}>
          <DialogTrigger asChild><Button variant="outline">Add Role</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>Add Role</DialogTitle></DialogHeader>
            <div className="space-y-2">
              <Input placeholder="Role name" value={roleName} onChange={e => setRoleName(e.target.value)} />
              <Select value={roleProvider} onValueChange={setRoleProvider}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="aws">AWS</SelectItem>
                  <SelectItem value="azure">Azure</SelectItem>
                  <SelectItem value="gcp">GCP</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <DialogFooter><Button onClick={() => { apiClient.addRole(roleName, roleProvider); toast.success('Role added'); setShowRoleDialog(false); }}>Add</Button></DialogFooter>
          </DialogContent>
        </Dialog>
        <Dialog open={showMappingDialog} onOpenChange={setShowMappingDialog}>
          <DialogTrigger asChild><Button variant="outline">Add Mapping</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>Add Role Mapping</DialogTitle></DialogHeader>
            <div className="space-y-2">
              <Input placeholder="Source role" value={srcRole} onChange={e => setSrcRole(e.target.value)} />
              <Input placeholder="Source provider" value={srcProv} onChange={e => setSrcProv(e.target.value)} />
              <Input placeholder="Target role" value={targetRole} onChange={e => setTargetRole(e.target.value)} />
              <Input placeholder="Target provider" value={tgtProv} onChange={e => setTgtProv(e.target.value)} />
            </div>
            <DialogFooter><Button onClick={() => { apiClient.createMapping(srcRole, srcProv, targetRole, tgtProv); toast.success('Mapping created'); setShowMappingDialog(false); }}>Create</Button></DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

  const [showAuditDialog, setShowAuditDialog] = useState(false);
  const [auditLog, setAuditLog] = useState<any[]>([]);
  const [showSsoDialog, setShowSsoDialog] = useState(false);
  const [ssoProvider, setSsoProvider] = useState('azure_ad');
  const [ssoDomain, setSsoDomain] = useState('example.com');
  const [ssoIdpUrl, setSsoIdpUrl] = useState('https://idp.example.com');
  const [ssoConfigs, setSsoConfigs] = useState<any[]>([]);

  const loadAuditLog = async () => {
    try {
      const data = await apiClient.getIamAuditLog();
      setAuditLog(data || []);
      setShowAuditDialog(true);
    } catch { toast.error('Failed to load audit log'); }
  };

  const configureSSO = async () => {
    try {
      const result = await apiClient.configureIamSso(ssoProvider, ssoDomain, ssoIdpUrl);
      setSsoConfigs([...ssoConfigs, result]);
      toast.success('SSO configured');
      setShowSsoDialog(false);
    } catch { toast.error('Failed to configure SSO'); }
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="grid grid-cols-4 gap-4">
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Mappings</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{mappings.length}</p></CardContent></Card>
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Policies</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{policies.length}</p></CardContent></Card>
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">SSO Configs</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{ssoConfigs.length}</p></CardContent></Card>
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Audit Entries</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{auditLog.length}</p></CardContent></Card>
      </div>

      <div className="flex gap-2">
        <Button variant="outline" onClick={loadAuditLog}>View Audit Log</Button>
        <Dialog open={showSsoDialog} onOpenChange={setShowSsoDialog}>
          <DialogTrigger asChild><Button>Configure SSO</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>Configure SSO</DialogTitle></DialogHeader>
            <div className="space-y-2">
              <Select value={ssoProvider} onValueChange={setSsoProvider}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="azure_ad">Azure AD</SelectItem>
                  <SelectItem value="okta">Okta</SelectItem>
                  <SelectItem value="keycloak">Keycloak</SelectItem>
                </SelectContent>
              </Select>
              <Input placeholder="Domain" value={ssoDomain} onChange={e => setSsoDomain(e.target.value)} />
              <Input placeholder="IdP URL" value={ssoIdpUrl} onChange={e => setSsoIdpUrl(e.target.value)} />
            </div>
            <DialogFooter><Button onClick={configureSSO}>Configure</Button></DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardHeader><CardTitle>SSO Configurations</CardTitle></CardHeader>
        <CardContent>
          <Table>
            <TableHeader><TableRow><TableHead>Provider</TableHead><TableHead>Domain</TableHead><TableHead>Status</TableHead></TableRow></TableHeader>
            <TableBody>{ssoConfigs.map((s, i) => (
              <TableRow key={i}>
                <TableCell className="font-medium">{s.provider}</TableCell>
                <TableCell>{s.domain}</TableCell>
                <TableCell><Badge variant="default">Active</Badge></TableCell>
              </TableRow>
            ))}</TableBody>
          </Table>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Sync History</CardTitle></CardHeader>
        <CardContent>
          <Table>
            <TableHeader><TableRow><TableHead>Mapping</TableHead><TableHead>Status</TableHead><TableHead>Synced At</TableHead></TableRow></TableHeader>
            <TableBody>{syncHistory.slice(-10).reverse().map((entry: any, i: number) => (
              <TableRow key={i}>
                <TableCell className="font-mono text-xs">{entry.mapping_id?.substring(0, 12)}</TableCell>
                <TableCell><Badge variant={entry.status === 'success' ? 'default' : 'destructive'}>{entry.status}</Badge></TableCell>
                <TableCell className="text-xs">{new Date(entry.synced_at).toLocaleString()}</TableCell>
              </TableRow>
            ))}</TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};

function RoleFormDialog({ open, onOpenChange, onSubmit }: { open: boolean; onOpenChange: (v: boolean) => void; onSubmit: (data: any) => void }) {
  const [name, setName] = useState(''); const [provider, setProvider] = useState('aws'); const [description, setDescription] = useState('');
  return (
    <Dialog open={open} onOpenChange={onOpenChange}><DialogContent><DialogHeader><DialogTitle>Create Role</DialogTitle></DialogHeader>
      <div className="space-y-4">
        <div><Label>Name</Label><Input value={name} onChange={e => setName(e.target.value)} /></div>
        <div><Label>Provider</Label><Select value={provider} onValueChange={setProvider}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{['aws','azure','gcp'].map(p => <SelectItem key={p} value={p}>{p.toUpperCase()}</SelectItem>)}</SelectContent></Select></div>
        <div><Label>Description</Label><Input value={description} onChange={e => setDescription(e.target.value)} /></div>
      </div>
      <DialogFooter><Button onClick={() => { onSubmit({ name, provider, description }); onOpenChange(false); }}>Create</Button></DialogFooter>
    </DialogContent></Dialog>
  );
}

function PolicyFormDialog({ open, onOpenChange, onSubmit }: { open: boolean; onOpenChange: (v: boolean) => void; onSubmit: (data: any) => void }) {
  const [name, setName] = useState(''); const [statementStr, setStatementStr] = useState('[{"Effect":"Allow","Action":["*"],"Resource":["*"]}]');
  return (
    <Dialog open={open} onOpenChange={onOpenChange}><DialogContent><DialogHeader><DialogTitle>Create Policy</DialogTitle></DialogHeader>
      <div className="space-y-4">
        <div><Label>Name</Label><Input value={name} onChange={e => setName(e.target.value)} /></div>
        <div><Label>Statements (JSON)</Label><textarea className="w-full h-24 p-2 border rounded text-xs font-mono" value={statementStr} onChange={e => setStatementStr(e.target.value)} /></div>
      </div>
      <DialogFooter><Button onClick={() => { try { onSubmit({ name, statements: JSON.parse(statementStr) }); onOpenChange(false); } catch { toast.error('Invalid JSON'); } }}>Create</Button></DialogFooter>
    </DialogContent></Dialog>
  );
}

function SyncHistoryChart({ history }: { history: any[] }) {
  const byDate: Record<string, number> = {};
  history.forEach((h: any) => { const d = h.synced_at?.substring(0, 10) || 'unknown'; byDate[d] = (byDate[d] || 0) + 1; });
  const sorted = Object.entries(byDate).sort((a, b) => a[0].localeCompare(b[0])).slice(-14);
  return (
    <Card><CardHeader><CardTitle>Sync Activity (14d)</CardTitle></CardHeader>
    <CardContent><div className="space-y-1">{sorted.map(([d, c]) => (
      <div key={d} className="flex items-center gap-2"><span className="text-xs w-24">{d}</span><div className="h-4 bg-primary rounded" style={{ width: `${(c / Math.max(...sorted.map(s => s[1]))) * 80 + 10}%` }} /><span className="text-xs">{c}</span></div>
    ))}</div></CardContent></Card>
  );
}

function ComplianceBadge({ compliant }: { compliant: boolean }) {
  return <Badge variant={compliant ? 'default' : 'destructive'}>{compliant ? 'Compliant' : 'Non-Compliant'}</Badge>;
}

function MappingTable({ mappings }: { mappings: any[] }) {
  return (
    <Card><CardHeader><CardTitle>Bridge Mappings</CardTitle></CardHeader>
    <CardContent><Table><TableHeader><TableRow><TableHead>Source</TableHead><TableHead>Target</TableHead><TableHead>Direction</TableHead><TableHead>Status</TableHead></TableRow></TableHeader>
    <TableBody>{mappings.slice(0, 20).map((m: any, i: number) => (
      <TableRow key={i}><TableCell>{m.source_provider}/{m.source_role}</TableCell><TableCell>{m.target_provider}/{m.target_role}</TableCell><TableCell>{m.sync_direction}</TableCell><TableCell><Badge variant={m.active ? 'default' : 'secondary'}>{m.active ? 'Active' : 'Inactive'}</Badge></TableCell></TableRow>
    ))}</TableBody></Table></CardContent></Card>
  );
}

function ProviderFilterBar({ providers, selected, onChange }: { providers: string[]; selected: string; onChange: (v: string) => void }) {
  return (
    <div className="flex gap-2 mb-4">{['all', ...providers].map(p => (
      <Button key={p} variant={selected === p ? 'default' : 'outline'} size="sm" onClick={() => onChange(p)}>{p === 'all' ? 'All' : p.toUpperCase()}</Button>
    ))}</div>
  );
}

function StatsCard({ title, value, description }: { title: string; value: string; description?: string }) {
  return (
    <Card><CardHeader className="pb-2"><CardTitle className="text-sm">{title}</CardTitle></CardHeader>
    <CardContent><p className="text-2xl font-bold">{value}</p>{description && <p className="text-xs text-muted-foreground">{description}</p>}</CardContent></Card>
  );
}

export default IAMBridge;
