import { useEffect, useState } from 'react';
import { FormattedMessage, useIntl } from 'react-intl';
import { apiClient } from '../lib/api';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';

interface RemediationRule {
  id: string;
  name: string;
  trigger_type: string;
  mode: string;
  enabled: boolean;
  resource_types: string[];
  cooldown_minutes: number;
}

interface RemediationExecution {
  id: string;
  rule_name: string;
  status: string;
  target_resource: string;
  started_at: string;
  duration_ms: number | null;
}

export const AutoRemediationPage = () => {
  const intl = useIntl();
  const [rules, setRules] = useState<RemediationRule[]>([]);
  const [executions, setExecutions] = useState<RemediationExecution[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    try {
      const [ruleData, execData] = await Promise.all([apiClient.listRemediationRules(), apiClient.listRemediationExecutions()]);
      setRules(ruleData || []);
      setExecutions(execData || []);
    } catch (error) {
      toast.error('Failed to load remediation data');
    } finally {
      setLoading(false);
    }
  };

  const toggleRule = async (id: string, enabled: boolean) => {
    try {
      if (enabled) await apiClient.disableRemediationRule(id);
      else await apiClient.enableRemediationRule(id);
      setRules(rules.map((r) => r.id === id ? { ...r, enabled: !r.enabled } : r));
      toast.success(`Rule ${enabled ? 'disabled' : 'enabled'}`);
    } catch (error) {
      toast.error('Failed to toggle rule');
    }
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>;

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold"><FormattedMessage id="autoRemediation.title" defaultMessage="Event-Driven Auto-Remediation" /></h1>
          <p className="text-muted-foreground mt-1"><FormattedMessage id="autoRemediation.description" defaultMessage="Configure automated remediation rules for infrastructure issues" /></p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span><FormattedMessage id="autoRemediation.remediationRules" defaultMessage="Remediation Rules" /></span>
              <Badge variant="default">{rules.filter((r) => r.enabled).length} active</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead><FormattedMessage id="common.name" defaultMessage="Name" /></TableHead>
                  <TableHead><FormattedMessage id="autoRemediation.triggerType" defaultMessage="Trigger" /></TableHead>
                  <TableHead><FormattedMessage id="autoRemediation.mode" defaultMessage="Mode" /></TableHead>
                  <TableHead><FormattedMessage id="common.status" defaultMessage="Status" /></TableHead>
                  <TableHead><FormattedMessage id="common.actions" defaultMessage="Actions" /></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {rules.map((rule) => (
                  <TableRow key={rule.id}>
                    <TableCell className="font-medium">{rule.name}</TableCell>
                    <TableCell><Badge variant="outline">{rule.trigger_type}</Badge></TableCell>
                    <TableCell>
                      <Badge variant={rule.mode === 'automatic' ? 'default' : rule.mode === 'semi_automatic' ? 'secondary' : 'outline'}>{rule.mode}</Badge>
                    </TableCell>
                    <TableCell><Badge variant={rule.enabled ? 'default' : 'outline'}>{rule.enabled ? 'Enabled' : 'Disabled'}</Badge></TableCell>
                    <TableCell>
                      <Button size="sm" variant="outline" onClick={() => toggleRule(rule.id, rule.enabled)}>
                        {rule.enabled ? <FormattedMessage id="common.disable" defaultMessage="Disable" /> : <FormattedMessage id="common.enable" defaultMessage="Enable" />}
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle><FormattedMessage id="autoRemediation.recentExecutions" defaultMessage="Recent Executions" /></CardTitle></CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead><FormattedMessage id="autoRemediation.ruleName" defaultMessage="Rule" /></TableHead>
                  <TableHead><FormattedMessage id="autoRemediation.targetResource" defaultMessage="Target" /></TableHead>
                  <TableHead><FormattedMessage id="common.status" defaultMessage="Status" /></TableHead>
                  <TableHead><FormattedMessage id="autoRemediation.duration" defaultMessage="Duration" /></TableHead>
                  <TableHead><FormattedMessage id="common.time" defaultMessage="Time" /></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {executions.map((ex) => (
                  <TableRow key={ex.id}>
                    <TableCell className="font-medium text-sm">{ex.rule_name}</TableCell>
                    <TableCell className="font-mono text-xs">{ex.target_resource}</TableCell>
                    <TableCell>
                      <Badge variant={ex.status === 'success' ? 'default' : ex.status === 'failed' ? 'destructive' : 'secondary'}>{ex.status}</Badge>
                    </TableCell>
                    <TableCell className="text-xs">{ex.duration_ms ? `${ex.duration_ms}ms` : '-'}</TableCell>
                    <TableCell className="text-xs">{new Date(ex.started_at).toLocaleString()}</TableCell>
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

export default AutoRemediationPage;
