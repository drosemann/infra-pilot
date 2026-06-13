import { useEffect, useState } from 'react';
import { FormattedMessage, useIntl } from 'react-intl';
import { apiClient } from '../lib/api';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { AlertTriangle, CheckCircle, XCircle } from 'lucide-react';

interface DriftEvent {
  id: string;
  baseline_id: string;
  check_id: string;
  resource_id: string;
  resource_type: string;
  severity: string;
  status: string;
  config_path: string;
  expected_value: any;
  actual_value: any;
  detected_at: string;
}

export const DriftDetectorPage = () => {
  const intl = useIntl();
  const [events, setEvents] = useState<DriftEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    try {
      const data = await apiClient.listDriftEvents();
      setEvents(data || []);
    } catch (error) {
      toast.error('Failed to load drift events');
    } finally {
      setLoading(false);
    }
  };

  const acknowledgeEvent = async (id: string) => {
    try {
      await apiClient.acknowledgeDriftEvent(id, 'current-user');
      setEvents(events.map((e) => e.id === id ? { ...e, status: 'acknowledged' } : e));
      toast.success('Event acknowledged');
    } catch (error) {
      toast.error('Failed to acknowledge');
    }
  };

  const markFalsePositive = async (id: string) => {
    try {
      await apiClient.markDriftFalsePositive(id);
      setEvents(events.map((e) => e.id === id ? { ...e, status: 'false_positive' } : e));
      toast.success('Marked as false positive');
    } catch (error) {
      toast.error('Failed to mark');
    }
  };

  const severityColor = (s: string) => {
    switch (s) {
      case 'critical': return 'destructive';
      case 'high': return 'destructive';
      case 'medium': return 'warning' as any;
      case 'low': return 'secondary';
      default: return 'outline';
    }
  };

  const statusIcon = (s: string) => {
    switch (s) {
      case 'detected': return <AlertTriangle className="h-4 w-4 text-red-500" />;
      case 'acknowledged': return <CheckCircle className="h-4 w-4 text-yellow-500" />;
      case 'remediated': return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'false_positive': return <XCircle className="h-4 w-4 text-gray-500" />;
      default: return null;
    }
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>;

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold"><FormattedMessage id="drift.title" defaultMessage="Configuration Drift Detector" /></h1>
          <p className="text-muted-foreground mt-1"><FormattedMessage id="drift.description" defaultMessage="Monitor and detect configuration drift across infrastructure" /></p>
        </div>
        <Button onClick={loadData} variant="outline"><FormattedMessage id="common.refresh" defaultMessage="Refresh" /></Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span><FormattedMessage id="drift.driftEvents" defaultMessage="Drift Events" /></span>
            <Badge variant="destructive">{events.filter((e) => e.status === 'detected').length}</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead></TableHead>
                <TableHead><FormattedMessage id="drift.resourceId" defaultMessage="Resource" /></TableHead>
                <TableHead><FormattedMessage id="drift.configPath" defaultMessage="Config Path" /></TableHead>
                <TableHead><FormattedMessage id="drift.expected" defaultMessage="Expected" /></TableHead>
                <TableHead><FormattedMessage id="drift.actual" defaultMessage="Actual" /></TableHead>
                <TableHead><FormattedMessage id="drift.severity" defaultMessage="Severity" /></TableHead>
                <TableHead><FormattedMessage id="drift.detectedAt" defaultMessage="Detected" /></TableHead>
                <TableHead><FormattedMessage id="common.actions" defaultMessage="Actions" /></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {events.map((ev) => (
                <TableRow key={ev.id}>
                  <TableCell>{statusIcon(ev.status)}</TableCell>
                  <TableCell className="font-mono text-xs">{ev.resource_id}</TableCell>
                  <TableCell className="font-mono text-xs">{ev.config_path}</TableCell>
                  <TableCell className="font-mono text-xs max-w-[100px] truncate">{JSON.stringify(ev.expected_value)}</TableCell>
                  <TableCell className="font-mono text-xs max-w-[100px] truncate">{JSON.stringify(ev.actual_value)}</TableCell>
                  <TableCell><Badge variant={severityColor(ev.severity) as any}>{ev.severity}</Badge></TableCell>
                  <TableCell className="text-xs">{new Date(ev.detected_at).toLocaleString()}</TableCell>
                  <TableCell className="space-x-1">
                    {ev.status === 'detected' && (
                      <>
                        <Button size="sm" variant="outline" onClick={() => acknowledgeEvent(ev.id)}>
                          <FormattedMessage id="drift.acknowledge" defaultMessage="Ack" />
                        </Button>
                        <Button size="sm" variant="ghost" onClick={() => markFalsePositive(ev.id)}>
                          <FormattedMessage id="drift.falsePositive" defaultMessage="FP" />
                        </Button>
                      </>
                    )}
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

export default DriftDetectorPage;
