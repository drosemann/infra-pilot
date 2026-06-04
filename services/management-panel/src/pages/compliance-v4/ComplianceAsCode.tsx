import { useState, useEffect, useCallback } from 'react';
import { toast } from 'sonner';
import { apiClient } from '../../lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Code, BarChart3, Search, Filter, Shield, CheckCircle, XCircle, RefreshCw, PlusCircle, Play, FileText, AlertTriangle, TrendingUp, Layers, GitBranch } from 'lucide-react';

function SeverityBadge({ severity }: { severity: string }) {
  const colors: Record<string, string> = { critical: 'bg-red-600', high: 'bg-orange-600', medium: 'bg-yellow-600', low: 'bg-green-600', info: 'bg-blue-600' };
  return <Badge className={colors[severity] || 'bg-slate-600'}>{severity}</Badge>;
}

function ControlDetailModal({ controlId, onClose }: { controlId: string; onClose: () => void }) {
  const [control, setControl] = useState<any>(null);
  useEffect(() => {
    apiClient.get(`/api/v1/compliance/cac/controls/${controlId}`).then(setControl).catch(() => setControl(null));
  }, [controlId]);
  if (!control) return null;
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-slate-800 rounded-lg p-6 w-[600px] max-h-[80vh] overflow-y-auto border border-slate-700" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-start justify-between mb-4">
          <div><h3 className="text-lg font-bold text-white">{control.name}</h3><p className="text-sm text-slate-400">{control.control_id}</p></div>
          <SeverityBadge severity={control.severity} />
        </div>
        <div className="grid grid-cols-2 gap-3 mb-4">
          <div><p className="text-xs text-slate-400">Framework</p><Badge variant="outline">{control.framework}</Badge></div>
          <div><p className="text-xs text-slate-400">Status</p><Badge className={control.status === 'active' ? 'bg-green-600' : control.status === 'draft' ? 'bg-yellow-600' : 'bg-slate-600'}>{control.status}</Badge></div>
          <div><p className="text-xs text-slate-400">Version</p><p className="text-white">{control.version}</p></div>
          <div><p className="text-xs text-slate-400">Rules</p><p className="text-white">{control.rules?.length || 0}</p></div>
        </div>
        <p className="text-sm text-slate-400 mb-2">{control.description}</p>
        {control.rules?.length > 0 && (
          <div><p className="text-sm text-slate-400 mb-2">Rules</p>{control.rules.slice(0, 3).map((rule: any, i: number) => (
            <div key={i} className="p-2 bg-slate-700 rounded mb-2">
              <p className="text-xs text-white font-mono">{rule.name}</p>
              <pre className="text-xs text-slate-400 mt-1 whitespace-pre-wrap">{rule.rego_expression?.slice(0, 200)}...</pre>
            </div>
          ))}</div>
        )}
        <Button variant="ghost" className="w-full mt-4 text-slate-400" onClick={onClose}>Close</Button>
      </div>
    </div>
  );
}

function EvaluateForm({ onEvaluated }: { onEvaluated: () => void }) {
  const [controlId, setControlId] = useState('');
  const [inputJson, setInputJson] = useState('{\n  "resource_type": "database",\n  "encryption_at_rest": false\n}');
  const [result, setResult] = useState<any>(null);
  const [evaluating, setEvaluating] = useState(false);

  const handleEvaluate = async () => {
    if (!controlId) { toast.error('Control ID required'); return; }
    setEvaluating(true);
    try {
      let inputData;
      try { inputData = JSON.parse(inputJson); } catch { toast.error('Invalid JSON'); setEvaluating(false); return; }
      const res = await apiClient.post(`/api/v1/compliance/cac/evaluate`, { control_id: controlId, input_data: inputData });
      setResult(res);
      onEvaluated();
    } catch { toast.error('Evaluation failed'); }
    setEvaluating(false);
  };

  return (
    <Card><CardHeader><CardTitle className="flex items-center gap-2"><Play className="h-4 w-4 text-green-400" /> Evaluate Policy</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        <Input className="bg-slate-800 border-slate-700 text-white font-mono text-sm" placeholder="Control ID (e.g., SOC2-CC5)" value={controlId} onChange={(e) => setControlId(e.target.value)} />
        <Textarea className="bg-slate-800 border-slate-700 text-white font-mono text-sm" rows={5} value={inputJson} onChange={(e) => setInputJson(e.target.value)} />
        <Button onClick={handleEvaluate} disabled={evaluating} className="bg-blue-600 hover:bg-blue-700 w-full">Evaluate</Button>
        {result && (
          <div className={`p-3 rounded ${result.status === 'compliant' ? 'bg-green-900/20 border border-green-800' : 'bg-red-900/20 border border-red-800'}`}>
            <p className="text-sm text-white flex items-center gap-2">{result.status === 'compliant' ? <CheckCircle className="h-4 w-4 text-green-400" /> : <XCircle className="h-4 w-4 text-red-400" />} {result.status.toUpperCase()} - {result.violation_count} violations</p>
          </div>
        )}
      </CardContent></Card>
  );
}

