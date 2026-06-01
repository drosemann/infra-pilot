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
import { Shield, Lock, FileText, AlertTriangle, CheckCircle, Clock, HardDrive, Plus, Trash2, Eye, EyeOff } from 'lucide-react';

interface VaultObject {
  object_id: string;
  name: string;
  bucket: string;
  size_bytes: number;
  size_mb: number;
  checksum: string;
  created_at: string;
  retention_until: string;
  locked: boolean;
  access_count: number;
  days_until_expiry: number;
}

interface RetentionPolicy {
  policy_id: string;
  name: string;
  retention_days: number;
  compliance_hold: boolean;
  legal_hold: boolean;
}

const mockObjects: VaultObject[] = [
  { object_id: 'obj-001', name: 'backup-2024-05-28-full.sql.gz', bucket: 'db-backups', size_bytes: 1073741824, size_mb: 1024, checksum: 'a1b2c3d4...', created_at: '2024-05-28T06:00:00Z', retention_until: '2024-06-27T06:00:00Z', locked: true, access_count: 3, days_until_expiry: 29 },
  { object_id: 'obj-002', name: 'logs-2024-05-archive.tar', bucket: 'log-archive', size_bytes: 5368709120, size_mb: 5120, checksum: 'e5f6g7h8...', created_at: '2024-05-01T00:00:00Z', retention_until: '2025-05-01T00:00:00Z', locked: true, access_count: 1, days_until_expiry: 337 },
  { object_id: 'obj-003', name: 'financial-2024-q1-report.pdf', bucket: 'compliance', size_bytes: 52428800, size_mb: 50, checksum: 'i9j0k1l2...', created_at: '2024-04-01T00:00:00Z', retention_until: '2034-04-01T00:00:00Z', locked: true, access_count: 5, days_until_expiry: 3594 },
  { object_id: 'obj-004', name: 'user-data-export-2024-05.csv', bucket: 'exports', size_bytes: 268435456, size_mb: 256, checksum: 'm3n4o5p6...', created_at: '2024-05-15T00:00:00Z', retention_until: '2024-08-13T00:00:00Z', locked: false, access_count: 12, days_until_expiry: 76 },
  { object_id: 'obj-005', name: 'system-image-v3.2.1.iso', bucket: 'images', size_bytes: 4294967296, size_mb: 4096, checksum: 'q7r8s9t0...', created_at: '2024-03-10T00:00:00Z', retention_until: '2025-03-10T00:00:00Z', locked: true, access_count: 8, days_until_expiry: 284 },
];

const mockPolicies: RetentionPolicy[] = [
  { policy_id: 'pol-daily', name: 'Daily Backups (30 days)', retention_days: 30, compliance_hold: false, legal_hold: false },
  { policy_id: 'pol-weekly', name: 'Weekly Backups (90 days)', retention_days: 90, compliance_hold: true, legal_hold: false },
  { policy_id: 'pol-monthly', name: 'Monthly Backups (1 year)', retention_days: 365, compliance_hold: false, legal_hold: false },
  { policy_id: 'pol-yearly', name: 'Yearly Backups (7 years)', retention_days: 2555, compliance_hold: true, legal_hold: false },
  { policy_id: 'pol-legal', name: 'Legal Hold', retention_days: 0, compliance_hold: true, legal_hold: true },
];

