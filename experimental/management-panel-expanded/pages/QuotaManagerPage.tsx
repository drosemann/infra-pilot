import { useEffect, useState } from 'react';
import { FormattedMessage, useIntl } from 'react-intl';
import { apiClient } from '../lib/api';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';

interface Quota {
  id: string;
  name: string;
  resource_type: string;
  hard_limit: number;
  current_usage: number;
  unit: string;
  scope: string;
}

export const QuotaManagerPage = () => {
  const intl = useIntl();
  const [quotas, setQuotas] = useState<Quota[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    try {
      const data = await apiClient.listQuotas();
      setQuotas(data || []);
    } catch (error) {
      toast.error('Failed to load quotas');
    } finally {
      setLoading(false);
    }
  };

  const utilizationColor = (used: number, limit: number) => {
    const pct = limit > 0 ? (used / limit) * 100 : 0;
    if (pct >= 90) return 'bg-red-500';
    if (pct >= 70) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>;

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold"><FormattedMessage id="quota.title" defaultMessage="Resource Quota Management" /></h1>
          <p className="text-muted-foreground mt-1"><FormattedMessage id="quota.description" defaultMessage="Manage resource quotas, limits, and usage tracking" /></p>
        </div>
      </div>

      {quotas.map((q) => {
        const pct = q.hard_limit > 0 ? (q.current_usage / q.hard_limit) * 100 : 0;
        return (
          <Card key={q.id}>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between mb-2">
                <div>
                  <h3 className="font-semibold">{q.name}</h3>
                  <p className="text-sm text-muted-foreground">{q.resource_type} ({q.scope})</p>
                </div>
                <div className="text-right">
                  <span className="text-2xl font-bold">{q.current_usage}</span>
                  <span className="text-muted-foreground"> / {q.hard_limit} {q.unit}</span>
                </div>
              </div>
              <div className="w-full bg-secondary rounded-full h-2.5">
                <div className={`h-2.5 rounded-full ${utilizationColor(q.current_usage, q.hard_limit)}`} style={{ width: `${Math.min(pct, 100)}%` }}></div>
              </div>
              <p className="text-xs text-muted-foreground mt-1">{pct.toFixed(1)}% utilized</p>
            </CardContent>
          </Card>
        );
      })}
      {quotas.length === 0 && (
        <Card>
          <CardContent className="py-8 text-center text-muted-foreground">
            <FormattedMessage id="quota.noLimits" defaultMessage="No quota limits configured" />
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default QuotaManagerPage;
