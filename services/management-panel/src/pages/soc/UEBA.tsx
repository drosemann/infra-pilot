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

interface EntityProfile { id: string; name: string; entity_type: string; display_name: string; risk_level: string; risk_score: number; tags?: string[]; last_seen?: string; }
interface AnomalyAlert { id: string; entity_id: string; entity_name: string; title: string; risk_level: string; risk_score: number; detected_at: string; acknowledged: boolean; acknowledged_by?: string; }

export const UEBAPage = () => {
  const [entities, setEntities] = useState<EntityProfile[]>([]);
  const [alerts, setAlerts] = useState<AnomalyAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [riskFilter, setRiskFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [selectedEntity, setSelectedEntity] = useState<EntityProfile | null>(null);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [e, a] = await Promise.all([
        apiClient.get('/api/v1/soc/ueba/entities'),
        apiClient.get('/api/v1/soc/ueba/alerts'),
      ]);
      setEntities(e?.data || []);
      setAlerts(a?.data || []);
    } catch { toast.error('Failed to load UEBA data'); }
    finally { setLoading(false); }
  };

  const acknowledgeAlert = async (id: string) => {
    try {
      await apiClient.post(`/api/v1/soc/ueba/alerts/${id}/acknowledge`);
      toast.success('Alert acknowledged');
      loadData();
    } catch { toast.error('Failed to acknowledge alert'); }
  };

  const filteredEntities = entities.filter(e => {
    if (riskFilter === 'high_risk' && !['high', 'critical'].includes(e.risk_level)) return false;
    if (typeFilter !== 'all' && e.entity_type !== typeFilter) return false;
    if (searchQuery && !e.name.toLowerCase().includes(searchQuery.toLowerCase()) && !e.display_name.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  const paginatedEntities = filteredEntities.slice((page - 1) * pageSize, page * pageSize);
  const highRiskCount = entities.filter(e => ['high', 'critical'].includes(e.risk_level)).length;
  const unacknowledgedAlerts = alerts.filter(a => !a.acknowledged).length;
  const avgRiskScore = entities.length ? (entities.reduce((s, e) => s + e.risk_score, 0) / entities.length).toFixed(1) : '0';

  return (
    <div className="space-y-6 p-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">User & Entity Behavior Analytics</h1>
        <Button onClick={loadData}>Refresh</Button>
      </div>
      <div className="grid gap-4 md:grid-cols-4">
        <Card><CardHeader><CardTitle>Entities</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold">{entities.length}</p><p className="text-xs text-muted-foreground">avg risk {avgRiskScore}</p></CardContent></Card>
        <Card><CardHeader><CardTitle>High Risk</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold text-red-500">{highRiskCount}</p></CardContent></Card>
        <Card><CardHeader><CardTitle>Alerts</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold">{alerts.length}</p></CardContent></Card>
        <Card><CardHeader><CardTitle>Unacknowledged</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold text-orange-500">{unacknowledgedAlerts}</p></CardContent></Card>
      </div>
      <div className="flex gap-4 items-center">
        <Input placeholder="Search entities..." value={searchQuery} onChange={e => { setSearchQuery(e.target.value); setPage(1); }} className="max-w-xs" />
        <Select value={riskFilter} onValueChange={v => { setRiskFilter(v); setPage(1); }}>
          <option value="all">All Risk Levels</option>
          <option value="high_risk">High/Critical</option>
        </Select>
        <Select value={typeFilter} onValueChange={v => { setTypeFilter(v); setPage(1); }}>
          <option value="all">All Types</option>
          <option value="user">User</option>
          <option value="service_account">Service Account</option>
          <option value="application">Application</option>
        </Select>
      </div>
      <Tabs defaultValue="entities">
        <TabsList><TabsTrigger value="entities">Entities ({filteredEntities.length})</TabsTrigger><TabsTrigger value="alerts">Anomaly Alerts ({alerts.length})</TabsTrigger></TabsList>
        <TabsContent value="entities">
          <Table>
            <TableHeader><TableRow><TableHead>Name</TableHead><TableHead>Type</TableHead><TableHead>Display Name</TableHead><TableHead>Risk Level</TableHead><TableHead>Risk Score</TableHead><TableHead>Last Seen</TableHead></TableRow></TableHeader>
            <TableBody>
              {paginatedEntities.map(e => (
                <TableRow key={e.id} className="cursor-pointer" onClick={() => setSelectedEntity(e)}>
                  <TableCell className="font-medium">{e.name}</TableCell>
                  <TableCell><Badge variant="outline">{e.entity_type}</Badge></TableCell>
                  <TableCell>{e.display_name}</TableCell>
                  <TableCell><Badge variant={['critical', 'high'].includes(e.risk_level) ? 'destructive' : e.risk_level === 'medium' ? 'default' : 'secondary'}>{e.risk_level}</Badge></TableCell>
                  <TableCell>{e.risk_score}</TableCell>
                  <TableCell className="text-xs">{e.last_seen ? new Date(e.last_seen).toLocaleDateString() : '-'}</TableCell>
                </TableRow>
              ))}
              {paginatedEntities.length === 0 && <TableRow><TableCell colSpan={6} className="text-center py-4 text-muted-foreground">No entities found</TableCell></TableRow>}
            </TableBody>
          </Table>
          {filteredEntities.length > pageSize && (
            <Pagination page={page} totalPages={Math.ceil(filteredEntities.length / pageSize)} onPageChange={setPage} />
          )}
        </TabsContent>
        <TabsContent value="alerts">
          <Table>
            <TableHeader><TableRow><TableHead>Title</TableHead><TableHead>Entity</TableHead><TableHead>Risk Level</TableHead><TableHead>Score</TableHead><TableHead>Detected</TableHead><TableHead>Status</TableHead><TableHead>Actions</TableHead></TableRow></TableHeader>
            <TableBody>
              {alerts.map(a => (
                <TableRow key={a.id}>
                  <TableCell className="font-medium max-w-xs truncate">{a.title}</TableCell>
                  <TableCell>{a.entity_name}</TableCell>
                  <TableCell><Badge variant={a.risk_level === 'critical' ? 'destructive' : a.risk_level === 'high' ? 'default' : 'secondary'}>{a.risk_level}</Badge></TableCell>
                  <TableCell>{a.risk_score}</TableCell>
                  <TableCell className="text-xs">{new Date(a.detected_at).toLocaleString()}</TableCell>
                  <TableCell>{a.acknowledged ? <Badge variant="default">Acknowledged</Badge> : <Badge variant="secondary">New</Badge>}</TableCell>
                  <TableCell>{!a.acknowledged && <Button size="sm" onClick={() => acknowledgeAlert(a.id)}>Acknowledge</Button>}</TableCell>
                </TableRow>
              ))}
              {alerts.length === 0 && <TableRow><TableCell colSpan={7} className="text-center py-4 text-muted-foreground">No alerts</TableCell></TableRow>}
            </TableBody>
          </Table>
        </TabsContent>
      </Tabs>

      <Dialog open={!!selectedEntity} onOpenChange={() => setSelectedEntity(null)}>
        <DialogContent className="max-w-lg">
          <DialogHeader><DialogTitle>{selectedEntity?.display_name || selectedEntity?.name}</DialogTitle></DialogHeader>
          <div className="space-y-3">
            <p><strong>Type:</strong> {selectedEntity?.entity_type}</p>
            <p><strong>Risk Level:</strong> {selectedEntity?.risk_level} (Score: {selectedEntity?.risk_score})</p>
            <p><strong>Tags:</strong> {selectedEntity?.tags?.join(', ') || 'None'}</p>
            <p><strong>Last Seen:</strong> {selectedEntity?.last_seen ? new Date(selectedEntity.last_seen).toLocaleString() : 'N/A'}</p>
            <p><strong>Entity Alerts:</strong> {alerts.filter(a => a.entity_id === selectedEntity?.id).length}</p>
          </div>
          <DialogFooter><Button variant="outline" onClick={() => setSelectedEntity(null)}>Close</Button></DialogFooter>
        </DialogContent>
      </Dialog>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-6">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Entities Monitored</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{summary.total_entities || 0}</div><p className="text-xs text-muted-foreground">{summary.active_entities || 0} active this period</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Anomalies (24h)</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-orange-500">{summary.anomalies_24h || 0}</div><p className="text-xs text-muted-foreground">{summary.anomaly_alerts || 0} escalated to alerts</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Avg Risk Score</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{summary.avg_risk_score || 0}</div><p className="text-xs text-muted-foreground">across all entities</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Baselines</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{summary.baselines || 0}</div><p className="text-xs text-muted-foreground">behavioral baselines established</p></CardContent></Card>
      </div>

      <Tabs defaultValue="anomaly_trend" className="mb-6">
        <TabsList><TabsTrigger value="anomaly_trend">Anomaly Trend</TabsTrigger><TabsTrigger value="risk_distribution">Risk Distribution</TabsTrigger><TabsTrigger value="top_anomalies">Top Anomalies</TabsTrigger></TabsList>
        <TabsContent value="anomaly_trend">
          <Card><CardHeader><CardTitle>Anomaly Detection Trend (Last 30 Days)</CardTitle></CardHeader><CardContent>
            <div className="space-y-2">{summary.anomaly_trend?.map?.((p: any, i: number) => (<div key={i} className="flex items-center justify-between"><span className="text-sm">{p.date}</span><div className="h-2 bg-orange-500 rounded" style={{ width: `${(p.count / (summary.anomaly_trend?.[0]?.count || 1)) * 100}%` }} /><span className="text-sm font-mono">{p.count}</span></div>))}</div>
          </CardContent></Card>
        </TabsContent>
        <TabsContent value="risk_distribution">
          <Card><CardHeader><CardTitle>Entity Risk Distribution</CardTitle></CardHeader><CardContent>
            <Table><TableHeader><TableRow><TableHead>Risk Level</TableHead><TableHead>Entities</TableHead><TableHead>Percent</TableHead></TableRow></TableHeader><TableBody>
              {summary.risk_distribution?.map?.((r: any, i: number) => (<TableRow key={i}><TableCell className="font-medium">{r.level}</TableCell><TableCell>{r.count}</TableCell><TableCell>{r.percent}%</TableCell></TableRow>))}
              {(!summary.risk_distribution || summary.risk_distribution.length === 0) && <TableRow><TableCell colSpan={3} className="text-center text-muted-foreground">No risk data available</TableCell></TableRow>}
            </TableBody></Table>
          </CardContent></Card>
        </TabsContent>
        <TabsContent value="top_anomalies">
          <Card><CardHeader><CardTitle>Top Anomaly Types</CardTitle></CardHeader><CardContent>
            <div className="space-y-2">{summary.top_anomaly_types?.map?.((a: any, i: number) => (<div key={i} className="flex items-center justify-between p-2 border rounded"><span>{a.type}</span><span className="text-sm font-mono">{a.count} ({a.percent}%)</span></div>))}</div>
          </CardContent></Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};
