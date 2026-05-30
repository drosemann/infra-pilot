import React, { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Progress } from "@/components/ui/progress";
import { Switch } from "@/components/ui/switch";
import { useToast } from "@/hooks/use-toast";
import { Workflow, Terminal, Layers, ArrowUpDown, Sliders, Zap, Calendar, BookOpen, Bug, RefreshCw, Play, Square, Plus, Trash2, Settings, Server, Globe, Clock, CheckCircle, XCircle, AlertTriangle, Activity } from "lucide-react";

export function WorkflowStudioPage() {
  const [workflows, setWorkflows] = useState<any[]>([]);
  const [nodeTypes, setNodeTypes] = useState<any[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [newWorkflow, setNewWorkflow] = useState({ name: "", description: "" });
  const { toast } = useToast();

  useEffect(() => {
    fetch("/api/v1/workflows").then(r => r.json()).then(setWorkflows).catch(() => {});
    fetch("/api/v1/workflows/node-types").then(r => r.json()).then(setNodeTypes).catch(() => {});
  }, []);

  const createWorkflow = async () => {
    try {
      const resp = await fetch("/api/v1/workflows", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: newWorkflow.name, description: newWorkflow.description, nodes: [], edges: [] })
      });
      if (resp.ok) { const d = await resp.json(); setWorkflows(prev => [d, ...prev]); setShowCreate(false); toast({ title: "Workflow Created" }); }
    } catch (e) { toast({ title: "Error", variant: "destructive" }); }
  };

  const executeWorkflow = async (wfId: string) => {
    try {
      const resp = await fetch(`/api/v1/workflows/${wfId}/execute`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ trigger_data: { source: "manual", timestamp: new Date().toISOString() } })
      });
      if (resp.ok) { toast({ title: "Execution Started" }); }
    } catch (e) { toast({ title: "Error", variant: "destructive" }); }
  };

  return (<div className="space-y-6"><div className="flex items-center justify-between"><div><h1 className="text-3xl font-bold tracking-tight">Workflow Studio</h1><p className="text-muted-foreground">Visual drag-and-drop workflow automation builder</p></div><Button onClick={() => setShowCreate(true)}><Plus className="mr-2 h-4 w-4" /> Create Workflow</Button></div>
    <Tabs defaultValue="workflows"><TabsList><TabsTrigger value="workflows">Workflows</TabsTrigger><TabsTrigger value="node-types">Node Types</TabsTrigger><TabsTrigger value="executions">Executions</TabsTrigger></TabsList>
    <TabsContent value="workflows"><div className="grid grid-cols-3 gap-4">{workflows.map(w => <Card key={w.workflow_id} className="cursor-pointer hover:border-primary"><CardHeader className="pb-2"><CardTitle className="text-sm">{w.name}</CardTitle><CardDescription className="text-xs">{w.description}</CardDescription></CardHeader><CardContent><div className="flex items-center gap-2 text-xs text-muted-foreground mb-2"><Badge variant={w.status === "active" ? "default" : "secondary"}>{w.status}</Badge><span>{w.nodes?.length || 0} nodes</span><span>{w.edges?.length || 0} edges</span></div><div className="text-xs text-muted-foreground">Executions: {w.execution_count || 0}</div><div className="flex gap-2 mt-3"><Button size="sm" variant="outline" className="flex-1" onClick={() => executeWorkflow(w.workflow_id)} disabled={w.status !== "active"}><Play className="mr-1 h-3 w-3" /> Run</Button><Button size="sm" variant="ghost"><Settings className="h-3 w-3" /></Button></div></CardContent></Card>)}</div></TabsContent>
    <TabsContent value="node-types"><Card><CardContent className="pt-6"><Table><TableHeader><TableRow><TableHead>Type</TableHead><TableHead>Category</TableHead><TableHead>Description</TableHead></TableRow></TableHeader><TableBody>{nodeTypes.map((n: any) => <TableRow key={n.type}><TableCell className="font-mono text-sm">{n.type}</TableCell><TableCell><Badge variant="outline">{n.category}</Badge></TableCell><TableCell className="text-sm text-muted-foreground">{n.description}</TableCell></TableRow>)}</TableBody></Table></CardContent></Card></TabsContent></Tabs>
    <Dialog open={showCreate} onOpenChange={setShowCreate}><DialogContent><DialogHeader><DialogTitle>Create Workflow</DialogTitle></DialogHeader><div className="space-y-4"><div><Label>Name</Label><Input value={newWorkflow.name} onChange={e => setNewWorkflow(p => ({...p, name: e.target.value}))} placeholder="My Automation" /></div><div><Label>Description</Label><textarea className="w-full h-24 p-2 border rounded-md" value={newWorkflow.description} onChange={e => setNewWorkflow(p => ({...p, description: e.target.value}))} placeholder="Describe what this workflow does..." /></div></div><DialogFooter><Button variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button><Button onClick={createWorkflow}>Create</Button></DialogFooter></DialogContent></Dialog></div>);
}

