import React, { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Progress } from "@/components/ui/progress";
import { useToast } from "@/hooks/use-toast";
import { Shield, FileText, BarChart3, Lock, BookOpen, Bell, Search, Download, Upload, Filter, AlertTriangle, CheckCircle, XCircle } from "lucide-react";

export function PolicyAsCodePage() {
  const [policies, setPolicies] = useState<any[]>([]);
  const [selectedPolicy, setSelectedPolicy] = useState<any>(null);
  const [evalInput, setEvalInput] = useState("{}");
  const [evalResult, setEvalResult] = useState<any>(null);
  const { toast } = useToast();

  useEffect(() => {
    fetch("/api/v1/policies").then(r => r.json()).then(setPolicies).catch(() => {});
  }, []);

  const evaluatePolicy = async () => {
    try {
      const resp = await fetch("/api/v1/policies/evaluate", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ package: selectedPolicy?.package || "infra_pilot.auth.health", input: JSON.parse(evalInput) })
      });
      if (resp.ok) setEvalResult(await resp.json());
    } catch (e) { toast({ title: "Error", description: "Invalid JSON input", variant: "destructive" }); }
  };

  return (<div className="space-y-6"><div className="flex items-center justify-between"><div><h1 className="text-3xl font-bold tracking-tight">Policy as Code</h1><p className="text-muted-foreground">OPA/Rego policy management with git-versioned policies</p></div></div>
    <div className="grid grid-cols-3 gap-6"><div className="col-span-1"><Card><CardHeader><CardTitle>Policies <Badge variant="secondary">{policies.length}</Badge></CardTitle></CardHeader><CardContent className="space-y-2">{policies.map(p => <div key={p.policy_id} className={`p-3 rounded-lg cursor-pointer border ${selectedPolicy?.policy_id === p.policy_id ? "border-primary bg-primary/5" : "hover:border-border"}`} onClick={() => setSelectedPolicy(p)}><div className="font-medium text-sm">{p.name}</div><div className="text-xs text-muted-foreground">{p.package}</div><div className="flex gap-1 mt-1">{p.tags?.map((t: string) => <Badge key={t} variant="outline" className="text-xs">{t}</Badge>)}</div></div>)}</CardContent></Card></div>
    <div className="col-span-2 space-y-4">{selectedPolicy && <><Card><CardHeader><CardTitle>{selectedPolicy.name}</CardTitle><CardDescription>{selectedPolicy.description}</CardDescription></CardHeader><CardContent><div className="grid grid-cols-2 gap-4 mb-4"><div><Label>Package</Label><Input value={selectedPolicy.package} readOnly className="font-mono" /></div><div><Label>Version</Label><Input value={selectedPolicy.version} readOnly /></div></div><div><Label>Rules ({selectedPolicy.rules_count})</Label><div className="space-y-2 mt-2">{selectedPolicy.rules?.map((r: any, i: number) => <div key={i} className="p-3 bg-muted rounded-lg font-mono text-sm"><span className={`inline-block px-2 py-0.5 rounded text-xs font-medium mr-2 ${r.effect === "allow" ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}`}>{r.effect || r.type}</span> {r.name}: {r.conditions?.map((c: any) => `${c.field} ${c.operator} ${c.value}`).join(", ")}</div>)}</div></div></CardContent></Card>
    <Card><CardHeader><CardTitle>Test Evaluation</CardTitle></CardHeader><CardContent className="space-y-4"><div><Label>Input JSON</Label><textarea className="w-full h-32 p-2 border rounded-md font-mono text-sm" value={evalInput} onChange={e => setEvalInput(e.target.value)} /></div><Button onClick={evaluatePolicy}><FileText className="mr-2 h-4 w-4" /> Evaluate</Button>
    {evalResult && <div className={`p-4 rounded-lg ${evalResult.allowed ? "bg-green-50 border border-green-200" : "bg-red-50 border border-red-200"}`}><div className="flex items-center gap-2 mb-2">{evalResult.allowed ? <CheckCircle className="h-5 w-5 text-green-600" /> : <XCircle className="h-5 w-5 text-red-600" />}<span className="font-medium">{evalResult.allowed ? "ALLOW" : "DENY"}</span></div>
    {evalResult.denied_rules?.length > 0 && <div className="text-sm text-red-700"><p className="font-medium">Denied by:</p>{evalResult.denied_rules.map((r: any, i: number) => <p key={i}>- {r.name}: {r.reason}</p>)}</div>}
    {evalResult.matched_rules?.length > 0 && <div className="text-sm text-green-700 mt-2"><p className="font-medium">Matched rules:</p>{evalResult.matched_rules.map((r: any, i: number) => <p key={i}>- {r.name} ({r.effect})</p>)}</div>}</div>}</CardContent></Card></>}</div></div></div>);
}

