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
import { Server, ShoppingCart, Clock, DollarSign, Users, Star, Zap, Calendar, Tag, Globe } from 'lucide-react';

interface RentalListing {
  listing_id: string;
  name: string;
  game: string;
  player_slots: number;
  price_hourly: number;
  price_daily: number;
  region: string;
  ram_gb: number;
  cpu_cores: number;
  storage_gb: number;
  status: string;
  owner: string;
  rating: number;
  total_rentals: number;
  available: boolean;
}

const mockListings: RentalListing[] = [
  { listing_id: 'rent-001', name: 'Premium PvP Server', game: 'minecraft', player_slots: 50, price_hourly: 0.99, price_daily: 14.99, region: 'NA-East', ram_gb: 8, cpu_cores: 4, storage_gb: 50, status: 'active', owner: 'NetworkOps', rating: 4.8, total_rentals: 234, available: true },
  { listing_id: 'rent-002', name: 'Survival World Hosting', game: 'minecraft', player_slots: 20, price_hourly: 0.49, price_daily: 7.99, region: 'EU-West', ram_gb: 4, cpu_cores: 2, storage_gb: 20, status: 'active', owner: 'GameHost Inc', rating: 4.5, total_rentals: 456, available: true },
  { listing_id: 'rent-003', name: 'Competitive Arena', game: 'minecraft', player_slots: 100, price_hourly: 1.99, price_daily: 29.99, region: 'NA-West', ram_gb: 16, cpu_cores: 8, storage_gb: 100, status: 'active', owner: 'ProGaming LLC', rating: 4.9, total_rentals: 89, available: true },
  { listing_id: 'rent-004', name: 'Modded Server (200+ mods)', game: 'minecraft', player_slots: 30, price_hourly: 1.49, price_daily: 19.99, region: 'EU-West', ram_gb: 12, cpu_cores: 6, storage_gb: 80, status: 'active', owner: 'ModHost Pro', rating: 4.6, total_rentals: 167, available: true },
  { listing_id: 'rent-005', name: 'Minigame Party Server', game: 'minecraft', player_slots: 40, price_hourly: 0.79, price_daily: 11.99, region: 'Asia-East', ram_gb: 6, cpu_cores: 3, storage_gb: 30, status: 'maintenance', owner: 'NetworkOps', rating: 4.3, total_rentals: 78, available: false },
];

