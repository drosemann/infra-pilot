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
import { Share2, Link, Lock, Clock, Download, Upload, Trash2, Plus, Globe, FileText } from 'lucide-react';

interface ShareLink {
  share_id: string;
  filename: string;
  path: string;
  created_by: string;
  created_at: string;
  expires_at: string;
  has_password: boolean;
  max_downloads: number;
  download_count: number;
  size_bytes: number;
  size_mb: number;
  is_upload_only: boolean;
}

interface IntegrationConfig {
  name: string;
  enabled: boolean;
  api_url: string;
  status: string;
}

const mockShares: ShareLink[] = [
  { share_id: 'share-001', filename: 'backup-2024-05-28.tar.gz', path: '/backups/server01/', created_by: 'admin', created_at: '2024-05-28T10:00:00Z', expires_at: '2024-06-04T10:00:00Z', has_password: true, max_downloads: 5, download_count: 2, size_bytes: 536870912, size_mb: 512, is_upload_only: false },
  { share_id: 'share-002', filename: 'logs-2024-05.zip', path: '/logs/nginx/', created_by: 'admin', created_at: '2024-05-27T08:00:00Z', expires_at: '2024-06-03T08:00:00Z', has_password: false, max_downloads: 0, download_count: 8, size_bytes: 104857600, size_mb: 100, is_upload_only: false },
  { share_id: 'share-003', filename: 'Upload Folder - Team Alpha', path: '/shares/team-alpha/', created_by: 'team-lead', created_at: '2024-05-25T14:00:00Z', expires_at: '2024-06-25T14:00:00Z', has_password: true, max_downloads: 0, download_count: 0, size_bytes: 0, size_mb: 0, is_upload_only: true },
  { share_id: 'share-004', filename: 'config-backup.json', path: '/config/production/', created_by: 'devops', created_at: '2024-05-26T16:00:00Z', expires_at: '2024-06-02T16:00:00Z', has_password: false, max_downloads: 10, download_count: 3, size_bytes: 5242880, size_mb: 5, is_upload_only: false },
  { share_id: 'share-005', filename: 'modpack-v2.1.zip', path: '/modpacks/minecraft/', created_by: 'content-creator', created_at: '2024-05-24T12:00:00Z', expires_at: '2024-06-24T12:00:00Z', has_password: false, max_downloads: 100, download_count: 45, size_bytes: 2147483648, size_mb: 2048, is_upload_only: false },
];