export function InfrastructurePipelinesPage() {
  const [pipelines, setPipelines] = useState<any[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [newPipeline, setNewPipeline] = useState({ name: "", description: "", repo_url: "", branch: "main" });
  const { toast } = useToast();

  useEffect(() => { fetch("/api/v1/pipelines").then(r => r.json()).then(setPipelines).catch(() => {}); }, []);

  const createPipeline = async () => {
    try {
      const resp = await fetch("/api/v1/pipelines", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(newPipeline) });
      if (resp.ok) { const d = await resp.json(); setPipelines(prev => [d, ...prev]); setShowCreate(false); toast({ title: "Pipeline Created" }); }
    } catch (e) { toast({ title: "Error", variant: "destructive" }); }
  };

  const runPipeline = async (pipelineId: string) => {
    try {
      const resp = await fetch(`/api/v1/pipelines/${pipelineId}/run`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ triggered_by: "manual" }) });
      if (resp.ok) { toast({ title: "Pipeline Run Started" }); }
    } catch (e) { toast({ title: "Error", variant: "destructive" }); }
  };

  return (<div className="space-y-6"><div className="flex items-center justify-between"><div><h1 className="text-3xl font-bold tracking-tight">Infrastructure Pipelines</h1><p className="text-muted-foreground">CI/CD for infrastructure as code (lint/plan/apply)</p></div><Button onClick={() => setShowCreate(true)}><Plus className="mr-2 h-4 w-4" /> Create Pipeline</Button></div>
    <Card><CardHeader><CardTitle>Pipelines</CardTitle></CardHeader><CardContent><Table><TableHeader><TableRow><TableHead>Name</TableHead><TableHead>Repo</TableHead><TableHead>Branch</TableHead><TableHead>Status</TableHead><TableHead>Runs</TableHead><TableHead>Actions</TableHead></TableRow></TableHeader><TableBody>{pipelines.map(p => <TableRow key={p.pipeline_id}><TableCell className="font-medium">{p.name}</TableCell><TableCell className="text-xs font-mono">{p.repo_url?.split("/").slice(-2).join("/")}</TableCell><TableCell>{p.branch}</TableCell><TableCell><Badge variant={p.status === "active" ? "default" : "secondary"}>{p.status}</Badge></TableCell><TableCell>{p.run_count || 0}</TableCell><TableCell><Button size="sm" onClick={() => runPipeline(p.pipeline_id)} disabled={p.status !== "active"}><Play className="mr-1 h-3 w-3" /> Run</Button></TableCell></TableRow>)}</TableBody></Table></CardContent></Card>
    <Dialog open={showCreate} onOpenChange={setShowCreate}><DialogContent><DialogHeader><DialogTitle>Create Pipeline</DialogTitle></DialogHeader><div className="space-y-4"><div><Label>Name</Label><Input value={newPipeline.name} onChange={e => setNewPipeline(p => ({...p, name: e.target.value}))} /></div><div><Label>Repository URL</Label><Input value={newPipeline.repo_url} onChange={e => setNewPipeline(p => ({...p, repo_url: e.target.value}))} placeholder="https://github.com/org/repo" /></div><div className="grid grid-cols-2 gap-4"><div><Label>Branch</Label><Input value={newPipeline.branch} onChange={e => setNewPipeline(p => ({...p, branch: e.target.value}))} /></div><div><Label>Description</Label><Input value={newPipeline.description} onChange={e => setNewPipeline(p => ({...p, description: e.target.value}))} /></div></div></div><DialogFooter><Button variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button><Button onClick={createPipeline}>Create</Button></DialogFooter></DialogContent></Dialog></div>);
}

