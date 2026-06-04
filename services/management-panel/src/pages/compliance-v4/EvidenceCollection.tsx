import { useState, useEffect, useCallback } from 'react';
import { toast } from 'sonner';
import { apiClient } from '../../lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { FileText, Archive, Search, Filter, Shield, CheckCircle, XCircle, RefreshCw, PlusCircle, Download, Upload, Eye, Hash, Clock, AlertTriangle } from 'lucide-react';

function EvidenceStatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = { active: 'bg-green-600', expired: 'bg-yellow-600', deleted: 'bg-red-600', finalized: 'bg-blue-600', draft: 'bg-slate-600' };
  return <Badge className={colors[status] || 'bg-slate-600'}>{status}</Badge>;
}

function EvidenceDetailModal({ evidenceId, onClose }: { evidenceId: string; onClose: () => void }) {
  const [item, setItem] = useState<any>(null);
  useEffect(() => {
    apiClient.get(`/api/v1/compliance/evidence/${evidenceId}`).then(setItem).catch(() => setItem(null));
  }, [evidenceId]);
  if (!item) return null;
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-slate-800 rounded-lg p-6 w-[550px] border border-slate-700" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-start justify-between mb-4">
          <div><h3 className="text-lg font-bold text-white">Evidence Detail</h3><p className="text-sm text-slate-400 font-mono">{evidenceId}</p></div>
          <EvidenceStatusBadge status={item.status} />
        </div>
        <div className="grid grid-cols-2 gap-3 mb-4">
          <div><p className="text-xs text-slate-400">Type</p><p className="text-white">{item.evidence_type}</p></div>
          <div><p className="text-xs text-slate-400">Control</p><Badge variant="outline">{item.control_id}</Badge></div>
          <div><p className="text-xs text-slate-400">Framework</p><p className="text-white">{item.framework}</p></div>
          <div><p className="text-xs text-slate-400">Source</p><p className="text-white">{item.source}</p></div>
          <div><p className="text-xs text-slate-400">Collected</p><p className="text-white">{item.collected_at ? new Date(item.collected_at).toLocaleString() : 'N/A'}</p></div>
          <div><p className="text-xs text-slate-400">Size</p><p className="text-white">{(item.size_bytes / 1024).toFixed(1)} KB</p></div>
        </div>
        <p className="text-sm text-slate-400 mb-2">{item.description}</p>
        {item.content_hash && (
          <div className="p-2 bg-slate-700 rounded"><p className="text-xs text-slate-400">Content Hash</p><p className="text-xs text-white font-mono">{item.content_hash}</p></div>
        )}
        <Button variant="ghost" className="w-full mt-4 text-slate-400" onClick={onClose}>Close</Button>
      </div>
    </div>
  );
}

function ChainOfCustodyCard({ evidenceId }: { evidenceId: string }) {
  const [chain, setChain] = useState<any[]>([]);
  useEffect(() => {
    apiClient.get(`/api/v1/compliance/evidence/${evidenceId}/custody`).then(setChain).catch(() => setChain([]));
  }, [evidenceId]);
  if (chain.length === 0) return null;
  return (
    <Card><CardHeader><CardTitle className="flex items-center gap-2"><Hash className="h-4 w-4 text-blue-400" /> Chain of Custody</CardTitle></CardHeader>
      <CardContent><div className="space-y-2">{chain.map((event: any, i: number) => (
        <div key={i} className="flex items-start gap-2 p-2 bg-slate-800 rounded">
          <div className="w-2 h-2 mt-1.5 rounded-full bg-blue-400 shrink-0" />
          <div><p className="text-sm text-white capitalize">{event.event?.replace(/_/g, ' ')}</p><p className="text-xs text-slate-400">{event.timestamp?.slice(0, 19)} - {event.detail}</p></div>
        </div>
      ))}</div></CardContent></Card>
  );
}