const FileSharing: React.FC = () => {
  const [shares, setShares] = useState<ShareLink[]>(mockShares);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isPasswordOpen, setIsPasswordOpen] = useState(false);
  const [selectedShare, setSelectedShare] = useState<ShareLink | null>(null);
  const [password, setPassword] = useState('');
  const [newShareFilename, setNewShareFilename] = useState('');
  const [newSharePath, setNewSharePath] = useState('/shares/');
  const [newShareExpiry, setNewShareExpiry] = useState(7);
  const [newSharePassword, setNewSharePassword] = useState('');

  const integrations: IntegrationConfig[] = [
    { name: 'Nextcloud', enabled: true, api_url: 'https://nextcloud.internal', status: 'connected' },
    { name: 'Seafile', enabled: false, api_url: '', status: 'disconnected' },
    { name: 'ownCloud', enabled: false, api_url: '', status: 'disconnected' },
  ];

  const handleCreateShare = () => {
    const share: ShareLink = {
      share_id: `share-${Date.now()}`,
      filename: newShareFilename,
      path: newSharePath,
      created_by: 'current-user',
      created_at: new Date().toISOString(),
      expires_at: new Date(Date.now() + newShareExpiry * 86400000).toISOString(),
      has_password: !!newSharePassword,
      max_downloads: 0,
      download_count: 0,
      size_bytes: 1024 * 1024 * 10,
      size_mb: 10,
      is_upload_only: false,
    };
    setShares([share, ...shares]);
    setIsCreateOpen(false);
    setNewShareFilename('');
    setNewSharePassword('');
  };

  const handleDeleteShare = (shareId: string) => {
    setShares(shares.filter(s => s.share_id !== shareId));
  };

  const handleVerifyPassword = () => {
    if (password === 'test1234') {
      setIsPasswordOpen(false);
      setPassword('');
    }
  };

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">File Sharing & Sync</h1>
          <p className="text-muted-foreground">Nextcloud/Seafile integration with share links, passwords, and cross-server sync</p>
        </div>
        <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
          <DialogTrigger asChild>
            <Button><Plus className="mr-2 h-4 w-4" />Create Share Link</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>Create Share Link</DialogTitle></DialogHeader>
            <div className="space-y-4">
              <div>
                <Label>Filename / Folder</Label>
                <Input value={newShareFilename} onChange={e => setNewShareFilename(e.target.value)} placeholder="my-file.zip" />
              </div>
              <div>
                <Label>Path</Label>
                <Input value={newSharePath} onChange={e => setNewSharePath(e.target.value)} />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Expires (days)</Label>
                  <Input type="number" value={newShareExpiry} onChange={e => setNewShareExpiry(parseInt(e.target.value) || 7)} min={1} />
                </div>
                <div>
                  <Label>Password (optional)</Label>
                  <Input type="password" value={newSharePassword} onChange={e => setNewSharePassword(e.target.value)} placeholder="Leave empty for no password" />
                </div>
              </div>
              <Button className="w-full" disabled={!newShareFilename} onClick={handleCreateShare}>
                <Link className="mr-2 h-4 w-4" />Generate Share Link
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Active Shares</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">{shares.filter(s => new Date(s.expires_at) > new Date()).length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Total Downloads</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">{shares.reduce((s, sh) => s + sh.download_count, 0)}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Password Protected</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">{shares.filter(s => s.has_password).length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Integrations</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">{integrations.filter(i => i.enabled).length}/{integrations.length}</div></CardContent></Card>
      </div>

      <Tabs defaultValue="shares">
        <TabsList>
          <TabsTrigger value="shares">Share Links</TabsTrigger>
          <TabsTrigger value="integrations">Integrations</TabsTrigger>
          <TabsTrigger value="sync">Cross-Server Sync</TabsTrigger>
        </TabsList>

        <TabsContent value="shares">
          <Card>
            <CardHeader><CardTitle>File Shares</CardTitle></CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>File</TableHead>
                    <TableHead>Size</TableHead>
                    <TableHead>Expires</TableHead>
                    <TableHead>Downloads</TableHead>
                    <TableHead>Password</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {shares.map(share => (
                    <TableRow key={share.share_id}>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {share.is_upload_only ? <Upload className="h-4 w-4 text-blue-500" /> : <FileText className="h-4 w-4" />}
                          <div>
                            <p className="font-medium text-sm">{share.filename}</p>
                            <p className="text-xs text-muted-foreground">{share.path}</p>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>{share.size_mb >= 1024 ? `${(share.size_mb/1024).toFixed(1)} GB` : `${share.size_mb.toFixed(0)} MB`}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          <span className="text-xs">{new Date(share.expires_at).toLocaleDateString()}</span>
                        </div>
                      </TableCell>
                      <TableCell>{share.download_count}{share.max_downloads > 0 ? `/${share.max_downloads}` : ''}</TableCell>
                      <TableCell>{share.has_password ? <Lock className="h-4 w-4 text-green-500" /> : <Lock className="h-4 w-4 text-gray-400" />}</TableCell>
                      <TableCell>
                        <div className="flex gap-2">
                          <Button variant="outline" size="sm" onClick={() => { setSelectedShare(share); navigator.clipboard?.writeText(`${window.location.origin}/share/${share.share_id}`); }}>
                            <Link className="h-4 w-4" />
                          </Button>
                          <Button variant="destructive" size="sm" onClick={() => handleDeleteShare(share.share_id)}>
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="integrations">
          <Card>
            <CardHeader><CardTitle>Cloud Integration Platforms</CardTitle></CardHeader>
            <CardContent>
              <div className="space-y-4">
                {integrations.map(intg => (
                  <div key={intg.name} className="flex items-center justify-between p-4 rounded-lg border">
                    <div className="flex items-center gap-3">
                      <Globe className="h-6 w-6" />
                      <div>
                        <p className="font-medium">{intg.name}</p>
                        <p className="text-sm text-muted-foreground">{intg.api_url || 'Not configured'}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <Badge variant={intg.enabled ? 'default' : 'secondary'}>{intg.status}</Badge>
                      <Button variant="outline" size="sm">{intg.enabled ? 'Configure' : 'Enable'}</Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="sync">
          <Card>
            <CardHeader><CardTitle>Cross-Server Sync</CardTitle></CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="p-4 rounded-lg bg-muted">
                  <p className="font-medium">Sync Status</p>
                  <p className="text-sm text-muted-foreground">All servers are in sync. Last sync: 5 minutes ago.</p>
                </div>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Server</TableHead>
                      <TableHead>Sync Status</TableHead>
                      <TableHead>Files Pending</TableHead>
                      <TableHead>Last Sync</TableHead>
                      <TableHead>Bandwidth</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    <TableRow><TableCell>Server-01 (Primary)</TableCell><TableCell><Badge variant="default">In Sync</Badge></TableCell><TableCell>0</TableCell><TableCell>2 min ago</TableCell><TableCell>-</TableCell></TableRow>
                    <TableRow><TableCell>Server-02 (EU-West)</TableCell><TableCell><Badge variant="default">In Sync</Badge></TableCell><TableCell>0</TableCell><TableCell>5 min ago</TableCell><TableCell>45 Mbps</TableCell></TableRow>
                    <TableRow><TableCell>Server-03 (US-East)</TableCell><TableCell><Badge variant="secondary">Syncing</Badge></TableCell><TableCell>12</TableCell><TableCell>Now</TableCell><TableCell>120 Mbps</TableCell></TableRow>
                    <TableRow><TableCell>Server-04 (APAC)</TableCell><TableCell><Badge variant="outline">Pending</Badge></TableCell><TableCell>234</TableCell><TableCell>1 hour ago</TableCell><TableCell>-</TableCell></TableRow>
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default FileSharing;
