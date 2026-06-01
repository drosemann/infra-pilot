import React, { useState } from 'react';
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
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Box, Bucket, Globe, Lock, Plus, RefreshCw, Trash2, Upload, Download, Eye } from 'lucide-react';

interface BucketInfo {
  name: string;
  backend: string;
  region: string;
  created: string;
  versioning: boolean;
  size_bytes: number;
  size_gb: number;
  object_count: number;
  policy_count: number;
  lifecycle_count: number;
}

interface GatewayStatus {
  status: string;
  total_buckets: number;
  total_objects: number;
  total_size_gb: number;
  backends_available: string[];
  backends_count: number;
  version: string;
  s3_compatible: boolean;
}

const mockBuckets: BucketInfo[] = [
  { name: 'backups', backend: 'local', region: 'us-east-1', created: '2024-01-15T00:00:00Z', versioning: true, size_bytes: 536870912000, size_gb: 500, object_count: 15234, policy_count: 2, lifecycle_count: 1 },
  { name: 'logs', backend: 'local', region: 'us-east-1', created: '2024-01-20T00:00:00Z', versioning: false, size_bytes: 107374182400, size_gb: 100, object_count: 89123, policy_count: 1, lifecycle_count: 0 },
  { name: 'media', backend: 'minio', region: 'us-east-1', created: '2024-02-01T00:00:00Z', versioning: true, size_bytes: 1099511627776, size_gb: 1024, object_count: 4567, policy_count: 3, lifecycle_count: 2 },
  { name: 'configs', backend: 'local', region: 'us-east-1', created: '2024-02-10T00:00:00Z', versioning: false, size_bytes: 5368709120, size_gb: 5, object_count: 234, policy_count: 0, lifecycle_count: 0 },
  { name: 'databases', backend: 'minio', region: 'us-west-2', created: '2024-03-01T00:00:00Z', versioning: true, size_bytes: 214748364800, size_gb: 200, object_count: 5678, policy_count: 2, lifecycle_count: 1 },
  { name: 'archives', backend: 'backblaze_b2', region: 'us-west-2', created: '2024-03-15T00:00:00Z', versioning: true, size_bytes: 2199023255552, size_gb: 2048, object_count: 12345, policy_count: 2, lifecycle_count: 2 },
  { name: 'static-assets', backend: 'wasabi', region: 'us-east-1', created: '2024-04-01T00:00:00Z', versioning: false, size_bytes: 10737418240, size_gb: 10, object_count: 890, policy_count: 1, lifecycle_count: 0 },
  { name: 'user-uploads', backend: 'minio', region: 'eu-central-1', created: '2024-04-10T00:00:00Z', versioning: true, size_bytes: 429496729600, size_gb: 400, object_count: 34567, policy_count: 3, lifecycle_count: 1 },
  { name: 'system-images', backend: 'aws_s3', region: 'us-east-1', created: '2024-05-01T00:00:00Z', versioning: false, size_bytes: 85899345920, size_gb: 80, object_count: 456, policy_count: 2, lifecycle_count: 1 },
  { name: 'analytics-data', backend: 'gcs', region: 'us-central1', created: '2024-05-15T00:00:00Z', versioning: true, size_bytes: 161061273600, size_gb: 150, object_count: 67890, policy_count: 1, lifecycle_count: 0 },
];

