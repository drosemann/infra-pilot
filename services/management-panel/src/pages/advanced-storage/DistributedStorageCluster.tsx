import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
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
import { AlertCircle, CheckCircle, Clock, Cpu, HardDrive, Plus, Server, Trash2, Activity, RefreshCw } from 'lucide-react';

interface ClusterNode {
  node_id: string;
  host: string;
  port: number;
  role: string;
  storage_path: string;
  status: string;
  uptime: number;
  capacity_total: number;
  capacity_used: number;
  capacity_percent: number;
  cpu_usage: number;
  memory_usage: number;
}

interface StorageCluster {
  cluster_id: string;
  name: string;
  cluster_type: string;
  nodes: ClusterNode[];
  status: string;
  created_at: string;
  replication_factor: number;
  erasure_parity: number;
  total_capacity: number;
  used_capacity: number;
  endpoint: string;
  access_key: string;
  secret_key: string;
}

interface ClusterHealth {
  cluster_id: string;
  name: string;
  status: string;
  nodes_online: number;
  nodes_total: number;
  health_percent: number;
  total_capacity_gb: number;
  used_capacity_gb: number;
  usage_percent: number;
}

const mockClusters: StorageCluster[] = [
  {
    cluster_id: 'sc-1715000000',
    name: 'Primary Storage',
    cluster_type: 'minio',
    nodes: [
      { node_id: 'n1', host: 'storage-1.internal', port: 9000, role: 'storage', storage_path: '/data/storage/1', status: 'online', uptime: 86400, capacity_total: 1099511627776, capacity_used: 329853488332, capacity_percent: 30, cpu_usage: 45.2, memory_usage: 62.1 },
      { node_id: 'n2', host: 'storage-2.internal', port: 9000, role: 'storage', storage_path: '/data/storage/2', status: 'online', uptime: 86400, capacity_total: 1099511627776, capacity_used: 274877906944, capacity_percent: 25, cpu_usage: 38.7, memory_usage: 55.3 },
      { node_id: 'n3', host: 'storage-3.internal', port: 9000, role: 'storage', storage_path: '/data/storage/3', status: 'online', uptime: 43200, capacity_total: 1099511627776, capacity_used: 439804651110, capacity_percent: 40, cpu_usage: 52.1, memory_usage: 70.8 },
    ],
    status: 'active',
    created_at: '2024-05-01T00:00:00Z',
    replication_factor: 3,
    erasure_parity: 2,
    total_capacity: 3298534883328,
    used_capacity: 1044536046386,
    endpoint: 'https://primary-storage.internal:9000',
    access_key: 'minio-admin',
    secret_key: '****',
  },
  {
    cluster_id: 'sc-1715100000',
    name: 'Archive Cluster',
    cluster_type: 'ceph',
    nodes: [
      { node_id: 'n4', host: 'archive-1.internal', port: 6789, role: 'storage', storage_path: '/data/ceph/osd1', status: 'online', uptime: 172800, capacity_total: 2199023255552, capacity_used: 1539316278886, capacity_percent: 70, cpu_usage: 35.0, memory_usage: 45.0 },
      { node_id: 'n5', host: 'archive-2.internal', port: 6789, role: 'storage', storage_path: '/data/ceph/osd2', status: 'online', uptime: 172800, capacity_total: 2199023255552, capacity_used: 1649267441664, capacity_percent: 75, cpu_usage: 42.0, memory_usage: 52.0 },
      { node_id: 'n6', host: 'archive-3.internal', port: 6789, role: 'storage', storage_path: '/data/ceph/osd3', status: 'offline', uptime: 0, capacity_total: 2199023255552, capacity_used: 0, capacity_percent: 0, cpu_usage: 0, memory_usage: 0 },
    ],
    status: 'active',
    created_at: '2024-04-15T00:00:00Z',
    replication_factor: 2,
    erasure_parity: 1,
    total_capacity: 6597069766656,
    used_capacity: 3188583720550,
    endpoint: 'https://archive-cluster.internal:7480',
    access_key: 'ceph-admin',
    secret_key: '****',
  },
];

