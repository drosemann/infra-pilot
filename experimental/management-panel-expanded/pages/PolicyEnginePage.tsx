import { useEffect, useState } from 'react';
import { FormattedMessage, useIntl } from 'react-intl';
import { apiClient } from '../lib/api';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';

interface Policy {
  policy_id: string;
  name: string;
  mode: string;
  enabled: boolean;
  tags: string[];
}

interface Decision {
  decision_id: string;
  user: string;
  action: string;
  resource: string;
  decision: string;
  timestamp: string;
}

export const PolicyEnginePage = () => {
  const intl = useIntl();
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    try {
      const [polData, decData] = await Promise.all([apiClient.listPolicies(), apiClient.listDecisions()]);
      setPolicies(polData || []);
      setDecisions(decData || []);
    } catch (error) {
      toast.error('Failed to load policy data');
    } finally {
      setLoading(false);
    }
  };

  const togglePolicy = async (id: string, enabled: boolean) => {
    try {
      if (enabled) await apiClient.disablePolicy(id);
      else await apiClient.enablePolicy(id);
      setPolicies(policies.map((p) => p.policy_id === id ? { ...p, enabled: !p.enabled } : p));
      toast.success(`Policy ${enabled ? 'disabled' : 'enabled'}`);
    } catch (error) {
      toast.error('Failed to toggle policy');
    }
  };

  const deletePolicy = async (id: string) => {
    try {
      await apiClient.deletePolicy(id);
      setPolicies(policies.filter((p) => p.policy_id !== id));
      toast.success('Policy deleted');
    } catch (error) {
      toast.error('Failed to delete policy');
    }
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>;

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold"><FormattedMessage id="policyEngine.title" defaultMessage="Policy Engine" /></h1>
          <p className="text-muted-foreground mt-1"><FormattedMessage id="policyEngine.description" defaultMessage="Manage policy-as-code rules and view access decisions" /></p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader><CardTitle><FormattedMessage id="policyEngine.policies" defaultMessage="Policies" /></CardTitle></CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead><FormattedMessage id="common.name" defaultMessage="Name" /></TableHead>
                  <TableHead><FormattedMessage id="policyEngine.mode" defaultMessage="Mode" /></TableHead>
                  <TableHead><FormattedMessage id="common.status" defaultMessage="Status" /></TableHead>
                  <TableHead><FormattedMessage id="common.actions" defaultMessage="Actions" /></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {policies.map((p) => (
                  <TableRow key={p.policy_id}>
                    <TableCell className="font-medium">{p.name}</TableCell>
                    <TableCell>
                      <Badge variant={p.mode === 'enforcing' ? 'destructive' : 'secondary'}>{p.mode}</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={p.enabled ? 'default' : 'outline'}>{p.enabled ? 'Enabled' : 'Disabled'}</Badge>
                    </TableCell>
                    <TableCell className="space-x-2">
                      <Button size="sm" variant="outline" onClick={() => togglePolicy(p.policy_id, p.enabled)}>
                        {p.enabled ? <FormattedMessage id="policyEngine.disable" defaultMessage="Disable" /> : <FormattedMessage id="policyEngine.enable" defaultMessage="Enable" />}
                      </Button>
                      <Button size="sm" variant="destructive" onClick={() => deletePolicy(p.policy_id)}>
                        <FormattedMessage id="common.delete" defaultMessage="Delete" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle><FormattedMessage id="policyEngine.recentDecisions" defaultMessage="Recent Decisions" /></CardTitle></CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead><FormattedMessage id="common.user" defaultMessage="User" /></TableHead>
                  <TableHead><FormattedMessage id="policyEngine.action" defaultMessage="Action" /></TableHead>
                  <TableHead><FormattedMessage id="policyEngine.resource" defaultMessage="Resource" /></TableHead>
                  <TableHead><FormattedMessage id="policyEngine.decision" defaultMessage="Decision" /></TableHead>
                  <TableHead><FormattedMessage id="common.time" defaultMessage="Time" /></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {decisions.map((d) => (
                  <TableRow key={d.decision_id}>
                    <TableCell className="font-medium">{d.user}</TableCell>
                    <TableCell>{d.action}</TableCell>
                    <TableCell className="font-mono text-xs">{d.resource}</TableCell>
                    <TableCell>
                      <Badge variant={d.decision === 'allow' ? 'default' : 'destructive'}>{d.decision}</Badge>
                    </TableCell>
                    <TableCell className="text-xs">{new Date(d.timestamp).toLocaleString()}</TableCell>
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

export default PolicyEnginePage;