export function AuditAnalyticsPage() {
  const [anomalies, setAnomalies] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [severityFilter, setSeverityFilter] = useState("");

  useEffect(() => {
    fetch("/api/v1/audit/analytics/overview").then(r => r.json()).then(setStats).catch(() => {});
    const params = severityFilter ? `?severity=${severityFilter}` : "";
    fetch(`/api/v1/audit/analytics/anomalies${params}`).then(r => r.json()).then(setAnomalies).catch(() => {});
  }, [severityFilter]);

  const runAnalysis = async () => {
    try { const resp = await fetch("/api/v1/audit/analytics/run", { method: "POST" }); if (resp.ok) { const d = await resp.json(); setStats(d); } }
    catch (e) {}
  };

  const getSeverityColor = (severity: string) => {
    switch(severity) {
      case "critical": return "bg-red-100 text-red-800 border-red-200";
      case "high": return "bg-orange-100 text-orange-800 border-orange-200";
      case "medium": return "bg-yellow-100 text-yellow-800 border-yellow-200";
      case "low": return "bg-blue-100 text-blue-800 border-blue-200";
      default: return "bg-gray-100 text-gray-800";
    }
  };

  return (<div className="space-y-6"><div className="flex items-center justify-between"><div><h1 className="text-3xl font-bold tracking-tight">Audit Trail Analytics</h1><p className="text-muted-foreground">Anomaly detection on audit logs using ML and statistical analysis</p></div><Button onClick={runAnalysis}><BarChart3 className="mr-2 h-4 w-4" /> Run Analysis</Button></div>
    <div className="grid grid-cols-4 gap-4">{stats && <>
      <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Events Ingested</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{stats.total_events_ingested || 0}</div></CardContent></Card>
      <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Anomalies Detected</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{stats.total_anomalies_detected || 0}</div></CardContent></Card>
      <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Users Tracked</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{stats.users_tracked || 0}</div></CardContent></Card>
      <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Detection Threshold</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{stats.detection_threshold || 0.7}</div></CardContent></Card>
    </>}</div>
    <Card><CardHeader><CardTitle>Detected Anomalies <Badge variant="secondary">{anomalies.length}</Badge></CardTitle></CardHeader><CardContent>
      <div className="flex gap-2 mb-4">{["", "critical", "high", "medium", "low"].map(s => <Badge key={s} variant={severityFilter === s ? "default" : "outline"} className="cursor-pointer" onClick={() => setSeverityFilter(s)}>{s || "All"}</Badge>)}</div>
      <Table><TableHeader><TableRow><TableHead>Type</TableHead><TableHead>Severity</TableHead><TableHead>Title</TableHead><TableHead>Score</TableHead><TableHead>Detected</TableHead></TableRow></TableHeader><TableBody>{anomalies.map(a => <TableRow key={a.anomaly_id}><TableCell><Badge variant="outline">{a.event_type}</Badge></TableCell><TableCell><span className={`px-2 py-1 rounded-full text-xs font-medium ${getSeverityColor(a.severity)}`}>{a.severity}</span></TableCell><TableCell className="max-w-xs truncate">{a.title}</TableCell><TableCell>{(a.score * 100).toFixed(0)}%</TableCell><TableCell>{new Date(a.detected_at).toLocaleString()}</TableCell></TableRow>)}</TableBody></Table></CardContent></Card></div>);
}

