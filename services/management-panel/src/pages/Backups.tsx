import { BackupArtifacts } from '../components/BackupArtifacts';
import { BackupManager } from '../components/BackupManager';
import { BackupStatus } from '../components/BackupStatus';
import { PageHeader } from '../components/PageHeader';

export const Backups = () => {
  return (
    <div className="mx-auto max-w-5xl space-y-8 px-2 py-8">
      <PageHeader eyebrow="Protect">
        <h1 className="text-4xl font-semibold tracking-tight text-white">Backups</h1>
        <p className="mt-2 text-white/55">Automatic copies of databases and servers.</p>
      </PageHeader>

      <BackupStatus />
      <BackupArtifacts />
      <BackupManager />
    </div>
  );
};

export default Backups;
