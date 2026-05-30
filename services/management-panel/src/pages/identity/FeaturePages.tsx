import React, { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Progress } from "@/components/ui/progress";
import { Switch } from "@/components/ui/switch";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useToast } from "@/hooks/use-toast";
import { Shield, Key, Fingerprint, Users, Activity, Globe, Lock, Eye, Bell, CheckCircle, XCircle, AlertTriangle, RefreshCw, Plus, Trash2, LogOut, Smartphone, Monitor, Clock, MapPin, ChevronRight, Search, FileText, BarChart3, BookOpen, Bug, Workflow, Server, Database, Network, Terminal, Zap, Play, Square, RotateCcw, Settings, Sliders, Layers, ArrowUpDown, Download, Upload, Filter, CheckCheck, Siren, Radio, RefreshCw as Refresh } from "lucide-react";

const featureModules = [
  { id: "sso", name: "SSO/OIDC Provider", icon: Key, description: "Centralized authentication via OIDC and SAML"},
  { id: "webauthn", name: "Passkey/WebAuthn", icon: Fingerprint, description: "Passwordless authentication with biometrics"},
  { id: "sessions", name: "Session Manager", icon: Activity, description: "View and revoke active sessions"},
  { id: "pam", name: "Privileged Access", icon: Shield, description: "JIT elevated access management"},
  { id: "policies", name: "Policy as Code", icon: FileText, description: "OPA/Rego policy management"},
  { id: "compliance", name: "Compliance Scanner", icon: CheckCircle, description: "CIS, NIST, BSI compliance scanning"},
  { id: "audit", name: "Audit Analytics", icon: BarChart3, description: "Anomaly detection on audit logs"},
  { id: "classification", name: "Data Classification", icon: Lock, description: "PII/PHI/PCI auto-classification"},
  { id: "vendors", name: "Vendor Risk", icon: BookOpen, description: "Security questionnaire automation"},
  { id: "breaches", name: "Breach Management", icon: Bell, description: "GDPR breach notification workflow"},
  { id: "workflows", name: "Workflow Studio", icon: Workflow, description: "Visual drag-and-drop workflow builder"},
  { id: "ansible", name: "Ansible/Salt", icon: Terminal, description: "Execute playbooks from panel"},
  { id: "pipelines", name: "Infra Pipelines", icon: Layers, description: "CI/CD for infrastructure"},
  { id: "drift", name: "Drift Detector", icon: ArrowUpDown, description: "Configuration drift detection"},
  { id: "quotas", name: "Quota Management", icon: Sliders, description: "Hierarchical resource quotas"},
  { id: "remediation", name: "Auto-Remediation", icon: Zap, description: "Event-driven auto-fixes"},
  { id: "maintenance", name: "Maintenance Planner", icon: Calendar, description: "Calendar-based maintenance"},
  { id: "runbooks", name: "Runbook Library", icon: BookOpen, description: "Community-contributed templates"},
  { id: "chaos", name: "Chaos Engineering", icon: Bug, description: "Controlled fault injection"},
  { id: "healing", name: "Self-Healing", icon: RefreshCw, description: "AI-driven auto-remediation"},
];

function Calendar(props: any) { return <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>; }

