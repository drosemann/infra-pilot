import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
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
import { Search, Database, Tag, GitBranch, Clock, Link, FileSearch, BookOpen } from 'lucide-react';

interface DataAsset {
  asset_id: string;
  name: string;
  type: string;
  location: string;
  schema: string;
  size_mb: number;
  record_count: number;
  owner: string;
  last_updated: string;
  quality_score: number;
  tags: string[];
  lineage: string[];
}

const mockAssets: DataAsset[] = [
  { asset_id: 'ds-001', name: 'user_profiles', type: 'postgresql', location: 'pg-01.internal:5432/infrapilot', schema: 'public.user_profiles (id, name, email, created_at)', size_mb: 256, record_count: 150000, owner: 'data-team', last_updated: '2024-05-29T06:00:00Z', quality_score: 98, tags: ['pii', 'user-data', 'production'], lineage: ['api-gateway', 'user-service', 'analytics-pipeline'] },
  { asset_id: 'ds-002', name: 'game_telemetry', type: 'timescaledb', location: 'ts-01.internal:5432/telemetry', schema: 'telemetry.sessions (session_id, player_id, event, ts)', size_mb: 5120, record_count: 45000000, owner: 'gaming-team', last_updated: '2024-05-29T05:55:00Z', quality_score: 95, tags: ['telemetry', 'gaming', 'real-time'], lineage: ['game-servers', 'event-bus', 'analytics'] },
  { asset_id: 'ds-003', name: 'financial_transactions', type: 'postgresql', location: 'pg-02.internal:5432/finance', schema: 'finance.transactions (tx_id, amount, currency, status)', size_mb: 1024, record_count: 8000000, owner: 'finance-team', last_updated: '2024-05-29T06:00:00Z', quality_score: 100, tags: ['finance', 'pci', 'audit'], lineage: ['payment-gateway', 'billing-service', 'ledger'] },
  { asset_id: 'ds-004', name: 'inventory_snapshots', type: 'parquet', location: 's3://data-lake/inventory/', schema: 'inventory_snapshot (sku, warehouse_id, quantity, date)', size_mb: 8192, record_count: 120000000, owner: 'logistics-team', last_updated: '2024-05-29T04:00:00Z', quality_score: 87, tags: ['inventory', 'data-lake', 'parquet'], lineage: ['erp-export', 'etl-pipeline', 'data-lake'] },
  { asset_id: 'ds-005', name: 'support_tickets', type: 'mongodb', location: 'mongo-01.internal:27017/support', schema: 'support.tickets (ticket_id, user_id, status, priority)', size_mb: 512, record_count: 250000, owner: 'support-team', last_updated: '2024-05-29T02:00:00Z', quality_score: 76, tags: ['support', 'customer-data'], lineage: ['zendesk-import', 'support-portal'] },
];

const DataCatalog: React.FC = () => {
  const [assets, setAssets] = useState<DataAsset[]>(mockAssets);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedAsset, setSelectedAsset] = useState<DataAsset | null>(null);

  const filteredAssets = assets.filter(a =>
    a.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    a.tags.some(t => t.includes(searchQuery.toLowerCase()))
  );

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Data Catalog</h1>
          <p className="text-muted-foreground">Automated discovery, schema detection, and lineage tracking across all data sources</p>
        </div>
        <Button variant="outline"><Search className="mr-2 h-4 w-4" />Run Discovery</Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Total Assets</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{assets.length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Total Records</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{assets.reduce((s, a) => s + a.record_count, 0).toLocaleString()}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Data Volume</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{(assets.reduce((s, a) => s + a.size_mb, 0) / 1024).toFixed(1)} GB</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Avg Quality</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{(assets.reduce((s, a) => s + a.quality_score, 0) / assets.length).toFixed(0)}%</div></CardContent></Card>
      </div>

      <div className="flex gap-2">
        <Input
          placeholder="Search assets, tags..."
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
          className="max-w-sm"
        />
        <Badge variant="secondary" className="flex items-center gap-1"><Database className="h-3 w-3" />PostgreSQL</Badge>
        <Badge variant="secondary" className="flex items-center gap-1"><Database className="h-3 w-3" />MongoDB</Badge>
        <Badge variant="secondary" className="flex items-center gap-1"><Database className="h-3 w-3" />Parquet</Badge>
        <Badge variant="secondary" className="flex items-center gap-1"><Database className="h-3 w-3" />TimescaleDB</Badge>
      </div>

      <Card>
        <CardHeader><CardTitle>Data Assets</CardTitle></CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Location</TableHead>
                <TableHead>Size</TableHead>
                <TableHead>Records</TableHead>
                <TableHead>Quality</TableHead>
                <TableHead>Last Updated</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredAssets.map(asset => (
                <TableRow key={asset.asset_id} className="cursor-pointer" onClick={() => setSelectedAsset(asset)}>
                  <TableCell className="font-medium">
                    <div className="flex items-center gap-2">
                      <Database className="h-4 w-4 text-muted-foreground" />
                      {asset.name}
                    </div>
                  </TableCell>
                  <TableCell><Badge variant="outline" className="text-xs">{asset.type}</Badge></TableCell>
                  <TableCell className="text-xs text-muted-foreground">{asset.location}</TableCell>
                  <TableCell>{asset.size_mb >= 1024 ? `${(asset.size_mb/1024).toFixed(1)} GB` : `${asset.size_mb} MB`}</TableCell>
                  <TableCell>{asset.record_count >= 1000000 ? `${(asset.record_count/1000000).toFixed(1)}M` : asset.record_count >= 1000 ? `${(asset.record_count/1000).toFixed(0)}K` : asset.record_count}</TableCell>
                  <TableCell>
                    <Badge variant={asset.quality_score >= 90 ? 'default' : asset.quality_score >= 70 ? 'secondary' : 'destructive'}>
                      {asset.quality_score}%
                    </Badge>
                  </TableCell>
                  <TableCell className="text-xs">{new Date(asset.last_updated).toLocaleString()}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Dialog open={!!selectedAsset} onOpenChange={() => setSelectedAsset(null)}>
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader><DialogTitle>{selectedAsset?.name}</DialogTitle></DialogHeader>
          {selectedAsset && (
            <div className="space-y-4">
              <div className="flex gap-2 flex-wrap">{selectedAsset.tags.map(t => <Badge key={t} variant="secondary" className="text-xs">{t}</Badge>)}</div>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div><strong>Type:</strong> {selectedAsset.type}</div>
                <div><strong>Location:</strong> {selectedAsset.location}</div>
                <div><strong>Owner:</strong> {selectedAsset.owner}</div>
                <div><strong>Records:</strong> {selectedAsset.record_count.toLocaleString()}</div>
                <div><strong>Size:</strong> {(selectedAsset.size_mb / 1024).toFixed(2)} GB</div>
                <div><strong>Quality Score:</strong> {selectedAsset.quality_score}%</div>
              </div>
              <div>
                <h4 className="font-medium text-sm mb-2">Schema</h4>
                <pre className="p-3 rounded-lg bg-muted text-xs overflow-x-auto">{selectedAsset.schema}</pre>
              </div>
              <div>
                <h4 className="font-medium text-sm mb-2">Lineage</h4>
                <div className="flex items-center gap-2 flex-wrap">
                  {selectedAsset.lineage.map((l, i) => (
                    <React.Fragment key={l}>
                      <Badge variant="outline" className="text-xs">{l}</Badge>
                      {i < selectedAsset.lineage.length - 1 && <Link className="h-3 w-3 text-muted-foreground" />}
                    </React.Fragment>
                  ))}
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default DataCatalog;
