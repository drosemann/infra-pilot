import { useEffect, useState } from 'react';
import { FormattedMessage, useIntl } from 'react-intl';
import { apiClient } from '../lib/api';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';

interface Pipeline {
  id: string;
  name: string;
  provider: string;
  status: string;
  repository: string;
  environment: string;
}

interface PipelineRun {
  id: string;
  pipeline_id: string;
  status: string;
  branch: string;
  started_at: string;
  duration_ms: number | null;
}

interface Deployment {
  id: string;
  pipeline_id: string;
  environment: string;
  version: string;
  status: string;
}

export const InfrastructurePipelinesPage = () => {
  const intl = useIntl();
  const [pipelines, setPipelines] = useState<Pipeline[]>([]);
  const [runs, setRuns] = useState<PipelineRun[]>([]);
  const [deployments, setDeployments] = useState<Deployment[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    try {
      const [plData, runData, depData] = await Promise.all([
        apiClient.listPipelines(),
        apiClient.listPipelineRuns(),
        apiClient.listDeployments(),
      ]);
      setPipelines(plData || []);
      setRuns(runData || []);
      setDeployments(depData || []);
    } catch (error) {
      toast.error('Failed to load pipeline data');
    } finally {
      setLoading(false);
    }
  };

  const triggerRun = async (id: string) => {
    try {
      const run = await apiClient.triggerPipelineRun(id);
      setRuns([run, ...runs]);
      toast.success('Pipeline run triggered');
    } catch (error) {
      toast.error('Failed to trigger run');
    }
  };

  const togglePipeline = async (id: string, currentStatus: string) => {
    try {
      if (currentStatus === 'active') {
        await apiClient.disablePipeline(id);
        setPipelines(pipelines.map((p) => p.id === id ? { ...p, status: 'disabled' } : p));
      } else {
        await apiClient.enablePipeline(id);
        setPipelines(pipelines.map((p) => p.id === id ? { ...p, status: 'active' } : p));
      }
      toast.success(`Pipeline ${currentStatus === 'active' ? 'disabled' : 'enabled'}`);
    } catch (error) {
      toast.error('Failed to toggle pipeline');
    }
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>;

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold"><FormattedMessage id="pipelines.title" defaultMessage="Infrastructure Pipelines" /></h1>
          <p className="text-muted-foreground mt-1"><FormattedMessage id="pipelines.description" defaultMessage="Manage CI/CD pipelines and deployments" /></p>
        </div>
      </div>

      <Tabs defaultValue="pipelines">
        <TabsList>
          <TabsTrigger value="pipelines"><FormattedMessage id="pipelines.pipelines" defaultMessage="Pipelines" /></TabsTrigger>
          <TabsTrigger value="runs"><FormattedMessage id="pipelines.runs" defaultMessage="Runs" /></TabsTrigger>
          <TabsTrigger value="deployments"><FormattedMessage id="pipelines.deployments" defaultMessage="Deployments" /></TabsTrigger>
        </TabsList>

        <TabsContent value="pipelines" className="space-y-4">
          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead><FormattedMessage id="common.name" defaultMessage="Name" /></TableHead>
                    <TableHead><FormattedMessage id="pipelines.provider" defaultMessage="Provider" /></TableHead>
                    <TableHead><FormattedMessage id="pipelines.repository" defaultMessage="Repository" /></TableHead>
                    <TableHead><FormattedMessage id="pipelines.environment" defaultMessage="Environment" /></TableHead>
                    <TableHead><FormattedMessage id="common.status" defaultMessage="Status" /></TableHead>
                    <TableHead><FormattedMessage id="common.actions" defaultMessage="Actions" /></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {pipelines.map((pl) => (
                    <TableRow key={pl.id}>
                      <TableCell className="font-medium">{pl.name}</TableCell>
                      <TableCell><Badge variant="outline">{pl.provider}</Badge></TableCell>
                      <TableCell className="font-mono text-sm">{pl.repository}</TableCell>
                      <TableCell>{pl.environment}</TableCell>
                      <TableCell><Badge variant={pl.status === 'active' ? 'default' : 'secondary'}>{pl.status}</Badge></TableCell>
                      <TableCell className="space-x-2">
                        <Button size="sm" onClick={() => triggerRun(pl.id)} disabled={pl.status !== 'active'}>
                          <FormattedMessage id="pipelines.run" defaultMessage="Run" />
                        </Button>
                        <Button size="sm" variant="outline" onClick={() => togglePipeline(pl.id, pl.status)}>
                          {pl.status === 'active' ? <FormattedMessage id="pipelines.disable" defaultMessage="Disable" /> : <FormattedMessage id="pipelines.enable" defaultMessage="Enable" />}
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="runs" className="space-y-4">
          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead><FormattedMessage id="pipelines.runId" defaultMessage="Run ID" /></TableHead>
                    <TableHead><FormattedMessage id="pipelines.branch" defaultMessage="Branch" /></TableHead>
                    <TableHead><FormattedMessage id="common.status" defaultMessage="Status" /></TableHead>
                    <TableHead><FormattedMessage id="pipelines.startedAt" defaultMessage="Started At" /></TableHead>
                    <TableHead><FormattedMessage id="pipelines.duration" defaultMessage="Duration" /></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {runs.map((run) => (
                    <TableRow key={run.id}>
                      <TableCell className="font-mono text-xs">{run.id.substring(0, 12)}...</TableCell>
                      <TableCell className="font-mono text-sm">{run.branch}</TableCell>
                      <TableCell><Badge variant={run.status === 'succeeded' ? 'default' : run.status === 'failed' ? 'destructive' : 'secondary'}>{run.status}</Badge></TableCell>
                      <TableCell className="text-xs">{new Date(run.started_at).toLocaleString()}</TableCell>
                      <TableCell>{run.duration_ms ? `${(run.duration_ms / 1000).toFixed(0)}s` : '-'}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="deployments" className="space-y-4">
          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead><FormattedMessage id="pipelines.deploymentId" defaultMessage="Deployment ID" /></TableHead>
                    <TableHead><FormattedMessage id="pipelines.environment" defaultMessage="Environment" /></TableHead>
                    <TableHead><FormattedMessage id="pipelines.version" defaultMessage="Version" /></TableHead>
                    <TableHead><FormattedMessage id="common.status" defaultMessage="Status" /></TableHead>
                    <TableHead><FormattedMessage id="pipelines.deployedAt" defaultMessage="Deployed At" /></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {deployments.map((dep) => (
                    <TableRow key={dep.id}>
                      <TableCell className="font-mono text-xs">{dep.id.substring(0, 12)}...</TableCell>
                      <TableCell><Badge variant="outline">{dep.environment}</Badge></TableCell>
                      <TableCell className="font-mono text-sm">{dep.version}</TableCell>
                      <TableCell><Badge variant={dep.status === 'deployed' ? 'default' : 'secondary'}>{dep.status}</Badge></TableCell>
                      <TableCell className="text-xs">-</TableCell>
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

export default InfrastructurePipelinesPage;
