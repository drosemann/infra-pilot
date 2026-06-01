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
} from '@/components/ui/dialog';
import { Scan, Archive, Percent, BarChart3, HardDrive, Zap, CheckCircle, Clock, AlertCircle } from 'lucide-react';

interface VolumeStats {
  volume_id: string;
  path: string;
  total_gb: number;
  used_gb: number;
  dedup_ratio: number;
  compression_ratio: number;
  savings_gb: number;
  algorithm: string;
  status: string;
  chunks: number;
  unique_chunks: number;
  last_run: string | null;
  throughput_mbps: number;
}

const mockVolumes: VolumeStats[] = [
  { volume_id: 'vol-docker-001', path: '/var/lib/docker/volumes/app-data', total_gb: 500, used_gb: 340, dedup_ratio: 3.2, compression_ratio: 2.1, savings_gb: 213, algorithm: 'zstd', status: 'active', chunks: 45000, unique_chunks: 14062, last_run: '2024-05-29T00:00:00Z', throughput_mbps: 850 },
  { volume_id: 'vol-pg-001', path: '/var/lib/postgresql/16/main', total_gb: 200, used_gb: 180, dedup_ratio: 1.1, compression_ratio: 1.8, savings_gb: 98, algorithm: 'lz4', status: 'active', chunks: 28000, unique_chunks: 25454, last_run: '2024-05-29T00:00:00Z', throughput_mbps: 1200 },
  { volume_id: 'vol-backup-001', path: '/mnt/backup/weekly', total_gb: 2000, used_gb: 1900, dedup_ratio: 8.5, compression_ratio: 3.4, savings_gb: 1672, algorithm: 'zstd', status: 'active', chunks: 320000, unique_chunks: 37647, last_run: '2024-05-28T00:00:00Z', throughput_mbps: 450 },
  { volume_id: 'vol-logs-001', path: '/var/log/containers', total_gb: 100, used_gb: 95, dedup_ratio: 12.1, compression_ratio: 5.2, savings_gb: 87, algorithm: 'zstd', status: 'active', chunks: 22000, unique_chunks: 1818, last_run: '2024-05-29T00:00:00Z', throughput_mbps: 2100 },
  { volume_id: 'vol-media-001', path: '/mnt/media/images', total_gb: 5000, used_gb: 4800, dedup_ratio: 1.5, compression_ratio: 1.1, savings_gb: 320, algorithm: 'lz4', status: 'paused', chunks: 850000, unique_chunks: 566666, last_run: '2024-05-27T00:00:00Z', throughput_mbps: 600 },
];

const DedupCompression: React.FC = () => {
  const [volumes, setVolumes] = useState<VolumeStats[]>(mockVolumes);
  const [activeTab, setActiveTab] = useState('volumes');

  const totalSavings = volumes.reduce((s, v) => s + v.savings_gb, 0);
  const totalDedup = volumes.reduce((s, v) => s + v.dedup_ratio, 0) / volumes.length;
  const totalCompression = volumes.reduce((s, v) => s + v.compression_ratio, 0) / volumes.length;

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Deduplication & Compression</h1>
          <p className="text-muted-foreground">Inline ZSTD/LZ4 dedup for container volumes with chunk-level analysis</p>
        </div>
        <Badge variant="secondary" className="text-lg px-4 py-2">
          <Percent className="mr-2 h-4 w-4" />{((totalSavings / volumes.reduce((s, v) => s + v.used_gb, 0)) * 100).toFixed(0)}% Savings
        </Badge>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Total Savings</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-green-500">{totalSavings.toFixed(0)} GB</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Avg Dedup Ratio</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{totalDedup.toFixed(1)}x</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Avg Compression</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{totalCompression.toFixed(1)}x</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Total Chunks</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{volumes.reduce((s, v) => s + v.chunks, 0).toLocaleString()}</div></CardContent></Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="volumes">Volumes</TabsTrigger>
          <TabsTrigger value="policies">Policies</TabsTrigger>
          <TabsTrigger value="stats">Statistics</TabsTrigger>
        </TabsList>

        <TabsContent value="volumes">
          <Card>
            <CardHeader><CardTitle>Managed Volumes</CardTitle></CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Volume</TableHead>
                    <TableHead>Algorithm</TableHead>
                    <TableHead>Dedup</TableHead>
                    <TableHead>Compress</TableHead>
                    <TableHead>Savings</TableHead>
                    <TableHead>Chunks</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Throughput</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {volumes.map(vol => (
                    <TableRow key={vol.volume_id}>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <HardDrive className="h-4 w-4 text-muted-foreground" />
                          <div>
                            <div className="font-medium text-sm">{vol.volume_id}</div>
                            <div className="text-xs text-muted-foreground">{vol.path}</div>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell><Badge variant="outline">{vol.algorithm}</Badge></TableCell>
                      <TableCell>{vol.dedup_ratio.toFixed(1)}x</TableCell>
                      <TableCell>{vol.compression_ratio.toFixed(1)}x</TableCell>
                      <TableCell className="text-green-500 font-medium">{vol.savings_gb.toFixed(0)} GB</TableCell>
                      <TableCell className="text-xs">{vol.unique_chunks.toLocaleString()} / {vol.chunks.toLocaleString()}</TableCell>
                      <TableCell>
                        <Badge variant={vol.status === 'active' ? 'default' : 'secondary'}>{vol.status}</Badge>
                      </TableCell>
                      <TableCell>{vol.throughput_mbps} Mbps</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="policies">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader><CardTitle>Deduplication Policy</CardTitle></CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between"><span>Chunk Size</span><Badge variant="outline">64 KB</Badge></div>
                <div className="flex items-center justify-between"><span>Hash Algorithm</span><Badge variant="outline">SHA-256 (blake3 optional)</Badge></div>
                <div className="flex items-center justify-between"><span>Min Dedup Ratio</span><Badge variant="outline">1.5x (below = bypass)</Badge></div>
                <div className="flex items-center justify-between"><span>Cache Size</span><Badge variant="outline">2 GB</Badge></div>
                <div className="flex items-center justify-between"><span>Exclude Patterns</span><Badge variant="outline">*.mp4, *.zip, *.enc</Badge></div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle>Compression Policy</CardTitle></CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between"><span>Default Algorithm</span><Badge variant="outline">ZSTD (level 3)</Badge></div>
                <div className="flex items-center justify-between"><span>Fast Algorithm</span><Badge variant="outline">LZ4</Badge></div>
                <div className="flex items-center justify-between"><span>Min Compress Ratio</span><Badge variant="outline">1.2x</Badge></div>
                <div className="flex items-center justify-between"><span>Compression Workers</span><Badge variant="outline">4 per CPU core</Badge></div>
                <div className="flex items-center justify-between"><span>Inline Mode</span><Badge variant="outline">Write-through</Badge></div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="stats">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card><CardHeader><CardTitle className="text-sm">Efficiency Over Time</CardTitle></CardHeader><CardContent><p className="text-xs text-muted-foreground">Chart: dedup ratio + compression ratio last 30d</p></CardContent></Card>
            <Card><CardHeader><CardTitle className="text-sm">Algorithm Comparison</CardTitle></CardHeader><CardContent><p className="text-xs text-muted-foreground">Chart: zstd vs lz4 ratio/throughput</p></CardContent></Card>
            <Card><CardHeader><CardTitle className="text-sm">Top Savings by Volume</CardTitle></CardHeader><CardContent><p className="text-xs text-muted-foreground">Chart: bar chart top 5 volumes</p></CardContent></Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default DedupCompression;
