import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Steps, Step } from '@/components/ui/steps';
import { ArrowRight, CheckCircle, AlertCircle, RefreshCw, Globe, Server, FileText, Activity, Play, RotateCcw } from 'lucide-react';

interface MigrationJob {
  job_id: string;
  name: string;
  source_type: string;
  destination_type: string;
  status: string;
  progress: number;
  total_bytes: number;
  total_gb: number;
  transferred_bytes: number;
  transferred_gb: number;
  error_count: number;
  warning_count: number;
  started_at: string | null;
  completed_at: string | null;
  checksum_match: boolean | null;
  rollback_available: boolean;
}

const mockJobs: MigrationJob[] = [
  { job_id: 'mig-1715000000', name: 'Server Data to S3', source_type: 'local', destination_type: 's3', status: 'completed', progress: 100, total_bytes: 536870912000, total_gb: 500, transferred_bytes: 536870912000, transferred_gb: 500, error_count: 0, warning_count: 2, started_at: '2024-05-28T08:00:00Z', completed_at: '2024-05-28T10:30:00Z', checksum_match: true, rollback_available: true },
  { job_id: 'mig-1715100000', name: 'Database Archive to Glacier', source_type: 'minio', destination_type: 'backblaze_b2', status: 'running', progress: 45, total_bytes: 2199023255552, total_gb: 2048, transferred_bytes: 989560464998, transferred_gb: 922, error_count: 1, warning_count: 3, started_at: '2024-05-29T06:00:00Z', completed_at: null, checksum_match: null, rollback_available: true },
  { job_id: 'mig-1715200000', name: 'Legacy NAS Migration', source_type: 'nfs', destination_type: 'ceph_rgw', status: 'pending', progress: 0, total_bytes: 4398046511104, total_gb: 4096, transferred_bytes: 0, transferred_gb: 0, error_count: 0, warning_count: 0, started_at: null, completed_at: null, checksum_match: null, rollback_available: true },
];

const backendTypes = [
  { id: 'local', name: 'Local Filesystem', icon: Server },
  { id: 's3', name: 'AWS S3', icon: Globe },
  { id: 'b2', name: 'Backblaze B2', icon: Globe },
  { id: 'wasabi', name: 'Wasabi', icon: Globe },
  { id: 'gcs', name: 'Google Cloud Storage', icon: Globe },
  { id: 'azure', name: 'Azure Blob Storage', icon: Globe },
  { id: 'minio', name: 'Minio', icon: Server },
  { id: 'nfs', name: 'Network File System', icon: Server },
  { id: 'ceph_rgw', name: 'Ceph RGW', icon: Server },
];

