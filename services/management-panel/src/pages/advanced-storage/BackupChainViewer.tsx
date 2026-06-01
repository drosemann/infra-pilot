import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import {
  Tree,
  TreeNode,
  TreeItem,
  TreeItemContent,
} from '@/components/ui/tree';
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
import { Shield, Clock, HardDrive, RotateCcw, GitBranch, CheckCircle, AlertTriangle } from 'lucide-react';

interface BackupNode {
  node_id: string;
  name: string;
  backup_type: string;
  size_bytes: number;
  size_gb: number;
  parent_id: string | null;
  created_at: string;
  status: string;
  restore_time_seconds: number;
  restore_time_minutes: number;
}

interface ChainSummary {
  chain_id: string;
  node_count: number;
  full_backups: number;
  incremental_count: number;
  differential_count: number;
  total_size_gb: number;
  last_backup: string;
}

interface RestorePath {
  chain_id: string;
  target_node: string;
  restore_steps: number;
  restore_path: BackupNode[];
  total_size_gb: number;
  estimated_restore_minutes: number;
}

const mockChains: ChainSummary[] = [
  { chain_id: 'chain-server-001', node_count: 9, full_backups: 2, incremental_count: 5, differential_count: 2, total_size_gb: 78.5, last_backup: '2024-05-28T06:00:00Z' },
  { chain_id: 'chain-db-main', node_count: 5, full_backups: 1, incremental_count: 4, differential_count: 0, total_size_gb: 21.9, last_backup: '2024-05-29T01:00:00Z' },
];

const mockRestorePath: RestorePath = {
  chain_id: 'chain-server-001',
  target_node: 'diff-002',
  restore_steps: 3,
  restore_path: [
    { node_id: 'full-001', name: 'Weekly Full Backup', backup_type: 'full', size_bytes: 53687091200, size_gb: 50, parent_id: null, created_at: '2024-05-20T06:00:00Z', status: 'completed', restore_time_seconds: 120, restore_time_minutes: 2 },
    { node_id: 'diff-002', name: 'Weekly Differential', backup_type: 'differential', size_bytes: 12884901888, size_gb: 12, parent_id: 'full-001', created_at: '2024-05-27T06:00:00Z', status: 'completed', restore_time_seconds: 45, restore_time_minutes: 0.8 },
  ],
  total_size_gb: 62,
  estimated_restore_minutes: 2.8,
};

const getBackupTypeIcon = (type: string) => {
  switch (type) {
    case 'full': return <Shield className="h-4 w-4 text-blue-500" />;
    case 'incremental': return <GitBranch className="h-4 w-4 text-green-500" />;
    case 'differential': return <RotateCcw className="h-4 w-4 text-orange-500" />;
    default: return <Clock className="h-4 w-4" />;
  }
};

const getBackupTypeColor = (type: string) => {
  switch (type) {
    case 'full': return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
    case 'incremental': return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
    case 'differential': return 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200';
    default: return '';
  }
};