const DistributedStorageCluster: React.FC = () => {
  const [clusters, setClusters] = useState<StorageCluster[]>(mockClusters);
  const [selectedCluster, setSelectedCluster] = useState<StorageCluster | null>(null);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [newClusterName, setNewClusterName] = useState('');
  const [newClusterType, setNewClusterType] = useState('minio');
  const [newClusterNodes, setNewClusterNodes] = useState(3);

  const getHealthColor = (percent: number) => {
    if (percent >= 80) return 'text-red-500';
    if (percent >= 60) return 'text-yellow-500';
    return 'text-green-500';
  };

  const getHealthProgress = (health: ClusterHealth) => {
    if (health.health_percent >= 90) return 'bg-green-500';
    if (health.health_percent >= 70) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getClusterHealth = (cluster: StorageCluster): ClusterHealth => {
    const online = cluster.nodes.filter(n => n.status === 'online').length;
    return {
      cluster_id: cluster.cluster_id,
      name: cluster.name,
      status: cluster.status,
      nodes_online: online,
      nodes_total: cluster.nodes.length,
      health_percent: Math.round((online / cluster.nodes.length) * 100),
      total_capacity_gb: Math.round(cluster.total_capacity / (1024 * 1024 * 1024)),
      used_capacity_gb: Math.round(cluster.used_capacity / (1024 * 1024 * 1024)),
      usage_percent: Math.round((cluster.used_capacity / cluster.total_capacity) * 100),
    };
  };

  const handleCreateCluster = () => {
    const clusterId = `sc-${Date.now()}`;
    const nodes: ClusterNode[] = [];
    for (let i = 0; i < newClusterNodes; i++) {
      nodes.push({
        node_id: `${clusterId}-n${i + 1}`,
        host: `storage-${i + 1}.internal`,
        port: newClusterType === 'minio' ? 9000 : 6789,
        role: 'storage',
        storage_path: `/data/storage/${clusterId}/node${i + 1}`,
        status: 'online',
        uptime: 0,
        capacity_total: 1099511627776,
        capacity_used: 0,
        capacity_percent: 0,
        cpu_usage: 0,
        memory_usage: 0,
      });
    }
    const newCluster: StorageCluster = {
      cluster_id: clusterId,
      name: newClusterName,
      cluster_type: newClusterType,
      nodes,
      status: 'active',
      created_at: new Date().toISOString(),
      replication_factor: 3,
      erasure_parity: 2,
      total_capacity: nodes.reduce((sum, n) => sum + n.capacity_total, 0),
      used_capacity: 0,
      endpoint: `https://${newClusterName.toLowerCase().replace(/\s+/g, '-')}.internal:${newClusterType === 'minio' ? 9000 : 7480}`,
      access_key: 'admin',
      secret_key: '********',
    };
    setClusters([...clusters, newCluster]);
    setIsCreateOpen(false);
    setNewClusterName('');
  };

  const handleDeleteCluster = (clusterId: string) => {
    setClusters(clusters.filter(c => c.cluster_id !== clusterId));
    if (selectedCluster?.cluster_id === clusterId) {
      setSelectedCluster(null);
    }
  };

  const totalCapacity = clusters.reduce((sum, c) => sum + c.total_capacity, 0);
  const totalUsed = clusters.reduce((sum, c) => sum + c.used_capacity, 0);
  const totalOnline = clusters.reduce((sum, c) => sum + c.nodes.filter(n => n.status === 'online').length, 0);
  const totalNodes = clusters.reduce((sum, c) => sum + c.nodes.length, 0);

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Distributed Storage Cluster</h1>
          <p className="text-muted-foreground">Deploy and manage Minio/Ceph/GlusterFS storage clusters</p>
        </div>
        <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              Create Cluster
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[500px]">
            <DialogHeader>
              <DialogTitle>Create Storage Cluster</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium">Cluster Name</label>
                <Input value={newClusterName} onChange={e => setNewClusterName(e.target.value)} placeholder="My Storage Cluster" />
              </div>
              <div>
                <label className="text-sm font-medium">Cluster Type</label>
                <select className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm" value={newClusterType} onChange={e => setNewClusterType(e.target.value)}>
                  <option value="minio">Minio (S3 Compatible)</option>
                  <option value="ceph">Ceph (Distributed)</option>
                  <option value="glusterfs">GlusterFS (Scale-Out)</option>
                </select>
              </div>
              <div>
                <label className="text-sm font-medium">Initial Nodes</label>
                <Input type="number" value={newClusterNodes} onChange={e => setNewClusterNodes(parseInt(e.target.value) || 3)} min={1} max={20} />
              </div>
              <Button onClick={handleCreateCluster} className="w-full" disabled={!newClusterName}>
                Deploy Cluster
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Clusters</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{clusters.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Nodes</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalOnline}/{totalNodes}</div>
            <p className="text-xs text-muted-foreground">online / total</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Capacity</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{Math.round(totalCapacity / (1024 * 1024 * 1024 * 1024))} TB</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Overall Usage</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{Math.round((totalUsed / totalCapacity) * 100)}%</div>
            <Progress value={(totalUsed / totalCapacity) * 100} className="mt-2" />
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="clusters">Clusters</TabsTrigger>
          <TabsTrigger value="health">Health</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Cluster Overview</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Nodes</TableHead>
                    <TableHead>Capacity</TableHead>
                    <TableHead>Usage</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {clusters.map(cluster => {
                    const health = getClusterHealth(cluster);
                    return (
                      <TableRow key={cluster.cluster_id}>
                        <TableCell className="font-medium">{cluster.name}</TableCell>
                        <TableCell><Badge variant="outline">{cluster.cluster_type}</Badge></TableCell>
                        <TableCell>{health.nodes_online}/{health.nodes_total}</TableCell>
                        <TableCell>{health.total_capacity_gb} GB</TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <Progress value={health.usage_percent} className="w-20" />
                            <span className={getHealthColor(health.usage_percent)}>{health.usage_percent}%</span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant={health.status === 'active' ? 'default' : 'secondary'}>{health.status}</Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex gap-2">
                            <Button variant="outline" size="sm" onClick={() => setSelectedCluster(cluster)}>
                              <Activity className="h-4 w-4" />
                            </Button>
                            <Button variant="destructive" size="sm" onClick={() => handleDeleteCluster(cluster.cluster_id)}>
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="clusters" className="space-y-4">
          {clusters.map(cluster => {
            const health = getClusterHealth(cluster);
            return (
              <Card key={cluster.cluster_id}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle>{cluster.name}</CardTitle>
                      <p className="text-sm text-muted-foreground">{cluster.cluster_id}</p>
                    </div>
                    <Badge variant={cluster.status === 'active' ? 'default' : 'secondary'}>{cluster.status}</Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                    <div>
                      <p className="text-sm text-muted-foreground">Type</p>
                      <p className="font-medium">{cluster.cluster_type}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Endpoint</p>
                      <p className="font-medium text-xs">{cluster.endpoint}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Replication</p>
                      <p className="font-medium">{cluster.replication_factor}x</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Erasure Parity</p>
                      <p className="font-medium">{cluster.erasure_parity}</p>
                    </div>
                  </div>
                  <Separator className="my-4" />
                  <h4 className="text-sm font-medium mb-3">Nodes</h4>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Node ID</TableHead>
                        <TableHead>Host</TableHead>
                        <TableHead>Role</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>CPU</TableHead>
                        <TableHead>Memory</TableHead>
                        <TableHead>Capacity</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {cluster.nodes.map(node => (
                        <TableRow key={node.node_id}>
                          <TableCell className="font-mono text-xs">{node.node_id}</TableCell>
                          <TableCell>{node.host}:{node.port}</TableCell>
                          <TableCell><Badge variant="outline">{node.role}</Badge></TableCell>
                          <TableCell>
                            <div className="flex items-center gap-1">
                              {node.status === 'online' ? (
                                <CheckCircle className="h-4 w-4 text-green-500" />
                              ) : (
                                <AlertCircle className="h-4 w-4 text-red-500" />
                              )}
                              {node.status}
                            </div>
                          </TableCell>
                          <TableCell>{node.cpu_usage.toFixed(1)}%</TableCell>
                          <TableCell>{node.memory_usage.toFixed(1)}%</TableCell>
                          <TableCell>{node.capacity_percent.toFixed(0)}%</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            );
          })}
        </TabsContent>

        <TabsContent value="health" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {clusters.map(cluster => {
              const health = getClusterHealth(cluster);
              return (
                <Card key={cluster.cluster_id}>
                  <CardHeader>
                    <CardTitle>{cluster.name} - Health</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <div className="flex justify-between mb-2">
                        <span className="text-sm">Cluster Health</span>
                        <span className={`text-sm font-medium ${getHealthColor(health.health_percent)}`}>{health.health_percent}%</span>
                      </div>
                      <Progress value={health.health_percent} className={getHealthProgress(health)} />
                    </div>
                    <div>
                      <div className="flex justify-between mb-2">
                        <span className="text-sm">Storage Usage</span>
                        <span className={`text-sm font-medium ${getHealthColor(health.usage_percent)}`}>{health.usage_percent}%</span>
                      </div>
                      <Progress value={health.usage_percent} />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="flex items-center gap-2">
                        <Server className="h-4 w-4 text-muted-foreground" />
                        <div>
                          <p className="text-sm font-medium">{health.nodes_online}/{health.nodes_total}</p>
                          <p className="text-xs text-muted-foreground">Nodes Online</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <HardDrive className="h-4 w-4 text-muted-foreground" />
                        <div>
                          <p className="text-sm font-medium">{health.used_capacity_gb}/{health.total_capacity_gb} GB</p>
                          <p className="text-xs text-muted-foreground">Used / Total</p>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default DistributedStorageCluster;
