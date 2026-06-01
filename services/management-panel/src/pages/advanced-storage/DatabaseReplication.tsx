import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
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
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Database, ArrowRight, Server, CheckCircle, AlertCircle, RefreshCw, Activity, Plus, Trash2 } from 'lucide-react';

interface ReplicationNode {
  node_id: string;
  host: string;
  port: number;
  role: string;
  status: string;
  lag_bytes: number;
  lag_seconds: number;
}

interface DatabaseReplication {
  repl_id: string;
  name: string;
  db_type: string;
  replication_type: string;
  status: string;
  nodes: ReplicationNode[];
}

const mockReplications: DatabaseReplication[] = [
  {
    repl_id: 'dbr-1715000000',
    name: 'App Database Cluster',
    db_type: 'mysql',
    replication_type: 'master-slave',
    status: 'active',
    nodes: [
      { node_id: 'dbr-1715000000-master', host: 'db-master.internal', port: 3306, role: 'master', status: 'online', lag_bytes: 0, lag_seconds: 0 },
      { node_id: 'dbr-1715000000-replica1', host: 'db-replica-1.internal', port: 3306, role: 'replica', status: 'online', lag_bytes: 2048, lag_seconds: 1 },
      { node_id: 'dbr-1715000000-replica2', host: 'db-replica-2.internal', port: 3306, role: 'replica', status: 'online', lag_bytes: 5120, lag_seconds: 2 },
    ],
  },
  {
    repl_id: 'dbr-1715100000',
    name: 'Analytics Cluster',
    db_type: 'postgres',
    replication_type: 'multi-master',
    status: 'active',
    nodes: [
      { node_id: 'dbr-1715100000-node1', host: 'analytics-1.internal', port: 5432, role: 'master', status: 'online', lag_bytes: 0, lag_seconds: 0 },
      { node_id: 'dbr-1715100000-node2', host: 'analytics-2.internal', port: 5432, role: 'master', status: 'online', lag_bytes: 1024, lag_seconds: 0 },
      { node_id: 'dbr-1715100000-node3', host: 'analytics-3.internal', port: 5432, role: 'master', status: 'offline', lag_bytes: 0, lag_seconds: 0 },
    ],
  },
];

const getNodeIcon = (role: string) => {
  switch (role) {
    case 'master': return <Database className="h-4 w-4 text-blue-500" />;
    case 'replica': return <Server className="h-4 w-4 text-green-500" />;
    default: return <Server className="h-4 w-4" />;
  }
};

