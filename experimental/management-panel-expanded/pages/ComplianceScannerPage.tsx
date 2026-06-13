import { useEffect, useState } from 'react';
import { FormattedMessage, useIntl } from 'react-intl';
import { apiClient } from '../lib/api';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Progress } from '../components/ui/progress';

interface ScanResult {
  check_id: string;
  framework: string;
  status: string;
  severity: string;
  description: string;
}

interface Waiver {
  check_id: string;
  framework: string;
  reason: string;
  expires_at: string;
}

export const ComplianceScannerPage = () => {
  const intl = useIntl();
  const [scanResults, setScanResults] = useState<ScanResult[]>([]);
  const [waivers, setWaivers] = useState<Waiver[]>([]);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [selectedFramework, setSelectedFramework] = useState('cis_docker');

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    try {
      const [scanData, waiverData] = await Promise.all([apiClient.listScanResults(), apiClient.listWaivers()]);
      setScanResults(scanData || []);
      setWaivers(waiverData || []);
    } catch (error) {
      toast.error('Failed to load compliance data');
    } finally {
      setLoading(false);
    }
  };

  const runScan = async () => {
    setScanning(true);
    try {
      const results = await apiClient.runComplianceScan(selectedFramework);
      setScanResults(results);
      toast.success('Scan completed');
    } catch (error) {
      toast.error('Scan failed');
    } finally {
      setScanning(false);
    }
  };

  const passedChecks = scanResults.filter((r) => r.status === 'pass').length;
  const failedChecks = scanResults.filter((r) => r.status === 'fail').length;
  const totalChecks = scanResults.length;
  const passRate = totalChecks > 0 ? (passedChecks / totalChecks) * 100 : 0;

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>;

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold"><FormattedMessage id="compliance.title" defaultMessage="Compliance Scanner" /></h1>
          <p className="text-muted-foreground mt-1"><FormattedMessage id="compliance.description" defaultMessage="Run compliance scans against CIS, NIST, and BSI benchmarks" /></p>
        </div>
      </div>

      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4 mb-4">
            <select value={selectedFramework} onChange={(e) => setSelectedFramework(e.target.value)} className="flex h-10 w-[200px] rounded-md border border-input bg-background px-3 py-2 text-sm">
              <option value="cis_docker">CIS Docker Benchmark</option>
              <option value="cis_kubernetes">CIS Kubernetes Benchmark</option>
              <option value="nist_800_53">NIST SP 800-53</option>
              <option value="bsi_grundschutz">BSI Grundschutz</option>
            </select>
            <Button onClick={runScan} disabled={scanning}>
              {scanning ? <FormattedMessage id="compliance.scanning" defaultMessage="Scanning..." /> : <FormattedMessage id="compliance.runScan" defaultMessage="Run Scan" />}
            </Button>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span><FormattedMessage id="compliance.complianceScore" defaultMessage="Compliance Score" /></span>
              <span className="font-bold">{passRate.toFixed(1)}%</span>
            </div>
            <Progress value={passRate} className="h-2" />
            <div className="flex gap-4 text-sm text-muted-foreground">
              <span className="text-green-600">{passedChecks} <FormattedMessage id="compliance.passed" defaultMessage="passed" /></span>
              <span className="text-red-600">{failedChecks} <FormattedMessage id="compliance.failed" defaultMessage="failed" /></span>
              <span>{totalChecks} <FormattedMessage id="compliance.total" defaultMessage="total" /></span>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle><FormattedMessage id="compliance.scanResults" defaultMessage="Scan Results" /></CardTitle></CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead><FormattedMessage id="compliance.checkId" defaultMessage="Check ID" /></TableHead>
                <TableHead><FormattedMessage id="compliance.framework" defaultMessage="Framework" /></TableHead>
                <TableHead><FormattedMessage id="common.description" defaultMessage="Description" /></TableHead>
                <TableHead><FormattedMessage id="compliance.severity" defaultMessage="Severity" /></TableHead>
                <TableHead><FormattedMessage id="compliance.status" defaultMessage="Status" /></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {scanResults.slice(0, 50).map((r, i) => (
                <TableRow key={`${r.check_id}-${i}`}>
                  <TableCell className="font-mono text-xs">{r.check_id}</TableCell>
                  <TableCell><Badge variant="outline">{r.framework}</Badge></TableCell>
                  <TableCell className="max-w-[300px] truncate">{r.description}</TableCell>
                  <TableCell>
                    <Badge variant={r.severity === 'critical' || r.severity === 'high' ? 'destructive' : 'secondary'}>{r.severity}</Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant={r.status === 'pass' ? 'default' : 'destructive'}>{r.status}</Badge>
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

export default ComplianceScannerPage;
