import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
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
} from '@/components/ui/dialog';
import { Swords, Users, Clock, Zap, TrendingUp, BarChart3, Search, Filter, Medal, Star, Activity } from 'lucide-react';

interface QueueState {
  queue_id: string;
  game: string;
  mode: string;
  region: string;
  players_waiting: number;
  avg_wait_time: number;
  min_elo: number;
  max_elo: number;
  party_size: number;
  status: string;
  matches_formed: number;
}

interface PlayerRanking {
  player_id: string;
  name: string;
  elo: number;
  mmr: number;
  wins: number;
  losses: number;
  win_rate: number;
  rank: string;
  tier: string;
  region: string;
  games_played: number;
}

const mockQueues: QueueState[] = [
  { queue_id: 'q-solo-arena', game: 'minecraft', mode: 'solo_arena', region: 'NA', players_waiting: 23, avg_wait_time: 45, min_elo: 0, max_elo: 3000, party_size: 1, status: 'active', matches_formed: 1240 },
  { queue_id: 'q-duo-pvp', game: 'minecraft', mode: 'duo_pvp', region: 'NA', players_waiting: 12, avg_wait_time: 62, min_elo: 500, max_elo: 2500, party_size: 2, status: 'active', matches_formed: 876 },
  { queue_id: 'q-squad-bw', game: 'minecraft', mode: 'squad_bedwars', region: 'EU', players_waiting: 8, avg_wait_time: 89, min_elo: 800, max_elo: 2200, party_size: 4, status: 'active', matches_formed: 543 },
  { queue_id: 'q-ranked-uhc', game: 'minecraft', mode: 'ranked_uhc', region: 'EU', players_waiting: 4, avg_wait_time: 120, min_elo: 1200, max_elo: 2800, party_size: 1, status: 'active', matches_formed: 234 },
  { queue_id: 'q-casual-ffa', game: 'minecraft', mode: 'free_for_all', region: 'Global', players_waiting: 45, avg_wait_time: 15, min_elo: 0, max_elo: 9999, party_size: 1, status: 'active', matches_formed: 3421 },
];

const mockLeaderboard: PlayerRanking[] = [
  { player_id: 'p-001', name: 'NinjaPro', elo: 2850, mmr: 1750, wins: 342, losses: 98, win_rate: 77.7, rank: '#1', tier: 'Diamond', region: 'NA', games_played: 440 },
  { player_id: 'p-002', name: 'BuildMaster', elo: 2720, mmr: 1680, wins: 289, losses: 112, win_rate: 72.1, rank: '#2', tier: 'Diamond', region: 'EU', games_played: 401 },
  { player_id: 'p-003', name: 'PvP_King', elo: 2650, mmr: 1620, wins: 456, losses: 210, win_rate: 68.5, rank: '#3', tier: 'Platinum', region: 'NA', games_played: 666 },
  { player_id: 'p-004', name: 'Tactical_Joe', elo: 2510, mmr: 1550, wins: 198, losses: 87, win_rate: 69.5, rank: '#4', tier: 'Platinum', region: 'EU', games_played: 285 },
  { player_id: 'p-005', name: 'SpeedRunner_X', elo: 2480, mmr: 1520, wins: 567, losses: 298, win_rate: 65.5, rank: '#5', tier: 'Gold', region: 'NA', games_played: 865 },
];

