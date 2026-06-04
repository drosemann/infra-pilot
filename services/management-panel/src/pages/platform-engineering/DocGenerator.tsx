import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const mockDocs = [
  { id: "doc1", title: "User Service Architecture", type: "architecture", service: "user-service", format: "markdown", words: 2450, version: 3, updatedAt: "2026-05-28" },
  { id: "doc2", title: "Payment System Context", type: "system_context", service: "payment-api", format: "markdown", words: 890, version: 2, updatedAt: "2026-05-25" },
  { id: "doc3", title: "ADR-001: Database Selection", type: "adr", service: "user-service", format: "markdown", words: 1200, version: 1, updatedAt: "2026-05-20" },
  { id: "doc4", title: "Data Pipeline Architecture", type: "architecture", service: "data-pipeline", format: "html", words: 3100, version: 1, updatedAt: "2026-05-18" },
  { id: "doc5", title: "Deployment Diagram v2", type: "deployment_diagram", service: "frontend-web", format: "markdown", words: 650, version: 2, updatedAt: "2026-05-15" },
];

const adrs = [
  { id: "adr1", title: "Database Selection", status: "accepted", domain: "data", context: "Need to choose primary DB", decision: "PostgreSQL 16", updatedAt: "2026-05-20" },
  { id: "adr2", title: "Message Broker Choice", status: "proposed", domain: "infra", context: "Event-driven architecture", decision: "Kafka vs RabbitMQ", updatedAt: "2026-05-28" },
  { id: "adr3", title: "Auth Strategy", status: "accepted", domain: "security", context: "Microservices auth approach", decision: "OAuth2 + OIDC", updatedAt: "2026-05-22" },
];

function CreateAdrModal({ onClose }: { onClose: () => void }) {
  const [title, setTitle] = useState("");
  const [context, setContext] = useState("");
  const [decision, setDecision] = useState("");
  const [domain, setDomain] = useState("");
  const handleSubmit = () => {
    adrs.push({ id: `adr${Date.now()}`, title, status: "proposed", domain, context, decision, updatedAt: new Date().toISOString().slice(0, 10) });
    onClose();
  };
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={onClose}>
      <div className="bg-white dark:bg-gray-900 rounded-lg p-6 w-full max-w-md" onClick={e => e.stopPropagation()}>
        <h2 className="text-lg font-semibold mb-4">New ADR</h2>
        <div className="space-y-3">
          <Input placeholder="Title" value={title} onChange={e => setTitle(e.target.value)} />
          <textarea placeholder="Context" value={context} onChange={e => setContext(e.target.value)} className="w-full border rounded px-3 py-2 text-sm min-h-[80px]" />
          <textarea placeholder="Decision" value={decision} onChange={e => setDecision(e.target.value)} className="w-full border rounded px-3 py-2 text-sm min-h-[80px]" />
          <Input placeholder="Domain" value={domain} onChange={e => setDomain(e.target.value)} />
          <div className="flex gap-2 justify-end">
            <Button variant="outline" onClick={onClose}>Cancel</Button>
            <Button onClick={handleSubmit} disabled={!title || !context || !decision}>Create</Button>
          </div>
        </div>
      </div>
    </div>
  );
}

