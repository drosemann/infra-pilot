import { useState, useEffect, useCallback } from 'react';
import { toast } from 'sonner';
import { apiClient } from '../../lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Globe, Search, Filter, Shield, CheckCircle, XCircle, RefreshCw, PlusCircle, ArrowRight, AlertTriangle, Database, MapPin, Activity, FileText, BookOpen, Lock, GitBranch } from 'lucide-react';

function ResidencyStatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = { compliant: 'bg-green-600', non_compliant: 'bg-red-600', pending: 'bg-yellow-600', migrating: 'bg-blue-600', unknown: 'bg-slate-600' };
  return <Badge className={colors[status] || 'bg-slate-600'}>{status}</Badge>;
}

function FlowDiagramCard({ flows }: { flows: any[] }) {
  if (!flows?.length) return null;
  return (
    <Card><CardHeader><CardTitle className="flex items-center gap-2"><Activity className="h-4 w-4 text-blue-400" /> Data Flow Map</CardTitle></CardHeader>
      <CardContent><div className="space-y-2">{flows.map((f: any, i: number) => (
        <div key={i} className="flex items-center gap-2 p-2 bg-slate-800 rounded">
          <MapPin className="h-4 w-4 text-green-400 shrink-0" />
          <span className="text-xs text-white">{f.source_region}</span>
          <ArrowRight className="h-3 w-3 text-slate-400 shrink-0" />
          <MapPin className="h-4 w-4 text-blue-400 shrink-0" />
          <span className="text-xs text-white">{f.destination_region}</span>
          <Badge variant="outline" className="ml-auto text-xs">{f.resource_type}</Badge>
          <ResidencyStatusBadge status={f.compliance_status || f.status} />
        </div>
      ))}</div></CardContent></Card>
  );
}

function MoveAssetForm({ onCreated }: { onCreated: () => void }) {
  const [assetId, setAssetId] = useState('');
  const [sourceRegion, setSourceRegion] = useState('us-east-1');
  const [destinationRegion, setDestinationRegion] = useState('eu-west-1');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (!assetId) { toast.error('Asset ID required'); return; }
    setSubmitting(true);
    try {
      await apiClient.post('/api/v1/compliance/residency/move', { asset_id: assetId, source_region: sourceRegion, destination_region: destinationRegion, reason: 'Compliance requirement' });
      toast.success('Asset move initiated');
      onCreated();
    } catch { toast.error('Move failed'); }
    setSubmitting(false);
  };

  return (
    <Card><CardHeader><CardTitle className="flex items-center gap-2"><ArrowRight className="h-4 w-4 text-green-400" /> Move Asset</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        <Input className="bg-slate-800 border-slate-700 text-white" placeholder="Asset ID" value={assetId} onChange={(e) => setAssetId(e.target.value)} />
        <select className="w-full bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-sm text-white" value={sourceRegion} onChange={(e) => setSourceRegion(e.target.value)}>
          <option value="us-east-1">US East (N. Virginia)</option><option value="us-west-2">US West (Oregon)</option><option value="eu-west-1">EU (Ireland)</option><option value="eu-central-1">EU (Frankfurt)</option><option value="ap-southeast-1">Asia (Singapore)</option>
        </select>
        <select className="w-full bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-sm text-white" value={destinationRegion} onChange={(e) => setDestinationRegion(e.target.value)}>
          <option value="eu-west-1">EU (Ireland)</option><option value="eu-central-1">EU (Frankfurt)</option><option value="us-east-1">US East (N. Virginia)</option><option value="ap-southeast-1">Asia (Singapore)</option>
        </select>
        <Button onClick={handleSubmit} disabled={submitting} className="bg-blue-600 hover:bg-blue-700 w-full">Move Asset</Button>
      </CardContent></Card>
  );
}

function ViolationCard({ violations }: { violations: any[] }) {
  if (!violations?.length) return null;
  return (
    <Card><CardHeader><CardTitle className="flex items-center gap-2"><AlertTriangle className="h-4 w-4 text-red-400" /> Residency Violations ({violations.length})</CardTitle></CardHeader>
      <CardContent><div className="space-y-2">{violations.map((v: any, i: number) => (
        <div key={i} className="p-2 bg-red-900/20 border border-red-800 rounded">
          <p className="text-sm text-white">{v.asset_id} - {v.region}</p>
          <p className="text-xs text-red-300">{v.reason}</p>
        </div>
      ))}</div></CardContent></Card>
  );
}