const DataMigrationWizard: React.FC = () => {
  const [jobs, setJobs] = useState<MigrationJob[]>(mockJobs);
  const [activeTab, setActiveTab] = useState('jobs');
  const [currentStep, setCurrentStep] = useState(0);
  const [isWizardOpen, setIsWizardOpen] = useState(false);
  const [wizardData, setWizardData] = useState({ name: '', sourceType: 'local', sourcePath: '', destType: 's3', destPath: '', bandwidth: 100 });
  const [isRunningJob, setIsRunningJob] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);

  const steps = ['Source Configuration', 'Destination Configuration', 'Migration Settings', 'Review & Start'];

  const handleStartWizard = () => {
    setIsWizardOpen(true);
    setCurrentStep(0);
    setWizardData({ name: '', sourceType: 'local', sourcePath: '', destType: 's3', destPath: '', bandwidth: 100 });
  };

  const handleCreateJob = () => {
    const job: MigrationJob = {
      job_id: `mig-${Date.now()}`,
      name: wizardData.name,
      source_type: wizardData.sourceType,
      destination_type: wizardData.destType,
      status: 'pending',
      progress: 0,
      total_bytes: 107374182400,
      total_gb: 100,
      transferred_bytes: 0,
      transferred_gb: 0,
      error_count: 0,
      warning_count: 0,
      started_at: null,
      completed_at: null,
      checksum_match: null,
      rollback_available: true,
    };
    setJobs([job, ...jobs]);
    setIsWizardOpen(false);
    setCurrentStep(0);
  };

  const handleStartJob = (jobId: string) => {
    setIsRunningJob(jobId);
    setProgress(0);
    const interval = setInterval(() => {
      setProgress(p => {
        if (p >= 100) {
          clearInterval(interval);
          setIsRunningJob(null);
          setJobs(prev => prev.map(j => j.job_id === jobId ? { ...j, status: 'completed', progress: 100, completed_at: new Date().toISOString(), checksum_match: true } : j));
          return 100;
        }
        setJobs(prev => prev.map(j => j.job_id === jobId ? { ...j, status: 'running', progress: p + 2, transferred_gb: (j.total_gb * (p + 2)) / 100 } : j));
        return p + 2;
      });
    }, 200);
  };

  const handleRollback = (jobId: string) => {
    setJobs(prev => prev.map(j => j.job_id === jobId ? { ...j, status: 'rolled_back', rollback_available: false } : j));
  };

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Data Migration Wizard</h1>
          <p className="text-muted-foreground">Guided migration between storage backends with progress tracking and rollback</p>
        </div>
        <Button onClick={handleStartWizard}>
          <Play className="mr-2 h-4 w-4" />New Migration
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Total Jobs</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{jobs.length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Completed</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-green-500">{jobs.filter(j => j.status === 'completed').length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">In Progress</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-yellow-500">{jobs.filter(j => j.status === 'running').length}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Total Data</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{jobs.reduce((s, j) => s + j.total_gb, 0).toFixed(0)} GB</div></CardContent></Card>
      </div>

      <Card>
        <CardHeader><CardTitle>Migration Jobs</CardTitle></CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Source → Destination</TableHead>
                <TableHead>Progress</TableHead>
                <TableHead>Data Transferred</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {jobs.map(job => (
                <TableRow key={job.job_id}>
                  <TableCell className="font-medium">{job.name}</TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1">
                      <Badge variant="outline" className="text-xs">{job.source_type}</Badge>
                      <ArrowRight className="h-3 w-3" />
                      <Badge variant="outline" className="text-xs">{job.destination_type}</Badge>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Progress value={job.progress} className="w-20" />
                      <span className="text-xs">{job.progress.toFixed(0)}%</span>
                    </div>
                  </TableCell>
                  <TableCell>{job.transferred_gb.toFixed(1)} / {job.total_gb.toFixed(0)} GB</TableCell>
                  <TableCell>
                    <Badge variant={
                      job.status === 'completed' ? 'default' :
                      job.status === 'running' ? 'secondary' :
                      job.status === 'rolled_back' ? 'outline' : 'destructive'
                    }>{job.status}</Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex gap-1">
                      {job.status === 'pending' && (
                        <Button size="sm" variant="outline" onClick={() => handleStartJob(job.job_id)} disabled={isRunningJob === job.job_id}>
                          <Play className="h-3 w-3" />
                        </Button>
                      )}
                      {job.rollback_available && job.status === 'completed' && (
                        <Button size="sm" variant="outline" onClick={() => handleRollback(job.job_id)}>
                          <RotateCcw className="h-3 w-3" />
                        </Button>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Dialog open={isWizardOpen} onOpenChange={setIsWizardOpen}>
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader><DialogTitle>Data Migration Wizard</DialogTitle></DialogHeader>
          <Steps currentStep={currentStep}>
            <Step title={steps[0]} />
            <Step title={steps[1]} />
            <Step title={steps[2]} />
            <Step title={steps[3]} />
          </Steps>
          <div className="py-4">
            {currentStep === 0 && (
              <div className="space-y-4">
                <h3 className="font-medium">Select Source</h3>
                <div className="grid grid-cols-3 gap-2">
                  {backendTypes.map(bt => (
                    <Button key={bt.id} variant={wizardData.sourceType === bt.id ? 'default' : 'outline'} className="h-20 flex-col" onClick={() => setWizardData({ ...wizardData, sourceType: bt.id })}>
                      <bt.icon className="h-5 w-5 mb-1" />
                      <span className="text-xs">{bt.name}</span>
                    </Button>
                  ))}
                </div>
                <div>
                  <Label>Source Path / Bucket</Label>
                  <Input value={wizardData.sourcePath} onChange={e => setWizardData({ ...wizardData, sourcePath: e.target.value })} placeholder="/mnt/data/ or s3://bucket/" />
                </div>
              </div>
            )}
            {currentStep === 1 && (
              <div className="space-y-4">
                <h3 className="font-medium">Select Destination</h3>
                <div className="grid grid-cols-3 gap-2">
                  {backendTypes.map(bt => (
                    <Button key={bt.id} variant={wizardData.destType === bt.id ? 'default' : 'outline'} className="h-20 flex-col" onClick={() => setWizardData({ ...wizardData, destType: bt.id })}>
                      <bt.icon className="h-5 w-5 mb-1" />
                      <span className="text-xs">{bt.name}</span>
                    </Button>
                  ))}
                </div>
                <div>
                  <Label>Destination Path / Bucket</Label>
                  <Input value={wizardData.destPath} onChange={e => setWizardData({ ...wizardData, destPath: e.target.value })} placeholder="s3://backup-bucket/" />
                </div>
              </div>
            )}
            {currentStep === 2 && (
              <div className="space-y-4">
                <h3 className="font-medium">Migration Settings</h3>
                <div>
                  <Label>Job Name</Label>
                  <Input value={wizardData.name} onChange={e => setWizardData({ ...wizardData, name: e.target.value })} placeholder="My Migration" />
                </div>
                <div>
                  <Label>Bandwidth Limit (Mbps)</Label>
                  <Input type="number" value={wizardData.bandwidth} onChange={e => setWizardData({ ...wizardData, bandwidth: parseInt(e.target.value) || 100 })} />
                </div>
                <div className="flex items-center gap-2">
                  <input type="checkbox" id="checksum" defaultChecked />
                  <Label htmlFor="checksum">Verify checksums after migration</Label>
                </div>
                <div className="flex items-center gap-2">
                  <input type="checkbox" id="rollback" defaultChecked />
                  <Label htmlFor="rollback">Enable rollback on failure</Label>
                </div>
              </div>
            )}
            {currentStep === 3 && (
              <div className="space-y-4">
                <h3 className="font-medium">Review Migration</h3>
                <div className="p-4 rounded-lg bg-muted space-y-2">
                  <div><strong>Name:</strong> {wizardData.name || 'Unnamed'}</div>
                  <div><strong>Source:</strong> {wizardData.sourceType} - {wizardData.sourcePath || 'default'}</div>
                  <div><strong>Destination:</strong> {wizardData.destType} - {wizardData.destPath || 'default'}</div>
                  <div><strong>Bandwidth:</strong> {wizardData.bandwidth} Mbps</div>
                  <div><strong>Estimated time:</strong> ~{(100 * 1024 / wizardData.bandwidth / 60).toFixed(0)} min (for 100 GB)</div>
                </div>
              </div>
            )}
          </div>
          <div className="flex justify-between">
            <Button variant="outline" disabled={currentStep === 0} onClick={() => setCurrentStep(s => s - 1)}>Back</Button>
            {currentStep < 3 ? (
              <Button onClick={() => setCurrentStep(s => s + 1)}>Next</Button>
            ) : (
              <Button onClick={handleCreateJob} disabled={!wizardData.name}>
                <Play className="mr-2 h-4 w-4" />Start Migration
              </Button>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default DataMigrationWizard;
