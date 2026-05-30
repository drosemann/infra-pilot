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
import { Shield, AlertTriangle, Ban, UserX, FileText, Clock, CheckCircle, Gavel, Eye, Search, Hash, Activity } from 'lucide-react';

interface BanRecord {
  ban_id: string;
  player_id: string;
  player_name: string;
  game: string;
  server_id: string;
  reason: string;
  ban_type: string;
  evidence_count: number;
  banned_by: string;
  banned_at: string;
  expires_at: string | null;
  appeal_status: string;
  detected_by: string;
  severity: string;
}

interface DetectionEvent {
  event_id: string;
  player_id: string;
  player_name: string;
  game: string;
  detection_type: string;
  confidence: number;
  details: string;
  timestamp: string;
  status: string;
}

const mockBans: BanRecord[] = [
  { ban_id: 'ban-001', player_id: 'p-abc123', player_name: 'xX_H4x0r_Xx', game: 'minecraft', server_id: 'mc-survival-01', reason: 'Aimbot detection (confidence 98.7%)', ban_type: 'permanent', evidence_count: 12, banned_by: 'AutoMod', banned_at: '2024-05-29T08:30:00Z', expires_at: null, appeal_status: 'denied', detected_by: 'Sentinel', severity: 'critical' },
  { ban_id: 'ban-002', player_id: 'p-def456', player_name: 'SpeedDemon99', game: 'minecraft', server_id: 'mc-pvp-02', reason: 'Speed hack (3.2x normal velocity)', ban_type: 'temporary', evidence_count: 5, banned_by: 'AutoMod', banned_at: '2024-05-29T07:15:00Z', expires_at: '2024-06-05T07:15:00Z', appeal_status: 'pending', detected_by: 'Sentinel', severity: 'high' },
  { ban_id: 'ban-003', player_id: 'p-ghi789', player_name: 'FlyHackKing', game: 'minecraft', server_id: 'mc-survival-02', reason: 'Flight hacks detected across 3 sessions', ban_type: 'permanent', evidence_count: 8, banned_by: 'Moderator_Steve', banned_at: '2024-05-28T22:00:00Z', expires_at: null, appeal_status: 'none', detected_by: 'EAC', severity: 'critical' },
  { ban_id: 'ban-004', player_id: 'p-jkl012', player_name: 'AutoClickerPro', game: 'minecraft', server_id: 'mc-pvp-01', reason: 'Auto-clicker (22 cps average)', ban_type: 'temporary', evidence_count: 3, banned_by: 'AutoMod', banned_at: '2024-05-28T18:45:00Z', expires_at: '2024-06-04T18:45:00Z', appeal_status: 'approved', detected_by: 'Sentinel', severity: 'medium' },
  { ban_id: 'ban-005', player_id: 'p-mno345', player_name: 'X-Ray_Vision', game: 'minecraft', server_id: 'mc-survival-03', reason: 'X-ray resource pack detected', ban_type: 'permanent', evidence_count: 6, banned_by: 'AutoMod', banned_at: '2024-05-27T14:20:00Z', expires_at: null, appeal_status: 'none', detected_by: 'EAC', severity: 'high' },
];

const mockDetections: DetectionEvent[] = [
  { event_id: 'det-001', player_id: 'p-pqr678', player_name: 'NewPlayer42', game: 'minecraft', detection_type: 'unusual_movement', confidence: 32.5, details: 'Minor speed variance', timestamp: '2024-05-29T09:00:00Z', status: 'investigating' },
  { event_id: 'det-002', player_id: 'p-stu901', player_name: 'BuilderJohn', game: 'minecraft', detection_type: 'impossible_block_break', confidence: 12.1, details: 'Single tick block break (latency spike)', timestamp: '2024-05-29T08:55:00Z', status: 'dismissed' },
  { event_id: 'det-003', player_id: 'p-vwx234', player_name: 'PvP_Master', game: 'minecraft', detection_type: 'reach_attack', confidence: 78.4, details: 'Extended reach 4.7 blocks (threshold 4.5)', timestamp: '2024-05-29T08:50:00Z', status: 'flagged' },
];