export default function DataResidencyPage() {
  const [assets, setAssets] = useState<any[]>([]);
  const [flows, setFlows] = useState<any[]>([]);
  const [violations, setViolations] = useState<any[]>([]);
  const [policies, setPolicies] = useState<any[]>([]);
  const [auditLog, setAuditLog] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [tab, setTab] = useState<'assets' | 'flows' | 'policies' | 'audit'>('assets');
  const [query, setQuery] = useState('');
  const [filterRegion, setFilterRegion] = useState('');
  const [showMove, setShowMove] = useState(false);
  const [selectedAsset, setSelectedAsset] = useState<any>(null);

  const fetchData = useCallback(() => {
    apiClient.get('/api/v1/compliance/residency/assets').then(setAssets).catch(() => {});
    apiClient.get('/api/v1/compliance/residency/flows').then(setFlows).catch(() => {});
    apiClient.get('/api/v1/compliance/residency/violations').then(setViolations).catch(() => {});
    apiClient.get('/api/v1/compliance/residency/policies').then(setPolicies).catch(() => {});
    apiClient.get('/api/v1/compliance/residency/audit').then(setAuditLog).catch(() => {});
    apiClient.get('/api/v1/compliance/residency/stats').then(setStats).catch(() => {});
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const filteredAssets = assets.filter((a: any) => {
    if (query && !a.asset_id?.toLowerCase().includes(query.toLowerCase()) && !a.resource_type?.toLowerCase().includes(query.toLowerCase())) return false;
    if (filterRegion && a.current_region !== filterRegion && a.region !== filterRegion) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div><h1 className="text-3xl font-bold text-white mb-2">Data Residency</h1><p className="text-slate-400">Manage data residency compliance across regions, track asset locations, and monitor data flows</p></div>
        <div className="flex gap-2">
          <Button onClick={fetchData} variant="outline" className="text-slate-400"><RefreshCw className="mr-2 h-4 w-4" /> Refresh</Button>
          <Button onClick={() => setShowMove(!showMove)} className="bg-blue-600 hover:bg-blue-700"><ArrowRight className="mr-2 h-4 w-4" /> Move Asset</Button>
        </div>
      </div>
      {stats && (
        <div className="grid grid-cols-4 gap-4">
          <Card><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Total Assets</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-white">{stats.total_assets}</div></CardContent></Card>
          <Card><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Compliant</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-green-400">{stats.compliant_count}</div></CardContent></Card>
          <Card><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Regions</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-white">{stats.unique_regions}</div></CardContent></Card>
          <Card><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Flows</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-blue-400">{stats.total_flows}</div></CardContent></Card>
        </div>
      )}
      <div className="flex space-x-2 border-b border-slate-700 pb-2">
        <Button variant={tab === 'assets' ? 'default' : 'ghost'} onClick={() => setTab('assets')}><Database className="mr-2 h-4 w-4" /> Assets</Button>
        <Button variant={tab === 'flows' ? 'default' : 'ghost'} onClick={() => setTab('flows')}><Activity className="mr-2 h-4 w-4" /> Data Flows</Button>
        <Button variant={tab === 'policies' ? 'default' : 'ghost'} onClick={() => setTab('policies')}><Lock className="mr-2 h-4 w-4" /> Policies</Button>
        <Button variant={tab === 'audit' ? 'default' : 'ghost'} onClick={() => setTab('audit')}><FileText className="mr-2 h-4 w-4" /> Audit Log</Button>
      </div>
      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2">
          {tab === 'assets' && (
            <Card><CardHeader><CardTitle>Data Assets ({filteredAssets.length})</CardTitle></CardHeader>
              <CardContent>
                <div className="flex gap-3 items-center mb-4">
                  <div className="relative flex-1"><Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                    <Input className="pl-9 bg-slate-800 border-slate-700 text-white" placeholder="Search assets..." value={query} onChange={(e) => setQuery(e.target.value)} /></div>
                  <select className="bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-sm text-white" value={filterRegion} onChange={(e) => setFilterRegion(e.target.value)}>
                    <option value="">All Regions</option><option value="us-east-1">US East</option><option value="eu-west-1">EU West</option><option value="eu-central-1">EU Central</option><option value="ap-southeast-1">Asia</option>
                  </select>
                </div>
                <Table><TableHeader><TableRow><TableHead className="text-slate-400">ID</TableHead><TableHead className="text-slate-400">Type</TableHead><TableHead className="text-slate-400">Region</TableHead><TableHead className="text-slate-400">Framework</TableHead><TableHead className="text-slate-400">Status</TableHead><TableHead className="text-slate-400">Actions</TableHead></TableRow></TableHeader>
                  <TableBody>{filteredAssets.map((a: any) => (
                    <TableRow key={a.asset_id || a.id}>
                      <TableCell className="font-mono text-xs text-white">{a.asset_id || a.id}</TableCell>
                      <TableCell><Badge variant="outline" className="text-xs">{a.resource_type || a.type}</Badge></TableCell>
                      <TableCell className="text-white text-sm">{a.current_region || a.region}</TableCell>
                      <TableCell><Badge variant="outline" className="text-xs">{a.framework}</Badge></TableCell>
                      <TableCell><ResidencyStatusBadge status={a.compliance_status || a.status} /></TableCell>
                      <TableCell><Button size="sm" variant="ghost" className="text-blue-400" onClick={() => setSelectedAsset(a)}>Review</Button></TableCell>
                    </TableRow>
                  ))}</TableBody></Table>
              </CardContent></Card>
          )}
          {tab === 'flows' && <FlowDiagramCard flows={flows} />}
          {tab === 'policies' && (
            <Card><CardHeader><CardTitle className="flex items-center gap-2"><Lock className="h-4 w-4 text-purple-400" /> Residency Policies ({policies.length})</CardTitle></CardHeader>
              <CardContent>
                <Table><TableHeader><TableRow><TableHead className="text-slate-400">Policy</TableHead><TableHead className="text-slate-400">Region</TableHead><TableHead className="text-slate-400">Constraint</TableHead><TableHead className="text-slate-400">Enforcement</TableHead><TableHead className="text-slate-400">Status</TableHead></TableRow></TableHeader>
                  <TableBody>{policies.map((p: any, i: number) => (
                    <TableRow key={p.policy_id || i}>
                      <TableCell className="text-white text-sm">{p.name || p.policy_id}</TableCell>
                      <TableCell><Badge variant="outline" className="text-xs">{p.region}</Badge></TableCell>
                      <TableCell className="text-xs text-slate-400">{p.constraint || p.description}</TableCell>
                      <TableCell><Badge className={p.enforcement === 'hard' ? 'bg-red-600' : 'bg-yellow-600'}>{p.enforcement || 'soft'}</Badge></TableCell>
                      <TableCell><ResidencyStatusBadge status={p.status || 'active'} /></TableCell>
                    </TableRow>
                  ))}</TableBody></Table>
              </CardContent></Card>
          )}
          {tab === 'audit' && (
            <Card><CardHeader><CardTitle className="flex items-center gap-2"><FileText className="h-4 w-4 text-blue-400" /> Audit Trail ({auditLog.length})</CardTitle></CardHeader>
              <CardContent>
                <Table><TableHeader><TableRow><TableHead className="text-slate-400">Timestamp</TableHead><TableHead className="text-slate-400">Action</TableHead><TableHead className="text-slate-400">Asset</TableHead><TableHead className="text-slate-400">User</TableHead><TableHead className="text-slate-400">Details</TableHead></TableRow></TableHeader>
                  <TableBody>{auditLog.slice(0, 50).map((a: any, i: number) => (
                    <TableRow key={i}>
                      <TableCell className="text-xs text-slate-400">{a.timestamp ? new Date(a.timestamp).toLocaleString() : 'N/A'}</TableCell>
                      <TableCell><Badge className={a.action === 'move' ? 'bg-blue-600' : a.action === 'create' ? 'bg-green-600' : 'bg-yellow-600'}>{a.action}</Badge></TableCell>
                      <TableCell className="font-mono text-xs text-white">{a.asset_id}</TableCell>
                      <TableCell className="text-xs text-slate-400">{a.user_id}</TableCell>
                      <TableCell className="text-xs text-slate-400">{a.detail || '-'}</TableCell>
                    </TableRow>
                  ))}</TableBody></Table>
              </CardContent></Card>
          )}
        </div>
        <div className="space-y-4">
          {showMove && <MoveAssetForm onCreated={fetchData} />}
          {violations?.length > 0 && <ViolationCard violations={violations} />}
          {selectedAsset && (
            <Card><CardHeader><CardTitle className="text-sm">Asset Detail</CardTitle></CardHeader>
              <CardContent className="space-y-2">
                <div className="flex justify-between"><span className="text-xs text-slate-400">ID</span><span className="text-xs text-white font-mono">{selectedAsset.asset_id || selectedAsset.id}</span></div>
                <div className="flex justify-between"><span className="text-xs text-slate-400">Type</span><span className="text-xs text-white">{selectedAsset.resource_type || selectedAsset.type}</span></div>
                <div className="flex justify-between"><span className="text-xs text-slate-400">Region</span><span className="text-xs text-white">{selectedAsset.current_region || selectedAsset.region}</span></div>
                <div className="flex justify-between"><span className="text-xs text-slate-400">Framework</span><Badge variant="outline" className="text-xs">{selectedAsset.framework}</Badge></div>
                <div className="flex justify-between"><span className="text-xs text-slate-400">Status</span><ResidencyStatusBadge status={selectedAsset.compliance_status || selectedAsset.status} /></div>
              </CardContent></Card>
          )}
        </div>
      </div>
    </div>
  );
}
import React from "react";

interface data_residencyAction {
  id: string;
  type: string;
  status: string;
  ts: string;
}

const data_residencyActions: React.FC<{}> = () => {
  const [items, setItems] = React.useState<data_residencyAction[]>([]);
  const [loading, setLoading] = React.useState(false);
  React.useEffect(() => {
    setLoading(true);
    setItems([
      { id: "1", type: "create", status: "done", ts: new Date().toISOString() },
      { id: "2", type: "update", status: "pending", ts: new Date().toISOString() },
    ]);
    setLoading(false);
  }, []);
  if (loading) return <div>Loading...</div>;
  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-4">data_residency Actions</h2>
      <div className="grid gap-4">
        {items.map((a) => (
          <div key={a.id} className="border rounded p-3 shadow-sm">
            <span className="font-medium">{a.type}</span>
            <span className={"ml-2 px-2 py-1 rounded " + (a.status === "done" ? "bg-green-100" : "bg-yellow-100")}>{a.status}</span>
          </div>
        ))}
      </div>
    </div>
  );
};
export default data_residencyActions;