export function OIDCProviderPage() {
  const [clients, setClients] = useState<any[]>([]);
  const [showRegister, setShowRegister] = useState(false);
  const [newClient, setNewClient] = useState({ name: "", redirectUris: "", grantTypes: "authorization_code", scopes: "openid profile email" });
  const { toast } = useToast();

  const registerClient = async () => {
    try {
      const resp = await fetch("/api/v1/identity/oidc/register", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ client_name: newClient.name, redirect_uris: newClient.redirectUris.split(",").map(s => s.trim()), grant_types: newClient.grantTypes.split(",").map(s => s.trim()), scopes: newClient.scopes.split(",").map(s => s.trim()) }) });
      if (resp.ok) { const data = await resp.json(); setClients(prev => [...prev, data]); toast({ title: "Client Registered", description: `Client ID: ${data.client_id}` }); setShowRegister(false); }
    } catch (e) { toast({ title: "Error", description: "Failed to register client", variant: "destructive" }); }
  };

  useEffect(() => {
    fetch("/api/v1/identity/oidc/clients").then(r => r.json()).then(setClients).catch(() => {});
  }, []);

  return (<div className="space-y-6"><div className="flex items-center justify-between"><div><h1 className="text-3xl font-bold tracking-tight">SSO / OIDC Provider</h1><p className="text-muted-foreground">Manage OpenID Connect clients and SAML service providers</p></div><Button onClick={() => setShowRegister(true)}><Plus className="mr-2 h-4 w-4" /> Register Client</Button></div>
    <Tabs defaultValue="oidc"><TabsList><TabsTrigger value="oidc">OIDC Clients</TabsTrigger><TabsTrigger value="saml">SAML SPs</TabsTrigger><TabsTrigger value="config">Configuration</TabsTrigger></TabsList>
    <TabsContent value="oidc"><Card><CardHeader><CardTitle>OIDC Clients <Badge variant="secondary">{clients.length}</Badge></CardTitle><CardDescription>Registered OpenID Connect relying parties</CardDescription></CardHeader>
    <CardContent><Table><TableHeader><TableRow><TableHead>Client ID</TableHead><TableHead>Name</TableHead><TableHead>Grant Types</TableHead><TableHead>Scopes</TableHead><TableHead>Created</TableHead></TableRow></TableHeader>
    <TableBody>{clients.length === 0 ? <TableRow><TableCell colSpan={5} className="text-center text-muted-foreground py-8">No clients registered yet</TableCell></TableRow> : clients.map(c => <TableRow key={c.client_id}><TableCell className="font-mono text-xs">{c.client_id.substring(0, 12)}...</TableCell><TableCell>{c.client_name}</TableCell><TableCell>{c.grant_types?.join(", ")}</TableCell><TableCell>{c.scopes?.join(", ")}</TableCell><TableCell>{new Date(c.created_at || Date.now()).toLocaleDateString()}</TableCell></TableRow>)}</TableBody></Table></CardContent></Card></TabsContent>
    <TabsContent value="config"><Card><CardHeader><CardTitle>Identity Provider Configuration</CardTitle></CardHeader><CardContent><div className="grid grid-cols-2 gap-4"><div><Label>Issuer</Label><Input value="https://auth.infrapilot.local" readOnly className="font-mono" /></div><div><Label>Token Signing Algorithm</Label><Input value="RS256" readOnly /></div><div><Label>Access Token TTL</Label><Input value="3600s (1 hour)" readOnly /></div><div><Label>Refresh Token TTL</Label><Input value="86400s (24 hours)" readOnly /></div></div></CardContent></Card></TabsContent></Tabs>
    <Dialog open={showRegister} onOpenChange={setShowRegister}><DialogContent><DialogHeader><DialogTitle>Register OIDC Client</DialogTitle><DialogDescription>Create a new OpenID Connect client application</DialogDescription></DialogHeader>
    <div className="space-y-4"><div><Label>Client Name</Label><Input value={newClient.name} onChange={e => setNewClient(p => ({...p, name: e.target.value}))} placeholder="My Application" /></div>
    <div><Label>Redirect URIs (comma-separated)</Label><Input value={newClient.redirectUris} onChange={e => setNewClient(p => ({...p, redirectUris: e.target.value}))} placeholder="https://app.example.com/callback" /></div>
    <div><Label>Grant Types</Label><Input value={newClient.grantTypes} onChange={e => setNewClient(p => ({...p, grantTypes: e.target.value}))} /></div>
    <div><Label>Scopes</Label><Input value={newClient.scopes} onChange={e => setNewClient(p => ({...p, scopes: e.target.value}))} /></div></div>
    <DialogFooter><Button variant="outline" onClick={() => setShowRegister(false)}>Cancel</Button><Button onClick={registerClient}>Register</Button></DialogFooter></DialogContent></Dialog></div>);
}