function CollectEvidenceForm({ onCreated }: { onCreated: () => void }) {
  const [controlId, setControlId] = useState('');
  const [framework, setFramework] = useState('SOC_2');
  const [type, setType] = useState('config_snapshot');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (!controlId) { toast.error('Control ID required'); return; }
    setSubmitting(true);
    try {
      await apiClient.post('/api/v1/compliance/evidence/collect', { control_id: controlId, framework, evidence_type: type, description: `Manual collection for ${controlId}`, source: 'manual', content: JSON.stringify({ collected_at: new Date().toISOString() }) });
      toast.success('Evidence collected');
      onCreated();
    } catch { toast.error('Collection failed'); }
    setSubmitting(false);
  };

  return (
    <Card><CardHeader><CardTitle className="flex items-center gap-2"><PlusCircle className="h-4 w-4 text-green-400" /> Collect Evidence</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        <Input className="bg-slate-800 border-slate-700 text-white" placeholder="Control ID" value={controlId} onChange={(e) => setControlId(e.target.value)} />
        <select className="w-full bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-sm text-white" value={framework} onChange={(e) => setFramework(e.target.value)}>
          <option value="SOC_2">SOC 2</option><option value="HIPAA">HIPAA</option><option value="PCI_DSS">PCI DSS</option><option value="GDPR">GDPR</option><option value="ISO_27001">ISO 27001</option>
        </select>
        <select className="w-full bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-sm text-white" value={type} onChange={(e) => setType(e.target.value)}>
          <option value="config_snapshot">Config Snapshot</option><option value="policy_decision">Policy Decision</option><option value="access_log">Access Log</option><option value="scan_result">Scan Result</option><option value="certification">Certification</option>
        </select>
        <Button onClick={handleSubmit} disabled={submitting} className="bg-blue-600 hover:bg-blue-700 w-full">Collect</Button>
      </CardContent></Card>
  );
}