const ServerRentalMarketplace: React.FC = () => {
  const [listings, setListings] = useState<RentalListing[]>(mockListings);
  const [selectedListing, setSelectedListing] = useState<RentalListing | null>(null);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('browse');

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Server Rental Marketplace</h1>
          <p className="text-muted-foreground">Hourly/daily rental marketplace with pricing tiers and availability</p>
        </div>
        <Button onClick={() => setIsCreateOpen(true)}><ShoppingCart className="mr-2 h-4 w-4" />List Server</Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Available</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold text-green-500">{listings.filter(l => l.available).length}</div></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Total Rentals</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">{listings.reduce((s, l) => s + l.total_rentals, 0)}</div></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Avg Rating</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">{(listings.reduce((s, l) => s + l.rating, 0) / listings.length).toFixed(1)}</div></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Price Range</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">$0.49 - $1.99/h</div></CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="browse">Browse</TabsTrigger>
          <TabsTrigger value="my-rentals">My Rentals</TabsTrigger>
          <TabsTrigger value="listings">My Listings</TabsTrigger>
        </TabsList>

        <TabsContent value="browse">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {listings.filter(l => l.available).map(listing => (
              <Card key={listing.listing_id} className="cursor-pointer hover:border-primary transition-colors" onClick={() => setSelectedListing(listing)}>
                <CardHeader className="pb-2">
                  <div className="flex justify-between items-start">
                    <CardTitle className="text-base">{listing.name}</CardTitle>
                    <Badge variant="outline">${listing.price_hourly}/h</Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Server className="h-4 w-4" />{listing.game} · {listing.player_slots} slots
                  </div>
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Globe className="h-4 w-4" />{listing.region} · {listing.ram_gb}GB RAM
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1"><Star className="h-4 w-4 text-yellow-500 fill-yellow-500" /><span className="text-sm font-medium">{listing.rating}</span></div>
                    <div className="flex items-center gap-1"><Users className="h-4 w-4 text-muted-foreground" /><span className="text-sm text-muted-foreground">{listing.total_rentals} rentals</span></div>
                  </div>
                  <div className="flex gap-2">
                    <Badge variant="secondary" className="text-xs">{listing.cpu_cores} CPU</Badge>
                    <Badge variant="secondary" className="text-xs">{listing.storage_gb}GB SSD</Badge>
                  </div>
                  <Button className="w-full" size="sm"><ShoppingCart className="mr-2 h-4 w-4" />Rent Now</Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="my-rentals">
          <Card>
            <CardContent className="py-8 text-center text-muted-foreground">
              <Server className="h-12 w-12 mx-auto mb-4" />
              <p>You have no active rentals</p>
              <Button className="mt-4" variant="outline" onClick={() => setActiveTab('browse')}>Browse Servers</Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="listings">
          <Card>
            <CardContent className="py-4">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Price</TableHead>
                    <TableHead>Region</TableHead>
                    <TableHead>Rentals</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {listings.filter(l => l.owner === 'NetworkOps').map(l => (
                    <TableRow key={l.listing_id}>
                      <TableCell className="font-medium">{l.name}</TableCell>
                      <TableCell>${l.price_hourly}/h · ${l.price_daily}/d</TableCell>
                      <TableCell>{l.region}</TableCell>
                      <TableCell>{l.total_rentals}</TableCell>
                      <TableCell><Badge variant={l.status === 'active' ? 'default' : 'secondary'}>{l.status}</Badge></TableCell>
                      <TableCell><Button size="sm" variant="outline">Manage</Button></TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <Dialog open={!!selectedListing} onOpenChange={() => setSelectedListing(null)}>
        <DialogContent className="sm:max-w-[450px]">
          <DialogHeader><DialogTitle>{selectedListing?.name}</DialogTitle></DialogHeader>
          {selectedListing && (
            <div className="space-y-4">
              <div className="flex gap-2">
                <Badge>{selectedListing.game}</Badge>
                <Badge variant="outline">{selectedListing.region}</Badge>
                <Badge variant={selectedListing.available ? 'default' : 'secondary'}>{selectedListing.available ? 'Available' : 'Unavailable'}</Badge>
              </div>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div><strong>CPU:</strong> {selectedListing.cpu_cores} cores</div>
                <div><strong>RAM:</strong> {selectedListing.ram_gb} GB</div>
                <div><strong>Storage:</strong> {selectedListing.storage_gb} GB SSD</div>
                <div><strong>Slots:</strong> {selectedListing.player_slots}</div>
              </div>
              <div className="p-4 rounded-lg bg-muted">
                <div className="flex justify-between items-center">
                  <span className="text-2xl font-bold">${selectedListing.price_hourly}/<span className="text-sm font-normal">hour</span></span>
                  <span className="text-lg">${selectedListing.price_daily}/<span className="text-sm font-normal">day</span></span>
                </div>
              </div>
              <div className="flex gap-2">
                <Button className="flex-1"><ShoppingCart className="mr-2 h-4 w-4" />Rent Hourly</Button>
                <Button variant="outline" className="flex-1">Rent Daily</Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>List Your Server</DialogTitle></DialogHeader>
          <div className="space-y-4">
            <div><Label>Server Name</Label><Input placeholder="My Awesome Server" /></div>
            <div className="grid grid-cols-2 gap-2">
              <div><Label>Hourly Price</Label><Input type="number" placeholder="0.99" /></div>
              <div><Label>Daily Price</Label><Input type="number" placeholder="14.99" /></div>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div><Label>CPU Cores</Label><Input type="number" defaultValue={4} /></div>
              <div><Label>RAM (GB)</Label><Input type="number" defaultValue={8} /></div>
            </div>
            <Button className="w-full">List Server</Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ServerRentalMarketplace;