export function SessionManagerPage() {
  const [sessions, setSessions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  const loadSessions = async () => {
    setLoading(true);
    try { const resp = await fetch("/api/v1/auth/sessions?user_id=current"); if (resp.ok) setSessions(await resp.json()); }
    catch (e) {} finally { setLoading(false); }
  };

  useEffect(() => { loadSessions(); }, []);

  const revokeSession = async (sessionId: string) => {
    try { const resp = await fetch(`/api/v1/auth/sessions/${sessionId}`, { method: "DELETE" }); if (resp.ok) { toast({ title: "Session Revoked" }); loadSessions(); } }
    catch (e) { toast({ title: "Error", variant: "destructive" }); }
  };

  const revokeAll = async () => {
    try { const resp = await fetch("/api/v1/auth/sessions?user_id=current&exclude_session_id=current", { method: "DELETE" }); if (resp.ok) { toast({ title: "All Other Sessions Revoked" }); loadSessions(); } }
    catch (e) { toast({ title: "Error", variant: "destructive" }); }
  };

  const getDeviceIcon = (platform: string) => {
    if (platform?.toLowerCase().includes("mobile") || platform?.toLowerCase().includes("android") || platform?.toLowerCase().includes("ios")) return Smartphone;
    return Monitor;
  };

  return (<div className="space-y-6"><div className="flex items-center justify-between"><div><h1 className="text-3xl font-bold tracking-tight">Session Manager</h1><p className="text-muted-foreground">View and manage active sessions across devices</p></div>
    <div className="flex gap-2"><Button variant="outline" onClick={loadSessions}><RefreshCw className="mr-2 h-4 w-4" />Refresh</Button><Button variant="destructive" onClick={revokeAll}><LogOut className="mr-2 h-4 w-4" />Revoke All</Button></div></div>
    <div className="grid gap-4">{loading ? <div className="text-center py-12 text-muted-foreground">Loading sessions...</div> : sessions.length === 0 ? <div className="text-center py-12 text-muted-foreground">No active sessions</div> : sessions.map(s => {
      const DeviceIcon = getDeviceIcon(s.device_fingerprint?.platform);
      const isCurrent = s.is_current;
      return <Card key={s.session_id} className={isCurrent ? "border-primary" : ""}><CardContent className="pt-6"><div className="flex items-start justify-between"><div className="flex items-start gap-4"><div className="p-2 rounded-lg bg-primary/10"><DeviceIcon className="h-6 w-6 text-primary" /></div>
      <div><div className="flex items-center gap-2"><h3 className="font-medium">{s.device_fingerprint?.platform || "Unknown Device"}{isCurrent && <Badge>Current</Badge>}</h3></div>
      <p className="text-sm text-muted-foreground">{s.device_fingerprint?.user_agent?.substring(0, 80)}...</p>
      <div className="flex flex-wrap gap-4 mt-2 text-xs text-muted-foreground"><span className="flex items-center gap-1"><MapPin className="h-3 w-3" /> {s.location?.city || "Unknown"}, {s.location?.country || "Unknown"}</span><span className="flex items-center gap-1"><Globe className="h-3 w-3" /> {s.ip_address}</span><span className="flex items-center gap-1"><Clock className="h-3 w-3" /> {new Date(s.created_at).toLocaleString()}</span><span className="flex items-center gap-1"><Activity className="h-3 w-3" /> Last: {new Date(s.last_activity).toLocaleString()}</span></div>
      <div className="flex flex-wrap gap-1 mt-2">{s.device_fingerprint?.screen_resolution && <Badge variant="outline" className="text-xs">{s.device_fingerprint.screen_resolution}</Badge>}{s.device_fingerprint?.timezone && <Badge variant="outline" className="text-xs">{s.device_fingerprint.timezone}</Badge>}{s.device_fingerprint?.language && <Badge variant="outline" className="text-xs">{s.device_fingerprint.language}</Badge>}</div></div></div>
      {!isCurrent && <Button variant="ghost" size="sm" onClick={() => revokeSession(s.session_id)}><Trash2 className="h-4 w-4 text-destructive" /></Button>}</div></Card>;
    })}</div></div>);
}

export function ComplianceScannerPage() {
  const [standards] = useState(["CIS_Docker", "CIS_Kubernetes", "NIST_800_53", "BSI_Grundschutz"]);
  const [scans, setScans] = useState<any[]>([]);
  const [selectedStandard, setSelectedStandard] = useState("CIS_Docker");
  const [scanning, setScanning] = useState(false);
  const { toast } = useToast();

  const runScan = async () => {
    setScanning(true);
    try { const resp = await fetch("/api/v1/compliance/scan", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ standard: selectedStandard, target: "all" }) }); if (resp.ok) { const data = await resp.json(); setScans(prev => [data, ...prev]); toast({ title: "Scan Complete", description: `Score: ${data.summary?.compliance_score}%` }); } }
    catch (e) { toast({ title: "Error", variant: "destructive" }); } finally { setScanning(false); }
  };

  useEffect(() => {
    fetch("/api/v1/compliance/scans").then(r => r.json()).then(setScans).catch(() => {});
  }, []);

  return (<div className="space-y-6"><div className="flex items-center justify-between"><div><h1 className="text-3xl font-bold tracking-tight">Compliance Scanner</h1><p className="text-muted-foreground">Automated compliance scanning against industry standards</p></div>
    <div className="flex gap-2"><select className="border rounded-md px-3 py-2 text-sm" value={selectedStandard} onChange={e => setSelectedStandard(e.target.value)}>{standards.map(s => <option key={s} value={s}>{s.replace(/_/g, " ")}</option>)}</select><Button onClick={runScan} disabled={scanning}><Shield className="mr-2 h-4 w-4" />{scanning ? "Scanning..." : "Run Scan"}</Button></div></div>
    <div className="grid grid-cols-4 gap-4">{standards.map(s => { const lastScan = scans.find(sc => sc.standard === s); return <Card key={s} className="cursor-pointer hover:border-primary" onClick={() => setSelectedStandard(s)}><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">{s.replace(/_/g, " ")}</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{lastScan ? `${lastScan.summary?.compliance_score?.toFixed(1)}%` : "N/A"}</div><Progress value={lastScan?.summary?.compliance_score || 0} className="mt-2" /><p className="text-xs text-muted-foreground mt-2">{lastScan ? `${lastScan.summary?.passed}/${lastScan.summary?.total_checks} passed` : "No scans yet"}</p></CardContent></Card>; })}</div>
    <Card><CardHeader><CardTitle>Scan History</CardTitle></CardHeader><CardContent><Table><TableHeader><TableRow><TableHead>Standard</TableHead><TableHead>Score</TableHead><TableHead>Passed</TableHead><TableHead>Failed</TableHead><TableHead>Waived</TableHead><TableHead>Date</TableHead></TableRow></TableHeader><TableBody>{scans.map(s => <TableRow key={s.scan_id}><TableCell>{s.standard}</TableCell><TableCell><span className={s.summary?.compliance_score >= 80 ? "text-green-600" : s.summary?.compliance_score >= 60 ? "text-yellow-600" : "text-red-600"}>{s.summary?.compliance_score?.toFixed(1)}%</span></TableCell><TableCell className="text-green-600">{s.summary?.passed}</TableCell><TableCell className="text-red-600">{s.summary?.failed}</TableCell><TableCell>{s.summary?.waived}</TableCell><TableCell>{new Date(s.timestamp).toLocaleString()}</TableCell></TableRow>)}</TableBody></Table></CardContent></Card></div>);
}