const ImmutableVault: React.FC = () => {
  const [objects] = useState<VaultObject[]>(mockObjects);
  const [policies] = useState<RetentionPolicy[]>(mockPolicies);
  const [selectedObject, setSelectedObject] = useState<VaultObject | null>(null);
  const [isLockDialogOpen, setIsLockDialogOpen] = useState(false);
  const [showLockConfirm, setShowLockConfirm] = useState(false);

  const totalSize = objects.reduce((s, o) => s + o.size_bytes, 0);
  const lockedCount = objects.filter(o => o.locked).length;
  const daysUntilExpiry = Math.min(...objects.map(o => o.days_until_expiry));

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Immutable Backup Vault</h1>
          <p className="text-muted-foreground">WORM storage with object lock, retention policies, and air-gapped recovery</p>
        </div>
        <div className="flex gap-2">
          <Badge variant="outline" className="text-yellow-600 bg-yellow-50">
            <Shield className="mr-1 h-4 w-4" />Compliance Mode
          </Badge>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Vault Status</CardTitle></CardHeader><CardContent><div className="flex items-center gap-2"><div className="h-2 w-2 rounded-full bg-green-500" /><span className="text-lg font-bold">Compliant</span></div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Stored Objects</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{objects.length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Locked Objects</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{lockedCount}/{objects.length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Total Size</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{(totalSize / (1024**3)).toFixed(1)} GB</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Min Expiry</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{daysUntilExpiry}d</div></CardContent></Card>
      </div>

      <Tabs defaultValue="objects">
        <TabsList>
          <TabsTrigger value="objects">Vault Objects</TabsTrigger>
          <TabsTrigger value="policies">Retention Policies</TabsTrigger>
          <TabsTrigger value="airgap">Air-Gapped Recovery</TabsTrigger>
        </TabsList>

        <TabsContent value="objects">
          <Card>
            <CardHeader><CardTitle>WORM Storage Objects</CardTitle></CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Bucket</TableHead>
                    <TableHead>Size</TableHead>
                    <TableHead>Retention Until</TableHead>
                    <TableHead>Locked</TableHead>
                    <TableHead>Expires</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {objects.map(obj => (
                    <TableRow key={obj.object_id} className="cursor-pointer" onClick={() => setSelectedObject(obj)}>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Lock className={`h-4 w-4 ${obj.locked ? 'text-green-500' : 'text-gray-400'}`} />
                          <span className="font-medium text-sm">{obj.name}</span>
                        </div>
                      </TableCell>
                      <TableCell><Badge variant="outline" className="text-xs">{obj.bucket}</Badge></TableCell>
                      <TableCell>{obj.size_mb >= 1024 ? `${(obj.size_mb/1024).toFixed(1)} GB` : `${obj.size_mb.toFixed(0)} MB`}</TableCell>
                      <TableCell className="text-xs">{new Date(obj.retention_until).toLocaleDateString()}</TableCell>
                      <TableCell>
                        {obj.locked ? <Lock className="h-4 w-4 text-green-500" /> : <EyeOff className="h-4 w-4 text-gray-400" />}
                      </TableCell>
                      <TableCell>
                        <Badge variant={obj.days_until_expiry < 30 ? 'destructive' : obj.days_until_expiry < 90 ? 'secondary' : 'outline'}>
                          {obj.days_until_expiry}d
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); setSelectedObject(obj); }}>
                          <Eye className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="policies">
          <Card>
            <CardHeader><CardTitle>Retention Policies</CardTitle></CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Retention Days</TableHead>
                    <TableHead>Compliance Hold</TableHead>
                    <TableHead>Legal Hold</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {policies.map(pol => (
                    <TableRow key={pol.policy_id}>
                      <TableCell className="font-medium">{pol.name}</TableCell>
                      <TableCell>{pol.retention_days > 0 ? `${pol.retention_days} days` : 'Indefinite'}</TableCell>
                      <TableCell>{pol.compliance_hold ? <CheckCircle className="h-4 w-4 text-green-500" /> : '-'}</TableCell>
                      <TableCell>{pol.legal_hold ? <AlertTriangle className="h-4 w-4 text-yellow-500" /> : '-'}</TableCell>
                      <TableCell><Badge variant="default">Active</Badge></TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="airgap">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader><CardTitle>Air-Gapped Recovery Vault</CardTitle></CardHeader>
              <CardContent className="space-y-4">
                <div className="p-4 rounded-lg bg-yellow-50 dark:bg-yellow-950 border border-yellow-200">
                  <div className="flex items-center gap-2 mb-2">
                    <Shield className="h-5 w-5 text-yellow-600" />
                    <span className="font-medium text-yellow-800 dark:text-yellow-200">Air-Gapped</span>
                  </div>
                  <p className="text-sm text-yellow-700 dark:text-yellow-300">This vault requires physical access to the storage media. No network connectivity available.</p>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between"><span className="text-sm text-muted-foreground">Location</span><span className="text-sm font-medium">Building A, Room 101 - Physical Safe</span></div>
                  <div className="flex justify-between"><span className="text-sm text-muted-foreground">Last Access</span><span className="text-sm font-medium">30 days ago</span></div>
                  <div className="flex justify-between"><span className="text-sm text-muted-foreground">Media Type</span><span className="text-sm font-medium">LTO-9 Tapes</span></div>
                  <div className="flex justify-between"><span className="text-sm text-muted-foreground">Capacity</span><span className="text-sm font-medium">45 TB / 180 TB</span></div>
                </div>
                <Separator />
                <h4 className="font-medium text-sm">Recovery Procedure</h4>
                <ol className="list-decimal pl-4 space-y-1 text-sm">
                  <li>Retrieve physical media from safe</li>
                  <li>Connect to isolated recovery workstation</li>
                  <li>Authenticate with hardware security key</li>
                  <li>Run recovery script from signed USB drive</li>
                  <li>Verify data integrity checksums</li>
                  <li>Transfer to production via isolated network</li>
                </ol>
              </CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle>Compliance Status</CardTitle></CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between p-3 rounded-lg bg-green-50 dark:bg-green-950 border border-green-200">
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-5 w-5 text-green-500" />
                    <span className="font-medium">SEC Rule 17a-4</span>
                  </div>
                  <Badge variant="default">Compliant</Badge>
                </div>
                <div className="flex items-center justify-between p-3 rounded-lg bg-green-50 dark:bg-green-950 border border-green-200">
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-5 w-5 text-green-500" />
                    <span className="font-medium">GDPR Data Retention</span>
                  </div>
                  <Badge variant="default">Compliant</Badge>
                </div>
                <div className="flex items-center justify-between p-3 rounded-lg bg-green-50 dark:bg-green-950 border border-green-200">
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-5 w-5 text-green-500" />
                    <span className="font-medium">PCI DSS Requirement 3</span>
                  </div>
                  <Badge variant="default">Compliant</Badge>
                </div>
                <div className="flex items-center justify-between p-3 rounded-lg bg-yellow-50 dark:bg-yellow-950 border border-yellow-200">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="h-5 w-5 text-yellow-500" />
                    <span className="font-medium">HIPAA Backup Required</span>
                  </div>
                  <Badge variant="secondary">Pending Review</Badge>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default ImmutableVault;
