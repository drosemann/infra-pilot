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
import { Trophy, Users, Swords, Calendar, CircleDot, ChevronRight, CheckCircle, Timer, Medal, Star, Play, Pause } from 'lucide-react';

interface Tournament {
  id: string;
  name: string;
  game: string;
  format: string;
  team_size: number;
  max_teams: number;
  registered_teams: number;
  status: string;
  start_date: string;
  prize_pool: string;
  region: string;
  current_round: number;
  total_rounds: number;
}

const mockTournaments: Tournament[] = [
  { id: 'trn-001', name: 'Summer Championship 2024', game: 'minecraft', format: 'double_elimination', team_size: 4, max_teams: 16, registered_teams: 14, status: 'in_progress', start_date: '2024-06-01T10:00:00Z', prize_pool: '$5,000', region: 'NA', current_round: 3, total_rounds: 7 },
  { id: 'trn-002', name: 'Weekly PvP Cup #42', game: 'minecraft', format: 'single_elimination', team_size: 2, max_teams: 32, registered_teams: 28, status: 'registration', start_date: '2024-06-05T14:00:00Z', prize_pool: '$500', region: 'EU', current_round: 0, total_rounds: 5 },
  { id: 'trn-003', name: 'Build Battle Masters', game: 'minecraft', format: 'swiss', team_size: 1, max_teams: 64, registered_teams: 45, status: 'registration', start_date: '2024-06-10T08:00:00Z', prize_pool: '$2,000', region: 'Global', current_round: 0, total_rounds: 7 },
  { id: 'trn-004', name: 'BedWars Pro League', game: 'minecraft', format: 'round_robin', team_size: 4, max_teams: 8, registered_teams: 8, status: 'completed', start_date: '2024-05-01T10:00:00Z', prize_pool: '$10,000', region: 'NA', current_round: 7, total_rounds: 7 },
  { id: 'trn-005', name: 'UHC Championship', game: 'minecraft', format: 'single_elimination', team_size: 3, max_teams: 24, registered_teams: 21, status: 'in_progress', start_date: '2024-05-25T12:00:00Z', prize_pool: '$3,000', region: 'EU', current_round: 4, total_rounds: 5 },
];

