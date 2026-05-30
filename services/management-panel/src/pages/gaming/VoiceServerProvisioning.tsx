import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Mic, Headphones, Volume2, Users, Globe, Settings, Plus, Play, Pause, Power, Radio, Activity } from 'lucide-react';

interface VoiceServer {
  server_id: string;
  name: string;
  type: string;
  region: string;
  host: string;
  port: number;
  max_slots: number;
  used_slots: number;
  status: string;
  bitrate: number;
  version: string;
  uptime: string;
  monthly_cost: number;
}

const mockServers: VoiceServer[] = [
  { server_id: 'ts-001', name: 'Main Gaming TS', type: 'teamspeak3', region: 'NA-East', host: 'ts01.infrapilot.io', port: 9987, max_slots: 100, used_slots: 67, status: 'online', bitrate: 48, version: '3.13.7', uptime: '45d 12h', monthly_cost: 15.99 },
  { server_id: 'ts-002', name: 'EU Competitive', type: 'teamspeak3', region: 'EU-West', host: 'ts02.infrapilot.io', port: 9987, max_slots: 50, used_slots: 42, status: 'online', bitrate: 64, version: '3.13.7', uptime: '30d 8h', monthly_cost: 9.99 },
  { server_id: 'mu-001', name: 'Community Mumble', type: 'mumble', region: 'NA-West', host: 'mu01.infrapilot.io', port: 64738, max_slots: 75, used_slots: 31, status: 'online', bitrate: 56, version: '1.4.287', uptime: '90d 3h', monthly_cost: 12.50 },
  { server_id: 'ts-003', name: 'Stream Team VC', type: 'teamspeak3', region: 'NA-East', host: 'ts03.infrapilot.io', port: 9987, max_slots: 25, used_slots: 8, status: 'online', bitrate: 96, version: '3.13.7', uptime: '12d 6h', monthly_cost: 4.99 },
  { server_id: 'mu-002', name: 'Dev Team Mumble', type: 'mumble', region: 'EU-West', host: 'mu02.infrapilot.io', port: 64738, max_slots: 15, used_slots: 6, status: 'offline', bitrate: 48, version: '1.4.287', uptime: '0d 0h', monthly_cost: 2.99 },
];

