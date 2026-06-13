import { useEffect, useState } from 'react';
import { FormattedMessage, useIntl } from 'react-intl';
import { apiClient } from '../lib/api';
import { toast } from 'sonner';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Label } from '../components/ui/label';
import { Input } from '../components/ui/input';

interface Session {
  session_id: string;
  user_id: string;
  ip_address: string;
  user_agent: string;
  risk_level: string;
  is_active: boolean;
  created_at: string;
  expires_at: string;
}

interface RiskEvent {
  event_id: string;
  session_id: string;
  risk_score: number;
  risk_level: string;
  details: string;
  detected_at: string;
}

export const SessionManagerPage = () => {
  const intl = useIntl();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [riskEvents, setRiskEvents] = useState<RiskEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [showRevokeDialog, setShowRevokeDialog] = useState(false);
  const [selectedSessionId, setSelectedSessionId] = useState('');
  const [revokeReason, setRevokeReason] = useState('');

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 10000);
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      const [sessionData, riskData] = await Promise.all([
        apiClient.listSessions(),
        apiClient.listRiskEvents(),
      ]);
      setSessions(sessionData || []);
      setRiskEvents(riskData || []);
    } catch (error) {
      toast.error('Failed to load session data');
    } finally {
      setLoading(false);
    }
  };

  const revokeSession = async () => {
    try {
      await apiClient.revokeSession(selectedSessionId, revokeReason);
      setSessions(sessions.map((s) => s.session_id === selectedSessionId ? { ...s, is_active: false } : s));
      toast.success('Session revoked');
      setShowRevokeDialog(false);
      setRevokeReason('');
    } catch (error) {
      toast.error('Failed to revoke session');
    }
  };

  const revokeAllSessions = async () => {
    try {
      const count = await apiClient.revokeAllSessions();
      setSessions(sessions.map((s) => ({ ...s, is_active: false })));
      toast.success(`Revoked ${count} sessions`);
    } catch (error) {
      toast.error('Failed to revoke sessions');
    }
  };

  const getRiskBadgeVariant = (level: string) => {
    switch (level) {
      case 'low': return 'default';
      case 'medium': return 'secondary';
      case 'high': return 'destructive';
      case 'critical': return 'destructive';
      default: return 'outline';
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>;
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold"><FormattedMessage id="sessionManager.title" defaultMessage="Session Manager" /></h1>
          <p className="text-muted-foreground mt-1"><FormattedMessage id="sessionManager.description" defaultMessage="Monitor and manage user sessions with risk scoring" /></p>
        </div>
      </div>

      <Tabs defaultValue="active">
        <TabsList>
          <TabsTrigger value="active"><FormattedMessage id="sessionManager.activeSessions" defaultMessage="Active Sessions" /></TabsTrigger>
          <TabsTrigger value="risk"><FormattedMessage id="sessionManager.riskEvents" defaultMessage="Risk Events" /></TabsTrigger>
        </TabsList>

        <TabsContent value="active" className="space-y-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-semibold">
                <FormattedMessage id="sessionManager.activeUserSessions" defaultMessage="Active User Sessions" />
              </h2>
              <Badge variant="default">{sessions.filter((s) => s.is_active).length} active</Badge>
            </div>
            <Button variant="destructive" onClick={revokeAllSessions}>
              <FormattedMessage id="sessionManager.revokeAll" defaultMessage="Revoke All" />
            </Button>
          </div>
          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead><FormattedMessage id="common.user" defaultMessage="User" /></TableHead>
                    <TableHead><FormattedMessage id="sessionManager.ipAddress" defaultMessage="IP Address" /></TableHead>
                    <TableHead><FormattedMessage id="sessionManager.userAgent" defaultMessage="User Agent" /></TableHead>
                    <TableHead><FormattedMessage id="sessionManager.riskLevel" defaultMessage="Risk Level" /></TableHead>
                    <TableHead><FormattedMessage id="common.status" defaultMessage="Status" /></TableHead>
                    <TableHead><FormattedMessage id="sessionManager.created" defaultMessage="Created" /></TableHead>
                    <TableHead><FormattedMessage id="common.actions" defaultMessage="Actions" /></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sessions.map((session) => (
                    <TableRow key={session.session_id}>
                      <TableCell className="font-medium">{session.user_id}</TableCell>
                      <TableCell className="font-mono text-sm">{session.ip_address}</TableCell>
                      <TableCell className="max-w-[150px] truncate text-xs">{session.user_agent}</TableCell>
                      <TableCell>
                        <Badge variant={getRiskBadgeVariant(session.risk_level)}>{session.risk_level}</Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant={session.is_active ? 'default' : 'secondary'}>{session.is_active ? 'Active' : 'Inactive'}</Badge>
                      </TableCell>
                      <TableCell className="text-xs">{new Date(session.created_at).toLocaleString()}</TableCell>
                      <TableCell>
                        {session.is_active && (
                          <Button variant="destructive" size="sm" onClick={() => { setSelectedSessionId(session.session_id); setShowRevokeDialog(true); }}>
                            <FormattedMessage id="sessionManager.revoke" defaultMessage="Revoke" />
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="risk" className="space-y-4">
          <h2 className="text-xl font-semibold"><FormattedMessage id="sessionManager.riskDetectionEvents" defaultMessage="Risk Detection Events" /></h2>
          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead><FormattedMessage id="sessionManager.eventId" defaultMessage="Event ID" /></TableHead>
                    <TableHead><FormattedMessage id="sessionManager.riskScore" defaultMessage="Risk Score" /></TableHead>
                    <TableHead><FormattedMessage id="sessionManager.riskLevel" defaultMessage="Risk Level" /></TableHead>
                    <TableHead><FormattedMessage id="sessionManager.details" defaultMessage="Details" /></TableHead>
                    <TableHead><FormattedMessage id="sessionManager.detectedAt" defaultMessage="Detected At" /></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {riskEvents.map((event) => (
                    <TableRow key={event.event_id}>
                      <TableCell className="font-mono text-xs">{event.event_id.substring(0, 12)}...</TableCell>
                      <TableCell>{event.risk_score.toFixed(1)}</TableCell>
                      <TableCell><Badge variant={getRiskBadgeVariant(event.risk_level)}>{event.risk_level}</Badge></TableCell>
                      <TableCell className="max-w-[200px] truncate">{event.details}</TableCell>
                      <TableCell className="text-xs">{new Date(event.detected_at).toLocaleString()}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <Dialog open={showRevokeDialog} onOpenChange={setShowRevokeDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle><FormattedMessage id="sessionManager.revokeSession" defaultMessage="Revoke Session" /></DialogTitle>
            <DialogDescription><FormattedMessage id="sessionManager.revokeDesc" defaultMessage="Are you sure you want to revoke this session?" /></DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label><FormattedMessage id="sessionManager.reason" defaultMessage="Reason (optional)" /></Label>
              <Input value={revokeReason} onChange={(e) => setRevokeReason(e.target.value)} placeholder="User reported suspicious activity" />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowRevokeDialog(false)}><FormattedMessage id="common.cancel" defaultMessage="Cancel" /></Button>
            <Button variant="destructive" onClick={revokeSession}><FormattedMessage id="sessionManager.revoke" defaultMessage="Revoke" /></Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default SessionManagerPage;