const TournamentManager: React.FC = () => {
  const [tournaments, setTournaments] = useState<Tournament[]>(mockTournaments);
  const [selectedTournament, setSelectedTournament] = useState<Tournament | null>(null);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [newT, setNewT] = useState({ name: '', game: 'minecraft', format: 'single_elimination', team_size: 4, max_teams: 16, prize_pool: '', region: 'NA' });

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Tournament Manager</h1>
          <p className="text-muted-foreground">Single/double elimination, Swiss, and round-robin brackets with prize management</p>
        </div>
        <Button onClick={() => setIsCreateOpen(true)}><Trophy className="mr-2 h-4 w-4" />Create Tournament</Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Active</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{tournaments.filter(t => t.status === 'in_progress').length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Upcoming</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{tournaments.filter(t => t.status === 'registration').length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Completed</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{tournaments.filter(t => t.status === 'completed').length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Total Prize Pool</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-green-500">$20,500</div></CardContent></Card>
      </div>

      <Tabs defaultValue="active">
        <TabsList>
          <TabsTrigger value="active">Active / Upcoming</TabsTrigger>
          <TabsTrigger value="completed">Completed</TabsTrigger>
        </TabsList>

        <TabsContent value="active">
          <Card>
            <CardHeader><CardTitle>Tournaments</CardTitle></CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Format</TableHead>
                    <TableHead>Teams</TableHead>
                    <TableHead>Round</TableHead>
                    <TableHead>Prize Pool</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {tournaments.filter(t => t.status !== 'completed').map(t => (
                    <TableRow key={t.id}>
                      <TableCell className="font-medium">
                        <div className="flex items-center gap-2"><Trophy className="h-4 w-4 text-yellow-500" />{t.name}</div>
                      </TableCell>
                      <TableCell><Badge variant="outline">{t.format.replace('_', ' ')}</Badge></TableCell>
                      <TableCell>{t.registered_teams}/{t.max_teams}</TableCell>
                      <TableCell>{t.status === 'registration' ? '-' : `${t.current_round}/${t.total_rounds}`}</TableCell>
                      <TableCell className="font-medium">{t.prize_pool}</TableCell>
                      <TableCell>
                        <Badge variant={t.status === 'in_progress' ? 'default' : 'secondary'}>{t.status.replace('_', ' ')}</Badge>
                      </TableCell>
                      <TableCell>
                        <Button size="sm" variant="outline" onClick={() => setSelectedTournament(t)}>View</Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="completed">
          <Card>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow><TableHead>Name</TableHead><TableHead>Winner</TableHead><TableHead>Prize Pool</TableHead><TableHead>Completed</TableHead></TableRow>
                </TableHeader>
                <TableBody>
                  {tournaments.filter(t => t.status === 'completed').map(t => (
                    <TableRow key={t.id}>
                      <TableCell className="font-medium">{t.name}</TableCell>
                      <TableCell><Badge variant="default">Team Alpha</Badge></TableCell>
                      <TableCell>{t.prize_pool}</TableCell>
                      <TableCell className="text-xs">May 28, 2024</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>Create Tournament</DialogTitle></DialogHeader>
          <div className="space-y-4">
            <div><Label>Name</Label><Input value={newT.name} onChange={e => setNewT({ ...newT, name: e.target.value })} placeholder="Tournament Name" /></div>
            <div><Label>Game</Label><select className="w-full p-2 rounded-md border" value={newT.game} onChange={e => setNewT({ ...newT, game: e.target.value })}><option value="minecraft">Minecraft</option></select></div>
            <div><Label>Format</Label><select className="w-full p-2 rounded-md border" value={newT.format} onChange={e => setNewT({ ...newT, format: e.target.value })}><option value="single_elimination">Single Elimination</option><option value="double_elimination">Double Elimination</option><option value="swiss">Swiss</option><option value="round_robin">Round Robin</option></select></div>
            <div className="grid grid-cols-2 gap-2"><div><Label>Team Size</Label><Input type="number" value={newT.team_size} onChange={e => setNewT({ ...newT, team_size: parseInt(e.target.value) || 1 })} /></div><div><Label>Max Teams</Label><Input type="number" value={newT.max_teams} onChange={e => setNewT({ ...newT, max_teams: parseInt(e.target.value) || 16 })} /></div></div>
            <div className="grid grid-cols-2 gap-2"><div><Label>Prize Pool</Label><Input value={newT.prize_pool} onChange={e => setNewT({ ...newT, prize_pool: e.target.value })} placeholder="$1,000" /></div><div><Label>Region</Label><select className="w-full p-2 rounded-md border" value={newT.region} onChange={e => setNewT({ ...newT, region: e.target.value })}><option value="NA">NA</option><option value="EU">EU</option><option value="Global">Global</option></select></div></div>
            <Button className="w-full" onClick={() => { setTournaments([...tournaments, { id: `trn-${Date.now()}`, ...newT, registered_teams: 0, status: 'registration', start_date: new Date().toISOString(), current_round: 0, total_rounds: 5 }]); setIsCreateOpen(false); }}>Create</Button>
          </div>
        </DialogContent>
      </Dialog>

      <Dialog open={!!selectedTournament} onOpenChange={() => setSelectedTournament(null)}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader><DialogTitle>{selectedTournament?.name} - Bracket</DialogTitle></DialogHeader>
          {selectedTournament && (
            <div className="space-y-4">
              <div className="p-4 rounded-lg bg-muted text-center">
                <Trophy className="h-10 w-10 text-yellow-500 mx-auto mb-2" />
                <div className="font-bold text-lg">{selectedTournament.prize_pool}</div>
                <div className="text-sm text-muted-foreground">Prize Pool</div>
              </div>
              <div className="grid grid-cols-2 gap-2 text-sm"><div><strong>Format:</strong> {selectedTournament.format.replace('_', ' ')}</div><div><strong>Region:</strong> {selectedTournament.region}</div><div><strong>Teams:</strong> {selectedTournament.registered_teams}/{selectedTournament.max_teams}</div><div><strong>Round:</strong> {selectedTournament.current_round}/{selectedTournament.total_rounds}</div></div>
              <Separator />
              <h4 className="font-medium text-sm">Current Round Matches</h4>
              <div className="space-y-2">
                <div className="p-2 rounded border flex justify-between items-center"><span>Team Dragon ⚔️ Team Phoenix</span><Badge variant="outline">Live</Badge></div>
                <div className="p-2 rounded border flex justify-between items-center"><span>Team Wolf ⚔️ Team Eagle</span><Badge>Upcoming</Badge></div>
                <div className="p-2 rounded border flex justify-between items-center"><span>Team Bear ⚔️ Team Shark</span><Badge variant="secondary">Scheduled</Badge></div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default TournamentManager;
