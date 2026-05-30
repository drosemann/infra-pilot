import { useEffect, useState } from 'react';
import { FormattedMessage, useIntl } from 'react-intl';
import { apiClient } from '../lib/api';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';

interface Workflow {
  id: string;
  name: string;
  description: string;
  status: string;
  category: string;
  tags: string[];
  created_at: string;
}

interface WorkflowExecution {
  id: string;
  workflow_id: string;
  status: string;
  started_at: string;
  duration_ms: number | null;
}

export const WorkflowStudioPage = () => {
  const intl = useIntl();
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [executions, setExecutions] = useState<WorkflowExecution[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    try {
      const [wfData, execData] = await Promise.all([apiClient.listWorkflows(), apiClient.listWorkflowExecutions()]);
      setWorkflows(wfData || []);
      setExecutions(execData || []);
    } catch (error) {
      toast.error('Failed to load workflow data');
    } finally {
      setLoading(false);
    }
  };

  const deleteWorkflow = async (id: string) => {
    try {
      await apiClient.deleteWorkflow(id);
      setWorkflows(workflows.filter((w) => w.id !== id));
      toast.success('Workflow deleted');
    } catch (error) {
      toast.error('Failed to delete workflow');
    }
  };

  const activateWorkflow = async (id: string) => {
    try {
      await apiClient.activateWorkflow(id);
      setWorkflows(workflows.map((w) => w.id === id ? { ...w, status: 'active' } : w));
      toast.success('Workflow activated');
    } catch (error) {
      toast.error('Failed to activate workflow');
    }
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>;

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold"><FormattedMessage id="workflowStudio.title" defaultMessage="Workflow Studio" /></h1>
          <p className="text-muted-foreground mt-1"><FormattedMessage id="workflowStudio.description" defaultMessage="Design, manage, and execute automation workflows" /></p>
        </div>
      </div>

      <Tabs defaultValue="workflows">
        <TabsList>
          <TabsTrigger value="workflows"><FormattedMessage id="workflowStudio.workflows" defaultMessage="Workflows" /></TabsTrigger>
          <TabsTrigger value="executions"><FormattedMessage id="workflowStudio.executions" defaultMessage="Executions" /></TabsTrigger>
        </TabsList>

        <TabsContent value="workflows" className="space-y-4">
          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead><FormattedMessage id="common.name" defaultMessage="Name" /></TableHead>
                    <TableHead><FormattedMessage id="common.description" defaultMessage="Description" /></TableHead>
                    <TableHead><FormattedMessage id="workflowStudio.category" defaultMessage="Category" /></TableHead>
                    <TableHead><FormattedMessage id="common.status" defaultMessage="Status" /></TableHead>
                    <TableHead><FormattedMessage id="common.created" defaultMessage="Created" /></TableHead>
                    <TableHead><FormattedMessage id="common.actions" defaultMessage="Actions" /></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {workflows.map((wf) => (
                    <TableRow key={wf.id}>
                      <TableCell className="font-medium">{wf.name}</TableCell>
                      <TableCell className="max-w-[200px] truncate text-sm text-muted-foreground">{wf.description}</TableCell>
                      <TableCell><Badge variant="outline">{wf.category}</Badge></TableCell>
                      <TableCell><Badge variant={wf.status === 'active' ? 'default' : wf.status === 'draft' ? 'secondary' : 'outline'}>{wf.status}</Badge></TableCell>
                      <TableCell className="text-xs">{new Date(wf.created_at).toLocaleDateString()}</TableCell>
                      <TableCell className="space-x-2">
                        {wf.status === 'draft' && (
                          <Button size="sm" variant="outline" onClick={() => activateWorkflow(wf.id)}>
                            <FormattedMessage id="workflowStudio.activate" defaultMessage="Activate" />
                          </Button>
                        )}
                        <Button size="sm" variant="destructive" onClick={() => deleteWorkflow(wf.id)}>
                          <FormattedMessage id="common.delete" defaultMessage="Delete" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="executions" className="space-y-4">
          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead><FormattedMessage id="workflowStudio.executionId" defaultMessage="Execution ID" /></TableHead>
                    <TableHead><FormattedMessage id="common.status" defaultMessage="Status" /></TableHead>
                    <TableHead><FormattedMessage id="workflowStudio.startedAt" defaultMessage="Started At" /></TableHead>
                    <TableHead><FormattedMessage id="workflowStudio.duration" defaultMessage="Duration" /></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {executions.map((exec) => (
                    <TableRow key={exec.id}>
                      <TableCell className="font-mono text-xs">{exec.id.substring(0, 12)}...</TableCell>
                      <TableCell>
                        <Badge variant={exec.status === 'succeeded' ? 'default' : exec.status === 'failed' ? 'destructive' : 'secondary'}>{exec.status}</Badge>
                      </TableCell>
                      <TableCell className="text-xs">{new Date(exec.started_at).toLocaleString()}</TableCell>
                      <TableCell>{exec.duration_ms ? `${(exec.duration_ms / 1000).toFixed(1)}s` : '-'}</TableCell>
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

export default WorkflowStudioPage;
