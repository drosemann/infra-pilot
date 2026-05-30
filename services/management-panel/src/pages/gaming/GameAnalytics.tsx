import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
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
import { TrendingUp, Users, Clock, DollarSign, Activity, Calendar, BarChart3, ArrowUp, ArrowDown, Zap, Globe, Gamepad2 } from 'lucide-react';

interface AnalyticsMetric {
  label: string;
  value: string;
  change: number;
  trend: string;
}

interface GameStats {
  game: string;
  active_players: number;
  total_players: number;
  avg_session_min: number;
  revenue_today: number;
  revenue_month: number;
  peak_today: number;
  servers_online: number;
}

const mockMetrics: AnalyticsMetric[] = [
  { label: 'Active Players', value: '1,247', change: 12.5, trend: 'up' },
  { label: 'New Players (24h)', value: '342', change: 8.3, trend: 'up' },
  { label: 'Avg Session', value: '47m', change: 3.2, trend: 'up' },
  { label: 'Revenue Today', value: '$847.50', change: 15.7, trend: 'up' },
  { label: 'Total Players', value: '45,231', change: 5.1, trend: 'up' },
  { label: 'Peak Concurrent', value: '2,891', change: -2.4, trend: 'down' },
];

const mockGameStats: GameStats[] = [
  { game: 'minecraft', active_players: 847, total_players: 32150, avg_session_min: 52, revenue_today: 523.00, revenue_month: 15230.00, peak_today: 1240, servers_online: 8 },
  { game: 'terraria', active_players: 182, total_players: 5670, avg_session_min: 68, revenue_today: 98.50, revenue_month: 2890.00, peak_today: 320, servers_online: 3 },
  { game: 'valheim', active_players: 124, total_players: 4210, avg_session_min: 85, revenue_today: 76.00, revenue_month: 2340.00, peak_today: 210, servers_online: 2 },
  { game: '7d2d', active_players: 94, total_players: 3201, avg_session_min: 92, revenue_today: 150.00, revenue_month: 4560.00, peak_today: 180, servers_online: 2 },
];

const GameAnalytics: React.FC = () => {
  const [metrics] = useState<AnalyticsMetric[]>(mockMetrics);
  const [gameStats] = useState<GameStats[]>(mockGameStats);

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Game Analytics</h1>
          <p className="text-muted-foreground">Active players, session duration, revenue, and engagement heatmaps</p>
        </div>
        <Badge variant="secondary" className="text-sm"><Activity className="mr-1 h-4 w-4" />Live</Badge>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {metrics.map(m => (
          <Card key={m.label}>
            <CardHeader className="pb-1"><CardTitle className="text-xs font-medium text-muted-foreground">{m.label}</CardTitle></CardHeader>
            <CardContent>
              <div className="text-xl font-bold">{m.value}</div>
              <div className={`flex items-center text-xs ${m.trend === 'up' ? 'text-green-500' : 'text-red-500'}`}>
                {m.trend === 'up' ? <ArrowUp className="h-3 w-3 mr-1" /> : <ArrowDown className="h-3 w-3 mr-1" />}
                {m.change}%
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="games">Per Game</TabsTrigger>
          <TabsTrigger value="heatmap">Activity Heatmap</TabsTrigger>
          <TabsTrigger value="revenue">Revenue</TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card><CardHeader><CardTitle className="text-sm">Player Activity (24h)</CardTitle></CardHeader><CardContent><p className="text-xs text-muted-foreground">Chart: line chart of active player count over last 24 hours</p></CardContent></Card>
            <Card><CardHeader><CardTitle className="text-sm">Server Status</CardTitle></CardHeader><CardContent><p className="text-xs text-muted-foreground">Chart: donut chart of online/offline servers</p></CardContent></Card>
          </div>
        </TabsContent>

        <TabsContent value="games">
          <Card>
            <CardHeader><CardTitle>Per-Game Statistics</CardTitle></CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Game</TableHead>
                    <TableHead>Active</TableHead>
                    <TableHead>Total Players</TableHead>
                    <TableHead>Avg Session</TableHead>
                    <TableHead>Peak Today</TableHead>
                    <TableHead>Revenue Today</TableHead>
                    <TableHead>Revenue/Month</TableHead>
                    <TableHead>Servers</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {gameStats.map(gs => (
                    <TableRow key={gs.game}>
                      <TableCell className="font-medium">
                        <div className="flex items-center gap-2">
                          <Gamepad2 className="h-4 w-4" />
                          {gs.game}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <div className="h-2 w-2 rounded-full bg-green-500" />
                          {gs.active_players}
                        </div>
                      </TableCell>
                      <TableCell>{gs.total_players.toLocaleString()}</TableCell>
                      <TableCell>{gs.avg_session_min}m</TableCell>
                      <TableCell className="font-bold">{gs.peak_today}</TableCell>
                      <TableCell>${gs.revenue_today.toFixed(2)}</TableCell>
                      <TableCell>${gs.revenue_month.toFixed(2)}</TableCell>
                      <TableCell>{gs.servers_online}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="heatmap">
          <Card>
            <CardHeader><CardTitle>Player Activity Heatmap</CardTitle></CardHeader>
            <CardContent>
              <div className="grid grid-cols-7 gap-1">
                {Array.from({ length: 7 * 24 }, (_, i) => {
                  const hour = i % 24;
                  const base = 50 + Math.sin(hour / 24 * Math.PI * 2) * 40 + Math.random() * 20;
                  const intensity = Math.min(100, Math.max(5, base));
                  return (
                    <div
                      key={i}
                      className="aspect-square rounded"
                      style={{ backgroundColor: `hsl(${120 - intensity}, 70%, ${50 - intensity * 0.3}%)` }}
                      title={`Day ${Math.floor(i / 24) + 1}, Hour ${hour}: ${intensity.toFixed(0)} players`}
                    />
                  );
                })}
              </div>
              <div className="flex justify-between mt-2 text-xs text-muted-foreground">
                <span>Mon</span><span>Tue</span><span>Wed</span><span>Thu</span><span>Fri</span><span>Sat</span><span>Sun</span>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="revenue">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <Card><CardHeader><CardTitle className="text-sm">Revenue (30d)</CardTitle></CardHeader><CardContent><div className="text-3xl font-bold">$25,020</div><p className="text-xs text-green-500 mt-1">↑ 12.3% from last month</p></CardContent></Card>
            <Card><CardHeader><CardTitle className="text-sm">Avg Revenue/Player</CardTitle></CardHeader><CardContent><div className="text-3xl font-bold">$0.55</div></CardContent></Card>
            <Card><CardHeader><CardTitle className="text-sm">Top Revenue Source</CardTitle></CardHeader><CardContent><div className="text-3xl font-bold">Server Rentals</div><p className="text-xs text-muted-foreground">62% of total revenue</p></CardContent></Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default GameAnalytics;