const MatchmakingService: React.FC = () => {
  const [queues, setQueues] = useState<QueueState[]>(mockQueues);
  const [leaderboard, setLeaderboard] = useState<PlayerRanking[]>(mockLeaderboard);

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Matchmaking Service</h1>
          <p className="text-muted-foreground">ELO/MMR queue management, skill-based balancing, party queuing, and regions</p>
        </div>
        <Badge variant="secondary" className="text-sm"><Activity className="mr-1 h-4 w-4" />{queues.reduce((s, q) => s + q.players_waiting, 0)} in queue</Badge>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Active Queues</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{queues.filter(q => q.status === 'active').length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Total Players</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{queues.reduce((s, q) => s + q.players_waiting, 0)}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Avg Wait Time</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{(queues.reduce((s, q) => s + q.avg_wait_time, 0) / queues.length).toFixed(0)}s</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Matches Today</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{queues.reduce((s, q) => s + q.matches_formed, 0)}</div></CardContent></Card>
      </div>

      <Tabs defaultValue="queues">
        <TabsList>
          <TabsTrigger value="queues">Active Queues</TabsTrigger>
          <TabsTrigger value="leaderboard">Leaderboard</TabsTrigger>
          <TabsTrigger value="config">Matchmaking Config</TabsTrigger>
        </TabsList>

        <TabsContent value="queues">
          <Card>
            <CardHeader><CardTitle>Queue Status</CardTitle></CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Queue</TableHead>
                    <TableHead>Mode</TableHead>
                    <TableHead>Region</TableHead>
                    <TableHead>Waiting</TableHead>
                    <TableHead>Avg Wait</TableHead>
                    <TableHead>ELO Range</TableHead>
                    <TableHead>Party</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {queues.map(q => (
                    <TableRow key={q.queue_id}>
                      <TableCell className="font-medium">{q.queue_id}</TableCell>
                      <TableCell><Badge variant="outline" className="text-xs">{q.mode.replace('_', ' ')}</Badge></TableCell>
                      <TableCell>{q.region}</TableCell>
                      <TableCell className="text-lg font-bold">{q.players_waiting}</TableCell>
                      <TableCell>{q.avg_wait_time}s</TableCell>
                      <TableCell className="text-xs">{q.min_elo} - {q.max_elo}</TableCell>
                      <TableCell>{q.party_size > 1 ? `${q.party_size}P` : 'Solo'}</TableCell>
                      <TableCell><Badge variant="default">active</Badge></TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="leaderboard">
          <Card>
            <CardHeader><CardTitle>Top Players</CardTitle></CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Rank</TableHead>
                    <TableHead>Player</TableHead>
                    <TableHead>ELO</TableHead>
                    <TableHead>MMR</TableHead>
                    <TableHead>W/L</TableHead>
                    <TableHead>Win Rate</TableHead>
                    <TableHead>Tier</TableHead>
                    <TableHead>Region</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {leaderboard.map(p => (
                    <TableRow key={p.player_id}>
                      <TableCell className="font-bold">{p.rank}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {p.rank === '#1' && <Trophy className="h-4 w-4 text-yellow-500" />}
                          {p.rank === '#2' && <Medal className="h-4 w-4 text-gray-400" />}
                          {p.rank === '#3' && <Medal className="h-4 w-4 text-amber-600" />}
                          {p.name}
                        </div>
                      </TableCell>
                      <TableCell className="font-bold">{p.elo}</TableCell>
                      <TableCell>{p.mmr}</TableCell>
                      <TableCell className="text-xs">{p.wins}W / {p.losses}L</TableCell>
                      <TableCell>
                        <Badge variant={p.win_rate >= 70 ? 'default' : p.win_rate >= 60 ? 'secondary' : 'outline'}>{p.win_rate.toFixed(1)}%</Badge>
                      </TableCell>
                      <TableCell><Badge variant="outline">{p.tier}</Badge></TableCell>
                      <TableCell>{p.region}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="config">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card><CardHeader><CardTitle className="text-sm">ELO Settings</CardTitle></CardHeader><CardContent className="space-y-2 text-sm"><div className="flex justify-between"><span>K-Factor</span><Badge>32</Badge></div><div className="flex justify-between"><span>Starting ELO</span><Badge>1000</Badge></div><div className="flex justify-between"><span>Placement Matches</span><Badge>10</Badge></div><div className="flex justify-between"><span>Decay Rate</span><Badge>5 ELO/week</Badge></div></CardContent></Card>
            <Card><CardHeader><CardTitle className="text-sm">Queue Settings</CardTitle></CardHeader><CardContent className="space-y-2 text-sm"><div className="flex justify-between"><span>Max Queue Time</span><Badge>300s</Badge></div><div className="flex justify-between"><span>ELO Spread</span><Badge>±200</Badge></div><div className="flex justify-between"><span>Party ELO Limit</span><Badge>±150</Badge></div><div className="flex justify-between"><span>Region Match</span><Badge variant="secondary">Preferred</Badge></div></CardContent></Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default MatchmakingService;
