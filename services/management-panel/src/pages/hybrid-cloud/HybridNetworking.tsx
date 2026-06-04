import { useEffect, useState } from 'react';
import { FormattedMessage } from 'react-intl';
import { apiClient } from '../../lib/api';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';

interface Peer { peer_id: string; name: string; node_type: string; endpoint: string; subnet: string; connected: boolean; latency_ms: number; }
interface Tunnel { tunnel_id: string; peer_name: string; type: string; status: string; }

export const HybridNetworking = () => {
  const [peers, setPeers] = useState<Peer[]>([]);
  const [tunnels, setTunnels] = useState<Tunnel[]>([]);
  const [loading, setLoading] = useState(true);
  const [showDialog, setShowDialog] = useState(false);
  const [peerName, setPeerName] = useState('');
  const [peerType, setPeerType] = useState('on_prem');
  const [peerEndpoint, setPeerEndpoint] = useState('');
  const [peerSubnet, setPeerSubnet] = useState('');

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    try {
      const [peerData, tunnelData] = await Promise.all([apiClient.listMeshPeers(), apiClient.listMeshTunnels()]);
      setPeers(peerData || []); setTunnels(tunnelData || []);
    } catch (e) { toast.error('Failed to load mesh data');
    } finally { setLoading(false); }
  };

  const registerPeer = async () => {
    try { await apiClient.registerMeshPeer({ name: peerName, node_type: peerType, endpoint: peerEndpoint, subnet: peerSubnet }); toast.success('Peer registered'); setShowDialog(false); loadData();
    } catch (e) { toast.error('Failed to register peer'); }
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>;

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex justify-between items-center">
        <div><h1 className="text-3xl font-bold"><FormattedMessage id="hybridNetworking.title" defaultMessage="Hybrid Networking Mesh" /></h1>
          <p className="text-muted-foreground mt-1"><FormattedMessage id="hybridNetworking.description" defaultMessage="VPN/GRE tunnel mesh between on-prem, edge, and cloud VPCs" /></p></div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card><CardHeader><CardTitle>Total Peers</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold">{peers.length}</p></CardContent></Card>
        <Card><CardHeader><CardTitle>Connected</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold text-green-500">{peers.filter(p => p.connected).length}</p></CardContent></Card>
        <Card><CardHeader><CardTitle>Tunnels</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold">{tunnels.length}</p></CardContent></Card>
        <Card><CardHeader><CardTitle>BGP ASN</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold">64512</p></CardContent></Card>
      </div>
      <Tabs defaultValue="peers">
        <TabsList><TabsTrigger value="peers">Peers</TabsTrigger><TabsTrigger value="tunnels">Tunnels</TabsTrigger><TabsTrigger value="topology">Topology</TabsTrigger></TabsList>
        <TabsContent value="peers" className="space-y-4">
          <div className="flex justify-between"><h2 className="text-xl font-semibold">Mesh Peers</h2>
            <Button onClick={() => setShowDialog(true)}>Register Peer</Button></div>
          <Card><CardContent className="p-0">
            <Table><TableHeader><TableRow>
              <TableHead>Name</TableHead><TableHead>Type</TableHead><TableHead>Endpoint</TableHead><TableHead>Subnet</TableHead><TableHead>Status</TableHead><TableHead>Latency</TableHead>
            </TableRow></TableHeader>
            <TableBody>{peers.map((p) => (
              <TableRow key={p.peer_id}><TableCell className="font-medium">{p.name}</TableCell>
                <TableCell><Badge variant="outline">{p.node_type}</Badge></TableCell>
                <TableCell className="font-mono text-xs">{p.endpoint}</TableCell>
                <TableCell className="font-mono text-xs">{p.subnet}</TableCell>
                <TableCell><Badge variant={p.connected ? 'default' : 'secondary'}>{p.connected ? 'Online' : 'Offline'}</Badge></TableCell>
                <TableCell>{p.latency_ms}ms</TableCell>
              </TableRow>
            ))}</TableBody></Table>
          </CardContent></Card>
          {showDialog && (<div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"><Card className="w-96">
            <CardHeader><CardTitle>Register Peer</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div><Label>Name</Label><Input value={peerName} onChange={(e) => setPeerName(e.target.value)} /></div>
              <div><Label>Type</Label><Input value={peerType} onChange={(e) => setPeerType(e.target.value)} /></div>
              <div><Label>Endpoint</Label><Input value={peerEndpoint} onChange={(e) => setPeerEndpoint(e.target.value)} /></div>
              <div><Label>Subnet</Label><Input value={peerSubnet} onChange={(e) => setPeerSubnet(e.target.value)} /></div>
              <div className="flex gap-2"><Button onClick={registerPeer}>Register</Button><Button variant="outline" onClick={() => setShowDialog(false)}>Cancel</Button></div>
            </CardContent></Card></div>)}
        </TabsContent>
        <TabsContent value="tunnels">
          <Card><CardContent className="p-0">
            <Table><TableHeader><TableRow>
              <TableHead>Tunnel ID</TableHead><TableHead>Peer</TableHead><TableHead>Type</TableHead><TableHead>Status</TableHead>
            </TableRow></TableHeader>
            <TableBody>{tunnels.map((t) => (
              <TableRow key={t.tunnel_id}><TableCell className="font-mono text-xs">{t.tunnel_id}</TableCell>
                <TableCell>{t.peer_name}</TableCell><TableCell>{t.type}</TableCell>
                <TableCell><Badge variant={t.status === 'established' ? 'default' : 'secondary'}>{t.status}</Badge></TableCell>
              </TableRow>
            ))}</TableBody></Table>
          </CardContent></Card>
        </TabsContent>
        <TabsContent value="topology">
          <div className="grid grid-cols-2 gap-4">
            <Card><CardHeader><CardTitle>On-Prem</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{peers.filter(p => p.node_type === 'on_prem').length} peers</p></CardContent></Card>
            <Card><CardHeader><CardTitle>Cloud VPC</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{peers.filter(p => p.node_type === 'cloud_vpc').length} peers</p></CardContent></Card>
            <Card><CardHeader><CardTitle>Edge</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{peers.filter(p => p.node_type === 'edge').length} peers</p></CardContent></Card>
            <Card><CardHeader><CardTitle>Default Tunnel</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">WireGuard</p></CardContent></Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};
  const [showPeerDialog, setShowPeerDialog] = useState(false);
  const [peerName, setPeerName] = useState('');
  const [peerEndpoint, setPeerEndpoint] = useState('');
  const [peerType, setPeerType] = useState('cloud_vpc');
  const [tunnelType, setTunnelType] = useState('wireguard');
  const [routes, setRoutes] = useState<any[]>([]);
  const [diagnosis, setDiagnosis] = useState<any>(null);
  const [diagnosePeerId, setDiagnosePeerId] = useState('');

  const addPeer = async () => {
    try {
      const result = await apiClient.addMeshPeer(peerName, peerEndpoint, peerType);
      setPeers([...peers, result]);
      toast.success('Peer added');
      setShowPeerDialog(false);
    } catch { toast.error('Failed to add peer'); }
  };

  const diagnosePeer = async () => {
    try {
      const result = await apiClient.diagnoseMeshPeer(diagnosePeerId);
      setDiagnosis(result);
    } catch { toast.error('Diagnosis failed'); }
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="grid grid-cols-4 gap-4">
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Peers</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{peers.length}</p></CardContent></Card>
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Tunnels</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{tunnels.length}</p></CardContent></Card>
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Routes</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{routes.length}</p></CardContent></Card>
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Avg Latency</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{peers.reduce((s, p) => s + (p.latency_ms || 0), 0) / (peers.length || 1)}ms</p></CardContent></Card>
      </div>

      <div className="flex gap-2">
        <Dialog open={showPeerDialog} onOpenChange={setShowPeerDialog}>
          <DialogTrigger asChild><Button>Add Peer</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>Add Mesh Peer</DialogTitle></DialogHeader>
            <div className="space-y-2">
              <Input placeholder="Peer name" value={peerName} onChange={e => setPeerName(e.target.value)} />
              <Input placeholder="Endpoint" value={peerEndpoint} onChange={e => setPeerEndpoint(e.target.value)} />
              <Select value={peerType} onValueChange={setPeerType}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="on_prem">On-Prem</SelectItem>
                  <SelectItem value="cloud_vpc">Cloud VPC</SelectItem>
                  <SelectItem value="edge">Edge</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <DialogFooter><Button onClick={addPeer}>Add</Button></DialogFooter>
          </DialogContent>
        </Dialog>
        <div className="flex gap-2 items-center">
          <Input placeholder="Peer ID to diagnose" value={diagnosePeerId} onChange={e => setDiagnosePeerId(e.target.value)} className="w-48" />
          <Button variant="outline" onClick={diagnosePeer}>Diagnose</Button>
        </div>
      </div>

      {diagnosis && (
        <Card>
          <CardHeader><CardTitle>Diagnosis: {diagnosis.peer_name}</CardTitle></CardHeader>
          <CardContent className="grid grid-cols-2 gap-4">
            <div><Label>Connected</Label><p>{diagnosis.connected ? '✅ Yes' : '❌ No'}</p></div>
            <div><Label>Latency</Label><p>{diagnosis.latency_ms}ms</p></div>
            <div><Label>Issues</Label><p>{diagnosis.issues?.length ? diagnosis.issues.join(', ') : 'None'}</p></div>
            <div><Label>Health</Label><p className={diagnosis.healthy ? 'text-green-600' : 'text-red-600'}>{diagnosis.healthy ? 'Healthy' : 'Unhealthy'}</p></div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

  const [showTunnelDialog, setShowTunnelDialog] = useState(false);
  const [tunnelName, setTunnelName] = useState('');
  const [tunnelPeerId, setTunnelPeerId] = useState('');
  const [tunnelLocalCidr, setTunnelLocalCidr] = useState('10.0.0.0/16');
  const [tunnelRemoteCidr, setTunnelRemoteCidr] = useState('172.16.0.0/16');
  const [tunnelType, setTunnelType] = useState('wireguard');
  const [showRouteDialog, setShowRouteDialog] = useState(false);
  const [routePrefix, setRoutePrefix] = useState('');
  const [routeNextHop, setRouteNextHop] = useState('');
  const [routes, setRoutes] = useState<any[]>([]);

  const createTunnel = async () => {
    try {
      const result = await apiClient.createMeshTunnel(tunnelName, tunnelPeerId, tunnelLocalCidr, tunnelRemoteCidr, tunnelType);
      setTunnels([...tunnels, result]);
      toast.success('Tunnel created');
      setShowTunnelDialog(false);
    } catch { toast.error('Failed to create tunnel'); }
  };

  const addRoute = async () => {
    try {
      await apiClient.addMeshRoute(routePrefix, routeNextHop);
      setRoutes([...routes, { prefix: routePrefix, next_hop: routeNextHop }]);
      toast.success('Route added');
      setShowRouteDialog(false);
    } catch { toast.error('Failed to add route'); }
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="grid grid-cols-4 gap-4">
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Peers</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{peers.length}</p></CardContent></Card>
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Tunnels</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{tunnels.length}</p></CardContent></Card>
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Routes</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{routes.length}</p></CardContent></Card>
        <Card><CardHeader className="py-3"><CardTitle className="text-sm">Avg Latency</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{peers.length > 0 ? (peers.reduce((s, p) => s + (p.latency_ms || 0), 0) / peers.length).toFixed(0) : 0}ms</p></CardContent></Card>
      </div>

      <div className="flex gap-2">
        <Dialog open={showTunnelDialog} onOpenChange={setShowTunnelDialog}>
          <DialogTrigger asChild><Button>Create Tunnel</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>Create Mesh Tunnel</DialogTitle></DialogHeader>
            <div className="space-y-2">
              <Input placeholder="Tunnel name" value={tunnelName} onChange={e => setTunnelName(e.target.value)} />
              <Input placeholder="Peer ID" value={tunnelPeerId} onChange={e => setTunnelPeerId(e.target.value)} />
              <Input placeholder="Local CIDR" value={tunnelLocalCidr} onChange={e => setTunnelLocalCidr(e.target.value)} />
              <Input placeholder="Remote CIDR" value={tunnelRemoteCidr} onChange={e => setTunnelRemoteCidr(e.target.value)} />
              <Select value={tunnelType} onValueChange={setTunnelType}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="wireguard">WireGuard</SelectItem>
                  <SelectItem value="ipsec">IPSec</SelectItem>
                  <SelectItem value="gre">GRE</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <DialogFooter><Button onClick={createTunnel}>Create</Button></DialogFooter>
          </DialogContent>
        </Dialog>
        <Dialog open={showRouteDialog} onOpenChange={setShowRouteDialog}>
          <DialogTrigger asChild><Button variant="outline">Add Route</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>Add Route</DialogTitle></DialogHeader>
            <div className="space-y-2">
              <Input placeholder="Prefix (e.g. 10.0.0.0/8)" value={routePrefix} onChange={e => setRoutePrefix(e.target.value)} />
              <Input placeholder="Next hop (e.g. 10.0.0.1)" value={routeNextHop} onChange={e => setRouteNextHop(e.target.value)} />
            </div>
            <DialogFooter><Button onClick={addRoute}>Add</Button></DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardHeader><CardTitle>Active Tunnels</CardTitle></CardHeader>
        <CardContent>
          <Table>
            <TableHeader><TableRow><TableHead>Name</TableHead><TableHead>Type</TableHead><TableHead>Local CIDR</TableHead><TableHead>Remote CIDR</TableHead><TableHead>Status</TableHead></TableRow></TableHeader>
            <TableBody>{tunnels.map(t => (
              <TableRow key={t.tunnel_id || t.id}>
                <TableCell className="font-medium">{t.name || t.tunnel_id}</TableCell>
                <TableCell><Badge variant="outline">{t.type}</Badge></TableCell>
                <TableCell className="font-mono text-xs">{t.local_cidr}</TableCell>
                <TableCell className="font-mono text-xs">{t.remote_cidr}</TableCell>
                <TableCell><Badge variant={t.status === 'active' || t.status === 'established' ? 'default' : 'secondary'}>{t.status}</Badge></TableCell>
              </TableRow>
            ))}</TableBody>
          </Table>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Routes</CardTitle></CardHeader>
        <CardContent>
          <Table>
            <TableHeader><TableRow><TableHead>Prefix</TableHead><TableHead>Next Hop</TableHead></TableRow></TableHeader>
            <TableBody>{routes.map((r, i) => (
              <TableRow key={i}>
                <TableCell className="font-mono text-xs">{r.prefix}</TableCell>
                <TableCell className="font-mono text-xs">{r.next_hop}</TableCell>
              </TableRow>
            ))}</TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};

function PeerFormDialog({ open, onOpenChange, onSubmit }: { open: boolean; onOpenChange: (v: boolean) => void; onSubmit: (data: any) => void }) {
  const [name, setName] = useState(''); const [endpoint, setEndpoint] = useState(''); const [nodeType, setNodeType] = useState('on_prem');
  return (
    <Dialog open={open} onOpenChange={onOpenChange}><DialogContent><DialogHeader><DialogTitle>Register Peer</DialogTitle></DialogHeader>
      <div className="space-y-4">
        <div><Label>Name</Label><Input value={name} onChange={e => setName(e.target.value)} /></div>
        <div><Label>Endpoint</Label><Input value={endpoint} onChange={e => setEndpoint(e.target.value)} /></div>
        <div><Label>Type</Label><Select value={nodeType} onValueChange={setNodeType}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{['on_prem','cloud_vpc','edge','remote_site'].map(t => <SelectItem key={t} value={t}>{t}</SelectItem>)}</SelectContent></Select></div>
      </div>
      <DialogFooter><Button onClick={() => { onSubmit({ name, endpoint, nodeType }); onOpenChange(false); }}>Register</Button></DialogFooter>
    </DialogContent></Dialog>
  );
}

function TopologyMap({ peers }: { peers: any[] }) {
  const connected = peers.filter(p => p.connected).length;
  const total = peers.length;
  return (
    <Card><CardHeader><CardTitle>Mesh Topology</CardTitle></CardHeader>
    <CardContent><div className="grid grid-cols-2 gap-4">
      <div><Label>Total Peers</Label><p className="text-2xl font-bold">{total}</p></div>
      <div><Label>Connected</Label><p className="text-2xl font-bold text-green-600">{connected}</p></div>
      <div><Label>Disconnected</Label><p className="text-2xl font-bold text-red-600">{total - connected}</p></div>
      <div><Label>Health</Label><p className="text-2xl font-bold">{total > 0 ? `${Math.round((connected / total) * 100)}%` : 'N/A'}</p></div>
    </div></CardContent></Card>
  );
}

function LatencyMatrix({ peers }: { peers: any[] }) {
  const connectedPeers = peers.filter(p => p.connected);
  if (connectedPeers.length < 2) return <Card><CardContent><p className="text-sm text-muted-foreground">Need 2+ connected peers for matrix</p></CardContent></Card>;
  return (
    <Card><CardHeader><CardTitle>Latency Matrix</CardTitle></CardHeader>
    <CardContent><Table><TableHeader><TableRow><TableHead>Peer</TableHead><TableHead>Avg Latency</TableHead><TableHead>Bandwidth</TableHead><TableHead>Status</TableHead></TableRow></TableHeader>
    <TableBody>{connectedPeers.map((p: any, i: number) => (
      <TableRow key={i}><TableCell className="font-medium">{p.name}</TableCell><TableCell>{p.latency_ms || '--'}ms</TableCell><TableCell>{p.bandwidth_mbps || 0} Mbps</TableCell><TableCell><Badge variant={p.connected ? 'default' : 'destructive'}>{p.connected ? 'Up' : 'Down'}</Badge></TableCell></TableRow>
    ))}</TableBody></Table></CardContent></Card>
  );
}

function BgpRouteTable({ routes }: { routes: any[] }) {
  return (
    <Card><CardHeader><CardTitle>BGP Routes</CardTitle></CardHeader>
    <CardContent><Table><TableHeader><TableRow><TableHead>Prefix</TableHead><TableHead>Next Hop</TableHead><TableHead>AS Path</TableHead><TableHead>Local Pref</TableHead></TableRow></TableHeader>
    <TableBody>{routes.filter((r: any) => !r.withdrawn).slice(0, 20).map((r: any, i: number) => (
      <TableRow key={i}><TableCell className="font-mono text-xs">{r.prefix}</TableCell><TableCell className="font-mono text-xs">{r.next_hop}</TableCell><TableCell className="font-mono text-xs">{r.as_path?.join(' ')}</TableCell><TableCell>{r.local_pref}</TableCell></TableRow>
    ))}</TableBody></Table></CardContent></Card>
  );
}

function ConnectionStatusBadge({ connected }: { connected: boolean }) {
  return <Badge variant={connected ? 'default' : 'destructive'}><span className={`h-2 w-2 rounded-full mr-1 ${connected ? 'bg-green-400' : 'bg-red-400'}`} />{connected ? 'Connected' : 'Disconnected'}</Badge>;
}

export default HybridNetworking;
