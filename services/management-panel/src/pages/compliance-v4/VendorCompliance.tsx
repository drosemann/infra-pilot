import { useState, useEffect, useCallback } from 'react';
import { toast } from 'sonner';
import { apiClient } from '../../lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Shield, Users, AlertTriangle, CheckCircle, XCircle, Search, Filter, TrendingUp, Star, RefreshCw, PlusCircle, Activity, ArrowUpDown, ExternalLink } from 'lucide-react';

function RiskBadge({ tier }: { tier: string }) {
  const colors: Record<string, string> = { critical: 'bg-red-600', high: 'bg-orange-600', medium: 'bg-yellow-600', low: 'bg-green-600' };
  return <Badge className={colors[tier] || 'bg-slate-600'}>{tier}</Badge>;
}

function VendorScorecardModal({ vendorId, onClose }: { vendorId: string; onClose: () => void }) {
  const [scorecard, setScorecard] = useState<any>(null);
  useEffect(() => {
    apiClient.get(`/api/v1/compliance/vendors/${vendorId}/scorecard`).then(setScorecard).catch(() => setScorecard(null));
  }, [vendorId]);
  if (!scorecard) return null;
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-slate-800 rounded-lg p-6 w-[500px] border border-slate-700" onClick={(e) => e.stopPropagation()}>
        <h3 className="text-lg font-bold text-white mb-4">Scorecard: {scorecard.vendor?.name}</h3>
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div className="p-3 bg-slate-700 rounded"><p className="text-xs text-slate-400">Avg Score</p><p className="text-xl font-bold text-white">{scorecard.average_score ?? 'N/A'}</p></div>
          <div className="p-3 bg-slate-700 rounded"><p className="text-xs text-slate-400">Latest Score</p><p className="text-xl font-bold text-white">{scorecard.latest_score ?? 'N/A'}</p></div>
          <div className="p-3 bg-slate-700 rounded"><p className="text-xs text-slate-400">Findings</p><p className="text-xl font-bold text-white">{scorecard.total_findings}</p></div>
          <div className="p-3 bg-slate-700 rounded"><p className="text-xs text-slate-400">Risk</p><p className="text-xl font-bold text-white capitalize">{scorecard.risk_assessment}</p></div>
        </div>
        <p className="text-sm text-slate-400">Trend: {scorecard.score_trend}</p>
        <Button variant="ghost" className="w-full mt-4 text-slate-400" onClick={onClose}>Close</Button>
      </div>
    </div>
  );
}

function RegisterVendorForm({ onCreated }: { onCreated: () => void }) {
  const [name, setName] = useState('');
  const [domain, setDomain] = useState('');
  const [email, setEmail] = useState('');
  const [tier, setTier] = useState('medium');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (!name || !domain) { toast.error('Name and domain required'); return; }
    setSubmitting(true);
    try {
      await apiClient.post('/api/v1/compliance/vendors/register', { name, domain, contact_email: email, risk_tier: tier });
      toast.success('Vendor registered');
      onCreated();
      setName(''); setDomain(''); setEmail('');
    } catch { toast.error('Registration failed'); }
    setSubmitting(false);
  };

  return (
    <Card><CardHeader><CardTitle className="flex items-center gap-2"><PlusCircle className="h-4 w-4 text-green-400" /> Register Vendor</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        <Input className="bg-slate-800 border-slate-700 text-white" placeholder="Vendor name" value={name} onChange={(e) => setName(e.target.value)} />
        <Input className="bg-slate-800 border-slate-700 text-white" placeholder="Domain" value={domain} onChange={(e) => setDomain(e.target.value)} />
        <Input className="bg-slate-800 border-slate-700 text-white" placeholder="Contact email" value={email} onChange={(e) => setEmail(e.target.value)} />
        <select className="w-full bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-sm text-white" value={tier} onChange={(e) => setTier(e.target.value)}>
          <option value="low">Low Risk</option><option value="medium">Medium Risk</option><option value="high">High Risk</option><option value="critical">Critical Risk</option>
        </select>
        <Button onClick={handleSubmit} disabled={submitting} className="bg-blue-600 hover:bg-blue-700 w-full">Register</Button>
      </CardContent></Card>
  );
}