export function DriftDetectorPage() {
  const [scans, setScans] = useState<any[]>([]);
  const [selectedScan, setSelectedScan] = useState<any>(null);
  const [scanning, setScanning] = useState(false);
  const { toast } = useToast();

  useEffect(() => { fetch("/api/v1/drift/scans").then(r => r.json()).then(setScans).catch(() => {}); }, []);

  const runScan = async () => {
    setScanning(true);
    try {
      const resp = await fetch("/api/v1/drift/scan", { method: "POST" });
      if (resp.ok) { const d = await resp.json(); setScans(prev => [d, ...prev]); setSelectedScan(d); toast({ title: "Scan Complete", description: `${d.drifted_resources} drifted resources found` }); }
    } catch (e) { toast({ title: "Error", variant: "destructive" }); } finally { setScanning(false); }
  };

  return (<div className="space-y-6"><div className="flex items-center justify-between"><div><h1 className="text-3xl font-bold tracking-tight">Configuration Drift Detector</h1><p className="text-muted-foreground">Detect configuration drift between desired and actual state</p></div><Button onClick={runScan} disabled={scanning}><ArrowUpDown className="mr-2 h-4 w-4" />{scanning ? "Scanning..." : "Run Drift Scan"}</Button></div>
    <div className="grid grid-cols-4 gap-4">{scans.length > 0 && <><Card><CardHeader className="pb-2"><CardTitle className="text-sm">Total Resources</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{scans[0]?.total_resources || 0}</div></CardContent></Card><Card><CardHeader className="pb-2"><CardTitle className="text-sm">Drifted</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-red-600">{scans[0]?.drifted_resources || 0}</div></CardContent></Card><Card><CardHeader className="pb-2"><CardTitle className="text-sm">Compliant</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-green-600">{scans[0]?.compliant_resources || 0}</div></CardContent></Card><Card><CardHeader className="pb-2"><CardTitle className="text-sm">Compliance %</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{scans[0]?.total_resources > 0 ? ((scans[0]?.compliant_resources / scans[0]?.total_resources) * 100).toFixed(1) : 0}%</div></CardContent></Card></>}</div>
    <Card><CardHeader><CardTitle>Drift Details</CardTitle></CardHeader><CardContent>{selectedScan ? <Table><TableHeader><TableRow><TableHead>Resource</TableHead><TableHead>Field</TableHead><TableHead>Expected</TableHead><TableHead>Actual</TableHead><TableHead>Severity</TableHead><TableHead>Status</TableHead></TableRow></TableHeader><TableBody>{selectedScan.drifts?.map((d: any) => <TableRow key={d.drift_id}><TableCell className="font-mono text-xs">{d.resource_id}</TableCell><TableCell>{d.field}</TableCell><TableCell className="font-mono text-xs">{d.expected}</TableCell><TableCell className="font-mono text-xs">{d.actual}</TableCell><TableCell><Badge className={d.severity === "critical" ? "bg-red-100 text-red-800" : d.severity === "high" ? "bg-orange-100 text-orange-800" : "bg-yellow-100 text-yellow-800"}>{d.severity}</Badge></TableCell><TableCell><Badge variant="outline">{d.status}</Badge></TableCell></TableRow>)}</TableBody></Table> : <div className="text-center py-8 text-muted-foreground">Run a scan to see drift details</div>}</CardContent></Card></div>);
}