const BackupChainVisualizer: React.FC = () => {
  const [chains] = useState<ChainSummary[]>(mockChains);
  const [selectedChain, setSelectedChain] = useState<string>('chain-server-001');
  const [restorePath] = useState<RestorePath>(mockRestorePath);
  const [isRestoreOpen, setIsRestoreOpen] = useState(false);

  const chainNodes: BackupNode[] = [
    { node_id: 'full-001', name: 'Weekly Full (May 20)', backup_type: 'full', size_bytes: 50 * 1024**3, size_gb: 50, parent_id: null, created_at: '2024-05-20T06:00:00Z', status: 'completed', restore_time_seconds: 120, restore_time_minutes: 2 },
    { node_id: 'inc-001', name: 'Daily Inc (May 21)', backup_type: 'incremental', size_bytes: 2 * 1024**3, size_gb: 2, parent_id: 'full-001', created_at: '2024-05-21T06:00:00Z', status: 'completed', restore_time_seconds: 10, restore_time_minutes: 0.2 },
    { node_id: 'inc-002', name: 'Daily Inc (May 22)', backup_type: 'incremental', size_bytes: 1.5 * 1024**3, size_gb: 1.5, parent_id: 'inc-001', created_at: '2024-05-22T06:00:00Z', status: 'completed', restore_time_seconds: 8, restore_time_minutes: 0.1 },
    { node_id: 'diff-001', name: 'Weekly Diff (May 23)', backup_type: 'differential', size_bytes: 8 * 1024**3, size_gb: 8, parent_id: 'full-001', created_at: '2024-05-23T06:00:00Z', status: 'completed', restore_time_seconds: 30, restore_time_minutes: 0.5 },
    { node_id: 'inc-003', name: 'Daily Inc (May 24)', backup_type: 'incremental', size_bytes: 3 * 1024**3, size_gb: 3, parent_id: 'diff-001', created_at: '2024-05-24T06:00:00Z', status: 'completed', restore_time_seconds: 12, restore_time_minutes: 0.2 },
    { node_id: 'inc-004', name: 'Daily Inc (May 25)', backup_type: 'incremental', size_bytes: 0.8 * 1024**3, size_gb: 0.8, parent_id: 'inc-003', created_at: '2024-05-25T06:00:00Z', status: 'completed', restore_time_seconds: 5, restore_time_minutes: 0.1 },
    { node_id: 'diff-002', name: 'Weekly Diff (May 27)', backup_type: 'differential', size_bytes: 12 * 1024**3, size_gb: 12, parent_id: 'full-001', created_at: '2024-05-27T06:00:00Z', status: 'completed', restore_time_seconds: 45, restore_time_minutes: 0.8 },
    { node_id: 'inc-005', name: 'Daily Inc (May 28)', backup_type: 'incremental', size_bytes: 1.2 * 1024**3, size_gb: 1.2, parent_id: 'full-002', created_at: '2024-05-28T06:00:00Z', status: 'completed', restore_time_seconds: 6, restore_time_minutes: 0.1 },
    { node_id: 'full-002', name: 'Weekly Full (May 27)', backup_type: 'full', size_bytes: 52 * 1024**3, size_gb: 52, parent_id: null, created_at: '2024-05-27T06:00:00Z', status: 'completed', restore_time_seconds: 130, restore_time_minutes: 2.2 },
  ];

  const renderChainTree = (nodes: BackupNode[]) => {
    const roots = nodes.filter(n => !n.parent_id);
    return (
      <div className="space-y-2">
        {roots.map(root => (
          <div key={root.node_id} className="ml-4">
            <div className="flex items-center gap-2 p-3 rounded-lg border bg-card">
              {getBackupTypeIcon(root.backup_type)}
              <div className="flex-1">
                <p className="font-medium text-sm">{root.name}</p>
                <p className="text-xs text-muted-foreground">{root.size_gb} GB | {root.created_at}</p>
              </div>
              <Badge variant="outline" className={getBackupTypeColor(root.backup_type)}>{root.backup_type}</Badge>
            </div>
            {renderChildren(nodes, root.node_id, 1)}
          </div>
        ))}
      </div>
    );
  };

  const renderChildren = (nodes: BackupNode[], parentId: string, depth: number) => {
    const children = nodes.filter(n => n.parent_id === parentId);
    if (children.length === 0) return null;
    return (
      <div className="ml-6 border-l-2 border-muted pl-4 space-y-2 mt-2">
        {children.map(child => (
          <div key={child.node_id}>
            <div className={`flex items-center gap-2 p-2.5 rounded-lg border bg-card cursor-pointer hover:bg-accent transition-colors ${
              child.backup_type === 'differential' ? 'border-orange-300' : ''
            }`}>
              {getBackupTypeIcon(child.backup_type)}
              <div className="flex-1">
                <p className="font-medium text-sm">{child.name}</p>
                <p className="text-xs text-muted-foreground">{child.size_gb} GB | {child.created_at}</p>
              </div>
              <Badge variant="outline" className={getBackupTypeColor(child.backup_type)}>{child.backup_type}</Badge>
            </div>
            {renderChildren(nodes, child.node_id, depth + 1)}
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Backup Chain Visualizer</h1>
          <p className="text-muted-foreground">Visual tree of full, incremental, and differential backup chains</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Backup Chains</CardTitle>
          </CardHeader>
          <CardContent><div className="text-2xl font-bold">{chains.length}</div></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Backups</CardTitle>
          </CardHeader>
          <CardContent><div className="text-2xl font-bold">{chainNodes.length}</div></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Size</CardTitle>
          </CardHeader>
          <CardContent><div className="text-2xl font-bold">{chainNodes.reduce((s, n) => s + n.size_gb, 0).toFixed(0)} GB</div></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Unique Restore Points</CardTitle>
          </CardHeader>
          <CardContent><div className="text-2xl font-bold">{chainNodes.length}</div></CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Backup Chain</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-1 mb-4">
              <div className="flex gap-4">
                <Badge variant="outline" className="bg-blue-100">F = Full</Badge>
                <Badge variant="outline" className="bg-green-100">I = Incremental</Badge>
                <Badge variant="outline" className="bg-orange-100">D = Differential</Badge>
              </div>
            </div>
            {renderChainTree(chainNodes.filter(n => n.parent_id === null || chainNodes.some(p => p.node_id === n.parent_id)))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Restore Point Analysis</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">Select a backup node to see the restore path</p>
            <div className="space-y-2">
              {chainNodes.filter(n => n.backup_type !== 'incremental').map(node => (
                <div key={node.node_id} className="p-3 rounded-lg border hover:bg-accent cursor-pointer transition-colors" onClick={() => setIsRestoreOpen(true)}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {getBackupTypeIcon(node.backup_type)}
                      <span className="text-sm font-medium">{node.name}</span>
                    </div>
                    <Badge variant="outline">{node.size_gb} GB</Badge>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">Est. restore: ~{node.restore_time_minutes} min</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Restore Path Details</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {restorePath.restore_path.map((step, idx) => (
              <div key={step.node_id} className="flex items-center gap-3 p-3 rounded-lg border bg-muted/50">
                <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary text-primary-foreground text-sm font-bold">
                  {idx + 1}
                </div>
                {getBackupTypeIcon(step.backup_type)}
                <div className="flex-1">
                  <p className="font-medium text-sm">{step.name}</p>
                  <p className="text-xs text-muted-foreground">{step.size_gb} GB | Est: {step.restore_time_minutes} min</p>
                </div>
                <Badge variant="outline" className={getBackupTypeColor(step.backup_type)}>{step.backup_type}</Badge>
              </div>
            ))}
          </div>
          <Separator className="my-4" />
          <div className="grid grid-cols-3 gap-4">
            <div>
              <p className="text-sm text-muted-foreground">Total Size</p>
              <p className="text-xl font-bold">{restorePath.total_size_gb} GB</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Restore Steps</p>
              <p className="text-xl font-bold">{restorePath.restore_steps}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Estimated Time</p>
              <p className="text-xl font-bold">{restorePath.estimated_restore_minutes} min</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Dialog open={isRestoreOpen} onOpenChange={setIsRestoreOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirm Restore</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <p>Restore from backup point to recover data. This will:</p>
            <ul className="list-disc pl-4 space-y-2 text-sm">
              <li>Restore {restorePath.total_size_gb} GB of data</li>
              <li>Apply {restorePath.restore_steps} backup steps</li>
              <li>Estimated time: ~{restorePath.estimated_restore_minutes} minutes</li>
            </ul>
            <div className="flex gap-2">
              <Button className="flex-1" onClick={() => setIsRestoreOpen(false)}>
                <RotateCcw className="mr-2 h-4 w-4" />
                Start Restore
              </Button>
              <Button variant="outline" onClick={() => setIsRestoreOpen(false)}>Cancel</Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default BackupChainVisualizer;
