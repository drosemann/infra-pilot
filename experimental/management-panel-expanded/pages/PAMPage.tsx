import { useEffect, useState } from 'react';
import { FormattedMessage, useIntl } from 'react-intl';
import { apiClient } from '../lib/api';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';

interface Role {
  role_id: string;
  name: string;
  role_type: string;
  permissions: string[];
}

interface AccessRequest {
  request_id: string;
  user_id: string;
  resource: string;
  status: string;
  reason: string;
  requested_duration_minutes: number;
}

interface SessionRecording {
  recording_id: string;
  user_id: string;
  resource: string;
  status: string;
  started_at: string;
}

export const PAMPage = () => {
  const intl = useIntl();
  const [roles, setRoles] = useState<Role[]>([]);
  const [requests, setRequests] = useState<AccessRequest[]>([]);
  const [recordings, setRecordings] = useState<SessionRecording[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    try {
      const [rolesData, requestsData, recordingsData] = await Promise.all([
        apiClient.listRoles(),
        apiClient.listAccessRequests(),
        apiClient.listSessionRecordings(),
      ]);
      setRoles(rolesData || []);
      setRequests(requestsData || []);
      setRecordings(recordingsData || []);
    } catch (error) {
      toast.error('Failed to load PAM data');
    } finally {
      setLoading(false);
    }
  };

  const approveRequest = async (id: string) => {
    try {
      await apiClient.approveAccessRequest(id, 'current-admin');
      setRequests(requests.map((r) => r.request_id === id ? { ...r, status: 'approved' } : r));
      toast.success('Request approved');
    } catch (error) {
      toast.error('Failed to approve request');
    }
  };

  const rejectRequest = async (id: string) => {
    try {
      await apiClient.rejectAccessRequest(id, 'current-admin', 'Denied');
      setRequests(requests.map((r) => r.request_id === id ? { ...r, status: 'rejected' } : r));
      toast.success('Request rejected');
    } catch (error) {
      toast.error('Failed to reject request');
    }
  };

  const getRoleBadgeColor = (type: string) => {
    const colors: Record<string, string> = { viewer: 'default', operator: 'secondary', admin: 'destructive', super_admin: 'destructive', break_glass: 'warning' };
    return colors[type] || 'outline';
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = { pending: 'secondary', approved: 'default', rejected: 'destructive', granted: 'default', expired: 'outline' };
    return variants[status] || 'outline';
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>;

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold"><FormattedMessage id="pam.title" defaultMessage="Privileged Access Management" /></h1>
          <p className="text-muted-foreground mt-1"><FormattedMessage id="pam.description" defaultMessage="Manage roles, access requests, and session recordings" /></p>
        </div>
      </div>

      <Tabs defaultValue="roles">
        <TabsList>
          <TabsTrigger value="roles"><FormattedMessage id="pam.roles" defaultMessage="Roles" /></TabsTrigger>
          <TabsTrigger value="requests"><FormattedMessage id="pam.requests" defaultMessage="Access Requests" /></TabsTrigger>
          <TabsTrigger value="recordings"><FormattedMessage id="pam.recordings" defaultMessage="Session Recordings" /></TabsTrigger>
        </TabsList>

        <TabsContent value="roles" className="space-y-4">
          <h2 className="text-xl font-semibold"><FormattedMessage id="pam.roleDefinitions" defaultMessage="Role Definitions" /></h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {roles.map((role) => (
              <Card key={role.role_id}>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span>{role.name}</span>
                    <Badge variant={getRoleBadgeColor(role.role_type) as any}>{role.role_type}</Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <p className="text-sm text-muted-foreground"><FormattedMessage id="pam.permissions" defaultMessage="Permissions" />:</p>
                    <div className="flex flex-wrap gap-1">
                      {role.permissions.map((perm, i) => (
                        <Badge key={i} variant="outline" className="text-xs">{perm}</Badge>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="requests" className="space-y-4">
          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead><FormattedMessage id="common.user" defaultMessage="User" /></TableHead>
                    <TableHead><FormattedMessage id="pam.resource" defaultMessage="Resource" /></TableHead>
                    <TableHead><FormattedMessage id="pam.reason" defaultMessage="Reason" /></TableHead>
                    <TableHead><FormattedMessage id="pam.duration" defaultMessage="Duration" /></TableHead>
                    <TableHead><FormattedMessage id="common.status" defaultMessage="Status" /></TableHead>
                    <TableHead><FormattedMessage id="common.actions" defaultMessage="Actions" /></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {requests.map((req) => (
                    <TableRow key={req.request_id}>
                      <TableCell className="font-medium">{req.user_id}</TableCell>
                      <TableCell className="font-mono text-sm">{req.resource}</TableCell>
                      <TableCell className="max-w-[200px] truncate">{req.reason}</TableCell>
                      <TableCell>{req.requested_duration_minutes} min</TableCell>
                      <TableCell><Badge variant={getStatusBadge(req.status)}>{req.status}</Badge></TableCell>
                      <TableCell className="space-x-2">
                        {req.status === 'pending' && (
                          <>
                            <Button size="sm" onClick={() => approveRequest(req.request_id)}><FormattedMessage id="pam.approve" defaultMessage="Approve" /></Button>
                            <Button size="sm" variant="destructive" onClick={() => rejectRequest(req.request_id)}><FormattedMessage id="pam.reject" defaultMessage="Reject" /></Button>
                          </>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="recordings" className="space-y-4">
          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead><FormattedMessage id="common.user" defaultMessage="User" /></TableHead>
                    <TableHead><FormattedMessage id="pam.resource" defaultMessage="Resource" /></TableHead>
                    <TableHead><FormattedMessage id="common.status" defaultMessage="Status" /></TableHead>
                    <TableHead><FormattedMessage id="pam.startedAt" defaultMessage="Started At" /></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {recordings.map((rec) => (
                    <TableRow key={rec.recording_id}>
                      <TableCell>{rec.user_id}</TableCell>
                      <TableCell className="font-mono text-sm">{rec.resource}</TableCell>
                      <TableCell><Badge variant={rec.status === 'recording' ? 'destructive' : 'default'}>{rec.status}</Badge></TableCell>
                      <TableCell className="text-xs">{new Date(rec.started_at).toLocaleString()}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default PAMPage;