const AntiCheat: React.FC = () => {
  const [bans, setBans] = useState<BanRecord[]>(mockBans);
  const [detections, setDetections] = useState<DetectionEvent[]>(mockDetections);
  const [selectedBan, setSelectedBan] = useState<BanRecord | null>(null);

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Anti-Cheat Management</h1>
          <p className="text-muted-foreground">Sentinel/EAC detection, ban workflow, evidence packaging and appeal management</p>
        </div>
        <Badge variant="secondary" className="text-sm">
          <Activity className="mr-1 h-4 w-4" />{detections.filter(d => d.status === 'investigating' || d.status === 'flagged').length} Active Flags
        </Badge>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Total Bans</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{bans.length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Permanent</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-red-500">{bans.filter(b => b.ban_type === 'permanent').length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Temporary</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-yellow-500">{bans.filter(b => b.ban_type === 'temporary').length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Pending Appeals</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-blue-500">{bans.filter(b => b.appeal_status === 'pending').length}</div></CardContent></Card>
      </div>

      <Tabs defaultValue="bans">
        <TabsList>
          <TabsTrigger value="bans">Bans</TabsTrigger>
          <TabsTrigger value="detections">Live Detections</TabsTrigger>
          <TabsTrigger value="config">Configuration</TabsTrigger>
        </TabsList>

        <TabsContent value="bans">
          <Card>
            <CardHeader><CardTitle>Ban Records</CardTitle></CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Player</TableHead>
                    <TableHead>Game</TableHead>
                    <TableHead>Reason</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Detected By</TableHead>
                    <TableHead>Severity</TableHead>
                    <TableHead>Banned</TableHead>
                    <TableHead>Appeal</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {bans.map(ban => (
                    <TableRow key={ban.ban_id} className="cursor-pointer" onClick={() => setSelectedBan(ban)}>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <UserX className="h-4 w-4 text-red-500" />
                          <span className="font-medium">{ban.player_name}</span>
                        </div>
                        <div className="text-xs text-muted-foreground">{ban.player_id}</div>
                      </TableCell>
                      <TableCell><Badge variant="outline" className="text-xs">{ban.game}</Badge></TableCell>
                      <TableCell className="max-w-[200px] truncate text-xs">{ban.reason}</TableCell>
                      <TableCell>
                        <Badge variant={ban.ban_type === 'permanent' ? 'destructive' : 'secondary'}>{ban.ban_type}</Badge>
                      </TableCell>
                      <TableCell><Badge variant="outline" className="text-xs">{ban.detected_by}</Badge></TableCell>
                      <TableCell>
                        <Badge variant={ban.severity === 'critical' ? 'destructive' : ban.severity === 'high' ? 'default' : 'secondary'}>{ban.severity}</Badge>
                      </TableCell>
                      <TableCell className="text-xs">{new Date(ban.banned_at).toLocaleDateString()}</TableCell>
                      <TableCell>
                        <Badge variant={ban.appeal_status === 'none' ? 'outline' : ban.appeal_status === 'pending' ? 'secondary' : ban.appeal_status === 'approved' ? 'default' : 'destructive'}>{ban.appeal_status}</Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="detections">
          <Card>
            <CardHeader><CardTitle>Live Detection Events</CardTitle></CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Player</TableHead>
                    <TableHead>Detection Type</TableHead>
                    <TableHead>Confidence</TableHead>
                    <TableHead>Details</TableHead>
                    <TableHead>Time</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {detections.map(det => (
                    <TableRow key={det.event_id}>
                      <TableCell className="font-medium">{det.player_name}</TableCell>
                      <TableCell><code className="text-xs bg-muted px-1 rounded">{det.detection_type}</code></TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Progress value={det.confidence} className="w-16" />
                          <span className="text-xs">{det.confidence.toFixed(0)}%</span>
                        </div>
                      </TableCell>
                      <TableCell className="text-xs max-w-[200px] truncate">{det.details}</TableCell>
                      <TableCell className="text-xs">{new Date(det.timestamp).toLocaleTimeString()}</TableCell>
                      <TableCell>
                        <Badge variant={det.status === 'flagged' ? 'destructive' : det.status === 'investigating' ? 'secondary' : 'outline'}>{det.status}</Badge>
                      </TableCell>
                      <TableCell>
                        <Button size="sm" variant="ghost"><Gavel className="h-4 w-4" /></Button>
                        <Button size="sm" variant="ghost"><Eye className="h-4 w-4" /></Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="config">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <Card><CardHeader><CardTitle className="text-sm">Sentinel Config</CardTitle></CardHeader><CardContent className="space-y-2 text-sm"><div className="flex justify-between"><span>Detection threshold</span><Badge>75%</Badge></div><div className="flex justify-between"><span>Auto-ban enabled</span><Badge variant="secondary">Yes</Badge></div><div className="flex justify-between"><span>Max violations</span><Badge>3 / 24h</Badge></div></CardContent></Card>
            <Card><CardHeader><CardTitle className="text-sm">EAC Config</CardTitle></CardHeader><CardContent className="space-y-2 text-sm"><div className="flex justify-between"><span>Scan interval</span><Badge>30s</Badge></div><div className="flex justify-between"><span>Memory scanning</span><Badge variant="secondary">Enabled</Badge></div><div className="flex justify-between"><span>Process whitelist</span><Badge>12 entries</Badge></div></CardContent></Card>
            <Card><CardHeader><CardTitle className="text-sm">Appeal Settings</CardTitle></CardHeader><CardContent className="space-y-2 text-sm"><div className="flex justify-between"><span>Appeal cooldown</span><Badge>7 days</Badge></div><div className="flex justify-between"><span>Requires evidence</span><Badge variant="secondary">Yes</Badge></div><div className="flex justify-between"><span>Auto-review</span><Badge>Disabled</Badge></div></CardContent></Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AntiCheat;
