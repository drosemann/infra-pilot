import { useEffect, useState } from 'react';
import { FormattedMessage, useIntl } from 'react-intl';
import { apiClient } from '../lib/api';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';

interface HealingPolicy {
  id: string;
  name: string;
  resource_type: string;
  mode: string;
  enabled: boolean;
  health_checks: any[];
  actions: any[];
}

interface HealingEvent {
  id: string;
  policy_name: string;
  resource_id: string;
  status_before: string;
  status_after: string | null;
  overall_success: boolean;
  started_at: string;
}

export const SelfHealingPage = () => {
  const intl = useIntl();
  const [policies, setPolicies] = useState<HealingPolicy[]>([]);
  const [events, setEvents] = useState<HealingEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    try {
      const [polData, evtData] = await Promise.all([apiClient.listHealingPolicies(), apiClient.listHealingEvents()]);
      setPolicies(polData || []);
      setEvents(evtData || []);
    } catch (error) {
      toast.error('Failed to load self-healing data');
    } finally {
      setLoading(false);
    }
  };

  const togglePolicy = async (id: string, enabled: boolean) => {
    try {
      if (enabled) await apiClient.disableHealingPolicy(id);
      else await apiClient.enableHealingPolicy(id);
      setPolicies(policies.map((p) => p.id === id ? { ...p, enabled: !p.enabled } : p));
      toast.success(`Policy ${enabled ? 'disabled' : 'enabled'}`);
    } catch (error) {
      toast.error('Failed to toggle policy');
    }
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>;

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold"><FormattedMessage id="selfHealing.title" defaultMessage="Self-Healing Infrastructure" /></h1>
          <p className="text-muted-foreground mt-1"><FormattedMessage id="selfHealing.description" defaultMessage="Monitor health and automatically recover from failures" /></p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        <Card><CardHeader><CardTitle className="text-2xl text-center">{policies.length}</CardTitle></CardHeader><CardContent className="text-center text-muted-foreground"><FormattedMessage id="selfHealing.totalPolicies" defaultMessage="Policies" /></CardContent></Card>
        <Card><CardHeader><CardTitle className="text-2xl text-center">{policies.filter((p) => p.enabled).length}</CardTitle></CardHeader><CardContent className="text-center text-muted-foreground"><FormattedMessage id="selfHealing.activePolicies" defaultMessage="Active" /></CardContent></Card>
        <Card><CardHeader><CardTitle className="text-2xl text-center text-green-600">{events.filter((e) => e.overall_success).length}</CardTitle></CardHeader><CardContent className="text-center text-muted-foreground"><FormattedMessage id="selfHealing.successfulHeals" defaultMessage="Successful Heals" /></CardContent></Card>
        <Card><CardHeader><CardTitle className="text-2xl text-center text-red-600">{events.filter((e) => !e.overall_success).length}</CardTitle></CardHeader><CardContent className="text-center text-muted-foreground"><FormattedMessage id="selfHealing.failedHeals" defaultMessage="Failed Heals" /></CardContent></Card>
      </div>

      <Card>
        <CardHeader><CardTitle><FormattedMessage id="selfHealing.healingPolicies" defaultMessage="Healing Policies" /></CardTitle></CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead><FormattedMessage id="common.name" defaultMessage="Name" /></TableHead>
                <TableHead><FormattedMessage id="selfHealing.resourceType" defaultMessage="Resource Type" /></TableHead>
                <TableHead><FormattedMessage id="selfHealing.mode" defaultMessage="Mode" /></TableHead>
                <TableHead><FormattedMessage id="selfHealing.checks" defaultMessage="Checks" /></TableHead>
                <TableHead><FormattedMessage id="selfHealing.actions" defaultMessage="Actions" /></TableHead>
                <TableHead><FormattedMessage id="common.status" defaultMessage="Status" /></TableHead>
                <TableHead><FormattedMessage id="common.actions" defaultMessage="Actions" /></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {policies.map((p) => (
                <TableRow key={p.id}>
                  <TableCell className="font-medium">{p.name}</TableCell>
                  <TableCell><Badge variant="outline">{p.resource_type}</Badge></TableCell>
                  <TableCell><Badge variant={p.mode === 'automatic' ? 'default' : 'secondary'}>{p.mode}</Badge></TableCell>
                  <TableCell>{p.health_checks?.length || 0}</TableCell>
                  <TableCell>{p.actions?.length || 0}</TableCell>
                  <TableCell><Badge variant={p.enabled ? 'default' : 'outline'}>{p.enabled ? 'Enabled' : 'Disabled'}</Badge></TableCell>
                  <TableCell>
                    <Button size="sm" variant="outline" onClick={() => togglePolicy(p.id, p.enabled)}>
                      {p.enabled ? <FormattedMessage id="common.disable" defaultMessage="Disable" /> : <FormattedMessage id="common.enable" defaultMessage="Enable" />}
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle><FormattedMessage id="selfHealing.recentEvents" defaultMessage="Recent Healing Events" /></CardTitle></CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead><FormattedMessage id="selfHealing.policyName" defaultMessage="Policy" /></TableHead>
                <TableHead><FormattedMessage id="selfHealing.resourceId" defaultMessage="Resource" /></TableHead>
                <TableHead><FormattedMessage id="selfHealing.statusBefore" defaultMessage="Status Before" /></TableHead>
                <TableHead><FormattedMessage id="selfHealing.statusAfter" defaultMessage="Status After" /></TableHead>
                <TableHead><FormattedMessage id="selfHealing.result" defaultMessage="Result" /></TableHead>
                <TableHead><FormattedMessage id="common.time" defaultMessage="Time" /></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {events.map((ev) => (
                <TableRow key={ev.id}>
                  <TableCell className="font-medium text-sm">{ev.policy_name}</TableCell>
                  <TableCell className="font-mono text-xs">{ev.resource_id}</TableCell>
                  <TableCell><Badge variant={ev.status_before === 'unhealthy' ? 'destructive' : 'secondary'}>{ev.status_before}</Badge></TableCell>
                  <TableCell><Badge variant={ev.status_after === 'healthy' ? 'default' : 'outline'}>{ev.status_after || '-'}</Badge></TableCell>
                  <TableCell><Badge variant={ev.overall_success ? 'default' : 'destructive'}>{ev.overall_success ? 'Success' : 'Failed'}</Badge></TableCell>
                  <TableCell className="text-xs">{new Date(ev.started_at).toLocaleString()}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};

export default SelfHealingPage;
