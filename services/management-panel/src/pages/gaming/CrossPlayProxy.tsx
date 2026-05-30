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
import { Globe, Users, ArrowRightLeft, Server, Gamepad2, CheckCircle, AlertTriangle, Activity, Wifi, Zap } from 'lucide-react';

interface ProxyServer {
  proxy_id: string;
  name: string;
  java_host: string;
  java_port: number;
  bedrock_host: string;
  bedrock_port: number;
  region: string;
  active_players: number;
  max_players: number;
  status: string;
  protocol: string;
  latency_ms: number;
  players_java: number;
  players_bedrock: number;
  uptime: string;
}

const mockProxies: ProxyServer[] = [
  { proxy_id: 'proxy-001', name: 'Global Proxy (NA)', java_host: 'play.infrapilot.io', java_port: 25565, bedrock_host: 'bedrock.infrapilot.io', bedrock_port: 19132, region: 'NA-East', active_players: 234, max_players: 500, status: 'online', protocol: 'geyser_1.21', latency_ms: 23, players_java: 187, players_bedrock: 47, uptime: '45d 12h' },
  { proxy_id: 'proxy-002', name: 'EU Proxy', java_host: 'eu.play.infrapilot.io', java_port: 25565, bedrock_host: 'eu.bedrock.infrapilot.io', bedrock_port: 19132, region: 'EU-West', active_players: 156, max_players: 300, status: 'online', protocol: 'geyser_1.21', latency_ms: 12, players_java: 120, players_bedrock: 36, uptime: '30d 8h' },
  { proxy_id: 'proxy-003', name: 'Asia Proxy', java_host: 'asia.play.infrapilot.io', java_port: 25565, bedrock_host: 'asia.bedrock.infrapilot.io', bedrock_port: 19132, region: 'Asia-East', active_players: 89, max_players: 200, status: 'online', protocol: 'geyser_1.20', latency_ms: 8, players_java: 65, players_bedrock: 24, uptime: '15d 3h' },
  { proxy_id: 'proxy-004', name: 'Dev Proxy', java_host: 'dev.play.infrapilot.io', java_port: 25565, bedrock_host: 'dev.bedrock.infrapilot.io', bedrock_port: 19132, region: 'NA-East', active_players: 0, max_players: 50, status: 'offline', protocol: 'geyser_1.21', latency_ms: 0, players_java: 0, players_bedrock: 0, uptime: '0d 0h' },
];

