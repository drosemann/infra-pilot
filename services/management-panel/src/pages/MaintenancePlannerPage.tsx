import { useEffect, useState } from 'react';
import { FormattedMessage, useIntl } from 'react-intl';
import { apiClient } from '../lib/api';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Progress } from '../components/ui/progress';

interface MaintenanceWindow {
  id: string;
  name: string;
  status: string;
  maintenance_type: string;
  priority: string;
  impact: string;
  start_time: string;
  duration_minutes: number;
  affected_services: string[];
}

export const MaintenancePlannerPage = () => {
  const intl = useIntl();
  const [windows, setWindows] = useState<MaintenanceWindow[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    try {
      const data = await apiClient.listMaintenanceWindows();
      setWindows(data || []);
    } catch (error) {
      toast.error('Failed to load maintenance windows');
    } finally {
      setLoading(false);
    }
  };

  const executeWindow = async (id: string) => {
    try {
      await apiClient.executeMaintenanceWindow(id);
      setWindows(windows.map((w) => w.id === id ? { ...w, status: 'in_progress' } : w));
      toast.success('Maintenance started');
    } catch (error) {
      toast.error('Failed to start maintenance');
    }
  };

  const cancelWindow = async (id: string) => {
    try {
      await apiClient.cancelMaintenanceWindow(id);
      setWindows(windows.map((w) => w.id === id ? { ...w, status: 'cancelled' } : w));
      toast.success('Maintenance cancelled');
    } catch (error) {
      toast.error('Failed to cancel maintenance');
    }
  };

  const statusBadge = (status: string) => {
    const variants: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
      draft: 'secondary', scheduled: 'default', approved: 'default', in_progress: 'default', completed: 'outline', cancelled: 'destructive', failed: 'destructive',
    };
    return variants[status] || 'outline';
  };

  const impactBadge = (impact: string) => {
    const colors: Record<string, 'default' | 'destructive' | 'secondary' | 'outline'> = {
      none: 'default', minimal: 'secondary', degraded: 'warning' as any, downtime: 'destructive', full_outage: 'destructive',
    };
    return colors[impact] || 'outline';
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>;

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold"><FormattedMessage id="maintenance.title" defaultMessage="Scheduled Maintenance Planner" /></h1>
          <p className="text-muted-foreground mt-1"><FormattedMessage id="maintenance.description" defaultMessage="Plan, schedule, and execute maintenance windows" /></p>
        </div>
        <Button onClick={loadData} variant="outline"><FormattedMessage id="common.refresh" defaultMessage="Refresh" /></Button>
      </div>

      <div className="grid gap-4">
        {windows.map((w) => (
          <Card key={w.id}>
            <CardContent className="pt-6">
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold text-lg">{w.name}</h3>
                    <Badge variant={statusBadge(w.status)}>{w.status}</Badge>
                    <Badge variant={impactBadge(w.impact)}>{w.impact}</Badge>
                  </div>
                  <div className="flex items-center gap-4 text-sm text-muted-foreground">
                    <span><FormattedMessage id="maintenance.type" defaultMessage="Type" />: {w.maintenance_type}</span>
                    <span><FormattedMessage id="maintenance.priority" defaultMessage="Priority" />: {w.priority}</span>
                    <span><FormattedMessage id="maintenance.duration" defaultMessage="Duration" />: {w.duration_minutes} min</span>
                  </div>
                  <div className="flex items-center gap-4 text-sm text-muted-foreground">
                    <span><FormattedMessage id="maintenance.startTime" defaultMessage="Start" />: {new Date(w.start_time).toLocaleString()}</span>
                  </div>
                  {w.affected_services.length > 0 && (
                    <div className="flex items-center gap-1 text-sm">
                      <span className="text-muted-foreground"><FormattedMessage id="maintenance.affectedServices" defaultMessage="Services" />:</span>
                      {w.affected_services.map((s, i) => <Badge key={i} variant="outline" className="text-xs">{s}</Badge>)}
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  {w.status === 'approved' && (
                    <Button size="sm" onClick={() => executeWindow(w.id)}>
                      <FormattedMessage id="maintenance.execute" defaultMessage="Execute" />
                    </Button>
                  )}
                  {(w.status === 'scheduled' || w.status === 'approved') && (
                    <Button size="sm" variant="destructive" onClick={() => cancelWindow(w.id)}>
                      <FormattedMessage id="maintenance.cancel" defaultMessage="Cancel" />
                    </Button>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default MaintenancePlannerPage;