const DatabaseReplicationManager: React.FC = () => {
  const [replications, setReplications] = useState<DatabaseReplication[]>(mockReplications);
  const [selectedRepl, setSelectedRepl] = useState<DatabaseReplication | null>(null);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [newName, setNewName] = useState('');
  const [newDbType, setNewDbType] = useState('mysql');
  const [newReplType, setNewReplType] = useState('master-slave');

  const handleCreate = () => {
    const replId = `dbr-${Date.now()}`;
    const port = newDbType === 'mysql' ? 3306 : 5432;
    const nodes: ReplicationNode[] = [
      { node_id: `${replId}-master`, host: `${newName.toLowerCase()}-master.internal`, port, role: 'master', status: 'online', lag_bytes: 0, lag_seconds: 0 },
      { node_id: `${replId}-replica1`, host: `${newName.toLowerCase()}-replica1.internal`, port, role: 'replica', status: 'online', lag_bytes: 0, lag_seconds: 0 },
    ];
    const repl: DatabaseReplication = {
      repl_id: replId, name: newName, db_type: newDbType,
      replication_type: newReplType, status: 'active', nodes,
    };
    setReplications([...replications, repl]);
    setIsCreateOpen(false);
    setNewName('');
  };

  const handleDelete = (replId: string) => {
    setReplications(replications.filter(r => r.repl_id !== replId));
  };

  const handleFailover = async (replId: string) => {
    setReplications(replications.map(r => {
      if (r.repl_id !== replId) return r;
      return {
        ...r,
        nodes: r.nodes.map(n => ({
          ...n,
          role: n.role === 'master' ? 'replica' as const : 'master' as const,
        })),
      };
    }));
  };

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Database Replication Manager</h1>
          <p className="text-muted-foreground">One-click master-slave / multi-master database replication</p>
        </div>
        <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
          <DialogTrigger asChild>
            <Button><Plus className="mr-2 h-4 w-4" />Create Replication</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>Create Database Replication</DialogTitle></DialogHeader>
            <div className="space-y-4">
              <div><Label>Name</Label><Input value={newName} onChange={e => setNewName(e.target.value)} placeholder="My Cluster" /></div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Database Type</Label>
                  <select className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm" value={newDbType} onChange={e => setNewDbType(e.target.value)}>
                    <option value="mysql">MySQL 8.0</option>
                    <option value="postgres">PostgreSQL 15</option>
                    <option value="mariadb">MariaDB 10</option>
                  </select>
                </div>
                <div>
                  <Label>Replication Type</Label>
                  <select className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm" value={newReplType} onChange={e => setNewReplType(e.target.value)}>
                    <option value="master-slave">Master-Slave</option>
                    <option value="multi-master">Multi-Master</option>
                  </select>
                </div>
              </div>
              <Button className="w-full" disabled={!newName} onClick={handleCreate}>Create Replication</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Replications</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{replications.length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Total Nodes</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{replications.reduce((s, r) => s + r.nodes.length, 0)}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Online</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{replications.reduce((s, r) => s + r.nodes.filter(n => n.status === 'online').length, 0)}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Avg Lag</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{replications.reduce((s, r) => s + r.nodes.reduce((ss, n) => ss + n.lag_seconds, 0), 0) / Math.max(replications.length, 1)}s</div></CardContent></Card>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {replications.map(repl => (
          <Card key={repl.repl_id}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>{repl.name}</CardTitle>
                  <p className="text-sm text-muted-foreground">{repl.repl_id} | {repl.db_type} | {repl.replication_type}</p>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={repl.status === 'active' ? 'default' : 'secondary'}>{repl.status}</Badge>
                  <Button variant="outline" size="sm" onClick={() => handleFailover(repl.repl_id)}>
                    <RefreshCw className="mr-1 h-3 w-3" />Failover
                  </Button>
                  <Button variant="destructive" size="sm" onClick={() => handleDelete(repl.repl_id)}>
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2 mb-4">
                {repl.nodes.map((node, idx) => (
                  <React.Fragment key={node.node_id}>
                    <div className={`p-3 rounded-lg border text-center flex-1 ${node.status === 'online' ? 'bg-card' : 'bg-muted'}`}>
                      <div className="flex justify-center mb-1">{getNodeIcon(node.role)}</div>
                      <p className="text-xs font-medium">{node.role}</p>
                      <p className="text-xs text-muted-foreground">{node.host}</p>
                      <Badge variant={node.status === 'online' ? 'default' : 'destructive'} className="mt-1 text-xs">{node.status}</Badge>
                      {node.role === 'replica' && <p className="text-xs text-muted-foreground mt-1">Lag: {node.lag_bytes} bytes ({node.lag_seconds}s)</p>}
                    </div>
                    {idx < repl.nodes.length - 1 && (
                      <div className="flex flex-col items-center">
                        <ArrowRight className="h-5 w-5 text-muted-foreground" />
                        <div className="text-xs text-muted-foreground mt-1">
                          {repl.replication_type === 'master-slave' ? 'sync' : 'p2p'}
                        </div>
                      </div>
                    )}
                  </React.Fragment>
                ))}
              </div>
              <Separator className="my-2" />
              <div className="grid grid-cols-3 gap-4 text-sm mt-4">
                <div>
                  <p className="text-muted-foreground">Database</p>
                  <p className="font-medium">{repl.db_type.toUpperCase()} {repl.db_type === 'mysql' ? '8.0' : '15'}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Replication Type</p>
                  <p className="font-medium capitalize">{repl.replication_type}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Status</p>
                  <p className="font-medium">{repl.status}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default DatabaseReplicationManager;
