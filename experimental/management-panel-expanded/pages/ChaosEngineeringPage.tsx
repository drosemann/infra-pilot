import { useEffect, useState } from 'react';
import { FormattedMessage, useIntl } from 'react-intl';
import { apiClient } from '../lib/api';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';

interface Experiment {
  id: string;
  name: string;
  status: string;
  target_type: string;
  hypothesis: string;
  blast_radius: string;
  duration_minutes: number;
  created_by: string;
  created_at: string;
}

interface ExperimentRun {
  id: string;
  experiment_id: string;
  status: string;
  hypothesis_result: string | null;
  duration_ms: number | null;
  started_at: string;
}

export const ChaosEngineeringPage = () => {
  const intl = useIntl();
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [runs, setRuns] = useState<ExperimentRun[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    try {
      const [expData, runData] = await Promise.all([apiClient.listChaosExperiments(), apiClient.listChaosRuns()]);
      setExperiments(expData || []);
      setRuns(runData || []);
    } catch (error) {
      toast.error('Failed to load chaos data');
    } finally {
      setLoading(false);
    }
  };

  const runExperiment = async (id: string) => {
    try {
      const run = await apiClient.runChaosExperiment(id);
      setRuns([run, ...runs]);
      toast.success('Experiment started');
    } catch (error) {
      toast.error('Failed to run experiment');
    }
  };

  const approveExperiment = async (id: string) => {
    try {
      await apiClient.approveChaosExperiment(id);
      setExperiments(experiments.map((e) => e.id === id ? { ...e, status: 'scheduled' } : e));
      toast.success('Experiment approved');
    } catch (error) {
      toast.error('Failed to approve');
    }
  };

  const cancelExperiment = async (id: string) => {
    try {
      await apiClient.cancelChaosExperiment(id);
      setExperiments(experiments.map((e) => e.id === id ? { ...e, status: 'cancelled' } : e));
      toast.success('Experiment cancelled');
    } catch (error) {
      toast.error('Failed to cancel');
    }
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>;

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold"><FormattedMessage id="chaos.title" defaultMessage="Chaos Engineering Toolkit" /></h1>
          <p className="text-muted-foreground mt-1"><FormattedMessage id="chaos.description" defaultMessage="Plan and execute chaos experiments to test infrastructure resilience" /></p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader><CardTitle><FormattedMessage id="chaos.experiments" defaultMessage="Experiments" /></CardTitle></CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead><FormattedMessage id="common.name" defaultMessage="Name" /></TableHead>
                  <TableHead><FormattedMessage id="chaos.targetType" defaultMessage="Target" /></TableHead>
                  <TableHead><FormattedMessage id="chaos.hypothesis" defaultMessage="Hypothesis" /></TableHead>
                  <TableHead><FormattedMessage id="chaos.blastRadius" defaultMessage="Blast Radius" /></TableHead>
                  <TableHead><FormattedMessage id="common.status" defaultMessage="Status" /></TableHead>
                  <TableHead><FormattedMessage id="common.actions" defaultMessage="Actions" /></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {experiments.map((exp) => (
                  <TableRow key={exp.id}>
                    <TableCell className="font-medium">{exp.name}</TableCell>
                    <TableCell><Badge variant="outline">{exp.target_type}</Badge></TableCell>
                    <TableCell className="text-xs max-w-[100px] truncate">{exp.hypothesis}</TableCell>
                    <TableCell><Badge variant={exp.blast_radius === 'full' ? 'destructive' : 'secondary'}>{exp.blast_radius}</Badge></TableCell>
                    <TableCell><Badge variant={exp.status === 'running' ? 'default' : exp.status === 'draft' ? 'secondary' : 'outline'}>{exp.status}</Badge></TableCell>
                    <TableCell className="space-x-1">
                      {exp.status === 'draft' && (
                        <Button size="sm" variant="outline" onClick={() => approveExperiment(exp.id)}>
                          <FormattedMessage id="chaos.approve" defaultMessage="Approve" />
                        </Button>
                      )}
                      {exp.status === 'scheduled' && (
                        <Button size="sm" onClick={() => runExperiment(exp.id)}>
                          <FormattedMessage id="chaos.run" defaultMessage="Run" />
                        </Button>
                      )}
                      {(exp.status === 'draft' || exp.status === 'scheduled') && (
                        <Button size="sm" variant="destructive" onClick={() => cancelExperiment(exp.id)}>
                          <FormattedMessage id="common.cancel" defaultMessage="Cancel" />
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle><FormattedMessage id="chaos.recentRuns" defaultMessage="Recent Runs" /></CardTitle></CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead><FormattedMessage id="chaos.runId" defaultMessage="Run ID" /></TableHead>
                  <TableHead><FormattedMessage id="common.status" defaultMessage="Status" /></TableHead>
                  <TableHead><FormattedMessage id="chaos.hypothesisResult" defaultMessage="Result" /></TableHead>
                  <TableHead><FormattedMessage id="chaos.duration" defaultMessage="Duration" /></TableHead>
                  <TableHead><FormattedMessage id="chaos.startedAt" defaultMessage="Started" /></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {runs.map((run) => (
                  <TableRow key={run.id}>
                    <TableCell className="font-mono text-xs">{run.id.substring(0, 12)}...</TableCell>
                    <TableCell><Badge variant={run.status === 'completed' ? 'default' : run.status === 'failed' ? 'destructive' : 'secondary'}>{run.status}</Badge></TableCell>
                    <TableCell><Badge variant={run.hypothesis_result === 'proved' ? 'default' : 'secondary'}>{run.hypothesis_result || '-'}</Badge></TableCell>
                    <TableCell>{run.duration_ms ? `${(run.duration_ms / 1000).toFixed(0)}s` : '-'}</TableCell>
                    <TableCell className="text-xs">{new Date(run.started_at).toLocaleString()}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default ChaosEngineeringPage;
