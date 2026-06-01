import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
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
import { Gamepad2, Users, Server, Cpu, MemoryStick, HardDrive, Activity, Wifi, Zap, TrendingUp, Clock, Thermometer } from 'lucide-react';

interface GameServer {
  server_id: string;
  name: string;
  game: string;
  map: string;
  version: string;
  players: number;
  max_players: number;
  tps: number;
  mspt: number;
  cpu_percent: number;
  ram_percent: number;
  ram_used_gb: number;
  ram_total_gb: number;
  uptime: string;
  status: string;
  region: string;
  entities: number;
  chunks: number;
}

const mockServers: GameServer[] = [
  { server_id: 'mc-survival-01', name: 'Survival World', game: 'minecraft', map: 'world', version: '1.21', players: 45, max_players: 100, tps: 20.0, mspt: 18.5, cpu_percent: 45, ram_percent: 62, ram_used_gb: 4.9, ram_total_gb: 8, uptime: '12d 8h', status: 'online', region: 'NA-East', entities: 3450, chunks: 892 },
  { server_id: 'mc-pvp-01', name: 'PvP Arena #1', game: 'minecraft', map: 'arena_1', version: '1.21', players: 32, max_players: 50, tps: 20.0, mspt: 22.1, cpu_percent: 55, ram_percent: 48, ram_used_gb: 3.8, ram_total_gb: 8, uptime: '30d 5h', status: 'online', region: 'NA-East', entities: 1200, chunks: 450 },
  { server_id: 'mc-minigames-01', name: 'Minigames Hub', game: 'minecraft', map: 'hub', version: '1.21', players: 78, max_players: 200, tps: 19.8, mspt: 28.3, cpu_percent: 70, ram_percent: 75, ram_used_gb: 6.0, ram_total_gb: 8, uptime: '45d 2h', status: 'online', region: 'NA-East', entities: 5200, chunks: 320 },
  { server_id: 'mc-events-01', name: 'Event Server', game: 'minecraft', map: 'events', version: '1.21', players: 0, max_players: 50, tps: 0, mspt: 0, cpu_percent: 5, ram_percent: 15, ram_used_gb: 1.2, ram_total_gb: 8, uptime: '2d 4h', status: 'idle', region: 'NA-West', entities: 50, chunks: 180 },
  { server_id: 'mc-survival-02', name: 'Survival World EU', game: 'minecraft', map: 'world_eu', version: '1.20.6', players: 28, max_players: 80, tps: 20.0, mspt: 15.2, cpu_percent: 35, ram_percent: 55, ram_used_gb: 4.4, ram_total_gb: 8, uptime: '8d 12h', status: 'online', region: 'EU-West', entities: 2100, chunks: 654 },
  { server_id: 'mc-creative-01', name: 'Creative World', game: 'minecraft', map: 'creative', version: '1.21', players: 12, max_players: 30, tps: 20.0, mspt: 12.8, cpu_percent: 25, ram_percent: 35, ram_used_gb: 2.8, ram_total_gb: 8, uptime: '60d 0h', status: 'online', region: 'NA-East', entities: 890, chunks: 1200 },
];