function RiskDistributionCard({ vendors }: { vendors: any[] }) {
  const distribution: Record<string, number> = {};
  vendors.forEach((v: any) => { const t = v.risk_tier || v.risk_level || 'unknown'; distribution[t] = (distribution[t] || 0) + 1; });
  const tiers = ['critical', 'high', 'medium', 'low'];
  return (
    <Card><CardHeader><CardTitle className="flex items-center gap-2"><Activity className="h-4 w-4 text-blue-400" /> Risk Distribution</CardTitle></CardHeader>
      <CardContent><div className="space-y-2">{tiers.map((tier) => {
        const count = distribution[tier] || 0;
        const total = vendors.length || 1;
        const pct = (count / total) * 100;
        const colors: Record<string, string> = { critical: 'bg-red-600', high: 'bg-orange-600', medium: 'bg-yellow-600', low: 'bg-green-600' };
        return (
          <div key={tier}>
            <div className="flex items-center justify-between text-sm mb-1"><span className="text-slate-400 capitalize">{tier}</span><span className="text-white">{count}</span></div>
            <div className="h-2 bg-slate-700 rounded-full overflow-hidden"><div className={`h-full ${colors[tier]} rounded-full`} style={{ width: `${pct}%` }} /></div>
          </div>
        );
      })}</div></CardContent></Card>
  );
}

function VendorDetailModal({ vendor, onClose, onAssess }: { vendor: any; onClose: () => void; onAssess: (id: string) => void }) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-slate-800 rounded-lg p-6 w-[500px] border border-slate-700" onClick={(e) => e.stopPropagation()}>
        <h3 className="text-lg font-bold text-white mb-2">{vendor.name}</h3>
        <p className="text-sm text-slate-400 mb-4">{vendor.domain}</p>
        <div className="grid grid-cols-2 gap-3 mb-4">
          <div><p className="text-xs text-slate-400">Category</p><p className="text-white">{vendor.category}</p></div>
          <div><p className="text-xs text-slate-400">Risk Tier</p><RiskBadge tier={vendor.risk_tier || vendor.risk_level} /></div>
          <div><p className="text-xs text-slate-400">Risk Score</p><p className="text-white">{vendor.risk_score?.toFixed(1)}</p></div>
          <div><p className="text-xs text-slate-400">Status</p><Badge variant="outline">{vendor.status}</Badge></div>
        </div>
        <Button className="w-full bg-blue-600 hover:bg-blue-700" onClick={() => { onAssess(vendor.vendor_id); onClose(); }}>Run Assessment</Button>
        <Button variant="ghost" className="w-full mt-2 text-slate-400" onClick={onClose}>Close</Button>
      </div>
    </div>
  );
}

