import { useEffect, useState } from 'react';
import { FormattedMessage, useIntl } from 'react-intl';
import { apiClient } from '../lib/api';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';

interface AnsibleInventory {
  id: string;
  name: string;
  description: string;
  hosts: Record<string, any>;
  groups: Record<string, any>;
}

interface Playbook {
  id: string;
  name: string;
  tool: string;
  version: string;
  tags: string[];
}

interface JobExecution {
  id: string;
  playbook_id: string;
  tool: string;
  status: string;
  output: string;
  started_at: string;
}

export const AnsibleSaltPage = () => {
  const intl = useIntl();
  const [inventories, setInventories] = useState<AnsibleInventory[]>([]);
  const [playbooks, setPlaybooks] = useState<Playbook[]>([]);
  const [jobs, setJobs] = useState<JobExecution[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    try {
      const [invData, pbData, jobData] = await Promise.all([
        apiClient.listAnsibleInventories(),
        apiClient.listAnsiblePlaybooks(),
        apiClient.listAnsibleJobs(),
      ]);
      setInventories(invData || []);
      setPlaybooks(pbData || []);
      setJobs(jobData || []);
    } catch (error) {
      toast.error('Failed to load Ansible/Salt data');
    } finally {
      setLoading(false);
    }
  };

  const executePlaybook = async (id: string) => {
    try {
      const job = await apiClient.executeAnsiblePlaybook(id);
      setJobs([job, ...jobs]);
      toast.success('Playbook execution started');
    } catch (error) {
      toast.error('Failed to execute playbook');
    }
  };

  const cancelJob = async (id: string) => {
    try {
      await apiClient.cancelAnsibleJob(id);
      setJobs(jobs.map((j) => j.id === id ? { ...j, status: 'cancelled' } : j));
      toast.success('Job cancelled');
    } catch (error) {
      toast.error('Failed to cancel job');
    }
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>;

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold"><FormattedMessage id="ansibleSalt.title" defaultMessage="Ansible & Salt Integration" /></h1>
          <p className="text-muted-foreground mt-1"><FormattedMessage id="ansibleSalt.description" defaultMessage="Manage inventories, playbooks, and automation jobs" /></p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span><FormattedMessage id="ansibleSalt.inventories" defaultMessage="Inventories" /></span>
              <Badge>{inventories.length}</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {inventories.map((inv) => (
                <div key={inv.id} className="p-3 border rounded-lg">
                  <p className="font-medium">{inv.name}</p>
                  <p className="text-xs text-muted-foreground">{Object.keys(inv.hosts).length} hosts, {Object.keys(inv.groups).length} groups</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span><FormattedMessage id="ansibleSalt.playbooks" defaultMessage="Playbooks" /></span>
              <Badge>{playbooks.length}</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead><FormattedMessage id="common.name" defaultMessage="Name" /></TableHead>
                  <TableHead><FormattedMessage id="ansibleSalt.tool" defaultMessage="Tool" /></TableHead>
                  <TableHead><FormattedMessage id="common.actions" defaultMessage="Actions" /></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {playbooks.map((pb) => (
                  <TableRow key={pb.id}>
                    <TableCell className="font-medium text-sm">{pb.name}</TableCell>
                    <TableCell><Badge variant="outline">{pb.tool}</Badge></TableCell>
                    <TableCell>
                      <Button size="sm" onClick={() => executePlaybook(pb.id)}>
                        <FormattedMessage id="ansibleSalt.run" defaultMessage="Run" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span><FormattedMessage id="ansibleSalt.jobs" defaultMessage="Jobs" /></span>
              <Badge variant="default">{jobs.filter((j) => j.status === 'running').length} running</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead><FormattedMessage id="ansibleSalt.jobId" defaultMessage="Job" /></TableHead>
                  <TableHead><FormattedMessage id="common.status" defaultMessage="Status" /></TableHead>
                  <TableHead><FormattedMessage id="common.actions" defaultMessage="Actions" /></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {jobs.map((job) => (
                  <TableRow key={job.id}>
                    <TableCell className="font-mono text-xs">{job.id.substring(0, 10)}...</TableCell>
                    <TableCell>
                      <Badge variant={job.status === 'success' ? 'default' : job.status === 'failed' ? 'destructive' : job.status === 'running' ? 'default' : 'secondary'}>{job.status}</Badge>
                    </TableCell>
                    <TableCell>
                      {job.status === 'running' && (
                        <Button size="sm" variant="destructive" onClick={() => cancelJob(job.id)}>
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
      </div>
    </div>
  );
};

export default AnsibleSaltPage;
