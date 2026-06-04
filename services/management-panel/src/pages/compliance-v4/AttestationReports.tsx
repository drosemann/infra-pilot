import { useState, useEffect, useCallback } from 'react';
import { toast } from 'sonner';
import { apiClient } from '../../lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { FileText, Download, CheckCircle, XCircle, Search, Filter, Clock, Shield, RefreshCw, PlusCircle, FileSignature, Eye, ArrowUpDown, AlertTriangle, BarChart3, Calendar } from 'lucide-react';

function ReportStatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = { compliant: 'bg-green-600', non_compliant: 'bg-red-600', generated: 'bg-blue-600', approved: 'bg-green-600', rejected: 'bg-red-600', draft: 'bg-yellow-600' };
  return <Badge className={colors[status] || 'bg-slate-600'}>{status}</Badge>;
}

function ReportDetailModal({ reportId, onClose }: { reportId: string; onClose: () => void }) {
  const [report, setReport] = useState<any>(null);
  useEffect(() => {
    apiClient.get(`/api/v1/compliance/attestation/reports/${reportId}`).then(setReport).catch(() => setReport(null));
  }, [reportId]);
  if (!report) return null;
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-slate-800 rounded-lg p-6 w-[600px] max-h-[80vh] overflow-y-auto border border-slate-700" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-start justify-between mb-4">
          <div><h3 className="text-lg font-bold text-white">{report.title}</h3><p className="text-sm text-slate-400">{report.framework} - {report.organization}</p></div>
          <ReportStatusBadge status={report.overall_status} />
        </div>
        <div className="grid grid-cols-2 gap-3 mb-4">
          <div><p className="text-xs text-slate-400">Type</p><p className="text-white">{report.report_type}</p></div>
          <div><p className="text-xs text-slate-400">Version</p><p className="text-white">{report.version}</p></div>
          <div><p className="text-xs text-slate-400">Period</p><p className="text-white">{report.period_start?.slice(0, 10)} to {report.period_end?.slice(0, 10)}</p></div>
          <div><p className="text-xs text-slate-400">Generated</p><p className="text-white">{new Date(report.generated_at).toLocaleDateString()}</p></div>
        </div>
        {report.control_mappings && (
          <div><p className="text-xs text-slate-400 mb-2">Controls ({report.control_mappings.length})</p>
            <Table><TableHeader><TableRow><TableHead className="text-slate-400">ID</TableHead><TableHead className="text-slate-400">Status</TableHead></TableRow></TableHeader>
              <TableBody>{report.control_mappings.slice(0, 10).map((m: any, i: number) => (
                <TableRow key={i}><TableCell className="text-white text-sm">{m.control_id}</TableCell><TableCell><Badge className={m.status === 'compliant' ? 'bg-green-600' : 'bg-red-600'}>{m.status}</Badge></TableCell></TableRow>
              ))}</TableBody></Table>
          </div>
        )}
        <Button variant="ghost" className="w-full mt-4 text-slate-400" onClick={onClose}>Close</Button>
      </div>
    </div>
  );
}

function GenerateReportForm({ onCreated }: { onCreated: () => void }) {
  const [reportType, setReportType] = useState('SOC_2_TYPE_II');
  const [framework, setFramework] = useState('SOC_2');
  const [organization, setOrganization] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (!organization) { toast.error('Organization is required'); return; }
    setSubmitting(true);
    try {
      await apiClient.post('/api/v1/compliance/attestation/generate', { report_type: reportType, framework, organization });
      toast.success('Report generated');
      onCreated();
    } catch { toast.error('Generation failed'); }
    setSubmitting(false);
  };

  return (
    <Card><CardHeader><CardTitle className="flex items-center gap-2"><PlusCircle className="h-4 w-4 text-green-400" /> Generate Report</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        <select className="w-full bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-sm text-white" value={reportType} onChange={(e) => setReportType(e.target.value)}>
          <option value="SOC_2_TYPE_II">SOC 2 Type II</option><option value="HIPAA">HIPAA</option><option value="PCI_DSS">PCI DSS v4.0</option>
        </select>
        <select className="w-full bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-sm text-white" value={framework} onChange={(e) => setFramework(e.target.value)}>
          <option value="SOC_2">SOC 2</option><option value="HIPAA">HIPAA</option><option value="PCI_DSS">PCI DSS</option><option value="ISO_27001">ISO 27001</option><option value="GDPR">GDPR</option>
        </select>
        <Input className="bg-slate-800 border-slate-700 text-white" placeholder="Organization name" value={organization} onChange={(e) => setOrganization(e.target.value)} />
        <Button onClick={handleSubmit} disabled={submitting} className="bg-blue-600 hover:bg-blue-700 w-full">Generate</Button>
      </CardContent></Card>
  );
}

