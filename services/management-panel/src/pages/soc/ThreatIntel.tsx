import { useEffect, useState } from 'react';
import { apiClient } from '../../lib/api';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../../components/ui/dialog';
import { Select } from '../../components/ui/select';
import { Pagination } from '../../components/ui/pagination';

interface Feed { id: string; name: string; provider: string; status: string; ioc_count: number; last_refresh: string; }
interface IOC { id: string; type: string; value: string; severity: string; confidence: string; source: string; tags?: string[]; created_at?: string; }

export const ThreatIntelPage = () => {
  const [feeds, setFeeds] = useState<Feed[]>([]);
  const [iocs, setIocs] = useState<IOC[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState('all');
  const [severityFilter, setSeverityFilter] = useState('all');
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [summary, setSummary] = useState<any>({});
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<IOC | null>(null);
  const [formData, setFormData] = useState({ type: 'ip', value: '', severity: 'medium', confidence: '50', source: 'manual', tags: '' });
  const [showAddFeedModal, setShowAddFeedModal] = useState(false);
  const [feedForm, setFeedForm] = useState({ name: '', provider: '', url: '' });

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [f, i, sm] = await Promise.all([
        apiClient.get('/api/v1/soc/threat-intel/feeds'),
        apiClient.get('/api/v1/soc/threat-intel/iocs'),
        apiClient.get('/api/v1/soc/threat-intel/summary'),
      ]);
      setFeeds(f?.data || []);
      setIocs(i?.data?.iocs || []);
      setSummary(sm?.data || {});
    } catch { toast.error('Failed to load threat intel'); }
    finally { setLoading(false); }
  };

  const refreshFeed = async (feedId: string) => {
    try {
      await apiClient.post(`/api/v1/soc/threat-intel/feeds/${feedId}/refresh`);
      toast.success('Feed refresh initiated');
    } catch { toast.error('Failed to refresh feed'); }
  };

  const createIOC = async () => {
    try {
      await apiClient.post('/api/v1/soc/threat-intel/iocs', { ...formData, tags: formData.tags.split(',').map(t => t.trim()).filter(Boolean) });
      toast.success('IOC created');
      setShowCreateModal(false);
      setFormData({ type: 'ip', value: '', severity: 'medium', confidence: '50', source: 'manual', tags: '' });
      loadData();
    } catch { toast.error('Failed to create IOC'); }
  };

  const deleteIOC = async () => {
    if (!showDeleteConfirm) return;
    try {
      await apiClient.delete(`/api/v1/soc/threat-intel/iocs/${showDeleteConfirm.id}`);
      toast.success('IOC deleted');
      setShowDeleteConfirm(null);
      loadData();
    } catch { toast.error('Failed to delete IOC'); }
  };

  const addFeed = async () => {
    try {
      await apiClient.post('/api/v1/soc/threat-intel/feeds', feedForm);
      toast.success('Feed added');
      setShowAddFeedModal(false);
      setFeedForm({ name: '', provider: '', url: '' });
      loadData();
    } catch { toast.error('Failed to add feed'); }
  };

  const filteredIocs = iocs.filter(i => {
    if (typeFilter !== 'all' && i.type !== typeFilter) return false;
    if (severityFilter !== 'all' && i.severity !== severityFilter) return false;
    if (searchQuery && !i.value.toLowerCase().includes(searchQuery.toLowerCase()) && !i.source.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  const paginatedIocs = filteredIocs.slice((page - 1) * pageSize, page * pageSize);
  const criticalCount = iocs.filter(i => i.severity === 'critical').length;
  const activeFeeds = feeds.filter(f => f.status === 'active').length;
  const totalIocs = iocs.length;

  return (
    <div className="space-y-6 p-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Threat Intelligence</h1>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setShowAddFeedModal(true)}>Add Feed</Button>
          <Button variant="outline" onClick={() => setShowCreateModal(true)}>Add IOC</Button>
          <Button onClick={loadData}>Refresh</Button>
        </div>
      </div>
      <div className="grid gap-4 md:grid-cols-4">
        <Card><CardHeader><CardTitle>Feeds</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold">{feeds.length}</p><p className="text-xs text-muted-foreground">{activeFeeds} active</p></CardContent></Card>
        <Card><CardHeader><CardTitle>IoCs</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold">{totalIocs}</p><p className="text-xs text-muted-foreground">{criticalCount} critical</p></CardContent></Card>
        <Card><CardHeader><CardTitle>Severity Breakdown</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold text-red-500">{criticalCount}</p><p className="text-xs text-muted-foreground">critical / {iocs.filter(i => i.severity === 'high').length} high</p></CardContent></Card>
        <Card><CardHeader><CardTitle>Active Blocklist</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold">{summary.active_blocklist || 0}</p><p className="text-xs text-muted-foreground">entries blocked</p></CardContent></Card>
      </div>
      <div className="flex gap-4 items-center">
        <Input placeholder="Search IoCs..." value={searchQuery} onChange={e => { setSearchQuery(e.target.value); setPage(1); }} className="max-w-xs" />
        <Select value={typeFilter} onValueChange={v => { setTypeFilter(v); setPage(1); }}>
          <option value="all">All Types</option>
          <option value="ip">IP</option>
          <option value="domain">Domain</option>
          <option value="url">URL</option>
          <option value="hash">Hash</option>
        </Select>
        <Select value={severityFilter} onValueChange={v => { setSeverityFilter(v); setPage(1); }}>
          <option value="all">All Severities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </Select>
      </div>
      <Tabs defaultValue="feeds">
        <TabsList><TabsTrigger value="feeds">Feeds ({feeds.length})</TabsTrigger><TabsTrigger value="iocs">Indicators ({filteredIocs.length})</TabsTrigger></TabsList>
        <TabsContent value="feeds">
          <Table>
            <TableHeader><TableRow><TableHead>Name</TableHead><TableHead>Provider</TableHead><TableHead>Status</TableHead><TableHead>IoCs</TableHead><TableHead>Last Refresh</TableHead><TableHead>Action</TableHead></TableRow></TableHeader>
            <TableBody>
              {feeds.map(f => (
                <TableRow key={f.id}>
                  <TableCell className="font-medium">{f.name}</TableCell>
                  <TableCell>{f.provider}</TableCell>
                  <TableCell><Badge variant={f.status === 'active' ? 'default' : 'secondary'}>{f.status}</Badge></TableCell>
                  <TableCell>{f.ioc_count}</TableCell>
                  <TableCell className="text-xs">{f.last_refresh ? new Date(f.last_refresh).toLocaleString() : 'Never'}</TableCell>
                  <TableCell><Button size="sm" onClick={() => refreshFeed(f.id)}>Refresh</Button></TableCell>
                </TableRow>
              ))}
              {feeds.length === 0 && <TableRow><TableCell colSpan={6} className="text-center py-4 text-muted-foreground">No feeds configured</TableCell></TableRow>}
            </TableBody>
          </Table>
        </TabsContent>
        <TabsContent value="iocs">
          <Table>
            <TableHeader><TableRow><TableHead>Value</TableHead><TableHead>Type</TableHead><TableHead>Severity</TableHead><TableHead>Confidence</TableHead><TableHead>Source</TableHead><TableHead>Created</TableHead><TableHead>Actions</TableHead></TableRow></TableHeader>
            <TableBody>
              {paginatedIocs.map(i => (
                <TableRow key={i.id}>
                  <TableCell className="font-mono text-xs max-w-xs truncate">{i.value}</TableCell>
                  <TableCell><Badge variant="outline">{i.type}</Badge></TableCell>
                  <TableCell><Badge variant={i.severity === 'critical' ? 'destructive' : i.severity === 'high' ? 'default' : 'secondary'}>{i.severity}</Badge></TableCell>
                  <TableCell>{i.confidence}</TableCell>
                  <TableCell>{i.source}</TableCell>
                  <TableCell className="text-xs">{i.created_at ? new Date(i.created_at).toLocaleDateString() : '-'}</TableCell>
                  <TableCell><Button size="sm" variant="destructive" onClick={() => setShowDeleteConfirm(i)}>Delete</Button></TableCell>
                </TableRow>
              ))}
              {paginatedIocs.length === 0 && <TableRow><TableCell colSpan={7} className="text-center py-4 text-muted-foreground">No IoCs found</TableCell></TableRow>}
            </TableBody>
          </Table>
          {filteredIocs.length > pageSize && (
            <Pagination page={page} totalPages={Math.ceil(filteredIocs.length / pageSize)} onPageChange={setPage} />
          )}
        </TabsContent>
      </Tabs>

      <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
        <DialogContent>
          <DialogHeader><DialogTitle>Add IOC</DialogTitle></DialogHeader>
          <div className="space-y-4">
            <div><Label>Type</Label><Select value={formData.type} onValueChange={v => setFormData({ ...formData, type: v })}>
              <option value="ip">IP Address</option><option value="domain">Domain</option><option value="url">URL</option><option value="hash">File Hash</option>
            </Select></div>
            <div><Label>Value</Label><Input value={formData.value} onChange={e => setFormData({ ...formData, value: e.target.value })} /></div>
            <div><Label>Severity</Label><Select value={formData.severity} onValueChange={v => setFormData({ ...formData, severity: v })}>
              <option value="critical">Critical</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option>
            </Select></div>
            <div><Label>Confidence</Label><Select value={formData.confidence} onValueChange={v => setFormData({ ...formData, confidence: v })}>
              <option value="25">Low (25)</option><option value="50">Medium (50)</option><option value="75">High (75)</option><option value="100">Confirmed (100)</option>
            </Select></div>
            <div><Label>Tags (comma-separated)</Label><Input value={formData.tags} onChange={e => setFormData({ ...formData, tags: e.target.value })} placeholder="ransomware, c2, etc" /></div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateModal(false)}>Cancel</Button>
            <Button onClick={createIOC}>Add IOC</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={showAddFeedModal} onOpenChange={setShowAddFeedModal}>
        <DialogContent>
          <DialogHeader><DialogTitle>Add Threat Feed</DialogTitle></DialogHeader>
          <div className="space-y-4">
            <div><Label>Name</Label><Input value={feedForm.name} onChange={e => setFeedForm({ ...feedForm, name: e.target.value })} /></div>
            <div><Label>Provider</Label><Input value={feedForm.provider} onChange={e => setFeedForm({ ...feedForm, provider: e.target.value })} /></div>
            <div><Label>Feed URL</Label><Input value={feedForm.url} onChange={e => setFeedForm({ ...feedForm, url: e.target.value })} /></div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAddFeedModal(false)}>Cancel</Button>
            <Button onClick={addFeed}>Add Feed</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={!!showDeleteConfirm} onOpenChange={() => setShowDeleteConfirm(null)}>
        <DialogContent>
          <DialogHeader><DialogTitle>Delete IOC</DialogTitle></DialogHeader>
          <p>Delete IOC "{showDeleteConfirm?.value}"?</p>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDeleteConfirm(null)}>Cancel</Button>
            <Button variant="destructive" onClick={deleteIOC}>Delete</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-6">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Total IoCs</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{summary.total_iocs || 0}</div><p className="text-xs text-muted-foreground">{summary.new_iocs_24h || 0} new in 24h</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Active Feeds</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{summary.active_feeds || 0}</div><p className="text-xs text-muted-foreground">{summary.total_feeds || 0} total feeds</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Enrichment Rate</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{summary.enrichment_rate || 0}%</div><p className="text-xs text-muted-foreground">IoCs matched to entities</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Correlated Alerts</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-red-500">{summary.correlated_alerts || 0}</div><p className="text-xs text-muted-foreground">alerts generated from intel</p></CardContent></Card>
      </div>

      <Tabs defaultValue="ioc_trend" className="mb-6">
        <TabsList><TabsTrigger value="ioc_trend">IOC Trend</TabsTrigger><TabsTrigger value="ioc_types">IOC Types</TabsTrigger><TabsTrigger value="feed_health">Feed Health</TabsTrigger></TabsList>
        <TabsContent value="ioc_trend">
          <Card><CardHeader><CardTitle>IOC Ingestion Trend (Last 30 Days)</CardTitle></CardHeader><CardContent>
            <div className="space-y-2">{summary.ioc_trend?.map?.((p: any, i: number) => (<div key={i} className="flex items-center justify-between"><span className="text-sm">{p.date}</span><div className="h-2 bg-red-500 rounded" style={{ width: `${(p.count / (summary.ioc_trend?.[0]?.count || 1)) * 100}%` }} /><span className="text-sm font-mono">{p.count}</span></div>))}</div>
          </CardContent></Card>
        </TabsContent>
        <TabsContent value="ioc_types">
          <Card><CardHeader><CardTitle>IOC Type Distribution</CardTitle></CardHeader><CardContent>
            <Table><TableHeader><TableRow><TableHead>Type</TableHead><TableHead>Count</TableHead><TableHead>Percent</TableHead></TableRow></TableHeader><TableBody>
              {summary.ioc_types?.map?.((t: any, i: number) => (<TableRow key={i}><TableCell className="font-medium">{t.type}</TableCell><TableCell>{t.count}</TableCell><TableCell>{t.percent}%</TableCell></TableRow>))}
              {(!summary.ioc_types || summary.ioc_types.length === 0) && <TableRow><TableCell colSpan={3} className="text-center text-muted-foreground">No IOC type data available</TableCell></TableRow>}
            </TableBody></Table>
          </CardContent></Card>
        </TabsContent>
        <TabsContent value="feed_health">
          <Card><CardHeader><CardTitle>Threat Feed Health</CardTitle></CardHeader><CardContent>
            <div className="space-y-2">{summary.feed_health?.map?.((f: any, i: number) => (<div key={i} className="flex items-center justify-between p-2 border rounded"><div><span className="font-medium">{f.name}</span><span className="text-sm text-muted-foreground ml-2">{f.provider}</span></div><Badge variant={f.healthy ? 'default' : 'destructive'}>{f.healthy ? 'Healthy' : 'Degraded'}</Badge></div>))}</div>
          </CardContent></Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};
