import { useEffect, useState } from 'react';
import { apiClient } from '../lib/api';
import { BackupJob, BackupStatusEntry } from '../lib/types';

export const BackupStatus = () => {
  const [jobs, setJobs] = useState<BackupJob[]>([]);
  const [statuses, setStatuses] = useState<Record<string, BackupStatusEntry[]>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const jobsData = await apiClient.getBackupJobs();
        setJobs(jobsData);
        const statusMap: Record<string, BackupStatusEntry[]> = {};
        for (const job of jobsData) {
          try {
            statusMap[job.id] = await apiClient.getBackupStatus(job.id);
          } catch {
            statusMap[job.id] = [];
          }
        }
        setStatuses(statusMap);
      } catch {
        // silent
      } finally {
        setLoading(false);
      }
    };
    load();
    const interval = setInterval(load, 30000);
    return () => clearInterval(interval);
  }, []);

  const allEntries = Object.values(statuses).flat();
  const successCount = allEntries.filter((e) => e.status === 'success').length;
  const failCount = allEntries.filter((e) => e.status === 'failed').length;
  const totalCount = allEntries.length;
  const successRate = totalCount > 0 ? Math.round((successCount / totalCount) * 100) : 0;

  if (loading) {
    return <div className="py-4 text-white/45">Loading backup status…</div>;
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-3 gap-4">
        <div className="card p-4 text-center">
          <p className="text-2xl font-semibold text-white">{successCount}</p>
          <p className="mt-1 text-xs text-white/45">Successful</p>
        </div>
        <div className="card p-4 text-center">
          <p className="text-2xl font-semibold text-white">{failCount}</p>
          <p className="mt-1 text-xs text-white/45">Failed</p>
        </div>
        <div className="card p-4 text-center">
          <p className="text-2xl font-semibold text-white">{successRate}%</p>
          <p className="mt-1 text-xs text-white/45">Success Rate</p>
        </div>
      </div>

      <div className="h-2 w-full overflow-hidden rounded-full bg-white/10">
        <div
          className="h-full rounded-full bg-emerald-400 transition-all"
          style={{ width: `${successRate}%` }}
        />
      </div>

      {jobs.length === 0 ? (
        <p className="text-sm text-white/45">No backup jobs configured</p>
      ) : (
        <div className="space-y-3">
          {jobs.map((job) => {
            const entries = statuses[job.id] || [];
            const recent = entries.slice(0, 5);
            return (
              <div key={job.id} className="card p-3">
                <p className="text-sm font-semibold text-white mb-2">{job.name}</p>
                {recent.length === 0 ? (
                  <p className="text-xs text-white/40">No backup runs yet</p>
                ) : (
                  <div className="space-y-1">
                    {recent.map((entry) => (
                      <div key={entry.id} className="flex items-center justify-between text-xs">
                        <div className="flex items-center gap-2">
                          <span className={`w-2 h-2 rounded-full ${
                            entry.status === 'success' ? 'bg-green-500' :
                            entry.status === 'failed' ? 'bg-red-500' : 'bg-yellow-500'
                          }`} />
                          <span className="text-white/60">{entry.status}</span>
                        </div>
                        <span className="text-white/40">
                          {entry.size_mb ? `${entry.size_mb.toFixed(1)} MB` : ''}
                          {entry.started_at && ` Â· ${new Date(entry.started_at).toLocaleDateString()}`}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default BackupStatus;
