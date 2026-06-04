import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const TEMPLATES = [
  { name: "microservice-fastapi", label: "Microservice (FastAPI)", lang: "python", desc: "Production-ready FastAPI microservice with CI/CD" },
  { name: "service-node-express", label: "Node.js Express Service", lang: "typescript", desc: "REST API with TypeScript and monitoring" },
  { name: "event-processor-go", label: "Event Processor (Go)", lang: "go", desc: "Go event processor with Kafka integration" },
  { name: "data-pipeline-python", label: "Data Pipeline (Python)", lang: "python", desc: "Python data pipeline with Airflow and dbt" },
];

const STEPS = ["repo_creation", "ci_cd_setup", "cloud_resources", "monitoring", "on_call_config", "documentation"];

export default function GoldenPathScaffolder() {
  const [selectedTemplate, setSelectedTemplate] = useState("");
  const [serviceName, setServiceName] = useState("");
  const [owner, setOwner] = useState("");
  const [scaffolds, setScaffolds] = useState<any[]>([]);
  const [currentStep, setCurrentStep] = useState(0);
  const [refreshKey, setRefreshKey] = useState(0);

  const handleStart = () => {
    if (!selectedTemplate || !serviceName) return;
    setScaffolds(prev => [...prev, {
      id: `s-${Date.now()}`,
      template: selectedTemplate,
      serviceName,
      owner: owner || "current-user",
      currentStep: 0,
      status: "in_progress",
      completedSteps: [],
      createdAt: new Date().toISOString(),
    }]);
    setServiceName("");
    setOwner("");
  };

  const handleAdvance = (id: string) => {
    setScaffolds(prev => prev.map(s => {
      if (s.id !== id) return s;
      const newStep = s.currentStep + 1;
      const isComplete = newStep >= STEPS.length;
      return {
        ...s,
        currentStep: isComplete ? s.currentStep : newStep,
        completedSteps: [...s.completedSteps, STEPS[s.currentStep]],
        status: isComplete ? "completed" : "in_progress",
      };
    }));
    setRefreshKey(k => k + 1);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Golden Path Scaffolder</h1>
        <Badge variant="outline" className="text-sm">Guided Service Creation</Badge>
      </div>

      <Card>
        <CardHeader><CardTitle>Start New Scaffold</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-3">
            <div><label className="text-sm font-medium">Template</label>
              <Select value={selectedTemplate} onValueChange={setSelectedTemplate}>
                <SelectTrigger><SelectValue placeholder="Select template..." /></SelectTrigger>
                <SelectContent>{TEMPLATES.map(t => <SelectItem key={t.name} value={t.name}>{t.label}</SelectItem>)}</SelectContent>
              </Select>
            </div>
            <div><label className="text-sm font-medium">Service Name</label><Input value={serviceName} onChange={e => setServiceName(e.target.value)} placeholder="my-new-service" /></div>
            <div><label className="text-sm font-medium">Owner</label><Input value={owner} onChange={e => setOwner(e.target.value)} placeholder="team or email" /></div>
          </div>
          <Button onClick={handleStart} disabled={!selectedTemplate || !serviceName}>Start Scaffold</Button>
        </CardContent>
      </Card>

      {scaffolds.length > 0 && (
        <Card>
          <CardHeader><CardTitle>Active Scaffolds</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            {scaffolds.map(s => (
              <div key={s.id} className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <div><h3 className="font-semibold">{s.serviceName}</h3><p className="text-sm text-muted-foreground">{s.template} &middot; {s.owner}</p></div>
                  <Badge>{s.status}</Badge>
                </div>
                  <div className="flex gap-2 flex-wrap items-center">
                    {STEPS.map((step, i) => (
                      <div key={step} className={`flex items-center gap-1 text-sm px-2 py-1 rounded ${i < s.completedSteps.length ? "bg-green-100 text-green-700" : i === s.currentStep ? "bg-blue-100 text-blue-700" : "bg-gray-100 text-gray-500"}`}>
                        <span>{i < s.completedSteps.length ? "✓" : i === s.currentStep ? "→" : "○"}</span>
                        <span>{step.replace(/_/g, " ")}</span>
                      </div>
                    ))}
                    {s.status !== "completed" && <Button size="sm" variant="outline" onClick={() => handleAdvance(s.id)}>Advance</Button>}
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        )}

      <Card>
        <CardHeader><CardTitle>Available Templates</CardTitle></CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            {TEMPLATES.map(t => (
              <div key={t.name} className="border rounded-lg p-4">
                <h3 className="font-semibold">{t.label}</h3>
                <p className="text-sm text-muted-foreground">{t.desc}</p>
                <Badge variant="outline" className="mt-2">{t.lang}</Badge>
                <div className="mt-2">
                  <Button size="sm" variant="outline" onClick={() => { setSelectedTemplate(t.name); }}>Use Template</Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
      {scaffolds.length > 0 && (
        <Card>
          <CardHeader><CardTitle>Summary</CardTitle></CardHeader>
          <CardContent>
            <div className="grid gap-3 md:grid-cols-3">
              <div className="border rounded-lg p-3 text-center"><p className="text-sm text-muted-foreground">Total</p><p className="text-2xl font-bold">{scaffolds.length}</p></div>
              <div className="border rounded-lg p-3 text-center"><p className="text-sm text-muted-foreground">Completed</p><p className="text-2xl font-bold text-green-500">{scaffolds.filter(s => s.status === "completed").length}</p></div>
              <div className="border rounded-lg p-3 text-center"><p className="text-sm text-muted-foreground">In Progress</p><p className="text-2xl font-bold text-blue-500">{scaffolds.filter(s => s.status === "in_progress").length}</p></div>
            </div>
          </CardContent>
        </Card>
      )}

      {selectedTemplate && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Launch: {selectedTemplate}</CardTitle>
              <Button variant="ghost" size="sm" onClick={() => setSelectedTemplate(null)}>Close</Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <Input placeholder="Service name" />
              <Input placeholder="Owner/team" />
              <select className="border rounded px-2 py-1 w-full text-sm">
                <option>Select language...</option>
                <option>python</option>
                <option>typescript</option>
                <option>go</option>
                <option>rust</option>
              </select>
              <div className="flex gap-2">
                <Button>Launch Scaffold</Button>
                <Button variant="outline" onClick={() => setSelectedTemplate(null)}>Cancel</Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader><CardTitle>Template Management</CardTitle></CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="border rounded-lg p-4">
              <p className="font-medium text-sm">Validate Template</p>
              <div className="mt-2 flex gap-2">
                <Input placeholder="Template name..." className="flex-1" />
                <Button variant="outline" size="sm">Validate</Button>
              </div>
            </div>
            <div className="border rounded-lg p-4">
              <p className="font-medium text-sm">Estimate Duration</p>
              <div className="mt-2 flex gap-2">
                <Input placeholder="Template name..." className="flex-1" />
                <Button variant="outline" size="sm">Estimate</Button>
              </div>
            </div>
          </div>
          <div className="mt-4 flex gap-2">
            <Button variant="outline" size="sm">Analytics</Button>
            <Button variant="outline" size="sm">Add Custom Step</Button>
            <Button variant="outline" size="sm">Add Approval Flow</Button>
            <Button variant="outline" size="sm">Bulk Retire Instances</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
