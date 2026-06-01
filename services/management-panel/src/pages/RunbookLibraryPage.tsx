import { useEffect, useState } from 'react';
import { FormattedMessage, useIntl } from 'react-intl';
import { apiClient } from '../lib/api';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';

interface Runbook {
  id: string;
  name: string;
  category: string;
  status: string;
  severity: string;
  tags: string[];
  author: string;
  version: number;
  steps: any[];
}

export const RunbookLibraryPage = () => {
  const intl = useIntl();
  const [runbooks, setRunbooks] = useState<Runbook[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedRunbook, setSelectedRunbook] = useState<Runbook | null>(null);
  const [showDetail, setShowDetail] = useState(false);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    try {
      const data = await apiClient.listRunbooks();
      setRunbooks(data || []);
    } catch (error) {
      toast.error('Failed to load runbooks');
    } finally {
      setLoading(false);
    }
  };

  const viewDetail = (rb: Runbook) => {
    setSelectedRunbook(rb);
    setShowDetail(true);
  };

  const categoryColor = (cat: string) => {
    const colors: Record<string, 'default' | 'destructive' | 'secondary' | 'outline'> = {
      incident_response: 'destructive',
      deployment: 'default',
      security: 'destructive',
      backup: 'secondary',
      troubleshooting: 'outline',
    };
    return colors[cat] || 'outline';
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>;

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold"><FormattedMessage id="runbook.title" defaultMessage="Runbook Templates Library" /></h1>
          <p className="text-muted-foreground mt-1"><FormattedMessage id="runbook.description" defaultMessage="Browse and manage runbook templates for common operations" /></p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {runbooks.map((rb) => (
          <Card key={rb.id} className="cursor-pointer hover:shadow-lg transition-shadow" onClick={() => viewDetail(rb)}>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span className="text-base">{rb.name}</span>
                <Badge variant={rb.status === 'published' ? 'default' : 'secondary'}>{rb.status}</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Badge variant={categoryColor(rb.category)} className="text-xs">{rb.category}</Badge>
                  <Badge variant="outline" className="text-xs">v{rb.version}</Badge>
                  {rb.severity === 'high' && <Badge variant="destructive" className="text-xs">high</Badge>}
                </div>
                <div className="flex flex-wrap gap-1">
                  {rb.tags.map((tag, i) => <Badge key={i} variant="outline" className="text-xs">{tag}</Badge>)}
                </div>
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>{rb.author}</span>
                  <span>{rb.steps?.length || 0} steps</span>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Dialog open={showDetail} onOpenChange={setShowDetail}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>{selectedRunbook?.name}</DialogTitle>
          </DialogHeader>
          {selectedRunbook && (
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <Badge variant={categoryColor(selectedRunbook.category)}>{selectedRunbook.category}</Badge>
                <Badge variant="outline">v{selectedRunbook.version}</Badge>
                <Badge variant={selectedRunbook.status === 'published' ? 'default' : 'secondary'}>{selectedRunbook.status}</Badge>
              </div>
              <div>
                <h4 className="font-semibold mb-2"><FormattedMessage id="runbook.steps" defaultMessage="Steps" /></h4>
                <div className="space-y-1">
                  {selectedRunbook.steps?.map((step: any, i: number) => (
                    <div key={i} className="flex items-center gap-2 p-2 border rounded text-sm">
                      <span className="w-6 h-6 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-xs">{i + 1}</span>
                      <span>{step.name || step.description || `Step ${i + 1}`}</span>
                      <Badge variant="outline" className="text-xs ml-auto">{step.type || 'manual'}</Badge>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default RunbookLibraryPage;
