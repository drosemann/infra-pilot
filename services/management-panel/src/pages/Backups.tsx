import { BackupArtifacts } from '../components/BackupArtifacts';
import { BackupManager } from '../components/BackupManager';
import { BackupStatus } from '../components/BackupStatus';
import { PageHeader } from '../components/PageHeader';

export const Backups = () => {
  return (
    <div className="space-y-8">
      <PageHeader eyebrow="Protect">
        <h1 className="text-3xl font-bold text-white mb-2">Backups</h1>
        <p className="text-slate-400">Database and server backup automation</p>
      </PageHeader>

      <BackupStatus />
      <BackupArtifacts />
      <BackupManager />
    </div>
  );
};

export default Backups;