export function DataClassificationPage() {
  const [inventory, setInventory] = useState<any[]>([]);
  const [scanText, setScanText] = useState("");
  const [scanResult, setScanResult] = useState<any>(null);
  const { toast } = useToast();

  useEffect(() => { fetch("/api/v1/classification/inventory").then(r => r.json()).then(setInventory).catch(() => {}); }, []);

  const runScan = async () => {
    try {
      const resp = await fetch("/api/v1/classification/scan", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: scanText, resource_id: "manual_scan", resource_type: "text" })
      });
      if (resp.ok) setScanResult(await resp.json());
    } catch (e) { toast({ title: "Error", variant: "destructive" }); }
  };

  const getLevelColor = (level: string) => {
    switch(level) {
      case "public": return "bg-green-100 text-green-800";
      case "internal": return "bg-blue-100 text-blue-800";
      case "confidential": return "bg-yellow-100 text-yellow-800";
      case "restricted": return "bg-orange-100 text-orange-800";
      case "regulated": return "bg-red-100 text-red-800";
      default: return "bg-gray-100";
    }
  };

  return (<div className="space-y-6"><div className="flex items-center justify-between"><div><h1 className="text-3xl font-bold tracking-tight">Data Classification Engine</h1><p className="text-muted-foreground">Auto-classify PII, PHI, and PCI data across resources</p></div></div>
    <div className="grid grid-cols-3 gap-6"><div className="col-span-2"><Card><CardHeader><CardTitle>Classify Text</CardTitle></CardHeader><CardContent className="space-y-4"><textarea className="w-full h-48 p-3 border rounded-md font-mono text-sm" value={scanText} onChange={e => setScanText(e.target.value)} placeholder="Paste text to scan for PII/PHI/PCI..." /><Button onClick={runScan}><Search className="mr-2 h-4 w-4" /> Scan Text</Button>
    {scanResult && <div className="space-y-3 mt-4"><div className="flex items-center gap-2"><Badge className={getLevelColor(scanResult.overall_level)}>{scanResult.overall_level}</Badge><span className="text-sm text-muted-foreground">Confidence: {(scanResult.confidence * 100).toFixed(1)}%</span></div>
    {scanResult.pii_found?.length > 0 && <div><h4 className="font-medium text-sm mb-1">PII Found ({scanResult.pii_found.length})</h4><div className="flex flex-wrap gap-2">{scanResult.pii_found.slice(0, 10).map((p: any, i: number) => <Badge key={i} variant="outline" className="text-xs">{p.type}: {p.value}</Badge>)}</div></div>}
    {scanResult.phi_found?.length > 0 && <div><h4 className="font-medium text-sm mb-1">PHI Found ({scanResult.phi_found.length})</h4><div className="flex flex-wrap gap-2">{scanResult.phi_found.slice(0, 10).map((p: any, i: number) => <Badge key={i} variant="outline" className="text-xs">{p.type}: {p.value}</Badge>)}</div></div>}
    {scanResult.pci_found?.length > 0 && <div><h4 className="font-medium text-sm mb-1">PCI Found ({scanResult.pci_found.length})</h4><div className="flex flex-wrap gap-2">{scanResult.pci_found.slice(0, 10).map((p: any, i: number) => <Badge key={i} variant="outline" className="text-xs">{p.type}: {p.value}</Badge>)}</div></div>}</div>}</CardContent></Card></div>
    <div><Card><CardHeader><CardTitle>Inventory <Badge variant="secondary">{inventory.length}</Badge></CardTitle></CardHeader><CardContent><div className="space-y-2">{inventory.map((item: any) => <div key={item.resource_id} className="p-2 rounded-lg border text-sm"><div className="font-medium truncate">{item.resource_id}</div><Badge className={getLevelColor(item.classification_level)}>{item.classification_level}</Badge><div className="text-xs text-muted-foreground mt-1">{item.resource_type} | Scanned: {new Date(item.last_scanned).toLocaleDateString()}</div></div>)}</div></CardContent></Card></div></div></div>);
}