function CoverageCard({ report }: { report: any }) {
  if (!report) return null;
  return (
    <Card><CardHeader><CardTitle className="flex items-center gap-2"><Shield className="h-4 w-4 text-blue-400" /> Coverage</CardTitle></CardHeader>
      <CardContent><div className="space-y-3">
        <div className="flex items-center justify-between"><span className="text-sm text-slate-400">Total Reports</span><span className="text-white font-bold">{report.total_reports}</span></div>
        <div className="flex items-center justify-between"><span className="text-sm text-slate-400">Compliant</span><span className="text-green-400 font-bold">{report.compliant_reports}</span></div>
        <div className="flex items-center justify-between"><span className="text-sm text-slate-400">By Framework</span><span className="text-white font-bold">{Object.keys(report.by_framework || {}).length}</span></div>
        <div><p className="text-sm text-slate-400 mb-2">By Type</p>{Object.entries(report.by_type || {}).map(([k, v]: [string, any]) => (
          <div key={k} className="flex items-center justify-between text-sm"><span className="text-slate-400">{k}</span><span className="text-white">{v}</span></div>
        ))}</div>
      </div></CardContent></Card>
  );
}

export default function AttestationReportsPage() {
  const [reports, setReports] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [coverage, setCoverage] = useState<any>(null);
  const [query, setQuery] = useState('');
  const [filterType, setFilterType] = useState('');
  const [selectedReport, setSelectedReport] = useState<string | null>(null);
  const [showGenerate, setShowGenerate] = useState(false);
  const [tab, setTab] = useState<'reports' | 'compare' | 'coverage' | 'schedule'>('reports');

  const fetchData = useCallback(() => {
    apiClient.get('/api/v1/compliance/attestation/reports').then(setReports).catch(() => {});
    apiClient.get('/api/v1/compliance/attestation/stats').then(setStats).catch(() => {});
    apiClient.get('/api/v1/compliance/attestation/coverage').then(setCoverage).catch(() => {});
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const filtered = reports.filter((r: any) => {
    if (query && !r.title?.toLowerCase().includes(query.toLowerCase()) && !r.framework?.toLowerCase().includes(query.toLowerCase()) && !r.organization?.toLowerCase().includes(query.toLowerCase())) return false;
    if (filterType && r.report_type !== filterType) return false;
    return true;
  });

  const handleApprove = async (reportId: string) => {
    try {
      await apiClient.post(`/api/v1/compliance/attestation/reports/${reportId}/approve`, { approver: 'admin' });
      toast.success('Report approved');
      fetchData();
    } catch { toast.error('Approval failed'); }
  };

  const handleVerify = async (reportId: string) => {
    try {
      const result = await apiClient.get(`/api/v1/compliance/attestation/reports/${reportId}/verify`);
      toast.success(result.verified ? 'Signature verified' : 'Signature invalid');
    } catch { toast.error('Verification failed'); }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div><h1 className="text-3xl font-bold text-white mb-2">Attestation Reports</h1><p className="text-slate-400">Generate and manage compliance attestation reports across frameworks</p></div>
        <div className="flex gap-2">
          <Button onClick={fetchData} variant="outline" className="text-slate-400"><RefreshCw className="mr-2 h-4 w-4" /> Refresh</Button>
          <Button onClick={() => setShowGenerate(!showGenerate)} className="bg-blue-600 hover:bg-blue-700"><PlusCircle className="mr-2 h-4 w-4" /> Generate</Button>
        </div>
      </div>
      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2 space-y-4">
          <Card><CardHeader><CardTitle>Attestation Reports ({filtered.length})</CardTitle></CardHeader>
            <CardContent>
              <div className="flex gap-3 items-center mb-4">
                <div className="relative flex-1"><Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                  <Input className="pl-9 bg-slate-800 border-slate-700 text-white" placeholder="Search reports..." value={query} onChange={(e) => setQuery(e.target.value)} /></div>
                <select className="bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-sm text-white" value={filterType} onChange={(e) => setFilterType(e.target.value)}>
                  <option value="">All Types</option><option value="SOC_2_TYPE_II">SOC 2</option><option value="HIPAA">HIPAA</option><option value="PCI_DSS">PCI DSS</option>
                </select>
              </div>
              <Table><TableHeader><TableRow><TableHead className="text-slate-400">ID</TableHead><TableHead className="text-slate-400">Framework</TableHead><TableHead className="text-slate-400">Period</TableHead><TableHead className="text-slate-400">Status</TableHead><TableHead className="text-slate-400">Actions</TableHead></TableRow></TableHeader>
                <TableBody>{filtered.map((r: any) => (
                  <TableRow key={r.report_id}>
                    <TableCell className="font-mono text-xs text-white">{r.report_id}</TableCell>
                    <TableCell><Badge variant="outline">{r.framework}</Badge></TableCell>
                    <TableCell className="text-white text-sm">{r.period_start?.slice(0, 10)} to {r.period_end?.slice(0, 10)}</TableCell>
                    <TableCell><ReportStatusBadge status={r.overall_status || r.status} /></TableCell>
                    <TableCell><div className="flex gap-1">
                      <Button size="sm" variant="ghost" onClick={() => setSelectedReport(r.report_id)}><Eye className="h-4 w-4" /></Button>
                      <Button size="sm" variant="ghost" onClick={() => handleApprove(r.report_id)}><FileSignature className="h-4 w-4 text-green-400" /></Button>
                      <Button size="sm" variant="ghost" onClick={() => handleVerify(r.report_id)}><CheckCircle className="h-4 w-4 text-blue-400" /></Button>
                    </div></TableCell>
                  </TableRow>
                ))}</TableBody></Table>
            </CardContent></Card>
        </div>
        <div className="space-y-4">
          {stats && <CoverageCard report={stats} />}
          {showGenerate && <GenerateReportForm onCreated={fetchData} />}
        </div>
      </div>
      {selectedReport && <ReportDetailModal reportId={selectedReport} onClose={() => setSelectedReport(null)} />}
      <div className="flex space-x-2 border-b border-slate-700 pb-2">
        <Button variant={tab === 'reports' ? 'default' : 'ghost'} onClick={() => setTab('reports')}><FileText className="mr-2 h-4 w-4" /> Reports</Button>
        <Button variant={tab === 'compare' ? 'default' : 'ghost'} onClick={() => setTab('compare')}><BarChart3 className="mr-2 h-4 w-4" /> Compare</Button>
        <Button variant={tab === 'coverage' ? 'default' : 'ghost'} onClick={() => setTab('coverage')}><Shield className="mr-2 h-4 w-4" /> Coverage</Button>
        <Button variant={tab === 'schedule' ? 'default' : 'ghost'} onClick={() => setTab('schedule')}><Calendar className="mr-2 h-4 w-4" /> Schedule</Button>
      </div>
      {tab === 'compare' && (
        <Card><CardHeader><CardTitle className="flex items-center gap-2"><BarChart3 className="h-4 w-4 text-blue-400" /> Report Comparison</CardTitle></CardHeader>
          <CardContent>
            <div className="flex gap-3 items-center mb-4">
              <select className="bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-sm text-white flex-1"><option value="">Select first report...</option>{reports.map(r => <option key={r.report_id} value={r.report_id}>{r.report_id}</option>)}</select>
              <select className="bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-sm text-white flex-1"><option value="">Select second report...</option>{reports.map(r => <option key={r.report_id} value={r.report_id}>{r.report_id}</option>)}</select>
              <Button className="bg-blue-600 hover:bg-blue-700"><BarChart3 className="mr-2 h-4 w-4" /> Compare</Button>
            </div>
            <p className="text-sm text-slate-400">Select two reports to compare their findings, scope, and status side by side.</p>
          </CardContent></Card>
      )}
      {tab === 'coverage' && coverage && (
        <Card><CardHeader><CardTitle className="flex items-center gap-2"><Shield className="h-4 w-4 text-green-400" /> Coverage Overview</CardTitle></CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4 mb-4">
              <div className="p-3 bg-slate-800 rounded"><p className="text-xs text-slate-400">Total Controls</p><p className="text-xl font-bold text-white">{coverage.total_controls || 0}</p></div>
              <div className="p-3 bg-slate-800 rounded"><p className="text-xs text-slate-400">Covered</p><p className="text-xl font-bold text-green-400">{coverage.covered_controls || 0}</p></div>
              <div className="p-3 bg-slate-800 rounded"><p className="text-xs text-slate-400">Gap</p><p className="text-xl font-bold text-red-400">{coverage.gap_controls || 0}</p></div>
            </div>
            {coverage.by_framework && Object.entries(coverage.by_framework).map(([fw, info]: [string, any]) => (
              <div key={fw} className="flex items-center justify-between p-2 bg-slate-800 rounded mb-2">
                <span className="text-white text-sm">{fw}</span><span className="text-slate-400 text-sm">{info.covered}/{info.total} ({info.percentage}%)</span>
              </div>
            ))}
          </CardContent></Card>
      )}
      {tab === 'schedule' && <GenerateReportForm onCreated={fetchData} />}
    </div>
  );
}
import React from "react";

interface attestation_reportsAction {
  id: string;
  type: string;
  status: string;
  ts: string;
}

const attestation_reportsActions: React.FC<{}> = () => {
  const [items, setItems] = React.useState<attestation_reportsAction[]>([]);
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
      <h2 className="text-xl font-bold mb-4">attestation_reports Actions</h2>
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
export default attestation_reportsActions;