const VoiceServerProvisioning: React.FC = () => {
  const [servers, setServers] = useState<VoiceServer[]>(mockServers);
  const [selectedServer, setSelectedServer] = useState<VoiceServer | null>(null);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [newServer, setNewServer] = useState({ name: '', type: 'teamspeak3', region: 'NA-East', max_slots: 50, bitrate: 48 });

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Voice Server Provisioning</h1>
          <p className="text-muted-foreground">TeamSpeak3 / Mumble server management with slot allocation</p>
        </div>
        <Button onClick={() => setIsCreateOpen(true)}><Plus className="mr-2 h-4 w-4" />Provision Server</Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Total Servers</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{servers.length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Online</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-green-500">{servers.filter(s => s.status === 'online').length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Active Users</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{servers.reduce((s, sv) => s + sv.used_slots, 0)}/{servers.reduce((s, sv) => s + sv.max_slots, 0)}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Monthly Cost</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">${servers.reduce((s, sv) => s + sv.monthly_cost, 0).toFixed(2)}</div></CardContent></Card>
      </div>

      <Card>
        <CardHeader><CardTitle>Voice Servers</CardTitle></CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Host</TableHead>
                <TableHead>Slots</TableHead>
                <TableHead>Bitrate</TableHead>
                <TableHead>Uptime</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {servers.map(sv => (
                <TableRow key={sv.server_id}>
                  <TableCell className="font-medium">
                    <div className="flex items-center gap-2">
                      {sv.type === 'teamspeak3' ? <Headphones className="h-4 w-4 text-blue-500" /> : <Mic className="h-4 w-4 text-green-500" />}
                      {sv.name}
                    </div>
                  </TableCell>
                  <TableCell><Badge variant="outline">{sv.type}</Badge></TableCell>
                  <TableCell className="text-xs">{sv.host}:{sv.port}</TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Progress value={(sv.used_slots / sv.max_slots) * 100} className="w-16" />
                      <span className="text-xs">{sv.used_slots}/{sv.max_slots}</span>
                    </div>
                  </TableCell>
                  <TableCell>{sv.bitrate} kbps</TableCell>
                  <TableCell className="text-xs">{sv.uptime}</TableCell>
                  <TableCell>
                    <Badge variant={sv.status === 'online' ? 'default' : 'secondary'}>{sv.status}</Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex gap-1">
                      <Button size="sm" variant="ghost" onClick={() => setSelectedServer(sv)}><Settings className="h-4 w-4" /></Button>
                      <Button size="sm" variant={sv.status === 'online' ? 'destructive' : 'default'}>
                        <Power className="h-4 w-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>Provision Voice Server</DialogTitle></DialogHeader>
          <div className="space-y-4">
            <div><Label>Server Name</Label><Input value={newServer.name} onChange={e => setNewServer({ ...newServer, name: e.target.value })} placeholder="My Voice Server" /></div>
            <div><Label>Type</Label><select className="w-full p-2 rounded-md border" value={newServer.type} onChange={e => setNewServer({ ...newServer, type: e.target.value })}><option value="teamspeak3">TeamSpeak 3</option><option value="mumble">Mumble</option></select></div>
            <div><Label>Region</Label><select className="w-full p-2 rounded-md border" value={newServer.region} onChange={e => setNewServer({ ...newServer, region: e.target.value })}><option value="NA-East">NA East</option><option value="NA-West">NA West</option><option value="EU-West">EU West</option><option value="EU-East">EU East</option></select></div>
            <div className="grid grid-cols-2 gap-2"><div><Label>Max Slots</Label><Input type="number" value={newServer.max_slots} onChange={e => setNewServer({ ...newServer, max_slots: parseInt(e.target.value) || 50 })} /></div><div><Label>Bitrate (kbps)</Label><Input type="number" value={newServer.bitrate} onChange={e => setNewServer({ ...newServer, bitrate: parseInt(e.target.value) || 48 })} /></div></div>
            <Button className="w-full" onClick={() => { setServers([...servers, { server_id: `sv-${Date.now()}`, ...newServer, host: `${newServer.name.toLowerCase().replace(/\s/g, '-')}.infrapilot.io`, port: newServer.type === 'teamspeak3' ? 9987 : 64738, used_slots: 0, status: 'provisioning', version: newServer.type === 'teamspeak3' ? '3.13.7' : '1.4.287', uptime: '0d 0h', monthly_cost: newServer.max_slots <= 25 ? 4.99 : newServer.max_slots <= 50 ? 9.99 : newServer.max_slots <= 100 ? 15.99 : 29.99 }]); setIsCreateOpen(false); }}>Provision</Button>
          </div>
        </DialogContent>
      </Dialog>

      <Dialog open={!!selectedServer} onOpenChange={() => setSelectedServer(null)}>
        <DialogContent className="sm:max-w-[400px]">
          <DialogHeader><DialogTitle>{selectedServer?.name}</DialogTitle></DialogHeader>
          {selectedServer && (
            <div className="space-y-4">
              <div className="flex items-center gap-4 p-3 rounded-lg bg-muted">
                {selectedServer.type === 'teamspeak3' ? <Headphones className="h-8 w-8 text-blue-500" /> : <Mic className="h-8 w-8 text-green-500" />}
                <div><div className="font-bold">{selectedServer.host}:{selectedServer.port}</div><div className="text-xs text-muted-foreground">{selectedServer.type} v{selectedServer.version}</div></div>
              </div>
              <div className="grid grid-cols-2 gap-2 text-sm"><div><strong>Region:</strong> {selectedServer.region}</div><div><strong>Bitrate:</strong> {selectedServer.bitrate} kbps</div><div><strong>Uptime:</strong> {selectedServer.uptime}</div><div><strong>Cost:</strong> ${selectedServer.monthly_cost}/mo</div></div>
              <div><Label>Slots Usage</Label><Progress value={(selectedServer.used_slots / selectedServer.max_slots) * 100} className="h-3 mt-1" /><div className="text-xs text-right mt-1">{selectedServer.used_slots}/{selectedServer.max_slots} used</div></div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default VoiceServerProvisioning;