export function VendorRiskPage() {
  const [vendors, setVendors] = useState<any[]>([]);
  const [showAdd, setShowAdd] = useState(false);
  const [newVendor, setNewVendor] = useState({ name: "", category: "cloud_provider", contact_email: "", risk_tier: "medium" });
  const { toast } = useToast();

  useEffect(() => { fetch("/api/v1/vendors").then(r => r.json()).then(setVendors).catch(() => {}); }, []);

  const addVendor = async () => {
    try {
      const resp = await fetch("/api/v1/vendors", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(newVendor) });
      if (resp.ok) { const d = await resp.json(); setVendors(prev => [d, ...prev]); setShowAdd(false); toast({ title: "Vendor Added" }); }
    } catch (e) { toast({ title: "Error", variant: "destructive" }); }
  };

  const createAssessment = async (vendorId: string) => {
    try {
      const resp = await fetch(`/api/v1/vendors/${vendorId}/assessments`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ template_type: "sig", assessor: "current_user" }) });
      if (resp.ok) { const d = await resp.json(); toast({ title: "Assessment Created", description: `ID: ${d.assessment_id}` }); }
    } catch (e) { toast({ title: "Error", variant: "destructive" }); }
  };

  return (<div className="space-y-6"><div className="flex items-center justify-between"><div><h1 className="text-3xl font-bold tracking-tight">Vendor Risk Assessment</h1><p className="text-muted-foreground">Automated security questionnaires (SIG/CAIQ)</p></div><Button onClick={() => setShowAdd(true)}><BookOpen className="mr-2 h-4 w-4" /> Add Vendor</Button></div>
    <div className="grid grid-cols-4 gap-4">
      <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Total Vendors</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{vendors.length}</div></CardContent></Card>
      <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Low Risk</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-green-600">{vendors.filter(v => v.risk_tier === "low").length}</div></CardContent></Card>
      <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Medium Risk</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-yellow-600">{vendors.filter(v => v.risk_tier === "medium").length}</div></CardContent></Card>
      <Card><CardHeader className="pb-2"><CardTitle className="text-sm">High/Critical</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-red-600">{vendors.filter(v => v.risk_tier === "high" || v.risk_tier === "critical").length}</div></CardContent></Card>
    </div>
    <Card><CardHeader><CardTitle>Vendors</CardTitle></CardHeader><CardContent><Table><TableHeader><TableRow><TableHead>Name</TableHead><TableHead>Category</TableHead><TableHead>Risk Tier</TableHead><TableHead>Status</TableHead><TableHead>Actions</TableHead></TableRow></TableHeader><TableBody>{vendors.map(v => <TableRow key={v.vendor_id}><TableCell className="font-medium">{v.name}</TableCell><TableCell>{v.category}</TableCell><TableCell><Badge className={v.risk_tier === "low" ? "bg-green-100 text-green-800" : v.risk_tier === "high" ? "bg-red-100 text-red-800" : "bg-yellow-100 text-yellow-800"}>{v.risk_tier}</Badge></TableCell><TableCell>{v.status}</TableCell><TableCell><Button variant="outline" size="sm" onClick={() => createAssessment(v.vendor_id)}>Assess</Button></TableCell></TableRow>)}</TableBody></Table></CardContent></Card>
    <Dialog open={showAdd} onOpenChange={setShowAdd}><DialogContent><DialogHeader><DialogTitle>Add Vendor</DialogTitle></DialogHeader><div className="space-y-4"><div><Label>Name</Label><Input value={newVendor.name} onChange={e => setNewVendor(p => ({...p, name: e.target.value}))} /></div><div><Label>Category</Label><select className="w-full border rounded-md px-3 py-2" value={newVendor.category} onChange={e => setNewVendor(p => ({...p, category: e.target.value}))}><option value="cloud_provider">Cloud Provider</option><option value="saas">SaaS</option><option value="security">Security</option><option value="infrastructure">Infrastructure</option><option value="consulting">Consulting</option></select></div><div><Label>Contact Email</Label><Input value={newVendor.contact_email} onChange={e => setNewVendor(p => ({...p, contact_email: e.target.value}))} /></div></div><DialogFooter><Button variant="outline" onClick={() => setShowAdd(false)}>Cancel</Button><Button onClick={addVendor}>Add</Button></DialogFooter></DialogContent></Dialog></div>);
}

