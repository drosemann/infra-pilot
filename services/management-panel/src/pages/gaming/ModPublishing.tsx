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
import { Package, Download, Upload, Star, GitBranch, Globe, FileCode, CheckCircle, AlertTriangle, Clock, ArrowUpCircle } from 'lucide-react';

interface ModVersion {
  version_id: string;
  mod_name: string;
  version: string;
  game: string;
  downloads: number;
  size_mb: number;
  created_at: string;
  status: string;
  dependencies: string[];
  conflicts: string[];
  rating: number;
  downloads_total: number;
}

const mockMods: ModVersion[] = [
  { version_id: 'mod-001', mod_name: 'BetterCombat', version: '2.4.1', game: 'minecraft', downloads: 1280, size_mb: 2.4, created_at: '2024-05-28T00:00:00Z', status: 'published', dependencies: ['fabric-api'], conflicts: ['old-combat'], rating: 4.7, downloads_total: 45000 },
  { version_id: 'mod-002', mod_name: 'WorldGenPlus', version: '1.8.0', game: 'minecraft', downloads: 456, size_mb: 8.1, created_at: '2024-05-25T00:00:00Z', status: 'published', dependencies: ['terraform-api'], conflicts: [], rating: 4.2, downloads_total: 12300 },
  { version_id: 'mod-003', mod_name: 'MiniMap Pro', version: '3.1.0', game: 'minecraft', downloads: 2340, size_mb: 1.8, created_at: '2024-05-20T00:00:00Z', status: 'published', dependencies: [], conflicts: ['voxelmap'], rating: 4.9, downloads_total: 89000 },
  { version_id: 'mod-004', mod_name: 'CustomUI Pack', version: '0.9.0', game: 'minecraft', downloads: 89, size_mb: 5.3, created_at: '2024-05-29T00:00:00Z', status: 'draft', dependencies: [], conflicts: [], rating: 0, downloads_total: 89 },
  { version_id: 'mod-005', mod_name: 'AntiCheat Addon', version: '1.2.0', game: 'minecraft', downloads: 567, size_mb: 0.9, created_at: '2024-05-22T00:00:00Z', status: 'published', dependencies: ['sentinel-api'], conflicts: ['eac-addon'], rating: 3.8, downloads_total: 15600 },
  { version_id: 'mod-006', mod_name: 'EconomyBridge', version: '2.0.1', game: 'minecraft', downloads: 1234, size_mb: 3.2, created_at: '2024-05-18T00:00:00Z', status: 'published', dependencies: ['vault-api'], conflicts: [], rating: 4.5, downloads_total: 34200 },
];