export function QuotaManagementPage() {
  const [quotas, setQuotas] = useState<any[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const { toast } = useToast();

  useEffect(() => { fetch("/api/v1/quotas").then(r => r.json()).then(setQuotas).catch(() => {}); }, []);

  const createQuota = async () => {
    try {
      const resp = await fetch("/api/v1/quotas", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ name: "New Quota", entity_type: "team", entity_id: "team-1", limits: {cpu_cores: 8, memory_gb: 32, containers: 10, storage_gb: 500} }) });
      if (resp.ok) { const d = await resp.json(); setQuotas(prev => [...prev, d]); setShowCreate(false); toast({ title: "Quota Created" }); }
    } catch (e) { toast({ title: "Error", variant: "destructive" }); }
  };

  return (<div className="space-y-6"><div className="flex items-center justify-between"><div><h1 className="text-3xl font-bold tracking-tight">Resource Quota Management</h1><p className="text-muted-foreground">Hierarchical resource quotas per team/project</p></div><Button onClick={createQuota}><Sliders className="mr-2 h-4 w-4" /> Create Quota</Button></div>
    <Card><CardHeader><CardTitle>Quotas <Badge variant="secondary">{quotas.length}</Badge></CardTitle></CardHeader><CardContent><Table><TableHeader><TableRow><TableHead>Name</TableHead><TableHead>Type</TableHead><TableHead>CPU</TableHead><TableHead>Memory</TableHead><TableHead>Containers</TableHead><TableHead>Storage</TableHead><TableHead>Status</TableHead></TableRow></TableHeader><TableBody>{quotas.map(q => <TableRow key={q.quota_id}><TableCell className="font-medium">{q.name}</TableCell><TableCell>{q.entity_type}</TableCell><TableCell>{q.limits?.cpu_cores || "-"} cores</TableCell><TableCell>{q.limits?.memory_gb || "-"} GB</TableCell><TableCell>{q.limits?.containers || "-"}</TableCell><TableCell>{q.limits?.storage_gb || "-"} GB</TableCell><TableCell><Badge variant={q.status === "active" ? "default" : "secondary"}>{q.status}</Badge></TableCell></TableRow>)}</TableBody></Table></CardContent></Card></div>);
}

export function RunbookLibraryPage() {
  const [templates, setTemplates] = useState<any[]>([]);
  const [categories] = useState(["incident_response", "maintenance", "deployment", "monitoring", "backup_restore", "security", "networking", "storage"]);
  const [selectedCategory, setSelectedCategory] = useState("");
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    const params = selectedCategory ? `?category=${selectedCategory}` : "";
    fetch(`/api/v1/runbook-templates${params}`).then(r => r.json()).then(setTemplates).catch(() => {});
  }, [selectedCategory]);

  const instantiate = async (templateId: string) => {
    try {
      const resp = await fetch(`/api/v1/runbook-templates/${templateId}/instantiate`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ variables: {}, initiated_by: "current_user" }) });
      if (resp.ok) { const d = await resp.json(); alert(`Runbook instantiated: ${d.instance_id}`); }
    } catch (e) {}
  };

  const filteredTemplates = searchQuery ? templates.filter(t => t.name?.toLowerCase().includes(searchQuery.toLowerCase()) || t.description?.toLowerCase().includes(searchQuery.toLowerCase())) : templates;

  return (<div className="space-y-6"><div className="flex items-center justify-between"><div><h1 className="text-3xl font-bold tracking-tight">Runbook Templates Library</h1><p className="text-muted-foreground">Community-contributed operational runbook templates</p></div><Input className="max-w-xs" placeholder="Search templates..." value={searchQuery} onChange={e => setSearchQuery(e.target.value)} /></div>
    <div className="flex gap-2 flex-wrap">{categories.map(c => <Badge key={c} variant={selectedCategory === c ? "default" : "outline"} className="cursor-pointer" onClick={() => setSelectedCategory(selectedCategory === c ? "" : c)}>{c.replace(/_/g, " ")}</Badge>)}</div>
    <div className="grid grid-cols-3 gap-4">{filteredTemplates.map((t: any) => <Card key={t.template_id} className="hover:border-primary"><CardHeader className="pb-2"><div className="flex items-start justify-between"><div><CardTitle className="text-sm">{t.name}</CardTitle><CardDescription className="text-xs mt-1">{t.description}</CardDescription></div><Badge variant="outline" className="text-xs">{t.difficulty}</Badge></div></CardHeader><CardContent><div className="flex items-center gap-2 text-xs text-muted-foreground mb-2"><Badge variant="secondary">{t.category}</Badge><span>v{t.version}</span><span>by {t.author}</span></div><div className="flex items-center gap-2 text-xs text-muted-foreground"><span>{(t.rating || 0).toFixed(1)} ★</span><span>{t.usage_count || 0} uses</span><span>{t.steps?.length || 0} steps</span><span>{t.estimated_duration}</span></div><div className="flex flex-wrap gap-1 mt-2">{t.tags?.map((tag: string) => <Badge key={tag} variant="outline" className="text-xs">{tag}</Badge>)}</div><div className="mt-3"><Button size="sm" className="w-full" onClick={() => instantiate(t.template_id)}><Play className="mr-1 h-3 w-3" /> Use Runbook</Button></div></CardContent></Card>)}</div></div>);
}