const GameServerDashboard: React.FC = () => {
  const [servers, setServers] = useState<GameServer[]>(mockServers);
  const [selectedServer, setSelectedServer] = useState<GameServer | null>(null);

  const onlineCount = servers.filter(s => s.status === 'online').length;
  const totalPlayers = servers.reduce((s, sv) => s + sv.players, 0);
  const avgTps = servers.filter(s => s.tps > 0).reduce((s, sv) => s + sv.tps, 0) / servers.filter(s => s.tps > 0).length;

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Game Server Dashboard</h1>
          <p className="text-muted-foreground">Live TPS, players, memory, uptime monitoring for all game servers</p>
        </div>
        <Badge variant="secondary" className="text-sm"><Activity className="mr-1 h-4 w-4" />{totalPlayers} players</Badge>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Online</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-green-500">{onlineCount}/{servers.length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Total Players</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{totalPlayers}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Avg TPS</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{avgTps.toFixed(1)}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Avg MSPT</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{(servers.filter(s => s.mspt > 0).reduce((s, sv) => s + sv.mspt, 0) / servers.filter(s => s.mspt > 0).length).toFixed(1)}ms</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Total Entities</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{servers.reduce((s, sv) => s + sv.entities, 0).toLocaleString()}</div></CardContent></Card>
      </div>

      <Card>
        <CardHeader><CardTitle>Server Status</CardTitle></CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Server</TableHead>
                <TableHead>Game</TableHead>
                <TableHead>Version</TableHead>
                <TableHead>Players</TableHead>
                <TableHead>TPS</TableHead>
                <TableHead>MSPT</TableHead>
                <TableHead>CPU</TableHead>
                <TableHead>RAM</TableHead>
                <TableHead>Uptime</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {servers.map(sv => (
                <TableRow key={sv.server_id} className="cursor-pointer" onClick={() => setSelectedServer(sv)}>
                  <TableCell className="font-medium">{sv.name}</TableCell>
                  <TableCell><Gamepad2 className="h-4 w-4 inline mr-1" />{sv.game}</TableCell>
                  <TableCell className="text-xs">{sv.version}</TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Users className="h-4 w-4" />
                      <span className={sv.players >= sv.max_players * 0.8 ? 'text-yellow-500 font-bold' : ''}>{sv.players}</span>
                      <span className="text-muted-foreground">/{sv.max_players}</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <span className={sv.tps < 20 ? 'text-yellow-500' : 'text-green-500'}>{sv.tps.toFixed(1)}</span>
                  </TableCell>
                  <TableCell>
                    <Badge variant={sv.mspt > 40 ? 'destructive' : sv.mspt > 30 ? 'secondary' : 'outline'} className="text-xs">{sv.mspt.toFixed(1)}ms</Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Progress value={sv.cpu_percent} className="w-16" />
                      <span className="text-xs">{sv.cpu_percent}%</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Progress value={sv.ram_percent} className="w-16" />
                      <span className="text-xs">{sv.ram_used_gb.toFixed(1)}/{sv.ram_total_gb}GB</span>
                    </div>
                  </TableCell>
                  <TableCell className="text-xs">{sv.uptime}</TableCell>
                  <TableCell>
                    <Badge variant={sv.status === 'online' ? 'default' : 'secondary'}>{sv.status}</Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Dialog open={!!selectedServer} onOpenChange={() => setSelectedServer(null)}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader><DialogTitle>{selectedServer?.name}</DialogTitle></DialogHeader>
          {selectedServer && (
            <div className="space-y-4">
              <div className="flex gap-2">
                <Badge>{selectedServer.game}</Badge>
                <Badge variant="outline">{selectedServer.version}</Badge>
                <Badge variant="secondary">{selectedServer.region}</Badge>
                <Badge variant={selectedServer.status === 'online' ? 'default' : 'secondary'}>{selectedServer.status}</Badge>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <span className="text-xs text-muted-foreground">TPS</span>
                  <div className="text-2xl font-bold" style={{ color: selectedServer.tps >= 19.5 ? '#22c55e' : '#eab308' }}>{selectedServer.tps.toFixed(1)}</div>
                </div>
                <div className="space-y-1">
                  <span className="text-xs text-muted-foreground">MSPT</span>
                  <div className="text-2xl font-bold" style={{ color: selectedServer.mspt < 25 ? '#22c55e' : selectedServer.mspt < 40 ? '#eab308' : '#ef4444' }}>{selectedServer.mspt.toFixed(1)}ms</div>
                </div>
                <div className="space-y-1">
                  <span className="text-xs text-muted-foreground">CPU</span>
                  <Progress value={selectedServer.cpu_percent} className="h-2" />
                  <div className="text-xs text-right">{selectedServer.cpu_percent}%</div>
                </div>
                <div className="space-y-1">
                  <span className="text-xs text-muted-foreground">RAM</span>
                  <Progress value={selectedServer.ram_percent} className="h-2" />
                  <div className="text-xs text-right">{selectedServer.ram_used_gb.toFixed(1)} / {selectedServer.ram_total_gb} GB</div>
                </div>
              </div>
              <div className="grid grid-cols-3 gap-2 text-sm p-3 rounded-lg bg-muted">
                <div className="text-center"><div className="font-bold">{selectedServer.entities.toLocaleString()}</div><div className="text-xs text-muted-foreground">Entities</div></div>
                <div className="text-center"><div className="font-bold">{selectedServer.chunks.toLocaleString()}</div><div className="text-xs text-muted-foreground">Chunks</div></div>
                <div className="text-center"><div className="font-bold">{selectedServer.uptime}</div><div className="text-xs text-muted-foreground">Uptime</div></div>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" className="flex-1">Console</Button>
                <Button variant="outline" className="flex-1">Restart</Button>
                <Button variant="destructive" className="flex-1">Stop</Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default GameServerDashboard;