function GenerateDocModal({ onClose }: { onClose: () => void }) {
  const [title, setTitle] = useState("");
  const [service, setService] = useState("user-service");
  const [template, setTemplate] = useState("microservice");
  const handleSubmit = () => {
    mockDocs.push({ id: `doc${Date.now()}`, title, type: "architecture", service, format: "markdown", words: 1500, version: 1, updatedAt: new Date().toISOString().slice(0, 10) });
    onClose();
  };
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={onClose}>
      <div className="bg-white dark:bg-gray-900 rounded-lg p-6 w-full max-w-md" onClick={e => e.stopPropagation()}>
        <h2 className="text-lg font-semibold mb-4">Generate Document</h2>
        <div className="space-y-3">
          <Input placeholder="Title" value={title} onChange={e => setTitle(e.target.value)} />
          <select value={service} onChange={e => setService(e.target.value)} className="w-full border rounded px-3 py-2 text-sm"><option value="user-service">user-service</option><option value="payment-api">payment-api</option><option value="data-pipeline">data-pipeline</option><option value="frontend-web">frontend-web</option></select>
          <select value={template} onChange={e => setTemplate(e.target.value)} className="w-full border rounded px-3 py-2 text-sm"><option value="microservice">Microservice</option><option value="event-driven">Event Driven</option><option value="layered">Layered</option></select>
          <div className="flex gap-2 justify-end">
            <Button variant="outline" onClick={onClose}>Cancel</Button>
            <Button onClick={handleSubmit} disabled={!title}>Generate</Button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function DocGenerator() {
  const [selectedService, setSelectedService] = useState("");
  const [showAdr, setShowAdr] = useState(false);
  const [showGenerate, setShowGenerate] = useState(false);

  return (
    <div className="space-y-6">
      {showAdr && <CreateAdrModal onClose={() => setShowAdr(false)} />}
      {showGenerate && <GenerateDocModal onClose={() => setShowGenerate(false)} />}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Documentation Generator</h1>
        <div className="flex gap-2">
          <Badge variant="outline" className="text-sm">Auto-Generated</Badge>
          <Button size="sm" onClick={() => setShowGenerate(true)}>Generate</Button>
          <Button size="sm" variant="outline" onClick={() => setShowAdr(true)}>New ADR</Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Total Documents</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{mockDocs.length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">ADRs</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{adrs.length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Architecture Docs</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{mockDocs.filter(d => d.type === "architecture").length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Total Words</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{mockDocs.reduce((a, d) => a + d.words, 0).toLocaleString()}</div></CardContent></Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>Generate New Document</CardTitle></CardHeader>
          <CardContent className="space-y-3">
          <div><label className="text-sm">Title</label><Input placeholder="My Service Architecture" /></div>
            <div className="grid gap-3 md:grid-cols-2">
              <div><label className="text-sm">Service</label><Select><SelectTrigger><SelectValue placeholder="Select service..." /></SelectTrigger><SelectContent><SelectItem value="user-service">user-service</SelectItem><SelectItem value="payment-api">payment-api</SelectItem><SelectItem value="data-pipeline">data-pipeline</SelectItem></SelectContent></Select></div>
              <div><label className="text-sm">Template</label><Select><SelectTrigger><SelectValue placeholder="Select template..." /></SelectTrigger><SelectContent><SelectItem value="microservice">Microservice</SelectItem><SelectItem value="event-driven">Event Driven</SelectItem><SelectItem value="layered">Layered</SelectItem></SelectContent></Select></div>
            </div>
            <Button onClick={() => setShowGenerate(true)}>Generate</Button>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Recent ADRs</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            {adrs.map(adr => (
              <div key={adr.id} className="p-2 border rounded text-sm">
                <div className="flex items-center justify-between"><span className="font-medium">{adr.title}</span><Badge variant={adr.status === "accepted" ? "default" : "secondary"}>{adr.status}</Badge></div>
                <p className="text-muted-foreground">{adr.domain} &middot; {adr.decision}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader><CardTitle>Generated Documents</CardTitle></CardHeader>
        <CardContent>
          <div className="space-y-2">
            {mockDocs.map(doc => (
              <div key={doc.id} className="flex items-center justify-between p-3 border rounded-lg">
                <div><p className="font-medium">{doc.title}</p><p className="text-sm text-muted-foreground">{doc.type.replace(/_/g, " ")} &middot; {doc.service} &middot; {doc.format} &middot; {doc.words} words &middot; v{doc.version}</p></div>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-muted-foreground">{doc.updatedAt}</span>
                  <Button variant="outline" size="sm">View</Button>
                  <Button variant="ghost" size="sm">Export</Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Document Review & Collaboration</CardTitle></CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="border rounded-lg p-4">
              <p className="font-medium text-sm">Start Review</p>
              <div className="mt-2 space-y-2">
                <Input placeholder="ADR ID" />
                <Input placeholder="Reviewers (comma-separated)" />
                <Button size="sm" className="w-full">Start Review</Button>
              </div>
            </div>
            <div className="border rounded-lg p-4">
              <p className="font-medium text-sm">Document Templates</p>
              <div className="mt-2 space-y-2">
                <select className="border rounded px-2 py-1 w-full text-sm">
                  <option>Select template...</option>
                  <option>Microservice Architecture</option>
                  <option>Event-Driven Design</option>
                  <option>API Specification</option>
                </select>
                <Button variant="outline" size="sm" className="w-full">Create from Template</Button>
              </div>
            </div>
          </div>
          <div className="mt-4 flex gap-2">
            <Button variant="outline" size="sm">Search Documents</Button>
            <Button variant="outline" size="sm">Cross-Reference</Button>
            <Button variant="outline" size="sm">Content Statistics</Button>
            <Button variant="outline" size="sm">Bulk Generate</Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>ADR Review Status</CardTitle></CardHeader>
        <CardContent>
          <div className="space-y-2">
            {adrs.map(adr => (
              <div key={adr.id} className="flex items-center justify-between p-2 border rounded">
                <div className="flex-1"><p className="text-sm font-medium">{adr.title}</p><p className="text-xs text-muted-foreground">{adr.status} &middot; {adr.domain}</p></div>
                <div className="flex gap-1">
                  <Button variant="outline" size="sm">Approve</Button>
                  <Button variant="outline" size="sm" className="text-red-500">Reject</Button>
                  <Button variant="ghost" size="sm">View</Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