const ObjectStorageGateway: React.FC = () => {
  const [buckets] = useState<BucketInfo[]>(mockBuckets);
  const [selectedBucket, setSelectedBucket] = useState<BucketInfo | null>(null);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [newBucketName, setNewBucketName] = useState('');
  const [newBucketBackend, setNewBucketBackend] = useState('local');
  const [newBucketRegion, setNewBucketRegion] = useState('us-east-1');

  const gatewayStatus: GatewayStatus = {
    status: 'online',
    total_buckets: buckets.length,
    total_objects: buckets.reduce((s, b) => s + b.object_count, 0),
    total_size_gb: Math.round(buckets.reduce((s, b) => s + b.size_gb, 0)),
    backends_available: ['local', 'aws_s3', 'backblaze_b2', 'wasabi', 'minio', 'gcs', 'azure_blob', 'ceph_rgw'],
    backends_count: 8,
    version: '1.0.0',
    s3_compatible: true,
  };

  const getBackendColor = (backend: string) => {
    const colors: Record<string, string> = {
      local: 'bg-gray-500',
      minio: 'bg-red-500',
      aws_s3: 'bg-orange-500',
      backblaze_b2: 'bg-blue-500',
      wasabi: 'bg-green-500',
      gcs: 'bg-yellow-500',
      azure_blob: 'bg-indigo-500',
      ceph_rgw: 'bg-purple-500',
    };
    return colors[backend] || 'bg-gray-500';
  };

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Object Storage Gateway</h1>
          <p className="text-muted-foreground">S3-compatible gateway with bucket policies and lifecycle management</p>
        </div>
        <div className="flex gap-2">
          <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Create Bucket
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create Bucket</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium">Bucket Name</label>
                  <Input value={newBucketName} onChange={e => setNewBucketName(e.target.value)} placeholder="my-bucket" />
                </div>
                <div>
                  <label className="text-sm font-medium">Backend</label>
                  <select className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm" value={newBucketBackend} onChange={e => setNewBucketBackend(e.target.value)}>
                    <option value="local">Local Filesystem</option>
                    <option value="minio">Minio</option>
                    <option value="aws_s3">AWS S3</option>
                    <option value="backblaze_b2">Backblaze B2</option>
                    <option value="wasabi">Wasabi</option>
                    <option value="gcs">Google Cloud Storage</option>
                  </select>
                </div>
                <div>
                  <label className="text-sm font-medium">Region</label>
                  <select className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm" value={newBucketRegion} onChange={e => setNewBucketRegion(e.target.value)}>
                    <option value="us-east-1">US East (N. Virginia)</option>
                    <option value="us-west-2">US West (Oregon)</option>
                    <option value="eu-central-1">EU (Frankfurt)</option>
                    <option value="eu-west-1">EU (Ireland)</option>
                    <option value="ap-southeast-1">Asia Pacific (Singapore)</option>
                  </select>
                </div>
                <Button className="w-full" disabled={!newBucketName}>Create Bucket</Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Gateway Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-green-500" />
              <span className="text-lg font-bold">{gatewayStatus.status}</span>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Buckets</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{gatewayStatus.total_buckets}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Objects</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{gatewayStatus.total_objects.toLocaleString()}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Size</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{gatewayStatus.total_size_gb} GB</div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Buckets</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Backend</TableHead>
                  <TableHead>Region</TableHead>
                  <TableHead>Versioning</TableHead>
                  <TableHead>Objects</TableHead>
                  <TableHead>Size</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {buckets.map(bucket => (
                  <TableRow key={bucket.name} className="cursor-pointer" onClick={() => setSelectedBucket(bucket)}>
                    <TableCell className="font-medium">
                      <div className="flex items-center gap-2">
                        <Bucket className="h-4 w-4" />
                        {bucket.name}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className={getBackendColor(bucket.backend)}>
                        {bucket.backend.replace('_', ' ')}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-xs">{bucket.region}</TableCell>
                    <TableCell>
                      {bucket.versioning ? <Lock className="h-4 w-4 text-green-500" /> : <Lock className="h-4 w-4 text-gray-400" />}
                    </TableCell>
                    <TableCell>{bucket.object_count.toLocaleString()}</TableCell>
                    <TableCell>{bucket.size_gb} GB</TableCell>
                    <TableCell>
                      <Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); setSelectedBucket(bucket); }}>
                        <Eye className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Backends</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {gatewayStatus.backends_available.map(backend => (
                <div key={backend} className="flex items-center gap-3 p-2 rounded-lg hover:bg-accent">
                  <div className={`h-3 w-3 rounded-full ${getBackendColor(backend)}`} />
                  <span className="text-sm capitalize">{backend.replace('_', ' ')}</span>
                  {backend === 'minio' && <Badge className="ml-auto">active</Badge>}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {selectedBucket && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Bucket Details: {selectedBucket.name}</CardTitle>
              <Button variant="outline" size="sm" onClick={() => setSelectedBucket(null)}>Close</Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              <div>
                <p className="text-sm text-muted-foreground">Backend</p>
                <p className="font-medium">{selectedBucket.backend}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Region</p>
                <p className="font-medium">{selectedBucket.region}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Created</p>
                <p className="font-medium">{new Date(selectedBucket.created).toLocaleDateString()}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Versioning</p>
                <p className="font-medium">{selectedBucket.versioning ? 'Enabled' : 'Disabled'}</p>
              </div>
            </div>
            <Separator className="my-4" />
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">Object Count</p>
                <p className="text-2xl font-bold">{selectedBucket.object_count.toLocaleString()}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Total Size</p>
                <p className="text-2xl font-bold">{selectedBucket.size_gb} GB</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Policies</p>
                <p className="text-2xl font-bold">{selectedBucket.policy_count}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Lifecycle Rules</p>
                <p className="text-2xl font-bold">{selectedBucket.lifecycle_count}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default ObjectStorageGateway;