function PolicyTemplateCard({ templates }: { templates: Record<string, string> }) {
  return (
    <Card><CardHeader><CardTitle className="flex items-center gap-2"><FileText className="h-4 w-4 text-blue-400" /> Policy Templates</CardTitle></CardHeader>
      <CardContent><div className="grid grid-cols-2 gap-3">
        {Object.entries(templates).map(([name, content]) => (
          <div key={name} className="p-3 bg-slate-800 rounded border border-slate-700">
            <p className="text-sm text-white font-medium capitalize mb-1">{name.replace(/_/g, ' ')}</p>
            <pre className="text-xs text-slate-400 truncate">{content.slice(0, 80)}...</pre>
          </div>
        ))}
      </div></CardContent></Card>
  );
}

function GapAnalysisCard({ gap }: { gap: any }) {
  if (!gap) return null;
  return (
    <Card><CardHeader><CardTitle className="flex items-center gap-2"><AlertTriangle className="h-4 w-4 text-yellow-400" /> Gap Analysis</CardTitle></CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div className="flex items-center justify-between"><span className="text-sm text-slate-400">Coverage</span><span className="text-white font-bold">{gap.policy_coverage}%</span></div>
          <div className="flex items-center justify-between"><span className="text-sm text-slate-400">Active</span><span className="text-green-400">{gap.active}</span></div>
          <div className="flex items-center justify-between"><span className="text-sm text-slate-400">Draft</span><span className="text-yellow-400">{gap.draft}</span></div>
          <div className="flex items-center justify-between"><span className="text-sm text-slate-400">Deprecated</span><span className="text-slate-400">{gap.deprecated}</span></div>
        </div>
        {gap.recommendations?.map((r: string, i: number) => (
          <p key={i} className="text-xs text-slate-400 mt-2">{r}</p>
        ))}
      </CardContent></Card>
  );
}