export default function EvidenceCollectionPage() {
  const [evidence, setEvidence] = useState<any[]>([]);
  const [packages, setPackages] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [tab, setTab] = useState<'evidence' | 'packages'>('evidence');
  const [query, setQuery] = useState('');
  const [filterType, setFilterType] = useState('');
  const [selectedEvidence, setSelectedEvidence] = useState<string | null>(null);
  const [showCollect, setShowCollect] = useState(false);

  const fetchData = useCallback(() => {
    apiClient.get('/api/v1/compliance/evidence').then(setEvidence).catch(() => {});
    apiClient.get('/api/v1/compliance/evidence/packages').then(setPackages).catch(() => {});
    apiClient.get('/api/v1/compliance/evidence/stats').then(setStats).catch(() => {});
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const filteredEvidence = evidence.filter((e: any) => {
    if (query && !e.description?.toLowerCase().includes(query.toLowerCase()) && !e.control_id?.toLowerCase().includes(query.toLowerCase())) return false;
    if (filterType && e.evidence_type !== filterType) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div><h1 className="text-3xl font-bold text-white mb-2">Evidence Collection</h1><p className="text-slate-400">Collect, package, and manage compliance evidence for audits</p></div>
        <div className="flex gap-2">
          <Button onClick={fetchData} variant="outline" className="text-slate-400"><RefreshCw className="mr-2 h-4 w-4" /> Refresh</Button>
          <Button onClick={() => setShowCollect(!showCollect)} className="bg-blue-600 hover:bg-blue-700"><PlusCircle className="mr-2 h-4 w-4" /> Collect</Button>
        </div>
      </div>
      {stats && (
        <div className="grid grid-cols-4 gap-4">
          <Card><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Total Items</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-white">{stats.total_evidence}</div></CardContent></Card>
          <Card><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Active</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-green-400">{stats.active_evidence}</div></CardContent></Card>
          <Card><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Packages</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-white">{stats.total_packages}</div></CardContent></Card>
          <Card><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Controls Covered</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-white">{stats.unique_controls_covered}</div></CardContent></Card>
        </div>
      )}
      <div className="flex space-x-2 border-b border-slate-700 pb-2">
        <Button variant={tab === 'evidence' ? 'default' : 'ghost'} onClick={() => setTab('evidence')}><FileText className="mr-2 h-4 w-4" /> Evidence Items</Button>
        <Button variant={tab === 'packages' ? 'default' : 'ghost'} onClick={() => setTab('packages')}><Archive className="mr-2 h-4 w-4" /> Evidence Packages</Button>
      </div>
      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2">
          {tab === 'evidence' && (
            <Card><CardHeader><CardTitle>Evidence Items ({filteredEvidence.length})</CardTitle></CardHeader>
              <CardContent>
                <div className="flex gap-3 items-center mb-4">
                  <div className="relative flex-1"><Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                    <Input className="pl-9 bg-slate-800 border-slate-700 text-white" placeholder="Search evidence..." value={query} onChange={(e) => setQuery(e.target.value)} /></div>
                  <select className="bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-sm text-white" value={filterType} onChange={(e) => setFilterType(e.target.value)}>
                    <option value="">All Types</option><option value="config_snapshot">Config</option><option value="policy_decision">Policy</option><option value="access_log">Access</option><option value="scan_result">Scan</option><option value="certification">Cert</option>
                  </select>
                </div>
                <Table><TableHeader><TableRow><TableHead className="text-slate-400">ID</TableHead><TableHead className="text-slate-400">Type</TableHead><TableHead className="text-slate-400">Control</TableHead><TableHead className="text-slate-400">Source</TableHead><TableHead className="text-slate-400">Status</TableHead><TableHead className="text-slate-400">Actions</TableHead></TableRow></TableHeader>
                  <TableBody>{filteredEvidence.slice(0, 50).map((e: any) => (
                    <TableRow key={e.evidence_id}>
                      <TableCell className="font-mono text-xs text-white">{e.evidence_id}</TableCell>
                      <TableCell><Badge variant="outline">{e.evidence_type}</Badge></TableCell>
                      <TableCell className="text-white">{e.control_id}</TableCell>
                      <TableCell className="text-slate-400 text-sm">{e.source}</TableCell>
                      <TableCell><EvidenceStatusBadge status={e.status} /></TableCell>
                      <TableCell><Button size="sm" variant="ghost" onClick={() => setSelectedEvidence(e.evidence_id)}><Eye className="h-4 w-4" /></Button></TableCell>
                    </TableRow>
                  ))}</TableBody></Table>
              </CardContent></Card>
          )}
          {tab === 'packages' && (
            <Card><CardHeader><CardTitle>Evidence Packages ({packages.length})</CardTitle></CardHeader>
              <CardContent>
                <Table><TableHeader><TableRow><TableHead className="text-slate-400">ID</TableHead><TableHead className="text-slate-400">Name</TableHead><TableHead className="text-slate-400">Framework</TableHead><TableHead className="text-slate-400">Items</TableHead><TableHead className="text-slate-400">Status</TableHead><TableHead className="text-slate-400">Actions</TableHead></TableRow></TableHeader>
                  <TableBody>{packages.map((p: any) => (
                    <TableRow key={p.package_id}>
                      <TableCell className="font-mono text-xs text-white">{p.package_id}</TableCell>
                      <TableCell className="text-white">{p.name}</TableCell>
                      <TableCell><Badge variant="outline">{p.framework}</Badge></TableCell>
                      <TableCell className="text-white">{p.evidence_count || p.evidence_items?.length || 0}</TableCell>
                      <TableCell><EvidenceStatusBadge status={p.status} /></TableCell>
                      <TableCell><Button size="sm" variant="ghost"><Download className="h-4 w-4" /></Button></TableCell>
                    </TableRow>
                  ))}</TableBody></Table>
              </CardContent></Card>
          )}
        </div>
        <div className="space-y-4">
          {showCollect && <CollectEvidenceForm onCreated={fetchData} />}
          {selectedEvidence && <ChainOfCustodyCard evidenceId={selectedEvidence} />}
        </div>
      </div>
      {selectedEvidence && <EvidenceDetailModal evidenceId={selectedEvidence} onClose={() => setSelectedEvidence(null)} />}
    </div>
  );
}
import React from "react";

interface evidence_collectionAction {
  id: string;
  type: string;
  status: string;
  ts: string;
}

const evidence_collectionActions: React.FC<{}> = () => {
  const [items, setItems] = React.useState<evidence_collectionAction[]>([]);
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
      <h2 className="text-xl font-bold mb-4">evidence_collection Actions</h2>
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
export default evidence_collectionActions;
