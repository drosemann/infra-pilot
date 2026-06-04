import { useEffect, useState } from 'react';
import { FormattedMessage } from 'react-intl';
import { apiClient } from '../../lib/api';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table';

interface Image { id: string; name: string; tag: string; registry: string; repository: string; vulnerability_count: number; }
interface Rule { id: string; source_registry: string; target_registries: string[]; image_pattern: string; }

export const ContainerRegistry = () => {
  const [images, setImages] = useState<Image[]>([]);
  const [rules, setRules] = useState<Rule[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    try { const [i, r] = await Promise.all([apiClient.listRegistryImages(), apiClient.listReplicationRules()]);
      setImages(i || []); setRules(r || []);
    } catch (e) { toast.error('Failed to load registry data');
    } finally { setLoading(false); }
  };

  const scanImage = async (imageId: string) => {
    try { const result = await apiClient.scanRegistryImage(imageId); toast.success(`Scan complete: ${result.vulnerability_count} vulns`); loadData();
    } catch (e) { toast.error('Scan failed'); }
  };

  const replicateImage = async (imageId: string) => {
    try { await apiClient.replicateRegistryImage(imageId); toast.success('Replication started'); loadData();
    } catch (e) { toast.error('Replication failed'); }
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>;

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex justify-between items-center">
        <div><h1 className="text-3xl font-bold"><FormattedMessage id="containerRegistry.title" defaultMessage="Container Registry" /></h1>
          <p className="text-muted-foreground mt-1"><FormattedMessage id="containerRegistry.description" defaultMessage="Cross-cloud container image replication" /></p></div>
      </div>
      <Tabs defaultValue="images">
        <TabsList><TabsTrigger value="images">Images</TabsTrigger><TabsTrigger value="rules">Replication Rules</TabsTrigger><TabsTrigger value="registries">Registries</TabsTrigger></TabsList>
        <TabsContent value="images" className="space-y-4">
          <Card><CardContent className="p-0">
            <Table><TableHeader><TableRow>
              <TableHead>Image</TableHead><TableHead>Registry</TableHead><TableHead>Repository</TableHead><TableHead>Vulns</TableHead><TableHead>Actions</TableHead>
            </TableRow></TableHeader>
            <TableBody>{images.map((img) => (
              <TableRow key={img.id}><TableCell className="font-medium">{img.name}:{img.tag}</TableCell>
                <TableCell><Badge variant="outline">{img.registry}</Badge></TableCell>
                <TableCell className="font-mono text-xs">{img.repository}</TableCell>
                <TableCell><Badge variant={img.vulnerability_count > 5 ? 'destructive' : 'default'}>{img.vulnerability_count}</Badge></TableCell>
                <TableCell className="flex gap-1"><Button size="sm" onClick={() => scanImage(img.id)}>Scan</Button><Button size="sm" variant="outline" onClick={() => replicateImage(img.id)}>Replicate</Button></TableCell>
              </TableRow>
            ))}</TableBody></Table>
          </CardContent></Card>
        </TabsContent>
        <TabsContent value="rules">
          <Card><CardContent className="p-0">
            <Table><TableHeader><TableRow>
              <TableHead>Source</TableHead><TableHead>Targets</TableHead><TableHead>Pattern</TableHead><TableHead>Sync on Push</TableHead>
            </TableRow></TableHeader>
            <TableBody>{rules.map((r) => (
              <TableRow key={r.id}><TableCell><Badge variant="outline">{r.source_registry}</Badge></TableCell>
                <TableCell>{r.target_registries?.join(", ")}</TableCell>
                <TableCell className="font-mono text-xs">{r.image_pattern}</TableCell>
                <TableCell>Yes</TableCell>
              </TableRow>
            ))}</TableBody></Table>
          </CardContent></Card>
        </TabsContent>
        <TabsContent value="registries">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {["AWS ECR", "Azure ACR", "GCP GCR", "Docker Hub", "GHCR", "GitLab"].map((r) => (
              <Card key={r}><CardHeader><CardTitle>{r}</CardTitle></CardHeader><CardContent><Badge variant="default">Connected</Badge></CardContent></Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};
  const [images, setImages] = useState<any[]>([]);
  const [showImageDialog, setShowImageDialog] = useState(false);
  const [imageName, setImageName] = useState('');
  const [imageTag, setImageTag] = useState('latest');
  const [imageRegistry, setImageRegistry] = useState('docker_hub');
  const [imageSize, setImageSize] = useState(100);
  const [replicationJobs, setReplicationJobs] = useState<any[]>([]);
  const [showRuleDialog, setShowRuleDialog] = useState(false);
  const [ruleName, setRuleName] = useState('');
  const [ruleSource, setRuleSource] = useState('docker_hub');
  const [ruleTargets, setRuleTargets] = useState('');

  const scanImage = async (imageId: string) => {
    try { const result = await apiClient.scanContainerImage(imageId); toast.success(`Vulnerabilities: ${result.vulnerability_count}`); } catch { toast.error('Scan failed'); }
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="grid grid-cols-4 gap-4">
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Images</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{images.length}</p></CardContent></Card>
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Registries</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">6</p></CardContent></Card>
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Rules</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{rules.length}</p></CardContent></Card>
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Jobs</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{replicationJobs.length}</p></CardContent></Card>
      </div>

      <div className="flex gap-2">
        <Dialog open={showImageDialog} onOpenChange={setShowImageDialog}>
          <DialogTrigger asChild><Button>Add Image</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>Add Container Image</DialogTitle></DialogHeader>
            <div className="space-y-2">
              <Input placeholder="Image name" value={imageName} onChange={e => setImageName(e.target.value)} />
              <Input placeholder="Tag" value={imageTag} onChange={e => setImageTag(e.target.value)} />
              <Select value={imageRegistry} onValueChange={setImageRegistry}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="docker_hub">Docker Hub</SelectItem>
                  <SelectItem value="aws_ecr">AWS ECR</SelectItem>
                  <SelectItem value="azure_acr">Azure ACR</SelectItem>
                  <SelectItem value="gcp_gcr">GCP GCR</SelectItem>
                </SelectContent>
              </Select>
              <Input type="number" placeholder="Size (MB)" value={imageSize} onChange={e => setImageSize(parseFloat(e.target.value) || 100)} />
            </div>
            <DialogFooter><Button onClick={() => { apiClient.addContainerImage(imageName, imageTag, imageRegistry, imageSize); toast.success('Image added'); setShowImageDialog(false); }}>Add</Button></DialogFooter>
          </DialogContent>
        </Dialog>
        <Dialog open={showRuleDialog} onOpenChange={setShowRuleDialog}>
          <DialogTrigger asChild><Button variant="outline">Add Rule</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>Add Replication Rule</DialogTitle></DialogHeader>
            <div className="space-y-2">
              <Input placeholder="Rule name" value={ruleName} onChange={e => setRuleName(e.target.value)} />
              <Input placeholder="Source registry" value={ruleSource} onChange={e => setRuleSource(e.target.value)} />
              <Input placeholder="Target registries (comma-sep)" value={ruleTargets} onChange={e => setRuleTargets(e.target.value)} />
            </div>
            <DialogFooter><Button onClick={() => { apiClient.createReplicationRule(ruleName, ruleSource, ruleTargets.split(',')); toast.success('Rule created'); setShowRuleDialog(false); }}>Create</Button></DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardHeader><CardTitle>Images</CardTitle></CardHeader>
        <CardContent>
          <Table>
            <TableHeader><TableRow><TableHead>Name</TableHead><TableHead>Tag</TableHead><TableHead>Registry</TableHead><TableHead>Size</TableHead><TableHead>Vulns</TableHead><TableHead>Actions</TableHead></TableRow></TableHeader>
            <TableBody>{images.map(img => (
              <TableRow key={img.id}>
                <TableCell className="font-medium">{img.name}</TableCell>
                <TableCell><Badge variant="outline">{img.tag}</Badge></TableCell>
                <TableCell>{img.registry}</TableCell>
                <TableCell>{img.size_mb}MB</TableCell>
                <TableCell><Badge variant={img.vulnerability_count > 5 ? 'destructive' : img.vulnerability_count > 0 ? 'secondary' : 'default'}>{img.vulnerability_count || 0}</Badge></TableCell>
                <TableCell><Button variant="outline" size="sm" onClick={() => scanImage(img.id)}>Scan</Button></TableCell>
              </TableRow>
            ))}</TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};

  const [replicationJobs, setReplicationJobs] = useState<any[]>([]);
  const [showJobDialog, setShowJobDialog] = useState(false);
  const [jobImageId, setJobImageId] = useState('');
  const [jobTargets, setJobTargets] = useState('');
  const [filterRegistry, setFilterRegistry] = useState('');
  const [cachedImages, setCachedImages] = useState<any[]>([]);

  useEffect(() => {
    loadCachedImages();
  }, []);

  const loadCachedImages = async () => {
    try { const data = await apiClient.getRegistryCache(); setCachedImages(data || []); } catch { /* ignore */ }
  };

  const startReplication = async () => {
    try {
      const result = await apiClient.replicateImageTo(jobImageId, jobTargets.split(','));
      setReplicationJobs([...replicationJobs, result]);
      toast.success('Replication started');
      setShowJobDialog(false);
    } catch { toast.error('Replication failed'); }
  };

  const filteredImages = images.filter(img => {
    if (filterRegistry && img.registry !== filterRegistry) return false;
    return true;
  });

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="grid grid-cols-4 gap-4">
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Images</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{images.length}</p></CardContent></Card>
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Cached</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{cachedImages.length}</p></CardContent></Card>
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Replication Jobs</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{replicationJobs.length}</p></CardContent></Card>
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Registries</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">6</p></CardContent></Card>
      </div>

      <div className="flex items-center gap-4">
        <Select value={filterRegistry} onValueChange={setFilterRegistry}>
          <SelectTrigger className="w-[200px]"><SelectValue placeholder="All Registries" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="">All Registries</SelectItem>
            <SelectItem value="docker_hub">Docker Hub</SelectItem>
            <SelectItem value="aws_ecr">AWS ECR</SelectItem>
            <SelectItem value="azure_acr">Azure ACR</SelectItem>
            <SelectItem value="gcp_gcr">GCP GCR</SelectItem>
          </SelectContent>
        </Select>
        <Dialog open={showJobDialog} onOpenChange={setShowJobDialog}>
          <DialogTrigger asChild><Button>Replicate Image</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>Replicate Image</DialogTitle></DialogHeader>
            <div className="space-y-2">
              <Input placeholder="Image ID" value={jobImageId} onChange={e => setJobImageId(e.target.value)} />
              <Input placeholder="Target registries (comma-sep)" value={jobTargets} onChange={e => setJobTargets(e.target.value)} />
            </div>
            <DialogFooter><Button onClick={startReplication}>Replicate</Button></DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardHeader><CardTitle>Replication Jobs</CardTitle></CardHeader>
        <CardContent>
          <Table>
            <TableHeader><TableRow><TableHead>Job ID</TableHead><TableHead>Target</TableHead><TableHead>State</TableHead></TableRow></TableHeader>
            <TableBody>{replicationJobs.map((j, i) => (
              <TableRow key={i}>
                <TableCell className="font-mono text-xs">{j.job_id || j.id}</TableCell>
                <TableCell>{j.target || j.target_registry}</TableCell>
                <TableCell><Badge variant={j.state === 'completed' ? 'default' : 'secondary'}>{j.state}</Badge></TableCell>
              </TableRow>
            ))}</TableBody>
          </Table>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Cached Images</CardTitle></CardHeader>
        <CardContent>
          <Table>
            <TableHeader><TableRow><TableHead>Image</TableHead><TableHead>Registry</TableHead><TableHead>TTL</TableHead></TableRow></TableHeader>
            <TableBody>{cachedImages.slice(0, 10).map((c, i) => (
              <TableRow key={i}>
                <TableCell className="font-medium">{c.name || c.image}</TableCell>
                <TableCell><Badge variant="outline">{c.registry}</Badge></TableCell>
                <TableCell>{c.ttl_hours || c.ttl}h</TableCell>
              </TableRow>
            ))}</TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};

function ImageFormDialog({ open, onOpenChange, onSubmit }: { open: boolean; onOpenChange: (v: boolean) => void; onSubmit: (data: any) => void }) {
  const [name, setName] = useState(''); const [tag, setTag] = useState('latest'); const [registry, setRegistry] = useState('docker_hub');
  return (
    <Dialog open={open} onOpenChange={onOpenChange}><DialogContent><DialogHeader><DialogTitle>Register Image</DialogTitle></DialogHeader>
      <div className="space-y-4">
        <div><Label>Name</Label><Input value={name} onChange={e => setName(e.target.value)} /></div>
        <div><Label>Tag</Label><Input value={tag} onChange={e => setTag(e.target.value)} /></div>
        <div><Label>Registry</Label><Select value={registry} onValueChange={setRegistry}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{['aws_ecr','azure_acr','gcp_gcr','docker_hub','ghcr'].map(r => <SelectItem key={r} value={r}>{r}</SelectItem>)}</SelectContent></Select></div>
      </div>
      <DialogFooter><Button onClick={() => { onSubmit({ name, tag, registry }); onOpenChange(false); }}>Register</Button></DialogFooter>
    </DialogContent></Dialog>
  );
}

function VulnerabilityBadge({ severity }: { severity: string }) {
  const colorMap: Record<string, string> = { critical: 'destructive', high: 'destructive', medium: 'secondary', low: 'outline', none: 'default' };
  return <Badge variant={(colorMap[severity] || 'outline') as any}>{severity}</Badge>;
}

function RegistryChart({ images }: { images: any[] }) {
  const byRegistry: Record<string, number> = {};
  images.forEach(i => { byRegistry[i.registry] = (byRegistry[i.registry] || 0) + 1; });
  const sorted = Object.entries(byRegistry).sort((a, b) => b[1] - a[1]);
  return (
    <Card><CardHeader><CardTitle>Images by Registry</CardTitle></CardHeader>
    <CardContent><div className="space-y-2">{sorted.map(([r, c]) => (
      <div key={r} className="flex items-center justify-between"><span className="text-sm">{r}</span><span className="text-sm font-mono">{c}</span><div className="w-1/2 h-2 bg-muted rounded"><div className="h-full bg-primary rounded" style={{ width: `${(c / sorted[0][1]) * 100}%` }} /></div></div>
    ))}</div></CardContent></Card>
  );
}

function SeverityPie({ images }: { images: any[] }) {
  const counts = { critical: 0, high: 0, medium: 0, low: 0, none: 0 };
  images.forEach((i: any) => { const s = i.max_severity || 'none'; counts[s as keyof typeof counts] = (counts[s as keyof typeof counts] || 0) + 1; });
  const total = Object.values(counts).reduce((s, c) => s + c, 0);
  return (
    <Card><CardHeader><CardTitle>Vulnerability Breakdown</CardTitle></CardHeader>
    <CardContent><div className="space-y-1">{(Object.entries(counts) as [string, number][]).map(([sev, cnt]) => (
      <div key={sev} className="flex items-center gap-2"><span className="text-xs w-16 capitalize">{sev}</span><div className="h-3 bg-muted rounded flex-1"><div className="h-full rounded" style={{ width: `${(cnt / total) * 100}%`, background: sev === 'critical' ? '#ef4444' : sev === 'high' ? '#f97316' : sev === 'medium' ? '#eab308' : sev === 'low' ? '#22c55e' : '#6b7280' }} /></div><span className="text-xs w-8 text-right">{cnt}</span></div>
    ))}</div></CardContent></Card>
  );
}

function ReplicationRuleCard({ rule, onDelete }: { rule: any; onDelete: (id: string) => void }) {
  return (
    <Card><CardHeader className="pb-2"><CardTitle className="text-sm">{rule.source} → {rule.targets?.join(', ')}</CardTitle></CardHeader>
    <CardContent><p className="text-xs text-muted-foreground">Pattern: {rule.pattern} | Created: {new Date(rule.created_at).toLocaleDateString()}</p>
    <Button variant="destructive" size="sm" className="mt-2" onClick={() => onDelete(rule.id)}>Delete</Button></CardContent></Card>
  );
}

function FilterTabs({ registries, selected, onChange }: { registries: string[]; selected: string; onChange: (v: string) => void }) {
  return (
    <Tabs value={selected} onValueChange={onChange}><TabsList>{registries.map(r => <TabsTrigger key={r} value={r}>{r}</TabsTrigger>)}</TabsList></Tabs>
  );
}

export default ContainerRegistry;