export default function VendorCompliancePage() {
  const [vendors, setVendors] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [query, setQuery] = useState('');
  const [filterTier, setFilterTier] = useState('');
  const [selectedVendor, setSelectedVendor] = useState<any>(null);
  const [scorecardVendor, setScorecardVendor] = useState<string | null>(null);
  const [showRegister, setShowRegister] = useState(false);

  const fetchData = useCallback(() => {
    apiClient.get('/api/v1/compliance/vendors').then(setVendors).catch(() => {});
    apiClient.get('/api/v1/compliance/vendors/risk-summary').then(setStats).catch(() => {});
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const filtered = vendors.filter((v: any) => {
    if (query && !v.name?.toLowerCase().includes(query.toLowerCase()) && !v.domain?.toLowerCase().includes(query.toLowerCase())) return false;
    if (filterTier && (v.risk_tier || v.risk_level) !== filterTier) return false;
    return true;
  });

  const handleAssess = async (vendorId: string) => {
    try {
      const result = await apiClient.post(`/api/v1/compliance/vendors/${vendorId}/assess`);
      toast.success(`Assessment created: ${result.assessment_id}`);
      fetchData();
    } catch { toast.error('Assessment failed'); }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div><h1 className="text-3xl font-bold text-white mb-2">Vendor Compliance</h1><p className="text-slate-400">Manage vendor risk assessments and compliance scoring</p></div>
        <div className="flex gap-2">
          <Button onClick={fetchData} variant="outline" className="text-slate-400"><RefreshCw className="mr-2 h-4 w-4" /> Refresh</Button>
          <Button onClick={() => setShowRegister(!showRegister)} className="bg-blue-600 hover:bg-blue-700"><PlusCircle className="mr-2 h-4 w-4" /> Register</Button>
        </div>
      </div>
      {stats && (
        <div className="grid grid-cols-4 gap-4">
          <Card><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Total Vendors</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-white">{stats.total_vendors}</div></CardContent></Card>
          <Card><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Assessed</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-green-400">{stats.assessed}</div></CardContent></Card>
          <Card><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Not Assessed</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-yellow-400">{stats.not_assessed}</div></CardContent></Card>
          <Card><CardHeader className="pb-2"><CardTitle className="text-sm text-slate-400">Avg Risk Score</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-white">{stats.average_risk_score?.toFixed(1)}</div></CardContent></Card>
        </div>
      )}
      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2 space-y-4">
          <Card><CardHeader><CardTitle>Vendors ({filtered.length})</CardTitle></CardHeader>
            <CardContent>
              <div className="flex gap-3 items-center mb-4">
                <div className="relative flex-1"><Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                  <Input className="pl-9 bg-slate-800 border-slate-700 text-white" placeholder="Search vendors..." value={query} onChange={(e) => setQuery(e.target.value)} /></div>
                <select className="bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-sm text-white" value={filterTier} onChange={(e) => setFilterTier(e.target.value)}>
                  <option value="">All Tiers</option><option value="critical">Critical</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option>
                </select>
              </div>
              <Table><TableHeader><TableRow><TableHead className="text-slate-400">Name</TableHead><TableHead className="text-slate-400">Category</TableHead><TableHead className="text-slate-400">Risk</TableHead><TableHead className="text-slate-400">Score</TableHead><TableHead className="text-slate-400">Status</TableHead><TableHead className="text-slate-400">Actions</TableHead></TableRow></TableHeader>
                <TableBody>{filtered.map((v: any) => (
                  <TableRow key={v.vendor_id}>
                    <TableCell className="font-medium text-white cursor-pointer hover:text-blue-400" onClick={() => setSelectedVendor(v)}>{v.name}</TableCell>
                    <TableCell className="text-slate-400">{v.category}</TableCell>
                    <TableCell><RiskBadge tier={v.risk_tier || v.risk_level} /></TableCell>
                    <TableCell className={v.risk_score >= 70 ? 'text-red-400' : v.risk_score >= 40 ? 'text-yellow-400' : 'text-green-400'}>{v.risk_score?.toFixed(1)}</TableCell>
                    <TableCell><Badge variant="outline">{v.status}</Badge></TableCell>
                    <TableCell><div className="flex gap-1">
                      <Button size="sm" variant="outline" onClick={() => handleAssess(v.vendor_id)}>Assess</Button>
                      <Button size="sm" variant="ghost" onClick={() => setScorecardVendor(v.vendor_id)}><Star className="h-4 w-4" /></Button>
                    </div></TableCell>
                  </TableRow>
                ))}</TableBody></Table>
            </CardContent></Card>
        </div>
        <div className="space-y-4">
          <RiskDistributionCard vendors={vendors} />
          {showRegister && <RegisterVendorForm onCreated={fetchData} />}
        </div>
      </div>
      {selectedVendor && <VendorDetailModal vendor={selectedVendor} onClose={() => setSelectedVendor(null)} onAssess={handleAssess} />}
      {scorecardVendor && <VendorScorecardModal vendorId={scorecardVendor} onClose={() => setScorecardVendor(null)} />}
    </div>
  );
}
import React from "react";

interface vendor_complianceAction {
  id: string;
  type: string;
  status: string;
  ts: string;
}

const vendor_complianceActions: React.FC<{}> = () => {
  const [items, setItems] = React.useState<vendor_complianceAction[]>([]);
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
      <h2 className="text-xl font-bold mb-4">vendor_compliance Actions</h2>
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
export default vendor_complianceActions;