const ModPublishing: React.FC = () => {
  const [mods, setMods] = useState<ModVersion[]>(mockMods);
  const [selectedMod, setSelectedMod] = useState<ModVersion | null>(null);
  const [isCreateOpen, setIsCreateOpen] = useState(false);

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Mod Publishing</h1>
          <p className="text-muted-foreground">Mod versioning, dependency graph, CurseForge/Modrinth sync</p>
        </div>
        <Button onClick={() => setIsCreateOpen(true)}><Package className="mr-2 h-4 w-4" />New Mod</Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Total Mods</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{mods.length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Published</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-green-500">{mods.filter(m => m.status === 'published').length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Total Downloads</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{mods.reduce((s, m) => s + m.downloads_total, 0).toLocaleString()}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Avg Rating</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{(mods.reduce((s, m) => s + m.rating, 0) / mods.filter(m => m.rating > 0).length).toFixed(1)}</div></CardContent></Card>
      </div>

      <Card>
        <CardHeader><CardTitle>Mod Library</CardTitle></CardHeader>
        <CardContent>
          <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Mod</TableHead>
                    <TableHead>Version</TableHead>
                    <TableHead>Downloads</TableHead>
                    <TableHead>Size</TableHead>
                    <TableHead>Dependencies</TableHead>
                    <TableHead>Rating</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
            <TableBody>
              {mods.map(mod => (
                <TableRow key={mod.version_id}>
                  <TableCell className="font-medium">
                    <div className="flex items-center gap-2">
                      <Package className="h-4 w-4 text-muted-foreground" />
                      {mod.mod_name}
                    </div>
                  </TableCell>
                  <TableCell><Badge variant="outline" className="font-mono text-xs">v{mod.version}</Badge></TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Download className="h-3 w-3" />
                      {mod.downloads_total.toLocaleString()}
                    </div>
                  </TableCell>
                  <TableCell>{mod.size_mb.toFixed(1)} MB</TableCell>
                  <TableCell>
                    <div className="flex gap-1 flex-wrap">
                      {mod.dependencies.length > 0 ? mod.dependencies.map(d => <Badge key={d} variant="secondary" className="text-xs">{d}</Badge>) : <span className="text-xs text-muted-foreground">None</span>}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1">
                      <Star className={`h-3 w-3 ${mod.rating >= 4 ? 'text-yellow-500 fill-yellow-500' : 'text-gray-300'}`} />
                      <span className="text-xs">{mod.rating > 0 ? mod.rating.toFixed(1) : '-'}</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant={mod.status === 'published' ? 'default' : 'secondary'}>{mod.status}</Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex gap-1">
                      <Button size="sm" variant="ghost" onClick={() => setSelectedMod(mod)}><Globe className="h-4 w-4" /></Button>
                      <Button size="sm" variant="ghost"><Upload className="h-4 w-4" /></Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Dialog open={!!selectedMod} onOpenChange={() => setSelectedMod(null)}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader><DialogTitle>{selectedMod?.mod_name} v{selectedMod?.version}</DialogTitle></DialogHeader>
          {selectedMod && (
            <div className="space-y-4">
              <div className="flex gap-2">
                <Badge>{selectedMod.game}</Badge>
                <Badge variant="outline">v{selectedMod.version}</Badge>
                <Badge variant={selectedMod.status === 'published' ? 'default' : 'secondary'}>{selectedMod.status}</Badge>
              </div>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div><strong>Downloads:</strong> {selectedMod.downloads_total.toLocaleString()}</div>
                <div><strong>Size:</strong> {selectedMod.size_mb} MB</div>
                <div><strong>Rating:</strong> {selectedMod.rating > 0 ? `${selectedMod.rating}/5` : 'Not rated'}</div>
                <div><strong>Created:</strong> {new Date(selectedMod.created_at).toLocaleDateString()}</div>
              </div>
              <div>
                <h4 className="font-medium text-sm mb-1">Dependencies</h4>
                <div className="flex gap-1 flex-wrap">
                  {selectedMod.dependencies.length > 0 ? selectedMod.dependencies.map(d => <Badge key={d} variant="secondary">{d}</Badge>) : <span className="text-sm text-muted-foreground">None</span>}
                </div>
              </div>
              {selectedMod.conflicts.length > 0 && (
                <div>
                  <h4 className="font-medium text-sm mb-1">Conflicts</h4>
                  <div className="flex gap-1 flex-wrap">
                    {selectedMod.conflicts.map(c => <Badge key={c} variant="destructive">{c}</Badge>)}
                  </div>
                </div>
              )}
              <div className="flex gap-2">
                <Button variant="default" className="flex-1"><Download className="mr-2 h-4 w-4" />Download</Button>
                <Button variant="outline" className="flex-1">Sync to CurseForge</Button>
                <Button variant="outline" className="flex-1">Sync to Modrinth</Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>Publish New Mod</DialogTitle></DialogHeader>
          <div className="space-y-4">
            <div><Label>Mod Name</Label><Input placeholder="My Awesome Mod" /></div>
            <div><Label>Version</Label><Input placeholder="1.0.0" /></div>
            <div><Label>Game</Label><select className="w-full p-2 rounded-md border"><option value="minecraft">Minecraft</option></select></div>
            <div><Label>Upload File</Label><Input type="file" /></div>
            <Button className="w-full">Upload & Publish</Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ModPublishing;