const CrossPlayProxy: React.FC = () => {
  const [proxies, setProxies] = useState<ProxyServer[]>(mockProxies);

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Cross-Play Proxy</h1>
          <p className="text-muted-foreground">Geyser Java-Bedrock bridge with player sync and protocol management</p>
        </div>
        <Badge variant="secondary" className="text-sm"><Wifi className="mr-1 h-4 w-4" />{proxies.filter(p => p.status === 'online').length} Online</Badge>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Total Players</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">{proxies.reduce((s, p) => s + p.active_players, 0)}</div></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Java Edition</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold text-blue-500">{proxies.reduce((s, p) => s + p.players_java, 0)}</div></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Bedrock Edition</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold text-green-500">{proxies.reduce((s, p) => s + p.players_bedrock, 0)}</div></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Bedrock %</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">20.1%</div></CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader><CardTitle>Proxy Servers</CardTitle></CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Java Address</TableHead>
                <TableHead>Bedrock Address</TableHead>
                <TableHead>Players</TableHead>
                <TableHead>J/B Split</TableHead>
                <TableHead>Latency</TableHead>
                <TableHead>Uptime</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {proxies.map(p => (
                <TableRow key={p.proxy_id}>
                  <TableCell className="font-medium">
                    <div className="flex items-center gap-2">
                      <Globe className="h-4 w-4 text-muted-foreground" />
                      {p.name}
                    </div>
                  </TableCell>
                  <TableCell className="font-mono text-xs">{p.java_host}:{p.java_port}</TableCell>
                  <TableCell className="font-mono text-xs">{p.bedrock_host}:{p.bedrock_port}</TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Users className="h-4 w-4" />
                      {p.active_players}/{p.max_players}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1 text-xs">
                      <span className="text-blue-500">{p.players_java}J</span>
                      <span className="text-muted-foreground">/</span>
                      <span className="text-green-500">{p.players_bedrock}B</span>
                    </div>
                  </TableCell>
                  <TableCell>{p.latency_ms > 0 ? `${p.latency_ms}ms` : '-'}</TableCell>
                  <TableCell className="text-xs">{p.uptime}</TableCell>
                  <TableCell>
                    <Badge variant={p.status === 'online' ? 'default' : 'secondary'}>{p.status}</Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Tabs defaultValue="player-sync">
        <TabsList>
          <TabsTrigger value="player-sync">Player Sync</TabsTrigger>
          <TabsTrigger value="protocol-mapping">Protocol Mapping</TabsTrigger>
          <TabsTrigger value="config">Configuration</TabsTrigger>
        </TabsList>

        <TabsContent value="player-sync">
          <Card>
            <CardHeader><CardTitle>Java ? Bedrock Player Sync</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between p-3 rounded-lg bg-green-50 dark:bg-green-950 border border-green-200">
                <div className="flex items-center gap-2"><CheckCircle className="h-5 w-5 text-green-500" /><span>Inventory Sync</span></div>
                <Badge variant="default">Active</Badge>
              </div>
              <div className="flex items-center justify-between p-3 rounded-lg bg-green-50 dark:bg-green-950 border border-green-200">
                <div className="flex items-center gap-2"><CheckCircle className="h-5 w-5 text-green-500" /><span>Skin Mapping</span></div>
                <Badge variant="default">Active</Badge>
              </div>
              <div className="flex items-center justify-between p-3 rounded-lg bg-yellow-50 dark:bg-yellow-950 border border-yellow-200">
                <div className="flex items-center gap-2"><AlertTriangle className="h-5 w-5 text-yellow-500" /><span>Chat Formatting</span></div>
                <Badge variant="secondary">Partial</Badge>
              </div>
              <div className="flex items-center justify-between p-3 rounded-lg bg-green-50 dark:bg-green-950 border border-green-200">
                <div className="flex items-center gap-2"><CheckCircle className="h-5 w-5 text-green-500" /><span>Commands Mapping</span></div>
                <Badge variant="default">Active</Badge>
              </div>
              <div className="flex items-center justify-between p-3 rounded-lg bg-green-50 dark:bg-green-950 border border-green-200">
                <div className="flex items-center gap-2"><CheckCircle className="h-5 w-5 text-green-500" /><span>Party/Friends</span></div>
                <Badge variant="default">Active</Badge>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="protocol-mapping">
          <Card>
            <CardHeader><CardTitle>Protocol Version Mapping</CardTitle></CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow><TableHead>Java Version</TableHead><TableHead>Bedrock Version</TableHead><TableHead>Status</TableHead><TableHead>Notes</TableHead></TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow><TableCell>1.21</TableCell><TableCell>1.21.0</TableCell><TableCell><Badge>Synced</Badge></TableCell><TableCell className="text-xs">Latest supported</TableCell></TableRow>
                  <TableRow><TableCell>1.20.6</TableCell><TableCell>1.20.80</TableCell><TableCell><Badge>Synced</Badge></TableCell><TableCell className="text-xs">Stable</TableCell></TableRow>
                  <TableRow><TableCell>1.20.4</TableCell><TableCell>1.20.70</TableCell><TableCell><Badge variant="secondary">Legacy</Badge></TableCell><TableCell className="text-xs">Deprecated soon</TableCell></TableRow>
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="config">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader><CardTitle className="text-sm">Geyser Config</CardTitle></CardHeader>
              <CardContent className="space-y-2 text-sm">
                <div className="flex justify-between"><span>Max Players</span><Badge>500</Badge></div>
                <div className="flex justify-between"><span>Allow Bedrock</span><Badge variant="secondary">Yes</Badge></div>
                <div className="flex justify-between"><span>Auth Mode</span><Badge>online</Badge></div>
                <div className="flex justify-between"><span>Motd</span><Badge variant="outline">InfraPilot Network</Badge></div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle className="text-sm">Floodgate Config</CardTitle></CardHeader>
              <CardContent className="space-y-2 text-sm">
                <div className="flex justify-between"><span>Enable</span><Badge variant="secondary">Yes</Badge></div>
                <div className="flex justify-between"><span>Username Prefix</span><Badge>.</Badge></div>
                <div className="flex justify-between"><span>Send Message on Join</span><Badge variant="secondary">Yes</Badge></div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default CrossPlayProxy;