export function BreachNotificationPage() {
  const [breaches, setBreaches] = useState<any[]>([]);
  const [showReport, setShowReport] = useState(false);
  const [newBreach, setNewBreach] = useState({ description: "", data_types_affected: "email,password", affected_users: 0, severity: "medium" });
  const { toast } = useToast();

  useEffect(() => { fetch("/api/v1/breaches").then(r => r.json()).then(setBreaches).catch(() => {}); }, []);

  const reportBreach = async () => {
    try {
      const resp = await fetch("/api/v1/breaches", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ...newBreach, data_types_affected: newBreach.data_types_affected.split(",").map(s => s.trim()), affected_systems: [] }) });
      if (resp.ok) { const d = await resp.json(); setBreaches(prev => [d, ...prev]); setShowReport(false); toast({ title: "Breach Reported", variant: "destructive" }); }
    } catch (e) { toast({ title: "Error", variant: "destructive" }); }
  };

  return (<div className="space-y-6"><div className="flex items-center justify-between"><div><h1 className="text-3xl font-bold tracking-tight">Breach Notification</h1><p className="text-muted-foreground">GDPR breach notification workflow automation</p></div><Button variant="destructive" onClick={() => setShowReport(true)}><Bell className="mr-2 h-4 w-4" /> Report Breach</Button></div>
    <Card><CardHeader><CardTitle>Breach Register <Badge variant="secondary">{breaches.length}</Badge></CardTitle></CardHeader><CardContent><Table><TableHeader><TableRow><TableHead>Severity</TableHead><TableHead>Status</TableHead><TableHead>Description</TableHead><TableHead>Data Types</TableHead><TableHead>Affected</TableHead><TableHead>Deadline</TableHead></TableRow></TableHeader><TableBody>{breaches.map(b => <TableRow key={b.breach_id}><TableCell><Badge className={b.severity === "critical" ? "bg-red-100 text-red-800" : b.severity === "high" ? "bg-orange-100 text-orange-800" : "bg-yellow-100 text-yellow-800"}>{b.severity}</Badge></TableCell><TableCell><Badge variant="outline">{b.status}</Badge></TableCell><TableCell className="max-w-xs truncate">{b.description}</TableCell><TableCell>{b.data_types_affected?.join(", ")}</TableCell><TableCell>{b.affected_users?.toLocaleString()}</TableCell><TableCell className="text-xs">{new Date(b.regulatory_deadline).toLocaleString()}</TableCell></TableRow>)}</TableBody></Table></CardContent></Card>
    <Dialog open={showReport} onOpenChange={setShowReport}><DialogContent><DialogHeader><DialogTitle>Report Data Breach</DialogTitle><DialogDescription>GDPR requires notification within 72 hours</DialogDescription></DialogHeader>
    <div className="space-y-4"><div><Label>Description</Label><textarea className="w-full h-24 p-2 border rounded-md" value={newBreach.description} onChange={e => setNewBreach(p => ({...p, description: e.target.value}))} placeholder="Describe the breach..." /></div>
    <div><Label>Data Types Affected (comma-separated)</Label><Input value={newBreach.data_types_affected} onChange={e => setNewBreach(p => ({...p, data_types_affected: e.target.value}))} /></div>
    <div className="grid grid-cols-2 gap-4"><div><Label>Affected Users</Label><Input type="number" value={newBreach.affected_users} onChange={e => setNewBreach(p => ({...p, affected_users: parseInt(e.target.value) || 0}))} /></div><div><Label>Severity</Label><select className="w-full border rounded-md px-3 py-2" value={newBreach.severity} onChange={e => setNewBreach(p => ({...p, severity: e.target.value}))}><option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option><option value="critical">Critical</option></select></div></div></div>
    <DialogFooter><Button variant="outline" onClick={() => setShowReport(false)}>Cancel</Button><Button variant="destructive" onClick={reportBreach}>Report Breach</Button></DialogFooter></DialogContent></Dialog></div>);
}