export default function ComplianceAsCodePage() {
  const [controls, setControls] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [templates, setTemplates] = useState<Record<string, string>>({});
  const [gap, setGap] = useState<any>(null);
  const [tab, setTab] = useState<'controls' | 'evaluate' | 'templates'>('controls');
  const [query, setQuery] = useState('');
  const [filterFramework, setFilterFramework] = useState('');
  const [selectedControl, setSelectedControl] = useState<string | null>(null);

  const fetchData = useCallback(() => {
    apiClient.get('/api/v1/compliance/cac/controls').then(r => setControls(r.controls || r || [])).catch(() => {});
    apiClient.get('/api/v1/compliance/cac/stats').then(setStats).catch(() => {});
    apiClient.get('/api/v1/compliance/cac/templates').then(setTemplates).catch(() => {});
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const fetchGap = async (fw: string) => {
    try {
      const res = await apiClient.get(`/api/v1/compliance/cac/gap/${fw}`);
      setGap(res);
    } catch { toast.error('Failed to load gap analysis'); }
  };

  const filtered = controls.filter((c: any) => {
    if (query && !c.name?.toLowerCase().includes(query.toLowerCase()) && !c.control_id?.toLowerCase().includes(query.toLowerCase())) return false;
    if (filterFramework && c.framework !== filterFramework) return false;
    return true;
  });

  const handleStatusUpdate = async (controlId: string, status: string) => {
    try {
      await apiClient.put(`/api/v1/compliance/cac/controls/${controlId}/status`, { status });
      toast.success(`Control ${status}`);
      fetchData();
    } catch { toast.error('Status update failed'); }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div><h1 className="text-3xl font-bold text-white mb-2">Compliance as Code</h1><p className="text-slate-400">Policy-as-code with OPA/Rego integration and continuous evaluation</p></div>
        <div className="flex gap-2">
          <Button onClick={fetchData} variant="outline" className="text-slate-400"><RefreshCw className="mr-2 h-4 w-4" /> Refresh</Button>
        </div>
      </div>
      {stats && (
        <div className="grid grid-cols-4 gap-4">
          <Card><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Controls</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-white">{stats.total_controls}</div></CardContent></Card>
          <Card><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Rules</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-white">{stats.total_rules}</div></CardContent></Card>
          <Card><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Evaluations</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-white">{stats.recent_evaluations}</div></CardContent></Card>
          <Card><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Versioned</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-white">{stats.versioned_policies}</div></CardContent></Card>
        </div>
      )}
      <div className="flex space-x-2 border-b border-slate-700 pb-2">
        <Button variant={tab === 'controls' ? 'default' : 'ghost'} onClick={() => setTab('controls')}><Shield className="mr-2 h-4 w-4" /> Controls</Button>
        <Button variant={tab === 'evaluate' ? 'default' : 'ghost'} onClick={() => setTab('evaluate')}><BarChart3 className="mr-2 h-4 w-4" /> Evaluate</Button>
        <Button variant={tab === 'templates' ? 'default' : 'ghost'} onClick={() => setTab('templates')}><Code className="mr-2 h-4 w-4" /> Templates</Button>
      </div>
      {tab === 'controls' && (
        <div className="grid grid-cols-3 gap-6">
          <div className="col-span-2">
            <Card><CardHeader><CardTitle>Compliance Controls ({filtered.length})</CardTitle></CardHeader>
              <CardContent>
                <div className="flex gap-3 items-center mb-4">
                  <div className="relative flex-1"><Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                    <Input className="pl-9 bg-slate-800 border-slate-700 text-white" placeholder="Search controls..." value={query} onChange={(e) => setQuery(e.target.value)} /></div>
                  <select className="bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-sm text-white" value={filterFramework} onChange={(e) => { setFilterFramework(e.target.value); if (e.target.value) fetchGap(e.target.value); }}>
                    <option value="">All Frameworks</option><option value="SOC_2">SOC 2</option><option value="HIPAA">HIPAA</option><option value="PCI_DSS">PCI DSS</option><option value="GDPR">GDPR</option><option value="ISO_27001">ISO 27001</option>
                  </select>
                </div>
                <Table><TableHeader><TableRow><TableHead className="text-slate-400">ID</TableHead><TableHead className="text-slate-400">Name</TableHead><TableHead className="text-slate-400">Framework</TableHead><TableHead className="text-slate-400">Severity</TableHead><TableHead className="text-slate-400">Status</TableHead><TableHead className="text-slate-400">Actions</TableHead></TableRow></TableHeader>
                  <TableBody>{filtered.map((c: any) => (
                    <TableRow key={c.control_id}>
                      <TableCell className="font-mono text-xs text-white cursor-pointer hover:text-blue-400" onClick={() => setSelectedControl(c.control_id)}>{c.control_id}</TableCell>
                      <TableCell className="text-white">{c.name}</TableCell>
                      <TableCell><Badge variant="outline">{c.framework}</Badge></TableCell>
                      <TableCell><SeverityBadge severity={c.severity} /></TableCell>
                      <TableCell><Badge className={c.status === 'active' ? 'bg-green-600' : c.status === 'draft' ? 'bg-yellow-600' : 'bg-slate-600'}>{c.status}</Badge></TableCell>
                      <TableCell><div className="flex gap-1">
                        <Button size="sm" variant="ghost" onClick={() => handleStatusUpdate(c.control_id, 'active')}><CheckCircle className="h-4 w-4 text-green-400" /></Button>
                        <Button size="sm" variant="ghost" onClick={() => handleStatusUpdate(c.control_id, 'inactive')}><XCircle className="h-4 w-4 text-red-400" /></Button>
                      </div></TableCell>
                    </TableRow>
                  ))}</TableBody></Table>
              </CardContent></Card>
          </div>
          <div className="space-y-4">
            {filterFramework && gap && <GapAnalysisCard gap={gap} />}
          </div>
        </div>
      )}
      {tab === 'evaluate' && (
        <div className="grid grid-cols-2 gap-6">
          <EvaluateForm onEvaluated={fetchData} />
          <Card><CardHeader><CardTitle>Recent Evaluations</CardTitle></CardHeader>
            <CardContent>
              <p className="text-slate-400 text-sm">Run evaluations to see results here. Use the Evaluate form to test controls against input data.</p>
            </CardContent></Card>
        </div>
      )}
      {tab === 'templates' && Object.keys(templates).length > 0 && <PolicyTemplateCard templates={templates} />}
      {selectedControl && <ControlDetailModal controlId={selectedControl} onClose={() => setSelectedControl(null)} />}
    </div>
  );
}
import React from "react";

interface compliance_as_codeAction {
  id: string;
  type: string;
  status: string;
  ts: string;
}

const compliance_as_codeActions: React.FC<{}> = () => {
  const [items, setItems] = React.useState<compliance_as_codeAction[]>([]);
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
      <h2 className="text-xl font-bold mb-4">compliance_as_code Actions</h2>
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
export default compliance_as_codeActions;
