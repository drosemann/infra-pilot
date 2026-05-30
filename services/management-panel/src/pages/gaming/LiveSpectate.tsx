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
import { Camera, Video, Play, Pause, Square, Monitor, Eye, Users, Radio, Clock, Activity, SwitchCamera, Layout } from 'lucide-react';

interface SpectateSession {
  session_id: string;
  server_id: string;
  server_name: string;
  game: string;
  spectator_count: number;
  max_spectators: number;
  stream_resolution: string;
  stream_fps: number;
  duration: string;
  status: string;
  current_scene: string;
  obs_connected: boolean;
  started_at: string;
  viewer_peak: number;
}

const mockSessions: SpectateSession[] = [
  { session_id: 'spec-001', server_id: 'mc-pvp-01', server_name: 'PvP Arena #1', game: 'minecraft', spectator_count: 12, max_spectators: 50, stream_resolution: '1920x1080', stream_fps: 60, duration: '1h 23m', status: 'live', current_scene: 'Arena Overview', obs_connected: true, started_at: '2024-05-29T08:00:00Z', viewer_peak: 34 },
  { session_id: 'spec-002', server_id: 'mc-events-01', server_name: 'Event Server', game: 'minecraft', spectator_count: 45, max_spectators: 100, stream_resolution: '1920x1080', stream_fps: 30, duration: '2h 45m', status: 'live', current_scene: 'Main Stage', obs_connected: true, started_at: '2024-05-29T06:30:00Z', viewer_peak: 89 },
  { session_id: 'spec-003', server_id: 'mc-survival-01', server_name: 'Survival World', game: 'minecraft', spectator_count: 3, max_spectators: 20, stream_resolution: '1280x720', stream_fps: 30, duration: '0h 45m', status: 'live', current_scene: 'Player Follow', obs_connected: true, started_at: '2024-05-29T09:30:00Z', viewer_peak: 8 },
  { session_id: 'spec-004', server_id: 'mc-pvp-02', server_name: 'PvP Arena #2', game: 'minecraft', spectator_count: 0, max_spectators: 50, stream_resolution: '1920x1080', stream_fps: 60, duration: '0h 0m', status: 'idle', current_scene: 'Lobby', obs_connected: false, started_at: '-', viewer_peak: 0 },
];

const LiveSpectate: React.FC = () => {
  const [sessions, setSessions] = useState<SpectateSession[]>(mockSessions);
  const [selectedSession, setSelectedSession] = useState<SpectateSession | null>(null);

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Live Spectate</h1>
          <p className="text-muted-foreground">OBS WebSocket integration with scene switching and spectator slot management</p>
        </div>
        <Badge variant="secondary" className="text-sm">
          <Radio className="mr-1 h-4 w-4" />{sessions.filter(s => s.status === 'live').length} Live
        </Badge>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Live Streams</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{sessions.filter(s => s.status === 'live').length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Total Viewers</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{sessions.reduce((s, ss) => s + ss.spectator_count, 0)}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Peak Viewers</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{sessions.reduce((s, ss) => Math.max(s, ss.viewer_peak), 0)}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">OBS Connected</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-green-500">{sessions.filter(s => s.obs_connected).length}</div></CardContent></Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {sessions.filter(s => s.status === 'live').map(session => (
          <Card key={session.session_id} className="overflow-hidden">
            <div className="aspect-video bg-muted flex items-center justify-center relative">
              <div className="absolute top-2 left-2 flex items-center gap-2">
                <Badge variant="destructive" className="animate-pulse"><div className="h-2 w-2 rounded-full bg-white mr-1" />LIVE</Badge>
                <Badge variant="secondary"><Eye className="h-3 w-3 mr-1" />{session.spectator_count}</Badge>
              </div>
              <div className="text-center"><Camera className="h-12 w-12 mx-auto text-muted-foreground" /><p className="text-muted-foreground text-sm mt-2">Live Stream Preview</p></div>
            </div>
            <CardContent className="p-4">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-bold">{session.server_name}</h3>
                  <p className="text-xs text-muted-foreground">{session.game} · {session.stream_resolution} @ {session.stream_fps}fps</p>
                </div>
                <Button size="sm" variant="outline"><Eye className="h-4 w-4 mr-1" />Spectate</Button>
              </div>
              <div className="mt-3 flex justify-between text-xs text-muted-foreground">
                <span>Scene: {session.current_scene}</span>
                <span>Duration: {session.duration}</span>
                <span>Peak: {session.viewer_peak}</span>
              </div>
            </CardContent>
          </Card>
        ))}

        {sessions.filter(s => s.status === 'live').length === 0 && (
          <Card className="col-span-2">
            <CardContent className="flex flex-col items-center justify-center py-16">
              <Video className="h-16 w-16 text-muted-foreground mb-4" />
              <p className="text-muted-foreground">No live spectate sessions</p>
              <Button className="mt-4" variant="outline"><Play className="mr-2 h-4 w-4" />Start Stream</Button>
            </CardContent>
          </Card>
        )}
      </div>

      <Card>
        <CardHeader><CardTitle>All Spectate Sessions</CardTitle></CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Server</TableHead>
                <TableHead>Viewers</TableHead>
                <TableHead>Resolution</TableHead>
                <TableHead>FPS</TableHead>
                <TableHead>Scene</TableHead>
                <TableHead>Duration</TableHead>
                <TableHead>OBS</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {sessions.map(ss => (
                <TableRow key={ss.session_id}>
                  <TableCell className="font-medium">{ss.server_name}</TableCell>
                  <TableCell>{ss.spectator_count}/{ss.max_spectators}</TableCell>
                  <TableCell className="text-xs">{ss.stream_resolution}</TableCell>
                  <TableCell>{ss.stream_fps}</TableCell>
                  <TableCell><Badge variant="outline" className="text-xs">{ss.current_scene}</Badge></TableCell>
                  <TableCell className="text-xs">{ss.duration}</TableCell>
                  <TableCell>{ss.obs_connected ? <div className="h-2 w-2 rounded-full bg-green-500" /> : <div className="h-2 w-2 rounded-full bg-gray-300" />}</TableCell>
                  <TableCell><Badge variant={ss.status === 'live' ? 'destructive' : 'secondary'}>{ss.status}</Badge></TableCell>
                  <TableCell>
                    <div className="flex gap-1">
                      <Button size="sm" variant="ghost"><SwitchCamera className="h-4 w-4" /></Button>
                      <Button size="sm" variant="ghost"><Layout className="h-4 w-4" /></Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};

export default LiveSpectate;