export function ChaosEngineeringPage() {
  const [experiments, setExperiments] = useState<any[]>([]);
  const [faultTypes, setFaultTypes] = useState<any[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    fetch("/api/v1/chaos/experiments").then(r => r.json()).then(setExperiments).catch(() => {});
    fetch("/api/v1/chaos/fault-types").then(r => r.json()).then(setFaultTypes).catch(() => {});
  }, []);

  const runExperiment = async (experimentId: string) => {
    try {
      const resp = await fetch(`/api/v1/chaos/experiments/${experimentId}/run`, { method: "POST" });
      if (resp.ok) { toast({ title: "Experiment Running", description: "Injecting faults..." }); }
    } catch (e) { toast({ title: "Error", variant: "destructive" }); }
  };

  const stopExperiment = async (experimentId: string) => {
    try {
      const resp = await fetch(`/api/v1/chaos/experiments/${experimentId}/stop`, { method: "POST" });
      if (resp.ok) { toast({ title: "Experiment Stopped" }); }
    } catch (e) { toast({ title: "Error", variant: "destructive" }); }
  };

  return (<div className="space-y-6"><div className="flex items-center justify-between"><div><h1 className="text-3xl font-bold tracking-tight">Chaos Engineering Toolkit</h1><p className="text-muted-foreground">Controlled fault injection for resilience testing</p></div><Button onClick={() => setShowCreate(true)}><Bug className="mr-2 h-4 w-4" /> New Experiment</Button></div>
    <Tabs defaultValue="experiments"><TabsList><TabsTrigger value="experiments">Experiments</TabsTrigger><TabsTrigger value="faults">Fault Types</TabsTrigger><TabsTrigger value="active">Active Faults</TabsTrigger></TabsList>
    <TabsContent value="experiments"><Table><TableHeader><TableRow><TableHead>Name</TableHead><TableHead>Target</TableHead><TableHead>Faults</TableHead><TableHead>Status</TableHead><TableHead>Actions</TableHead></TableRow></TableHeader><TableBody>{experiments.map(e => <TableRow key={e.experiment_id}><TableCell className="font-medium">{e.name}</TableCell><TableCell className="font-mono text-xs">{e.target?.type}:{e.target?.selector}</TableCell><TableCell>{e.faults?.length}</TableCell><TableCell><Badge variant={e.status === "running" ? "destructive" : e.status === "completed" ? "default" : "secondary"}>{e.status}</Badge></TableCell><TableCell><div className="flex gap-2">{e.status !== "running" ? <Button size="sm" onClick={() => runExperiment(e.experiment_id)}><Play className="h-3 w-3" /></Button> : <Button size="sm" variant="destructive" onClick={() => stopExperiment(e.experiment_id)}><Square className="h-3 w-3" /></Button>}</div></TableCell></TableRow>)}</TableBody></Table></TabsContent>
    <TabsContent value="faults"><Card><CardContent className="pt-6"><div className="grid grid-cols-2 gap-4">{faultTypes.map((f: any) => <div key={f.id} className="p-4 border rounded-lg"><div className="flex items-center gap-2"><Badge variant="outline">{f.category}</Badge><h3 className="font-medium">{f.name}</h3></div><p className="text-sm text-muted-foreground mt-1">{f.description}</p><div className="text-xs text-muted-foreground mt-2">Parameters: {f.parameters?.map((p: any) => p.name).join(", ")}</div></div>)}</div></CardContent></Card></TabsContent></Tabs></div>);
}

export function SelfHealingPage() {
  const [status, setStatus] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [patterns, setPatterns] = useState<any[]>([]);
  const { toast } = useToast();

  useEffect(() => {
    fetch("/api/v1/healing/status").then(r => r.json()).then(setStatus).catch(() => {});
    fetch("/api/v1/healing/history?limit=50").then(r => r.json()).then(setHistory).catch(() => {});
    fetch("/api/v1/healing/patterns").then(r => r.json()).then(setPatterns).catch(() => {});
  }, []);

  const triggerHealing = async () => {
    try {
      const resp = await fetch("/api/v1/healing/remediate", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ context: { container: { cpu_percent: 90, memory_percent: 85, health: "unhealthy", restart_count: 6 } } }) });
      if (resp.ok) { const d = await resp.json(); toast({ title: `Action: ${d.action}`, description: d.remediation }); }
    } catch (e) { toast({ title: "Error", variant: "destructive" }); }
  };

  const retrainModel = async () => {
    try { const resp = await fetch("/api/v1/healing/retrain", { method: "POST" }); if (resp.ok) { toast({ title: "Model Retrained" }); } }
    catch (e) { toast({ title: "Error", variant: "destructive" }); }
  };

  return (<div className="space-y-6"><div className="flex items-center justify-between"><div><h1 className="text-3xl font-bold tracking-tight">Self-Healing Infrastructure</h1><p className="text-muted-foreground">AI-driven auto-remediation learning loop</p></div><div className="flex gap-2"><Button onClick={triggerHealing}><Zap className="mr-2 h-4 w-4" /> Test Healing</Button><Button variant="outline" onClick={retrainModel}><RefreshCw className="mr-2 h-4 w-4" /> Retrain</Button></div></div>
    {status && <div className="grid grid-cols-5 gap-4">
      <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Total Remediations</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{status.total_remediations}</div></CardContent></Card>
      <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Success Rate</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-green-600">{status.success_rate}%</div></CardContent></Card>
      <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Patterns</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{status.patterns_detected}</div></CardContent></Card>
      <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Learned Actions</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{status.model_learned_actions}</div></CardContent></Card>
      <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Auto-Healing</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{status.auto_remediation_enabled ? "ON" : "OFF"}</div></CardContent></Card>
    </div>}
    <Tabs defaultValue="history"><TabsList><TabsTrigger value="history">Remediation History</TabsTrigger><TabsTrigger value="patterns">Detected Patterns</TabsTrigger><TabsTrigger value="learned">Learned Actions</TabsTrigger></TabsList>
    <TabsContent value="history"><Table><TableHeader><TableRow><TableHead>Pattern</TableHead><TableHead>Action</TableHead><TableHead>Result</TableHead><TableHead>Confidence</TableHead><TableHead>Time</TableHead></TableRow></TableHeader><TableBody>{history.map((h: any) => <TableRow key={h.remediation_id}><TableCell><Badge variant="outline">{h.detected_pattern}</Badge></TableCell><TableCell className="font-mono text-xs">{h.action_taken}</TableCell><TableCell><Badge className={h.result?.success ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}>{h.result?.success ? "Success" : "Failed"}</Badge></TableCell><TableCell>{(h.confidence * 100).toFixed(0)}%</TableCell><TableCell className="text-xs">{new Date(h.timestamp).toLocaleString()}</TableCell></TableRow>)}</TableBody></Table></TabsContent>
    <TabsContent value="patterns"><div className="grid grid-cols-2 gap-4">{patterns.map((p: any) => <Card key={p.pattern}><CardHeader className="pb-2"><CardTitle className="text-sm">{p.pattern.replace(/_/g, " ")}</CardTitle></CardHeader><CardContent><div className="text-xs text-muted-foreground"><p>Recommended: {p.recommended_action}</p><p>Success Rate: {(p.avg_success_rate * 100).toFixed(0)}%</p><p>Detected: {p.detection_count} times</p></div></CardContent></Card>)}</div></TabsContent></Tabs></div>);
}
